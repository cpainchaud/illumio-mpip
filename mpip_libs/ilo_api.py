import logging
from typing import List, Optional

from pylo.API.JsonPayloadTypes import WorkloadObjectJsonStructure, NetworkDeviceObjectJsonStructure

import mpip_libs.runtime_env as runtime_env
import pylo


connector: pylo.APIConnector


def init():
    global connector

    # settings_pce_fqdn_and_port must be split into two parts: the fqdn and the port
    fqdn_and_port = runtime_env.settings_pce_fqdn_and_port.split(':')
    if len(fqdn_and_port) != 2:
        raise ValueError(f"Invalid PCE FQDN and port: {runtime_env.settings_pce_fqdn_and_port}")

    # create the API connector
    connector = pylo.APIConnector(
        hostname=fqdn_and_port[0],
        port=int(fqdn_and_port[1]),
        apiuser=runtime_env.settings_pce_api_user,
        apikey=runtime_env.settings_pce_api_secret,
        org_id=runtime_env.settings_pce_org_id
    )

    #testing the PCE connection now:
    connector.get_software_version()


def find_unmanaged_workloads_with_specific_name(name: str) -> List[WorkloadObjectJsonStructure]:
    # find the workload with the specific name
    workloads = []

    json_workloads = connector.objects_workload_get(filter_by_name=name)

    for workload in json_workloads:
        #logging.warning(workload)
        if workload['managed'] is not False:
            continue
        if workload['name'] == name or workload['hostname'] == name:
            workloads.append(workload)
    return workloads

def find_switch_from_href_or_name(switch_href_or_name: str) -> Optional[NetworkDeviceObjectJsonStructure]:
    # find the switch from the href or name
    search_on_href = False
    if switch_href_or_name.startswith('/orgs/'):
        search_on_href = True

    devices_json = connector.objects_network_device_get()

    for device in devices_json:
        if device['supported_endpoint_type'] != 'switch_port':
            continue
        if search_on_href:
            if device['href'] == switch_href_or_name:
                return device
        else:
            if device['config']['name'] == switch_href_or_name:
                return device

    return None

def find_if_workload_is_already_assigned_to_a_switch_port(workload_href: str, network_device_href: str) -> bool:
    endpoints = connector.object_network_device_endpoints_get(network_device_href=network_device_href)
    for endpoint in endpoints:
        for local_workload_href in endpoint['workloads']:
            if local_workload_href['href'] == workload_href:
                return True

    return False

def bind_workload_to_switch(workload_href: str, network_device_href: str):
    connector.object_network_device_endpoint_create(name=workload_href,
                                                    network_device_href=network_device_href,
                                                    endpoint_type='switch_port',
                                                    workloads_href=[workload_href])

def get_workload_active_policies(workload_href: str):
    return connector.object_workload_get_active_policies(workload_href=workload_href)