import argparse
import mpip_libs.api_server
from pid import PidFile

from mpip_libs import runtime_env, ilo_api, database

process_title = 'illumio-mpip-server'
pid_file = 'illumio-mpip-server.pid'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Illumio MPIP SERVER')
    parser.add_argument('--runtime-env-file',
                        required=False, default='/etc/illumio-mpip/runtime_env.yml',
                        help='Path to the runtime_env.yml file')
    parser.add_argument('--local-dev-server', action='store_true', help='Run the server on the local development server')
    parser.add_argument('--create-database-if-not-exists', action='store_true', help='Create the database if it does not exist')
    args = parser.parse_args()

    runtime_env.load_runtime_env_yaml(args.runtime_env_file)
    #ilo_api.init()

    # here we ensure that the pid file is created and locked then we can finally serve our first requests
    with PidFile(process_title, piddir=runtime_env.settings_runtime_directory) as p:
        if args.create_database_if_not_exists:
            database.create_database()
        mpip_libs.database.init()
        mpip_libs.ilo_api.init()
        mpip_libs.api_server.start_server(developer_mode=args.local_dev_server)



