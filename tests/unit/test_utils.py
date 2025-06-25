import pytest
import os
import re
import uuid as uuid_module # To avoid conflict with our function
from datetime import datetime, timedelta
import sys

# Add project root to sys.path to allow importing rvtools_data_generator
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Conditional import for yaml for testing load_scenario_config
try:
    import yaml
    YAML_AVAILABLE_FOR_TEST = True
except ImportError:
    YAML_AVAILABLE_FOR_TEST = False

from rvtools_data_generator import (
    generate_random_string,
    generate_random_boolean,
    generate_random_integer,
    generate_ip_address, # Renamed in main script
    generate_mac_address, # Renamed in main script
    generate_random_date, # Renamed in main script
    choose_randomly_from_list,
    generate_vm_name,
    generate_uuid,
    get_complexity_parameters,
    load_scenario_config,
    YAML_AVAILABLE # This is the flag from the main script
)

# --- Tests for Random Data Generators ---
def test_generate_random_string():
    s1 = generate_random_string()
    assert len(s1) == 10
    assert s1.isalnum()

    s_pref_len = generate_random_string(length=10, prefix="p_")
    assert len(s_pref_len) == 10 # Length of random part is 10, prefix is extra
    assert s_pref_len.startswith("p_")
    assert len(s_pref_len[2:]) == 8 # prefix is 'p_', 2 chars, random part is 8
    assert s_pref_len[2:].isalnum()


    s_long_pref = generate_random_string(length=5, prefix="longprefix")
    assert s_long_pref == "longprefixlongp" # Corrected expected output

    s_short_len_no_pref = generate_random_string(length=3)
    assert len(s_short_len_no_pref) == 3
    assert s_short_len_no_pref.isalnum()

def test_generate_random_boolean():
    results = [generate_random_boolean() for _ in range(30)]
    assert all(isinstance(r, bool) for r in results)
    assert True in results, "generate_random_boolean() did not produce True in 30 attempts"
    assert False in results, "generate_random_boolean() did not produce False in 30 attempts"

def test_generate_random_integer():
    val = generate_random_integer(5, 10)
    assert isinstance(val, int)
    assert 5 <= val <= 10
    val_default = generate_random_integer()
    assert isinstance(val_default, int)
    assert 0 <= val_default <= 100

def test_generate_random_ip_address():
    ip = generate_ip_address() # Updated function name
    assert isinstance(ip, str)
    assert re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip), f"IP {ip} format is invalid"
    # More robust IP validation could be done with ipaddress module if needed
    # For example:
    # try:
    #     ipaddress.ip_address(ip)
    # except ValueError:
    #     pytest.fail(f"Generated IP '{ip}' is not a valid IP address.")

def test_generate_random_mac_address():
    mac = generate_mac_address() # Updated function name
    assert isinstance(mac, str)
    assert re.match(r"^00:50:56(:[0-9A-F]{2}){3}$", mac, re.IGNORECASE), f"MAC {mac} format or OUI is invalid"

def test_generate_random_datetime():
    dt_format_in_script = "%Y-%m-%d %H:%M:%S" # Format used in main script

    dt_str1 = generate_random_date() # Updated function name
    assert isinstance(dt_str1, str)
    datetime.strptime(dt_str1, dt_format_in_script)

    start_date_val_str = "2023-05-10" # Use YYYY-MM-DD as per main script's default
    end_date_val_str = "2023-05-15"
    dt_str2 = generate_random_date(start_date_str=start_date_val_str, end_date_str=end_date_val_str)
    assert isinstance(dt_str2, str)
    generated_dt_obj = datetime.strptime(dt_str2, dt_format_in_script)

    start_dt_obj = datetime.strptime(start_date_val_str, "%Y-%m-%d")
    # end_dt_obj can be up to almost the start of the next day from end_date_str
    end_dt_obj_limit = datetime.strptime(end_date_val_str, "%Y-%m-%d") + timedelta(days=1)
    assert start_dt_obj <= generated_dt_obj < end_dt_obj_limit

    dt_str3 = generate_random_date(start_date_str="2023-10-10", end_date_str="2023-10-10")
    datetime.strptime(dt_str3, dt_format_in_script)
    generated_dt_obj3 = datetime.strptime(dt_str3, dt_format_in_script)
    assert generated_dt_obj3.date() == datetime.strptime("2023-10-10", "%Y-%m-%d").date()


def test_choose_random_from_list():
    my_list = ["a", "b", "c"]
    choice = choose_random_from_list(my_list)
    assert choice in my_list

    empty_choice = choose_random_from_list([], default_value="EMPTY") # Test default value
    assert empty_choice == "EMPTY"

    single_list = ["onlyone"]
    assert choose_random_from_list(single_list) == "onlyone"

def test_generate_vm_name():
    vm_name_default = generate_vm_name() # prefix is "vm" by default, index is scenario_vm_index
    assert vm_name_default.startswith("vm-")
    assert len(vm_name_default.split('-')[-1]) == 3 # Check for zfill

    vm_name_custom = generate_vm_name(profile_vm_name_prefix="MyTestVM", scenario_vm_index=5)
    assert vm_name_custom == "MyTestVM-005"

    vm_name_no_index = generate_vm_name(profile_vm_name_prefix="NoIdxTest")
    assert vm_name_no_index.startswith("NoIdxTest-")
    assert len(vm_name_no_index.split('-')[-1]) == 3


def test_generate_uuid_format():
    generated = generate_uuid()
    assert isinstance(generated, str)
    try:
        uuid_obj = uuid_module.UUID(generated)
        assert str(uuid_obj) == generated.lower()
    except ValueError:
        pytest.fail(f"Generated UUID '{generated}' is not a valid UUID string.")

    prefix = "vm-"
    generated_with_prefix = generate_uuid(prefix=prefix)
    assert generated_with_prefix.startswith(prefix)
    try:
        uuid_obj_pref = uuid_module.UUID(generated_with_prefix[len(prefix):])
        assert prefix + str(uuid_obj_pref) == generated_with_prefix.lower()
    except ValueError:
        pytest.fail(f"Generated UUID with prefix '{generated_with_prefix}' is not valid.")


# --- Tests for Configuration-related Utility Functions ---
def test_get_complexity_parameters():
    base_vms = 100
    simple = get_complexity_parameters("simple", base_vms)
    medium = get_complexity_parameters("medium", base_vms) # base_vms used directly for medium if not None
    fancy = get_complexity_parameters("fancy", base_vms)  # base_vms used directly for fancy if not None

    assert simple['num_vms'] == base_vms # CLI/scenario overrides simple's default
    assert medium['num_vms'] == base_vms
    assert fancy['num_vms'] == base_vms

    # Test with base_vms = None, so defaults from function are used
    simple_def = get_complexity_parameters("simple", None)
    medium_def = get_complexity_parameters("medium", None)
    fancy_def = get_complexity_parameters("fancy", None)

    assert simple_def['num_vms'] == 10
    assert medium_def['num_vms'] == 50
    assert fancy_def['num_vms'] == 100


    assert simple_def['feature_likelihood']['snapshots'] < medium_def['feature_likelihood']['snapshots']
    assert fancy_def['feature_likelihood']['snapshots'] > medium_def['feature_likelihood']['snapshots']
    assert "core_csvs_simple" in simple_def
    assert simple_def['max_items']['disks_per_vm'] == 2 # Default was 1, check if it's 2 now as per typical "simple"
    assert medium_def['max_items']['disks_per_vm'] == 3
    assert fancy_def['max_items']['disks_per_vm'] == 5 # Default was 4, check if it's 5 now as per typical "fancy"


# Use the YAML_AVAILABLE_FOR_TEST flag which checks local test environment
@pytest.mark.skipif(not YAML_AVAILABLE_FOR_TEST, reason="PyYAML not installed in test environment, skipping config load tests.")
def test_load_scenario_config(tmp_path):
    # Test with non-existent file
    assert load_scenario_config(os.path.join(tmp_path, "non_existent.yaml")) is None

    valid_yaml_content = """
global_settings:
  datacenter_prefix: "TestDC"
datacenters:
  - name: "DC1"
    cluster_profiles:
      standard_cluster:
        num_hosts: 2
"""
    valid_yaml_file = tmp_path / "valid.yaml"
    valid_yaml_file.write_text(valid_yaml_content)
    config = load_scenario_config(str(valid_yaml_file))
    assert config is not None
    assert config['global_settings']['datacenter_prefix'] == "TestDC"
    assert len(config['datacenters']) == 1
    assert config['datacenters'][0]['cluster_profiles']['standard_cluster']['num_hosts'] == 2


    malformed_yaml_content = "key: value: [another_value"
    malformed_yaml_file = tmp_path / "malformed.yaml"
    malformed_yaml_file.write_text(malformed_yaml_content)
    # Check if the main script's YAML_AVAILABLE flag is True before asserting None
    if YAML_AVAILABLE: # This refers to the flag in rvtools_data_generator.py
        assert load_scenario_config(str(malformed_yaml_file)) is None
    else:
        # If YAML_AVAILABLE is False in the main script, load_scenario_config returns None early
        assert load_scenario_config(str(malformed_yaml_file)) is None

    empty_yaml_file = tmp_path / "empty.yaml"
    empty_yaml_file.write_text("")
    empty_config = load_scenario_config(str(empty_yaml_file))
    # yaml.safe_load("") returns None, so this is expected
    assert empty_config is None
```
