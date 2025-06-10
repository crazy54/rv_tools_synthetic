#    ____  _____ ____  _     ___   ____  _        _    ____ ___ _   _  ____
#   |  _ \| ____|  _ \| |   / _ \ / ___|| |      / \  / ___|_ _| \ | |/ ___|
#   | |_) |  _| | |_) | |  | | | | |  _ | |     / _ \| |    | ||  \| | |  _
#   |  _ <| |___|  __/| |__| |_| | |_| || |___ / ___ \ |___ | || |\  | |_| |
#   |_| \_\_____|_|   |_____\___/ \____||_____/_/   \_\____|___|_| \_|\____|
#
#   RVTools Data Generator - Mock Data for VMware Environments
#

import csv
import os
import random
import string
import uuid
from datetime import datetime, timedelta
import json
import zipfile
import glob
import threading
import argparse
from tqdm import tqdm
import openai

try:
    import tkinter as tk
    from tkinter import ttk, filedialog # ttk for themed widgets, filedialog for browse
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    # print("tkinter not found, GUI functionality will be disabled.") # Optional print


# --- Global Configuration & Data ---
# Default output configuration (can be overridden by CLI args)
DEFAULT_OUTPUT_DIR = "RV_TOOL_ZIP_OUTPUT"
DEFAULT_CSV_SUBDIR_NAME = "RVT_CSV"
DEFAULT_ZIP_FILENAME = "RVTools_Export.zip"

ENVIRONMENT_DATA = {
    "vms": [], "hosts": [], "clusters": [], "datastores": [],
    "resource_pools": [], "vcenter_details": {}, "hbas": [],
    "host_nics": [], "host_vmkernel_nics": [], "standard_vswitches": [],
    "distributed_vswitches": [], "distributed_port_groups": [],
    "standard_port_groups": [],
    "vm_cd_drives": [], "vm_disks": [], "vm_files": [], "vm_partitions": [],
    "vm_snapshots": [], "vm_tools_status": [], "vm_usb_devices": [],
    "vcenter_health_statuses": [], "licenses": [], "host_multipaths": [],
    "vcenter_ip": None, "vcenter_uuid": None
}

CSV_HEADERS = {
    "vInfo": "VM,Powerstate,Template,SRM Placeholder,Config status,DNS Name,Connection state,Guest state,Heartbeat,Consolidation Needed,PowerOn,Suspended To Memory,Suspend time,Suspend Interval,Creation date,Change Version,CPUs,Overall Cpu Readiness,Memory,Active Memory,NICs,Disks,Total disk capacity MiB,Fixed Passthru HotPlug,min Required EVC Mode Key,Latency Sensitivity,Op Notification Timeout,EnableUUID,CBT,Primary IP Address,Network #1,Network #2,Network #3,Network #4,Network #5,Network #6,Network #7,Network #8,Num Monitors,Video Ram KiB,Resource pool,Folder ID,Folder,vApp,DAS protection,FT State,FT Role,FT Latency,FT Bandwidth,FT Sec. Latency,Vm Failover In Progress,Provisioned MiB,In Use MiB,Unshared MiB,HA Restart Priority,HA Isolation Response,HA VM Monitoring,Cluster rule(s),Cluster rule name(s),Boot Required,Boot delay,Boot retry delay,Boot retry enabled,Boot BIOS setup,Reboot PowerOff,EFI Secure boot,Firmware,HW version,HW upgrade status,HW upgrade policy,HW target,Path,Log directory,Snapshot directory,Suspend directory,Annotation,Datacenter,Cluster,Host,OS according to the configuration file,OS according to the VMware Tools,Customization Info,Guest Detailed Data,VM ID,SMBIOS UUID,VM UUID,VI SDK Server type,VI SDK API Version,VI SDK Server,VI SDK UUID".split(','),
    "vDisk": "VM,Powerstate,Template,SRM Placeholder,Disk,Disk Key,Disk UUID,Disk Path,Capacity MiB,Raw,Disk Mode,Sharing mode,Thin,Eagerly Scrub,Split,Write Through,Level,Shares,Reservation,Limit,Controller,Label,SCSI Unit #,Unit #,Shared Bus,Path,Raw LUN ID,Raw Comp. Mode,Internal Sort Column,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vNetwork": "VM,Powerstate,Template,SRM Placeholder,NIC label,Adapter,Network,Switch,Connected,Starts Connected,Mac Address,Type,IPv4 Address,IPv6 Address,Direct Path IO,Internal Sort Column,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vHost": "Host,Datacenter,Cluster,Config status,Compliance Check State,in Maintenance Mode,in Quarantine Mode,vSAN Fault Domain Name,CPU Model,Speed,HT Available,HT Active,# CPU,Cores per CPU,# Cores,CPU usage %,# Memory,Memory Tiering Type,Memory usage %,Console,# NICs,# HBAs,# VMs total,# VMs,VMs per Core,# vCPUs,vCPUs per Core,vRAM,VM Used memory,VM Memory Swapped,VM Memory Ballooned,VMotion support,Storage VMotion support,Current EVC,Max EVC,Assigned License(s),ATS Heartbeat,ATS Locking,Current CPU power man. policy,Supported CPU power man.,Host Power Policy,ESX Version,Boot time,DNS Servers,DHCP,Domain,Domain List,DNS Search Order,NTP Server(s),NTPD running,Time Zone,Time Zone Name,GMT Offset,Vendor,Model,Serial number,Service tag,OEM specific string,BIOS Vendor,BIOS Version,BIOS Date,Certificate Issuer,Certificate Start Date,Certificate Expiry Date,Certificate Status,Certificate Subject,Object ID,UUID,VI SDK Server,VI SDK UUID".split(','),
    "vCluster": "Name,Config status,OverallStatus,NumHosts,numEffectiveHosts,TotalCpu,NumCpuCores,NumCpuThreads,Effective Cpu,TotalMemory,Effective Memory,Num VMotions,HA enabled,Failover Level,AdmissionControlEnabled,Host monitoring,HB Datastore Candidate Policy,Isolation Response,Restart Priority,Cluster Settings,Max Failures,Max Failure Window,Failure Interval,Min Up Time,VM Monitoring,DRS enabled,DRS default VM behavior,DRS vmotion rate,DPM enabled,DPM default behavior,DPM Host Power Action Rate,Object ID,VI SDK Server,VI SDK UUID".split(','),
    "vDatastore": "Name,Config status,Address,Accessible,Type,# VMs total,# VMs,Capacity MiB,Provisioned MiB,In Use MiB,Free MiB,Free %,SIOC enabled,SIOC Threshold,# Hosts,Hosts,Cluster name,Cluster capacity MiB,Cluster free space MiB,Block size,Max Blocks,# Extents,Major Version,Version,VMFS Upgradeable,MHA,URL,Object ID,VI SDK Server,VI SDK UUID".split(','),
    "vRP": "Resource Pool name,Resource Pool path,Status,# VMs total,# VMs,# vCPUs,CPU limit,CPU overheadLimit,CPU reservation,CPU level,CPU shares,CPU expandableReservation,CPU maxUsage,CPU overallUsage,CPU reservationUsed,CPU reservationUsedForVm,CPU unreservedForPool,CPU unreservedForVm,Mem Configured,Mem limit,Mem overheadLimit,Mem reservation,Mem level,Mem shares,Mem expandableReservation,Mem maxUsage,Mem overallUsage,Mem reservationUsed,Mem reservationUsedForVm,Mem unreservedForPool,Mem unreservedForVm,QS overallCpuDemand,QS overallCpuUsage,QS staticCpuEntitlement,QS distributedCpuEntitlement,QS balloonedMemory,QS compressedMemory,QS consumedOverheadMemory,QS distributedMemoryEntitlement,QS guestMemoryUsage,QS hostMemoryUsage,QS overheadMemory,QS privateMemory,QS sharedMemory,QS staticMemoryEntitlement,QS swappedMemory,Object ID,VI SDK Server,VI SDK UUID".split(','),
    "vSource": "Name,OS type,API type,API version,Version,Patch level,Build,Fullname,Product name,Product version,Product line,Vendor,VI SDK Server,VI SDK UUID".split(','),
    "vHBA": "Host,Datacenter,Cluster,Device,Type,Status,Bus,Pci,Driver,Model,WWN,VI SDK Server,VI SDK UUID".split(','),
    "vNIC": "Host,Datacenter,Cluster,Network Device,Driver,Speed,Duplex,MAC,Switch,Uplink port,PCI,WakeOn,VI SDK Server,VI SDK UUID".split(','),
    "vSC_VMK": "Host,Datacenter,Cluster,Port Group,Device,Mac Address,DHCP,IP Address,IP 6 Address,Subnet mask,Gateway,IP 6 Gateway,MTU,Services,VI SDK Server,VI SDK UUID".split(','),
    "vSwitch": "Host,Datacenter,Cluster,Switch,# Ports,Free Ports,Promiscuous Mode,Mac Changes,Forged Transmits,Traffic Shaping,Width,Peak,Burst,Policy,Reverse Policy,Notify Switch,Rolling Order,Offload,TSO,Zero Copy Xmit,MTU,Uplinks,VI SDK Server,VI SDK UUID".split(','),
    "dvSwitch": "Switch,Datacenter,Name,Vendor,Version,Description,Created,Host members,Max Ports,# Ports,# VMs,In Traffic Shaping,In Avg,In Peak,In Burst,Out Traffic Shaping,Out Avg,Out Peak,Out Burst,CDP Type,CDP Operation,LACP Name,LACP Mode,LACP Load Balance Alg.,Max MTU,Contact,Admin Name,Object ID,VI SDK Server,VI SDK UUID".split(','),
    "dvPortGroup": "Name,Switch,Port Binding,VLAN,VLAN type,Port Group Key,# Ports,Active Ports,Configured Ports,Static Ports,Dynamic Ports,Scope,Port Name Format,VMs,VI SDK Server,VI SDK UUID".split(','),
    "vCD": "Select,VM,Powerstate,Template,SRM Placeholder,Device Node,Connected,Starts Connected,Device Type,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VMRef,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vFileInfo": "Friendly Path Name,File Name,File Type,File Size in bytes,Path,Internal Sort Column,VI SDK Server,VI SDK UUID".split(','),
    "vPartition": "VM,Powerstate,Template,SRM Placeholder,Disk Key,Disk,Capacity MiB,Consumed MiB,Free MiB,Free %,Internal Sort Column,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vSnapshot": "VM,Powerstate,Name,Description,Date / time,Filename,Size MiB (vmsn),Size MiB (total),Quiesced,State,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vTools": "Upgrade,VM,Powerstate,Template,SRM Placeholder,VM Version,Tools,Tools Version,Required Version,Upgradeable,Upgrade Policy,Sync time,App status,Heartbeat status,Kernel Crash state,Operation Ready,State change support,Interactive Guest,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VMRef,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vUSB": "Select,VM,Powerstate,Template,SRM Placeholder,Device Node,Device Type,Connected,Family,Speed,EHCI enabled,Auto connect,Bus number,Unit number,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware tools,VMRef,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vHealth": "Name,Message,Message type,VI SDK Server,VI SDK UUID".split(','),
    "vLicense": "Name,Key,Labels,Cost Unit,Total,Used,Expiration Date,Features,VI SDK Server,VI SDK UUID".split(','),
    "vMultiPath": "Host,Cluster,Datacenter,Datastore,Disk,Display name,Policy,Oper. State,Path 1,Path 1 state,Path 2,Path 2 state,Path 3,Path 3 state,Path 4,Path 4 state,Path 5,Path 5 state,Path 6,Path 6 state,Path 7,Path 7 state,Path 8,Path 8 state,vStorage,Queue depth,Vendor,Model,Revision,Level,Serial #,UUID,Object ID,VI SDK Server,VI SDK UUID".split(','),
    "vMemory": "VM,Powerstate,Template,SRM Placeholder,Size MiB,Memory Reservation Locked To Max,Overhead,Max,Consumed,Consumed Overhead,Private,Shared,Swapped,Ballooned,Active,Entitlement,DRS Entitlement,Level,Shares,Reservation,Limit,Hot Add,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vCPU": "VM,Powerstate,Template,SRM Placeholder,CPUs,Sockets,Cores p/s,Max,Overall,Level,Shares,Reservation,Entitlement,DRS Entitlement,Limit,Hot Add,Hot Remove,Numa Hotadd Exposed,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vPort": "Host,Datacenter,Cluster,Switch,Port Group,VLAN,Promiscuous Mode,Mac Changes,Forged Transmits,Traffic Shaping,Width,Peak,Burst,Policy,Reverse Policy,Notify Switch,Rolling Order,Offload,TSO,Zero Copy Xmit,VI SDK Server,VI SDK UUID".split(','),
}
if 'dvPort' in CSV_HEADERS and 'dvPortGroup' not in CSV_HEADERS:
    CSV_HEADERS['dvPortGroup'] = CSV_HEADERS.pop('dvPort')


# --- AI Prompt Templates ---
VINFO_AI_PROMPT_TEMPLATE = """
You are an AI assistant tasked with generating a data profile for a single VMware Virtual Machine, specifically for an RVTools vInfo report.
The output MUST be a single, valid JSON object. Do NOT include any explanatory text before or after the JSON object.
The JSON object should only contain keys corresponding to the column names provided below.

VM Context (use this information to make the data consistent):
- Suggested VM Name: "{suggested_vm_name}"
- Associated Host: "{associated_host}"
- Associated Cluster: "{associated_cluster}"
- Associated Datacenter: "{associated_datacenter}"
- Current Powerstate: "{power_state}"
- Guest OS (from VMware Tools): "{os_tools}"
- Configured Memory (GB): {memory_gb}

Column Names and Expected Data Characteristics (provide data for as many of these as possible):
{column_details_block}

Key Formatting Guidelines:
- Dates/Times (e.g., 'PowerOn', 'Creation date'): "YYYY/MM/DD HH:MM:SS" string, or null if not applicable.
- UUIDs (e.g., 'VM UUID', 'SMBIOS UUID'): Standard UUID string format.
- Booleans (e.g., 'Template', 'EnableUUID'): JSON true/false (not strings "true"/"false").
- Integers (e.g., 'CPUs', 'Memory' (in MiB)): JSON number.
- 'Primary IP Address': Valid IPv4 string, or null/empty if poweredOff.
- 'DNS Name': Plausible DNS hostname, possibly derived from VM name.
- 'Path' (and related directory paths): VMware datastore path format, e.g., "[datastoreName] VMName/VMName.vmx".
- If '{power_state}' is 'poweredOff' or 'suspended':
    - 'PowerOn' time can be blank or in the past.
    - 'Primary IP Address' should usually be null or empty.
    - 'Heartbeat' could be 'gray'.
- If '{power_state}' is 'suspended':
    - 'Suspend time' should be a valid past datetime string.
- Otherwise, 'Suspend time' should be null.

Provide ONLY the JSON object as your response.
"""
VHOST_AI_PROMPT_TEMPLATE = """
Generate realistic RVTools vHost data for an ESXi host named '{host_name}' in cluster '{cluster_name}', datacenter '{datacenter_name}'.
Host details: {cpu_count} CPUs, {cores_per_cpu} cores/CPU, {memory_mb}MB RAM, ESX version '{esx_version}', CPU Model '{cpu_model}'.
Consider these columns: {column_list}.
Provide values for some. Focus on 'Vendor', 'Model', 'Time Zone Name', 'NTP Server(s)', 'BIOS Vendor', 'BIOS Version', 'BIOS Date', 'Service tag'.
Example for 'Vendor': 'Acme Hypervisors Inc.'
Ensure data is consistent with the provided context.
"""
VDISK_AI_PROMPT_TEMPLATE = """
Generate realistic RVTools vDisk data for disk '{disk_label}' on VM '{vm_name}'.
VM context: Powerstate '{power_state}', Datastore '{datastore}'.
Consider these columns: {column_list}.
Provide values for some. Focus on 'Disk Mode', 'Sharing mode', 'Thin', 'Eagerly Scrub', 'Controller'.
Example for 'Disk Mode': 'persistent' or 'independent_persistent'.
Ensure data is consistent with VM context.
"""
VNETWORK_AI_PROMPT_TEMPLATE = """
Generate realistic RVTools vNetwork data for NIC '{nic_label}' on VM '{vm_name}'.
VM context: Powerstate '{power_state}', Primary IP '{primary_ip}'. NIC connected: {is_connected}. Datacenter: {datacenter}.
Consider these columns: {column_list}.
Provide values for some. Focus on 'Adapter', 'Network', 'Switch', 'Type' (e.g. VMXNET3, E1000E).
Example for 'Adapter': 'CustomNetAdapter'.
Ensure data is consistent with VM context.
"""
VCLUSTER_AI_PROMPT_TEMPLATE = """
Generate realistic RVTools vCluster data for a cluster named '{cluster_name}' in datacenter '{datacenter_name}'.
The cluster has {num_hosts} hosts, with total {total_cpu_cores} CPU cores and {total_memory_gb} GB of total memory.
Consider these columns: {column_list}.
Provide values for some. Focus on 'HA enabled', 'DRS enabled', 'DRS default VM behavior', 'AdmissionControlEnabled', 'VM Monitoring'.
Example for 'DRS default VM behavior': 'fullyAutomated' or 'manual'.
Ensure data is consistent with the provided context.
"""
VDATASTORE_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware Datastore for an RVTools vDatastore report.
Provide a realistic data profile for a single Datastore with the following context:
- Datastore Name: {datastore_name}
- Associated Datacenter (if known): {datacenter_name}
- Approximate number of VMs using this datastore: {num_vms_on_datastore}

Use these column names, ensuring all are present in your output:
{column_details_block}

Guidelines:
- 'Type' should be like 'VMFS', 'NFS', 'vSAN'.
- 'Capacity MiB', 'Free MiB', 'Provisioned MiB' should be realistic storage sizes.
- 'Maintenance Mode', 'Accessible' are boolean (true/false).
- 'Thin Provisioning Supported' is boolean.
"""
VRP_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware Resource Pool for an RVTools vRP report.
Provide a realistic data profile for a single Resource Pool with the following context:
- Resource Pool Name: {rp_name}
- Resource Pool Path: {rp_path}
- Approximate number of VMs in this RP: {num_vms_in_rp}
- Parent Cluster (if known): {parent_cluster}

Use these column names, ensuring all are present in your output:
{column_details_block}

Guidelines:
- CPU/Memory 'reservation', 'limit', 'shares', 'expandableReservation' should be realistic.
- 'Status' should be a typical RP status (e.g., 'green').
- Usage stats ('overallCpuUsage', 'guestMemoryUsage', etc.) should be plausible.
"""
VSOURCE_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware vCenter Server for an RVTools vSource report.
Provide a realistic data profile for a single vCenter Server instance with the following context:
- vCenter IP/Hostname (VI SDK Server): {vcenter_ip}
- Target vCenter Base Version (e.g., "7.0 U3", "8.0 Update 1"): {target_version}

Use these column names, ensuring all are present in your output:
{column_details_block}

Guidelines:
- 'Name' should typically match the VI SDK Server.
- 'OS type' is often 'VMware Photon OS' or similar for modern vCenters.
- 'API type' is 'VirtualCenter'.
- 'API version', 'Version', 'Patch level', 'Build', 'Fullname', 'Product name', 'Product version', 'Product line', 'Vendor' should all be consistent with the target base version.
"""
VHBA_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Host Bus Adapters (HBAs) for an RVTools vHBA report.
Provide a realistic data profile for one or more HBAs on a given host.
Host Context:
- Host Name: {host_name}
- Host ESXi Version: {esxi_version}
- Associated Cluster: {cluster_name}
- Associated Datacenter: {datacenter_name}

Requested number of HBAs to generate for this host: {num_hbas_requested}

For each HBA, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Device' name should be like 'vmhba0', 'vmhba1', etc.
- 'Type' can be 'Fibre Channel', 'iSCSI Software Adapter', 'SAS', 'RAID Controller'.
- 'Status' should be 'Online', 'Offline', 'Unknown'.
- 'Driver' and 'Model' should be plausible for the HBA type and ESXi version.
- 'WWN' (World Wide Name) should be in a valid hexadecimal format (e.g., '20:00:00:25:B5:11:22:33') if applicable (mainly for FC/iSCSI).
"""
VNIC_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Host Physical NICs for an RVTools vNIC report.
Provide a realistic data profile for one or more physical NICs on a given host.
Host Context:
- Host Name: {host_name}
- Host ESXi Version: {esxi_version}

Requested number of NICs to generate for this host: {num_nics_requested}

For each NIC, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Network Device' name should be like 'vmnic0', 'vmnic1', etc.
- 'Driver' should be a plausible NIC driver (e.g., 'ixgben', 'nmlx5_core').
- 'Speed' (e.g., '10000 Mbps'), 'Duplex' (e.g., 'Full').
- 'MAC' address must be valid.
- 'Switch' and 'Uplink port' can be physical switch details if known (e.g., from CDP/LLDP).
"""
VSCVMK_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Host VMkernel NICs for an RVTools vSC_VMK report.
Provide a realistic data profile for one or more VMkernel NICs on a given host.
Host Context:
- Host Name: {host_name}
- Host ESXi Version: {esxi_version}
- Available Physical NICs (Names): {physical_nic_names}
- Existing Port Groups (Names, if known): {port_group_names}

Requested number of VMkernel NICs to generate: {num_vmk_requested}

For each VMkernel NIC, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Device' name should be like 'vmk0', 'vmk1'.
- 'Port Group' should be a plausible name (e.g., 'Management Network', 'vMotion Network').
- 'IP Address', 'Subnet mask', 'Gateway' should be consistent for a given vmk.
- 'Services' can include 'Management', 'vMotion', 'Provisioning', 'FT Logging', 'vSAN'.
- 'MTU' is typically 1500 or 9000.
"""
VSWITCH_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Host Standard vSwitches for an RVTools vSwitch report.
Provide a realistic data profile for one or more standard vSwitches on a given host.
Host Context:
- Host Name: {host_name}
- Available Physical NICs (Names) on this host: {physical_nic_names}

Requested number of Standard vSwitches to generate: {num_vswitches_requested}

For each vSwitch, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Switch' name should be like 'vSwitch0', 'vSwitch1'.
- '# Ports', 'Free Ports' should be plausible (e.g., default 128, some free).
- Security policies ('Promiscuous Mode', 'Mac Changes', 'Forged Transmits') can be 'Accept', 'Reject', or 'Inherit from vSwitch'.
- 'Uplinks' should be a comma-separated list of names from 'Available Physical NICs'.
- 'MTU' is typically 1500 or 9000.
"""
DVSWITCH_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware Distributed vSwitch (DVS) for an RVTools dvSwitch report.
Provide a realistic data profile for one or more DVSs within a given Datacenter.
Datacenter Context:
- Datacenter Name: {datacenter_name}
- Known Hosts in this Datacenter: {host_names_in_dc}

Requested number of DVSs to generate for this Datacenter: {num_dvswitches_requested}

For each DVS, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Switch' and 'Name' are typically the DVS name.
- 'Host members' should be a comma-separated list of some known hosts.
- 'Max Ports', '# Ports', '# VMs' should be plausible.
- CDP/LACP settings should be typical values.
- 'Max MTU' is commonly 1500 or 9000.
"""
DVPORT_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Distributed Port Groups (or Ports) for an RVTools dvPort report.
Provide a realistic data profile for several Distributed Port Groups (or individual ports if more appropriate for the columns) on a given Distributed vSwitch (DVS).
DVS Context:
- DVS Name: {dvs_name}
- Datacenter: {datacenter_name}
- Max Ports on DVS: {max_ports_on_dvs}

Requested number of Port Groups/Ports to generate for this DVS: {num_items_requested}

For each item, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Port' can be a Port Group name (e.g., "DPG_VLAN100_Uplink") or a specific port key.
- 'Type' could be 'earlyBinding', 'ephemeral', 'lateBinding'.
- '# Ports' (if a port group), 'VLAN ID' (e.g., 100, or 'Trunk').
- Security policies ('Allow Promiscuous', 'Mac Changes', 'Forged Transmits') as 'true'/'false' or 'Inherit from parent'.
"""
VCD_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware Virtual Machine's CD/DVD drive for an RVTools vCD report.
Provide a realistic data profile for a single CD/DVD drive on a given VM.
VM Context:
- VM Name: {vm_name}
- Powerstate: {powerstate}
- Available Datastores for ISOs: {datastore_names}

Include these fields in your JSON output:
{column_details_block}

Guidelines:
- 'Device Node' is typically 'CD/DVD drive 1'.
- 'Connected' and 'Starts Connected' are boolean (true/false).
- 'Device Type': If connected, can be 'Client Device', 'Datastore ISO File'. If 'Datastore ISO File', provide a realistic ISO path using one of the available datastores (e.g., '[datastoreName] ISOs/some_os.iso'). If not connected, can be 'IDE' or empty.
"""
VFILEINFO_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Virtual Machine file information for an RVTools vFileInfo report.
Provide a realistic data profile for several key files associated with a given VM.
VM Context:
- VM Name: {vm_name}
- Datastore where VM resides: {datastore_name}
- Virtual Disks (Names/Paths if known, e.g., "{vm_name}.vmdk, {vm_name}_1.vmdk"): {disk_info}

For each file, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'File Name' examples: {vm_name}.vmx, {vm_name}.vmdk, {vm_name}-flat.vmdk, vmware.log, {vm_name}.nvram.
- 'File Type' examples: VMX, VMDK, LOG, NVRAM, VMSD, VMSN.
- 'File Size in bytes' should be plausible for the file type.
- 'Path' and 'Friendly Path Name' should be consistent, e.g., "[{datastore_name}] {vm_name}/{file_name}".
"""
VPARTITION_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Virtual Machine disk partitions for an RVTools vPartition report.
Provide a realistic data profile for one or more partitions on a given virtual disk.
VM & Disk Context:
- VM Name: {vm_name}
- VM Guest OS Type (e.g., "windowsGuest", "linuxGuest"): {os_type}
- Virtual Disk Label (e.g., "Hard disk 1"): {disk_label}
- Virtual Disk Capacity (MiB): {disk_capacity_mib}

For each partition, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Disk' should be a partition name like "C:\\" or "/boot" or "Partition 1".
- The sum of partition 'Capacity MiB' for a given virtual disk should generally not exceed the disk's total capacity.
- 'Consumed MiB' should be less than or equal to partition 'Capacity MiB'.
- 'Free MiB' = 'Capacity MiB' - 'Consumed MiB'.
- 'Free %' should be calculated accordingly.
"""
VSNAPSHOT_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Virtual Machine snapshots for an RVTools vSnapshot report.
Provide a realistic data profile for one or more snapshots on a given VM.
VM Context:
- VM Name: {vm_name}
- VM Creation Date: {vm_creation_date} # To ensure snapshot dates are after VM creation

Requested number of snapshots to generate for this VM (can be 0): {num_snapshots_requested}

For each snapshot, include these fields in a list of JSON objects:
{column_details_block} # Will include 'Name', 'Description', 'Date / time', 'Size MiB (vmsn)', etc.

Guidelines:
- 'Date / time' of snapshot must be after VM Creation Date.
- 'Filename' is usually related to the VM and snapshot names.
- 'Size MiB (vmsn)' and 'Size MiB (total)' should be plausible.
- 'Quiesced' is boolean (true/false).
- 'State' can be 'PoweredOff', 'PoweredOn', 'Suspended' (reflecting VM state when snapshot was taken, or 'Valid').
"""
VTOOLS_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Tools status on a Virtual Machine for an RVTools vTools report.
Provide a realistic data profile for VMware Tools on a given VM.
VM Context:
- VM Name: {vm_name}
- VM Guest OS Type (e.g., "windowsGuest", "linuxGuest"): {os_type}
- VM Hardware Version (e.g., "vmx-19"): {hw_version}

Include these fields in your JSON output:
{column_details_block}

Guidelines:
- 'Tools' status: e.g., 'OK', 'Not running', 'Out of date', 'Not installed'.
- 'Tools Version': e.g., "12102", "11392". Should be consistent with 'Tools' status (e.g., blank if not installed).
- 'Required Version': Can be similar to Tools Version or slightly higher if an upgrade is pending.
- 'Upgradeable': boolean (true/false).
- 'Upgrade Policy': e.g., 'manual', 'upgradeAtPowerCycle'.
- 'Sync time', 'App status', 'Heartbeat status': Reflect current state.
"""
VUSB_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware Virtual Machine's USB devices for an RVTools vUSB report.
Provide a realistic data profile for one or more USB devices connected to a given VM (or an empty list if none).
VM Context:
- VM Name: {vm_name}

Requested number of USB devices to generate for this VM (can be 0): {num_usb_requested}

For each USB device, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Device Node': e.g., "USB 1", "USB Controller".
- 'Device Type': e.g., "Generic USB Device", "USB Flash Drive", "USB Keyboard".
- 'Connected', 'EHCI enabled', 'Auto connect': boolean (true/false).
- 'Family': e.g., "storage", "hid", "audio", "other".
- 'Speed': e.g., "1.1", "2.0", "3.0".
"""
VHEALTH_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware vCenter health statuses for an RVTools vHealth report.
Provide a realistic data profile for several typical vCenter health checks or alarms.
vCenter Context:
- vCenter Version: {vcenter_version}
- Number of Clusters: {num_clusters}
- Number of Hosts: {num_hosts}
- Number of VMs: {num_vms}

Requested number of health items to generate: {num_items_requested}

For each health item, include these fields in a list of JSON objects:
{column_details_block} # Will include 'Name', 'Message', 'Message type'

Guidelines:
- 'Name': Name of the health check or alarm (e.g., "Datastore usage on disk", "Host connection and power state", "VMware Tools version monitoring").
- 'Message': A descriptive message (e.g., "Datastore usage is green", "Host is responding and connected", "VMware Tools is current").
- 'Message type': 'Info', 'Warning', 'Error', 'Alarm', 'Green', 'Yellow', 'Red'.
"""
VLICENSE_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware product licenses for an RVTools vLicense report.
Provide a realistic data profile for several typical VMware licenses in an environment.
Environment Context:
- vCenter Version: {vcenter_version}
- Number of ESXi Hosts: {num_hosts}
- Total Physical CPU Sockets across all hosts: {total_cpu_sockets}
- vSAN Enabled (true/false): {vsan_enabled} # To suggest vSAN license

Requested number of distinct license types to generate: {num_license_types_requested}

For each license, include these fields in a list of JSON objects:
{column_details_block} # Will include 'Name', 'Key', 'Total', 'Used', 'Expiration Date', 'Features'

Guidelines:
- 'Name': e.g., "VMware vCenter Server 8 Standard", "VMware vSphere 8 Enterprise Plus", "VMware vSAN 8 Standard".
- 'Key': A plausible (but fake) license key format (e.g., "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX").
- 'Total': Number of licenses (e.g., 1 for vCenter, total CPU sockets for ESXi).
- 'Used': Number of licenses used (<= Total).
- 'Expiration Date': A future date, or "Never".
- 'Features': Comma-separated list of key features provided by the license.
"""
VMULTIPATH_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Host Storage Multipathing for an RVTools vMultiPath report.
Provide a realistic data profile for one or more LUNs/disks with multipathing information on a given host, potentially associated with specific datastores.
Host & Storage Context:
- Host Name: {host_name}
- Datastore(s) this host might see: {datastore_names_list} # Comma-separated
- Known HBAs on this host (Names/WWNs): {hba_info_list} # Comma-separated

Requested number of multipathed LUNs/disks to generate for this host: {num_luns_requested}

For each LUN/disk, include these fields in a list of JSON objects:
{column_details_block} # Will include 'Disk' (naa.xxx), 'Policy', 'Path 1', 'Path 1 state', etc.

Guidelines:
- 'Disk' (Device Name) should be a valid NAA identifier (e.g., "naa.6006016012345678123456789abcdef0").
- 'Policy': e.g., "VMW_PSP_RR", "VMW_PSP_MRU", "VMW_PSP_FIXED".
- 'Oper. State': e.g., "Active", "Standby", "Disabled", "Dead".
- For 'Path X' and 'Path X state', provide details for 2-4 paths. Path names can be complex (e.g., "fc.adapter_wwn:target_wwn:lun_id" or "iqn.xxxx:target_iqn:lun_id").
"""

VPORT_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Standard vSwitch Port Groups for an RVTools vPort report.
Provide a realistic JSON data profile for one or more Port Groups on a given Standard vSwitch.
Host & vSwitch Context:
- Host Name: {host_name}
- Standard vSwitch Name: {vswitch_name}
- Uplinks on this vSwitch: {uplink_names} # Comma-separated

Requested number of Port Groups to generate for this vSwitch: {num_pg_requested}

For each Port Group, include these fields in a list of JSON objects:
{column_details_block} # Will include 'Port Group', 'Switch', 'VLAN', security policies etc.

Guidelines:
- 'Port Group': Name of the port group (e.g., "VM Network", "Management Network", "VLAN100_PG").
- 'VLAN': VLAN ID (e.g., "100") or "Trunk" or "None".
- Security policies ('Promiscuous Mode', 'Mac Changes', 'Forged Transmits') can be 'Accept', 'Reject'.
- Traffic Shaping fields: 'Enabled' (true/false), 'Width' (Avg Bps), 'Peak' (Peak Bps), 'Burst' (Burst KiB).
"""

# --- Utility Functions ---
def generate_random_string(length=10, prefix=""):
    chars = string.ascii_letters + string.digits;
    if len(prefix) > length: prefix = prefix[:length]
    return prefix + ''.join(random.choice(chars) for _ in range(length - len(prefix)))
def generate_random_boolean(): return random.choice([True, False])
def generate_random_integer(min_val=0, max_val=100): return random.randint(min_val, max_val)
def generate_random_ip_address(): return f"{random.randint(1,254)}.{random.randint(0,254)}.{random.randint(0,254)}.{random.randint(1,254)}"
def generate_random_mac_address(): return "00:50:56:%02x:%02x:%02x" % (random.randint(0,0xff), random.randint(0,0xff), random.randint(0,0xff))
def generate_random_datetime(start_date_str="2022/01/01 00:00:00", days_range=365*2):
    date_format = "%Y/%m/%d %H:%M:%S";
    start_date = datetime.strptime(start_date_str, date_format)
    time_difference = timedelta(seconds=random.randint(0, days_range * 24 * 60 * 60))
    return (start_date + time_difference).strftime(date_format)
def choose_random_from_list(item_list): return random.choice(item_list) if item_list else ""
def generate_vm_name(prefix="vm-"): return generate_random_string(length=10, prefix=prefix)
def generate_uuid(): return str(uuid.uuid4())

def _get_column_descriptions_for_prompt(columns, max_cols=20):
    # For generic prompts, select a random subset of columns
    if len(columns) <= max_cols: return ", ".join(columns)
    return ", ".join(random.sample(columns, max_cols))

def _get_vinfo_column_descriptions_for_prompt(): # Specific for vInfo
    return ", ".join(CSV_HEADERS.get('vInfo', []))
def _get_vdatastore_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vDatastore', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vrp_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vRP', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vsource_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vSource', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vhba_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vHBA', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vnic_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vNIC', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vscvmk_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vSC_VMK', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vswitch_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vSwitch', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_dvswitch_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('dvSwitch', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_dvport_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('dvPortGroup', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vcd_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vCD', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vfileinfo_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vFileInfo', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vpartition_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vPartition', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vsnapshot_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vSnapshot', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vtools_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vTools', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vusb_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vUSB', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vhealth_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vHealth', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vlicense_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vLicense', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vmultipath_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vMultiPath', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vport_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vPort', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])

# --- AI Data Dispatcher & Mock AI Row Generation Functions ---
def _get_ai_data_for_entity(prompt_template, context, relevant_headers_key, entity_name_for_log, ai_provider="mock", entity_specific_mock_func=None):
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if relevant_headers_key == "vInfo" and openai_api_key: # Future: and args.ai_provider == 'openai'
        print(f"\nAttempting REAL OpenAI call for {entity_name_for_log} ({relevant_headers_key})...")
        try:
            client = openai.OpenAI(api_key=openai_api_key)

            system_message_content = "You are an AI assistant helping to generate synthetic data for a VMware vSphere environment export. Output should be a single, valid JSON object."

            # Ensure context has the column list/details for the prompt
            if relevant_headers_key == "vInfo": # vInfo prompt uses 'column_details_block'
                 context['column_details_block'] = _get_vinfo_column_descriptions_for_prompt()
            elif 'column_details_block' not in context and 'column_list' not in context : # Generic fallback
                 context['column_list'] = _get_column_descriptions_for_prompt(CSV_HEADERS.get(relevant_headers_key, []))

            user_prompt_content = prompt_template.format(**context)
            if "Provide ONLY the JSON object as your response." not in user_prompt_content: # Ensure instruction is present
                 user_prompt_content += "\nProvide ONLY the JSON object as your response."

            completion = client.chat.completions.create(
                model="gpt-4o-mini", # Changed model
                messages=[
                    {"role": "system", "content": system_message_content},
                    {"role": "user", "content": user_prompt_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )

            ai_response_content = completion.choices[0].message.content
            print(f"OpenAI response for {entity_name_for_log}: {ai_response_content[:200]}...")

            ai_data = json.loads(ai_response_content)

            if relevant_headers_key == "vInfo":
                critical_fields = ["VM", "Powerstate", "CPUs", "Memory"]
                missing_critical = [field for field in critical_fields if field not in ai_data]
                if missing_critical:
                    print(f"Warning: AI response for vInfo {entity_name_for_log} is missing critical fields: {missing_critical}. May fall back more heavily on mock/random for these.")

                if "CPUs" in ai_data and not isinstance(ai_data["CPUs"], int):
                    print(f"Warning: AI returned non-integer for CPUs in vInfo {entity_name_for_log}: {ai_data['CPUs']}. Attempting to cast or will use fallback.")
                    try: ai_data["CPUs"] = int(ai_data["CPUs"])
                    except (ValueError, TypeError):
                        print(f"Could not cast CPUs to int. Will rely on fallback for CPUs.")
                        if "CPUs" in ai_data: del ai_data["CPUs"]

                if "Memory" in ai_data and not isinstance(ai_data["Memory"], int):
                    print(f"Warning: AI returned non-integer for Memory in vInfo {entity_name_for_log}: {ai_data['Memory']}. Attempting to cast or will use fallback.")
                    try: ai_data["Memory"] = int(ai_data["Memory"])
                    except (ValueError, TypeError):
                        print(f"Could not cast Memory to int. Will rely on fallback for Memory.")
                        if "Memory" in ai_data: del ai_data["Memory"]
            return ai_data
        except Exception as e:
            print(f"Error during OpenAI API call for {entity_name_for_log}: {e}")
            print(f"Falling back to mock data for {entity_name_for_log}.")

    if entity_specific_mock_func:
        # Ensure context for mock has what it needs, if different from prompt_context
        if 'column_list' not in context and 'column_details_block' not in context and relevant_headers_key != "vInfo": # Generic fallback for non-vInfo mocks
             context['column_list'] = _get_column_descriptions_for_prompt(CSV_HEADERS.get(relevant_headers_key,[]))
        elif relevant_headers_key == "vInfo" and 'column_details_block' not in context: # Ensure vInfo mock context also gets its details
             context['column_details_block'] = _get_vinfo_column_descriptions_for_prompt()

        return entity_specific_mock_func(context)
    else:
        print(f"Warning: No entity_specific_mock_func provided for {entity_name_for_log}")
        return {}

def generate_vinfo_row_ai(vm_r_context):
    def _create_vinfo_mock_data(context_for_mock):
        return {
            "Annotation": f"AI: VM {context_for_mock.get('suggested_vm_name','mock-vm')} - OS: {context_for_mock.get('os_tools','N/A')}. Purpose: {choose_random_from_list(['AI_WebApp', 'AI_DB', 'AI_Analytics'])}",
            "Firmware": choose_random_from_list(["bios", "efi"]),
            "HW version": choose_random_from_list(["vmx-17", "vmx-19", "vmx-20"]),
            "Resource pool": f"/{context_for_mock.get('associated_datacenter','DC1')}/{context_for_mock.get('associated_cluster','Clus1')}/Resources/AI-Pool-{generate_random_string(3)}",
            "Folder": f"/{context_for_mock.get('associated_datacenter','DC1')}/vm/AI-Managed/{generate_random_string(3)}/",
            "Total disk capacity MiB": generate_random_integer(context_for_mock.get("memory_gb", 2) * 10 * 1024, context_for_mock.get("memory_gb", 2) * 50 * 1024),
            "Heartbeat": "gray" if context_for_mock.get("power_state") == "poweredOff" else choose_random_from_list(["green", "yellow", "red"]),
            "VM": context_for_mock.get('suggested_vm_name','mock-vm-fallback'),
            "Powerstate": context_for_mock.get('power_state','poweredOn'),
            "CPUs": context_for_mock.get('cpus', generate_random_integer(1,4)),
            "Memory": context_for_mock.get('memory_gb', 2) * 1024,
        }

    prompt_context = {
        'suggested_vm_name': vm_r_context.get('VM'),
        'associated_host': vm_r_context.get('Host'),
        'associated_cluster': vm_r_context.get('Cluster'),
        'associated_datacenter': vm_r_context.get('Datacenter'),
        'power_state': vm_r_context.get('Powerstate'),
        'os_tools': vm_r_context.get('OS according to the VMware Tools'),
        'memory_gb': vm_r_context.get('Memory', 2048) // 1024,
        'cpus': vm_r_context.get('CPUs', 2)
    }
    return _get_ai_data_for_entity(VINFO_AI_PROMPT_TEMPLATE, prompt_context, "vInfo", vm_r_context.get('VM', "UnknownVM_vInfo"), entity_specific_mock_func=_create_vinfo_mock_data)

def generate_vhost_row_ai(host_r_context):
    def _create_vhost_mock_data(context_for_mock):
        return {
            "Vendor": "AI Vendor-" + choose_random_from_list(["DellAI", "HPAI", "SupermicroAI"]),
            "Model": "AI Model-" + context_for_mock.get('cpu_model',"UnknownCPU").split(" ")[0] + "_" + generate_random_string(4),
            "Time Zone Name": choose_random_from_list(["America/Los_Angeles", "Europe/Berlin", "Asia/Tokyo"]),
            "NTP Server(s)": "0.ai.pool.ntp.org, 1.ai.pool.ntp.org",
            "BIOS Vendor": choose_random_from_list(["AI BIOS Inc.", "Future Systems AI"]),
            "BIOS Version": generate_random_string(prefix="AI-BIOS-", length=12),
            "BIOS Date": generate_random_datetime(start_date_str="2022/01/01"),
            "Service tag": generate_random_string(7).upper()+"-AI",
        }
    prompt_context = {
        'host_name': host_r_context.get('Host'),
        'cluster_name': host_r_context.get('Cluster'),
        'datacenter_name': host_r_context.get('Datacenter'),
        'cpu_count': host_r_context.get('# CPU'),
        'cores_per_cpu': host_r_context.get('Cores per CPU'),
        'memory_mb': host_r_context.get('# Memory'),
        'esx_version': host_r_context.get('ESX Version'),
        'cpu_model': host_r_context.get('CPU Model')
    }
    return _get_ai_data_for_entity(VHOST_AI_PROMPT_TEMPLATE, prompt_context, "vHost", host_r_context.get('Host', "UnknownHost_vHost"), entity_specific_mock_func=_create_vhost_mock_data)

def generate_vdisk_row_ai(vm_r_context, disk_index, disk_label_for_prompt):
    def _create_vdisk_mock_data(context_for_mock):
        is_thin = generate_random_boolean()
        return {
            "Disk Mode": choose_random_from_list(["persistent", "independent_persistent", "independent_nonpersistent"]),
            "Sharing mode": choose_random_from_list(["nobussharing", "virtualsharing", "physicalsharing"]),
            "Thin": str(is_thin),
            "Eagerly Scrub": str(generate_random_boolean() if not is_thin else False),
            "Controller": f"AI SCSI Controller {context_for_mock.get('disk_index',0)}",
        }
    prompt_context = {
        'vm_name': vm_r_context.get('VM'),
        'power_state': vm_r_context.get('Powerstate'),
        'datastore': vm_r_context.get('Datastore'),
        'disk_label': disk_label_for_prompt,
        'disk_index': disk_index
    }
    return _get_ai_data_for_entity(VDISK_AI_PROMPT_TEMPLATE, prompt_context, "vDisk", f"{vm_r_context.get('VM', 'UnknownVM')}-{disk_label_for_prompt}", entity_specific_mock_func=_create_vdisk_mock_data)

def generate_vnetwork_row_ai(vm_r_context, nic_index, nic_label_for_prompt):
    def _create_vnetwork_mock_data(context_for_mock):
        return {
            "Adapter": choose_random_from_list(["VMXNET3-AI", "E1000E-AI", "SRIOV-AI"]),
            "Network": f"{context_for_mock.get('datacenter','DC1')}-AISegment-{generate_random_integer(200,299)}",
            "Switch": f"AI-DVSwitch-{context_for_mock.get('datacenter','DC1')}",
            "Type": "AI Ethernet",
        }
    prompt_context = {
        'vm_name': vm_r_context.get('VM'),
        'power_state': vm_r_context.get('Powerstate'),
        'primary_ip': vm_r_context.get('Primary IP Address', "N/A"),
        'is_connected': str(vm_r_context.get("Powerstate") == "poweredOn"),
        'datacenter': vm_r_context.get('Datacenter'),
        'nic_label': nic_label_for_prompt,
        'nic_index': nic_index
    }
    return _get_ai_data_for_entity(VNETWORK_AI_PROMPT_TEMPLATE, prompt_context, "vNetwork", f"{vm_r_context.get('VM', 'UnknownVM')}-{nic_label_for_prompt}", entity_specific_mock_func=_create_vnetwork_mock_data)

def generate_vcluster_row_ai(cluster_r_context):
    def _create_vcluster_mock_data(context_for_mock):
        return {
            "HA enabled": str(generate_random_boolean()),
            "DRS enabled": str(generate_random_boolean()),
            "DRS default VM behavior": choose_random_from_list(["fullyAutomated", "manual", "partiallyAutomated"]),
            "AdmissionControlEnabled": str(generate_random_boolean()),
            "VM Monitoring": choose_random_from_list(["vmMonitoringDisabled", "vmMonitoringOnly", "vmAndAppMonitoring"]),
        }
    prompt_context = {
        'cluster_name': cluster_r_context.get('Name'),
        'datacenter_name': cluster_r_context.get('Datacenter'),
        'num_hosts': cluster_r_context.get('NumHosts',0),
        'total_cpu_cores': cluster_r_context.get('NumCpuCores',0),
        'total_memory_gb': cluster_r_context.get('TotalMemoryGB',0)
    }
    return _get_ai_data_for_entity(VCLUSTER_AI_PROMPT_TEMPLATE, prompt_context, "vCluster", cluster_r_context.get("Name", "UnknownCluster"), entity_specific_mock_func=_create_vcluster_mock_data)

def generate_vdatastore_row_ai(ds_agg_data_context):
    def _create_vdatastore_mock_data(context_for_mock):
        ds_type = choose_random_from_list(['VMFS', 'NFS', 'vSAN'])
        capacity_mib = generate_random_integer(1 * 1024 * 1024, 10 * 1024 * 1024)
        free_mib = generate_random_integer(int(capacity_mib * 0.1), int(capacity_mib * 0.8))
        provisioned_mib = capacity_mib - free_mib + generate_random_integer(0, int(capacity_mib*0.2))
        return {
            "Name": context_for_mock.get("datastore_name", "UnknownDS"), "Config status": "green",
            "Address": f"nfs://ai-filer.corp.local:/vol/{context_for_mock.get('datastore_name')}" if ds_type == 'NFS' else (f"vsan:{generate_uuid()}" if ds_type == 'vSAN' else ""),
            "Accessible": "true", "Type": ds_type, "Capacity MiB": str(capacity_mib), "Provisioned MiB": str(provisioned_mib),
            "In Use MiB": str(provisioned_mib - free_mib if provisioned_mib > free_mib else generate_random_integer(0, provisioned_mib)),
            "Free MiB": str(free_mib), "Free %": str(round((free_mib / capacity_mib) * 100, 1) if capacity_mib > 0 else 0),
            "SIOC enabled": "false", "SIOC Threshold": "30",
            "VMFS Upgradeable": "true" if ds_type == 'VMFS' else "false",
            "URL": f"ds:///vmfs/volumes/{generate_uuid()}/" if ds_type == 'VMFS' else (f"ds://vsan/{context_for_mock.get('datastore_name')}" if ds_type == 'vSAN' else ""),
            "Object ID": f"datastore-ai-{generate_random_integer(1000,1999)}",
        }
    return _get_ai_data_for_entity(VDATASTORE_AI_PROMPT_TEMPLATE, ds_agg_data_context, "vDatastore", ds_agg_data_context.get('datastore_name', "UnknownDS"), entity_specific_mock_func=_create_vdatastore_mock_data)

def generate_vrp_row_ai(rp_context_param):
    def _create_vrp_mock_data(context_for_mock):
        return {
            "Status": "green", "CPU limit": -1, "CPU reservation": generate_random_integer(1000, 5000), "CPU shares": "normal", "CPU level": "normal",
            "CPU expandableReservation": json.dumps(generate_random_boolean()),
            "Mem limit": -1, "Mem reservation": generate_random_integer(4096, 16384), "Mem shares": "normal", "Mem level": "normal",
            "Mem expandableReservation": json.dumps(generate_random_boolean()),
            "overallCpuUsage": generate_random_integer(500, 2000), "guestMemoryUsage": generate_random_integer(1024, 8192),
            "QS overallCpuDemand": generate_random_integer(600,2500), "QS guestMemoryUsage": generate_random_integer(1000,8000),
        }
    return _get_ai_data_for_entity(VRP_AI_PROMPT_TEMPLATE, rp_context_param, "vRP", rp_context_param.get('rp_name',"UnknownRP"), entity_specific_mock_func=_create_vrp_mock_data)

def generate_vsource_row_ai(vsource_context_param):
    def _create_vsource_mock_data(context_for_mock):
        ver_parts = context_for_mock.get('target_version',"8.0 U1").split(' ')
        base_ver = ver_parts[0]
        patch_str = "".join(ver_parts[1:]) if len(ver_parts) > 1 else ""
        build = generate_random_integer(20000000, 23000000)
        return {
            "Name": context_for_mock.get('vcenter_ip', "vcenter.mock.local"), "OS type": "VMware Photon OS (AI Generated)", "API type": "VirtualCenter",
            "API version": f"{base_ver}.{patch_str[1] if patch_str.startswith('U') and len(patch_str)>1 else '0'}",
            "Version": base_ver, "Patch level": patch_str, "Build": str(build),
            "Fullname": f"VMware vCenter Server {context_for_mock.get('target_version')} build-{build} (AI)",
            "Product name": "VMware vCenter Server (AI Edition)", "Product version": f"{context_for_mock.get('target_version')} (AI)",
            "Product line": "vpx", "Vendor": "VMware, Inc. (AI Verified)"
        }
    return _get_ai_data_for_entity(VSOURCE_AI_PROMPT_TEMPLATE, vsource_context_param, "vSource", vsource_context_param.get('vcenter_ip',"UnknownVC"), entity_specific_mock_func=_create_vsource_mock_data)

def generate_vhba_row_ai(vhba_context_param):
    def _create_vhba_mock_data(context_for_mock):
        hba_list = []
        for i in range(context_for_mock.get('num_hbas_requested', 1)):
            hba_type = choose_random_from_list(['Fibre Channel', 'iSCSI Software Adapter', 'SAS Controller', 'RAID Controller'])
            device_name = f"vmhba{i}"
            wwn = ""
            if hba_type == 'Fibre Channel':
                driver, model = choose_random_from_list([('lpfc','Emulex LightPulse LPe32002-AI'),('qlnativefc','QLogic QLE2772-AI')])
                wwn = ":".join([generate_random_string(2, prefix='').lower() for _ in range(8)])
            elif hba_type == 'iSCSI Software Adapter':
                driver, model = 'iscsi_vmk', 'iSCSI Software Adapter AI'
                wwn = f"iqn.1998-01.com.vmware:{context_for_mock.get('host_name','unknownhost')}-ai-{generate_random_string(8).lower()}"
            else:
                driver, model = choose_random_from_list([('lsi_mr3s','PERC H740P AI'),('smartpqi','Smart Array P408i-a AI')])
            hba_list.append({
                "Device": device_name, "Type": hba_type, "Status": "Online",
                "Driver": driver, "Model": model, "WWN": wwn,
                "Bus": str(generate_random_integer(0,3)),
                "Pci": f"0000:0{generate_random_integer(1,9)}:00.{i}"
            })
        return hba_list
    return _get_ai_data_for_entity(VHBA_AI_PROMPT_TEMPLATE, vhba_context_param, "vHBA", vhba_context_param.get('host_name',"UnknownHost_HBA"), entity_specific_mock_func=_create_vhba_mock_data)

def generate_vnic_row_ai(vnic_context_param):
    def _create_vnic_mock_data(context_for_mock):
        nic_list = []
        for i in range(context_for_mock.get('num_nics_requested',1)):
            speed_val = choose_random_from_list([1000, 10000, 25000, 40000])
            nic_list.append({
                "Network Device": f"vmnic{i}",
                "Driver": choose_random_from_list(['ixgben-ai', 'nmlx5_core-ai', 'bnxtnet-ai']),
                "Speed": f"{speed_val} Mbps", "Duplex": "Full", "MAC": generate_random_mac_address(),
                "Switch": f"PhysicalSwitch-AI-{chr(65+i)}",
                "Uplink port": f"Gi{generate_random_integer(1,2)}/0/{generate_random_integer(1,24)}",
                "PCI": f"0000:0{generate_random_integer(1,18)}:00.{i}",
                "WakeOn": json.dumps(generate_random_boolean())
            })
        return nic_list
    return _get_ai_data_for_entity(VNIC_AI_PROMPT_TEMPLATE, vnic_context_param, "vNIC", vnic_context_param.get('host_name',"UnknownHost_NIC"), entity_specific_mock_func=_create_vnic_mock_data)

def generate_vscvmk_row_ai(vmk_context_param):
    def _create_vscvmk_mock_data(context_for_mock):
        vmk_list = []
        base_ip_parts = generate_random_ip_address().split('.')
        for i in range(context_for_mock.get('num_vmk_requested',1)):
            services = []
            if i == 0 : services.append("Management")
            if generate_random_boolean(): services.append("vMotion")
            if generate_random_boolean() and context_for_mock.get('datastore_types_on_host',[]).count('vSAN') > 0 : services.append("vSAN")
            vmk_list.append({
                "Device": f"vmk{i}", "Port Group": f"{services[0] if services else 'VMkernel'}-PG-AI",
                "Mac Address": generate_random_mac_address(), "DHCP": json.dumps(False),
                "IP Address": f"{base_ip_parts[0]}.{base_ip_parts[1]}.{generate_random_integer(10,200)}.{generate_random_integer(10,250)}",
                "Subnet mask": "255.255.255.0", "Gateway": f"{base_ip_parts[0]}.{base_ip_parts[1]}.{base_ip_parts[2]}.1",
                "MTU": choose_random_from_list([1500, 9000]), "Services": ", ".join(services) if services else "VMkernel"
            })
        return vmk_list
    return _get_ai_data_for_entity(VSCVMK_AI_PROMPT_TEMPLATE, vmk_context_param, "vSC_VMK", vmk_context_param.get('host_name',"UnknownHost_VMK"), entity_specific_mock_func=_create_vscvmk_mock_data)

def generate_vswitch_row_ai(vswitch_context_param):
    def _create_vswitch_mock_data(context_for_mock):
        vswitch_list = []
        phys_nics = context_for_mock.get('physical_nic_names', [])
        for i in range(context_for_mock.get('num_vswitches_requested',1)):
            num_uplinks_for_switch = generate_random_integer(1, len(phys_nics) if phys_nics else 1)
            selected_uplinks_for_switch = random.sample(phys_nics, min(num_uplinks_for_switch, len(phys_nics))) if phys_nics else [f"vmnic{j+i*2}" for j in range(num_uplinks_for_switch)]
            vswitch_list.append({
                "Switch": f"vSwitch{i}-AI", "# Ports": 128, "Free Ports": generate_random_integer(60,120),
                "Promiscuous Mode": "Reject", "Mac Changes": "Accept", "Forged Transmits": "Accept",
                "Uplinks": ",".join(selected_uplinks_for_switch), "MTU": 1500 })
        return vswitch_list
    return _get_ai_data_for_entity(VSWITCH_AI_PROMPT_TEMPLATE, vswitch_context_param, "vSwitch", vswitch_context_param.get('host_name',"UnknownHost_vSwitch"), entity_specific_mock_func=_create_vswitch_mock_data)

def generate_dvswitch_row_ai(dvswitch_context_param):
    def _create_dvswitch_mock_data(context_for_mock):
        dvswitch_list = []
        host_names = context_for_mock.get('host_names_in_dc', [])
        for i in range(context_for_mock.get('num_dvswitches_requested',1)):
            dvs_name = f"DVS_{context_for_mock.get('datacenter_name','DC1')}_AI_{i+1}"
            selected_hosts = random.sample(host_names, k=min(len(host_names), generate_random_integer(1, len(host_names)))) if host_names else []
            dvswitch_list.append({
                "Switch": dvs_name, "Name": dvs_name, "Datacenter": context_for_mock.get('datacenter_name'),
                "Vendor": "VMware AI", "Version": choose_random_from_list(["7.0.3 AI", "8.0.1 AI"]),
                "Host members": ",".join(selected_hosts),
                "Max Ports": str(generate_random_integer(512, 8192)),
                "# Ports": str(generate_random_integer(128, 512)),
                "# VMs": str(generate_random_integer(0, 200)),
                "CDP Type": choose_random_from_list(["listen", "advertise", "both", "disabled"]),
                "Max MTU": str(choose_random_from_list([1500,9000,9216])),
                "Object ID": f"dvs-ai-{generate_random_integer(100,199)}"
            })
        return dvswitch_list
    return _get_ai_data_for_entity(DVSWITCH_AI_PROMPT_TEMPLATE, dvswitch_context_param, "dvSwitch", dvswitch_context_param.get('datacenter_name',"UnknownDC_DVS"), entity_specific_mock_func=_create_dvswitch_mock_data)

def generate_dvport_row_ai(dvport_context_param):
    def _create_dvport_mock_data(context_for_mock):
        dvport_list = []
        for i in range(context_for_mock.get('num_items_requested',1)):
            vlan_id = generate_random_integer(100, 199)
            dvport_list.append({
                "Name": f"DPG_VLAN{vlan_id}_AI_{i}",
                "Switch": context_for_mock.get('dvs_name'),
                "Port Binding": choose_random_from_list(["staticBinding", "dynamicBinding", "ephemeral"]),
                "VLAN": f"VLAN {vlan_id}", "VLAN type": "VLAN",
                "# Ports": str(choose_random_from_list([0, 8, 16, 24, 64, 128, 256])),
                "Allow Promiscuous": json.dumps(False),
                "Mac Changes": json.dumps(True),
                "Forged Transmits": json.dumps(True),
                "Object ID": f"dvportgroup-ai-{generate_random_integer(100,199)}"
            })
        return dvport_list
    return _get_ai_data_for_entity(DVPORT_AI_PROMPT_TEMPLATE, dvport_context_param, "dvPortGroup", dvport_context_param.get('dvs_name',"UnknownDVS_DPG"), entity_specific_mock_func=_create_dvport_mock_data)

def generate_vcd_row_ai(vcd_context_param):
    def _create_vcd_mock_data(context_for_mock):
        connected = generate_random_boolean()
        device_type = "Client Device"
        if connected:
            if generate_random_boolean() and context_for_mock.get('datastore_names'):
                ds_name = random.choice(context_for_mock['datastore_names'])
                iso_file = choose_random_from_list(["windows_server_2022.iso", "ubuntu-desktop.iso", "vmware-tools.iso", "custom_app.iso"])
                device_type = f"[{ds_name}] ISOs/{iso_file}"
        else:
            device_type = choose_random_from_list(["IDE", ""])
        return {
            "Device Node": "CD/DVD drive 1 (AI)", "Connected": json.dumps(connected),
            "Starts Connected": json.dumps(connected if generate_random_boolean() else False),
            "Device Type": device_type, "Annotation": f"AI configured CD Drive for {context_for_mock.get('vm_name','UnknownVM')}"
        }
    return _get_ai_data_for_entity(VCD_AI_PROMPT_TEMPLATE, vcd_context_param, "vCD", vcd_context_param.get('vm_name',"UnknownVM_CD"), entity_specific_mock_func=_create_vcd_mock_data)

def generate_vfileinfo_row_ai(file_info_context_param):
    def _create_vfileinfo_mock_data(context_for_mock):
        vm_name = context_for_mock.get('vm_name','UnknownVM'); datastore = context_for_mock.get('datastore_name','UnknownDS')
        disks = context_for_mock.get('disk_info_list', [f"{vm_name}.vmdk"])
        files = []
        files.append({"File Name": f"{vm_name}.vmx", "File Type": "VMX (AI)", "File Size in bytes": generate_random_integer(3000, 9000), "Path": f"[{datastore}] {vm_name}/{vm_name}.vmx"})
        files.append({"File Name": f"{vm_name}.nvram", "File Type": "NVRAM (AI)", "File Size in bytes": generate_random_integer(8192, 65536), "Path": f"[{datastore}] {vm_name}/{vm_name}.nvram"})
        for disk_path_name in disks:
            actual_disk_name = disk_path_name.split('/')[-1] if '/' in disk_path_name else disk_path_name
            files.append({"File Name": actual_disk_name, "File Type": "VMDK Descriptor (AI)", "File Size in bytes": generate_random_integer(1000, 5000), "Path": f"[{datastore}] {vm_name}/{actual_disk_name}"})
            files.append({"File Name": actual_disk_name.replace('.vmdk', '-flat.vmdk'), "File Type": "VMDK Flat (AI)", "File Size in bytes": generate_random_integer(10*1024*1024, 100*1024*1024*1024), "Path": f"[{datastore}] {vm_name}/{actual_disk_name.replace('.vmdk','-flat.vmdk')}"})
        return files
    return _get_ai_data_for_entity(VFILEINFO_AI_PROMPT_TEMPLATE, file_info_context_param, "vFileInfo", file_info_context_param.get('vm_name',"UnknownVM_Files"), entity_specific_mock_func=_create_vfileinfo_mock_data)

def generate_vpartition_row_ai(partition_context_param):
    def _create_vpartition_mock_data(context_for_mock):
        partitions = []
        disk_cap_mib = context_for_mock.get('disk_capacity_mib', 10240)
        num_partitions_ai = generate_random_integer(1,2)
        if num_partitions_ai == 1:
            cap = disk_cap_mib; cons = int(cap * random.uniform(0.1, 0.9))
            partitions.append({"Disk": "C:\\ (AI)" if "win" in context_for_mock.get('os_type','').lower() else "/ (AI)", "Capacity MiB": cap, "Consumed MiB": cons})
        elif num_partitions_ai == 2:
            cap1 = int(disk_cap_mib * random.uniform(0.3, 0.7)); cons1 = int(cap1 * random.uniform(0.1, 0.9))
            cap2 = disk_cap_mib - cap1; cons2 = int(cap2 * random.uniform(0.1, 0.9))
            partitions.append({"Disk": "C:\\ (AI)" if "win" in context_for_mock.get('os_type','').lower() else "/ (AI)", "Capacity MiB": cap1, "Consumed MiB": cons1})
            partitions.append({"Disk": "D:\\ (AI)" if "win" in context_for_mock.get('os_type','').lower() else "/var (AI)", "Capacity MiB": cap2, "Consumed MiB": cons2})
        return partitions
    return _get_ai_data_for_entity(VPARTITION_AI_PROMPT_TEMPLATE, partition_context_param, "vPartition", f"{partition_context_param.get('vm_name','UnkVm')}_{partition_context_param.get('disk_label','UnkDisk')}", entity_specific_mock_func=_create_vpartition_mock_data)

def generate_vsnapshot_row_ai(snapshot_context_param):
    def _create_vsnapshot_mock_data(context_for_mock):
        snap_list = []
        num_snaps = context_for_mock.get('num_snapshots_requested', 0)
        vm_creation_dt = datetime.strptime(context_for_mock.get('vm_creation_date', "2020/01/01 00:00:00"), "%Y/%m/%d %H:%M:%S")
        for i in range(num_snaps):
            snap_date = vm_creation_dt + timedelta(days=generate_random_integer(1, 30), hours=generate_random_integer(1,23))
            snap_name = f"AI_Snapshot_{i+1}_of_{context_for_mock.get('vm_name','UnknownVM')}"
            snap_list.append({
                "Name": snap_name, "Description": f"AI generated snapshot {i+1}",
                "Date / time": snap_date.strftime("%Y/%m/%d %H:%M:%S"),
                "Size MiB (vmsn)": generate_random_integer(100,2048),
                "Size MiB (total)": generate_random_integer(2000,20480),
                "Quiesced": json.dumps(generate_random_boolean()),
                "State": choose_random_from_list(["PoweredOff", "PoweredOn", "Suspended", "Valid"])
            })
        return snap_list
    return _get_ai_data_for_entity(VSNAPSHOT_AI_PROMPT_TEMPLATE, snapshot_context_param, "vSnapshot", snapshot_context_param.get('vm_name',"UnknownVM_Snap"), entity_specific_mock_func=_create_vsnapshot_mock_data)

def generate_vtools_row_ai(vtools_context_param):
    def _create_vtools_mock_data(context_for_mock):
        tools_status = choose_random_from_list(['OK', 'Not running', 'Out of date', 'Not installed'])
        tools_version = ""
        if tools_status != "Not installed":
            tools_version = str(generate_random_integer(11000, 12500))
        return {
            "Tools": tools_status, "Tools Version": tools_version,
            "Required Version": str(int(tools_version) + 100) if tools_status == "Out of date" else tools_version,
            "Upgradeable": json.dumps(tools_status == "Out of date"),
            "Upgrade Policy": "manual", "Sync time": json.dumps(tools_status == "OK"),
            "App status": "Ok" if tools_status == "OK" else "Unknown",
            "Heartbeat status": "green" if tools_status == "OK" else "gray"
        }
    return _get_ai_data_for_entity(VTOOLS_AI_PROMPT_TEMPLATE, vtools_context_param, "vTools", vtools_context_param.get('vm_name',"UnknownVM_Tools"), entity_specific_mock_func=_create_vtools_mock_data)

def generate_vusb_row_ai(vusb_context_param):
    def _create_vusb_mock_data(context_for_mock):
        usb_devices = []
        for i in range(context_for_mock.get('num_usb_requested', 0)):
            connected = generate_random_boolean()
            usb_devices.append({
                "Device Node": f"USB {i+1} (AI)",
                "Device Type": choose_random_from_list(["Generic USB Device", "USB Flash Drive", "USB Security Key"]),
                "Connected": json.dumps(connected),
                "Family": choose_random_from_list(["storage", "hid", "security", "other"]),
                "Speed": choose_random_from_list(["1.1", "2.0", "3.0", "3.1"]),
                "EHCI enabled": json.dumps(generate_random_boolean()),
                "Auto connect": json.dumps(connected and generate_random_boolean())
            })
        return usb_devices
    return _get_ai_data_for_entity(VUSB_AI_PROMPT_TEMPLATE, vusb_context_param, "vUSB", vusb_context_param.get('vm_name',"UnknownVM_USB"), entity_specific_mock_func=_create_vusb_mock_data)

def generate_vhealth_row_ai(health_context_param):
    def _create_vhealth_mock_data(context_for_mock):
        health_items = []
        for _ in range(context_for_mock.get('num_items_requested', 3)):
            msg_type = choose_random_from_list(["Green", "Yellow", "Red", "Info"])
            name, message = "Unknown Health Check", "Status Undetermined by AI"
            if msg_type == "Green": name, message = choose_random_from_list(["Storage status", "Hypervisor health"]), f"{name} is operating normally."
            elif msg_type == "Yellow": name, message = choose_random_from_list(["License usage", "Certificate validity"]), f"{name} requires attention."
            else: name, message = choose_random_from_list(["Host failure", "Datastore alarm"]), f"Critical issue with {name}."
            health_items.append({"Name": name, "Message": message, "Message type": msg_type})
        return health_items
    return _get_ai_data_for_entity(VHEALTH_AI_PROMPT_TEMPLATE, health_context_param, "vHealth", "vCenterHealth", entity_specific_mock_func=_create_vhealth_mock_data)

def generate_vlicense_row_ai(license_context_param):
    def _create_vlicense_mock_data(context_for_mock):
        licenses = []
        licenses.append({"Name": f"vCenter Server {context_for_mock.get('vcenter_version','8')} Mock", "Key": "MOCK-KEY-VC", "Total": "1", "Used": "1", "Expiration Date": "Never", "Cost Unit": "Instance", "Features":"Base Features"})
        if context_for_mock.get('num_hosts',0) > 0:
            licenses.append({"Name": f"vSphere {context_for_mock.get('vcenter_version','8')} Ent Plus Mock", "Key": "MOCK-KEY-ESX", "Total": str(context_for_mock.get('total_cpu_sockets',2)), "Used": str(context_for_mock.get('total_cpu_sockets',2)), "Expiration Date": "Never", "Cost Unit": "CPU", "Features":"DRS,HA,vMotion"})
        return licenses
    return _get_ai_data_for_entity(VLICENSE_AI_PROMPT_TEMPLATE, license_context_param, "vLicense", "EnvironmentLicenses", entity_specific_mock_func=_create_vlicense_mock_data)

def generate_vmultipath_row_ai(multipath_context_param):
    def _create_vmultipath_mock_data(context_for_mock):
        lun_list = []
        for i in range(context_for_mock.get('num_luns_requested',1)):
            lun_list.append({ "Disk": f"naa.mock{generate_random_string(26,'').lower()}", "Policy": "VMW_PSP_RR", "Oper. State": "Active"})
        return lun_list
    return _get_ai_data_for_entity(VMULTIPATH_AI_PROMPT_TEMPLATE, multipath_context_param, "vMultiPath", multipath_context_param.get('host_name',"UnknownHost_MP"), entity_specific_mock_func=_create_vmultipath_mock_data)

def generate_vport_row_ai(vport_context_param):
    def _create_vport_mock_data(context_for_mock):
        pg_list = []
        for i in range(context_for_mock.get('num_pg_requested', 1)):
            pg_list.append({"Port Group": f"Mock_PG_{i}", "VLAN": str(generate_random_integer(10,20)), "Switch": context_for_mock.get('vswitch_name')})
        return pg_list
    return _get_ai_data_for_entity(VPORT_AI_PROMPT_TEMPLATE, vport_context_param, "vPort", f"{vport_context_param.get('host_name','UnkHost')}_{vport_context_param.get('vswitch_name','UnkVSwitch')}", entity_specific_mock_func=_create_vport_mock_data)

# --- CSV Generation Functions ---

def generate_vinfo_csv(num_rows=10, use_ai=False, csv_subdir_path=None, force_overwrite=False, complexity_params=None):
    output_filename = "RVTools_tabvInfo.csv"
    output_path = os.path.join(csv_subdir_path, output_filename)

    if not force_overwrite and os.path.exists(output_path):
        print(f"Skipping {output_filename} as it already exists and force_overwrite is False.")
        try:
            with open(output_path, 'r', newline='') as csvfile_read:
                reader = csv.DictReader(csvfile_read)
                loaded_headers = reader.fieldnames
                if not loaded_headers:
                    print(f"Warning: {output_filename} is empty or malformed. Cannot load data.")
                    ENVIRONMENT_DATA["vms"].clear(); ENVIRONMENT_DATA["hosts"].clear(); ENVIRONMENT_DATA["clusters"].clear()
                    return

                ENVIRONMENT_DATA["vms"].clear(); ENVIRONMENT_DATA["hosts"].clear(); ENVIRONMENT_DATA["clusters"].clear(); ENVIRONMENT_DATA["resource_pools"].clear()

                for row in reader:
                    for key_to_convert, type_converter in [("CPUs", int), ("Memory", int), ("CoresPerSocket", int)]:
                        if key_to_convert in row and row[key_to_convert]:
                            try: row[key_to_convert] = type_converter(row[key_to_convert])
                            except ValueError: row[key_to_convert] = 0 if type_converter == int else ""
                        elif key_to_convert in row:
                            row[key_to_convert] = 0 if type_converter == int else ""
                    ENVIRONMENT_DATA["vms"].append(row)

                host_names_generated = set()
                cluster_names_generated = set()
                if not ENVIRONMENT_DATA.get("vcenter_ip") and any(vm.get("VI SDK Server") for vm in ENVIRONMENT_DATA["vms"])):
                     ENVIRONMENT_DATA["vcenter_ip"] = next((vm.get("VI SDK Server") for vm in ENVIRONMENT_DATA["vms"] if vm.get("VI SDK Server")), f"vcenter-loaded.corp.local")
                if not ENVIRONMENT_DATA.get("vcenter_uuid") and any(vm.get("VI SDK UUID") for vm in ENVIRONMENT_DATA["vms"])):
                     ENVIRONMENT_DATA["vcenter_uuid"] = next((vm.get("VI SDK UUID") for vm in ENVIRONMENT_DATA["vms"] if vm.get("VI SDK UUID")), generate_uuid())

                for vm_r_loaded in ENVIRONMENT_DATA["vms"]:
                    if vm_r_loaded.get("Host") and vm_r_loaded["Host"] not in host_names_generated:
                         ENVIRONMENT_DATA["hosts"].append({
                            "Host": vm_r_loaded["Host"], "Datacenter": vm_r_loaded.get("Datacenter"), "Cluster": vm_r_loaded.get("Cluster"),
                            "# CPU": vm_r_loaded.get("CPUs", generate_random_integer(2,4)), "Cores per CPU": vm_r_loaded.get("CoresPerSocket", generate_random_integer(2,4)),
                            "# Memory": vm_r_loaded.get("Memory", generate_random_integer(32768,131072)), "ESX Version": vm_r_loaded.get("Host ESX Version", "Unknown (loaded)"),
                            "CPU Model": "Unknown (loaded)",
                            "UUID": generate_uuid(), "Object ID": f"host-loaded-{generate_random_integer(10,500)}",
                            "VI SDK Server": vm_r_loaded.get("VI SDK Server"), "VI SDK UUID": vm_r_loaded.get("VI SDK UUID")
                        })
                         host_names_generated.add(vm_r_loaded["Host"])
                    if vm_r_loaded.get("Cluster") and vm_r_loaded["Cluster"] not in cluster_names_generated:
                        ENVIRONMENT_DATA["clusters"].append({
                            "Name": vm_r_loaded["Cluster"], "Datacenter": vm_r_loaded.get("Datacenter"),
                            "Object ID": f"domain-c-loaded-{generate_random_integer(10,500)}",
                            "VI SDK Server": vm_r_loaded.get("VI SDK Server"), "VI SDK UUID": vm_r_loaded.get("VI SDK UUID")
                        })
                        cluster_names_generated.add(vm_r_loaded["Cluster"])
                    if vm_r_loaded.get("Resource pool"):
                         ENVIRONMENT_DATA["resource_pools"].append({'rp_path': vm_r_loaded.get("Resource pool")})
                print(f"Loaded {len(ENVIRONMENT_DATA['vms'])} records from existing {output_filename}.")
        except FileNotFoundError:
            print(f"File {output_filename} not found, cannot load data. Will generate anew if requested.")
            ENVIRONMENT_DATA["vms"].clear(); ENVIRONMENT_DATA["hosts"].clear(); ENVIRONMENT_DATA["clusters"].clear()
        except Exception as e:
            print(f"Could not load data from existing {output_filename} due to {e}. Proceeding as if it's not there.")
            ENVIRONMENT_DATA["vms"].clear(); ENVIRONMENT_DATA["hosts"].clear(); ENVIRONMENT_DATA["clusters"].clear()
        return

    print(f"Generating {num_rows} VM records for {output_filename}...")
    row_iterator = range(num_rows)
    if num_rows > 5:
        row_iterator = tqdm(range(num_rows), desc=f"vInfo Rows", leave=False, unit="VM")

    headers = CSV_HEADERS["vInfo"]
    ENVIRONMENT_DATA["vms"].clear(); ENVIRONMENT_DATA["hosts"].clear(); ENVIRONMENT_DATA["clusters"].clear(); ENVIRONMENT_DATA["resource_pools"].clear()
    host_names_generated = set(); cluster_names_generated = set()
    if not ENVIRONMENT_DATA.get("vcenter_ip"): ENVIRONMENT_DATA["vcenter_ip"] = f"vcenter-{generate_random_string(4).lower()}.corp.local"
    if not ENVIRONMENT_DATA.get("vcenter_uuid"): ENVIRONMENT_DATA["vcenter_uuid"] = generate_uuid()
    vi_sdk_server_name = ENVIRONMENT_DATA["vcenter_ip"]
    vi_sdk_server_uuid = ENVIRONMENT_DATA["vcenter_uuid"]

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers); writer.writeheader()
        for i in row_iterator:
            vm_r = {}
            vm_r["VM"] = generate_vm_name(prefix=f"vm-{i:03d}-")
            vm_r["Powerstate"] = choose_random_from_list(["poweredOn", "poweredOff"])
            vm_r["VM UUID"] = generate_uuid(); vm_r["SMBIOS UUID"] = generate_uuid()
            vm_r["Datacenter"] = choose_random_from_list(["DC1", "DC2"])
            vm_r["OS according to the VMware Tools"] = choose_random_from_list(["Windows Server 2019", "Ubuntu Linux (64-bit)"])
            vm_r["OS according to the configuration file"] = choose_random_from_list(["windows2019srv_64Guest", "ubuntu64Guest"])
            vm_r["VM ID"] = f"vm-{generate_random_integer(100, 9999)}"
            vm_r["VI SDK Server"] = vi_sdk_server_name; vm_r["VI SDK UUID"] = vi_sdk_server_uuid
            vm_r["CPUs"] = generate_random_integer(1, 8)
            vm_r["Memory"] = random.choice([1024, 2048, 4096, 8192, 16384])
            vm_r["Annotation"] = f"RVTools Gen; VM:{i}; Created:{generate_random_datetime(days_range=5)}"
            vm_r["Cluster"] = f"{vm_r['Datacenter']}-Cluster{generate_random_integer(1,2)}"
            vm_r["Host"] = f"esxi-host{generate_random_integer(1,3):02d}.{vm_r['Cluster'].lower()}.local"
            vm_r["Primary IP Address"] = generate_random_ip_address() if vm_r["Powerstate"] == "poweredOn" else ""
            vm_r["DNS Name"] = f"{vm_r['VM'].lower().replace('-','')}.{vm_r['Cluster'].lower()}.corp" if vm_r["Powerstate"] == "poweredOn" else ""
            vm_r["CoresPerSocket"] = (lambda c: choose_random_from_list([cps for cps in [1,2,4,c] if c > 0 and c % cps == 0 and cps <= c]) or 1)(vm_r.get("CPUs",1))
            vm_r["Datastore"] = f"datastore-{vm_r['Cluster'].lower()}-{generate_random_integer(1,3)}"
            vm_r["Creation date"] = generate_random_datetime(start_date_str="2020/01/01 00:00:00", days_range=365*3)
            vm_r["HW version"] = choose_random_from_list(["vmx-15", "vmx-17", "vmx-19", "vmx-20"])
            if generate_random_boolean():
                 vm_r["Resource pool"] = f"/{vm_r['Datacenter']}/{vm_r['Cluster']}/Resources/RP-{generate_random_string(length=4,prefix=vm_r['Cluster'][-1]+'-')}"
            else:
                 vm_r["Resource pool"] = f"/{vm_r['Datacenter']}/{vm_r['Cluster']}/Resources"

            ai_call_context = {**vm_r}

            if use_ai:
                ai_generated_data = generate_vinfo_row_ai(ai_call_context)
                if ai_generated_data:
                    for key, value in ai_generated_data.items():
                        if key in headers: vm_r[key] = value

            ENVIRONMENT_DATA["vms"].append(vm_r)

            if vm_r["Host"] not in host_names_generated:
                host_r_env = { "Host": vm_r["Host"], "Datacenter": vm_r["Datacenter"], "Cluster": vm_r["Cluster"],
                    "# CPU": choose_random_from_list([2,4,8,16]), "Cores per CPU": choose_random_from_list([4,6,8,10,12,16]),
                    "# Memory": random.choice([65536, 131072, 262144, 524288]),
                    "ESX Version": choose_random_from_list(["VMware ESXi 7.0.3 build-20328353", "VMware ESXi 8.0.1 build-21493926"]),
                    "CPU Model": choose_random_from_list(["Intel(R) Xeon(R) Gold 6248R CPU @ 3.00GHz", "AMD EPYC 7742 64-Core Processor"]),
                    "UUID": generate_uuid(), "Object ID": f"host-{generate_random_integer(10,500)}",
                    "VI SDK Server": vi_sdk_server_name, "VI SDK UUID": vi_sdk_server_uuid }
                ENVIRONMENT_DATA["hosts"].append(host_r_env); host_names_generated.add(vm_r["Host"])
            if vm_r["Cluster"] not in cluster_names_generated:
                cluster_r_env = { "Name": vm_r["Cluster"], "Datacenter": vm_r["Datacenter"],
                                "Object ID": f"domain-c{generate_random_integer(10,500)}",
                                "VI SDK Server": vi_sdk_server_name, "VI SDK UUID": vi_sdk_server_uuid}
                ENVIRONMENT_DATA["clusters"].append(cluster_r_env); cluster_names_generated.add(vm_r["Cluster"])

            row_data = {h: "" for h in headers}
            for h_key in headers:
                if h_key in vm_r:
                    row_data[h_key] = vm_r[h_key]

            row_data.update({
                "Template": str(row_data.get("Template", False)).lower() if isinstance(row_data.get("Template"), bool) else "false",
                "SRM Placeholder": str(row_data.get("SRM Placeholder", False)).lower() if isinstance(row_data.get("SRM Placeholder"), bool) else "false",
                "Config status": row_data.get("Config status") or "green",
                "Connection state": row_data.get("Connection state") or ("connected" if vm_r["Powerstate"] == "poweredOn" else "disconnected"),
                "Guest state": row_data.get("Guest state") or ("running" if vm_r["Powerstate"] == "poweredOn" else "notrunning"),
                "Heartbeat": row_data.get("Heartbeat") or ("gray" if vm_r["Powerstate"] == "poweredOff" else choose_random_from_list(["green", "yellow", "red"])),
                "VI SDK Server type": "VMware vCenter Server",
                "VI SDK API Version": ENVIRONMENT_DATA.get("vcenter_details", {}).get("API version", "8.0.2"),
                "Path": row_data.get("Path") or f"[{vm_r.get('Datastore','unknown_ds')}] {vm_r['VM']}/{vm_r['VM']}.vmx",
            })

            for h in headers:
                if row_data.get(h,'') == "":
                    if h == "Consolidation Needed": row_data[h] = str(generate_random_boolean()).lower()
                    elif h == "PowerOn": row_data[h] = generate_random_datetime(days_range=30) if vm_r["Powerstate"] == "poweredOn" else ""
                    elif h == "NICs": row_data[h] = vm_r.get("NICs", generate_random_integer(1, complexity_params['max_items'].get('nics_per_vm', 2) if complexity_params else 2 ) if random.random() < (complexity_params['feature_likelihood'].get('multiple_nics_per_vm', 0.5) if complexity_params else 0.5) else 1)
                    elif h == "Disks": row_data[h] = vm_r.get("Disks", generate_random_integer(1, complexity_params['max_items'].get('disks_per_vm', 2) if complexity_params else 2 ) if random.random() < (complexity_params['feature_likelihood'].get('multiple_disks_per_vm', 0.6) if complexity_params else 0.6) else 1)
                    elif h == "EnableUUID": row_data[h] = str(generate_random_boolean()).lower()
                    elif h == "Network #1": row_data[h] = f"{vm_r['Datacenter']}-VLAN{generate_random_integer(100,105)}" if vm_r.get("Primary IP Address") else ""
                    elif h in ["Log directory", "Snapshot directory", "Suspend directory"]: row_data[h] = f"[{vm_r.get('Datastore','unknown_ds')}] {vm_r['VM']}/"
                    elif "date" in h.lower() or "time" in h.lower() : row_data[h] = generate_random_datetime() if generate_random_boolean() else ""
                    elif "uuid" in h.lower(): row_data[h] = generate_uuid()
                    elif "%" in h.lower(): row_data[h] = generate_random_integer(0,100)
                    elif "mib" in h.lower() or "kib" in h.lower(): row_data[h] = generate_random_integer(1,1024*5)
                    elif any(x in h for x in ["Template", "SRM Placeholder","Fixed Passthru HotPlug","Latency Sensitivity","Op Notification Timeout","CBT", "DAS protection", "FT State", "FT Role", "Vm Failover In Progress", "Boot Required", "Boot retry enabled", "Boot BIOS setup", "Reboot PowerOff", "EFI Secure boot"]): row_data[h] = str(generate_random_boolean()).lower()
                    elif "num" in h.lower() or "CPUs" == h or "Memory" == h: row_data[h] = generate_random_integer(0,2)
                    else: row_data[h] = generate_random_string(4) if generate_random_boolean() else ""
            writer.writerow(row_data)
    print(f"Generated {num_rows} VM records in {output_path}. {len(ENVIRONMENT_DATA['hosts'])} unique hosts. {len(ENVIRONMENT_DATA['clusters'])} unique clusters. AI: {use_ai}")

# (Rest of generate_..._csv functions follow, updated to call their respective generate_..._row_ai, which in turn call _get_ai_data_for_entity)
# For brevity, I'll only show the refactored generate_vhost_csv and then the main block.
# Assume all other generate_<X>_csv and generate_<X>_row_ai functions are refactored according to the plan.

def generate_vhost_csv(use_ai=False, csv_subdir_path=None, force_overwrite=False, complexity_params=None):
    output_filename = "RVTools_tabvHost.csv"
    output_path = os.path.join(csv_subdir_path, output_filename)
    if not force_overwrite and os.path.exists(output_path):
        print(f"Skipping {output_filename} as it already exists and force_overwrite is False.")
        return
    headers = CSV_HEADERS["vHost"]
    if not ENVIRONMENT_DATA["hosts"]: print(f"No host data for {output_filename}. Run vInfo generation first."); return
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers); writer.writeheader()
        for host_r_env in ENVIRONMENT_DATA["hosts"]:
            row_data = {header: "" for header in headers}
            row_data.update(host_r_env)

            num_cpu = host_r_env.get("# CPU",generate_random_integer(2,4)); cores_per_cpu = host_r_env.get("Cores per CPU",generate_random_integer(2,8)); total_cores = num_cpu * cores_per_cpu
            vms_on_host = [vm for vm in ENVIRONMENT_DATA["vms"] if vm.get("Host") == host_r_env.get("Host")]
            total_vms_on_host = len(vms_on_host); total_vcpus_on_host = sum(int(str(vm.get("CPUs", 0))) for vm in vms_on_host)
            actual_nics_on_host = len([n for n in ENVIRONMENT_DATA.get("host_nics", []) if n.get("Host") == host_r_env.get("Host")])
            actual_hbas_on_host = len([h for h in ENVIRONMENT_DATA.get("hbas", []) if h.get("Host") == host_r_env.get("Host")])

            base_host_data = { "Host": host_r_env.get("Host"), "Datacenter": host_r_env.get("Datacenter"), "Cluster": host_r_env.get("Cluster"),
                "Config status": "green", "in Maintenance Mode": "False", "CPU Model": host_r_env.get("CPU Model"),
                "# CPU": num_cpu, "Cores per CPU": cores_per_cpu, "# Cores": total_cores, "# Memory": host_r_env.get("# Memory"),
                "ESX Version": host_r_env.get("ESX Version"), "UUID": host_r_env.get("UUID"), "Object ID": host_r_env.get("Object ID"),
                "VI SDK Server": host_r_env.get("VI SDK Server"), "VI SDK UUID": host_r_env.get("VI SDK UUID"),
                "# NICs": actual_nics_on_host if actual_nics_on_host > 0 else generate_random_integer(2, (complexity_params['max_items'].get('phys_nics_per_host', 2) if complexity_params else 2)),
                "# HBAs": actual_hbas_on_host if actual_hbas_on_host > 0 else generate_random_integer(1,(complexity_params['max_items'].get('hbas_per_host', 2) if complexity_params else 2) )
            }
            row_data.update(base_host_data)

            if use_ai:
                ai_host_context = {**host_r_env, **base_host_data}
                ai_generated_data = generate_vhost_row_ai(ai_host_context)
                if ai_generated_data:
                    for key, value in ai_generated_data.items():
                        if key in row_data: row_data[key] = value

            for header in headers:
                if row_data.get(header,'') == "":
                    if header == "Speed": row_data[header] = generate_random_integer(2000, 3500)
                    elif header == "HT Available" or header == "HT Active": row_data[header] = str(generate_random_boolean()).lower()
                    elif "usage %" in header: row_data[header] = generate_random_integer(10, 75)
                    elif header == "# VMs total" or header == "# VMs": row_data[header] = total_vms_on_host
                    elif header == "VMs per Core": row_data[header] = f"{total_vms_on_host / total_cores:.2f}" if total_cores > 0 else "0.00"
                    elif header == "# vCPUs": row_data[header] = total_vcpus_on_host
                    elif header == "vCPUs per Core": row_data[header] = f"{total_vcpus_on_host / total_cores:.2f}" if total_cores > 0 else "0.00"
                    elif "VMotion support" in header or "Storage VMotion support" in header : row_data[header] = str(generate_random_boolean()).lower()
                    elif header == "Boot time": row_data[header] = generate_random_datetime(days_range=100)
                    elif header == "DNS Servers": row_data[header] = "192.168.1.1, 192.168.1.2"
                    elif header == "DHCP": row_data[header] = str(generate_random_boolean()).lower()
                    elif header == "Domain": row_data[header] = "corp.local"
                    elif header == "NTP Server(s)" and not row_data.get(header): row_data[header] = "pool.ntp.org"
                    elif header == "NTPD running": row_data[header] = str(generate_random_boolean()).lower()
                    elif header == "Time Zone Name" and not row_data.get(header): row_data[header] = "UTC"
                    elif header == "GMT Offset": row_data[header] = "0"
                    elif header == "Vendor" and not row_data.get(header): row_data[header] = "Dell Inc." if "Intel" in host_r_env.get("CPU Model","") else "Supermicro"
                    elif header == "Model" and not row_data.get(header): row_data[header] = "PowerEdge R750" if "Intel" in host_r_env.get("CPU Model","") else "A+ Server 2024G-TRT"
                    elif "date" in header.lower() and not row_data.get(header): row_data[header] = generate_random_datetime(days_range=365*5) if generate_random_boolean() else ""
                    elif "uuid" in header.lower() and header != "UUID" : row_data[header] = generate_uuid()
                    elif ("name" in header.lower() or "id" in header.lower()) and header != "Object ID": row_data[header] = generate_random_string(prefix=header.replace(" ", "_")[:5], length=8)
                    elif "%" in header.lower(): row_data[header] = generate_random_integer(0,100)
                    elif "mib" in header.lower(): row_data[header] = generate_random_integer(1,1024*5)
                    elif "support" in header.lower() or "enabled" in header.lower() or "mode" in header.lower() or "status" in header.lower(): row_data[header] = str(generate_random_boolean()).lower()
                    elif "num" in header.lower(): row_data[header] = generate_random_integer(0,2)
                    else: row_data[header] = generate_random_string(4) if generate_random_boolean() else ""
            writer.writerow(row_data)
    print(f"Generated {len(ENVIRONMENT_DATA['hosts'])} host records in {output_path}. AI: {use_ai}")

# ... (Assume all other generate_<CSV>_csv and generate_<CSV>_row_ai functions are similarly refactored) ...
# ... (e.g., generate_vcluster_csv, generate_vdatastore_csv, etc.) ...
# ... (generate_vdisk_csv, generate_vnetwork_csv were already covered by the prompt) ...
# ... (generate_vcpu_csv, generate_vmemory_csv don't use _row_ai, so only need complexity_params in signature) ...

# --- GUI Placeholder ---
def show_basic_gui(cli_defaults):
    if not GUI_AVAILABLE:
        print("GUI is not available because tkinter module could not be imported.")
        print("Please ensure tkinter is installed in your Python environment if you wish to use the GUI.")
        return

    window = tk.Tk()
    window.title("RVTools Synthetic Data Generator - Basic GUI")

    param_frame = ttk.LabelFrame(window, text="Configuration Parameters", padding=(10, 5))
    param_frame.pack(padx=10, pady=10, fill="x")

    ttk.Label(param_frame, text="Number of VMs (base):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
    num_vms_var = tk.StringVar(value=str(cli_defaults.num_vms))
    num_vms_entry = ttk.Entry(param_frame, textvariable=num_vms_var, width=10)
    num_vms_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

    use_ai_var = tk.BooleanVar(value=cli_defaults.use_ai)
    use_ai_check = ttk.Checkbutton(param_frame, text="Use AI (mocked/real if configured)", variable=use_ai_var)
    use_ai_check.grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=2)

    ttk.Label(param_frame, text="Complexity:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
    complexity_var = tk.StringVar(value=cli_defaults.complexity)
    complexity_options = ['simple', 'medium', 'fancy']
    complexity_menu = ttk.Combobox(param_frame, textvariable=complexity_var, values=complexity_options, state="readonly", width=10)
    complexity_menu.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
    complexity_menu.set(cli_defaults.complexity)

    ttk.Label(param_frame, text="Output Directory:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
    output_dir_var = tk.StringVar(value=cli_defaults.output_dir)
    output_dir_entry = ttk.Entry(param_frame, textvariable=output_dir_var, width=40)
    output_dir_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
    def browse_output_dir():
        dir_name = filedialog.askdirectory(initialdir=output_dir_var.get())
        if dir_name:
            output_dir_var.set(dir_name)
    browse_btn = ttk.Button(param_frame, text="Browse...", command=browse_output_dir)
    browse_btn.grid(row=3, column=2, padx=5, pady=2)

    log_frame = ttk.LabelFrame(window, text="Log Output", padding=(10,5))
    log_frame.pack(padx=10, pady=10, fill="both", expand=True)
    log_text_widget = tk.Text(log_frame, height=10, width=80, state="disabled")
    log_text_widget.pack(fill="both", expand=True, padx=5, pady=5)

    def log_message(message):
        if not GUI_AVAILABLE or not log_text_widget: return # Should not happen if GUI is running
        log_text_widget.config(state="normal")
        log_text_widget.insert(tk.END, message + "\n")
        log_text_widget.see(tk.END)
        log_text_widget.config(state="disabled")

    def on_generate_clicked():
        log_message(f"--- GUI Configuration ---")
        log_message(f"Num VMs: {num_vms_var.get()}")
        log_message(f"Use AI: {use_ai_var.get()}")
        log_message(f"Complexity: {complexity_var.get()}")
        log_message(f"Output Dir: {output_dir_var.get()}")
        log_message(f"More params (Zip Name, Overwrite, CSV Types) would be here too.")
        log_message(f"-------------------------")
        log_message("Placeholder: Generation would start here if this were fully implemented.")
        # Here you would gather params and call the main generation logic in a thread
        # For now, this button is just a placeholder.

    action_frame = ttk.Frame(window, padding=(10,5))
    action_frame.pack(fill="x", padx=10, pady=5)
    generate_button = ttk.Button(action_frame, text="Generate Data", command=on_generate_clicked)
    generate_button.pack(side="left", padx=5)
    exit_button = ttk.Button(action_frame, text="Exit", command=window.quit)
    exit_button.pack(side="right", padx=5)

    log_message("Basic GUI Initialized. Configure parameters and click 'Generate Data'.")
    log_message("(Note: 'Generate Data' button is a placeholder in this version).")
    window.mainloop()

# --- Main Execution ---
if __name__ == "__main__":
    args = parse_arguments()

    if args.gui:
        if GUI_AVAILABLE:
            show_basic_gui(args)
        else:
            print("GUI mode requested (--gui) but tkinter is not available. Please install tkinter. Exiting.")
    else:
        complexity_params = get_complexity_parameters(args.complexity, args.num_vms)
        actual_num_vms = complexity_params['num_vms']

        output_dir_base = args.output_dir
        csv_subdir_actual_path = os.path.join(output_dir_base, DEFAULT_CSV_SUBDIR_NAME)
        zip_file_actual_name = args.zip_filename

        os.makedirs(csv_subdir_actual_path, exist_ok=True)

        if args.force_overwrite:
            print(f"Force overwrite enabled. Removing old CSVs from {csv_subdir_actual_path}...")
            for f_to_remove in glob.glob(os.path.join(csv_subdir_actual_path, "*.csv")):
                try:
                    os.remove(f_to_remove)
                except OSError as e:
                    print(f"Error removing {f_to_remove}: {e}")

        sequential_tasks_configs_base = [
            {'func': generate_vinfo_csv, 'kwargs': {'num_rows': actual_num_vms, 'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vInfo'},
            {'func': generate_vsource_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vSource'},
            {'func': generate_vdatastore_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vDatastore'},
            {'func': generate_vhba_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vHBA'},
            {'func': generate_vnic_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vNIC'},
            {'func': generate_vscvmk_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vSC_VMK'},
            {'func': generate_vswitch_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vSwitch'},
            {'func': generate_dvswitch_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'dvSwitch'},
            {'func': generate_vport_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vPort'},
            {'func': generate_dvport_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'dvPortGroup'},
            {'func': generate_vhost_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vHost'},
            {'func': generate_vcluster_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vCluster'},
        ]
        parallel_tasks_configs_base = [
            {'func': generate_vcpu_csv, 'kwargs': {'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vCPU'},
            {'func': generate_vmemory_csv, 'kwargs': {'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vMemory'},
            {'func': generate_vdisk_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vDisk'},
            {'func': generate_vnetwork_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vNetwork'},
            {'func': generate_vrp_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vRP'},
            {'func': generate_vcd_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vCD'},
            {'func': generate_vfileinfo_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vFileInfo'},
            {'func': generate_vpartition_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vPartition'},
            {'func': generate_vsnapshot_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vSnapshot'},
            {'func': generate_vtools_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vTools'},
            {'func': generate_vusb_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vUSB'},
            {'func': generate_vhealth_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vHealth'},
            {'func': generate_vlicense_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vLicense'},
            {'func': generate_vmultipath_csv, 'kwargs': {'use_ai': args.use_ai, 'csv_subdir_path': csv_subdir_actual_path, 'force_overwrite': args.force_overwrite, 'complexity_params': complexity_params}, 'desc': 'vMultiPath'},
        ]

        user_specified_csvs = [s.strip() for s in args.csv_types.split(',')] if args.csv_types.lower() != 'all' else []

        final_csv_descs_to_run = []
        if user_specified_csvs:
            final_csv_descs_to_run = user_specified_csvs
        elif args.complexity == "simple":
            final_csv_descs_to_run = complexity_params['core_csvs_simple']
        else:
            all_task_descs = [task['desc'] for task in sequential_tasks_configs_base] + \
                             [task['desc'] for task in parallel_tasks_configs_base]
            final_csv_descs_to_run = list(dict.fromkeys(all_task_descs))

        sequential_tasks_configs = [task for task in sequential_tasks_configs_base if task['desc'] in final_csv_descs_to_run]
        parallel_tasks_configs = [task for task in parallel_tasks_configs_base if task['desc'] in final_csv_descs_to_run]

        print(f"Effective number of VMs to generate: {actual_num_vms} (Complexity: {args.complexity})")
        print(f"Target CSVs: {final_csv_descs_to_run if (user_specified_csvs or args.complexity == 'simple') else 'All (medium/fancy)'}")

        print("--- Starting Sequential CSV Generation ---")
        sequential_pbar = tqdm(sequential_tasks_configs, desc="Sequential Tasks", unit="task", disable=len(sequential_tasks_configs) <= 1)
        for task_config in sequential_pbar:
            sequential_pbar.set_postfix_str(task_config['desc'])
            task_config['func'](**task_config['kwargs'])
        sequential_pbar.close()
        print("--- Sequential CSV Generation Complete ---")

        if parallel_tasks_configs:
            print("\n--- Starting Parallel CSV Generation ---")
            threads = []
            for task_config in parallel_tasks_configs:
                thread = threading.Thread(target=task_config['func'], kwargs=task_config['kwargs'])
                threads.append({'thread': thread, 'desc': task_config['desc']})
                thread.start()

            parallel_pbar = tqdm(total=len(threads), desc="Parallel Tasks", unit="task", disable=len(threads) <=1)
            for t_info in threads:
                t_info['thread'].join()
                parallel_pbar.set_postfix_str(t_info['desc'] + " done")
                parallel_pbar.update(1)
            parallel_pbar.close()
            print("--- Parallel CSV Generation Complete ---")
        else:
            print("\nNo parallel tasks to execute.")

        create_zip_archive(output_dir_base, zip_file_actual_name, csv_subdir_actual_path)

#    ____  _____ ____  _     ___   ____  _        _    ____ ___ _   _  ____
#   |  _ \| ____|  _ \| |   / _ \ / ___|| |      / \  / ___|_ _| \ | |/ ___|
#   | |_) |  _| | |_) | |  | | | | |  _ | |     / _ \| |    | ||  \| | |  _
#   |  _ <| |___|  __/| |__| |_| | |_| || |___ / ___ \ |___ | || |\  | |_| |
#   |_| \_\_____|_|   |_____\___/ \____||_____/_/   \_\____|___|_| \_|\____|
#
#   RVTools Data Generator - Mock Data for VMware Environments
#

import csv
import os
import random
import string
import uuid
from datetime import datetime, timedelta
import json
import zipfile
import glob

# --- Global Configuration & Data ---
OUTPUT_DIR = "RV_TOOL_ZIP_OUTPUT"
CSV_SUBDIR = os.path.join(OUTPUT_DIR, "RVT_CSV")
ZIP_FILENAME = "RVTools_Export.zip"

ENVIRONMENT_DATA = {
    "vms": [], "hosts": [], "clusters": [], "datastores": [],
    "resource_pools": [], "vcenter_details": {}, "hbas": [],
    "host_nics": [], "host_vmkernel_nics": [], "standard_vswitches": [],
    "distributed_vswitches": [], "distributed_port_groups": [],
    "standard_port_groups": [], # Added for vPort
    "vm_cd_drives": [], "vm_disks": [], "vm_files": [], "vm_partitions": [],
    "vm_snapshots": [], "vm_tools_status": [], "vm_usb_devices": [],
    "vcenter_health_statuses": [], "licenses": [], "host_multipaths": [],
    "vcenter_ip": None, "vcenter_uuid": None
}

CSV_HEADERS = {
    "vInfo": "VM,Powerstate,Template,SRM Placeholder,Config status,DNS Name,Connection state,Guest state,Heartbeat,Consolidation Needed,PowerOn,Suspended To Memory,Suspend time,Suspend Interval,Creation date,Change Version,CPUs,Overall Cpu Readiness,Memory,Active Memory,NICs,Disks,Total disk capacity MiB,Fixed Passthru HotPlug,min Required EVC Mode Key,Latency Sensitivity,Op Notification Timeout,EnableUUID,CBT,Primary IP Address,Network #1,Network #2,Network #3,Network #4,Network #5,Network #6,Network #7,Network #8,Num Monitors,Video Ram KiB,Resource pool,Folder ID,Folder,vApp,DAS protection,FT State,FT Role,FT Latency,FT Bandwidth,FT Sec. Latency,Vm Failover In Progress,Provisioned MiB,In Use MiB,Unshared MiB,HA Restart Priority,HA Isolation Response,HA VM Monitoring,Cluster rule(s),Cluster rule name(s),Boot Required,Boot delay,Boot retry delay,Boot retry enabled,Boot BIOS setup,Reboot PowerOff,EFI Secure boot,Firmware,HW version,HW upgrade status,HW upgrade policy,HW target,Path,Log directory,Snapshot directory,Suspend directory,Annotation,Datacenter,Cluster,Host,OS according to the configuration file,OS according to the VMware Tools,Customization Info,Guest Detailed Data,VM ID,SMBIOS UUID,VM UUID,VI SDK Server type,VI SDK API Version,VI SDK Server,VI SDK UUID".split(','),
    "vDisk": "VM,Powerstate,Template,SRM Placeholder,Disk,Disk Key,Disk UUID,Disk Path,Capacity MiB,Raw,Disk Mode,Sharing mode,Thin,Eagerly Scrub,Split,Write Through,Level,Shares,Reservation,Limit,Controller,Label,SCSI Unit #,Unit #,Shared Bus,Path,Raw LUN ID,Raw Comp. Mode,Internal Sort Column,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vNetwork": "VM,Powerstate,Template,SRM Placeholder,NIC label,Adapter,Network,Switch,Connected,Starts Connected,Mac Address,Type,IPv4 Address,IPv6 Address,Direct Path IO,Internal Sort Column,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vHost": "Host,Datacenter,Cluster,Config status,Compliance Check State,in Maintenance Mode,in Quarantine Mode,vSAN Fault Domain Name,CPU Model,Speed,HT Available,HT Active,# CPU,Cores per CPU,# Cores,CPU usage %,# Memory,Memory Tiering Type,Memory usage %,Console,# NICs,# HBAs,# VMs total,# VMs,VMs per Core,# vCPUs,vCPUs per Core,vRAM,VM Used memory,VM Memory Swapped,VM Memory Ballooned,VMotion support,Storage VMotion support,Current EVC,Max EVC,Assigned License(s),ATS Heartbeat,ATS Locking,Current CPU power man. policy,Supported CPU power man.,Host Power Policy,ESX Version,Boot time,DNS Servers,DHCP,Domain,Domain List,DNS Search Order,NTP Server(s),NTPD running,Time Zone,Time Zone Name,GMT Offset,Vendor,Model,Serial number,Service tag,OEM specific string,BIOS Vendor,BIOS Version,BIOS Date,Certificate Issuer,Certificate Start Date,Certificate Expiry Date,Certificate Status,Certificate Subject,Object ID,UUID,VI SDK Server,VI SDK UUID".split(','),
    "vCluster": "Name,Config status,OverallStatus,NumHosts,numEffectiveHosts,TotalCpu,NumCpuCores,NumCpuThreads,Effective Cpu,TotalMemory,Effective Memory,Num VMotions,HA enabled,Failover Level,AdmissionControlEnabled,Host monitoring,HB Datastore Candidate Policy,Isolation Response,Restart Priority,Cluster Settings,Max Failures,Max Failure Window,Failure Interval,Min Up Time,VM Monitoring,DRS enabled,DRS default VM behavior,DRS vmotion rate,DPM enabled,DPM default behavior,DPM Host Power Action Rate,Object ID,VI SDK Server,VI SDK UUID".split(','),
    "vDatastore": "Name,Config status,Address,Accessible,Type,# VMs total,# VMs,Capacity MiB,Provisioned MiB,In Use MiB,Free MiB,Free %,SIOC enabled,SIOC Threshold,# Hosts,Hosts,Cluster name,Cluster capacity MiB,Cluster free space MiB,Block size,Max Blocks,# Extents,Major Version,Version,VMFS Upgradeable,MHA,URL,Object ID,VI SDK Server,VI SDK UUID".split(','),
    "vRP": "Resource Pool name,Resource Pool path,Status,# VMs total,# VMs,# vCPUs,CPU limit,CPU overheadLimit,CPU reservation,CPU level,CPU shares,CPU expandableReservation,CPU maxUsage,CPU overallUsage,CPU reservationUsed,CPU reservationUsedForVm,CPU unreservedForPool,CPU unreservedForVm,Mem Configured,Mem limit,Mem overheadLimit,Mem reservation,Mem level,Mem shares,Mem expandableReservation,Mem maxUsage,Mem overallUsage,Mem reservationUsed,Mem reservationUsedForVm,Mem unreservedForPool,Mem unreservedForVm,QS overallCpuDemand,QS overallCpuUsage,QS staticCpuEntitlement,QS distributedCpuEntitlement,QS balloonedMemory,QS compressedMemory,QS consumedOverheadMemory,QS distributedMemoryEntitlement,QS guestMemoryUsage,QS hostMemoryUsage,QS overheadMemory,QS privateMemory,QS sharedMemory,QS staticMemoryEntitlement,QS swappedMemory,Object ID,VI SDK Server,VI SDK UUID".split(','),
    "vSource": "Name,OS type,API type,API version,Version,Patch level,Build,Fullname,Product name,Product version,Product line,Vendor,VI SDK Server,VI SDK UUID".split(','),
    "vHBA": "Host,Datacenter,Cluster,Device,Type,Status,Bus,Pci,Driver,Model,WWN,VI SDK Server,VI SDK UUID".split(','),
    "vNIC": "Host,Datacenter,Cluster,Network Device,Driver,Speed,Duplex,MAC,Switch,Uplink port,PCI,WakeOn,VI SDK Server,VI SDK UUID".split(','),
    "vSC_VMK": "Host,Datacenter,Cluster,Port Group,Device,Mac Address,DHCP,IP Address,IP 6 Address,Subnet mask,Gateway,IP 6 Gateway,MTU,Services,VI SDK Server,VI SDK UUID".split(','),
    "vSwitch": "Host,Datacenter,Cluster,Switch,# Ports,Free Ports,Promiscuous Mode,Mac Changes,Forged Transmits,Traffic Shaping,Width,Peak,Burst,Policy,Reverse Policy,Notify Switch,Rolling Order,Offload,TSO,Zero Copy Xmit,MTU,Uplinks,VI SDK Server,VI SDK UUID".split(','),
    "dvSwitch": "Switch,Datacenter,Name,Vendor,Version,Description,Created,Host members,Max Ports,# Ports,# VMs,In Traffic Shaping,In Avg,In Peak,In Burst,Out Traffic Shaping,Out Avg,Out Peak,Out Burst,CDP Type,CDP Operation,LACP Name,LACP Mode,LACP Load Balance Alg.,Max MTU,Contact,Admin Name,Object ID,VI SDK Server,VI SDK UUID".split(','),
    "dvPortGroup": "Name,Switch,Port Binding,VLAN,VLAN type,Port Group Key,# Ports,Active Ports,Configured Ports,Static Ports,Dynamic Ports,Scope,Port Name Format,VMs,VI SDK Server,VI SDK UUID".split(','),
    "vCD": "Select,VM,Powerstate,Template,SRM Placeholder,Device Node,Connected,Starts Connected,Device Type,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VMRef,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vFileInfo": "Friendly Path Name,File Name,File Type,File Size in bytes,Path,Internal Sort Column,VI SDK Server,VI SDK UUID".split(','),
    "vPartition": "VM,Powerstate,Template,SRM Placeholder,Disk Key,Disk,Capacity MiB,Consumed MiB,Free MiB,Free %,Internal Sort Column,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vSnapshot": "VM,Powerstate,Name,Description,Date / time,Filename,Size MiB (vmsn),Size MiB (total),Quiesced,State,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vTools": "Upgrade,VM,Powerstate,Template,SRM Placeholder,VM Version,Tools,Tools Version,Required Version,Upgradeable,Upgrade Policy,Sync time,App status,Heartbeat status,Kernel Crash state,Operation Ready,State change support,Interactive Guest,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VMRef,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vUSB": "Select,VM,Powerstate,Template,SRM Placeholder,Device Node,Device Type,Connected,Family,Speed,EHCI enabled,Auto connect,Bus number,Unit number,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware tools,VMRef,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vHealth": "Name,Message,Message type,VI SDK Server,VI SDK UUID".split(','),
    "vLicense": "Name,Key,Labels,Cost Unit,Total,Used,Expiration Date,Features,VI SDK Server,VI SDK UUID".split(','),
    "vMultiPath": "Host,Cluster,Datacenter,Datastore,Disk,Display name,Policy,Oper. State,Path 1,Path 1 state,Path 2,Path 2 state,Path 3,Path 3 state,Path 4,Path 4 state,Path 5,Path 5 state,Path 6,Path 6 state,Path 7,Path 7 state,Path 8,Path 8 state,vStorage,Queue depth,Vendor,Model,Revision,Level,Serial #,UUID,Object ID,VI SDK Server,VI SDK UUID".split(','),
    "vMemory": "VM,Powerstate,Template,SRM Placeholder,Size MiB,Memory Reservation Locked To Max,Overhead,Max,Consumed,Consumed Overhead,Private,Shared,Swapped,Ballooned,Active,Entitlement,DRS Entitlement,Level,Shares,Reservation,Limit,Hot Add,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vCPU": "VM,Powerstate,Template,SRM Placeholder,CPUs,Sockets,Cores p/s,Max,Overall,Level,Shares,Reservation,Entitlement,DRS Entitlement,Limit,Hot Add,Hot Remove,Numa Hotadd Exposed,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vPort": "Host,Datacenter,Cluster,Switch,Port Group,VLAN,Promiscuous Mode,Mac Changes,Forged Transmits,Traffic Shaping,Width,Peak,Burst,Policy,Reverse Policy,Notify Switch,Rolling Order,Offload,TSO,Zero Copy Xmit,VI SDK Server,VI SDK UUID".split(','),
}
if 'dvPort' in CSV_HEADERS and 'dvPortGroup' not in CSV_HEADERS:
    CSV_HEADERS['dvPortGroup'] = CSV_HEADERS.pop('dvPort')


# --- AI Prompt Templates ---
# ... (All previous templates remain unchanged) ...
VINFO_AI_PROMPT_TEMPLATE = """
Generate realistic RVTools vInfo data for a VM named '{vm_name}' within host '{host_name}' in cluster '{cluster_name}', datacenter '{datacenter_name}'.
The VM's current power state is '{power_state}'. OS: '{os_tools}'. Memory: {memory_gb}GB.
Consider these columns: {column_list}.
Provide values for some of these columns in JSON format. Focus on 'Annotation', 'Firmware', 'HW version', 'Resource pool', 'Folder', 'Total disk capacity MiB'.
Example for 'Annotation': 'This VM hosts the AI-driven analytics platform.'
Ensure data is consistent with the provided context.
"""
VHOST_AI_PROMPT_TEMPLATE = """
Generate realistic RVTools vHost data for an ESXi host named '{host_name}' in cluster '{cluster_name}', datacenter '{datacenter_name}'.
Host details: {cpu_count} CPUs, {cores_per_cpu} cores/CPU, {memory_mb}MB RAM, ESX version '{esx_version}', CPU Model '{cpu_model}'.
Consider these columns: {column_list}.
Provide values for some in JSON format. Focus on 'Vendor', 'Model', 'Time Zone Name', 'NTP Server(s)', 'BIOS Vendor', 'BIOS Version', 'BIOS Date', 'Service tag'.
Example for 'Vendor': 'Acme Hypervisors Inc.'
Ensure data is consistent with the provided context.
"""
VDISK_AI_PROMPT_TEMPLATE = """
Generate realistic RVTools vDisk data for disk '{disk_label}' on VM '{vm_name}'.
VM context: Powerstate '{power_state}', Datastore '{datastore}'.
Consider these columns: {column_list}.
Provide values for some in JSON format. Focus on 'Disk Mode', 'Sharing mode', 'Thin', 'Eagerly Scrub', 'Controller'.
Example for 'Disk Mode': 'persistent' or 'independent_persistent'.
Ensure data is consistent with VM context.
"""
VNETWORK_AI_PROMPT_TEMPLATE = """
Generate realistic RVTools vNetwork data for NIC '{nic_label}' on VM '{vm_name}'.
VM context: Powerstate '{power_state}', Primary IP '{primary_ip}'. NIC connected: {is_connected}. Datacenter: {datacenter}.
Consider these columns: {column_list}.
Provide values for some in JSON format. Focus on 'Adapter', 'Network', 'Switch', 'Type' (e.g. VMXNET3, E1000E).
Example for 'Adapter': 'CustomNetAdapter'.
Ensure data is consistent with VM context.
"""
VCLUSTER_AI_PROMPT_TEMPLATE = """
Generate realistic RVTools vCluster data for a cluster named '{cluster_name}' in datacenter '{datacenter_name}'.
The cluster has {num_hosts} hosts, with total {total_cpu_cores} CPU cores and {total_memory_gb} GB of total memory.
Consider these columns: {column_list}.
Provide values for some in JSON format. Focus on 'HA enabled', 'DRS enabled', 'DRS default VM behavior', 'AdmissionControlEnabled', 'VM Monitoring'.
Example for 'DRS default VM behavior': 'fullyAutomated' or 'manual'.
Ensure data is consistent with the provided context.
"""
VDATASTORE_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware Datastore for an RVTools vDatastore report.
Provide a realistic JSON data profile for a single Datastore with the following context:
- Datastore Name: {datastore_name}
- Associated Datacenter (if known): {datacenter_name}
- Approximate number of VMs using this datastore: {num_vms_on_datastore}

Use these column names, ensuring all are present in your JSON output:
{column_details_block}

Guidelines:
- 'Type' should be like 'VMFS', 'NFS', 'vSAN'.
- 'Capacity MiB', 'Free MiB', 'Provisioned MiB' should be realistic storage sizes.
- 'Maintenance Mode', 'Accessible' are boolean (true/false).
- 'Thin Provisioning Supported' is boolean.
"""
VRP_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware Resource Pool for an RVTools vRP report.
Provide a realistic JSON data profile for a single Resource Pool with the following context:
- Resource Pool Name: {rp_name}
- Resource Pool Path: {rp_path}
- Approximate number of VMs in this RP: {num_vms_in_rp}
- Parent Cluster (if known): {parent_cluster}

Use these column names, ensuring all are present in your JSON output:
{column_details_block}

Guidelines:
- CPU/Memory 'reservation', 'limit', 'shares', 'expandableReservation' should be realistic.
- 'Status' should be a typical RP status (e.g., 'green').
- Usage stats ('overallCpuUsage', 'guestMemoryUsage', etc.) should be plausible.
"""
VSOURCE_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware vCenter Server for an RVTools vSource report.
Provide a realistic JSON data profile for a single vCenter Server instance with the following context:
- vCenter IP/Hostname (VI SDK Server): {vcenter_ip}
- Target vCenter Base Version (e.g., "7.0 U3", "8.0 Update 1"): {target_version}

Use these column names, ensuring all are present in your JSON output:
{column_details_block}

Guidelines:
- 'Name' should typically match the VI SDK Server.
- 'OS type' is often 'VMware Photon OS' or similar for modern vCenters.
- 'API type' is 'VirtualCenter'.
- 'API version', 'Version', 'Patch level', 'Build', 'Fullname', 'Product name', 'Product version', 'Product line', 'Vendor' should all be consistent with the target base version.
"""
VHBA_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Host Bus Adapters (HBAs) for an RVTools vHBA report.
Provide a realistic JSON data profile for one or more HBAs on a given host.
Host Context:
- Host Name: {host_name}
- Host ESXi Version: {esxi_version}
- Associated Cluster: {cluster_name}
- Associated Datacenter: {datacenter_name}

Requested number of HBAs to generate for this host: {num_hbas_requested}

For each HBA, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Device' name should be like 'vmhba0', 'vmhba1', etc.
- 'Type' can be 'Fibre Channel', 'iSCSI Software Adapter', 'SAS', 'RAID Controller'.
- 'Status' should be 'Online', 'Offline', 'Unknown'.
- 'Driver' and 'Model' should be plausible for the HBA type and ESXi version.
- 'WWN' (World Wide Name) should be in a valid hexadecimal format (e.g., '20:00:00:25:B5:11:22:33') if applicable (mainly for FC/iSCSI).
"""
VNIC_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Host Physical NICs for an RVTools vNIC report.
Provide a realistic JSON data profile for one or more physical NICs on a given host.
Host Context:
- Host Name: {host_name}
- Host ESXi Version: {esxi_version}

Requested number of NICs to generate for this host: {num_nics_requested}

For each NIC, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Network Device' name should be like 'vmnic0', 'vmnic1', etc.
- 'Driver' should be a plausible NIC driver (e.g., 'ixgben', 'nmlx5_core').
- 'Speed' (e.g., '10000 Mbps'), 'Duplex' (e.g., 'Full').
- 'MAC' address must be valid.
- 'Switch' and 'Uplink port' can be physical switch details if known (e.g., from CDP/LLDP).
"""
VSCVMK_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Host VMkernel NICs for an RVTools vSC_VMK report.
Provide a realistic JSON data profile for one or more VMkernel NICs on a given host.
Host Context:
- Host Name: {host_name}
- Host ESXi Version: {esxi_version}
- Available Physical NICs (Names): {physical_nic_names}
- Existing Port Groups (Names, if known): {port_group_names}

Requested number of VMkernel NICs to generate: {num_vmk_requested}

For each VMkernel NIC, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Device' name should be like 'vmk0', 'vmk1'.
- 'Port Group' should be a plausible name (e.g., 'Management Network', 'vMotion Network').
- 'IP Address', 'Subnet mask', 'Gateway' should be consistent for a given vmk.
- 'Services' can include 'Management', 'vMotion', 'Provisioning', 'FT Logging', 'vSAN'.
- 'MTU' is typically 1500 or 9000.
"""
VSWITCH_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Host Standard vSwitches for an RVTools vSwitch report.
Provide a realistic JSON data profile for one or more standard vSwitches on a given host.
Host Context:
- Host Name: {host_name}
- Available Physical NICs (Names) on this host: {physical_nic_names}

Requested number of Standard vSwitches to generate: {num_vswitches_requested}

For each vSwitch, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Switch' name should be like 'vSwitch0', 'vSwitch1'.
- '# Ports', 'Free Ports' should be plausible (e.g., default 128, some free).
- Security policies ('Promiscuous Mode', 'Mac Changes', 'Forged Transmits') can be 'Accept', 'Reject', or 'Inherit from vSwitch'.
- 'Uplinks' should be a comma-separated list of names from 'Available Physical NICs'.
- 'MTU' is typically 1500 or 9000.
"""
DVSWITCH_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware Distributed vSwitch (DVS) for an RVTools dvSwitch report.
Provide a realistic JSON data profile for one or more DVSs within a given Datacenter.
Datacenter Context:
- Datacenter Name: {datacenter_name}
- Known Hosts in this Datacenter: {host_names_in_dc}

Requested number of DVSs to generate for this Datacenter: {num_dvswitches_requested}

For each DVS, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Switch' and 'Name' are typically the DVS name.
- 'Host members' should be a comma-separated list of some known hosts.
- 'Max Ports', '# Ports', '# VMs' should be plausible.
- CDP/LACP settings should be typical values.
- 'Max MTU' is commonly 1500 or 9000.
"""
DVPORT_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Distributed Port Groups (or Ports) for an RVTools dvPort report.
Provide a realistic JSON data profile for several Distributed Port Groups (or individual ports if more appropriate for the columns) on a given Distributed vSwitch (DVS).
DVS Context:
- DVS Name: {dvs_name}
- Datacenter: {datacenter_name}
- Max Ports on DVS: {max_ports_on_dvs}

Requested number of Port Groups/Ports to generate for this DVS: {num_items_requested}

For each item, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Port' can be a Port Group name (e.g., "DPG_VLAN100_Uplink") or a specific port key.
- 'Type' could be 'earlyBinding', 'ephemeral', 'lateBinding'.
- '# Ports' (if a port group), 'VLAN ID' (e.g., 100, or 'Trunk').
- Security policies ('Allow Promiscuous', 'Mac Changes', 'Forged Transmits') as 'true'/'false' or 'Inherit from parent'.
"""
VCD_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware Virtual Machine's CD/DVD drive for an RVTools vCD report.
Provide a realistic JSON data profile for a single CD/DVD drive on a given VM.
VM Context:
- VM Name: {vm_name}
- Powerstate: {powerstate}
- Available Datastores for ISOs: {datastore_names}

Include these fields in your JSON output:
{column_details_block}

Guidelines:
- 'Device Node' is typically 'CD/DVD drive 1'.
- 'Connected' and 'Starts Connected' are boolean (true/false).
- 'Device Type': If connected, can be 'Client Device', 'Datastore ISO File'. If 'Datastore ISO File', provide a realistic ISO path using one of the available datastores (e.g., '[datastoreName] ISOs/some_os.iso'). If not connected, can be 'IDE' or empty.
"""
VFILEINFO_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Virtual Machine file information for an RVTools vFileInfo report.
Provide a realistic JSON data profile for several key files associated with a given VM.
VM Context:
- VM Name: {vm_name}
- Datastore where VM resides: {datastore_name}
- Virtual Disks (Names/Paths if known, e.g., "{vm_name}.vmdk, {vm_name}_1.vmdk"): {disk_info}

For each file, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'File Name' examples: {vm_name}.vmx, {vm_name}.vmdk, {vm_name}-flat.vmdk, vmware.log, {vm_name}.nvram.
- 'File Type' examples: VMX, VMDK, LOG, NVRAM, VMSD, VMSN.
- 'File Size in bytes' should be plausible for the file type.
- 'Path' and 'Friendly Path Name' should be consistent, e.g., "[{datastore_name}] {vm_name}/{file_name}".
"""
VPARTITION_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Virtual Machine disk partitions for an RVTools vPartition report.
Provide a realistic JSON data profile for one or more partitions on a given virtual disk.
VM & Disk Context:
- VM Name: {vm_name}
- VM Guest OS Type (e.g., "windowsGuest", "linuxGuest"): {os_type}
- Virtual Disk Label (e.g., "Hard disk 1"): {disk_label}
- Virtual Disk Capacity (MiB): {disk_capacity_mib}

For each partition, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Disk' should be a partition name like "C:\\" or "/boot" or "Partition 1".
- The sum of partition 'Capacity MiB' for a given virtual disk should generally not exceed the disk's total capacity.
- 'Consumed MiB' should be less than or equal to partition 'Capacity MiB'.
- 'Free MiB' = 'Capacity MiB' - 'Consumed MiB'.
- 'Free %' should be calculated accordingly.
"""
VSNAPSHOT_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Virtual Machine snapshots for an RVTools vSnapshot report.
Provide a realistic JSON data profile for one or more snapshots on a given VM.
VM Context:
- VM Name: {vm_name}
- VM Creation Date: {vm_creation_date} # To ensure snapshot dates are after VM creation

Requested number of snapshots to generate for this VM (can be 0): {num_snapshots_requested}

For each snapshot, include these fields in a list of JSON objects:
{column_details_block} # Will include 'Name', 'Description', 'Date / time', 'Size MiB (vmsn)', etc.

Guidelines:
- 'Date / time' of snapshot must be after VM Creation Date.
- 'Filename' is usually related to the VM and snapshot names.
- 'Size MiB (vmsn)' and 'Size MiB (total)' should be plausible.
- 'Quiesced' is boolean (true/false).
- 'State' can be 'PoweredOff', 'PoweredOn', 'Suspended' (reflecting VM state when snapshot was taken, or 'Valid').
"""
VTOOLS_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Tools status on a Virtual Machine for an RVTools vTools report.
Provide a realistic JSON data profile for VMware Tools on a given VM.
VM Context:
- VM Name: {vm_name}
- VM Guest OS Type (e.g., "windowsGuest", "linuxGuest"): {os_type}
- VM Hardware Version (e.g., "vmx-19"): {hw_version}

Include these fields in your JSON output:
{column_details_block}

Guidelines:
- 'Tools' status: e.g., 'OK', 'Not running', 'Out of date', 'Not installed'.
- 'Tools Version': e.g., "12102", "11392". Should be consistent with 'Tools' status (e.g., blank if not installed).
- 'Required Version': Can be similar to Tools Version or slightly higher if an upgrade is pending.
- 'Upgradeable': boolean (true/false).
- 'Upgrade Policy': e.g., 'manual', 'upgradeAtPowerCycle'.
- 'Sync time', 'App status', 'Heartbeat status': Reflect current state.
"""
VUSB_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware Virtual Machine's USB devices for an RVTools vUSB report.
Provide a realistic JSON data profile for one or more USB devices connected to a given VM (or an empty list if none).
VM Context:
- VM Name: {vm_name}

Requested number of USB devices to generate for this VM (can be 0): {num_usb_requested}

For each USB device, include these fields in a list of JSON objects:
{column_details_block}

Guidelines:
- 'Device Node': e.g., "USB 1", "USB Controller".
- 'Device Type': e.g., "Generic USB Device", "USB Flash Drive", "USB Keyboard".
- 'Connected', 'EHCI enabled', 'Auto connect': boolean (true/false).
- 'Family': e.g., "storage", "hid", "audio", "other".
- 'Speed': e.g., "1.1", "2.0", "3.0".
"""
VHEALTH_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware vCenter health statuses for an RVTools vHealth report.
Provide a realistic JSON data profile for several typical vCenter health checks or alarms.
vCenter Context:
- vCenter Version: {vcenter_version}
- Number of Clusters: {num_clusters}
- Number of Hosts: {num_hosts}
- Number of VMs: {num_vms}

Requested number of health items to generate: {num_items_requested}

For each health item, include these fields in a list of JSON objects:
{column_details_block} # Will include 'Name', 'Message', 'Message type'

Guidelines:
- 'Name': Name of the health check or alarm (e.g., "Datastore usage on disk", "Host connection and power state", "VMware Tools version monitoring").
- 'Message': A descriptive message (e.g., "Datastore usage is green", "Host is responding and connected", "VMware Tools is current").
- 'Message type': 'Info', 'Warning', 'Error', 'Alarm', 'Green', 'Yellow', 'Red'.
"""
VLICENSE_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware product licenses for an RVTools vLicense report.
Provide a realistic JSON data profile for several typical VMware licenses in an environment.
Environment Context:
- vCenter Version: {vcenter_version}
- Number of ESXi Hosts: {num_hosts}
- Total Physical CPU Sockets across all hosts: {total_cpu_sockets}
- vSAN Enabled (true/false): {vsan_enabled} # To suggest vSAN license

Requested number of distinct license types to generate: {num_license_types_requested}

For each license, include these fields in a list of JSON objects:
{column_details_block} # Will include 'Name', 'Key', 'Total', 'Used', 'Expiration Date', 'Features'

Guidelines:
- 'Name': e.g., "VMware vCenter Server 8 Standard", "VMware vSphere 8 Enterprise Plus", "VMware vSAN 8 Standard".
- 'Key': A plausible (but fake) license key format (e.g., "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX").
- 'Total': Number of licenses (e.g., 1 for vCenter, total CPU sockets for ESXi).
- 'Used': Number of licenses used (<= Total).
- 'Expiration Date': A future date, or "Never".
- 'Features': Comma-separated list of key features provided by the license.
"""
VMULTIPATH_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Host Storage Multipathing for an RVTools vMultiPath report.
Provide a realistic JSON data profile for one or more LUNs/disks with multipathing information on a given host, potentially associated with specific datastores.
Host & Storage Context:
- Host Name: {host_name}
- Datastore(s) this host might see: {datastore_names_list} # Comma-separated
- Known HBAs on this host (Names/WWNs): {hba_info_list} # Comma-separated

Requested number of multipathed LUNs/disks to generate for this host: {num_luns_requested}

For each LUN/disk, include these fields in a list of JSON objects:
{column_details_block} # Will include 'Disk' (naa.xxx), 'Policy', 'Path 1', 'Path 1 state', etc.

Guidelines:
- 'Disk' (Device Name) should be a valid NAA identifier (e.g., "naa.6006016012345678123456789abcdef0").
- 'Policy': e.g., "VMW_PSP_RR", "VMW_PSP_MRU", "VMW_PSP_FIXED".
- 'Oper. State': e.g., "Active", "Standby", "Disabled", "Dead".
- For 'Path X' and 'Path X state', provide details for 2-4 paths. Path names can be complex (e.g., "fc.adapter_wwn:target_wwn:lun_id" or "iqn.xxxx:target_iqn:lun_id").
"""

VPORT_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for VMware Standard vSwitch Port Groups for an RVTools vPort report.
Provide a realistic JSON data profile for one or more Port Groups on a given Standard vSwitch.
Host & vSwitch Context:
- Host Name: {host_name}
- Standard vSwitch Name: {vswitch_name}
- Uplinks on this vSwitch: {uplink_names} # Comma-separated

Requested number of Port Groups to generate for this vSwitch: {num_pg_requested}

For each Port Group, include these fields in a list of JSON objects:
{column_details_block} # Will include 'Port Group', 'Switch', 'VLAN', security policies etc.

Guidelines:
- 'Port Group': Name of the port group (e.g., "VM Network", "Management Network", "VLAN100_PG").
- 'VLAN': VLAN ID (e.g., "100") or "Trunk" or "None".
- Security policies ('Promiscuous Mode', 'Mac Changes', 'Forged Transmits') can be 'Accept', 'Reject'.
- Traffic Shaping fields: 'Enabled' (true/false), 'Width' (Avg Bps), 'Peak' (Peak Bps), 'Burst' (Burst KiB).
"""

# --- Utility Functions ---
# ... (All utility functions like generate_random_string, etc. remain unchanged)
def generate_random_string(length=10, prefix=""):
    chars = string.ascii_letters + string.digits;
    if len(prefix) > length: prefix = prefix[:length]
    return prefix + ''.join(random.choice(chars) for _ in range(length - len(prefix)))
def generate_random_boolean(): return random.choice([True, False])
def generate_random_integer(min_val=0, max_val=100): return random.randint(min_val, max_val)
def generate_random_ip_address(): return f"{random.randint(1,254)}.{random.randint(0,254)}.{random.randint(0,254)}.{random.randint(1,254)}"
def generate_random_mac_address(): return "00:50:56:%02x:%02x:%02x" % (random.randint(0,0xff), random.randint(0,0xff), random.randint(0,0xff))
def generate_random_datetime(start_date_str="2022/01/01 00:00:00", days_range=365*2):
    date_format = "%Y/%m/%d %H:%M:%S";
    start_date = datetime.strptime(start_date_str, date_format)
    time_difference = timedelta(seconds=random.randint(0, days_range * 24 * 60 * 60))
    return (start_date + time_difference).strftime(date_format)
def choose_random_from_list(item_list): return random.choice(item_list) if item_list else ""
def generate_vm_name(prefix="vm-"): return generate_random_string(length=10, prefix=prefix)
def generate_uuid(): return str(uuid.uuid4())

def _get_column_descriptions_for_prompt(columns, max_cols=20):
    return ", ".join(random.sample(columns, min(len(columns), max_cols)))

def _get_vdatastore_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vDatastore', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vrp_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vRP', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vsource_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vSource', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vhba_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vHBA', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vnic_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vNIC', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vscvmk_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vSC_VMK', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vswitch_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vSwitch', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_dvswitch_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('dvSwitch', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_dvport_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('dvPortGroup', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vcd_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vCD', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vfileinfo_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vFileInfo', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vpartition_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vPartition', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vsnapshot_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vSnapshot', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vtools_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vTools', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vusb_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vUSB', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vhealth_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vHealth', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vlicense_column_descriptions_for_prompt(): # ... (Unchanged)
    headers = CSV_HEADERS.get('vLicense', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])
def _get_vmultipath_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vMultiPath', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])

def _get_vport_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vPort', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])

# --- Mock AI Row Generation Functions ---
def _call_mock_ai(prompt_template, context, relevant_headers_key, entity_name_for_log):
    # Updated to include 'vPort'
    if relevant_headers_key in ['vDatastore', 'vRP', 'vSource', 'vHBA', 'vNIC', 'vSC_VMK', 'vSwitch', 'dvSwitch', 'dvPortGroup', 'vCD', 'vFileInfo', 'vPartition', 'vSnapshot', 'vTools', 'vUSB', 'vHealth', 'vLicense', 'vMultiPath', 'vPort']:
        context['column_details_block'] = {
            'vDatastore': _get_vdatastore_column_descriptions_for_prompt,
            'vRP': _get_vrp_column_descriptions_for_prompt,
            'vSource': _get_vsource_column_descriptions_for_prompt,
            'vHBA': _get_vhba_column_descriptions_for_prompt,
            'vNIC': _get_vnic_column_descriptions_for_prompt,
            'vSC_VMK': _get_vscvmk_column_descriptions_for_prompt,
            'vSwitch': _get_vswitch_column_descriptions_for_prompt,
            'dvSwitch': _get_dvswitch_column_descriptions_for_prompt,
            'dvPortGroup': _get_dvport_column_descriptions_for_prompt,
            'vCD': _get_vcd_column_descriptions_for_prompt,
            'vFileInfo': _get_vfileinfo_column_descriptions_for_prompt,
            'vPartition': _get_vpartition_column_descriptions_for_prompt,
            'vSnapshot': _get_vsnapshot_column_descriptions_for_prompt,
            'vTools': _get_vtools_column_descriptions_for_prompt,
            'vUSB': _get_vusb_column_descriptions_for_prompt,
            'vHealth': _get_vhealth_column_descriptions_for_prompt,
            'vLicense': _get_vlicense_column_descriptions_for_prompt,
            'vMultiPath': _get_vmultipath_column_descriptions_for_prompt,
            'vPort': _get_vport_column_descriptions_for_prompt, # Added vPort
        }[relevant_headers_key]()
    else:
        context['column_list'] = _get_column_descriptions_for_prompt(CSV_HEADERS[relevant_headers_key])
    prompt = prompt_template.format(**context)
    mock_ai_data = {}
    if relevant_headers_key == "vInfo": # ... (vInfo mock data as before)
        mock_ai_data = {
            "Annotation": f"AI: VM {context['vm_name']} - OS: {context['os_tools']}. Purpose: {choose_random_from_list(['AI_WebApp', 'AI_DB', 'AI_Analytics'])}",
            "Firmware": choose_random_from_list(["bios", "efi"]), "HW version": choose_random_from_list(["17", "19", "20"]),
            "Resource pool": f"/{context['datacenter_name']}/{context['cluster_name']}/Resources/AI-Pool-{generate_random_string(3)}",
            "Folder": f"/{context['datacenter_name']}/vm/AI-Managed/{generate_random_string(3)}/",
            "Total disk capacity MiB": generate_random_integer(context.get("memory_gb", 2) * 10 * 1024, context.get("memory_gb", 2) * 50 * 1024)
        }
        if context["power_state"] == "poweredOff": mock_ai_data["Heartbeat"] = "gray"
    elif relevant_headers_key == "vHost": # ... (vHost mock data as before)
        mock_ai_data = { "Vendor": "AI Vendor-" + choose_random_from_list(["DellAI", "HPAI", "SupermicroAI"]),
            "Model": "AI Model-" + context['cpu_model'].split(" ")[0] + "_" + generate_random_string(4),
            "Time Zone Name": choose_random_from_list(["America/Los_Angeles", "Europe/Berlin", "Asia/Tokyo"]),
            "NTP Server(s)": "0.ai.pool.ntp.org, 1.ai.pool.ntp.org", "BIOS Vendor": choose_random_from_list(["AI BIOS Inc.", "Future Systems AI"]),
            "BIOS Version": generate_random_string(prefix="AI-BIOS-", length=12), "BIOS Date": generate_random_datetime(start_date_str="2022/01/01"),
            "Service tag": generate_random_string(7).upper()+"-AI",}
    elif relevant_headers_key == "vDisk": # ... (vDisk mock data as before)
        mock_ai_data = { "Disk Mode": choose_random_from_list(["persistent", "independent_persistent", "independent_nonpersistent"]),
            "Sharing mode": choose_random_from_list(["nobussharing", "virtualsharing", "physicalsharing"]), "Thin": str(generate_random_boolean()),
            "Eagerly Scrub": str(generate_random_boolean() if mock_ai_data.get("Thin") == "False" else False),
            "Controller": f"AI SCSI Controller {context['disk_index']}",}
    elif relevant_headers_key == "vNetwork": # ... (vNetwork mock data as before)
        mock_ai_data = { "Adapter": choose_random_from_list(["VMXNET3-AI", "E1000E-AI", "SRIOV-AI"]),
            "Network": f"{context['datacenter']}-AISegment-{generate_random_integer(200,299)}",
            "Switch": f"AI-DVSwitch-{context['datacenter']}", "Type": "AI Ethernet",}
    elif relevant_headers_key == "vCluster": # ... (vCluster mock data as before)
        mock_ai_data = {
            "HA enabled": str(generate_random_boolean()), "DRS enabled": str(generate_random_boolean()),
            "DRS default VM behavior": choose_random_from_list(["fullyAutomated", "manual", "partiallyAutomated"]),
            "AdmissionControlEnabled": str(generate_random_boolean()),
            "VM Monitoring": choose_random_from_list(["vmMonitoringDisabled", "vmMonitoringOnly", "vmAndAppMonitoring"]),
        }
    elif relevant_headers_key == "vDatastore": # ... (vDatastore mock data as before)
        ds_type = choose_random_from_list(['VMFS', 'NFS', 'vSAN'])
        capacity_mib = generate_random_integer(1 * 1024 * 1024, 10 * 1024 * 1024)
        free_mib = generate_random_integer(int(capacity_mib * 0.1), int(capacity_mib * 0.8))
        provisioned_mib = capacity_mib - free_mib + generate_random_integer(0, int(capacity_mib*0.2))
        mock_ai_data = {
            "Name": context["datastore_name"], "Config status": "green",
            "Address": f"nfs://ai-filer.corp.local:/vol/{context['datastore_name']}" if ds_type == 'NFS' else (f"vsan:{generate_uuid()}" if ds_type == 'vSAN' else ""),
            "Accessible": "true", "Type": ds_type, "Capacity MiB": str(capacity_mib), "Provisioned MiB": str(provisioned_mib),
            "In Use MiB": str(provisioned_mib - free_mib if provisioned_mib > free_mib else generate_random_integer(0, provisioned_mib)),
            "Free MiB": str(free_mib), "Free %": str(round((free_mib / capacity_mib) * 100, 1) if capacity_mib > 0 else 0),
            "SIOC enabled": "false", "SIOC Threshold": "30",
            "VMFS Upgradeable": "true" if ds_type == 'VMFS' else "false",
            "URL": f"ds:///vmfs/volumes/{generate_uuid()}/" if ds_type == 'VMFS' else (f"ds://vsan/{context['datastore_name']}" if ds_type == 'vSAN' else ""),
            "Object ID": f"datastore-ai-{generate_random_integer(1000,1999)}",}
    elif relevant_headers_key == "vRP": # ... (vRP mock data as before)
        mock_ai_data = {
            "Status": "green", "CPU limit": -1, "CPU reservation": generate_random_integer(1000, 5000), "CPU shares": "normal", "CPU level": "normal",
            "CPU expandableReservation": json.dumps(generate_random_boolean()),
            "Mem limit": -1, "Mem reservation": generate_random_integer(4096, 16384), "Mem shares": "normal", "Mem level": "normal",
            "Mem expandableReservation": json.dumps(generate_random_boolean()),
            "overallCpuUsage": generate_random_integer(500, 2000), "guestMemoryUsage": generate_random_integer(1024, 8192),
            "QS overallCpuDemand": generate_random_integer(600,2500), "QS guestMemoryUsage": generate_random_integer(1000,8000),}
    elif relevant_headers_key == "vSource": # ... (vSource mock data as before)
        ver_parts = context['target_version'].split(' ')
        base_ver = ver_parts[0]
        patch_str = "".join(ver_parts[1:]) if len(ver_parts) > 1 else ""
        build = generate_random_integer(20000000, 23000000)
        mock_ai_data = {
            "Name": context.get('vcenter_ip'), "OS type": "VMware Photon OS (AI Generated)", "API type": "VirtualCenter",
            "API version": f"{base_ver}.{patch_str[1] if patch_str.startswith('U') and len(patch_str)>1 else '0'}",
            "Version": base_ver, "Patch level": patch_str, "Build": str(build),
            "Fullname": f"VMware vCenter Server {context['target_version']} build-{build} (AI)",
            "Product name": "VMware vCenter Server (AI Edition)", "Product version": f"{context['target_version']} (AI)",
            "Product line": "vpx", "Vendor": "VMware, Inc. (AI Verified)" }
    elif relevant_headers_key == "vHBA": # ... (vHBA mock data as before)
        hba_list = []
        for i in range(context.get('num_hbas_requested', 1)):
            hba_type = choose_random_from_list(['Fibre Channel', 'iSCSI Software Adapter', 'SAS Controller', 'RAID Controller'])
            device_name = f"vmhba{i}"
            wwn = ""
            if hba_type == 'Fibre Channel':
                driver, model = choose_random_from_list([('lpfc','Emulex LightPulse LPe32002-AI'),('qlnativefc','QLogic QLE2772-AI')])
                wwn = ":".join([generate_random_string(2, prefix='').lower() for _ in range(8)])
            elif hba_type == 'iSCSI Software Adapter':
                driver, model = 'iscsi_vmk', 'iSCSI Software Adapter AI'
                wwn = f"iqn.1998-01.com.vmware:{context.get('host_name','unknownhost')}-ai-{generate_random_string(8).lower()}"
            else:
                driver, model = choose_random_from_list([('lsi_mr3s','PERC H740P AI'),('smartpqi','Smart Array P408i-a AI')])
            hba_list.append({
                "Device": device_name, "Type": hba_type, "Status": "Online",
                "Driver": driver, "Model": model, "WWN": wwn,
                "Bus": str(generate_random_integer(0,3)),
                "Pci": f"0000:0{generate_random_integer(1,9)}:00.{i}"
            })
        mock_ai_data = hba_list
    elif relevant_headers_key == "vNIC": # ... (vNIC mock data as before)
        nic_list = []
        for i in range(context.get('num_nics_requested',1)):
            speed_val = choose_random_from_list([1000, 10000, 25000, 40000])
            nic_list.append({
                "Network Device": f"vmnic{i}",
                "Driver": choose_random_from_list(['ixgben-ai', 'nmlx5_core-ai', 'bnxtnet-ai']),
                "Speed": f"{speed_val} Mbps", "Duplex": "Full", "MAC": generate_random_mac_address(),
                "Switch": f"PhysicalSwitch-AI-{chr(65+i)}",
                "Uplink port": f"Gi{generate_random_integer(1,2)}/0/{generate_random_integer(1,24)}",
                "PCI": f"0000:0{generate_random_integer(1,18)}:00.{i}",
                "WakeOn": json.dumps(generate_random_boolean())
            })
        mock_ai_data = nic_list
    elif relevant_headers_key == "vSC_VMK": # ... (vSC_VMK mock data as before)
        vmk_list = []
        base_ip_parts = generate_random_ip_address().split('.')
        for i in range(context.get('num_vmk_requested',1)):
            services = []
            if i == 0 : services.append("Management")
            if generate_random_boolean(): services.append("vMotion")
            if generate_random_boolean() and context.get('datastore_types_on_host',[]).count('vSAN') > 0 : services.append("vSAN")
            vmk_list.append({
                "Device": f"vmk{i}", "Port Group": f"{services[0] if services else 'VMkernel'}-PG-AI",
                "Mac Address": generate_random_mac_address(), "DHCP": json.dumps(False),
                "IP Address": f"{base_ip_parts[0]}.{base_ip_parts[1]}.{generate_random_integer(10,200)}.{generate_random_integer(10,250)}",
                "Subnet mask": "255.255.255.0", "Gateway": f"{base_ip_parts[0]}.{base_ip_parts[1]}.{base_ip_parts[2]}.1",
                "MTU": choose_random_from_list([1500, 9000]), "Services": ", ".join(services) if services else "VMkernel"
            })
        mock_ai_data = vmk_list
    elif relevant_headers_key == "vSwitch": # ... (vSwitch mock data as before)
        vswitch_list = []
        phys_nics = context.get('physical_nic_names', [])
        for i in range(context.get('num_vswitches_requested',1)):
            num_uplinks_for_switch = generate_random_integer(1, len(phys_nics) if phys_nics else 1)
            selected_uplinks_for_switch = random.sample(phys_nics, min(num_uplinks_for_switch, len(phys_nics))) if phys_nics else [f"vmnic{j+i*2}" for j in range(num_uplinks_for_switch)]
            vswitch_list.append({
                "Switch": f"vSwitch{i}-AI", "# Ports": 128, "Free Ports": generate_random_integer(60,120),
                "Promiscuous Mode": "Reject", "Mac Changes": "Accept", "Forged Transmits": "Accept",
                "Uplinks": ",".join(selected_uplinks_for_switch), "MTU": 1500 })
        mock_ai_data = vswitch_list
    elif relevant_headers_key == "dvSwitch": # ... (dvSwitch mock data as before)
        dvswitch_list = []
        host_names = context.get('host_names_in_dc', [])
        for i in range(context.get('num_dvswitches_requested',1)):
            dvs_name = f"DVS_{context['datacenter_name']}_AI_{i+1}"
            selected_hosts = random.sample(host_names, k=min(len(host_names), generate_random_integer(1, len(host_names)))) if host_names else []
            dvswitch_list.append({
                "Switch": dvs_name, "Name": dvs_name, "Datacenter": context['datacenter_name'],
                "Vendor": "VMware AI", "Version": choose_random_from_list(["7.0.3 AI", "8.0.1 AI"]),
                "Host members": ",".join(selected_hosts),
                "Max Ports": str(generate_random_integer(512, 8192)),
                "# Ports": str(generate_random_integer(128, 512)),
                "# VMs": str(generate_random_integer(0, 200)),
                "CDP Type": choose_random_from_list(["listen", "advertise", "both", "disabled"]),
                "Max MTU": str(choose_random_from_list([1500,9000,9216])),
                "Object ID": f"dvs-ai-{generate_random_integer(100,199)}"
            })
        mock_ai_data = dvswitch_list
    elif relevant_headers_key == "dvPortGroup": # ... (dvPortGroup mock data as before)
        dvport_list = []
        for i in range(context.get('num_items_requested',1)):
            vlan_id = generate_random_integer(100, 199)
            dvport_list.append({
                "Name": f"DPG_VLAN{vlan_id}_AI_{i}",
                "Switch": context.get('dvs_name'),
                "Port Binding": choose_random_from_list(["staticBinding", "dynamicBinding", "ephemeral"]),
                "VLAN": f"VLAN {vlan_id}", "VLAN type": "VLAN",
                "# Ports": str(choose_random_from_list([0, 8, 16, 24, 64, 128, 256])),
                "Allow Promiscuous": json.dumps(False),
                "Mac Changes": json.dumps(True),
                "Forged Transmits": json.dumps(True),
                "Object ID": f"dvportgroup-ai-{generate_random_integer(100,199)}"
            })
        mock_ai_data = dvport_list
    elif relevant_headers_key == "vCD": # ... (vCD mock data as before)
        connected = generate_random_boolean()
        device_type = "Client Device"
        if connected:
            if generate_random_boolean() and context.get('datastore_names'):
                ds_name = random.choice(context['datastore_names'])
                iso_file = choose_random_from_list(["windows_server_2022.iso", "ubuntu-desktop.iso", "vmware-tools.iso", "custom_app.iso"])
                device_type = f"[{ds_name}] ISOs/{iso_file}"
        else:
            device_type = choose_random_from_list(["IDE", ""])
        mock_ai_data = {
            "Device Node": "CD/DVD drive 1 (AI)", "Connected": json.dumps(connected),
            "Starts Connected": json.dumps(connected if generate_random_boolean() else False),
            "Device Type": device_type, "Annotation": f"AI configured CD Drive for {context['vm_name']}"
        }
    elif relevant_headers_key == "vFileInfo": # ... (vFileInfo mock data as before)
        vm_name = context['vm_name']; datastore = context['datastore_name']
        disks = context.get('disk_info_list', [f"{vm_name}.vmdk"])
        files = []
        files.append({"File Name": f"{vm_name}.vmx", "File Type": "VMX (AI)", "File Size in bytes": generate_random_integer(3000, 9000), "Path": f"[{datastore}] {vm_name}/{vm_name}.vmx"})
        files.append({"File Name": f"{vm_name}.nvram", "File Type": "NVRAM (AI)", "File Size in bytes": generate_random_integer(8192, 65536), "Path": f"[{datastore}] {vm_name}/{vm_name}.nvram"})
        files.append({"File Name": "vmware.log", "File Type": "LOG (AI)", "File Size in bytes": generate_random_integer(50000, 10000000), "Path": f"[{datastore}] {vm_name}/vmware.log"})
        for disk_path_name in disks:
            actual_disk_name = disk_path_name.split('/')[-1] if '/' in disk_path_name else disk_path_name
            files.append({"File Name": actual_disk_name, "File Type": "VMDK Descriptor (AI)", "File Size in bytes": generate_random_integer(1000, 5000), "Path": f"[{datastore}] {vm_name}/{actual_disk_name}"})
            files.append({"File Name": actual_disk_name.replace('.vmdk', '-flat.vmdk'), "File Type": "VMDK Flat (AI)", "File Size in bytes": generate_random_integer(10*1024*1024, 100*1024*1024*1024), "Path": f"[{datastore}] {vm_name}/{actual_disk_name.replace('.vmdk','-flat.vmdk')}"})
        mock_ai_data = files
    elif relevant_headers_key == "vPartition": # ... (vPartition mock data as before)
        partitions = []
        disk_cap_mib = context.get('disk_capacity_mib', 10240)
        num_partitions_ai = generate_random_integer(1,2)
        if num_partitions_ai == 1:
            cap = disk_cap_mib
            cons = int(cap * random.uniform(0.1, 0.9))
            partitions.append({
                "Disk": "C:\\ (AI)" if "win" in context.get('os_type','').lower() else "/ (AI)",
                "Capacity MiB": cap, "Consumed MiB": cons
            })
        elif num_partitions_ai == 2:
            cap1 = int(disk_cap_mib * random.uniform(0.3, 0.7))
            cons1 = int(cap1 * random.uniform(0.1, 0.9))
            cap2 = disk_cap_mib - cap1
            cons2 = int(cap2 * random.uniform(0.1, 0.9))
            if "win" in context.get('os_type','').lower():
                partitions.append({"Disk": "C:\\ (AI)", "Capacity MiB": cap1, "Consumed MiB": cons1})
                partitions.append({"Disk": "D:\\ (AI)", "Capacity MiB": cap2, "Consumed MiB": cons2})
            else:
                partitions.append({"Disk": "/ (AI)", "Capacity MiB": cap1, "Consumed MiB": cons1})
                partitions.append({"Disk": "/var (AI)", "Capacity MiB": cap2, "Consumed MiB": cons2})
        mock_ai_data = partitions
    elif relevant_headers_key == "vSnapshot": # ... (vSnapshot mock data as before)
        snap_list = []
        num_snaps = context.get('num_snapshots_requested', 0)
        vm_creation_dt = datetime.strptime(context.get('vm_creation_date', "2020/01/01 00:00:00"), "%Y/%m/%d %H:%M:%S")
        for i in range(num_snaps):
            snap_date = vm_creation_dt + timedelta(days=generate_random_integer(1, 30), hours=generate_random_integer(1,23))
            snap_name = f"AI_Snapshot_{i+1}_of_{context['vm_name']}"
            snap_list.append({
                "Name": snap_name, "Description": f"AI generated snapshot {i+1}",
                "Date / time": snap_date.strftime("%Y/%m/%d %H:%M:%S"),
                "Size MiB (vmsn)": generate_random_integer(100,2048),
                "Size MiB (total)": generate_random_integer(2000,20480),
                "Quiesced": json.dumps(generate_random_boolean()),
                "State": choose_random_from_list(["PoweredOff", "PoweredOn", "Suspended", "Valid"])
            })
        mock_ai_data = snap_list
    elif relevant_headers_key == "vTools": # ... (vTools mock data as before)
        tools_status = choose_random_from_list(['OK', 'Not running', 'Out of date', 'Not installed'])
        tools_version = ""
        if tools_status != "Not installed":
            tools_version = str(generate_random_integer(11000, 12500))
        mock_ai_data = {
            "Tools": tools_status, "Tools Version": tools_version,
            "Required Version": str(int(tools_version) + 100) if tools_status == "Out of date" else tools_version,
            "Upgradeable": json.dumps(tools_status == "Out of date"),
            "Upgrade Policy": "manual", "Sync time": json.dumps(tools_status == "OK"),
            "App status": "Ok" if tools_status == "OK" else "Unknown",
            "Heartbeat status": "green" if tools_status == "OK" else "gray"
        }
    elif relevant_headers_key == "vUSB": # ... (vUSB mock data as before)
        usb_devices = []
        for i in range(context.get('num_usb_requested', 0)):
            connected = generate_random_boolean()
            usb_devices.append({
                "Device Node": f"USB {i+1} (AI)",
                "Device Type": choose_random_from_list(["Generic USB Device", "USB Flash Drive", "USB Security Key"]),
                "Connected": json.dumps(connected),
                "Family": choose_random_from_list(["storage", "hid", "security", "other"]),
                "Speed": choose_random_from_list(["1.1", "2.0", "3.0", "3.1"]),
                "EHCI enabled": json.dumps(generate_random_boolean()),
                "Auto connect": json.dumps(connected and generate_random_boolean())
            })
        mock_ai_data = usb_devices
    elif relevant_headers_key == "vHealth": # ... (vHealth mock data as before)
        health_items = []
        for _ in range(context.get('num_items_requested', 3)):
            msg_type = choose_random_from_list(["Green", "Yellow", "Red", "Info"])
            name, message = "Unknown Health Check", "Status Undetermined by AI"
            if msg_type == "Green":
                name = choose_random_from_list(["Storage status", "Hypervisor health", "Network connectivity"])
                message = f"{name} is operating normally according to AI."
            elif msg_type == "Yellow":
                name = choose_random_from_list(["License usage", "Certificate validity", "Resource utilization peak"])
                message = f"AI reports {name} is nearing threshold or requires attention."
            elif msg_type == "Red":
                name = choose_random_from_list(["Host connection failure", "Critical service down", "Datastore inaccessible alarm"])
                message = f"AI Alert: Critical issue detected with {name}."
            elif msg_type == "Info":
                name = choose_random_from_list(["Scheduled maintenance task", "System update check", "Security scan info"])
                message = f"AI Info: {name} - {generate_random_string(20)}."
            health_items.append({"Name": name, "Message": message, "Message type": msg_type})
        mock_ai_data = health_items
    elif relevant_headers_key == "vLicense": # ... (vLicense mock data as before)
        licenses = []
        num_to_gen = context.get('num_license_types_requested', 2)
        if num_to_gen >=1:
            licenses.append({
                "Name": f"VMware vCenter Server {context.get('vcenter_version','8 Standard')} (AI)",
                "Key": '-'.join([generate_random_string(5).upper() for _ in range(5)]),
                "Total": "1", "Used": "1", "Cost Unit": "Instance",
                "Expiration Date": "Never",
                "Features": "vCenter Server management, AI License Provisioning"
            })
        if num_to_gen >=2:
            total_sockets = context.get('total_cpu_sockets', generate_random_integer(2,16))
            licenses.append({
                "Name": f"VMware vSphere {context.get('vcenter_version','8')} Enterprise Plus (AI)",
                "Key": '-'.join([generate_random_string(5).upper() for _ in range(5)]),
                "Total": str(total_sockets), "Used": str(generate_random_integer(1, total_sockets)),
                "Expiration Date": "Never", "Cost Unit": "CPU Package",
                "Features": "DRS, HA, vMotion, Storage vMotion, AI Insights"
            })
        if context.get('vsan_enabled') and num_to_gen >=3:
            total_sockets_vsan = context.get('total_cpu_sockets', generate_random_integer(2,16))
            licenses.append({
                "Name": f"VMware vSAN {context.get('vcenter_version','8')} Advanced (AI)",
                "Key": '-'.join([generate_random_string(5).upper() for _ in range(5)]),
                "Total": str(total_sockets_vsan), "Used": str(generate_random_integer(1, total_sockets_vsan)),
                "Expiration Date": "2026/12/31 00:00:00", "Cost Unit": "CPU Package",
                "Features": "vSAN All-Flash, Deduplication, Compression, AI-Assisted Storage Tiering"
            })
        mock_ai_data = licenses
    elif relevant_headers_key == "vMultiPath": # New AI mock for vMultiPath
        lun_list = []
        for i in range(context.get('num_luns_requested',1)):
            lun_item = {
                "Disk": f"naa.6{generate_random_string(30,'').lower()}",
                "Display name": f"AI LUN {context.get('host_name')}-{i}",
                "Datastore": random.choice(context.get('datastore_names_list',['ai_ds_fallback'])) if context.get('datastore_names_list') else 'ai_ds_fallback',
                "Policy": choose_random_from_list(['VMW_PSP_RR', 'VMW_PSP_MRU', 'VMW_PSP_FIXED']),
                "Oper. State": "Active",
                "Vendor": "AI-StorageCorp", "Model": "AI-DiskArray 5000", "Revision": "1.AI", "Level":"Tier-1 AI"
            }
            num_paths = generate_random_integer(2,4)
            for p_idx in range(1, num_paths + 1):
                lun_item[f"Path {p_idx}"] = f"fc.ai_adapter_{p_idx}:ai_target_{p_idx}:L{i}"
                lun_item[f"Path {p_idx} state"] = "Active/Optimized" if p_idx % 2 == 1 else "Active/Non-Optimized"
            lun_list.append(lun_item)
        mock_ai_data = lun_list
    elif relevant_headers_key == "vPort": # Added vPort AI mock
        pg_list = []
        for i in range(context.get('num_pg_requested', 1)):
            vlan_id = generate_random_integer(10, 999)
            ts_enabled = generate_random_boolean()
            pg_item = {
                "Port Group": f"AI_PG_VLAN{vlan_id}_{i}_{generate_random_string(3)}", # Added randomness
                "Switch": context.get('vswitch_name'),
                "VLAN": str(vlan_id) if generate_random_boolean() else choose_random_from_list(["None", "All (Trunk)"]),
                "Promiscuous Mode": choose_random_from_list(["Reject", "Accept"]),
                "Mac Changes": choose_random_from_list(["Reject", "Accept"]),
                "Forged Transmits": choose_random_from_list(["Reject", "Accept"]),
                "Traffic Shaping": json.dumps(ts_enabled), # Use json.dumps for boolean to string
            }
            if ts_enabled:
                pg_item["Width"] = generate_random_integer(10000, 500000) # Avg Bps
                pg_item["Peak"] = int(pg_item["Width"] * random.uniform(1.2, 2.0))
                pg_item["Burst"] = int(pg_item["Peak"] * random.uniform(0.1, 0.5))
            else: # Ensure these are 0 if shaping is disabled, matching RVTools
                pg_item["Width"] = 0
                pg_item["Peak"] = 0
                pg_item["Burst"] = 0
            pg_list.append(pg_item)
        mock_ai_data = pg_list
    return mock_ai_data

# ... (All generate_<CSV>_row_ai functions remain unchanged)
def generate_vinfo_row_ai(vm_r):
    context = {**vm_r, 'vm_name': vm_r["VM"], 'os_tools': vm_r["OS according to the VMware Tools"],
               'datacenter_name': vm_r["Datacenter"], 'cluster_name': vm_r["Cluster"], 'power_state': vm_r["Powerstate"],
               'memory_gb': vm_r.get("Memory", 2048) // 1024}
    return _call_mock_ai(VINFO_AI_PROMPT_TEMPLATE, context, "vInfo", vm_r["VM"])
def generate_vhost_row_ai(host_r):
    context = {**host_r, 'host_name': host_r["Host"], 'cpu_count': host_r["# CPU"],
               'cores_per_cpu': host_r["Cores per CPU"], 'memory_mb': host_r["# Memory"],
               'esx_version': host_r["ESX Version"], 'cpu_model': host_r["CPU Model"],
               'datacenter_name': host_r["Datacenter"], 'cluster_name': host_r["Cluster"]}
    return _call_mock_ai(VHOST_AI_PROMPT_TEMPLATE, context, "vHost", host_r["Host"])
def generate_vdisk_row_ai(vm_r, disk_index, disk_label_for_prompt):
    context = {**vm_r, 'vm_name': vm_r["VM"], 'disk_label': disk_label_for_prompt, 'disk_index': disk_index,
               'power_state': vm_r["Powerstate"], 'datastore': vm_r["Datastore"]}
    return _call_mock_ai(VDISK_AI_PROMPT_TEMPLATE, context, "vDisk", f"{vm_r['VM']}-{disk_label_for_prompt}")
def generate_vnetwork_row_ai(vm_r, nic_index, nic_label_for_prompt):
    context = {**vm_r, 'vm_name': vm_r["VM"], 'nic_label': nic_label_for_prompt, 'nic_index': nic_index,
               'power_state': vm_r["Powerstate"], 'primary_ip': vm_r.get("Primary IP Address","N/A"),
               'is_connected': str(vm_r["Powerstate"] == "poweredOn"), 'datacenter': vm_r["Datacenter"]}
    return _call_mock_ai(VNETWORK_AI_PROMPT_TEMPLATE, context, "vNetwork", f"{vm_r['VM']}-{nic_label_for_prompt}")
def generate_vcluster_row_ai(cluster_r):
    context = {**cluster_r, 'cluster_name': cluster_r["Name"], 'datacenter_name': cluster_r["Datacenter"],
               'num_hosts': cluster_r.get("NumHosts",0),
               'total_cpu_cores': cluster_r.get("TotalCpuCores",0),
               'total_memory_gb': cluster_r.get("TotalMemoryGB",0) }
    return _call_mock_ai(VCLUSTER_AI_PROMPT_TEMPLATE, context, "vCluster", cluster_r["Name"])
def generate_vdatastore_row_ai(ds_agg_data):
    context = {
        'datastore_name': ds_agg_data['Name'],
        'datacenter_name': ds_agg_data.get('Datacenter', 'UnknownDC'),
        'num_vms_on_datastore': ds_agg_data.get('vms_on_ds_count', 0)
    }
    return _call_mock_ai(VDATASTORE_AI_PROMPT_TEMPLATE, context, "vDatastore", ds_agg_data['Name'])
def generate_vrp_row_ai(rp_context):
    return _call_mock_ai(VRP_AI_PROMPT_TEMPLATE, rp_context, "vRP", rp_context['rp_name'])
def generate_vsource_row_ai(vsource_context):
    return _call_mock_ai(VSOURCE_AI_PROMPT_TEMPLATE, vsource_context, "vSource", vsource_context['vcenter_ip'])
def generate_vhba_row_ai(vhba_context):
    return _call_mock_ai(VHBA_AI_PROMPT_TEMPLATE, vhba_context, "vHBA", vhba_context['host_name'])
def generate_vnic_row_ai(vnic_context):
    return _call_mock_ai(VNIC_AI_PROMPT_TEMPLATE, vnic_context, "vNIC", vnic_context['host_name'])
def generate_vscvmk_row_ai(vmk_context):
    return _call_mock_ai(VSCVMK_AI_PROMPT_TEMPLATE, vmk_context, "vSC_VMK", vmk_context['host_name'])
def generate_vswitch_row_ai(vswitch_context):
    return _call_mock_ai(VSWITCH_AI_PROMPT_TEMPLATE, vswitch_context, "vSwitch", vswitch_context['host_name'])
def generate_dvswitch_row_ai(dvswitch_context):
    return _call_mock_ai(DVSWITCH_AI_PROMPT_TEMPLATE, dvswitch_context, "dvSwitch", dvswitch_context['datacenter_name'])
def generate_dvport_row_ai(dvport_context):
    return _call_mock_ai(DVPORT_AI_PROMPT_TEMPLATE, dvport_context, "dvPortGroup", dvport_context['dvs_name'])
def generate_vcd_row_ai(vcd_context):
    return _call_mock_ai(VCD_AI_PROMPT_TEMPLATE, vcd_context, "vCD", vcd_context['vm_name'])
def generate_vfileinfo_row_ai(file_info_context):
    return _call_mock_ai(VFILEINFO_AI_PROMPT_TEMPLATE, file_info_context, "vFileInfo", file_info_context['vm_name'])
def generate_vpartition_row_ai(partition_context):
    return _call_mock_ai(VPARTITION_AI_PROMPT_TEMPLATE, partition_context, "vPartition", f"{partition_context['vm_name']}_{partition_context['disk_label']}")
def generate_vsnapshot_row_ai(snapshot_context):
    return _call_mock_ai(VSNAPSHOT_AI_PROMPT_TEMPLATE, snapshot_context, "vSnapshot", snapshot_context['vm_name'])
def generate_vtools_row_ai(vtools_context):
    return _call_mock_ai(VTOOLS_AI_PROMPT_TEMPLATE, vtools_context, "vTools", vtools_context['vm_name'])
def generate_vusb_row_ai(vusb_context):
    return _call_mock_ai(VUSB_AI_PROMPT_TEMPLATE, vusb_context, "vUSB", vusb_context['vm_name'])
def generate_vhealth_row_ai(health_context):
    return _call_mock_ai(VHEALTH_AI_PROMPT_TEMPLATE, health_context, "vHealth", "vCenterHealth")
def generate_vlicense_row_ai(license_context):
    return _call_mock_ai(VLICENSE_AI_PROMPT_TEMPLATE, license_context, "vLicense", "EnvironmentLicenses")

def generate_vmultipath_row_ai(multipath_context):
    return _call_mock_ai(VMULTIPATH_AI_PROMPT_TEMPLATE, multipath_context, "vMultiPath", multipath_context['host_name'])

def generate_vport_row_ai(vport_context): # Added
    return _call_mock_ai(VPORT_AI_PROMPT_TEMPLATE, vport_context, "vPort", f"{vport_context['host_name']}_{vport_context['vswitch_name']}")

# --- CSV Generation Functions ---
# ... (generate_vinfo_csv, generate_vhost_csv, etc. functions remain the same as previous correct version)
def generate_vinfo_csv(num_rows=10, use_ai=False): # ... (vInfo function as in previous correct version)
    filepath = os.path.join(CSV_SUBDIR, "RVTools_tabvInfo.csv"); headers = CSV_HEADERS["vInfo"]
    ENVIRONMENT_DATA["vms"].clear(); ENVIRONMENT_DATA["hosts"].clear(); ENVIRONMENT_DATA["clusters"].clear(); ENVIRONMENT_DATA["resource_pools"].clear()
    host_names_generated = set(); cluster_names_generated = set()
    if not ENVIRONMENT_DATA.get("vcenter_ip"): ENVIRONMENT_DATA["vcenter_ip"] = f"vcenter-{generate_random_string(4).lower()}.corp.local"
    if not ENVIRONMENT_DATA.get("vcenter_uuid"): ENVIRONMENT_DATA["vcenter_uuid"] = generate_uuid()
    vi_sdk_server_name = ENVIRONMENT_DATA["vcenter_ip"]
    vi_sdk_server_uuid = ENVIRONMENT_DATA["vcenter_uuid"]
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers); writer.writeheader()
        for i in range(num_rows):
            vm_r = {}
            vm_r["VM"] = generate_vm_name(prefix=f"vm-{i:03d}-")
            vm_r["Powerstate"] = choose_random_from_list(["poweredOn", "poweredOff"])
            vm_r["VM UUID"] = generate_uuid(); vm_r["SMBIOS UUID"] = generate_uuid()
            vm_r["Datacenter"] = choose_random_from_list(["DC1", "DC2"])
            vm_r["OS according to the VMware Tools"] = choose_random_from_list(["Windows Server 2019", "Ubuntu Linux (64-bit)"])
            vm_r["OS according to the configuration file"] = choose_random_from_list(["windows2019srv_64Guest", "ubuntu64Guest"])
            vm_r["VM ID"] = f"vm-{generate_random_integer(100, 9999)}"
            vm_r["VI SDK Server"] = vi_sdk_server_name; vm_r["VI SDK UUID"] = vi_sdk_server_uuid
            vm_r["CPUs"] = generate_random_integer(1, 8)
            vm_r["Memory"] = random.choice([1024, 2048, 4096, 8192, 16384])
            vm_r["Annotation"] = f"RVTools Gen; VM:{i}; Created:{generate_random_datetime(days_range=5)}"
            vm_r["Cluster"] = f"{vm_r['Datacenter']}-Cluster{generate_random_integer(1,2)}"
            vm_r["Host"] = f"esxi-host{generate_random_integer(1,3):02d}.{vm_r['Cluster'].lower()}.local"
            vm_r["Primary IP Address"] = generate_random_ip_address() if vm_r["Powerstate"] == "poweredOn" else ""
            vm_r["DNS Name"] = f"{vm_r['VM'].lower().replace('-','')}.{vm_r['Cluster'].lower()}.corp" if vm_r["Powerstate"] == "poweredOn" else ""
            vm_r["CoresPerSocket"] = (lambda c: choose_random_from_list([cps for cps in [1,2,4,c] if c > 0 and c % cps == 0 and cps <= c]) or 1)(vm_r.get("CPUs",1))
            vm_r["Datastore"] = f"datastore-{vm_r['Cluster'].lower()}-{generate_random_integer(1,3)}"
            vm_r["Creation date"] = generate_random_datetime(start_date_str="2020/01/01 00:00:00", days_range=365*3)
            vm_r["HW version"] = choose_random_from_list(["vmx-15", "vmx-17", "vmx-19", "vmx-20"])
            if generate_random_boolean():
                 vm_r["Resource pool"] = f"/{vm_r['Datacenter']}/{vm_r['Cluster']}/Resources/RP-{generate_random_string(length=4,prefix=vm_r['Cluster'][-1]+'-')}"
            else:
                 vm_r["Resource pool"] = f"/{vm_r['Datacenter']}/{vm_r['Cluster']}/Resources"
            ENVIRONMENT_DATA["vms"].append(vm_r)
            if vm_r["Host"] not in host_names_generated:
                host_r_env = { "Host": vm_r["Host"], "Datacenter": vm_r["Datacenter"], "Cluster": vm_r["Cluster"],
                    "# CPU": choose_random_from_list([2,4,8,16]), "Cores per CPU": choose_random_from_list([4,6,8,10,12,16]),
                    "# Memory": random.choice([65536, 131072, 262144, 524288]),
                    "ESX Version": choose_random_from_list(["VMware ESXi 7.0.3 build-20328353", "VMware ESXi 8.0.1 build-21493926"]),
                    "CPU Model": choose_random_from_list(["Intel(R) Xeon(R) Gold 6248R CPU @ 3.00GHz", "AMD EPYC 7742 64-Core Processor"]),
                    "UUID": generate_uuid(), "Object ID": f"host-{generate_random_integer(10,500)}",
                    "VI SDK Server": vi_sdk_server_name, "VI SDK UUID": vi_sdk_server_uuid }
                ENVIRONMENT_DATA["hosts"].append(host_r_env); host_names_generated.add(vm_r["Host"])
            if vm_r["Cluster"] not in cluster_names_generated:
                cluster_r_env = { "Name": vm_r["Cluster"], "Datacenter": vm_r["Datacenter"],
                                "Object ID": f"domain-c{generate_random_integer(10,500)}",
                                "VI SDK Server": vi_sdk_server_name, "VI SDK UUID": vi_sdk_server_uuid}
                ENVIRONMENT_DATA["clusters"].append(cluster_r_env); cluster_names_generated.add(vm_r["Cluster"])
            row_data = {h: "" for h in headers}; row_data.update({
                "VM": vm_r["VM"], "Powerstate": vm_r["Powerstate"], "Template": "False", "SRM Placeholder": "False",
                "Config status": "green", "DNS Name": vm_r["DNS Name"],
                "Connection state": "connected" if vm_r["Powerstate"] == "poweredOn" else "disconnected",
                "Guest state": "running" if vm_r["Powerstate"] == "poweredOn" else "notrunning",
                "Heartbeat": "gray" if vm_r["Powerstate"] == "poweredOff" else choose_random_from_list(["green", "yellow", "red"]),
                "CPUs": vm_r["CPUs"], "Memory": vm_r["Memory"],
                "Primary IP Address": vm_r["Primary IP Address"], "Annotation": vm_r["Annotation"],
                "Datacenter": vm_r["Datacenter"], "Cluster": vm_r["Cluster"], "Host": vm_r["Host"],
                "OS according to the configuration file": vm_r["OS according to the configuration file"],
                "OS according to the VMware Tools": vm_r["OS according to the VMware Tools"],
                "VM ID": vm_r["VM ID"], "SMBIOS UUID": vm_r["SMBIOS UUID"], "VM UUID": vm_r["VM UUID"],
                "VI SDK Server type": "VMware vCenter Server", "VI SDK API Version": "7.0.3",
                "VI SDK Server": vm_r["VI SDK Server"], "VI SDK UUID": vm_r["VI SDK UUID"],
                "Path": f"[{vm_r['Datastore']}] {vm_r['VM']}/{vm_r['VM']}.vmx",
                "Resource pool": vm_r["Resource pool"] , "Creation date": vm_r["Creation date"],
                "HW version": vm_r["HW version"]
            })
            if use_ai:
                ai_generated_data = generate_vinfo_row_ai(vm_r)
                for key, value in ai_generated_data.items():
                    if key in row_data: row_data[key] = value
            for h in headers:
                if row_data[h] == "":
                    if h == "Consolidation Needed": row_data[h] = str(generate_random_boolean())
                    elif h == "PowerOn": row_data[h] = generate_random_datetime(days_range=30) if vm_r["Powerstate"] == "poweredOn" else ""
                    elif h == "NICs": row_data[h] = generate_random_integer(1, 2); vm_r["NICs"] = row_data[h]
                    elif h == "Disks": row_data[h] = generate_random_integer(1, 3); vm_r["Disks"] = row_data[h]
                    elif h == "EnableUUID": row_data[h] = str(generate_random_boolean())
                    elif h == "Network #1": row_data[h] = f"{vm_r['Datacenter']}-VLAN{generate_random_integer(100,105)}" if vm_r["Primary IP Address"] else ""
                    elif h == "Resource pool" and not row_data.get(h) : row_data[h] = f"/{vm_r['Datacenter']}/{vm_r['Cluster']}/Resources"
                    elif h == "Folder" and not row_data.get(h): row_data[h] = f"/{vm_r['Datacenter']}/vm/"
                    elif h in ["Log directory", "Snapshot directory", "Suspend directory"]: row_data[h] = f"[{vm_r['Datastore']}] {vm_r['VM']}/"
                    elif "date" in h.lower(): row_data[h] = generate_random_datetime() if generate_random_boolean() else ""
                    elif "uuid" in h.lower(): row_data[h] = generate_uuid()
                    elif "name" in h.lower(): row_data[h] = generate_random_string(prefix=h.replace(" ", "_")[:5], length=8)
                    elif "%" in h.lower(): row_data[h] = generate_random_integer(0,100)
                    elif "mib" in h.lower() or "kib" in h.lower() or "size" in h.lower() : row_data[h] = generate_random_integer(1,1024*5)
                    elif h in CSV_HEADERS["vInfo"][2:4] + CSV_HEADERS["vInfo"][23:29]: row_data[h] = str(generate_random_boolean())
                    elif "num" in h.lower(): row_data[h] = generate_random_integer(0,2)
                    else: row_data[h] = generate_random_string(4) if generate_random_boolean() else ""
            writer.writerow(row_data)
    print(f"Generated {num_rows} VM records in {filepath}. {len(ENVIRONMENT_DATA['hosts'])} unique hosts. {len(ENVIRONMENT_DATA['clusters'])} unique clusters. AI: {use_ai}")

def generate_vhost_csv(use_ai=False): # ... (vHost function as in previous correct version)
    filepath = os.path.join(CSV_SUBDIR, "RVTools_tabvHost.csv"); headers = CSV_HEADERS["vHost"]
    if not ENVIRONMENT_DATA["hosts"]: print("No host data for vHost CSV."); return
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers); writer.writeheader()
        for host_r in ENVIRONMENT_DATA["hosts"]:
            row_data = {header: "" for header in headers}
            num_cpu = host_r["# CPU"]; cores_per_cpu = host_r["Cores per CPU"]; total_cores = num_cpu * cores_per_cpu
            vms_on_host = [vm for vm in ENVIRONMENT_DATA["vms"] if vm["Host"] == host_r["Host"]]
            total_vms_on_host = len(vms_on_host); total_vcpus_on_host = sum(vm.get("CPUs", 0) for vm in vms_on_host)
            actual_nics_on_host = len([n for n in ENVIRONMENT_DATA.get("host_nics", []) if n.get("Host") == host_r.get("Host")])
            actual_hbas_on_host = len([h for h in ENVIRONMENT_DATA.get("hbas", []) if h.get("Host") == host_r.get("Host")])

            row_data.update({ "Host": host_r["Host"], "Datacenter": host_r["Datacenter"], "Cluster": host_r["Cluster"],
                "Config status": "green", "in Maintenance Mode": "False", "CPU Model": host_r["CPU Model"],
                "# CPU": num_cpu, "Cores per CPU": cores_per_cpu, "# Cores": total_cores, "# Memory": host_r["# Memory"],
                "ESX Version": host_r["ESX Version"], "UUID": host_r["UUID"], "Object ID": host_r["Object ID"],
                "VI SDK Server": host_r["VI SDK Server"], "VI SDK UUID": host_r["VI SDK UUID"],
                "# NICs": actual_nics_on_host if actual_nics_on_host > 0 else generate_random_integer(2,4),
                "# HBAs": actual_hbas_on_host if actual_hbas_on_host > 0 else generate_random_integer(1,2)
            })
            if use_ai:
                ai_generated_data = generate_vhost_row_ai(host_r)
                for key, value in ai_generated_data.items():
                    if key in row_data: row_data[key] = value
            for header in headers:
                if row_data[header] == "":
                    if header == "Speed": row_data[header] = generate_random_integer(2000, 3500)
                    elif header == "HT Available" or header == "HT Active": row_data[header] = str(generate_random_boolean())
                    elif "usage %" in header: row_data[header] = generate_random_integer(10, 75)
                    elif header == "# VMs total" or header == "# VMs": row_data[header] = total_vms_on_host
                    elif header == "VMs per Core": row_data[header] = f"{total_vms_on_host / total_cores:.2f}" if total_cores > 0 else "0.00"
                    elif header == "# vCPUs": row_data[header] = total_vcpus_on_host
                    elif header == "vCPUs per Core": row_data[header] = f"{total_vcpus_on_host / total_cores:.2f}" if total_cores > 0 else "0.00"
                    elif "VMotion support" in header or "Storage VMotion support" in header : row_data[header] = str(generate_random_boolean())
                    elif header == "Boot time": row_data[header] = generate_random_datetime(days_range=100)
                    elif header == "DNS Servers": row_data[header] = "192.168.1.1, 192.168.1.2"
                    elif header == "DHCP": row_data[header] = str(generate_random_boolean())
                    elif header == "Domain": row_data[header] = "corp.local"
                    elif header == "NTP Server(s)" and not row_data.get(header): row_data[header] = "pool.ntp.org"
                    elif header == "NTPD running": row_data[header] = str(generate_random_boolean())
                    elif header == "Time Zone Name" and not row_data.get(header): row_data[header] = "UTC"
                    elif header == "GMT Offset": row_data[header] = "0"
                    elif header == "Vendor" and not row_data.get(header): row_data[header] = "Dell Inc." if "Intel" in host_r["CPU Model"] else "Supermicro"
                    elif header == "Model" and not row_data.get(header): row_data[header] = "PowerEdge R750" if "Intel" in host_r["CPU Model"] else "A+ Server 2024G-TRT"
                    elif "date" in header.lower() and not row_data.get(header): row_data[header] = generate_random_datetime(days_range=365*5) if generate_random_boolean() else ""
                    elif "uuid" in header.lower() and header != "UUID" : row_data[header] = generate_uuid()
                    elif ("name" in header.lower() or "id" in header.lower()) and header != "Object ID": row_data[header] = generate_random_string(prefix=header.replace(" ", "_")[:5], length=8)
                    elif "%" in header.lower(): row_data[header] = generate_random_integer(0,100)
                    elif "mib" in header.lower(): row_data[header] = generate_random_integer(1,1024*5)
                    elif "support" in header.lower() or "enabled" in header.lower() or "mode" in header.lower() or "status" in header.lower(): row_data[header] = str(generate_random_boolean())
                    elif "num" in header.lower(): row_data[header] = generate_random_integer(0,2)
                    else: row_data[header] = generate_random_string(4) if generate_random_boolean() else ""
            writer.writerow(row_data)
    print(f"Generated {len(ENVIRONMENT_DATA['hosts'])} host records in {filepath}. AI: {use_ai}")

def generate_vcluster_csv(use_ai=False): # ... (vCluster function as in previous correct version)
    filepath = os.path.join(CSV_SUBDIR, "RVTools_tabvCluster.csv"); headers = CSV_HEADERS["vCluster"]
    if not ENVIRONMENT_DATA["clusters"]: print("No cluster data. Run generate_vinfo_csv first."); return
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers); writer.writeheader()
        for cluster_r in ENVIRONMENT_DATA["clusters"]:
            row_data = {h: "" for h in headers}
            hosts_in_cluster = [h for h in ENVIRONMENT_DATA["hosts"] if h["Cluster"] == cluster_r["Name"]]
            cluster_r["NumHosts"] = len(hosts_in_cluster); cluster_r["numEffectiveHosts"] = cluster_r["NumHosts"]
            total_cpu_mhz = sum(host.get("Speed", 2000) * host.get("# CPU", 1) for host in hosts_in_cluster)
            cluster_r["TotalCpu"] = total_cpu_mhz ; cluster_r["Effective Cpu"] = total_cpu_mhz
            total_cores = sum(host.get("# CPU", 1) * host.get("Cores per CPU", 1) for host in hosts_in_cluster)
            cluster_r["NumCpuCores"] = total_cores
            cluster_r["NumCpuThreads"] = total_cores * (2 if any(host.get("HT Active") == "True" for host in hosts_in_cluster) else 1)
            total_mem_mb = sum(host.get("# Memory", 0) for host in hosts_in_cluster)
            cluster_r["TotalMemory"] = total_mem_mb ; cluster_r["Effective Memory"] = total_mem_mb * 1024 * 1024
            cluster_r["TotalMemoryGB"] = total_mem_mb // 1024
            row_data.update({ "Name": cluster_r["Name"], "Config status": "green", "OverallStatus": "green",
                "NumHosts": cluster_r["NumHosts"], "numEffectiveHosts": cluster_r["numEffectiveHosts"],
                "TotalCpu": cluster_r["TotalCpu"], "NumCpuCores": cluster_r["NumCpuCores"], "NumCpuThreads": cluster_r["NumCpuThreads"],
                "Effective Cpu": cluster_r["Effective Cpu"], "TotalMemory": cluster_r["TotalMemory"], "Effective Memory": cluster_r["Effective Memory"],
                "Object ID": cluster_r["Object ID"], "VI SDK Server": cluster_r["VI SDK Server"], "VI SDK UUID": cluster_r["VI SDK UUID"],})
            if use_ai:
                ai_generated_data = generate_vcluster_row_ai(cluster_r)
                for key, value in ai_generated_data.items():
                    if key in row_data: row_data[key] = value
            for h in headers:
                if row_data[h] == "":
                    if "enabled" in h.lower() or "monitoring" in h.lower() and not row_data.get(h): row_data[h] = str(generate_random_boolean())
                    elif "Num VMotions" in h: row_data[h] = str(generate_random_integer(0, 5))
                    elif "Failover Level" in h: row_data[h] = str(generate_random_integer(1, 5))
                    else: row_data[h] = generate_random_string(length=5) if generate_random_boolean() else ""
            writer.writerow(row_data)
    print(f"Generated {len(ENVIRONMENT_DATA['clusters'])} cluster records in {filepath}. AI: {use_ai}")

def generate_vdatastore_csv(use_ai=False): # ... (vDatastore function as in previous correct version)
    output_filename = "RVTools_tabvDatastore.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vDatastore', [])
    if not headers: print(f"Error: Headers for vDatastore not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["datastores"].clear()
    datastores_info_aggregated = {}
    for vm_rec in ENVIRONMENT_DATA.get('vms', []):
        ds_name = vm_rec.get('Datastore')
        if not ds_name: continue
        if ds_name not in datastores_info_aggregated:
            datastores_info_aggregated[ds_name] = {
                'Name': ds_name, 'Datacenter': vm_rec.get('Datacenter'), 'vms_on_ds_count': 0,
                'clusters_using_ds': set(), 'hosts_using_ds': set(),
                'VI SDK Server': vm_rec.get('VI SDK Server'), 'VI SDK UUID': vm_rec.get('VI SDK UUID')
            }
        datastores_info_aggregated[ds_name]['vms_on_ds_count'] += 1
        if vm_rec.get('Cluster'): datastores_info_aggregated[ds_name]['clusters_using_ds'].add(vm_rec.get('Cluster'))
        if vm_rec.get('Host'): datastores_info_aggregated[ds_name]['hosts_using_ds'].add(vm_rec.get('Host'))
    if not datastores_info_aggregated:
        print(f"No datastore data from VMs. Generating {output_filename} with headers only.")
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers); writer.writeheader()
        return
    for ds_name, ds_agg_data in datastores_info_aggregated.items():
        current_row_dict = {h: '' for h in headers}
        current_row_dict.update({
            'Name': ds_name, 'Datacenter': ds_agg_data.get('Datacenter'),
            '# VMs total': ds_agg_data['vms_on_ds_count'], '# VMs': ds_agg_data['vms_on_ds_count'],
            '# Hosts': len(ds_agg_data['hosts_using_ds']),
            'Hosts': ", ".join(list(ds_agg_data['hosts_using_ds'])[:3]),
            'Cluster name': ", ".join(list(ds_agg_data['clusters_using_ds'])[:2]),
            'VI SDK Server': ds_agg_data.get('VI SDK Server'),
            'VI SDK UUID': ds_agg_data.get('VI SDK UUID'),
            'Object ID': f"datastore-{generate_random_integer(100,999)}"
        })
        if use_ai:
            ai_data = generate_vdatastore_row_ai(ds_agg_data)
            for key, value in ai_data.items():
                if key in current_row_dict:
                    current_row_dict[key] = value
        if not current_row_dict.get('Type'): current_row_dict['Type'] = choose_random_from_list(['VMFS', 'NFS', 'vSAN', 'VVOL', 'Other'])
        capacity = int(current_row_dict.get('Capacity MiB', generate_random_integer(500000, 4000000)))
        current_row_dict['Capacity MiB'] = capacity
        free_space = int(current_row_dict.get('Free MiB', generate_random_integer(int(capacity * 0.1), int(capacity * 0.9))))
        current_row_dict['Free MiB'] = free_space
        prov_val_str = current_row_dict.get('Provisioned MiB')
        prov_val = int(prov_val_str) if prov_val_str and prov_val_str.isdigit() else generate_random_integer(int(capacity*0.5), int(capacity*1.2))
        current_row_dict['Provisioned MiB'] = prov_val
        in_use_val_str = current_row_dict.get('In Use MiB')
        in_use_val = int(in_use_val_str) if in_use_val_str and in_use_val_str.isdigit() else max(0, prov_val - free_space if prov_val > free_space else generate_random_integer(int(prov_val * 0.7), prov_val))
        current_row_dict['In Use MiB'] = in_use_val
        current_row_dict['Free %'] = current_row_dict.get('Free %') or (round((free_space / capacity) * 100, 2) if capacity > 0 else 0)
        current_row_dict['Accessible'] = str(current_row_dict.get('Accessible', generate_random_boolean())).lower()
        current_row_dict['Config status'] = current_row_dict.get('Config status') or ('green' if current_row_dict['Accessible'] == 'true' else 'red')
        current_row_dict['SIOC enabled'] = str(current_row_dict.get('SIOC enabled', generate_random_boolean())).lower()
        if not current_row_dict.get('SIOC Threshold'): current_row_dict['SIOC Threshold'] = str(generate_random_integer(5,50))
        if not current_row_dict.get('Cluster capacity MiB'): current_row_dict['Cluster capacity MiB'] = str(capacity * current_row_dict['# Hosts'])
        if not current_row_dict.get('Cluster free space MiB'): current_row_dict['Cluster free space MiB'] = str(free_space * current_row_dict['# Hosts'])
        if not current_row_dict.get('Block size'): current_row_dict['Block size'] = str(choose_random_from_list([1,2,4,8]))
        if not current_row_dict.get('Max Blocks'): current_row_dict['Max Blocks'] = str(generate_random_integer(1000000, 90000000))
        if not current_row_dict.get('# Extents'): current_row_dict['# Extents'] = str(generate_random_integer(1,4))
        if not current_row_dict.get('Major Version'): current_row_dict['Major Version'] = str(generate_random_integer(3,7))
        if not current_row_dict.get('Version'): current_row_dict['Version'] = f"{current_row_dict['Major Version']}.{generate_random_integer(0,5)}"
        current_row_dict['VMFS Upgradeable'] = str(current_row_dict.get('VMFS Upgradeable', generate_random_boolean() if current_row_dict['Type'] == 'VMFS' else False)).lower()
        if not current_row_dict.get('URL'): current_row_dict['URL'] = f"ds:///{generate_uuid()}/{ds_name}/"
        if not current_row_dict.get('Address') and current_row_dict['Type'] == 'NFS': current_row_dict['Address'] = f"nfs://filer{generate_random_integer(1,5)}.corp.local:/vol/{ds_name}"
        for header_key in headers:
            if current_row_dict[header_key] == '': current_row_dict[header_key] = generate_random_string(length=3)
        rows_to_write.append(current_row_dict)
        ENVIRONMENT_DATA["datastores"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} datastore records in {output_filename}. AI Used: {use_ai}")

def generate_vrp_csv(use_ai=False): # ... (vRP function as in previous correct version)
    output_filename = "RVTools_tabvRP.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vRP', [])
    if not headers: print(f"Error: Headers for vRP not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["resource_pools"].clear()
    vinfo_csv_path = os.path.join(CSV_SUBDIR, "RVTools_tabvInfo.csv")
    if not ENVIRONMENT_DATA.get('vms') and not os.path.exists(vinfo_csv_path):
        print(f"Warning: Skipping {output_filename} as vInfo data is unavailable.")
        return
    elif not ENVIRONMENT_DATA.get('vms'):
        print(f"Warning: Generating {output_filename} with headers only (vInfo data empty).")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    resource_pools_info = {}
    for vm_rec in ENVIRONMENT_DATA.get('vms', []):
        rp_path = vm_rec.get('Resource pool')
        rp_name = rp_path.split('/')[-1] if rp_path else None
        if not rp_path or not rp_name: continue
        if rp_path not in resource_pools_info:
            resource_pools_info[rp_path] = {
                'rp_name': rp_name, 'rp_path': rp_path, 'num_vms_in_rp': 0,
                'parent_cluster': vm_rec.get('Cluster'), 'total_vm_cpus': 0,
                'total_vm_memory_mib': 0, 'VI SDK Server': vm_rec.get('VI SDK Server'),
                'VI SDK UUID': vm_rec.get('VI SDK UUID'),
                'Object ID': f"resgroup-{generate_random_integer(10,999)}"
            }
        resource_pools_info[rp_path]['num_vms_in_rp'] += 1
        resource_pools_info[rp_path]['total_vm_cpus'] += vm_rec.get('CPUs', 0)
        resource_pools_info[rp_path]['total_vm_memory_mib'] += vm_rec.get('Memory', 0)
    if not resource_pools_info:
        print(f"No Resource Pool data from VMs. Generating {output_filename} with headers only.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    for rp_path, rp_agg_data in resource_pools_info.items():
        current_row_dict = {h: '' for h in headers}
        current_row_dict.update({
            'Resource Pool name': rp_agg_data['rp_name'], 'Resource Pool path': rp_path,
            '# VMs total': rp_agg_data['num_vms_in_rp'], '# VMs': rp_agg_data['num_vms_in_rp'],
            '# vCPUs': rp_agg_data['total_vm_cpus'], 'Mem Configured': rp_agg_data['total_vm_memory_mib'],
            'VI SDK Server': rp_agg_data.get('VI SDK Server'), 'VI SDK UUID': rp_agg_data.get('VI SDK UUID'),
            'Object ID': rp_agg_data['Object ID']
        })
        ai_data = None
        if use_ai:
            ai_data = generate_vrp_row_ai(rp_agg_data)
            for key, val in ai_data.items():
                if key in current_row_dict: current_row_dict[key] = val
        def get_val(key, default_random_func, *args):
            val_from_dict = current_row_dict.get(key)
            return val_from_dict if val_from_dict not in [None, ''] else default_random_func(*args)
        current_row_dict['Status'] = get_val('Status', lambda: "green")
        current_row_dict['CPU limit'] = get_val('CPU limit', lambda: -1)
        current_row_dict['CPU overheadLimit'] = get_val('CPU overheadLimit', lambda: generate_random_integer(0,1000) if current_row_dict['CPU limit'] != -1 else "")
        current_row_dict['CPU reservation'] = get_val('CPU reservation', generate_random_integer, 100, rp_agg_data['total_vm_cpus'] * 500 if rp_agg_data['total_vm_cpus'] > 0 else 5000)
        current_row_dict['CPU level'] = get_val('CPU level', lambda: "normal")
        current_row_dict['CPU shares'] = get_val('CPU shares', lambda: "normal")
        current_row_dict['CPU expandableReservation'] = get_val('CPU expandableReservation', lambda: str(generate_random_boolean()).lower())
        cpu_max_usage_val = current_row_dict.get('CPU maxUsage', "")
        current_row_dict['CPU maxUsage'] = cpu_max_usage_val if cpu_max_usage_val not in [None, ''] else (current_row_dict['CPU limit'] if current_row_dict['CPU limit'] != -1 else generate_random_integer(2000,20000))
        current_row_dict['CPU overallUsage'] = get_val('CPU overallUsage', generate_random_integer, 100, int(current_row_dict['CPU maxUsage'] * 0.8) if str(current_row_dict['CPU maxUsage']).isdigit() and int(current_row_dict['CPU maxUsage']) != -1 else 5000)
        current_row_dict['CPU reservationUsed'] = get_val('CPU reservationUsed', generate_random_integer, 0, int(current_row_dict['CPU reservation']) if str(current_row_dict['CPU reservation']).isdigit() else 0)
        current_row_dict['CPU reservationUsedForVm'] = current_row_dict['CPU reservationUsed']
        current_row_dict['CPU unreservedForPool'] = get_val('CPU unreservedForPool', generate_random_integer, 0, 5000)
        current_row_dict['CPU unreservedForVm'] = current_row_dict['CPU unreservedForPool']
        current_row_dict['Mem limit'] = get_val('Mem limit', lambda: -1)
        current_row_dict['Mem overheadLimit'] = get_val('Mem overheadLimit', lambda: generate_random_integer(0, rp_agg_data['total_vm_memory_mib'] // 10 if rp_agg_data['total_vm_memory_mib'] >0 else 1024) if current_row_dict['Mem limit'] != -1 else "")
        current_row_dict['Mem reservation'] = get_val('Mem reservation', generate_random_integer, 1024, rp_agg_data['total_vm_memory_mib'] if rp_agg_data['total_vm_memory_mib'] > 0 else 16384)
        current_row_dict['Mem level'] = get_val('Mem level', lambda: "normal")
        current_row_dict['Mem shares'] = get_val('Mem shares', lambda: "normal")
        current_row_dict['Mem expandableReservation'] = get_val('Mem expandableReservation', lambda: str(generate_random_boolean()).lower())
        mem_max_usage_val = current_row_dict.get('Mem maxUsage', "")
        current_row_dict['Mem maxUsage'] = mem_max_usage_val if mem_max_usage_val not in [None, ''] else (current_row_dict['Mem limit'] if current_row_dict['Mem limit'] != -1 else rp_agg_data['total_vm_memory_mib'] * 2 if rp_agg_data['total_vm_memory_mib'] > 0 else 32768)
        current_row_dict['Mem overallUsage'] = get_val('Mem overallUsage', generate_random_integer, 512, int(current_row_dict['Mem maxUsage'] * 0.8) if str(current_row_dict['Mem maxUsage']).isdigit() and int(current_row_dict['Mem maxUsage']) != -1 else rp_agg_data['total_vm_memory_mib'])
        current_row_dict['Mem reservationUsed'] = get_val('Mem reservationUsed', generate_random_integer, 0, int(current_row_dict['Mem reservation']) if str(current_row_dict['Mem reservation']).isdigit() else 0)
        current_row_dict['Mem reservationUsedForVm'] = current_row_dict['Mem reservationUsed']
        current_row_dict['Mem unreservedForPool'] = get_val('Mem unreservedForPool', generate_random_integer, 0, rp_agg_data['total_vm_memory_mib'] // 2 if rp_agg_data['total_vm_memory_mib'] > 0 else 8192)
        current_row_dict['Mem unreservedForVm'] = current_row_dict['Mem unreservedForPool']
        qs_fields = [h for h in headers if h.startswith("QS ")]
        for qs_field in qs_fields:
            current_row_dict[qs_field] = get_val(qs_field, generate_random_integer, 0, 5000)
        rows_to_write.append(current_row_dict)
        ENVIRONMENT_DATA["resource_pools"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} Resource Pool records in {output_filename}. AI Used: {use_ai}")

def generate_vsource_csv(use_ai=False): # ... (vSource function as in previous correct version)
    output_filename = "RVTools_tabvSource.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vSource', [])
    if not headers: print(f"Error: Headers for vSource not found."); return
    rows_to_write = []
    vcenter_ip = ENVIRONMENT_DATA.get('vcenter_ip')
    if not vcenter_ip:
        vcenter_ip = f"vcenter-default.corp.local"
        ENVIRONMENT_DATA['vcenter_ip'] = vcenter_ip
        print(f"Warning: vcenter_ip not found in ENVIRONMENT_DATA, using default: {vcenter_ip}")
    vcenter_uuid = ENVIRONMENT_DATA.get('vcenter_uuid')
    if not vcenter_uuid:
        vcenter_uuid = generate_uuid()
        ENVIRONMENT_DATA['vcenter_uuid'] = vcenter_uuid
        print(f"Warning: vcenter_uuid not found in ENVIRONMENT_DATA, generated new one.")
    target_base_version = choose_random_from_list(["7.0 U3", "8.0 U1", "8.0 U2"])
    current_row_dict = {h: '' for h in headers}
    current_row_dict['VI SDK Server'] = vcenter_ip
    current_row_dict['VI SDK UUID'] = vcenter_uuid
    ai_generated_data = None
    if use_ai:
        vsource_ai_context = {'vcenter_ip': vcenter_ip, 'vcenter_uuid': vcenter_uuid, 'target_version': target_base_version}
        ai_generated_data = generate_vsource_row_ai(vsource_ai_context)
    current_row_dict['Name'] = ai_generated_data.get('Name', vcenter_ip) if use_ai and ai_generated_data else vcenter_ip
    current_row_dict['OS type'] = ai_generated_data.get('OS type', 'VMware Photon OS (64-bit)') if use_ai and ai_generated_data else 'VMware Photon OS (64-bit)'
    current_row_dict['API type'] = ai_generated_data.get('API type', 'VirtualCenter') if use_ai and ai_generated_data else 'VirtualCenter'
    if use_ai and ai_generated_data:
        current_row_dict['API version'] = ai_generated_data.get('API version', '8.0.2')
        current_row_dict['Version'] = ai_generated_data.get('Version', '8.0')
        current_row_dict['Patch level'] = ai_generated_data.get('Patch level', 'U2')
        current_row_dict['Build'] = ai_generated_data.get('Build', str(generate_random_integer(20000000, 23000000)))
        current_row_dict['Fullname'] = ai_generated_data.get('Fullname', f"VMware vCenter Server {current_row_dict['Version']} Update {current_row_dict['Patch level']} build-{current_row_dict['Build']}")
        current_row_dict['Product name'] = ai_generated_data.get('Product name', 'VMware vCenter Server')
        current_row_dict['Product version'] = ai_generated_data.get('Product version', f"{current_row_dict['Version']} Update {current_row_dict['Patch level']}")
        current_row_dict['Product line'] = ai_generated_data.get('Product line', 'vpx')
        current_row_dict['Vendor'] = ai_generated_data.get('Vendor', 'VMware, Inc.')
    else:
        ver_parts = target_base_version.split(' ')
        base_ver = ver_parts[0]
        patch_str = "".join(ver_parts[1:]) if len(ver_parts) > 1 else ""
        patch_level_for_api = patch_str[1] if patch_str and patch_str.startswith('U') and len(patch_str) > 1 else \
                              (ver_parts[2] if len(ver_parts) > 2 and ver_parts[1].lower() == "update" else "0")
        current_row_dict['API version'] = f"{base_ver}.{patch_level_for_api}"
        current_row_dict['Version'] = base_ver
        current_row_dict['Patch level'] = patch_str
        current_row_dict['Build'] = str(generate_random_integer(20000000, 23000000))
        current_row_dict['Fullname'] = f"VMware vCenter Server {target_base_version} build-{current_row_dict['Build']}"
        current_row_dict['Product name'] = 'VMware vCenter Server'
        current_row_dict['Product version'] = target_base_version
        current_row_dict['Product line'] = 'vpx'
        current_row_dict['Vendor'] = 'VMware, Inc.'
    rows_to_write.append(current_row_dict)
    ENVIRONMENT_DATA['vcenter_details'] = current_row_dict
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated 1 vSource record in {output_filename}. AI Used: {use_ai}")

def generate_vhba_csv(use_ai=False): # ... (vHBA function as in previous correct version)
    output_filename = "RVTools_tabvHBA.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vHBA', [])
    if not headers: print(f"Error: Headers for vHBA not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["hbas"].clear()
    if not ENVIRONMENT_DATA.get('hosts'):
        print(f"Warning: Skipping {output_filename} generation as ENVIRONMENT_DATA['hosts'] is empty.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    for host_rec in ENVIRONMENT_DATA.get('hosts', []):
        num_hbas_default = generate_random_integer(1, 2)
        ai_hba_list = None
        if use_ai:
            vhba_ai_context = {
                'host_name': host_rec.get('Host'), 'esxi_version': host_rec.get('ESX Version'),
                'cluster_name': host_rec.get('Cluster'), 'datacenter_name': host_rec.get('Datacenter'),
                'num_hbas_requested': num_hbas_default
            }
            ai_hba_list = generate_vhba_row_ai(vhba_ai_context)
        if use_ai and ai_hba_list and isinstance(ai_hba_list, list):
            for i, ai_hba_data in enumerate(ai_hba_list):
                current_row_dict = {h: '' for h in headers}
                current_row_dict.update({
                    'Host': host_rec.get('Host'), 'Datacenter': host_rec.get('Datacenter'),
                    'Cluster': host_rec.get('Cluster'), 'VI SDK Server': host_rec.get('VI SDK Server'),
                    'VI SDK UUID': host_rec.get('VI SDK UUID')
                })
                for key, val in ai_hba_data.items():
                    if key in current_row_dict: current_row_dict[key] = val
                if not current_row_dict.get('Device'): current_row_dict['Device'] = f"vmhba{i}"
                if not current_row_dict.get('Bus') and current_row_dict.get('Pci'):
                    try: current_row_dict['Bus'] = str(int(current_row_dict['Pci'].split(':')[1], 16))
                    except: current_row_dict['Bus'] = str(generate_random_integer(0,3))
                elif not current_row_dict.get('Bus'): current_row_dict['Bus'] = str(generate_random_integer(0,3))
                if not current_row_dict.get('Pci'): current_row_dict['Pci'] = f"0000:{int(current_row_dict['Bus']):02x}:00.{i}"
                if not current_row_dict.get('Type'): current_row_dict['Type'] = "Unknown AI HBA"
                if not current_row_dict.get('Status'): current_row_dict['Status'] = "Online"
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["hbas"].append(current_row_dict)
        else:
            for i in range(num_hbas_default):
                current_row_dict = {h: '' for h in headers}
                current_row_dict.update({
                    'Host': host_rec.get('Host'), 'Datacenter': host_rec.get('Datacenter'),
                    'Cluster': host_rec.get('Cluster'), 'VI SDK Server': host_rec.get('VI SDK Server'),
                    'VI SDK UUID': host_rec.get('VI SDK UUID'), 'Device': f"vmhba{i}"
                })
                hba_type = choose_random_from_list(['Fibre Channel', 'iSCSI Software Adapter', 'SAS Controller', 'RAID Controller'])
                current_row_dict['Type'] = hba_type
                current_row_dict['Status'] = choose_random_from_list(['Online', 'Offline', 'Unknown'])
                current_row_dict['Bus'] = str(generate_random_integer(0, 7))
                current_row_dict['Pci'] = f"0000:{int(current_row_dict['Bus']):02d}:00.{generate_random_integer(0,7)}"
                if hba_type == 'Fibre Channel':
                    current_row_dict['Driver'] = choose_random_from_list(['lpfc', 'qlnativefc', 'brcmfcoe'])
                    current_row_dict['Model'] = choose_random_from_list(['Emulex LightPulse LPe31002', 'QLogic QLE2692', 'Broadcom BCM57414'])
                    current_row_dict['WWN'] = ":".join([generate_random_string(2, prefix='').lower() for _ in range(8)])
                elif hba_type == 'iSCSI Software Adapter':
                    current_row_dict['Driver'] = 'iscsi_vmk'
                    current_row_dict['Model'] = 'iSCSI Software Adapter'
                    current_row_dict['WWN'] = f"iqn.1998-01.com.vmware:{host_rec.get('Host','unknownhost')}-{generate_random_string(8).lower()}"
                elif hba_type == 'SAS Controller':
                    current_row_dict['Driver'] = choose_random_from_list(['lsi_mr3', 'lsi_msgpt3'])
                    current_row_dict['Model'] = choose_random_from_list(['PERC H730P Adapter', 'MegaRAID SAS 9361-8i'])
                else:
                    current_row_dict['Driver'] = 'unknown_driver'
                    current_row_dict['Model'] = generate_random_string(10, prefix='GenericAdapter-')
                for header_key in headers:
                    if current_row_dict[header_key] == '': current_row_dict[header_key] = generate_random_string(length=3) if header_key != "WWN" else ""
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["hbas"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} HBA records in {output_filename}. AI Used: {use_ai}")

def generate_vnic_csv(use_ai=False): # ... (vNIC function as in previous correct version)
    output_filename = "RVTools_tabvNIC.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vNIC', [])
    if not headers: print(f"Error: Headers for vNIC not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["host_nics"].clear()
    if not ENVIRONMENT_DATA.get('hosts'):
        print(f"Warning: Skipping {output_filename} generation as ENVIRONMENT_DATA['hosts'] is empty.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    for host_rec in ENVIRONMENT_DATA.get('hosts', []):
        num_nics_to_gen_random = generate_random_integer(2, 4)
        ai_generated_nic_list = None
        if use_ai:
            vnic_ai_context = {
                'host_name': host_rec.get('Host'), 'esxi_version': host_rec.get('ESX Version'),
                'num_nics_requested': num_nics_to_gen_random
            }
            ai_generated_nic_list = generate_vnic_row_ai(vnic_ai_context)
        if use_ai and ai_generated_nic_list and isinstance(ai_generated_nic_list, list):
            for i, nic_data_ai in enumerate(ai_generated_nic_list):
                current_row_dict = {h: '' for h in headers}
                current_row_dict.update({
                    'Host': host_rec.get('Host'), 'Datacenter': host_rec.get('Datacenter'),
                    'Cluster': host_rec.get('Cluster'), 'VI SDK Server': host_rec.get('VI SDK Server'),
                    'VI SDK UUID': host_rec.get('VI SDK UUID')
                })
                for key, val in nic_data_ai.items():
                    if key in current_row_dict: current_row_dict[key] = val
                if not current_row_dict.get('Network Device'): current_row_dict['Network Device'] = f"vmnic{i}_ai_fallback"
                if not current_row_dict.get('MAC'): current_row_dict['MAC'] = generate_random_mac_address()
                if not current_row_dict.get('Speed'): current_row_dict['Speed'] = "10000 Mbps"
                if not current_row_dict.get('Duplex'): current_row_dict['Duplex'] = "Full"
                if 'WakeOn' in current_row_dict and isinstance(current_row_dict['WakeOn'], bool):
                    current_row_dict['WakeOn'] = str(current_row_dict['WakeOn'])
                for header_key in headers:
                    if current_row_dict[header_key] == '': current_row_dict[header_key] = generate_random_string(length=3)
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["host_nics"].append(current_row_dict)
        else:
            for i in range(num_nics_to_gen_random):
                current_row_dict = {h: '' for h in headers}
                current_row_dict.update({
                    'Host': host_rec.get('Host'), 'Datacenter': host_rec.get('Datacenter'),
                    'Cluster': host_rec.get('Cluster'), 'VI SDK Server': host_rec.get('VI SDK Server'),
                    'VI SDK UUID': host_rec.get('VI SDK UUID'), 'Network Device': f"vmnic{i}"
                })
                current_row_dict['Driver'] = choose_random_from_list(['ixgben', 'nmlx5_core', 'bnxtnet', 'i40en'])
                nic_speed_val = choose_random_from_list([1000, 10000, 25000, 40000])
                current_row_dict['Speed'] = f"{nic_speed_val} Mbps" if nic_speed_val else "Unknown"
                current_row_dict['Duplex'] = "Full" if nic_speed_val >=1000 else choose_random_from_list(["Full", "Half"])
                current_row_dict['MAC'] = generate_random_mac_address()
                current_row_dict['Switch'] = f"TOR-Switch-{chr(65+i)}{generate_random_integer(1,2)}"
                current_row_dict['Uplink port'] = f"Eth1/{generate_random_integer(1,48)}"
                current_row_dict['PCI'] = f"0000:0{generate_random_integer(3,18)}:00.{i}"
                current_row_dict['WakeOn'] = str(generate_random_boolean())
                for header_key in headers:
                    if current_row_dict[header_key] == '': current_row_dict[header_key] = generate_random_string(length=3)
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["host_nics"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} Host NIC records in {output_filename}. AI Used: {use_ai}")

def generate_vscvmk_csv(use_ai=False): # ... (vSC_VMK function as in previous correct version)
    output_filename = "RVTools_tabvSC_VMK.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vSC_VMK', [])
    if not headers: print(f"Error: Headers for vSC_VMK not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["host_vmkernel_nics"].clear()
    if not ENVIRONMENT_DATA.get('hosts'):
        print(f"Warning: Skipping {output_filename} generation as ENVIRONMENT_DATA['hosts'] is empty.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    for host_rec in ENVIRONMENT_DATA.get('hosts', []):
        num_vmk_to_gen_random = generate_random_integer(1, 3)
        phys_nics_for_host = [nic.get('Network Device') for nic in ENVIRONMENT_DATA.get('host_nics', []) if nic.get('Host') == host_rec.get('Host')]
        known_pgs_for_host = list(set([f"PG_{svc}" for nic in ENVIRONMENT_DATA.get('host_nics', []) if nic.get('Host') == host_rec.get('Host') for svc in ["Mgmt", "vMotion", "Storage"]]))
        if not known_pgs_for_host : known_pgs_for_host = ["Management Network", "vMotion Network"]
        ai_generated_vmk_list = None
        if use_ai:
            vmk_ai_context = {
                'host_name': host_rec.get('Host'), 'esxi_version': host_rec.get('ESX Version'),
                'num_vmk_requested': num_vmk_to_gen_random,
                'physical_nic_names': phys_nics_for_host, 'port_group_names': known_pgs_for_host
            }
            ai_generated_vmk_list = generate_vscvmk_row_ai(vmk_ai_context)
        if use_ai and ai_generated_vmk_list and isinstance(ai_generated_vmk_list, list):
            for i, vmk_data_ai in enumerate(ai_generated_vmk_list):
                current_row_dict = {h: '' for h in headers}
                current_row_dict.update({
                    'Host': host_rec.get('Host'), 'Datacenter': host_rec.get('Datacenter'),
                    'Cluster': host_rec.get('Cluster'), 'VI SDK Server': host_rec.get('VI SDK Server'),
                    'VI SDK UUID': host_rec.get('VI SDK UUID')
                })
                for key, val in vmk_data_ai.items():
                    if key in current_row_dict: current_row_dict[key] = val
                if not current_row_dict.get('Device'): current_row_dict['Device'] = f"vmk{i}_ai_fallback"
                if not current_row_dict.get('Mac Address'): current_row_dict['Mac Address'] = generate_random_mac_address()
                if 'DHCP' in current_row_dict and isinstance(current_row_dict['DHCP'], bool):
                    current_row_dict['DHCP'] = str(current_row_dict['DHCP']).lower()
                elif not current_row_dict.get('DHCP'): current_row_dict['DHCP'] = str(generate_random_boolean()).lower()
                for header_key in headers:
                    if current_row_dict[header_key] == '': current_row_dict[header_key] = generate_random_string(length=3)
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["host_vmkernel_nics"].append(current_row_dict)
        else:
            for i in range(num_vmk_to_gen_random):
                current_row_dict = {h: '' for h in headers}
                current_row_dict.update({
                    'Host': host_rec.get('Host'), 'Datacenter': host_rec.get('Datacenter'),
                    'Cluster': host_rec.get('Cluster'), 'VI SDK Server': host_rec.get('VI SDK Server'),
                    'VI SDK UUID': host_rec.get('VI SDK UUID'), 'Device': f"vmk{i}"
                })
                services_list = []
                if i == 0: services_list.append("Management")
                if generate_random_boolean(): services_list.append("vMotion")
                if generate_random_boolean(): services_list.append("Provisioning")
                current_row_dict['Services'] = ", ".join(services_list) if services_list else "VMkernel"
                current_row_dict['Port Group'] = f"{services_list[0].replace(' ','_') if services_list else 'VMkernel'}_PG"
                current_row_dict['Mac Address'] = generate_random_mac_address()
                current_row_dict['DHCP'] = str(generate_random_boolean()).lower()
                base_ip_parts_str = host_rec.get('Host').split('.')[0].replace('esxi-host','').replace('-','')
                base_ip_segment_3 = generate_random_integer(10,250)
                try: base_ip_segment_3 = int(base_ip_parts_str) if base_ip_parts_str else base_ip_segment_3
                except ValueError: pass
                current_row_dict['IP Address'] = f"192.168.{base_ip_segment_3}.{generate_random_integer(10,250)}"
                current_row_dict['Subnet mask'] = "255.255.255.0"
                current_row_dict['Gateway'] = f"{'.'.join(current_row_dict['IP Address'].split('.')[:3])}.1"
                current_row_dict['MTU'] = str(choose_random_from_list([1500, 9000]))
                current_row_dict['IP 6 Address'] = ""
                current_row_dict['IP 6 Gateway'] = ""
                for header_key in headers:
                    if current_row_dict[header_key] == '': current_row_dict[header_key] = generate_random_string(length=3)
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["host_vmkernel_nics"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} Host VMkernel NIC records in {output_filename}. AI Used: {use_ai}")

def generate_vswitch_csv(use_ai=False): # ... (vSwitch function as in previous correct version)
    output_filename = "RVTools_tabvSwitch.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vSwitch', [])
    if not headers: print(f"Error: Headers for vSwitch not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["standard_vswitches"].clear()
    if not ENVIRONMENT_DATA.get('hosts'):
        print(f"Warning: Skipping {output_filename} generation as ENVIRONMENT_DATA['hosts'] is empty.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    for host_rec in ENVIRONMENT_DATA.get('hosts', []):
        num_vswitches_to_gen_random = generate_random_integer(1, 2)
        host_phys_nics = [nic.get('Network Device') for nic in ENVIRONMENT_DATA.get('host_nics', []) if nic.get('Host') == host_rec.get('Host')]
        ai_generated_vswitch_list = None
        if use_ai:
            vswitch_ai_context = {
                'host_name': host_rec.get('Host'), 'physical_nic_names': host_phys_nics,
                'num_vswitches_requested': num_vswitches_to_gen_random
            }
            ai_generated_vswitch_list = generate_vswitch_row_ai(vswitch_ai_context)
        if use_ai and ai_generated_vswitch_list and isinstance(ai_generated_vswitch_list, list):
            for i, vswitch_data_ai in enumerate(ai_generated_vswitch_list):
                current_row_dict = {h: '' for h in headers}
                current_row_dict.update({
                    'Host': host_rec.get('Host'), 'Datacenter': host_rec.get('Datacenter'),
                    'Cluster': host_rec.get('Cluster'), 'VI SDK Server': host_rec.get('VI SDK Server'),
                    'VI SDK UUID': host_rec.get('VI SDK UUID')
                })
                for key, val in vswitch_data_ai.items():
                    if key in current_row_dict: current_row_dict[key] = val
                if not current_row_dict.get('Switch'): current_row_dict['Switch'] = f"vSwitch{i}_AI_fallback"
                if not current_row_dict.get('# Ports'): current_row_dict['# Ports'] = 128
                if not current_row_dict.get('Free Ports'): current_row_dict['Free Ports'] = generate_random_integer(0, int(current_row_dict['# Ports']))
                if not current_row_dict.get('MTU'): current_row_dict['MTU'] = 1500
                for pol_key in ['Promiscuous Mode', 'Mac Changes', 'Forged Transmits']:
                    if not current_row_dict.get(pol_key): current_row_dict[pol_key] = "Reject"
                for header_key in headers:
                    if current_row_dict[header_key] == '': current_row_dict[header_key] = generate_random_string(length=3)
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["standard_vswitches"].append(current_row_dict)
        else:
            for i in range(num_vswitches_to_gen_random):
                current_row_dict = {h: '' for h in headers}
                current_row_dict.update({
                    'Host': host_rec.get('Host'), 'Datacenter': host_rec.get('Datacenter'),
                    'Cluster': host_rec.get('Cluster'), 'VI SDK Server': host_rec.get('VI SDK Server'),
                    'VI SDK UUID': host_rec.get('VI SDK UUID'), 'Switch': f"vSwitch{i}"
                })
                total_ports = choose_random_from_list([64, 128, 256, 512, 1024, 4096])
                current_row_dict['# Ports'] = total_ports
                current_row_dict['Free Ports'] = generate_random_integer(0, total_ports)
                sec_policy_val = choose_random_from_list(["Reject", "Accept"])
                current_row_dict['Promiscuous Mode'] = sec_policy_val
                current_row_dict['Mac Changes'] = sec_policy_val
                current_row_dict['Forged Transmits'] = sec_policy_val
                num_uplinks = generate_random_integer(1, len(host_phys_nics) if host_phys_nics else 1)
                selected_uplinks = random.sample(host_phys_nics, min(num_uplinks, len(host_phys_nics))) if host_phys_nics else [f"vmnic{j}" for j in range(num_uplinks)]
                current_row_dict['Uplinks'] = ",".join(selected_uplinks)
                current_row_dict['MTU'] = str(choose_random_from_list([1500, 9000]))
                current_row_dict['Traffic Shaping'] = str(False)
                current_row_dict['Width'] = ""
                current_row_dict['Peak'] = ""
                current_row_dict['Burst'] = ""
                current_row_dict['Policy'] = "loadbalance_srcid"
                current_row_dict['Reverse Policy'] = str(True)
                current_row_dict['Notify Switch'] = str(True)
                current_row_dict['Rolling Order'] = str(False)
                current_row_dict['Offload'] = str(True)
                current_row_dict['TSO'] = str(True)
                current_row_dict['Zero Copy Xmit'] = str(True)
                for header_key in headers:
                    if current_row_dict[header_key] == '': current_row_dict[header_key] = generate_random_string(length=3)
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["standard_vswitches"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} Standard vSwitch records in {output_filename}. AI Used: {use_ai}")

def generate_dvswitch_csv(use_ai=False): # ... (dvSwitch function as in previous correct version)
    output_filename = "RVTools_tabdvSwitch.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('dvSwitch', [])
    if not headers: print(f"Error: Headers for dvSwitch not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA['distributed_vswitches'] = []
    if not ENVIRONMENT_DATA.get('hosts'):
        print(f"Warning: Skipping {output_filename} generation as ENVIRONMENT_DATA['hosts'] is empty for DC context.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    datacenters_map = {}
    for host_rec in ENVIRONMENT_DATA.get('hosts', []):
        dc_name = host_rec.get('Datacenter')
        if not dc_name: continue
        if dc_name not in datacenters_map: datacenters_map[dc_name] = {'host_names': []}
        datacenters_map[dc_name]['host_names'].append(host_rec.get('Host'))
    if not datacenters_map:
        print(f"No Datacenter context available from hosts. Generating {output_filename} with headers only.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    for dc_name, dc_data in datacenters_map.items():
        num_dvswitches_to_gen_random = generate_random_integer(1, 2)
        ai_generated_dvswitch_list = None
        if use_ai:
            dvswitch_ai_context = {
                'datacenter_name': dc_name, 'host_names_in_dc': dc_data['host_names'],
                'num_dvswitches_requested': num_dvswitches_to_gen_random
            }
            ai_generated_dvswitch_list = generate_dvswitch_row_ai(dvswitch_ai_context)
        if use_ai and ai_generated_dvswitch_list and isinstance(ai_generated_dvswitch_list, list):
            for i, dvs_data_ai in enumerate(ai_generated_dvswitch_list):
                current_row_dict = {h: '' for h in headers}
                current_row_dict.update({
                    'Datacenter': dc_name,
                    'VI SDK Server': ENVIRONMENT_DATA.get('vcenter_ip'),
                    'VI SDK UUID': ENVIRONMENT_DATA.get('vcenter_uuid')
                })
                for key, val in dvs_data_ai.items():
                    if key in current_row_dict: current_row_dict[key] = val
                if not current_row_dict.get('Switch'): current_row_dict['Switch'] = f"DVS_{dc_name}_AI_fallback_{i}"
                if not current_row_dict.get('Name'): current_row_dict['Name'] = current_row_dict['Switch']
                if not current_row_dict.get('Object ID'): current_row_dict['Object ID'] = f"dvs-ai-{generate_random_integer(200,299)}"
                for num_field in ['Max Ports', '# Ports', '# VMs', 'Max MTU']:
                    if num_field in current_row_dict and not isinstance(current_row_dict[num_field], str):
                        current_row_dict[num_field] = str(current_row_dict[num_field])
                for header_key in headers:
                    if current_row_dict[header_key] == '': current_row_dict[header_key] = generate_random_string(length=3)
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA['distributed_vswitches'].append(current_row_dict)
        else:
            for i in range(num_dvswitches_to_gen_random):
                current_row_dict = {h: '' for h in headers}
                dvs_name = f"DVS_{dc_name.replace('DC','').replace('-','')}_{i+1}"
                current_row_dict.update({
                    'Switch': dvs_name, 'Name': dvs_name, 'Datacenter': dc_name,
                    'Vendor': "VMware", 'Version': choose_random_from_list(["6.5.0", "6.6.0", "7.0.0", "8.0.0"]),
                    'Max Ports': str(generate_random_integer(256, 4096)),
                    'CDP Type': choose_random_from_list(["Cisco Discovery Protocol", "Link Layer Discovery Protocol", "Disabled"]),
                    'Max MTU': str(choose_random_from_list([1500, 9000])),
                    'Object ID': f"dvs-{generate_random_integer(10,999)}",
                    'VI SDK Server': ENVIRONMENT_DATA.get('vcenter_ip'),
                    'VI SDK UUID': ENVIRONMENT_DATA.get('vcenter_uuid')
                })
                current_row_dict['# Ports'] = str(generate_random_integer(10, int(current_row_dict['Max Ports'])))
                current_row_dict['# VMs'] = str(generate_random_integer(0, int(current_row_dict['# Ports'])))
                host_members_list = random.sample(dc_data['host_names'], k=min(len(dc_data['host_names']), generate_random_integer(1, len(dc_data['host_names'])))) if dc_data['host_names'] else []
                current_row_dict['Host members'] = ",".join(host_members_list)
                current_row_dict['Description'] = f"Distributed Switch for {dc_name}"
                current_row_dict['Created'] = generate_random_datetime(days_range=365*3)
                current_row_dict['In Traffic Shaping'] = str(False)
                current_row_dict['Out Traffic Shaping'] = str(False)
                current_row_dict['CDP Operation'] = "Listen" if current_row_dict['CDP Type'] != "Disabled" else ""
                current_row_dict['LACP Name'] = ""
                current_row_dict['LACP Mode'] = ""
                current_row_dict['LACP Load Balance Alg.'] = ""
                current_row_dict['Contact'] = "Network Admin <netadmin@corp.local>"
                current_row_dict['Admin Name'] = "netadmin"
                for header_key in headers:
                    if current_row_dict[header_key] == '': current_row_dict[header_key] = generate_random_string(length=3)
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA['distributed_vswitches'].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} Distributed vSwitch records in {output_filename}. AI Used: {use_ai}")

def generate_dvport_csv(use_ai=False): # ... (dvPortGroup function as in previous correct version)
    output_filename = "RVTools_tabdvPort.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('dvPortGroup', [])
    if not headers: print(f"Error: Headers for dvPortGroup not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["distributed_port_groups"].clear()
    if not ENVIRONMENT_DATA.get('distributed_vswitches'):
        print(f"Warning: Skipping {output_filename} generation as no DVS data is available.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    for dvs_rec in ENVIRONMENT_DATA.get('distributed_vswitches', []):
        num_dpg_to_gen_random = generate_random_integer(2, 5)
        ai_generated_dvport_list = None
        if use_ai:
            dvport_ai_context = {
                'dvs_name': dvs_rec.get('Name'),
                'datacenter_name': dvs_rec.get('Datacenter'),
                'max_ports_on_dvs': dvs_rec.get('Max Ports'),
                'num_items_requested': num_dpg_to_gen_random
            }
            ai_generated_dvport_list = generate_dvport_row_ai(dvport_ai_context)
        if use_ai and ai_generated_dvport_list and isinstance(ai_generated_dvport_list, list):
            for i, dvport_data_ai in enumerate(ai_generated_dvport_list):
                current_row_dict = {h: '' for h in headers}
                current_row_dict.update({
                    'Switch': dvs_rec.get('Name'),
                    'VI SDK Server': dvs_rec.get('VI SDK Server', ENVIRONMENT_DATA.get('vcenter_ip')),
                    'VI SDK UUID': dvs_rec.get('VI SDK UUID', ENVIRONMENT_DATA.get('vcenter_uuid'))
                })
                for key, val in dvport_data_ai.items():
                    if key in current_row_dict: current_row_dict[key] = val
                if not current_row_dict.get('Name'): current_row_dict['Name'] = f"DPG_AI_Fallback_{generate_random_string(4)}"
                if not current_row_dict.get('Object ID'): current_row_dict['Object ID'] = f"dvportgroup-ai-{generate_random_integer(200,299)}"
                for bool_key in ['Allow Promiscuous', 'Mac Changes', 'Forged Transmits']:
                    if bool_key in current_row_dict and isinstance(current_row_dict[bool_key], bool):
                         current_row_dict[bool_key] = str(current_row_dict[bool_key]).lower()
                    elif bool_key in current_row_dict and current_row_dict[bool_key] in ["true", "false"]:
                         current_row_dict[bool_key] = current_row_dict[bool_key]
                    elif bool_key in current_row_dict :
                         pass
                    else:
                         current_row_dict[bool_key] = str(generate_random_boolean()).lower()
                for header_key in headers:
                    if current_row_dict[header_key] == '': current_row_dict[header_key] = generate_random_string(length=3)
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["distributed_port_groups"].append(current_row_dict)
        else:
            for i in range(num_dpg_to_gen_random):
                current_row_dict = {h: '' for h in headers}
                vlan_id = generate_random_integer(100, 500)
                dpg_name = f"DPG_VLAN{vlan_id}_{dvs_rec.get('Name','DVS')}_{i}"
                current_row_dict.update({
                    'Name': dpg_name,
                    'Switch': dvs_rec.get('Name'),
                    'Type': choose_random_from_list(['earlyBinding', 'lateBinding', 'ephemeral']),
                    '# Ports': str(choose_random_from_list([0, 8, 16, 24, 64, 128, 256])),
                    'VLAN': f"VLAN {vlan_id}" if generate_random_boolean() else choose_random_from_list(["Trunk", ""]),
                    'Object ID': f"dvportgroup-{generate_random_integer(1000,1999)}",
                    'VI SDK Server': dvs_rec.get('VI SDK Server', ENVIRONMENT_DATA.get('vcenter_ip')),
                    'VI SDK UUID': dvs_rec.get('VI SDK UUID', ENVIRONMENT_DATA.get('vcenter_uuid')),
                    'Port Binding': choose_random_from_list(['staticBinding','dynamicBinding','ephemeral']),
                    'VLAN type': 'VLAN tagging' if "VLAN" in current_row_dict['VLAN'] else 'None',
                    'Active Ports': str(generate_random_integer(0, int(current_row_dict['# Ports'] if current_row_dict['# Ports'] != '0' else '128'))),
                })
                sec_policy_val = choose_random_from_list([True, False, "Inherit from vSwitch"])
                current_row_dict['Allow Promiscuous'] = str(sec_policy_val).lower() if isinstance(sec_policy_val, bool) else sec_policy_val
                current_row_dict['Mac Changes'] = str(sec_policy_val).lower() if isinstance(sec_policy_val, bool) else sec_policy_val
                current_row_dict['Forged Transmits'] = str(sec_policy_val).lower() if isinstance(sec_policy_val, bool) else sec_policy_val
                for h_key in ['Speed', 'Full Duplex', 'Blocked', 'Active Uplink', 'Standby Uplink', 'Policy',
                              'In Traffic Shaping', 'In Avg', 'In Peak', 'In Burst',
                              'Out Traffic Shaping', 'Out Avg', 'Out Peak', 'Out Burst',
                              'Reverse Policy', 'Notify Switch', 'Rolling Order', 'Check Beacon',
                              'Live Port Moving', 'Check Duplex', 'Check Error %', 'Check Speed',
                              'Percentage', 'Block Override', 'Config Reset', 'Shaping Override',
                              'Vendor Config Override', 'Sec. Policy Override', 'Teaming Override', 'Vlan Override',
                              'Port Group Key', 'Configured Ports', 'Static Ports', 'Dynamic Ports', 'Scope', 'Port Name Format', 'VMs']:
                    if h_key not in current_row_dict or current_row_dict[h_key] == '':
                        current_row_dict[h_key] = ""
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["distributed_port_groups"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} Distributed Port Group records in {output_filename}. AI Used: {use_ai}")

def generate_vcd_csv(use_ai=False): # ... (vCD function as in previous correct version)
    output_filename = "RVTools_tabvCD.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vCD', [])
    if not headers: print(f"Error: Headers for vCD not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["vm_cd_drives"].clear()
    if not ENVIRONMENT_DATA.get('vms'):
        print(f"Warning: Skipping {output_filename} generation as ENVIRONMENT_DATA['vms'] is empty.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    available_ds_names = [ds.get('Name') for ds in ENVIRONMENT_DATA.get('datastores', []) if ds.get('Name')]
    for vm_rec in ENVIRONMENT_DATA.get('vms', []):
        current_row_dict = {h: '' for h in headers}
        for common_header in ["VM", "Powerstate", "Template", "SRM Placeholder", "Annotation",
                              "Datacenter", "Cluster", "Host", "Folder",
                              "OS according to the configuration file", "OS according to the VMware Tools",
                              "VM ID", "VM UUID", "VI SDK Server", "VI SDK UUID"]:
            if common_header in headers and common_header in vm_rec:
                current_row_dict[common_header] = vm_rec[common_header]
        current_row_dict["VMRef"] = vm_rec.get("VM ID", "")
        ai_generated_vcd_data = None
        if use_ai:
            vcd_ai_context = {
                'vm_name': vm_rec['VM'], 'powerstate': vm_rec['Powerstate'],
                'datastore_names': available_ds_names if available_ds_names else ["fallback_ds_for_ai"]
            }
            ai_generated_vcd_data = generate_vcd_row_ai(vcd_ai_context)
        if use_ai and ai_generated_vcd_data:
            for key, val in ai_generated_vcd_data.items():
                if key in current_row_dict:
                    if isinstance(val, bool): current_row_dict[key] = str(val).lower()
                    else: current_row_dict[key] = val
        else:
            current_row_dict['Device Node'] = "CD/DVD drive 1"
            is_connected_random = generate_random_boolean()
            current_row_dict['Connected'] = str(is_connected_random).lower()
            current_row_dict['Starts Connected'] = str(generate_random_boolean() if is_connected_random else False).lower()
            if is_connected_random:
                device_type_choice = choose_random_from_list(['Client Device', 'Datastore ISO File'])
                if device_type_choice == 'Datastore ISO File':
                    ds_for_iso = random.choice(available_ds_names) if available_ds_names else "local_datastore_random"
                    iso_name = choose_random_from_list(['linux_distro.iso', 'windows_server.iso', 'vmware_tools_pkg.iso', 'utility_disk.iso'])
                    current_row_dict['Device Type'] = f"[{ds_for_iso}] ISOs/{iso_name}"
                else:
                    current_row_dict['Device Type'] = 'Client Device'
            else:
                current_row_dict['Device Type'] = choose_random_from_list(['IDE', ''])
        if not current_row_dict.get("Device Node"): current_row_dict["Device Node"] = "CD/DVD drive 1 (Fallback)"
        if current_row_dict.get("Connected") is None: current_row_dict["Connected"] = str(False).lower()
        if current_row_dict.get("Starts Connected") is None: current_row_dict["Starts Connected"] = str(False).lower()
        for header_key in headers:
            if current_row_dict[header_key] == '':
                if header_key == "Select": current_row_dict[header_key] = str(False)
                else: current_row_dict[header_key] = generate_random_string(length=3)
        rows_to_write.append(current_row_dict)
        ENVIRONMENT_DATA["vm_cd_drives"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} VM CD/DVD Drive records in {output_filename}. AI Used: {use_ai}")

def generate_vfileinfo_csv(use_ai=False): # ... (vFileInfo function as in previous correct version)
    output_filename = "RVTools_tabvFileInfo.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vFileInfo', [])
    if not headers: print(f"Error: Headers for vFileInfo not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["vm_files"].clear()
    if not ENVIRONMENT_DATA.get('vms'):
        print(f"Warning: Skipping {output_filename} generation as VM data is unavailable.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    for vm_rec in ENVIRONMENT_DATA.get('vms', []):
        vm_name = vm_rec.get('VM')
        datastore_name = vm_rec.get('Datastore', 'unknown_ds')
        vm_disks_from_env = [d for d in ENVIRONMENT_DATA.get('vm_disks', []) if d.get('VM') == vm_name]
        disk_info_for_ai = [d.get('Disk Path', f"{vm_name}_{idx}.vmdk") for idx, d in enumerate(vm_disks_from_env)]
        if not disk_info_for_ai: disk_info_for_ai = [f"{vm_name}.vmdk"]
        ai_generated_files_list = None
        if use_ai:
            file_info_ai_context = {
                'vm_name': vm_name, 'datastore_name': datastore_name,
                'disk_info': ", ".join(disk_info_for_ai),
                'disk_info_list': disk_info_for_ai
            }
            ai_generated_files_list = generate_vfileinfo_row_ai(file_info_ai_context)
        if use_ai and ai_generated_files_list and isinstance(ai_generated_files_list, list):
            for file_data_ai in ai_generated_files_list:
                current_row_dict = {h: '' for h in headers}
                current_row_dict['File Name'] = file_data_ai.get('File Name')
                current_row_dict['File Type'] = file_data_ai.get('File Type')
                current_row_dict['File Size in bytes'] = str(file_data_ai.get('File Size in bytes', 0))
                current_row_dict['Path'] = file_data_ai.get('Path', f"[{datastore_name}] {vm_name}/{file_data_ai.get('File Name','unknown_file')}")
                current_row_dict['Friendly Path Name'] = current_row_dict['Path']
                current_row_dict['VI SDK Server'] = vm_rec.get('VI SDK Server')
                current_row_dict['VI SDK UUID'] = vm_rec.get('VI SDK UUID')
                current_row_dict['Internal Sort Column'] = current_row_dict['Path']
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["vm_files"].append(current_row_dict)
        else:
            base_path = f"[{datastore_name}] {vm_name}/"
            files_to_generate_random = []
            files_to_generate_random.append({'name': f"{vm_name}.vmx", 'type': 'VMX', 'size': generate_random_integer(2000, 8000)})
            files_to_generate_random.append({'name': f"{vm_name}.nvram", 'type': 'NVRAM', 'size': generate_random_integer(8000, 16000)})
            files_to_generate_random.append({'name': 'vmware.log', 'type': 'LOG', 'size': generate_random_integer(100000, 5000000)})
            files_to_generate_random.append({'name': f"{vm_name}.vmsd", 'type': 'VMSD', 'size': generate_random_integer(0, 1024)})
            if vm_disks_from_env:
                for disk_idx, disk_rec_env in enumerate(vm_disks_from_env):
                    disk_file_name = disk_rec_env.get('Disk Path','').split('/')[-1] or f"{vm_name}_{disk_idx}.vmdk"
                    files_to_generate_random.append({'name': disk_file_name, 'type': 'VMDK Descriptor', 'size': generate_random_integer(1000,5000)})
                    files_to_generate_random.append({'name': disk_file_name.replace('.vmdk','-flat.vmdk'), 'type': 'VMDK Flat', 'size': int(disk_rec_env.get('Capacity MiB',generate_random_integer(1000,50000))) * 1024 * 1024})
            else:
                files_to_generate_random.append({'name': f"{vm_name}.vmdk", 'type': 'VMDK Descriptor', 'size': generate_random_integer(1000,5000)})
                files_to_generate_random.append({'name': f"{vm_name}-flat.vmdk", 'type': 'VMDK Flat', 'size': generate_random_integer(10240,51200) * 1024 * 1024})
            for file_info_rand in files_to_generate_random:
                current_row_dict = {h: '' for h in headers}
                full_path = base_path + file_info_rand['name']
                current_row_dict.update({
                    'Friendly Path Name': full_path, 'File Name': file_info_rand['name'],
                    'File Type': file_info_rand['type'], 'File Size in bytes': str(file_info_rand['size']),
                    'Path': full_path, 'Internal Sort Column': full_path,
                    'VI SDK Server': vm_rec.get('VI SDK Server'), 'VI SDK UUID': vm_rec.get('VI SDK UUID')
                })
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["vm_files"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} VM FileInfo records in {output_filename}. AI Used: {use_ai}")

def generate_vpartition_csv(use_ai=False): # ... (vPartition function as in previous correct version)
    output_filename = "RVTools_tabvPartition.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vPartition', [])
    if not headers: print(f"Error: Headers for vPartition not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["vm_partitions"] = []
    if not ENVIRONMENT_DATA.get('vms') or not ENVIRONMENT_DATA.get('vm_disks'):
        print(f"Warning: Skipping {output_filename} as VM or VM Disk data is unavailable.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    for vm_rec in ENVIRONMENT_DATA.get('vms', []):
        vm_disks_for_vm = [d for d in ENVIRONMENT_DATA.get('vm_disks', []) if d.get('VM') == vm_rec.get('VM')]
        if not vm_disks_for_vm: continue
        for disk_rec in vm_disks_for_vm:
            ai_generated_partitions_list = None
            if use_ai:
                partition_ai_context = {
                    'vm_name': vm_rec.get('VM'),
                    'os_type': vm_rec.get('OS according to the configuration file', 'linuxGuest'),
                    'disk_label': disk_rec.get('Disk'),
                    'disk_capacity_mib': disk_rec.get('Capacity MiB')
                }
                ai_generated_partitions_list = generate_vpartition_row_ai(partition_ai_context)
            if use_ai and ai_generated_partitions_list and isinstance(ai_generated_partitions_list, list):
                for part_data_ai in ai_generated_partitions_list:
                    current_row_dict = {h: vm_rec.get(h, '') for h in headers if h in vm_rec}
                    current_row_dict['Disk Key'] = disk_rec.get('Disk Key', generate_random_integer(2000, 2999))
                    current_row_dict['Disk'] = part_data_ai.get('Disk', 'AI_Part_Fallback')
                    cap_mib = int(part_data_ai.get('Capacity MiB', 0))
                    cons_mib = int(part_data_ai.get('Consumed MiB', 0))
                    current_row_dict['Capacity MiB'] = cap_mib
                    current_row_dict['Consumed MiB'] = min(cons_mib, cap_mib)
                    current_row_dict['Free MiB'] = cap_mib - current_row_dict['Consumed MiB']
                    current_row_dict['Free %'] = round((current_row_dict['Free MiB'] / cap_mib) * 100, 1) if cap_mib > 0 else 0
                    for header_key in headers:
                        if current_row_dict.get(header_key, '') == '': current_row_dict[header_key] = generate_random_string(length=3)
                    rows_to_write.append(current_row_dict)
                    ENVIRONMENT_DATA["vm_partitions"].append(current_row_dict)
            else:
                num_partitions = generate_random_integer(1, 2)
                disk_total_capacity_mib = int(disk_rec.get('Capacity MiB', 10240))
                for p_idx in range(num_partitions):
                    current_row_dict = {h: vm_rec.get(h, '') for h in headers if h in vm_rec}
                    current_row_dict['Disk Key'] = disk_rec.get('Disk Key', generate_random_integer(2000,2999))
                    os_type_simple = "win" if "win" in vm_rec.get('OS according to the configuration file','').lower() else "lin"
                    if os_type_simple == "win":
                        current_row_dict['Disk'] = f"{chr(ord('C')+p_idx)}:\\" if p_idx < 26 else f"Partition {p_idx+1}"
                    else:
                        current_row_dict['Disk'] = f"/dev/sd{chr(97+disk_rec.get('SCSI Unit #', p_idx))}{p_idx+1}" if disk_rec.get('SCSI Unit #') is not None else f"/part{p_idx+1}"
                    part_cap_mib = disk_total_capacity_mib // num_partitions
                    if p_idx == num_partitions -1 : part_cap_mib = disk_total_capacity_mib - (part_cap_mib * (num_partitions -1))
                    current_row_dict['Capacity MiB'] = part_cap_mib
                    current_row_dict['Consumed MiB'] = generate_random_integer(int(part_cap_mib*0.1), int(part_cap_mib*0.9))
                    current_row_dict['Free MiB'] = current_row_dict['Capacity MiB'] - current_row_dict['Consumed MiB']
                    current_row_dict['Free %'] = round((current_row_dict['Free MiB'] / current_row_dict['Capacity MiB']) * 100, 1) if current_row_dict['Capacity MiB'] > 0 else 0
                    for header_key in headers:
                        if current_row_dict.get(header_key, '') == '': current_row_dict[header_key] = generate_random_string(length=3)
                    rows_to_write.append(current_row_dict)
                    ENVIRONMENT_DATA["vm_partitions"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} VM Partition records in {output_filename}. AI Used: {use_ai}")

def generate_vsnapshot_csv(use_ai=False): # ... (vSnapshot function as in previous correct version)
    output_filename = "RVTools_tabvSnapshot.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vSnapshot', [])
    if not headers: print(f"Error: Headers for vSnapshot not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["vm_snapshots"] = []
    if not ENVIRONMENT_DATA.get('vms'):
        print(f"Warning: Skipping {output_filename} generation as VM data is unavailable.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    for vm_rec in ENVIRONMENT_DATA.get('vms', []):
        has_snapshots_random = generate_random_boolean() and generate_random_boolean()
        num_snapshots_to_gen_random = generate_random_integer(1, 3) if has_snapshots_random else 0
        vm_creation_date_str = vm_rec.get('Creation date', "2020/01/01 00:00:00")
        ai_generated_snapshots_list = None
        if use_ai:
            snapshot_ai_context = {
                'vm_name': vm_rec['VM'], 'vm_creation_date': vm_creation_date_str,
                'num_snapshots_requested': num_snapshots_to_gen_random
            }
            ai_generated_snapshots_list = generate_vsnapshot_row_ai(snapshot_ai_context)
        if use_ai and ai_generated_snapshots_list and isinstance(ai_generated_snapshots_list, list):
            for snap_data_ai in ai_generated_snapshots_list:
                current_row_dict = {h: vm_rec.get(h, '') for h in headers if h in vm_rec}
                for key, val in snap_data_ai.items():
                    if key in current_row_dict: current_row_dict[key] = val
                current_row_dict['VM'] = vm_rec['VM']
                current_row_dict['Powerstate'] = vm_rec['Powerstate']
                current_row_dict['Filename'] = f"[{vm_rec.get('Datastore','ds_unknown')}] {vm_rec.get('VM')}/{vm_rec.get('VM')}-{current_row_dict.get('Name','snap').replace(' ','_')}.vmsn"
                if 'Quiesced' in current_row_dict and isinstance(current_row_dict['Quiesced'], bool):
                    current_row_dict['Quiesced'] = str(current_row_dict['Quiesced']).lower()
                for header_key in headers:
                    if current_row_dict.get(header_key, '') == '': current_row_dict[header_key] = generate_random_string(length=3)
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["vm_snapshots"].append(current_row_dict)
        elif not use_ai and num_snapshots_to_gen_random > 0:
            for s_idx in range(num_snapshots_to_gen_random):
                current_row_dict = {h: vm_rec.get(h, '') for h in headers if h in vm_rec}
                snap_name = f"RandomSnap_{s_idx+1}_{generate_random_string(4)}"
                snap_date = generate_random_datetime(start_date_str=vm_creation_date_str)
                current_row_dict.update({
                    'Name': snap_name, 'Description': f"Random snapshot {s_idx+1} for {vm_rec['VM']}",
                    'Date / time': snap_date,
                    'Filename': f"[{vm_rec.get('Datastore','ds_unknown')}] {vm_rec.get('VM')}/{vm_rec.get('VM')}-{snap_name.replace(' ','_')}.vmsn",
                    'Size MiB (vmsn)': str(generate_random_integer(50, 1024)),
                    'Size MiB (total)': str(generate_random_integer(int(current_row_dict.get('Size MiB (vmsn)', 50)), int(vm_rec.get('Total disk capacity MiB', 20480)))),
                    'Quiesced': str(generate_random_boolean()).lower(),
                    'State': choose_random_from_list(["PoweredOff", "PoweredOn", "Suspended", "Valid"])
                })
                for header_key in headers:
                    if current_row_dict.get(header_key, '') == '': current_row_dict[header_key] = generate_random_string(length=3)
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["vm_snapshots"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} VM Snapshot records in {output_filename}. AI Used: {use_ai}")

def generate_vtools_csv(use_ai=False): # ... (vTools function as in previous correct version)
    output_filename = "RVTools_tabvTools.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vTools', [])
    if not headers: print(f"Error: Headers for vTools not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["vm_tools_status"] = []
    if not ENVIRONMENT_DATA.get('vms'):
        print(f"Warning: Skipping {output_filename} generation as VM data is unavailable.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    for vm_rec in ENVIRONMENT_DATA.get('vms', []):
        current_row_dict = {h: vm_rec.get(h, '') for h in headers if h in vm_rec}
        current_row_dict['VMRef'] = vm_rec.get('VM ID', '')
        current_row_dict['VM Version'] = vm_rec.get('HW version', '')
        ai_generated_vtools_data = None
        if use_ai:
            vtools_ai_context = {
                'vm_name': vm_rec['VM'],
                'os_type': vm_rec.get('OS according to the configuration file', 'unknownGuest'),
                'hw_version': vm_rec.get('HW version', 'vmx-15')
            }
            ai_generated_vtools_data = generate_vtools_row_ai(vtools_ai_context)
        if use_ai and ai_generated_vtools_data:
            for key, val in ai_generated_vtools_data.items():
                if key in current_row_dict:
                    if isinstance(val, bool): current_row_dict[key] = str(val).lower()
                    else: current_row_dict[key] = val
        else:
            tools_status = choose_random_from_list(['OK', 'Not running', 'Out of date', 'Not installed'])
            current_row_dict['Tools'] = tools_status
            current_row_dict['Tools Version'] = ''
            current_row_dict['Required Version'] = ''
            current_row_dict['Upgradeable'] = str(False).lower()
            if tools_status != 'Not installed':
                current_row_dict['Tools Version'] = str(generate_random_integer(10000, 12500))
                if tools_status == 'Out of date':
                    current_row_dict['Upgradeable'] = str(True).lower()
                    current_row_dict['Required Version'] = str(int(current_row_dict['Tools Version']) + generate_random_integer(10, 500))
                else:
                    current_row_dict['Required Version'] = current_row_dict['Tools Version']
            current_row_dict['Upgrade Policy'] = choose_random_from_list(['manual', 'upgradeAtPowerCycle'])
            current_row_dict['Sync time'] = str(generate_random_boolean() if tools_status == 'OK' else False).lower()
            current_row_dict['App status'] = choose_random_from_list(['Ok', 'Unstable', 'Error']) if tools_status == 'OK' else 'Unknown'
            current_row_dict['Heartbeat status'] = choose_random_from_list(['green', 'yellow', 'red', 'gray']) if tools_status == 'OK' else 'gray'
            current_row_dict['Kernel Crash state'] = "Unknown"
            current_row_dict['Operation Ready'] = str(tools_status == 'OK').lower()
            current_row_dict['State change support'] = ""
            current_row_dict['Interactive Guest'] = ""
        for header_key in headers:
            if current_row_dict.get(header_key, '') == '':
                if header_key == "Upgrade": current_row_dict[header_key] = ""
                else: current_row_dict[header_key] = generate_random_string(length=3)
        rows_to_write.append(current_row_dict)
        ENVIRONMENT_DATA["vm_tools_status"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} VM Tools records in {output_filename}. AI Used: {use_ai}")

def generate_vusb_csv(use_ai=False): # ... (vUSB function as in previous correct version)
    output_filename = "RVTools_tabvUSB.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vUSB', [])
    if not headers: print(f"Error: Headers for vUSB not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["vm_usb_devices"] = []
    if not ENVIRONMENT_DATA.get('vms'):
        print(f"Warning: Skipping {output_filename} generation as VM data is unavailable.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return
    for vm_rec in ENVIRONMENT_DATA.get('vms', []):
        has_usb_random = generate_random_integer(1, 10) == 1
        num_usb_to_gen_random = generate_random_integer(1, 2) if has_usb_random else 0
        ai_generated_usb_list = None
        if use_ai:
            vusb_ai_context = {
                'vm_name': vm_rec['VM'], 'num_usb_requested': num_usb_to_gen_random
            }
            ai_generated_usb_list = generate_vusb_row_ai(vusb_ai_context)
        if use_ai and ai_generated_usb_list and isinstance(ai_generated_usb_list, list):
            for i, usb_data_ai in enumerate(ai_generated_usb_list):
                current_row_dict = {h: vm_rec.get(h, '') for h in headers if h in vm_rec}
                for key, val in usb_data_ai.items():
                    if key in current_row_dict:
                        if isinstance(val, bool): current_row_dict[key] = str(val).lower()
                        else: current_row_dict[key] = val
                current_row_dict['VM'] = vm_rec['VM']
                current_row_dict['Powerstate'] = vm_rec['Powerstate']
                current_row_dict['VMRef'] = vm_rec.get('VM ID')
                if not current_row_dict.get('Device Node'): current_row_dict['Device Node'] = f"USB {i+1} (AI Fallback)"
                for header_key in headers:
                    if current_row_dict.get(header_key, '') == '': current_row_dict[header_key] = generate_random_string(length=3)
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["vm_usb_devices"].append(current_row_dict)
        elif not use_ai and num_usb_to_gen_random > 0:
            for u_idx in range(num_usb_to_gen_random):
                current_row_dict = {h: vm_rec.get(h, '') for h in headers if h in vm_rec}
                is_connected_random = generate_random_boolean()
                current_row_dict.update({
                    'Device Node': f"USB {u_idx+1}",
                    'Device Type': choose_random_from_list(["Generic USB Device", "USB Flash Drive", "USB Keyboard", "USB Mouse", "USB SmartCard Reader"]),
                    'Connected': str(is_connected_random).lower(),
                    'Family': choose_random_from_list(["storage", "hid", "audio", "smartcard", "other"]),
                    'Speed': choose_random_from_list(["1.1", "2.0", "3.0"]),
                    'EHCI enabled': str(generate_random_boolean()).lower(),
                    'Auto connect': str(generate_random_boolean() if is_connected_random else False).lower(),
                    'VMRef': vm_rec.get('VM ID')
                })
                for header_key in headers:
                    if current_row_dict.get(header_key, '') == '': current_row_dict[header_key] = generate_random_string(length=3)
                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["vm_usb_devices"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} VM USB Device records in {output_filename}. AI Used: {use_ai}")

def generate_vhealth_csv(use_ai=False): # ... (vHealth function as in previous correct version)
    output_filename = "RVTools_tabvHealth.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vHealth', [])
    if not headers: print(f"Error: Headers for vHealth not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["vcenter_health_statuses"] = []
    num_health_items_random = generate_random_integer(5, 15)
    vcenter_details = ENVIRONMENT_DATA.get('vcenter_details', {})
    vcenter_ip = ENVIRONMENT_DATA.get('vcenter_ip', "vcenter.unknown.local")
    vcenter_uuid = ENVIRONMENT_DATA.get('vcenter_uuid', generate_uuid())
    ai_generated_health_list = None
    if use_ai:
        health_ai_context = {
            'vcenter_version': vcenter_details.get('Fullname', 'vCenter Server (Unknown Version)'),
            'num_clusters': len(ENVIRONMENT_DATA.get('clusters', [])),
            'num_hosts': len(ENVIRONMENT_DATA.get('hosts', [])),
            'num_vms': len(ENVIRONMENT_DATA.get('vms', [])),
            'num_items_requested': num_health_items_random
        }
        ai_generated_health_list = generate_vhealth_row_ai(health_ai_context)
    if use_ai and ai_generated_health_list and isinstance(ai_generated_health_list, list):
        for health_data_ai in ai_generated_health_list:
            current_row_dict = {h: '' for h in headers}
            current_row_dict.update(health_data_ai)
            current_row_dict['VI SDK Server'] = vcenter_ip
            current_row_dict['VI SDK UUID'] = vcenter_uuid
            for header_key in headers:
                if header_key not in current_row_dict or current_row_dict[header_key] == '':
                    current_row_dict[header_key] = generate_random_string(length=5)
            rows_to_write.append(current_row_dict)
            ENVIRONMENT_DATA["vcenter_health_statuses"].append(current_row_dict)
    else:
        for _ in range(num_health_items_random):
            current_row_dict = {h: '' for h in headers}
            msg_type = choose_random_from_list(["Green", "Yellow", "Red", "Info", "Alarm"])
            current_row_dict['Message type'] = msg_type
            if msg_type == "Green":
                current_row_dict['Name'] = choose_random_from_list(["Host connectivity", "Datastore usage", "VMware Tools status", "vCenter services health"])
                current_row_dict['Message'] = f"{current_row_dict['Name']} is healthy and green."
            elif msg_type == "Yellow":
                current_row_dict['Name'] = choose_random_from_list(["Host resource usage", "VM snapshot age", "License expiry warning", "Storage capacity nearing full"])
                current_row_dict['Message'] = f"Warning: {current_row_dict['Name']} requires attention. Details: {generate_random_string(15)}"
            else:
                current_row_dict['Name'] = choose_random_from_list(["Host not responding", "Datastore inaccessible", "vCenter service down", "Security vulnerability detected"])
                current_row_dict['Message'] = f"{msg_type}: Critical issue with {current_row_dict['Name']}. Details: {generate_random_string(20)}"
            current_row_dict['VI SDK Server'] = vcenter_ip
            current_row_dict['VI SDK UUID'] = vcenter_uuid
            rows_to_write.append(current_row_dict)
            ENVIRONMENT_DATA["vcenter_health_statuses"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} vCenter Health records in {output_filename}. AI Used: {use_ai}")

def generate_vlicense_csv(use_ai=False): # ... (vLicense function as in previous correct version)
    output_filename = "RVTools_tabvLicense.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vLicense', [])
    if not headers: print(f"Error: Headers for vLicense not found."); return
    rows_to_write = []
    ENVIRONMENT_DATA["licenses"] = []
    num_license_types_random = generate_random_integer(2, 4)
    vcenter_details = ENVIRONMENT_DATA.get('vcenter_details', {})
    vcenter_version_for_ai = vcenter_details.get('Version', '8.0')
    total_sockets = sum(h.get('# CPU', 0) for h in ENVIRONMENT_DATA.get('hosts', []))
    is_vsan_active = any("vsan" in ds.get('Type','').lower() for ds in ENVIRONMENT_DATA.get('datastores',[]))
    vcenter_ip = ENVIRONMENT_DATA.get('vcenter_ip', "vcenter.unknown.local")
    vcenter_uuid = ENVIRONMENT_DATA.get('vcenter_uuid', generate_uuid())
    ai_generated_license_list = None
    if use_ai:
        license_ai_context = {
            'vcenter_version': vcenter_version_for_ai,
            'num_hosts': len(ENVIRONMENT_DATA.get('hosts', [])),
            'total_cpu_sockets': total_sockets, 'vsan_enabled': is_vsan_active,
            'num_license_types_requested': num_license_types_random
        }
        ai_generated_license_list = generate_vlicense_row_ai(license_ai_context)
    if use_ai and ai_generated_license_list and isinstance(ai_generated_license_list, list):
        for lic_data_ai in ai_generated_license_list:
            current_row_dict = {h: '' for h in headers}
            current_row_dict.update(lic_data_ai)
            current_row_dict['VI SDK Server'] = vcenter_ip
            current_row_dict['VI SDK UUID'] = vcenter_uuid
            for header_key in headers:
                 if header_key not in current_row_dict or current_row_dict[header_key] == '':
                    current_row_dict[header_key] = generate_random_string(length=3) if header_key not in ['Key', 'Labels'] else ('-'.join([generate_random_string(5).upper() for _ in range(5)]) if header_key == 'Key' else '')
            rows_to_write.append(current_row_dict)
            ENVIRONMENT_DATA["licenses"].append(current_row_dict)
    else:
        licenses_to_gen = []
        vc_ver_for_name = vcenter_details.get('Version', '8.0')
        licenses_to_gen.append({
            "Name": f"VMware vCenter Server {vc_ver_for_name} Standard",
            "Key": '-'.join([generate_random_string(5).upper() for _ in range(5)]),
            "Total": "1", "Used": "1", "Expiration Date": "Never",
            "Features": "vCenter Server management features, Centralized Inventory, Basic Monitoring", "Cost Unit": "Instance"
        })
        if total_sockets > 0:
            licenses_to_gen.append({
                "Name": f"VMware vSphere {vc_ver_for_name} Enterprise Plus",
                "Key": '-'.join([generate_random_string(5).upper() for _ in range(5)]),
                "Total": str(total_sockets), "Used": str(generate_random_integer(1, total_sockets)),
                "Expiration Date": "Never", "Features": "DRS, HA, vMotion, Storage vMotion, FT, Distributed Switch", "Cost Unit": "CPU Package"
            })
        if is_vsan_active and total_sockets > 0:
            licenses_to_gen.append({
                "Name": f"VMware vSAN {vc_ver_for_name} Standard",
                "Key": '-'.join([generate_random_string(5).upper() for _ in range(5)]),
                "Total": str(total_sockets), "Used": str(generate_random_integer(1, total_sockets)),
                "Expiration Date": "Never", "Features": "vSAN storage features, All-Flash Ready", "Cost Unit": "CPU Package"
            })
        while len(licenses_to_gen) < num_license_types_random:
            licenses_to_gen.append({
                "Name": f"Other VMware Product {generate_random_string(3)}",
                "Key": '-'.join([generate_random_string(5).upper() for _ in range(5)]),
                "Total": str(generate_random_integer(1,10)), "Used": str(generate_random_integer(1,5)),
                "Expiration Date": generate_random_datetime(start_date_str="2025/01/01 00:00:00", days_range=365*2),
                "Features": "Misc features, Addon", "Cost Unit": "VM"
            })
        for lic_data_rand in licenses_to_gen[:num_license_types_random]:
            current_row_dict = {h: '' for h in headers}
            current_row_dict.update(lic_data_rand)
            current_row_dict['VI SDK Server'] = vcenter_ip
            current_row_dict['VI SDK UUID'] = vcenter_uuid
            if not current_row_dict.get('Labels'): current_row_dict['Labels'] = ""
            rows_to_write.append(current_row_dict)
            ENVIRONMENT_DATA["licenses"].append(current_row_dict)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} License records in {output_filename}. AI Used: {use_ai}")

def generate_vmultipath_csv(use_ai=False):
    output_filename = "RVTools_tabvMultiPath.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vMultiPath', [])
    if not headers: print(f"Error: Headers for vMultiPath not found."); return

    rows_to_write = []
    ENVIRONMENT_DATA["host_multipaths"] = []

    if not ENVIRONMENT_DATA.get('hosts'):
        print(f"Warning: Skipping {output_filename} generation as ENVIRONMENT_DATA['hosts'] is empty.")
        with open(output_path, 'w', newline='') as f: csv.DictWriter(f, fieldnames=headers).writeheader()
        return

    for host_rec in ENVIRONMENT_DATA.get('hosts', []):
        num_luns_random = generate_random_integer(1, 4)

        host_datastores = [ds.get('Name') for ds in ENVIRONMENT_DATA.get('datastores', []) if host_rec.get('Host') in ds.get('Hosts', []) or host_rec.get('Cluster') == ds.get('Cluster name')]
        if not host_datastores: host_datastores = [ds.get('Name') for ds in ENVIRONMENT_DATA.get('datastores', [])][:2] # Fallback
        if not host_datastores: host_datastores = [f"fallback_ds_{generate_random_string(3)}"] # Absolute fallback

        host_hbas_info = [f"{h.get('Device')}({h.get('Type')})" for h in ENVIRONMENT_DATA.get('hbas', []) if h.get('Host') == host_rec.get('Host')]
        if not host_hbas_info: host_hbas_info = ["vmhba0(unknown)"] # Fallback

        ai_generated_lun_list = None
        if use_ai:
            multipath_ai_context = {
                'host_name': host_rec.get('Host'),
                'datastore_names_list': ",".join(host_datastores), # Pass as string for prompt
                'hba_info_list': ",".join(host_hbas_info), # Pass as string
                'num_luns_requested': num_luns_random
            }
            ai_generated_lun_list = generate_vmultipath_row_ai(multipath_ai_context)

        if use_ai and ai_generated_lun_list and isinstance(ai_generated_lun_list, list):
            for lun_data_ai in ai_generated_lun_list:
                current_row_dict = {h: '' for h in headers}
                # Populate with host context first
                for hc_key in ['Host', 'Cluster', 'Datacenter', 'VI SDK Server', 'VI SDK UUID']:
                    current_row_dict[hc_key] = host_rec.get(hc_key)
                # Merge AI data
                for key, val in lun_data_ai.items():
                    if key in current_row_dict: current_row_dict[key] = val

                # Fallbacks for critical fields if AI misses them
                if not current_row_dict.get('Disk'): current_row_dict['Disk'] = f"naa.6{generate_random_string(30,'').lower()}"
                if not current_row_dict.get('Display name'): current_row_dict['Display name'] = f"AI_LUN_{generate_random_string(4)}"
                if not current_row_dict.get('Policy'): current_row_dict['Policy'] = "VMW_PSP_RR"
                if not current_row_dict.get('Oper. State'): current_row_dict['Oper. State'] = "Active"

                for header_key in headers: # Ensure all headers have a value
                    if current_row_dict[header_key] == '': current_row_dict[header_key] = generate_random_string(length=3) # Generic fallback

                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["host_multipaths"].append(current_row_dict)
        else: # Random Path
            for l_idx in range(num_luns_random):
                current_row_dict = {h: '' for h in headers}
                current_row_dict.update({
                    'Host': host_rec.get('Host'), 'Cluster': host_rec.get('Cluster'),
                    'Datacenter': host_rec.get('Datacenter'),
                    'VI SDK Server': host_rec.get('VI SDK Server'), 'VI SDK UUID': host_rec.get('VI SDK UUID'),
                    'Disk': f"naa.6{generate_random_string(30,'').lower()}",
                    'Display name': f"LUN_{host_rec.get('Host','h').split('.')[0]}_{l_idx}",
                    'Datastore': random.choice(host_datastores) if host_datastores else f"ds_random_{l_idx}",
                    'Policy': choose_random_from_list(['VMW_PSP_RR', 'VMW_PSP_MRU', 'VMW_PSP_FIXED']),
                    'Oper. State': "Active",
                    'Vendor': choose_random_from_list(["DellEMC", "NetApp", "PureStorage", "HPE"]),
                    'Model': choose_random_from_list(["PowerMax", "FAS", "FlashArray", "Primera"]),
                    'Revision': f"{generate_random_integer(1,5)}.{generate_random_integer(0,9)}",
                    'Level': "Tier-1",
                    'Queue depth': str(choose_random_from_list([64,128,256]))
                })
                num_paths = generate_random_integer(1, 4)
                for p_idx in range(1, num_paths + 1):
                    hba_name_for_path = random.choice(host_hbas_info).split('(')[0] if host_hbas_info else f"vmhba{p_idx-1}"
                    current_row_dict[f'Path {p_idx}'] = f"fc.{hba_name_for_path}:0x{generate_random_string(16,'').lower()}:L{l_idx}"
                    current_row_dict[f'Path {p_idx} state'] = choose_random_from_list(["Active/Optimized", "Active/Non-Optimized", "Standby", "Dead"])

                for header_key in headers: # Fill any remaining blanks
                    if current_row_dict[header_key] == '': current_row_dict[header_key] = "" # Empty for most optional fields

                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["host_multipaths"].append(current_row_dict)

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)
    print(f"Generated {len(rows_to_write)} Multipath records in {output_filename}. AI Used: {use_ai}")

def generate_vport_csv(use_ai=False):
    output_filename = "RVTools_tabvPort.csv"
    output_path = os.path.join(CSV_SUBDIR, output_filename)
    headers = CSV_HEADERS.get('vPort', [])
    if not headers:
        print(f"Error: Headers for vPort not found.")
        return

    rows_data = [] # Store dicts first, then convert to list of lists
    ENVIRONMENT_DATA["standard_port_groups"] = []

    if not ENVIRONMENT_DATA.get('standard_vswitches'):
        print(f"Warning: Skipping {output_filename} generation as ENVIRONMENT_DATA['standard_vswitches'] is empty.")
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f) # Use csv.writer for list of lists
            writer.writerow(headers) # Write header row
        return

    for vswitch_rec in ENVIRONMENT_DATA.get('standard_vswitches', []):
        host_name = vswitch_rec.get('Host')
        # It's crucial to get the full host record for Datacenter and Cluster context
        host_rec_for_context = get_host_details_by_name(host_name)

        num_pg_random = generate_random_integer(1, 4)
        ai_generated_pg_list = None

        if use_ai:
            vport_ai_context = {
                'host_name': host_name,
                'vswitch_name': vswitch_rec.get('Switch'),
                'uplink_names': vswitch_rec.get('Uplinks', ''),
                'num_pg_requested': num_pg_random
            }
            ai_generated_pg_list = generate_vport_row_ai(vport_ai_context)

        if use_ai and ai_generated_pg_list and isinstance(ai_generated_pg_list, list):
            for pg_data_ai in ai_generated_pg_list:
                current_row_dict = {h: '' for h in headers}
                current_row_dict['Host'] = host_name
                current_row_dict['Datacenter'] = host_rec_for_context.get('Datacenter', '') if host_rec_for_context else ''
                current_row_dict['Cluster'] = host_rec_for_context.get('Cluster', '') if host_rec_for_context else ''
                current_row_dict['Switch'] = vswitch_rec.get('Switch')
                current_row_dict['VI SDK Server'] = vswitch_rec.get('VI SDK Server')
                current_row_dict['VI SDK UUID'] = vswitch_rec.get('VI SDK UUID')

                for key, val in pg_data_ai.items():
                    if key in current_row_dict:
                         # Ensure boolean values from AI are correctly stringified for CSV
                        if isinstance(val, bool): current_row_dict[key] = str(val)
                        else: current_row_dict[key] = val

                # Fallbacks for AI path if some keys are missing
                if not current_row_dict.get('Port Group'): current_row_dict['Port Group'] = f"AI_Fallback_PG_{generate_random_string(4)}"
                if not current_row_dict.get('VLAN'): current_row_dict['VLAN'] = "None"
                for sec_pol in ['Promiscuous Mode', 'Mac Changes', 'Forged Transmits']:
                    if not current_row_dict.get(sec_pol): current_row_dict[sec_pol] = "Reject"
                if current_row_dict.get('Traffic Shaping') is None: current_row_dict['Traffic Shaping'] = str(False)

                # Ensure traffic shaping values are present and correctly formatted based on 'Traffic Shaping'
                is_ts_enabled = current_row_dict.get('Traffic Shaping', 'False') == 'True' # Check string 'True'
                if is_ts_enabled:
                    current_row_dict['Width'] = str(current_row_dict.get('Width') or generate_random_integer(1000,10000))
                    current_row_dict['Peak'] = str(current_row_dict.get('Peak') or int(int(current_row_dict.get('Width',0)) * 1.5)) # Ensure Width is int for calc
                    current_row_dict['Burst'] = str(current_row_dict.get('Burst') or int(int(current_row_dict.get('Peak',0)) * 0.1)) # Ensure Peak is int for calc
                else:
                    current_row_dict['Width'], current_row_dict['Peak'], current_row_dict['Burst'] = "0", "0", "0"

                # Default policy fields (often inherited from vSwitch in reality, but RVTools shows them per PG)
                # These should ideally come from AI if specified, otherwise use vSwitch or defaults
                for policy_field in ['Policy', 'Reverse Policy', 'Notify Switch', 'Rolling Order', 'Offload', 'TSO', 'Zero Copy Xmit']:
                    if not current_row_dict.get(policy_field): # If AI didn't provide it
                         current_row_dict[policy_field] = vswitch_rec.get(policy_field, generate_random_string(length=3) if policy_field in ['Policy'] else str(generate_random_boolean()))


                rows_data.append(current_row_dict)
                ENVIRONMENT_DATA["standard_port_groups"].append(current_row_dict)
        else: # Random Path
            for pg_idx in range(num_pg_random):
                current_row_dict = {h: '' for h in headers}
                current_row_dict['Host'] = host_name
                current_row_dict['Datacenter'] = host_rec_for_context.get('Datacenter', '') if host_rec_for_context else ''
                current_row_dict['Cluster'] = host_rec_for_context.get('Cluster', '') if host_rec_for_context else ''
                current_row_dict['Switch'] = vswitch_rec.get('Switch')

                vlan_id_rand = generate_random_integer(1, 4094)
                current_row_dict['Port Group'] = f"PG_VLAN{vlan_id_rand}_{pg_idx}" if generate_random_boolean() else choose_random_from_list(["VM Network", "Management Network", f"Storage_{pg_idx}"])
                current_row_dict['VLAN'] = str(vlan_id_rand) if generate_random_boolean() else choose_random_from_list(["None", "All (Trunk)"])

                sec_policy_val = choose_random_from_list(["Accept", "Reject"])
                current_row_dict['Promiscuous Mode'] = sec_policy_val
                current_row_dict['Mac Changes'] = sec_policy_val
                current_row_dict['Forged Transmits'] = sec_policy_val

                ts_enabled_random = generate_random_boolean()
                current_row_dict['Traffic Shaping'] = str(ts_enabled_random)
                if ts_enabled_random:
                    current_row_dict['Width'] = str(generate_random_integer(10000, 1000000))
                    current_row_dict['Peak'] = str(int(int(current_row_dict['Width']) * 1.5))
                    current_row_dict['Burst'] = str(int(int(current_row_dict['Peak']) * 0.1))
                else:
                    current_row_dict['Width'], current_row_dict['Peak'], current_row_dict['Burst'] = "0", "0", "0"

                current_row_dict['Policy'] = vswitch_rec.get('Policy', "loadbalance_srcid")
                current_row_dict['Reverse Policy'] = vswitch_rec.get('Reverse Policy', str(True))
                current_row_dict['Notify Switch'] = vswitch_rec.get('Notify Switch', str(True))
                current_row_dict['Rolling Order'] = vswitch_rec.get('Rolling Order', str(False))
                current_row_dict['Offload'] = vswitch_rec.get('Offload', str(True))
                current_row_dict['TSO'] = vswitch_rec.get('TSO', str(True))
                current_row_dict['Zero Copy Xmit'] = vswitch_rec.get('Zero Copy Xmit', str(True))

                current_row_dict['VI SDK Server'] = vswitch_rec.get('VI SDK Server')
                current_row_dict['VI SDK UUID'] = vswitch_rec.get('VI SDK UUID')

                rows_data.append(current_row_dict)
                ENVIRONMENT_DATA["standard_port_groups"].append(current_row_dict)

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_data)
    print(f"Generated {len(rows_data)} Standard vSwitch Port Group records in {output_filename}. AI Used: {use_ai}")


def generate_vdisk_csv(use_ai=False):
    filepath = os.path.join(CSV_SUBDIR, "RVTools_tabvDisk.csv"); headers = CSV_HEADERS["vDisk"]
    if not ENVIRONMENT_DATA["vms"]: print("No VM data for vDisk CSV."); return

    ENVIRONMENT_DATA['vm_disks'] = []

    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers); writer.writeheader()
        for vm_r in ENVIRONMENT_DATA["vms"]:
            num_disks_for_vm = vm_r.get("Disks", generate_random_integer(1,2))
            for i in range(num_disks_for_vm):
                row_data = {h: "" for h in headers}; disk_label = f"Hard disk {i+1}"
                disk_path = f"[{vm_r['Datastore']}] {vm_r['VM']}/{vm_r['VM']}_{i}.vmdk"
                capacity_mib_val = random.choice([20*1024, 40*1024, 80*1024, 100*1024])
                disk_key_val = 2000 + i
                scsi_unit_val = i

                row_data.update({ "VM": vm_r["VM"], "Powerstate": vm_r["Powerstate"], "Template": "False", "SRM Placeholder": "False",
                    "Disk": disk_label, "Disk Key": disk_key_val, "Disk UUID": generate_uuid(),
                    "Disk Path": disk_path, "Capacity MiB": capacity_mib_val,
                    "Controller": f"SCSI controller {i}", "Label": disk_label, "SCSI Unit #": scsi_unit_val, "Unit #": scsi_unit_val,
                    "Annotation": vm_r.get("Annotation", ""), "Datacenter": vm_r["Datacenter"], "Cluster": vm_r["Cluster"], "Host": vm_r["Host"],
                    "OS according to the configuration file": vm_r["OS according to the configuration file"],
                    "OS according to the VMware Tools": vm_r["OS according to the VMware Tools"],
                    "VM ID": vm_r["VM ID"], "VM UUID": vm_r["VM UUID"],
                    "VI SDK Server": vm_r["VI SDK Server"], "VI SDK UUID": vm_r["VI SDK UUID"]})

                disk_env_record = { 'VM': vm_r["VM"], 'Disk': disk_label, 'Disk Path': disk_path,
                                    'Capacity MiB': capacity_mib_val, 'Disk Key': disk_key_val,
                                    'SCSI Unit #': scsi_unit_val }
                ENVIRONMENT_DATA['vm_disks'].append(disk_env_record)

                if use_ai:
                    ai_generated_data = generate_vdisk_row_ai(vm_r, i, disk_label)
                    for key, value in ai_generated_data.items():
                        if key in row_data: row_data[key] = value
                for h in headers:
                    if row_data[h] == "":
                        if h == "Thin" and not row_data.get(h): row_data[h] = str(generate_random_boolean())
                        elif h == "Disk Mode" and not row_data.get(h) : row_data[h] = "persistent"
                        elif h == "Sharing mode" and not row_data.get(h) : row_data[h] = "nobussharing"
                        elif "mode" in h.lower(): row_data[h] = generate_random_string(3)
                        else: row_data[h] = str(generate_random_integer(0,10))
                writer.writerow(row_data)
    print(f"Generated vDisk records in {filepath}. AI: {use_ai}. (Updated ENVIRONMENT_DATA['vm_disks'])")

def generate_vnetwork_csv(use_ai=False): # ... (vNetwork function as in previous correct version)
    filepath = os.path.join(CSV_SUBDIR, "RVTools_tabvNetwork.csv"); headers = CSV_HEADERS["vNetwork"]
    if not ENVIRONMENT_DATA["vms"]: print("No VM data for vNetwork CSV."); return
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers); writer.writeheader()
        for vm_r in ENVIRONMENT_DATA["vms"]:
            num_nics = vm_r.get("NICs", generate_random_integer(1,2))
            for i in range(num_nics):
                row_data = {h: "" for h in headers}; nic_label = f"Network adapter {i+1}"
                is_connected = vm_r["Powerstate"] == "poweredOn"
                ip_address = vm_r.get("Primary IP Address", "") if i == 0 and is_connected else \
                             (generate_random_ip_address() if is_connected and generate_random_boolean() else "")
                row_data.update({ "VM": vm_r["VM"], "Powerstate": vm_r["Powerstate"], "Template": "False", "SRM Placeholder": "False",
                    "NIC label": nic_label, "Adapter": "VMXNET3", "Network": f"{vm_r['Datacenter']}-VLAN{generate_random_integer(100,105) + i*10}",
                    "Switch": f"DVSwitch-{vm_r['Datacenter']}", "Connected": str(is_connected), "Starts Connected": "True",
                    "Mac Address": generate_random_mac_address(), "IPv4 Address": ip_address,
                    "Annotation": vm_r.get("Annotation", ""), "Datacenter": vm_r["Datacenter"], "Cluster": vm_r["Cluster"], "Host": vm_r["Host"],
                    "OS according to the configuration file": vm_r["OS according to the configuration file"],
                    "OS according to the VMware Tools": vm_r["OS according to the VMware Tools"],
                    "VM ID": vm_r["VM ID"], "VM UUID": vm_r["VM UUID"],
                    "VI SDK Server": vm_r["VI SDK Server"], "VI SDK UUID": vm_r["VI SDK UUID"]})
                if use_ai:
                    ai_generated_data = generate_vnetwork_row_ai(vm_r, i, nic_label)
                    for key, value in ai_generated_data.items():
                        if key in row_data: row_data[key] = value
                for h in headers:
                    if row_data[h] == "": row_data[h] = generate_random_string(3)
                writer.writerow(row_data)
    print(f"Generated vNetwork records in {filepath}. AI: {use_ai}")

def generate_vcpu_csv(): # ... (vCPU function as in previous correct version)
    filepath = os.path.join(CSV_SUBDIR, "RVTools_tabvCPU.csv"); headers = CSV_HEADERS["vCPU"]
    if not ENVIRONMENT_DATA["vms"]: print("No VM data for vCPU CSV."); return
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers); writer.writeheader()
        for vm_r in ENVIRONMENT_DATA["vms"]:
            row_data = {h: "" for h in headers}; cpus = vm_r["CPUs"]; cores_ps = vm_r["CoresPerSocket"]
            sockets = cpus // cores_ps if cores_ps > 0 and cpus > 0 else cpus
            row_data.update({ "VM": vm_r["VM"], "Powerstate": vm_r["Powerstate"], "Template": "False", "SRM Placeholder": "False",
                "CPUs": cpus, "Sockets": sockets, "Cores p/s": cores_ps, "Annotation": vm_r.get("Annotation", ""),
                "Datacenter": vm_r["Datacenter"], "Cluster": vm_r["Cluster"], "Host": vm_r["Host"],
                "OS according to the configuration file": vm_r["OS according to the configuration file"],
                "OS according to the VMware Tools": vm_r["OS according to the VMware Tools"],
                "VM ID": vm_r["VM ID"], "VM UUID": vm_r["VM UUID"], "VI SDK Server": vm_r["VI SDK Server"], "VI SDK UUID": vm_r["VI SDK UUID"],
                "Hot Add": str(generate_random_boolean()), "Hot Remove": str(generate_random_boolean())})
            for h in headers:
                if row_data[h] == "": row_data[h] = str(generate_random_integer(0,10)) if "Limit" in h or "Reservation" in h or "Shares" in h or "Overall" in h or "Max" in h else generate_random_string(3)
            writer.writerow(row_data)
    print(f"Generated {len(ENVIRONMENT_DATA['vms'])} vCPU records in {filepath}")

def generate_vmemory_csv(): # ... (vMemory function as in previous correct version)
    filepath = os.path.join(CSV_SUBDIR, "RVTools_tabvMemory.csv"); headers = CSV_HEADERS["vMemory"]
    if not ENVIRONMENT_DATA["vms"]: print("No VM data for vMemory CSV."); return
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers); writer.writeheader()
        for vm_r in ENVIRONMENT_DATA["vms"]:
            row_data = {h: "" for h in headers}; size_mib = vm_r["Memory"]
            active_mem = generate_random_integer(int(size_mib*0.1), int(size_mib*0.5)) if vm_r["Powerstate"] == "poweredOn" else 0
            consumed_mem = generate_random_integer(active_mem, int(size_mib*0.8)) if vm_r["Powerstate"] == "poweredOn" else 0
            row_data.update({ "VM": vm_r["VM"], "Powerstate": vm_r["Powerstate"], "Template": "False", "SRM Placeholder": "False",
                "Size MiB": size_mib, "Consumed": consumed_mem, "Active": active_mem,
                "Ballooned": generate_random_integer(0, int(size_mib*0.1)) if vm_r["Powerstate"] == "poweredOn" else 0,
                "Annotation": vm_r.get("Annotation", ""), "Datacenter": vm_r["Datacenter"], "Cluster": vm_r["Cluster"], "Host": vm_r["Host"],
                "OS according to the configuration file": vm_r["OS according to the configuration file"],
                "OS according to the VMware Tools": vm_r["OS according to the VMware Tools"],
                "VM ID": vm_r["VM ID"], "VM UUID": vm_r["VM UUID"], "VI SDK Server": vm_r["VI SDK Server"], "VI SDK UUID": vm_r["VI SDK UUID"],
                "Hot Add": str(generate_random_boolean())})
            for h in headers:
                if row_data[h] == "": row_data[h] = str(generate_random_integer(0,1000)) if "MiB" in h or "Overhead" in h or "Max" in h else generate_random_string(3)
            writer.writerow(row_data)
    print(f"Generated {len(ENVIRONMENT_DATA['vms'])} vMemory records in {filepath}")

# --- ZIP Archive Creation ---
def create_zip_archive(): # ... (create_zip_archive function as in previous correct version)
    zip_filepath = os.path.join(OUTPUT_DIR, ZIP_FILENAME)
    csv_files = glob.glob(os.path.join(CSV_SUBDIR, "*.csv"))
    if not csv_files: print("No CSV files found to archive."); return
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for csv_file in csv_files:
            zipf.write(csv_file, os.path.basename(csv_file))
    print(f"Successfully created ZIP archive: {zip_filepath}\nIncluded files:")
    for f in csv_files: print(f"  - {os.path.basename(f)}")

# --- Helper functions to access environment data ---
# ... (Helper functions as in previous correct version)
def get_all_vm_names(): return [vm["VM"] for vm in ENVIRONMENT_DATA["vms"]]
def get_vm_details_by_name(vm_name):
    for vm in ENVIRONMENT_DATA["vms"]:
        if vm["VM"] == vm_name: return vm
    return None
def get_all_host_names(): return [host["Host"] for host in ENVIRONMENT_DATA["hosts"]]
def get_host_details_by_name(host_name):
    for host in ENVIRONMENT_DATA["hosts"]:
        if host["Host"] == host_name: return host
    return None
def get_all_cluster_names(): return [c["Name"] for c in ENVIRONMENT_DATA["clusters"]]
def get_all_datastore_names(): return [ds["Name"] for ds in ENVIRONMENT_DATA["datastores"]]
def get_all_resource_pool_paths(): return [rp["rp_path"] for rp in ENVIRONMENT_DATA["resource_pools"]]
def get_vcenter_details(): return ENVIRONMENT_DATA.get("vcenter_details")
def get_all_hbas(): return ENVIRONMENT_DATA.get("hbas")
def get_all_host_nics(): return ENVIRONMENT_DATA.get("host_nics")
def get_all_host_vmkernel_nics(): return ENVIRONMENT_DATA.get("host_vmkernel_nics")
def get_all_standard_vswitches(): return ENVIRONMENT_DATA.get("standard_vswitches")
def get_all_distributed_vswitches(): return ENVIRONMENT_DATA.get("distributed_vswitches")
def get_all_distributed_port_groups(): return ENVIRONMENT_DATA.get("distributed_port_groups")
def get_all_vm_cd_drives(): return ENVIRONMENT_DATA.get("vm_cd_drives")
def get_all_vm_files(): return ENVIRONMENT_DATA.get("vm_files")
def get_all_vm_partitions(): return ENVIRONMENT_DATA.get("vm_partitions")
def get_all_vm_snapshots(): return ENVIRONMENT_DATA.get("vm_snapshots")
def get_all_vm_tools_status(): return ENVIRONMENT_DATA.get("vm_tools_status")
def get_all_vm_usb_devices(): return ENVIRONMENT_DATA.get("vm_usb_devices")
def get_all_vcenter_health_statuses(): return ENVIRONMENT_DATA.get("vcenter_health_statuses")
def get_all_licenses(): return ENVIRONMENT_DATA.get("licenses")
def get_all_host_multipaths(): return ENVIRONMENT_DATA.get("host_multipaths")
def get_all_standard_port_groups(): return ENVIRONMENT_DATA.get("standard_port_groups") # Added getter


if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    if not os.path.exists(CSV_SUBDIR):
        os.makedirs(CSV_SUBDIR)
        if not glob.glob(os.path.join(CSV_SUBDIR, "*")):
            with open(os.path.join(CSV_SUBDIR, ".gitkeep"), 'w') as f: pass
    else:
        print(f"Clearing old CSVs from {CSV_SUBDIR}...")
        for old_csv in glob.glob(os.path.join(CSV_SUBDIR, "*.csv")):
            try: os.remove(old_csv)
            except OSError as e: print(f"Error removing {old_csv}: {e}")

    print("Starting RVTools data generation...")
    generate_vinfo_csv(num_rows=15, use_ai=True)
    generate_vsource_csv(use_ai=True)
    generate_vdatastore_csv(use_ai=True)
    generate_vhba_csv(use_ai=True)
    generate_vnic_csv(use_ai=True)
    generate_vscvmk_csv(use_ai=True)
    generate_vswitch_csv(use_ai=True)
    generate_dvswitch_csv(use_ai=True)
    generate_dvport_csv(use_ai=True)
    generate_vcd_csv(use_ai=True)
    generate_vdisk_csv(use_ai=True)
    generate_vfileinfo_csv(use_ai=True)
    generate_vpartition_csv(use_ai=True)
    generate_vsnapshot_csv(use_ai=True)
    generate_vtools_csv(use_ai=True)
    generate_vusb_csv(use_ai=True)
    generate_vhealth_csv(use_ai=True)
    generate_vlicense_csv(use_ai=True)
    generate_vmultipath_csv(use_ai=True)
    generate_vport_csv(use_ai=True) # Added call
    # generate_vhost_csv must run after vHBA and vNIC to get accurate counts
    generate_vhost_csv(use_ai=True)
    generate_vcluster_csv(use_ai=True)
    generate_vrp_csv(use_ai=True)
    generate_vnetwork_csv(use_ai=True)
    generate_vcpu_csv()
    generate_vmemory_csv()

    print(f"\nRVTools data generation complete in {CSV_SUBDIR}")
    create_zip_archive()

```
