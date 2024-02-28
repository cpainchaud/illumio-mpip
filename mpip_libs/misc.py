default_runtime_env_file_location = '/etc/illumio-mpip/runtime_env.yml'

import mpip_libs.runtime_env as runtime_env
import os

def check_required_directories_exist():
    # check if the runtime directory exists and is writable
    if not os.path.exists(runtime_env.settings_persistent_directory):
        raise FileNotFoundError(f"The directory {runtime_env.settings_persistent_directory} does not exist.")
    if not os.access(runtime_env.settings_persistent_directory, os.W_OK):
        raise PermissionError(f"The directory {runtime_env.settings_persistent_directory} is not writable.")

    # check if the persistent directory exists and is writable
    if not os.path.exists(runtime_env.settings_runtime_directory):
        raise FileNotFoundError(f"The directory {runtime_env.settings_runtime_directory} does not exist.")
    if not os.access(runtime_env.settings_runtime_directory, os.W_OK):
        raise PermissionError(f"The directory {runtime_env.settings_runtime_directory} is not writable.")

    # check if the log directory exists and is writable
    if not os.path.exists(runtime_env.settings_log_directory):
        raise FileNotFoundError(f"The directory {runtime_env.settings_log_directory} does not exist.")
    if not os.access(runtime_env.settings_log_directory, os.W_OK):
        raise PermissionError(f"The directory {runtime_env.settings_log_directory} is not writable.")
