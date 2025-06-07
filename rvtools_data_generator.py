# ASCII Art Logo Placeholder
import random
import string
import uuid
from datetime import datetime, timedelta
import csv
import zipfile
import os
import glob
import json

# For actual AI calls (commented out for now)
# import openai
# import google.generativeai as genai
# import boto3 # For Bedrock

# Global store for generated data
ENVIRONMENT_DATA = {
    'vms': [],    # List of VM dictionaries
    'hosts': []   # List of Host dictionaries (to be populated later)
}

CSV_HEADERS = {
    'dvPort': ['Port', 'Switch', 'Type', '# Ports', 'VLAN', 'Speed', 'Full Duplex', 'Blocked', 'Allow Promiscuous', 'Mac Changes', 'Active Uplink', 'Standby Uplink', 'Policy', 'Forged Transmits', 'In Traffic Shaping', 'In Avg', 'In Peak', 'In Burst', 'Out Traffic Shaping', 'Out Avg', 'Out Peak', 'Out Burst', 'Reverse Policy', 'Notify Switch', 'Rolling Order', 'Check Beacon', 'Live Port Moving', 'Check Duplex', 'Check Error %', 'Check Speed', 'Percentage', 'Block Override', 'Config Reset', 'Shaping Override', 'Vendor Config Override', 'Sec. Policy Override', 'Teaming Override', 'Vlan Override', 'Object ID', 'VI SDK Server', 'VI SDK UUID'],
    'dvSwitch': ['Switch', 'Datacenter', 'Name', 'Vendor', 'Version', 'Description', 'Created', 'Host members', 'Max Ports', '# Ports', '# VMs', 'In Traffic Shaping', 'In Avg', 'In Peak', 'In Burst', 'Out Traffic Shaping', 'Out Avg', 'Out Peak', 'Out Burst', 'CDP Type', 'CDP Operation', 'LACP Name', 'LACP Mode', 'LACP Load Balance Alg.', 'Max MTU', 'Contact', 'Admin Name', 'Object ID', 'VI SDK Server', 'VI SDK UUID'],
    'vCD': ['Select', 'VM', 'Powerstate', 'Template', 'SRM Placeholder', 'Device Node', 'Connected', 'Starts Connected', 'Device Type', 'Annotation', 'Datacenter', 'Cluster', 'Host', 'Folder', 'OS according to the configuration file', 'OS according to the VMware Tools', 'VMRef', 'VM ID', 'VM UUID', 'VI SDK Server', 'VI SDK UUID'],
    'vCPU': ['VM', 'Powerstate', 'Template', 'SRM Placeholder', 'CPUs', 'Sockets', 'Cores p/s', 'Max', 'Overall', 'Level', 'Shares', 'Reservation', 'Entitlement', 'DRS Entitlement', 'Limit', 'Hot Add', 'Hot Remove', 'Numa Hotadd Exposed', 'Annotation', 'Datacenter', 'Cluster', 'Host', 'Folder', 'OS according to the configuration file', 'OS according to the VMware Tools', 'VM ID', 'VM UUID', 'VI SDK Server', 'VI SDK UUID'],
    'vCluster': ['Name', 'Config status', 'OverallStatus', 'NumHosts', 'numEffectiveHosts', 'TotalCpu', 'NumCpuCores', 'NumCpuThreads', 'Effective Cpu', 'TotalMemory', 'Effective Memory', 'Num VMotions', 'HA enabled', 'Failover Level', 'AdmissionControlEnabled', 'Host monitoring', 'HB Datastore Candidate Policy', 'Isolation Response', 'Restart Priority', 'Cluster Settings', 'Max Failures', 'Max Failure Window', 'Failure Interval', 'Min Up Time', 'VM Monitoring', 'DRS enabled', 'DRS default VM behavior', 'DRS vmotion rate', 'DPM enabled', 'DPM default behavior', 'DPM Host Power Action Rate', 'Object ID', 'VI SDK Server', 'VI SDK UUID'],
    'vDatastore': ['Name', 'Config status', 'Address', 'Accessible', 'Type', '# VMs total', '# VMs', 'Capacity MiB', 'Provisioned MiB', 'In Use MiB', 'Free MiB', 'Free %', 'SIOC enabled', 'SIOC Threshold', '# Hosts', 'Hosts', 'Cluster name', 'Cluster capacity MiB', 'Cluster free space MiB', 'Block size', 'Max Blocks', '# Extents', 'Major Version', 'Version', 'VMFS Upgradeable', 'MHA', 'URL', 'Object ID', 'VI SDK Server', 'VI SDK UUID'],
    'vDisk': ['VM', 'Powerstate', 'Template', 'SRM Placeholder', 'Disk', 'Disk Key', 'Disk UUID', 'Disk Path', 'Capacity MiB', 'Raw', 'Disk Mode', 'Sharing mode', 'Thin', 'Eagerly Scrub', 'Split', 'Write Through', 'Level', 'Shares', 'Reservation', 'Limit', 'Controller', 'Label', 'SCSI Unit #', 'Unit #', 'Shared Bus', 'Path', 'Raw LUN ID', 'Raw Comp. Mode', 'Internal Sort Column', 'Annotation', 'Datacenter', 'Cluster', 'Host', 'Folder', 'OS according to the configuration file', 'OS according to the VMware Tools', 'VM ID', 'VM UUID', 'VI SDK Server', 'VI SDK UUID'],
    'vFileInfo': ['Friendly Path Name', 'File Name', 'File Type', 'File Size in bytes', 'Path', 'Internal Sort Column', 'VI SDK Server', 'VI SDK UUID'],
    'vHBA': ['Host', 'Datacenter', 'Cluster', 'Device', 'Type', 'Status', 'Bus', 'Pci', 'Driver', 'Model', 'WWN', 'VI SDK Server', 'VI SDK UUID'],
    'vHealth': ['Name', 'Message', 'Message type', 'VI SDK Server', 'VI SDK UUID'],
    'vHost': ['Host', 'Datacenter', 'Cluster', 'Config status', 'Compliance Check State', 'in Maintenance Mode', 'in Quarantine Mode', 'vSAN Fault Domain Name', 'CPU Model', 'Speed', 'HT Available', 'HT Active', '# CPU', 'Cores per CPU', '# Cores', 'CPU usage %', '# Memory', 'Memory Tiering Type', 'Memory usage %', 'Console', '# NICs', '# HBAs', '# VMs total', '# VMs', 'VMs per Core', '# vCPUs', 'vCPUs per Core', 'vRAM', 'VM Used memory', 'VM Memory Swapped', 'VM Memory Ballooned', 'VMotion support', 'Storage VMotion support', 'Current EVC', 'Max EVC', 'Assigned License(s)', 'ATS Heartbeat', 'ATS Locking', 'Current CPU power man. policy', 'Supported CPU power man.', 'Host Power Policy', 'ESX Version', 'Boot time', 'DNS Servers', 'DHCP', 'Domain', 'Domain List', 'DNS Search Order', 'NTP Server(s)', 'NTPD running', 'Time Zone', 'Time Zone Name', 'GMT Offset', 'Vendor', 'Model', 'Serial number', 'Service tag', 'OEM specific string', 'BIOS Vendor', 'BIOS Version', 'BIOS Date', 'Certificate Issuer', 'Certificate Start Date', 'Certificate Expiry Date', 'Certificate Status', 'Certificate Subject', 'Object ID', 'UUID', 'VI SDK Server', 'VI SDK UUID'],
    'vInfo': ['VM', 'Powerstate', 'Template', 'SRM Placeholder', 'Config status', 'DNS Name', 'Connection state', 'Guest state', 'Heartbeat', 'Consolidation Needed', 'PowerOn', 'Suspended To Memory', 'Suspend time', 'Suspend Interval', 'Creation date', 'Change Version', 'CPUs', 'Overall Cpu Readiness', 'Memory', 'Active Memory', 'NICs', 'Disks', 'Total disk capacity MiB', 'Fixed Passthru HotPlug', 'min Required EVC Mode Key', 'Latency Sensitivity', 'Op Notification Timeout', 'EnableUUID', 'CBT', 'Primary IP Address', 'Network #1', 'Network #2', 'Network #3', 'Network #4', 'Network #5', 'Network #6', 'Network #7', 'Network #8', 'Num Monitors', 'Video Ram KiB', 'Resource pool', 'Folder ID', 'Folder', 'vApp', 'DAS protection', 'FT State', 'FT Role', 'FT Latency', 'FT Bandwidth', 'FT Sec. Latency', 'Vm Failover In Progress', 'Provisioned MiB', 'In Use MiB', 'Unshared MiB', 'HA Restart Priority', 'HA Isolation Response', 'HA VM Monitoring', 'Cluster rule(s)', 'Cluster rule name(s)', 'Boot Required', 'Boot delay', 'Boot retry delay', 'Boot retry enabled', 'Boot BIOS setup', 'Reboot PowerOff', 'EFI Secure boot', 'Firmware', 'HW version', 'HW upgrade status', 'HW upgrade policy', 'HW target', 'Path', 'Log directory', 'Snapshot directory', 'Suspend directory', 'Annotation', 'Datacenter', 'Cluster', 'Host', 'OS according to the configuration file', 'OS according to the VMware Tools', 'Customization Info', 'Guest Detailed Data', 'VM ID', 'SMBIOS UUID', 'VM UUID', 'VI SDK Server type', 'VI SDK API Version', 'VI SDK Server', 'VI SDK UUID'],
    'vLicense': ['Name', 'Key', 'Labels', 'Cost Unit', 'Total', 'Used', 'Expiration Date', 'Features', 'VI SDK Server', 'VI SDK UUID'],
    'vMemory': ['VM', 'Powerstate', 'Template', 'SRM Placeholder', 'Size MiB', 'Memory Reservation Locked To Max', 'Overhead', 'Max', 'Consumed', 'Consumed Overhead', 'Private', 'Shared', 'Swapped', 'Ballooned', 'Active', 'Entitlement', 'DRS Entitlement', 'Level', 'Shares', 'Reservation', 'Limit', 'Hot Add', 'Annotation', 'Datacenter', 'Cluster', 'Host', 'Folder', 'OS according to the configuration file', 'OS according to the VMware Tools', 'VM ID', 'VM UUID', 'VI SDK Server', 'VI SDK UUID'],
    'vMultiPath': ['Host', 'Cluster', 'Datacenter', 'Datastore', 'Disk', 'Display name', 'Policy', 'Oper. State', 'Path 1', 'Path 1 state', 'Path 2', 'Path 2 state', 'Path 3', 'Path 3 state', 'Path 4', 'Path 4 state', 'Path 5', 'Path 5 state', 'Path 6', 'Path 6 state', 'Path 7', 'Path 7 state', 'Path 8', 'Path 8 state', 'vStorage', 'Queue depth', 'Vendor', 'Model', 'Revision', 'Level', 'Serial #', 'UUID', 'Object ID', 'VI SDK Server', 'VI SDK UUID'],
    'vNIC': ['Host', 'Datacenter', 'Cluster', 'Network Device', 'Driver', 'Speed', 'Duplex', 'MAC', 'Switch', 'Uplink port', 'PCI', 'WakeOn', 'VI SDK Server', 'VI SDK UUID'],
    'vNetwork': ['VM', 'Powerstate', 'Template', 'SRM Placeholder', 'NIC label', 'Adapter', 'Network', 'Switch', 'Connected', 'Starts Connected', 'Mac Address', 'Type', 'IPv4 Address', 'IPv6 Address', 'Direct Path IO', 'Internal Sort Column', 'Annotation', 'Datacenter', 'Cluster', 'Host', 'Folder', 'OS according to the configuration file', 'OS according to the VMware Tools', 'VM ID', 'VM UUID', 'VI SDK Server', 'VI SDK UUID'],
    'vPartition': ['VM', 'Powerstate', 'Template', 'SRM Placeholder', 'Disk Key', 'Disk', 'Capacity MiB', 'Consumed MiB', 'Free MiB', 'Free %', 'Internal Sort Column', 'Annotation', 'Datacenter', 'Cluster', 'Host', 'Folder', 'OS according to the configuration file', 'OS according to the VMware Tools', 'VM ID', 'VM UUID', 'VI SDK Server', 'VI SDK UUID'],
    'vPort': ['Host', 'Datacenter', 'Cluster', 'Port Group', 'Switch', 'VLAN', 'Promiscuous Mode', 'Mac Changes', 'Forged Transmits', 'Traffic Shaping', 'Width', 'Peak', 'Burst', 'Policy', 'Reverse Policy', 'Notify Switch', 'Rolling Order', 'Offload', 'TSO', 'Zero Copy Xmit', 'VI SDK Server', 'VI SDK UUID'],
    'vRP': ['Resource Pool name', 'Resource Pool path', 'Status', '# VMs total', '# VMs', '# vCPUs', 'CPU limit', 'CPU overheadLimit', 'CPU reservation', 'CPU level', 'CPU shares', 'CPU expandableReservation', 'CPU maxUsage', 'CPU overallUsage', 'CPU reservationUsed', 'CPU reservationUsedForVm', 'CPU unreservedForPool', 'CPU unreservedForVm', 'Mem Configured', 'Mem limit', 'Mem overheadLimit', 'Mem reservation', 'Mem level', 'Mem shares', 'Mem expandableReservation', 'Mem maxUsage', 'Mem overallUsage', 'Mem reservationUsed', 'Mem reservationUsedForVm', 'Mem unreservedForPool', 'Mem unreservedForVm', 'QS overallCpuDemand', 'QS overallCpuUsage', 'QS staticCpuEntitlement', 'QS distributedCpuEntitlement', 'QS balloonedMemory', 'QS compressedMemory', 'QS consumedOverheadMemory', 'QS distributedMemoryEntitlement', 'QS guestMemoryUsage', 'QS hostMemoryUsage', 'QS overheadMemory', 'QS privateMemory', 'QS sharedMemory', 'QS staticMemoryEntitlement', 'QS swappedMemory', 'Object ID', 'VI SDK Server', 'VI SDK UUID'],
    'vSC_VMK': ['Host', 'Datacenter', 'Cluster', 'Port Group', 'Device', 'Mac Address', 'DHCP', 'IP Address', 'IP 6 Address', 'Subnet mask', 'Gateway', 'IP 6 Gateway', 'MTU', 'VI SDK Server', 'VI SDK UUID'],
    'vSnapshot': ['VM', 'Powerstate', 'Name', 'Description', 'Date / time', 'Filename', 'Size MiB (vmsn)', 'Size MiB (total)', 'Quiesced', 'State', 'Annotation', 'Datacenter', 'Cluster', 'Host', 'Folder', 'OS according to the configuration file', 'OS according to the VMware Tools', 'VM ID', 'VM UUID', 'VI SDK Server', 'VI SDK UUID'],
    'vSource': ['Name', 'OS type', 'API type', 'API version', 'Version', 'Patch level', 'Build', 'Fullname', 'Product name', 'Product version', 'Product line', 'Vendor', 'VI SDK Server', 'VI SDK UUID'],
    'vSwitch': ['Host', 'Datacenter', 'Cluster', 'Switch', '# Ports', 'Free Ports', 'Promiscuous Mode', 'Mac Changes', 'Forged Transmits', 'Traffic Shaping', 'Width', 'Peak', 'Burst', 'Policy', 'Reverse Policy', 'Notify Switch', 'Rolling Order', 'Offload', 'TSO', 'Zero Copy Xmit', 'MTU', 'VI SDK Server', 'VI SDK UUID'],
    'vTools': ['Upgrade', 'VM', 'Powerstate', 'Template', 'SRM Placeholder', 'VM Version', 'Tools', 'Tools Version', 'Required Version', 'Upgradeable', 'Upgrade Policy', 'Sync time', 'App status', 'Heartbeat status', 'Kernel Crash state', 'Operation Ready', 'State change support', 'Interactive Guest', 'Annotation', 'Datacenter', 'Cluster', 'Host', 'Folder', 'OS according to the configuration file', 'OS according to the VMware Tools', 'VMRef', 'VM ID', 'VM UUID', 'VI SDK Server', 'VI SDK UUID'],
    'vUSB': ['Select', 'VM', 'Powerstate', 'Template', 'SRM Placeholder', 'Device Node', 'Device Type', 'Connected', 'Family', 'Speed', 'EHCI enabled', 'Auto connect', 'Bus number', 'Unit number', 'Annotation', 'Datacenter', 'Cluster', 'Host', 'Folder', 'OS according to the configuration file', 'OS according to the VMware tools', 'VMRef', 'VM ID', 'VM UUID', 'VI SDK Server', 'VI SDK UUID'],
}

# --- AI Prompt Templates ---

VINFO_AI_PROMPT_TEMPLATE = """
You are an AI assistant helping to generate synthetic data for a VMware vSphere environment export, specifically for the 'vInfo' report (RVTools_tabvInfo.csv).

Please generate a realistic data profile for a single virtual machine.
The output should be a JSON object where keys are the column names and values are the generated data.

Consider the following column names and their typical data characteristics:

{column_details_block}

Guidelines for data generation:
- Ensure data types match typical VMware values (strings, integers, booleans, dates, IP addresses, UUIDs, etc.).
- Dates and times should be in "YYYY/MM/DD HH:MM:SS" format.
- If 'Powerstate' is 'poweredOff' or 'suspended', 'PowerOn' time might be blank or in the past. 'Suspend time' should only be present if suspended.
- 'DNS Name' should look like a valid hostname, possibly derived from the VM name.
- 'Primary IP Address' should be a valid IPv4 address. 'Network #1' through 'Network #8' can also be IPs or blank.
- Paths for 'Log directory', 'Snapshot directory', etc., should resemble VMware datastore paths (e.g., "[datastoreName] VMName/").
- Ensure 'VM UUID' and 'SMBIOS UUID' are valid UUIDs.
- 'OS according to the configuration file' and 'OS according to the VMware Tools' should be plausible guest OS strings (e.g., "windows10Server64Guest", "ubuntuLinux64Guest", "other3xLinux64Guest").
- 'VI SDK Server' is typically an IP or FQDN of vCenter/ESXi. 'VI SDK API Version' is like "6.7", "7.0".

Context (Optional - provide if available):
- Suggested VM Name: "{suggested_vm_name}"
- Associated Host: "{associated_host}"
- Associated Cluster: "{associated_cluster}"
- Associated Datacenter: "{associated_datacenter}"

Please provide the JSON output for one VM, ensuring all requested columns are present in the JSON.
"""

# --- Helper Functions for Prompt Formatting (Optional) ---
def _get_vinfo_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vInfo', [])
    descriptions = []
    for header in headers:
        descriptions.append(f"- `{header}`: (description or data type hint needed)")
    return "\\n".join(descriptions)

def _get_vhost_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vHost', [])
    descriptions = []
    for header in headers:
        descriptions.append(f"- `{header}`: (description or data type hint needed)")
    return "\\n".join(descriptions)

def _get_vdisk_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vDisk', [])
    descriptions = []
    for header in headers:
        descriptions.append(f"- `{header}`: (description or data type hint needed)")
    return "\\n".join(descriptions)

def _get_vnetwork_column_descriptions_for_prompt():
    headers = CSV_HEADERS.get('vNetwork', [])
    descriptions = []
    for header in headers:
        descriptions.append(f"- `{header}`: (description or data type hint needed)")
    return "\\n".join(descriptions)

# --- AI Prompt Templates (Continued) ---

VHOST_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware ESXi host for an RVTools vHost report.
Provide a realistic JSON data profile for an ESXi host with the following context:
- Host Name: {host_name}
- Cluster: {cluster_name}
- Datacenter: {datacenter_name}
- Approximate number of VMs running on it: {num_vms_on_host}

Use these column names, ensuring all are present in your JSON output:
{column_details_block}

Guidelines:
- Adhere to typical VMware data formats and value ranges.
- 'ESX Version' should be a realistic build string.
- '# CPU', '# Cores', '# Memory' should be appropriate for an ESXi host.
"""

VDISK_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware virtual disk for an RVTools vDisk report.
Provide a realistic JSON data profile for a single virtual disk with the following context:
- VM Name: {vm_name}
- VM Guest OS: {vm_os}
- Host Name: {host_name}
- Datastore: {datastore_name}
- This is Disk Number: {disk_index} for this VM.

Use these column names, ensuring all are present in your JSON output:
{column_details_block}

Guidelines:
- 'Capacity MiB' should be a reasonable size.
- 'Disk Mode', 'Sharing mode', 'Controller' should be valid VMware settings.
- 'Disk Path' should be consistent with the datastore and VM name.
"""

VNETWORK_AI_PROMPT_TEMPLATE = """
You are an AI assistant generating synthetic data for a VMware virtual NIC for an RVTools vNetwork report.
Provide a realistic JSON data profile for a single virtual NIC with the following context:
- VM Name: {vm_name}
- VM Guest OS: {vm_os}
- This is NIC Number: {nic_index} for this VM.

Use these column names, ensuring all are present in your JSON output:
{column_details_block}

Guidelines:
- 'Adapter' type should be a common vNIC type.
- 'Network' name should be plausible.
- 'Mac Address' must be valid.
- 'IPv4 Address' should be valid if 'Connected' is true.
"""

# --- AI Integration Functions ---
def generate_vinfo_row_ai(vm_name, environment_context):
    """
    Generates a single VM data row for vInfo using a (mocked) AI call.
    """
    column_details = _get_vinfo_column_descriptions_for_prompt()

    # Use context from environment_data if available, otherwise use placeholders
    datacenter_name = environment_context.get('datacenter_name', 'AnyDatacenter')
    cluster_name = environment_context.get('cluster_name', 'AnyCluster')
    host_name_ctx = environment_context.get('host_name', 'AnyHost') # Renamed to avoid conflict
    vcenter_ip = environment_context.get('vcenter_ip', generate_random_ip_address())
    vcenter_uuid = environment_context.get('vcenter_uuid', generate_uuid())


    prompt = VINFO_AI_PROMPT_TEMPLATE.format(
        column_details_block=column_details,
        suggested_vm_name=vm_name,
        associated_host=host_name_ctx,
        associated_cluster=cluster_name,
        associated_datacenter=datacenter_name
    )

    print("\n--- Mock AI Prompt for vInfo ---")
    # print(prompt) # Printing the full prompt can be very verbose
    print(f"Prompt prepared for VM: {vm_name} (Full prompt text suppressed for brevity)")
    print("--- End Mock AI Prompt ---\n")

    # Hardcoded sample JSON response
    mock_ai_response_json = f"""{{
        "VM": "{vm_name}",
        "Powerstate": "{choose_random_from_list(['poweredOn', 'poweredOff', 'suspended'])}",
        "Template": {json.dumps(generate_random_boolean())},
        "SRM Placeholder": {json.dumps(generate_random_boolean())},
        "Config status": "{choose_random_from_list(['green', 'yellow', 'red'])}",
        "DNS Name": "{vm_name.lower().replace('vm-','')}.{cluster_name.lower().replace('_','-')}.example.com",
        "Connection state": "{choose_random_from_list(['connected', 'disconnected', 'invalid', 'inaccessible'])}",
        "Guest state": "{choose_random_from_list(['running', 'notrunning', 'shuttingdown', 'unknown'])}",
        "Heartbeat": "{choose_random_from_list(['green', 'yellow', 'red', 'gray'])}",
        "Consolidation Needed": {json.dumps(generate_random_boolean())},
        "PowerOn": "{generate_random_datetime(start_date_str='2023/01/01 00:00:00')}",
        "Suspended To Memory": {json.dumps(generate_random_boolean())},
        "Suspend time": null,
        "Suspend Interval": 0,
        "Creation date": "{generate_random_datetime(start_date_str='2022/01/01 00:00:00', end_date_str='2022/12/31 00:00:00')}",
        "Change Version": "cv-{generate_random_string(5)}",
        "CPUs": {generate_random_integer(1, 4)},
        "Overall Cpu Readiness": {generate_random_integer(0,100)},
        "Memory": {generate_random_integer(2048, 8192)},
        "Active Memory": {generate_random_integer(1024, 4096)},
        "NICs": {generate_random_integer(1,2)},
        "Disks": {generate_random_integer(1,2)},
        "Total disk capacity MiB": {generate_random_integer(20480, 102400)},
        "min Required EVC Mode Key": "{choose_random_from_list(['', 'intel-sandybridge', 'amd-piledriver'])}",
        "Latency Sensitivity": "{choose_random_from_list(['normal', 'high'])}",
        "EnableUUID": {json.dumps(generate_random_boolean())},
        "CBT": {json.dumps(generate_random_boolean())},
        "Primary IP Address": "{generate_random_ip_address()}",
        "Network #1": "VLAN_{generate_random_integer(100,199)}",
        "Network #2": "",
        "Network #3": "",
        "Network #4": "",
        "Network #5": "",
        "Network #6": "",
        "Network #7": "",
        "Network #8": "",
        "Num Monitors": {choose_random_from_list([1,2])},
        "Video Ram KiB": {choose_random_from_list([4096, 8192, 16384])},
        "Resource pool": "/{datacenter_name}/{cluster_name}/Resources/UserGeneratedPool",
        "Folder ID": "group-v{generate_random_integer(100,999)}",
        "Folder": "/{datacenter_name}/vm/Discovered virtual machine",
        "vApp": "",
        "DAS protection": "{choose_random_from_list(['Disabled', 'Unknown'])}",
        "FT State": "Not Configured",
        "FT Role": "N/A",
        "FT Latency": "N/A",
        "FT Bandwidth": "N/A",
        "FT Sec. Latency": "N/A",
        "Vm Failover In Progress": {json.dumps(generate_random_boolean())},
        "Provisioned MiB": {generate_random_integer(20480, 102400)},
        "In Use MiB": {generate_random_integer(10240, 51200)},
        "Unshared MiB": {generate_random_integer(0, 10240)},
        "HA Restart Priority": "Medium",
        "HA Isolation Response": "None",
        "HA VM Monitoring": "VM Monitoring Disabled",
        "Cluster rule(s)": "",
        "Cluster rule name(s)": "",
        "Boot Required": {json.dumps(generate_random_boolean())},
        "Boot delay": 0,
        "Boot retry delay": 10000,
        "Boot retry enabled": {json.dumps(generate_random_boolean())},
        "Boot BIOS setup": {json.dumps(generate_random_boolean())},
        "Reboot PowerOff": {json.dumps(generate_random_boolean())},
        "EFI Secure boot": {json.dumps(generate_random_boolean())},
        "Firmware": "{choose_random_from_list(['bios', 'efi'])}",
        "HW version": "{choose_random_from_list(['vmx-15', 'vmx-17', 'vmx-19'])}",
        "HW upgrade status": "Up-to-date",
        "HW upgrade policy": "Never",
        "HW target": "",
        "Path": "[datastore-sample] {vm_name}/{vm_name}.vmx",
        "Log directory": "[datastore-sample] {vm_name}/",
        "Snapshot directory": "[datastore-sample] {vm_name}/",
        "Suspend directory": "[datastore-sample] {vm_name}/",
        "Annotation": "AI Generated VM: {generate_random_string(10)}",
        "OS according to the configuration file": "ubuntuLinux64Guest",
        "OS according to the VMware Tools": "Ubuntu Linux (64-bit)",
        "Customization Info": "",
        "Guest Detailed Data": "",
        "VM ID": "vm-{generate_random_integer(1000,9999)}",
        "SMBIOS UUID": "{generate_uuid()}",
        "VM UUID": "{generate_uuid()}",
        "VI SDK Server type": "VMware vCenter Server",
        "VI SDK API Version": "7.0.3",
        "VI SDK Server": "{vcenter_ip}",
        "VI SDK UUID": "{vcenter_uuid}"
    }}"""
    try:
        ai_data = json.loads(mock_ai_response_json)
        return ai_data
    except json.JSONDecodeError as e:
        print(f"Error decoding mock AI JSON response: {e}")
        print(f"Problematic JSON string: {mock_ai_response_json}")
        return None

def generate_vhost_row_ai(host_record_from_env, environment_data_context):
    column_details = _get_vhost_column_descriptions_for_prompt()
    num_vms_on_host = sum(1 for vm in environment_data_context['vms'] if vm.get('Host') == host_record_from_env['Host'])

    prompt = VHOST_AI_PROMPT_TEMPLATE.format(
        host_name=host_record_from_env['Host'],
        cluster_name=host_record_from_env['Cluster'],
        datacenter_name=host_record_from_env['Datacenter'],
        num_vms_on_host=num_vms_on_host,
        column_details_block=column_details
    )
    print(f"\n--- Mock AI Prompt for vHost: {host_record_from_env['Host']} ---")
    print(f"Prompt prepared (Full prompt text suppressed for brevity)")
    print("--- End Mock AI Prompt ---\n")

    mock_ai_response_json = f"""{{
        "Host": "{host_record_from_env['Host']}",
        "Cluster": "{host_record_from_env['Cluster']}",
        "Datacenter": "{host_record_from_env['Datacenter']}",
        "ESX Version": "{choose_random_from_list(['VMware ESXi 8.0.2 build-22380479', 'VMware ESXi 7.0.3 build-21424296'])}",
        "CPU Model": "{choose_random_from_list(['Intel(R) Xeon(R) Gold 6240 CPU @ 2.60GHz', 'AMD EPYC 7742 64-Core Processor'])}",
        "# CPU": {host_record_from_env.get('# CPU', 2)},
        "Cores per CPU": {host_record_from_env.get('Cores per CPU', 8)},
        "# Memory": {host_record_from_env.get('# Memory', 262144)},
        "# NICs": {generate_random_integer(2, 6)},
        "# HBAs": {generate_random_integer(1, 2)},
        "VMs total": {num_vms_on_host},
        "VMs": {num_vms_on_host},
        "Config status": "green",
        "NTPD running": {json.dumps(generate_random_boolean())},
        "VI SDK Server": "{host_record_from_env.get('VI SDK Server', '')}",
        "VI SDK UUID": "{host_record_from_env.get('VI SDK UUID', '')}"
    }}"""
    try:
        return json.loads(mock_ai_response_json)
    except json.JSONDecodeError as e:
        print(f"Error decoding mock AI JSON for vHost {host_record_from_env['Host']}: {e}")
        return None

def generate_vdisk_row_ai(vm_record_from_env, disk_index):
    column_details = _get_vdisk_column_descriptions_for_prompt()
    prompt = VDISK_AI_PROMPT_TEMPLATE.format(
        vm_name=vm_record_from_env['VM'],
        vm_os=vm_record_from_env.get('OS according to the configuration file', 'linuxGuest'),
        host_name=vm_record_from_env['Host'],
        datastore_name=vm_record_from_env.get('Datastore', 'ds-generic-01'),
        disk_index=disk_index + 1,
        column_details_block=column_details
    )
    print(f"\n--- Mock AI Prompt for vDisk on {vm_record_from_env['VM']}, Disk {disk_index+1} ---")
    print(f"Prompt prepared (Full prompt text suppressed for brevity)")
    print("--- End Mock AI Prompt ---\n")

    mock_ai_response_json = f"""{{
        "VM": "{vm_record_from_env['VM']}",
        "Disk": "Hard disk {disk_index + 1}",
        "Capacity MiB": {generate_random_integer(20480, 204800)},
        "Disk Mode": "{choose_random_from_list(['persistent', 'independent_persistent'])}",
        "Thin": {json.dumps(generate_random_boolean())},
        "Controller": "{choose_random_from_list(['SCSI controller 0', 'NVMe controller 0'])}",
        "Disk Path": "[{vm_record_from_env.get('Datastore', 'ds-generic-01')}] {vm_record_from_env['VM']}/{vm_record_from_env['VM']}_{disk_index}.vmdk",
        "Sharing mode": "nobussharing"
    }}"""
    try:
        return json.loads(mock_ai_response_json)
    except json.JSONDecodeError as e:
        print(f"Error decoding mock AI JSON for vDisk {vm_record_from_env['VM']}_{disk_index}: {e}")
        return None

def generate_vnetwork_row_ai(vm_record_from_env, nic_index):
    column_details = _get_vnetwork_column_descriptions_for_prompt()
    prompt = VNETWORK_AI_PROMPT_TEMPLATE.format(
        vm_name=vm_record_from_env['VM'],
        vm_os=vm_record_from_env.get('OS according to the configuration file', 'linuxGuest'),
        nic_index=nic_index + 1,
        column_details_block=column_details
    )
    print(f"\n--- Mock AI Prompt for vNetwork on {vm_record_from_env['VM']}, NIC {nic_index+1} ---")
    print(f"Prompt prepared (Full prompt text suppressed for brevity)")
    print("--- End Mock AI Prompt ---\n")

    is_connected = generate_random_boolean()
    ipv4_address = generate_random_ip_address() if is_connected and vm_record_from_env.get('Powerstate') == 'poweredOn' else ""

    mock_ai_response_json = f"""{{
        "VM": "{vm_record_from_env['VM']}",
        "NIC label": "Network adapter {nic_index + 1}",
        "Adapter": "{choose_random_from_list(['VMXNET3', 'E1000E'])}",
        "Network": "VLAN_{generate_random_integer(200,299)}_{vm_record_from_env.get('Datacenter','DC1').replace('DC-','')}",
        "Switch": "DSwitch_{vm_record_from_env.get('Datacenter','DC1').replace('DC-','')}",
        "Connected": {json.dumps(is_connected)},
        "Starts Connected": {json.dumps(generate_random_boolean())},
        "Mac Address": "{generate_random_mac_address()}",
        "IPv4 Address": "{ipv4_address}"
    }}"""
    try:
        return json.loads(mock_ai_response_json)
    except json.JSONDecodeError as e:
        print(f"Error decoding mock AI JSON for vNetwork {vm_record_from_env['VM']}_{nic_index}: {e}")
        return None

# --- Utility functions for random data generation ---
def generate_random_string(length=10, prefix=""):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for i in range(length))
    return prefix + random_string

def generate_random_boolean():
    return random.choice([True, False])

def generate_random_integer(min_val=0, max_val=100):
    return random.randint(min_val, max_val)

def generate_random_ip_address():
    return ".".join(str(random.randint(0, 255)) for _ in range(4))

def generate_random_mac_address():
    return ":".join("".join(random.choice("0123456789abcdef") for _ in range(2)) for _ in range(6)).upper()

def generate_random_datetime(start_date_str=None, end_date_str=None):
    date_format = "%Y/%m/%d %H:%M:%S"
    if start_date_str:
        start_date = datetime.strptime(start_date_str, date_format)
    else:
        start_date = datetime.strptime("2020/01/01 00:00:00", date_format)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, date_format)
    else:
        end_date = datetime.strptime("2024/12/31 23:59:59", date_format)

    time_difference = end_date - start_date # Calculate time_difference first
    if time_difference.total_seconds() < 0: # Then check it
        raise ValueError("Start date must be before end date.")

    random_seconds = random.randint(0, int(time_difference.total_seconds()))
    random_date = start_date + timedelta(seconds=random_seconds)
    return random_date.strftime(date_format)

def choose_random_from_list(item_list):
    if item_list:
        return random.choice(item_list)
    return None

def generate_vm_name(prefix="VM"):
    name_part = ''.join(random.choice(string.ascii_uppercase) for _ in range(random.randint(3, 5)))
    number_part = ''.join(random.choice(string.digits) for _ in range(random.randint(2, 3)))
    return f"{prefix}-{name_part}{number_part}"

def generate_uuid():
    return str(uuid.uuid4())

# --- Getter functions for ENVIRONMENT_DATA ---
def get_all_vm_names():
    return [vm.get('VM') for vm in ENVIRONMENT_DATA['vms'] if vm.get('VM')]

def get_vm_details_by_name(vm_name):
    for vm in ENVIRONMENT_DATA['vms']:
        if vm.get('VM') == vm_name:
            return vm
    return None

def get_all_host_names():
    return [host.get('Host') for host in ENVIRONMENT_DATA['hosts'] if host.get('Host')]

def get_host_details_by_name(host_name):
    for host in ENVIRONMENT_DATA['hosts']:
        if host.get('Host') == host_name:
            return host
    return None

# --- CSV Generation Functions ---
def generate_vinfo_csv(num_rows=10, use_ai=False): # Added use_ai parameter
    headers = CSV_HEADERS['vInfo']
    rows = [headers]
    ENVIRONMENT_DATA['vms'] = []
    ENVIRONMENT_DATA['hosts'] = []

    # Generate VI SDK Server details once per vCenter/ESXi instance being simulated
    # These can be passed as context to AI if needed for consistency.
    # For now, they will also be used as fallback if AI doesn't provide them.
    shared_vcenter_ip = ENVIRONMENT_DATA.get('vcenter_ip', generate_random_ip_address())
    shared_vcenter_uuid = ENVIRONMENT_DATA.get('vcenter_uuid', generate_uuid())
    ENVIRONMENT_DATA['vcenter_ip'] = shared_vcenter_ip # Store for potential use by AI
    ENVIRONMENT_DATA['vcenter_uuid'] = shared_vcenter_uuid


    for _ in range(num_rows):
        # Pre-generate essential, consistent IDs and name locally
        vm_name = generate_vm_name()
        vm_uuid_bios = generate_uuid() # This is the main VM UUID (InstanceUUID)
        smbios_uuid = generate_uuid() # SMBIOS UUID is distinct
        vm_id_moref = f"vm-{generate_random_integer(100, 9999)}" # vCenter MoRef

        vm_data_source = {} # This will hold data from AI if use_ai is True

        # AI Generation Path
        if use_ai:
            print(f"Attempting AI generation for VM: {vm_name}")
            # Create context for AI. These are suggestions or constraints for the AI.
            # The AI might generate its own if these are not strictly enforced in the prompt.
            temp_dc_choice = choose_random_from_list(['Alpha', 'Beta', 'Gamma', 'Delta'])
            temp_datacenter_name = f"DC-{temp_dc_choice}"
            temp_cluster_choice = choose_random_from_list(['Compute-A', 'Compute-B', 'Mgmt-X'])
            temp_cluster_name = f"{temp_cluster_choice}_{temp_dc_choice}"
            temp_host_number = generate_random_integer(1, 3)
            temp_host_name = f"esx{temp_host_number:02d}.{temp_cluster_name.lower().replace('_','-')}.example.local"

            context_for_ai = {
                'vcenter_ip': shared_vcenter_ip,
                'vcenter_uuid': shared_vcenter_uuid,
                'datacenter_name': temp_datacenter_name,
                'cluster_name': temp_cluster_name,
                'host_name': temp_host_name
            }
            ai_generated_data = generate_vinfo_row_ai(vm_name, context_for_ai)
            if ai_generated_data:
                vm_data_source = ai_generated_data
                print(f"Successfully used AI data for {vm_name}")
                 # Ensure AI-provided name is used if different, but log it.
                if vm_data_source.get("VM") != vm_name:
                    print(f"  Note: AI provided VM name '{vm_data_source.get('VM')}', using local '{vm_name}'.")
            else:
                print(f"AI data generation failed for {vm_name}, falling back to random.")

        # Consolidate vm_record: Start with AI data, then fill/override with local/random
        # Essential IDs are always locally generated for consistency management by this script.
        vm_record = {
            'VM': vm_name,
            'VM UUID': vm_uuid_bios,
            'SMBIOS UUID': smbios_uuid,
            'VM ID': vm_id_moref,
        }

        # Merge AI data into vm_record, local essentials take precedence if AI also provides them
        for key, value in vm_data_source.items():
            if key not in vm_record: # Only add if not one of the above pre-set essentials
                vm_record[key] = value

        # Fill remaining fields for ENVIRONMENT_DATA['vms'] consistency, using AI data if present, else random
        vm_record['Powerstate'] = vm_data_source.get('Powerstate', choose_random_from_list(['poweredOn', 'poweredOff', 'suspended']))
        vm_record['DNS Name'] = vm_data_source.get('DNS Name', f"{vm_name.lower().replace('vm-','')}.example.com")
        vm_record['Datacenter'] = vm_data_source.get('Datacenter', f"DC-{choose_random_from_list(['Alpha', 'Beta', 'Gamma', 'Delta'])}")
        vm_record['Cluster'] = vm_data_source.get('Cluster', f"{choose_random_from_list(['Compute-A', 'Compute-B', 'Mgmt-X'])}_{vm_record['Datacenter'].replace('DC-','')}")
        vm_record['Host'] = vm_data_source.get('Host', f"esx{generate_random_integer(1,3):02d}.{vm_record['Cluster'].lower().replace('_','-')}.example.local")

        vm_record['OS according to the configuration file'] = vm_data_source.get('OS according to the configuration file', choose_random_from_list(['otherGuest', 'windowsGuest', 'linuxGuest']))
        vm_record['OS according to the VMware Tools'] = vm_data_source.get('OS according to the VMware Tools', "VMware Tools running an OS")

        vm_record['CPUs'] = int(vm_data_source.get('CPUs', generate_random_integer(1, 8)))
        vm_record['CoresPerSocket'] = int(vm_data_source.get('CoresPerSocket', choose_random_from_list([1, 2, 4, 8])))
        if vm_record['CPUs'] < vm_record['CoresPerSocket']: vm_record['CoresPerSocket'] = vm_record['CPUs']

        vm_record['Memory'] = int(vm_data_source.get('Memory', generate_random_integer(1024, 32768)))
        vm_record['Datastore'] = vm_data_source.get('Datastore', f"datastore-{generate_random_integer(1,4)}-{vm_record['Cluster'].split('_')[0].lower()}")
        vm_record['Annotation'] = vm_data_source.get('Annotation', generate_random_string(20, prefix='Notes: ') if generate_random_boolean() else '')

        vm_record['VI SDK Server'] = vm_data_source.get('VI SDK Server', shared_vcenter_ip)
        vm_record['VI SDK UUID'] = vm_data_source.get('VI SDK UUID', shared_vcenter_uuid)

        ENVIRONMENT_DATA['vms'].append(vm_record)

        # Populate Host Data if new host (using finalized vm_record fields for consistency)
        host_name_final = vm_record['Host'] # Use the host name that's set for the VM
        if not get_host_details_by_name(host_name_final):
            host_cores_per_cpu = choose_random_from_list([1, 2, 4, 6, 8, 10, 12]) # For the host
            host_num_cpu_sockets = choose_random_from_list([2, 4, 8]) # For the host
            host_record = {
                'Host': host_name_final,
                'Datacenter': vm_record['Datacenter'],
                'Cluster': vm_record['Cluster'],
                'ESX Version': choose_random_from_list(['VMware ESXi 8.0.2 build-21997540', 'VMware ESXi 7.0.3 build-20328353', 'VMware ESXi 6.7.0 build-17499825']),
                '# CPU': host_num_cpu_sockets,
                'Cores per CPU': host_cores_per_cpu,
                '# Memory': choose_random_from_list([65536, 131072, 262144, 524288, 1048576]), # Larger memory for hosts
                'Config status': 'green',
                'Boot time': generate_random_datetime("2023/01/01 00:00:00", "2023/12/31 23:59:59"),
                'NTPD running': generate_random_boolean(),
                'VI SDK Server': vm_record['VI SDK Server'], # Host managed by same vCenter
                'VI SDK UUID': vm_record['VI SDK UUID']
            }
            ENVIRONMENT_DATA['hosts'].append(host_record)

        current_row = []
        for header in headers:
            # Build the CSV row using the finalized vm_record, ensuring all vInfo headers are covered
            value = vm_record.get(header)
            if value is None:
                # Fallback to random generation for any fields not covered by AI or vm_record essentials
                if header == 'Template' or header == 'SRM Placeholder': value = generate_random_boolean()
                elif header == 'Config status': value = choose_random_from_list(['green', 'yellow', 'red']) # VM config status
                elif header == 'Connection state': value = choose_random_from_list(['connected', 'disconnected', 'invalid', 'inaccessible'])
                elif header == 'Guest state': value = choose_random_from_list(['running', 'shuttingdown', 'notrunning', 'unknown'])
                elif header == 'Heartbeat': value = choose_random_from_list(['gray', 'green', 'yellow', 'red'])
                elif header == 'Consolidation Needed': value = generate_random_boolean()
                elif header == 'PowerOn': value = generate_random_datetime() if vm_record['Powerstate'] == 'poweredOn' else ''
                elif header == 'Suspended To Memory': value = True if vm_record['Powerstate'] == 'suspended' else False
                elif header == 'Suspend time' : value = generate_random_datetime() if vm_record['Powerstate'] == 'suspended' else ''
                elif header == 'Creation date': value = generate_random_datetime(end_date_str="2023/01/01 00:00:00")
                elif header == 'Suspend Interval': value = generate_random_integer(0,3600) if vm_record['Powerstate'] == 'suspended' else ''
                elif header == 'Change Version': value = generate_random_string(10)
                elif header == 'Active Memory': value = generate_random_integer(0, vm_record['Memory'])
                elif header == 'Overall Cpu Readiness': value = generate_random_integer(0, 2000)
                elif header == 'NICs' or header == 'Disks': value = generate_random_integer(1, 4)
                elif header == 'Total disk capacity MiB' or header == 'Provisioned MiB' or \
                    header == 'In Use MiB' or header == 'Unshared MiB': value = generate_random_integer(10000, 500000)
                elif header == 'Fixed Passthru HotPlug': value = generate_random_boolean()
                elif header == 'min Required EVC Mode Key': value = generate_random_string(15) if generate_random_boolean() else ''
                elif header == 'Latency Sensitivity': value = choose_random_from_list(['normal', 'high'])
                elif header == 'Op Notification Timeout': value = generate_random_integer(0, 600)
                elif header == 'EnableUUID' or header == 'CBT': value = generate_random_boolean()
                elif header == 'Primary IP Address': value = generate_random_ip_address() if vm_record['Powerstate'] == 'poweredOn' else ''
                elif header.startswith('Network #'):
                    if header == 'Network #1': value = generate_random_ip_address() if vm_record['Powerstate'] == 'poweredOn' else ''
                    else: value = ''
                elif header == 'Num Monitors': value = choose_random_from_list([1, 2, 4])
                elif header == 'Video Ram KiB': value = choose_random_from_list([4096, 8192, 16384])
                elif header == 'Resource pool': value = f"{vm_record['Cluster']}/Resources"
                elif header == 'Folder ID': value = generate_random_string(8, prefix='group-v')
                elif header == 'Folder': value = f"/{vm_record['Datacenter']}/vm/{generate_random_string(6, prefix='AppGroup-')}"
                elif header == 'vApp': value = generate_random_string(10, prefix='vApp-') if generate_random_boolean() else ''
                elif header == 'DAS protection': value = choose_random_from_list(['Unknown', 'Disabled', 'Enabled'])
                elif header == 'FT State' or header == 'FT Role' or header == 'FT Latency' or header == 'FT Bandwidth' or header == 'FT Sec. Latency': value = 'N/A'
                elif header == 'Vm Failover In Progress': value = generate_random_boolean()
                elif header == 'HA Restart Priority': value = choose_random_from_list(['Medium', 'High', 'Low', 'Disabled', 'Cluster default'])
                elif header == 'HA Isolation Response': value = choose_random_from_list(['None', 'PowerOff', 'Shutdown', 'Cluster default'])
                elif header == 'HA VM Monitoring': value = choose_random_from_list(['VM Monitoring Disabled', 'VM Monitoring Enabled', 'VM and Application Monitoring', 'Cluster default'])
                elif header == 'Cluster rule(s)' or header == 'Cluster rule name(s)': value = generate_random_string(10, prefix='Rule-') if generate_random_boolean() else ''
                elif header == 'Boot Required' or header == 'Boot retry enabled' or \
                    header == 'Boot BIOS setup' or header == 'Reboot PowerOff' or header == 'EFI Secure boot': value = generate_random_boolean()
                elif header == 'Boot delay' or header == 'Boot retry delay': value = generate_random_integer(0, 10000)
                elif header == 'Firmware': value = choose_random_from_list(['bios', 'efi'])
                elif header == 'HW version': value = choose_random_from_list(['vmx-07', 'vmx-08', 'vmx-09', 'vmx-10', 'vmx-11', 'vmx-13', 'vmx-14', 'vmx-15', 'vmx-17', 'vmx-18', 'vmx-19', 'vmx-20'])
                elif header == 'HW upgrade status': value = choose_random_from_list(['Up-to-date', 'Unsupported', 'Upgrade Recommended', 'None'])
                elif header == 'HW upgrade policy': value = choose_random_from_list(['Never', 'On Soft PowerOff', 'Always'])
                elif header == 'HW target': value = choose_random_from_list(['None', 'currentHost', 'specificHost'])
                elif header == 'Path' or header == 'Log directory' or header == 'Snapshot directory' or header == 'Suspend directory':
                    value = f"/vmfs/volumes/{vm_record['Datastore']}/{vm_record['VM']}/{vm_record['VM']}{'.vmx' if header == 'Path' else ''}"
                elif header == 'Customization Info': value = generate_random_string(10) if generate_random_boolean() else ''
                elif header == 'Guest Detailed Data': value = generate_random_string(15, prefix='detail-') if generate_random_boolean() else ''
                elif header == 'VI SDK Server type': value = choose_random_from_list(['VMware vCenter Server', 'ESXi'])
                elif header == 'VI SDK API Version': value = choose_random_from_list(['6.5', '6.7', '7.0', '8.0'])
                else: value = '' # Default for unhandled vInfo specific columns after checking vm_record
            current_row.append(str(value))
        rows.append(current_row)

    output_path = "RV_TOOL_ZIP_OUTPUT/RVT_CSV/RVTools_tabvInfo.csv"
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    print(f"{output_path} generated successfully with {num_rows} data rows. {len(ENVIRONMENT_DATA['vms'])} VMs and {len(ENVIRONMENT_DATA['hosts'])} unique hosts recorded.")

def generate_vhost_csv(use_ai=False): # Added use_ai
    headers = CSV_HEADERS['vHost']
    rows = [headers]
    for host_env_rec in ENVIRONMENT_DATA['hosts']: # Iterate through hosts populated by vInfo
        host_data_source = {}
        if use_ai:
            print(f"Attempting AI generation for host: {host_env_rec['Host']}")
            ai_generated_data = generate_vhost_row_ai(host_env_rec, ENVIRONMENT_DATA)
            if ai_generated_data:
                host_data_source = ai_generated_data
                print(f"Successfully used AI data for host {host_env_rec['Host']}")
            else:
                print(f"AI data generation failed for host {host_env_rec['Host']}, falling back to random.")

        current_row = []
        num_vms_on_host = sum(1 for vm in ENVIRONMENT_DATA['vms'] if vm.get('Host') == host_env_rec['Host'])

        for header in headers:
            # Priority: 1. host_env_rec (core IDs), 2. AI data, 3. Calculated, 4. Random/Default
            if header in host_env_rec: # Core fields like Host, Datacenter, Cluster, VI SDK details
                value = host_env_rec[header]
            elif header in host_data_source: # AI provided data
                value = host_data_source[header]
            elif header == '# Cores': # Calculated
                value = host_env_rec.get('# CPU', 2) * host_env_rec.get('Cores per CPU', 4) # Use from ENV_DATA if available
            elif header == '# VMs total' or header == '# VMs': value = num_vms_on_host
            # Fallback to random generation for other fields
            elif header == 'CPU Model': value = choose_random_from_list(["Intel(R) Xeon(R) CPU E5-2690 v4 @ 2.60GHz", "AMD EPYC 7R32 Processor", "Intel(R) Xeon(R) Gold 6248R CPU @ 3.00GHz"])
            elif header == 'Speed': value = generate_random_integer(2000, 4000)
            elif header == 'HT Available' or header == 'HT Active' or header == 'in Maintenance Mode' or \
                 header == 'VMotion support' or header == 'Storage VMotion support' or \
                 header == 'ATS Heartbeat' or header == 'ATS Locking' or header == 'DHCP': value = generate_random_boolean()
            elif header == 'in Quarantine Mode': value = False
            elif header == 'vSAN Fault Domain Name': value = ""
            elif header == 'CPU usage %' or header == 'Memory usage %': value = generate_random_integer(10, 90)
            elif header == 'Memory Tiering Type': value = ""
            elif header == 'Console': value = generate_random_ip_address()
            elif header == '# NICs' or header == '# HBAs': value = generate_random_integer(2, 8)
            # elif header == '# VMs total' or header == '# VMs': value = num_vms_on_host # This is already handled by a line above
            elif header == '# vCPUs': value = num_vms_on_host * generate_random_integer(1,4) # Simplification
            elif header == 'VMs per Core' or header == 'vCPUs per Core':
                cores_total = host_env_rec.get('# CPU', 2) * host_env_rec.get('Cores per CPU', 4)
                if cores_total > 0:
                    if header == 'VMs per Core': value = round(num_vms_on_host / cores_total, 2)
                    else: value = round((num_vms_on_host * generate_random_integer(1,4)) / cores_total, 2) # Assuming avg 1-4 vCPUs per VM for this calculation
                else: value = 0
            elif header == 'vRAM': value = num_vms_on_host * generate_random_integer(1024, 8192)
            elif header == 'VM Used memory' or header == 'VM Memory Swapped' or header == 'VM Memory Ballooned':
                host_mem = host_env_rec.get('# Memory', 262144)
                value = generate_random_integer(0, host_mem // (num_vms_on_host + 1) if num_vms_on_host > 0 else host_mem // 10)
            elif header == 'Current EVC' or header == 'Max EVC': value = choose_random_from_list(["intel-sandybridge", "intel-ivybridge", "amd-piledriver", ""])
            elif header == 'Assigned License(s)': value = '00000-00000-00000-00000-00000' # Standard eval/placeholder
            elif header == 'Current CPU power man. policy' or header == 'Supported CPU power man.' or header == 'Host Power Policy': value = choose_random_from_list(['Balanced', 'High performance', 'Low power', 'Static'])
            elif header == 'DNS Servers' or header == 'NTP Server(s)': value = f"{generate_random_ip_address()},{generate_random_ip_address()}" if generate_random_boolean() else generate_random_ip_address()
            elif header == 'Domain' or header == 'Domain List' or header == 'DNS Search Order': value = "example.local" if generate_random_boolean() else "corp.example.com"
            elif header == 'Time Zone' or header == 'Time Zone Name': value = "UTC"
            elif header == 'GMT Offset': value = 0
            elif header == 'Vendor': value = choose_random_from_list(["Dell Inc.", "HP", "Supermicro", "VMware, Inc."])
            elif header == 'Model': value = generate_random_string(10, prefix="Serv") if host_env_rec.get('Vendor') != "VMware, Inc." else "VMware Virtual Platform"
            elif header == 'Serial number' or header == 'Service tag': value = generate_random_string(10).upper() if host_env_rec.get('Vendor') != "VMware, Inc." else ""
            elif header == 'OEM specific string': value = ""
            elif header == 'BIOS Vendor': value = host_env_rec.get('Vendor', "Phoenix Technologies LTD")
            elif header == 'BIOS Version': value = generate_random_string(5)
            elif header == 'BIOS Date': value = generate_random_datetime("2022/01/01 00:00:00", "2023/01/01 00:00:00")
            elif header == 'Certificate Issuer' or header == 'Certificate Subject': value = f"CN={host_env_rec['Host']}, OU=Example Org, O=Example Inc."
            elif header == 'Certificate Start Date': value = generate_random_datetime("2023/01/01 00:00:00", "2023/06/01 00:00:00")
            elif header == 'Certificate Expiry Date': value = generate_random_datetime("2025/01/01 00:00:00", "2026/01/01 00:00:00")
            elif header == 'Certificate Status': value = "OK"
            elif header == 'Object ID': value = f"host-{generate_random_integer(10,500)}"
            elif header == 'UUID': value = generate_uuid()
            else: value = '' # Default for unhandled vHost specific columns
            current_row.append(str(value))
        rows.append(current_row)
    output_path = "RV_TOOL_ZIP_OUTPUT/RVT_CSV/RVTools_tabvHost.csv"
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    print(f"{output_path} generated successfully with {len(ENVIRONMENT_DATA['hosts'])} hosts.")

def generate_vcpu_csv():
    headers = CSV_HEADERS['vCPU']
    rows = [headers]
    for vm_rec in ENVIRONMENT_DATA['vms']:
        current_row = []
        sockets = max(1, vm_rec.get('CPUs', 1) // vm_rec.get('CoresPerSocket', 1))
        for header in headers:
            value = vm_rec.get(header)
            if value is None:
                if header == 'CPUs': value = vm_rec.get('CPUs', 1)
                elif header == 'Sockets': value = sockets
                elif header == 'Cores p/s': value = vm_rec.get('CoresPerSocket', 1)
                elif header == 'Max' or header == 'Overall' or header == 'Reservation' or \
                     header == 'Entitlement' or header == 'DRS Entitlement' or header == 'Limit':
                    value = generate_random_integer(0, 2000)
                elif header == 'Level': value = choose_random_from_list(['normal', 'high', 'low', 'custom'])
                elif header == 'Shares': value = generate_random_integer(500, 4000) * vm_rec.get('CPUs',1)
                elif header == 'Hot Add' or header == 'Hot Remove' or header == 'Numa Hotadd Exposed':
                    value = generate_random_boolean()
                elif header == 'Template' or header == 'SRM Placeholder': value = generate_random_boolean()
                else: value = ''
            current_row.append(str(value))
        rows.append(current_row)
    output_path = "RV_TOOL_ZIP_OUTPUT/RVT_CSV/RVTools_tabvCPU.csv"
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    print(f"{output_path} generated successfully with {len(ENVIRONMENT_DATA['vms'])} VMs.")

def generate_vmemory_csv():
    headers = CSV_HEADERS['vMemory']
    rows = [headers]
    for vm_rec in ENVIRONMENT_DATA['vms']:
        current_row = []
        vm_memory_mb = vm_rec.get('Memory', 1024)
        for header in headers:
            value = vm_rec.get(header)
            if value is None:
                if header == 'Size MiB': value = vm_memory_mb
                elif header == 'Memory Reservation Locked To Max': value = generate_random_boolean()
                elif header == 'Overhead' or header == 'Consumed Overhead': value = generate_random_integer(32, 512)
                elif header == 'Max' or header == 'Consumed' or header == 'Private' or header == 'Shared' or \
                     header == 'Swapped' or header == 'Ballooned' or header == 'Active' or \
                     header == 'Entitlement' or header == 'DRS Entitlement' or \
                     header == 'Reservation' or header == 'Limit':
                    value = generate_random_integer(0, vm_memory_mb)
                elif header == 'Level': value = choose_random_from_list(['normal', 'high', 'low', 'custom'])
                elif header == 'Shares': value = generate_random_integer(10, 100) * vm_memory_mb
                elif header == 'Hot Add': value = generate_random_boolean()
                elif header == 'Template' or header == 'SRM Placeholder': value = generate_random_boolean()
                else: value = ''
            current_row.append(str(value))
        rows.append(current_row)
    output_path = "RV_TOOL_ZIP_OUTPUT/RVT_CSV/RVTools_tabvMemory.csv"
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    print(f"{output_path} generated successfully with {len(ENVIRONMENT_DATA['vms'])} VMs.")

def generate_vdisk_csv(use_ai=False): # Added use_ai
    headers = CSV_HEADERS['vDisk']
    rows = [headers]
    for vm_env_rec in ENVIRONMENT_DATA['vms']: # Changed to vm_env_rec to avoid conflict
        num_disks = generate_random_integer(1, 3)
        for i in range(num_disks):
            disk_data_source = {}
            if use_ai:
                print(f"Attempting AI generation for vDisk {i+1} on VM: {vm_env_rec['VM']}")
                ai_generated_data = generate_vdisk_row_ai(vm_env_rec, i)
                if ai_generated_data:
                    disk_data_source = ai_generated_data
                    print(f"Successfully used AI data for vDisk {i+1} on {vm_env_rec['VM']}")
                else:
                    print(f"AI data generation failed for vDisk {i+1} on {vm_env_rec['VM']}, falling back.")

            current_row = []
            # Base disk attributes from vm_env_rec (VM context)
            base_attributes = {h: vm_env_rec.get(h, '') for h in ['VM', 'Powerstate', 'Template', 'SRM Placeholder', 'Annotation', 'Datacenter', 'Cluster', 'Host', 'Folder', 'OS according to the configuration file', 'OS according to the VMware Tools', 'VM ID', 'VM UUID', 'VI SDK Server', 'VI SDK UUID']}

            # Disk specific attributes (AI or random)
            base_attributes['Disk'] = disk_data_source.get('Disk', f"Hard disk {i+1}")
            base_attributes['Disk Key'] = disk_data_source.get('Disk Key', 2000 + i)
            base_attributes['Disk UUID'] = disk_data_source.get('Disk UUID', generate_uuid())
            base_attributes['Capacity MiB'] = disk_data_source.get('Capacity MiB', generate_random_integer(10240, 256000))
            base_attributes['Disk Mode'] = disk_data_source.get('Disk Mode', choose_random_from_list(['persistent', 'independent_persistent']))
            base_attributes['Thin'] = disk_data_source.get('Thin', generate_random_boolean())
            base_attributes['Controller'] = disk_data_source.get('Controller', choose_random_from_list(['SCSI controller 0', 'SATA controller 0']))
            base_attributes['Disk Path'] = disk_data_source.get('Disk Path', f"[{vm_env_rec.get('Datastore', 'ds-generic-01')}] {vm_env_rec['VM']}/{vm_env_rec['VM']}_{i}.vmdk")
            base_attributes['Sharing mode'] = disk_data_source.get('Sharing mode', 'nobussharing')

            # Fill current_row based on headers
            for header in headers:
                value = base_attributes.get(header)
                if value is None: # Fields not in base_attributes or AI data
                    if header == 'Raw' or header == 'Eagerly Scrub' or \
                       header == 'Split' or header == 'Write Through': value = generate_random_boolean()
                    elif header == 'Level' or header == 'Shares' or header == 'Reservation' or header == 'Limit': value = generate_random_integer(0,1000)
                    elif header == 'Label': value = f"DiskLabel_{i}"
                    elif header == 'SCSI Unit #' or header == 'Unit #': value = i
                    elif header == 'Shared Bus': value = "No Sharing" # Default
                    elif header == 'Path': value = base_attributes['Disk Path'] # Redundant but ensures it's there
                    elif header == 'Raw LUN ID' or header == 'Raw Comp. Mode' or header == 'Internal Sort Column': value = ''
                    else: value = ''
                current_row.append(str(value))
            rows.append(current_row)
    output_path = "RV_TOOL_ZIP_OUTPUT/RVT_CSV/RVTools_tabvDisk.csv"
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    print(f"{output_path} generated successfully with data for {len(ENVIRONMENT_DATA['vms'])} VMs.")

def generate_vnetwork_csv(use_ai=False): # Added use_ai
    headers = CSV_HEADERS['vNetwork']
    rows = [headers]
    for vm_env_rec in ENVIRONMENT_DATA['vms']: # Changed to vm_env_rec
        num_nics = generate_random_integer(1, 2)
        for i in range(num_nics):
            nic_data_source = {}
            if use_ai:
                print(f"Attempting AI generation for vNetwork NIC {i+1} on VM: {vm_env_rec['VM']}")
                ai_generated_data = generate_vnetwork_row_ai(vm_env_rec, i)
                if ai_generated_data:
                    nic_data_source = ai_generated_data
                    print(f"Successfully used AI data for vNetwork NIC {i+1} on {vm_env_rec['VM']}")
                else:
                    print(f"AI data generation failed for vNetwork NIC {i+1} on {vm_env_rec['VM']}, falling back.")

            current_row_dict = {}
             # Populate from vm_env_rec first (for VM context fields)
            for header in headers:
                if header in vm_env_rec:
                    current_row_dict[header] = vm_env_rec[header]

            # Override with AI data or generate new if not present
            current_row_dict['NIC label'] = nic_data_source.get('NIC label', f"Network adapter {i+1}")
            current_row_dict['Adapter'] = nic_data_source.get('Adapter', choose_random_from_list(['VMXNET3', 'E1000E']))
            current_row_dict['Network'] = nic_data_source.get('Network', f"VLAN-{generate_random_integer(10,20)}0_{vm_env_rec.get('Datacenter','DefaultDC').replace('DC-','')}")
            current_row_dict['Switch'] = nic_data_source.get('Switch', f"DSwitch-{vm_env_rec.get('Datacenter','DefaultDC').replace('DC-','')}")
            current_row_dict['Connected'] = nic_data_source.get('Connected', generate_random_boolean())
            current_row_dict['Starts Connected'] = nic_data_source.get('Starts Connected', generate_random_boolean())
            current_row_dict['Mac Address'] = nic_data_source.get('Mac Address', generate_random_mac_address())
            current_row_dict['Type'] = nic_data_source.get('Type', 'ethernet')
            current_row_dict['IPv4 Address'] = nic_data_source.get('IPv4 Address', generate_random_ip_address() if current_row_dict.get('Connected') and vm_env_rec.get('Powerstate') == 'poweredOn' else '')
            current_row_dict['IPv6 Address'] = nic_data_source.get('IPv6 Address', '')
            current_row_dict['Direct Path IO'] = nic_data_source.get('Direct Path IO', generate_random_boolean())
            current_row_dict['Internal Sort Column'] = nic_data_source.get('Internal Sort Column', f"{vm_env_rec['VM']}_{i}")

            current_row_list = [str(current_row_dict.get(h, '')) for h in headers]
            rows.append(current_row_list)
    output_path = "RV_TOOL_ZIP_OUTPUT/RVT_CSV/RVTools_tabvNetwork.csv"
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)
    print(f"{output_path} generated successfully with data for {len(ENVIRONMENT_DATA['vms'])} VMs.")

def create_zip_archive(zip_filename="RVTools_Export.zip"):
    csv_dir = "RV_TOOL_ZIP_OUTPUT/RVT_CSV/"
    # Place the zip file in RV_TOOL_ZIP_OUTPUT, not inside RVT_CSV
    zip_path = os.path.join("RV_TOOL_ZIP_OUTPUT", zip_filename)

    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))

    if not csv_files:
        print(f"No CSV files found in {csv_dir} to zip.")
        return

    # Ensure the base output directory exists
    os.makedirs("RV_TOOL_ZIP_OUTPUT", exist_ok=True)

    zipped_files_list = []
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for csv_file_path in csv_files:
            base_filename = os.path.basename(csv_file_path)
            zf.write(csv_file_path, arcname=base_filename)
            zipped_files_list.append(base_filename)

    if zipped_files_list:
        print(f"\nSuccessfully created ZIP archive: {zip_path}")
        print("Included files:")
        for f_name in zipped_files_list:
            print(f"  - {f_name}")
    else:
        # This case should ideally not be reached if csv_files was not empty,
        # but as a fallback.
        print(f"No files were added to the zip archive: {zip_path}")


if __name__ == "__main__":
    generate_vinfo_csv(num_rows=5, use_ai=True)
    generate_vhost_csv(use_ai=True)
    generate_vcpu_csv() # No AI for vCPU in this step
    generate_vmemory_csv() # No AI for vMemory in this step
    generate_vdisk_csv(use_ai=True)
    generate_vnetwork_csv(use_ai=True)
    create_zip_archive()

    # Example usage of getter functions:
    # print("\nVMs created:", len(ENVIRONMENT_DATA['vms']))
    # print("\nHosts created:", ENVIRONMENT_DATA['hosts'])

    # print("\nAll VM Names:", get_all_vm_names())
    # if ENVIRONMENT_DATA['vms'] and len(ENVIRONMENT_DATA['vms']) > 0:
    #     sample_vm_name = ENVIRONMENT_DATA['vms'][0]['VM']
    #     print(f"\nDetails for {sample_vm_name}:", get_vm_details_by_name(sample_vm_name))
    # print("\nAll Host Names:", get_all_host_names())
    # if ENVIRONMENT_DATA['hosts'] and len(ENVIRONMENT_DATA['hosts']) > 0:
    #     sample_host_name = ENVIRONMENT_DATA['hosts'][0]['Host']
    #     print(f"\nDetails for {sample_host_name}:", get_host_details_by_name(sample_host_name))
