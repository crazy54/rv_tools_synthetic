import pytest
import os
import csv
from unittest import mock # For @patch decorator and MagicMock

# Add project root to sys.path
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from rvtools_data_generator import (
    generate_vinfo_csv,
    generate_vhost_csv,
    generate_vdisk_csv,
    ENVIRONMENT_DATA,
    CSV_HEADERS,
    get_complexity_parameters,
    generate_ip_address, # Corrected name
    generate_uuid # For default vcenter_uuid in reset
)

def reset_environment_data_for_test():
    ENVIRONMENT_DATA["vms"].clear()
    ENVIRONMENT_DATA["hosts"].clear()
    ENVIRONMENT_DATA["clusters"].clear()
    # ENVIRONMENT_DATA["vm_disks"].clear() # vm_disks is not a standard key, vDisk populates its own list
    ENVIRONMENT_DATA["datastores"].clear()
    ENVIRONMENT_DATA["networks"].clear()
    ENVIRONMENT_DATA["resource_pools"].clear()
    ENVIRONMENT_DATA["datacenters"].clear()
    ENVIRONMENT_DATA["folders"].clear()
    ENVIRONMENT_DATA["dvSwitches"].clear()
    ENVIRONMENT_DATA["vswitches"].clear()
    ENVIRONMENT_DATA["sdk_server_map"].clear()

    # Reset config to a basic state
    ENVIRONMENT_DATA["config"] = {
        "output_dir": "test_output", # Use a test-specific output if needed by functions
        "ai_model": "gpt-4o-mini" # Default, if any function tries to access it
    }


@pytest.fixture(autouse=True)
def setup_and_teardown_env_data(tmp_path): # Add tmp_path for test-specific output
    # Configure a test-specific output directory that will be cleaned up
    test_output_dir = tmp_path / "test_rvtools_output"
    test_output_dir.mkdir()
    ENVIRONMENT_DATA["config"]["output_dir"] = str(test_output_dir)

    reset_environment_data_for_test()
    yield
    reset_environment_data_for_test()

@mock.patch('rvtools_data_generator.write_csv') # Patch write_csv directly
@mock.patch('rvtools_data_generator._get_ai_data_for_entity')
def test_generate_vinfo_csv_random_path(mock_get_ai, mock_write_csv, tmp_path):
    # _get_ai_data_for_entity is called by generate_vinfo_row_ai
    # For random path, it uses _create_vinfo_mock_data if AI is "mock" or if real AI fails
    # If use_ai is False, _get_ai_data_for_entity is not called directly by generate_vinfo_csv,
    # but by generate_vinfo_row_ai which might be called.
    # Let's ensure the mock function inside generate_vinfo_row_ai is used.
    # The mock_get_ai here will mock the dispatcher.

    # We need to ensure that generate_vinfo_row_ai, when it calls _get_ai_data_for_entity,
    # gets a predictable mock response.
    def mock_vinfo_data_creator(context): # This is the entity_specific_mock_func
        vm_name = context.get("vm_name_hint", "TestVM")
        return {
            "VM Name": vm_name, "Powerstate": "PoweredOn",
            "OS according to VMWare": "otherGuest", "DNS Name": f"{vm_name}.test.local",
            "IP Address": "192.168.1.100", "vCPU": 2, "Memory MB": 2048,
            "Provisioned MB": 40960, "In Use MB": 20480, "Annotation": "Random Test VM"
        }
    mock_get_ai.side_effect = lambda prompt_template, context, relevant_headers_key, entity_name_for_log, **kwargs: \
        mock_vinfo_data_creator(context)


    num_test_vms = 2
    # Ensure complexity_params has all keys expected by generate_vinfo_csv's random path
    test_complexity = get_complexity_parameters("medium", num_test_vms)
    ENVIRONMENT_DATA["config"].update(test_complexity) # Ensure config has complexity

    generate_vinfo_csv(
        num_vms=num_test_vms,
        sdk_server_name="test-vc.local",
        base_sdk_uuid=generate_uuid(),
        complexity_params=test_complexity,
        use_ai_cli_flag=False, # Testing pure random path, AI dispatcher shouldn't be hit for decision
        ai_provider_cli_arg="mock", # This will make _get_ai_data_for_entity use the mock
        ollama_model_name="llama3", # Add all params expected by the function
        scenario_config=None
    )

    assert len(ENVIRONMENT_DATA["vms"]) == num_test_vms
    assert len(ENVIRONMENT_DATA["hosts"]) >= 1 # vInfo random path creates at least one host
    assert len(ENVIRONMENT_DATA["clusters"]) >= 1

    # Check that write_csv was called correctly
    mock_write_csv.assert_called_once()
    args, _ = mock_write_csv.call_args
    assert args[1] == "vInfo" # filename_prefix
    assert len(args[0]) == num_test_vms # Number of data rows


@mock.patch('rvtools_data_generator.write_csv')
@mock.patch('rvtools_data_generator._get_ai_data_for_entity')
def test_generate_vinfo_csv_with_simple_scenario(mock_get_ai, mock_write_csv, tmp_path):

    def side_effect_ai_vinfo(prompt_template, context, *args, **kwargs):
        # Simulate AI providing some data, merging with context from scenario
        vm_name = context.get("vm_name_hint", "ScenarioVM")
        return {
            "VM Name": vm_name,
            "Powerstate": "PoweredOn",
            "OS according to VMWare": context.get("profile_os_hints", ["otherGuest"])[0],
            "DNS Name": f"{vm_name}.scenario.local",
            "IP Address": generate_ip_address(),
            "vCPU": context.get("profile_vcpu", 1),
            "Memory MB": context.get("profile_memory_mb", 512),
            "Provisioned MB": 20480,
            "In Use MB": 10240,
            "Annotation": "AI Test VM for Scenario"
        }
    mock_get_ai.side_effect = side_effect_ai_vinfo

    test_scenario = {
        'global_settings': {'datacenter_prefix': "TestDC"},
        'datacenters': [{
            'name': "MyDC1",
            'cluster_profiles': {
                "GenPurp": {'host_hardware_profile': "StdHost", 'num_hosts': 1}
            },
            'deployment_plan': [{
                'profile_name': "tinyvm",
                'count': 2,
                'target_cluster_profile': "GenPurp"
            }]
        }],
        'host_hardware_profiles': { "StdHost": {'num_physical_nics': 2, 'nic_speed_gbps': 10, 'local_storage_gb': 100}},
        'vm_profiles': { "tinyvm": {'name_prefix':"scenvm", 'os_options': ["otherGuest"], 'vcpu': 1, 'memory_mb': 512, 'disks': [{'size_gb': 10}]}}
    }
    # Base num_vms for complexity doesn't matter much if scenario dictates counts
    test_complexity = get_complexity_parameters("medium", 1)
    ENVIRONMENT_DATA["config"].update(test_complexity)


    generate_vinfo_csv(
        num_vms=1, # This will be overridden by scenario's 'count'
        sdk_server_name="scenario-vc.local",
        base_sdk_uuid=generate_uuid(),
        complexity_params=test_complexity,
        use_ai_cli_flag=True, # Enable AI path
        ai_provider_cli_arg="openai", # Simulate OpenAI provider
        ollama_model_name="llama3",
        scenario_config=test_scenario
    )

    assert len(ENVIRONMENT_DATA["vms"]) == 2 # From scenario config's deployment_plan count
    assert len(ENVIRONMENT_DATA["hosts"]) == 1
    assert len(ENVIRONMENT_DATA["clusters"]) == 1

    assert mock_get_ai.call_count == 2 # AI called for each VM in scenario
    mock_write_csv.assert_called_once()
    args, _ = mock_write_csv.call_args
    assert args[1] == "vInfo"
    assert len(args[0]) == 2


@mock.patch('rvtools_data_generator.write_csv')
@mock.patch('rvtools_data_generator._get_ai_data_for_entity')
def test_generate_vhost_csv_basic(mock_get_ai, mock_write_csv, tmp_path):

    def side_effect_ai_vhost(prompt_template, context, *args, **kwargs):
        host_name = context.get("host_name_hint", "TestHost")
        return {
            "Name": host_name, "Cluster": "Clus1", "Datacenter": "DC1",
            "CPUMhz": 32000, "CPU Model": "AI CPU", "CPU Sockets": 2, "CPU Cores": 16,
            "MEM Size": 131072, "VMs": 5, "Vendor": "AI Host Vendor", "Model": "AI Model X",
            "ESXi Version": "VMware ESXi 8.0.1 AI-Build"
        }
    mock_get_ai.side_effect = side_effect_ai_vhost

    ENVIRONMENT_DATA["hosts"] = [
        {'name': 'host1', 'datacenter': 'DC1', 'cluster': 'Clus1', 'sdk_server': 'vc.test', 'sdk_uuid': 'vc-uuid1', 'uuid': 'h-uuid1'},
        {'name': 'host2', 'datacenter': 'DC1', 'cluster': 'Clus1', 'sdk_server': 'vc.test', 'sdk_uuid': 'vc-uuid1', 'uuid': 'h-uuid2'}
    ]
    # Make sure VMs exist for VM count on host
    ENVIRONMENT_DATA["vms"] = [
        {'host': 'host1', 'name': 'vm1'}, {'host': 'host1', 'name': 'vm2'}, {'host': 'host2', 'name': 'vm3'}
    ]
    test_complexity = get_complexity_parameters("medium", 2)
    ENVIRONMENT_DATA["config"].update(test_complexity)


    generate_vhost_csv(
        complexity_params=test_complexity,
        scenario_config=None,
        use_ai_cli_flag=True,
        ai_provider_cli_arg="openai",
        ollama_model_name="llama3"
    )

    mock_write_csv.assert_called_once()
    args, _ = mock_write_csv.call_args
    assert args[1] == "vHost" # filename_prefix
    assert len(args[0]) == 2 # Number of hosts

    # Check if AI data was merged by looking at one of the AI-provided fields in the data passed to write_csv
    # args[0] is the list of rows (which are lists themselves)
    header_list = CSV_HEADERS["vHost"]
    vendor_index = header_list.index("Vendor")
    assert args[0][0][vendor_index] == "AI Host Vendor"
    assert args[0][1][vendor_index] == "AI Host Vendor"


@mock.patch('rvtools_data_generator.write_csv')
@mock.patch('rvtools_data_generator._get_ai_data_for_entity')
def test_generate_vdisk_csv_with_profile(mock_get_ai, mock_write_csv, tmp_path):

    def side_effect_ai_vdisk(prompt_template, context, *args, **kwargs):
        return {
            "Disk": context.get("disk_label", "Hard disk AI"),
            "Capacity MB": context.get("profile_disk_capacity_mib", 20480),
            "Thin": True, # AI decides true, overriding profile if different
            "Disk Mode": "persistent",
            "Controller": "AI SCSI Controller",
            "Path": f"[{context.get('datastore_name', 'ai_ds')}] {context.get('vm_name', 'ai_vm')}/{context.get('vm_name', 'ai_vm')}_{context.get('disk_index', 0)}.vmdk"
        }
    mock_get_ai.side_effect = side_effect_ai_vdisk

    vm_name_test = 'TestVM_DiskProfile'
    ENVIRONMENT_DATA["vms"] = [{
        'name': vm_name_test, 'uuid': generate_uuid(), 'power_state': 'PoweredOn',
        'is_template': False, 'host': 'host1', 'cluster': 'Clus1',
        'datacenter': 'DC1', 'folder': 'Folder1', 'resource_pool': 'RP1',
        'os': 'otherGuest', 'num_disks': 2, # This field from vInfo drives disk generation
        'profile_disks': [ # This is used by generate_vdisk_csv to pass to _row_ai
            {'label': 'OSDisk', 'size_gb': 50, 'thin_provisioned': False, 'controller_type': "SCSI"},
            {'label': 'DataDisk', 'size_gb': 100, 'thin_provisioned': True, 'controller_type': "NVMe"}
        ],
        'sdk_server': 'vc.test', 'sdk_uuid': 'vc-uuid1'
    }]
    # Ensure a datastore exists for the disk to be placed on
    ENVIRONMENT_DATA["datastores"].append(
        {"name": "TestDS01", "type": "VMFS", "is_local": False, "datacenter": "DC1"}
    )

    test_complexity = get_complexity_parameters("medium", 1)
    ENVIRONMENT_DATA["config"].update(test_complexity)
    test_scenario = {'description': 'Test scenario with profile disks'}

    generate_vdisk_csv(
        complexity_params=test_complexity,
        scenario_config=test_scenario, # Pass scenario to enable profile usage
        use_ai_cli_flag=True,
        ai_provider_cli_arg="openai",
        ollama_model_name="llama3"
    )

    mock_write_csv.assert_called_once()
    args, _ = mock_write_csv.call_args
    assert args[1] == "vDisk"
    assert len(args[0]) == 2 # 2 disks for the VM

    # Check if AI data ('Thin': True) was applied to the first disk, overriding profile's False
    header_list = CSV_HEADERS["vDisk"]
    thin_index = header_list.index("Thin")
    controller_index = header_list.index("Controller") # Assuming 'Controller' is a header, adjust if not

    first_disk_data_written = args[0][0] # This is a list
    assert first_disk_data_written[thin_index] is True
    assert first_disk_data_written[controller_index] == "AI SCSI Controller"
```
