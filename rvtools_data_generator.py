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
