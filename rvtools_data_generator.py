# ASCII Art Logo Placeholder
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
    "host_nics": [], "host_vmkernel_nics": [], "standard_vswitches": [], # Added standard_vswitches
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
    "vSwitch": "Host,Datacenter,Cluster,Switch,# Ports,Free Ports,Promiscuous Mode,Mac Changes,Forged Transmits,Traffic Shaping,Width,Peak,Burst,Policy,Reverse Policy,Notify Switch,Rolling Order,Offload,TSO,Zero Copy Xmit,MTU,Uplinks,VI SDK Server,VI SDK UUID".split(','), # Added Uplinks
    "vMemory": "VM,Powerstate,Template,SRM Placeholder,Size MiB,Memory Reservation Locked To Max,Overhead,Max,Consumed,Consumed Overhead,Private,Shared,Swapped,Ballooned,Active,Entitlement,DRS Entitlement,Level,Shares,Reservation,Limit,Hot Add,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
    "vCPU": "VM,Powerstate,Template,SRM Placeholder,CPUs,Sockets,Cores p/s,Max,Overall,Level,Shares,Reservation,Entitlement,DRS Entitlement,Limit,Hot Add,Hot Remove,Numa Hotadd Exposed,Annotation,Datacenter,Cluster,Host,Folder,OS according to the configuration file,OS according to the VMware Tools,VM ID,VM UUID,VI SDK Server,VI SDK UUID".split(','),
}

# --- AI Prompt Templates ---
# ... (VINFO_AI_PROMPT_TEMPLATE, VHOST_AI_PROMPT_TEMPLATE, etc. remain unchanged)
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
def _get_vswitch_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vSwitch', [])
    return "\n".join([f"- `{header}`: (data for this column)" for header in headers])


# --- Mock AI Row Generation Functions ---
def _call_mock_ai(prompt_template, context, relevant_headers_key, entity_name_for_log): # ... (Unchanged, handles new vSwitch case)
    if relevant_headers_key in ['vDatastore', 'vRP', 'vSource', 'vHBA', 'vNIC', 'vSC_VMK', 'vSwitch']:
        context['column_details_block'] = {
            'vDatastore': _get_vdatastore_column_descriptions_for_prompt,
            'vRP': _get_vrp_column_descriptions_for_prompt,
            'vSource': _get_vsource_column_descriptions_for_prompt,
            'vHBA': _get_vhba_column_descriptions_for_prompt,
            'vNIC': _get_vnic_column_descriptions_for_prompt,
            'vSC_VMK': _get_vscvmk_column_descriptions_for_prompt,
            'vSwitch': _get_vswitch_column_descriptions_for_prompt,
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
    elif relevant_headers_key == "vSwitch": # New AI mock for vSwitch
        vswitch_list = []
        phys_nics = context.get('physical_nic_names', [])
        for i in range(context.get('num_vswitches_requested',1)):
            num_uplinks_for_switch = generate_random_integer(1, len(phys_nics) if phys_nics else 1)
            selected_uplinks_for_switch = random.sample(phys_nics, min(num_uplinks_for_switch, len(phys_nics))) if phys_nics else [f"vmnic{j+i*2}" for j in range(num_uplinks_for_switch)] # Ensure unique uplinks if phys_nics is empty

            vswitch_list.append({
                "Switch": f"vSwitch{i}-AI",
                "# Ports": 128, "Free Ports": generate_random_integer(60,120),
                "Promiscuous Mode": "Reject", "Mac Changes": "Accept", "Forged Transmits": "Accept",
                "Uplinks": ",".join(selected_uplinks_for_switch),
                "MTU": 1500
            })
        mock_ai_data = vswitch_list
    return mock_ai_data

# ... (generate_vinfo_row_ai, etc. AI row generators remain unchanged)
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

def generate_vswitch_row_ai(vswitch_context): # New AI row generator for vSwitch
    return _call_mock_ai(VSWITCH_AI_PROMPT_TEMPLATE, vswitch_context, "vSwitch", vswitch_context['host_name'])


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
                "Resource pool": vm_r["Resource pool"]
            })
            if use_ai:
                ai_generated_data = generate_vinfo_row_ai(vm_r)
                for key, value in ai_generated_data.items():
                    if key in row_data: row_data[key] = value
            for h in headers:
                if row_data[h] == "":
                    if h == "Consolidation Needed": row_data[h] = str(generate_random_boolean())
                    elif h == "PowerOn": row_data[h] = generate_random_datetime(days_range=30) if vm_r["Powerstate"] == "poweredOn" else ""
                    elif h == "Creation date": row_data[h] = generate_random_datetime(start_date_str="2020/01/01 00:00:00")
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

def generate_vswitch_csv(use_ai=False):
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
                'host_name': host_rec.get('Host'),
                'physical_nic_names': host_phys_nics,
                'num_vswitches_requested': num_vswitches_to_gen_random
            }
            ai_generated_vswitch_list = generate_vswitch_row_ai(vswitch_ai_context)

        if use_ai and ai_generated_vswitch_list and isinstance(ai_generated_vswitch_list, list):
            for i, vswitch_data_ai in enumerate(ai_generated_vswitch_list):
                current_row_dict = {h: '' for h in headers}
                current_row_dict.update({ # Base host context
                    'Host': host_rec.get('Host'), 'Datacenter': host_rec.get('Datacenter'),
                    'Cluster': host_rec.get('Cluster'), 'VI SDK Server': host_rec.get('VI SDK Server'),
                    'VI SDK UUID': host_rec.get('VI SDK UUID')
                })
                # Merge AI data
                for key, val in vswitch_data_ai.items():
                    if key in current_row_dict: current_row_dict[key] = val

                # Fallbacks for critical fields if AI misses them
                if not current_row_dict.get('Switch'): current_row_dict['Switch'] = f"vSwitch{i}_AI_fallback"
                if not current_row_dict.get('# Ports'): current_row_dict['# Ports'] = 128
                if not current_row_dict.get('Free Ports'): current_row_dict['Free Ports'] = generate_random_integer(0, int(current_row_dict['# Ports']))
                if not current_row_dict.get('MTU'): current_row_dict['MTU'] = 1500

                for pol_key in ['Promiscuous Mode', 'Mac Changes', 'Forged Transmits']:
                    if not current_row_dict.get(pol_key): current_row_dict[pol_key] = "Reject"

                for header_key in headers: # Ensure all headers have a value
                    if current_row_dict[header_key] == '': current_row_dict[header_key] = generate_random_string(length=3)

                rows_to_write.append(current_row_dict)
                ENVIRONMENT_DATA["standard_vswitches"].append(current_row_dict)
        else: # Random path
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

                # Default other policy fields
                current_row_dict['Traffic Shaping'] = str(False)
                current_row_dict['Width'] = "" # Empty if not shaping
                current_row_dict['Peak'] = ""
                current_row_dict['Burst'] = ""
                current_row_dict['Policy'] = "loadbalance_srcid" # Common default
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


def generate_vdisk_csv(use_ai=False): # ... (vDisk function as in previous correct version)
    filepath = os.path.join(CSV_SUBDIR, "RVTools_tabvDisk.csv"); headers = CSV_HEADERS["vDisk"]
    if not ENVIRONMENT_DATA["vms"]: print("No VM data for vDisk CSV."); return
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers); writer.writeheader()
        for vm_r in ENVIRONMENT_DATA["vms"]:
            num_disks = vm_r.get("Disks", generate_random_integer(1,2))
            for i in range(num_disks):
                row_data = {h: "" for h in headers}; disk_label = f"Hard disk {i+1}"
                row_data.update({ "VM": vm_r["VM"], "Powerstate": vm_r["Powerstate"], "Template": "False", "SRM Placeholder": "False",
                    "Disk": disk_label, "Disk Key": 2000 + i, "Disk UUID": generate_uuid(),
                    "Disk Path": f"[{vm_r['Datastore']}] {vm_r['VM']}/{vm_r['VM']}_{i}.vmdk",
                    "Capacity MiB": random.choice([20*1024, 40*1024, 80*1024, 100*1024]),
                    "Controller": f"SCSI controller {i}", "Label": disk_label, "SCSI Unit #": i,
                    "Annotation": vm_r.get("Annotation", ""), "Datacenter": vm_r["Datacenter"], "Cluster": vm_r["Cluster"], "Host": vm_r["Host"],
                    "OS according to the configuration file": vm_r["OS according to the configuration file"],
                    "OS according to the VMware Tools": vm_r["OS according to the VMware Tools"],
                    "VM ID": vm_r["VM ID"], "VM UUID": vm_r["VM UUID"],
                    "VI SDK Server": vm_r["VI SDK Server"], "VI SDK UUID": vm_r["VI SDK UUID"]})
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
    print(f"Generated vDisk records in {filepath}. AI: {use_ai}")

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
    generate_vhba_csv(use_ai=True)
    generate_vnic_csv(use_ai=True)
    generate_vscvmk_csv(use_ai=True)
    generate_vswitch_csv(use_ai=True) # New, with AI
    # generate_vhost_csv must run after vHBA and vNIC to get accurate counts
    generate_vhost_csv(use_ai=True)
    generate_vcluster_csv(use_ai=True)
    generate_vdatastore_csv(use_ai=True)
    generate_vrp_csv(use_ai=True)
    generate_vdisk_csv(use_ai=True)
    generate_vnetwork_csv(use_ai=True)
    generate_vcpu_csv()
    generate_vmemory_csv()

    print(f"\nRVTools data generation complete in {CSV_SUBDIR}")
    create_zip_archive()

```
