import os
import yaml


# the following variables could be overriden by the runtime_env.yml file
settings_persistent_directory = '/var/lib/illumio-mpip/data'
settings_runtime_directory = '/var/lib/illumio-mpip/runtime'
settings_log_directory = '/var/log/illumio-mpip'

#the following variables MUST be set by the runtime_env.yml file
settings_pce_fqdn_and_port: str
settings_pce_api_user: str
settings_pce_api_secret: str
settings_pce_org_id: str

def load_runtime_env_yaml(file_path: str):
    # throw error of file_path doesn't exist
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    # open yaml file
    with open(file_path, 'r') as stream:
        try:
            yaml_content = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

        # update the settings with the yaml content
        if 'persistent_data_dir' in yaml_content:
            global settings_persistent_directory
            settings_persistent_directory = yaml_content['persistent_data_dir']
        if 'runtime_dir' in yaml_content:
            global settings_runtime_directory
            settings_runtime_directory = yaml_content['runtime_dir']
        if 'log_dir' in yaml_content:
            global settings_log_directory
            settings_log_directory = yaml_content['log_dir']

        # update the mandatory settings with the yaml content
        if 'pce_fqdn_and_port' in yaml_content:
            global settings_pce_fqdn_and_port
            settings_pce_fqdn_and_port = yaml_content['pce_fqdn_and_port']
        else:
            raise ValueError('pce_fqdn_and_port is not defined in the runtime_env.yml file')

        if 'pce_api_user' in yaml_content:
            global settings_pce_api_user
            settings_pce_api_user = yaml_content['pce_api_user']
        else:
            raise ValueError('pce_api_user is not defined in the runtime_env.yml file')

        if 'pce_api_secret' in yaml_content:
            global settings_pce_api_secret
            settings_pce_api_secret = yaml_content['pce_api_secret']
        else:
            raise ValueError('pce_api_secret is not defined in the runtime_env.yml file')

        if 'pce_org_id' in yaml_content:
            global settings_pce_org_id
            settings_pce_org_id = yaml_content['pce_org_id']


    return yaml_content



