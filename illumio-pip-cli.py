import argparse
import os
import logging
import time
import datetime

from mpip_libs import runtime_env, database
from mpip_libs.database import LVENPairingKey, LVENAgent

from mpip_libs.misc import default_runtime_env_file_location, check_required_directories_exist
from mpip_libs import ilo_api

parser = argparse.ArgumentParser(description = 'Illumio MPIP CLI')
parser.add_argument('--runtime-env-file', '-r',
                    required=False, default=default_runtime_env_file_location,
                    help='Path to the runtime_env.yml file')

sub_parsers = parser.add_subparsers(dest='tool', required=True)
sub_parser_status = sub_parsers.add_parser('status', help='Check the status of the illumio-mpip server')
sub_parser_db_setup = sub_parsers.add_parser('db-setup', help='Setup the database for the illumio-mpip tools and server')
sub_parser_pairing_key_manager = sub_parsers.add_parser('pairing-key-manager', help='Manage pairing keys')
sub_parser_lven_agent_manager = sub_parsers.add_parser('lven-agent-manager', help='Manage LVEN agents')

sub_parser_pairing_key_manager_sub_parsers = sub_parser_pairing_key_manager.add_subparsers(dest='action', required=True)
sub_parser_pairing_key_manager_action_list = sub_parser_pairing_key_manager_sub_parsers.add_parser('list', help='List pairing keys')
sub_parser_pairing_key_manager_action_create = sub_parser_pairing_key_manager_sub_parsers.add_parser('create', help='Create a pairing key')
sub_parser_pairing_key_manager_action_delete = sub_parser_pairing_key_manager_sub_parsers.add_parser('delete', help='Delete a pairing key')

# remaining uses is required and can be an int or the string 'unlimited'
sub_parser_pairing_key_manager_action_create.add_argument('--remaining-uses', '-r', type=str, required=True, help='Number of uses remaining for the pairing key or "unlimited"')
sub_parser_pairing_key_manager_action_create.add_argument('--expiration-delay', '-e', type=str, required=True, help='Expiration delay (seconds) for the pairing key or "unlimited"')
sub_parser_pairing_key_manager_action_create.add_argument('--target-switch-href-or-name', '-t', type=str, required=False, help='Target switch HREF or name for the pairing key')

sub_parser_lven_agent_manager_sub_parsers = sub_parser_lven_agent_manager.add_subparsers(dest='action', required=True)
sub_parser_lven_agent_manager_delete_all = sub_parser_lven_agent_manager_sub_parsers.add_parser('delete-all', help='Delete all LVEN agents')
sub_parser_lven_agent_manager_list = sub_parser_lven_agent_manager_sub_parsers.add_parser('list', help='List LVEN agents')
sub_parser_lven_agent_manager_list.add_argument('--show-authentication-keys', '-p', action='store_true', help='Show the authentication keys of the agents')

args = parser.parse_args()

# get full path of the runtime_env file
runtime_env_file = os.path.abspath(args.runtime_env_file)

print('* using runtime_env file:', runtime_env_file, flush=True)
runtime_env.load_runtime_env_yaml(runtime_env_file)

print('* checking directories... ', end='', flush=True)
check_required_directories_exist()
print('OK')

print('* Initializing Illumio PCE API link... ', end='', flush=True)
ilo_api.init()
print('OK')

if args.tool == 'db-setup':
    print("** STARTED DB SETUP **", flush=True)
    if not database.database_exists():
        print("* DB doesn't exist yet, creating it...", flush=True, end='')
        database.create_database()
        print('OK')
    else:
        # database already exists, ERROR!
        logging.error("* DB already exists, nothing to do.")
        exit(1)
    exit(0)

print("* checking database...", end='', flush=True)
if not database.database_exists():
    print('FAIL')
    print(f"The database file {database.database_file_path()} does not exist. Did you set it up first? (db-setup)")
    exit(1)

conn = database.new_connection()
print('OK', flush=True)


if args.tool == 'pairing-key-manager':
    if args.action == 'list':
        print("** LISTING PAIRING KEYS **", flush=True)
        pairing_keys = database.LVENPairingKey.get_all(conn)
        # print pairing keys as nice table
        print("  {:<32} | {:<10} | {:<61} | {:<19} | {:<19}".format('Key', 'Remaining', 'Switch HREF', 'Valid Until', 'Created at'))
        for pairing_key in pairing_keys:
            print("  {:<32} | {:<10} | {:<61} | {:<19} | {:<19}".format(pairing_key['key'],
                                                          pairing_key['remaining_uses'] if pairing_key['remaining_uses'] is not None else 'unlimited',
                                                          pairing_key['target_switch_href'] if pairing_key['target_switch_href'] is not None else 'none',
                                                          str(datetime.datetime.fromtimestamp(pairing_key['valid_until'])) if pairing_key['valid_until'] is not None else 'never',
                                                          str(datetime.datetime.fromtimestamp(pairing_key["created_at"]))
                                                          )
                  )
        exit(0)
    elif args.action == 'create':
        # check for remaining uses value to be 'unlimited' or an int
        if args.remaining_uses.lower() != 'unlimited':
            try:
                args.remaining_uses = int(args.remaining_uses)
            except ValueError:
                print("The remaining uses value must be 'unlimited' or an integer")
                exit(1)

        # if remaining_uses is still a string, then it's 'unlimited'
        if type(args.remaining_uses) == str:
            args.remaining_uses = None

        # check for expiration delay value to be 'unlimited' or an int
        if args.expiration_delay.lower() != 'unlimited':
            try:
                args.expiration_delay = int(args.expiration_delay)
            except ValueError:
                print("The expiration delay value must be 'unlimited' or an integer")
                exit(1)

        # if expiration_delay is still a string, then it's 'unlimited' so it must be set to None
        if type(args.expiration_delay) == str:
            args.expiration_delay = None

        if args.target_switch_href_or_name is not None:
            # first we need to find if the switch exists inside the PCE
            print("** FINDING SWITCH IN PCE **", flush=True)
            print(" * Searching for switch with HREF or name: {}".format(args.target_switch_href_or_name))
            switch = ilo_api.find_switch_from_href_or_name(args.target_switch_href_or_name)
            if switch is None:
                print(" * Switch not found")
                exit(1)
            print(" * Switch found: {} with HREF={}".format(switch['config']['name'], switch['href']))
            args.target_switch_href_or_name = switch['href']


        print("** CREATING PAIRING KEY **", flush=True)
        print(" * Request parameters: remaining uses: {} - expiration delay: {} seconds".format(args.remaining_uses, args.expiration_delay))
        pairing_key = database.LVENPairingKey.create(conn, args.expiration_delay, args.remaining_uses, args.target_switch_href_or_name)
        print(" * Pairing key created: {}"
              " - {} uses left"
              " - valid until {}"
              " - created at {}"
              " - target switch: {}"
              .format(pairing_key['key'],
                        pairing_key['remaining_uses'] if pairing_key['remaining_uses'] is not None else 'unlimited',
                        datetime.datetime.fromtimestamp(pairing_key['valid_until']) if pairing_key['valid_until'] is not None else 'never',
                        datetime.datetime.fromtimestamp(pairing_key["created_at"]),
                        pairing_key['target_switch_href'] if pairing_key['target_switch_href'] is not None else 'none'
                      )
              )


        exit(0)
    else:
        # unsupported action
        logging.error(f"Unsupported action: {args.action}")
        exit(1)
elif args.tool == 'lven-agent-manager':
    if args.action == 'delete-all':
        print("** DELETING ALL LVEN AGENTS **", flush=True)
        print("* Deleting all LVEN agents...", flush=True, end='')
        database.LVENAgent.delete_all(conn)
        print('OK')
        exit(0)
    elif args.action == 'list':
        print("** LISTING LVEN AGENTS **", flush=True)
        agents = database.LVENAgent.get_all(conn)
        # print agents as nice table
        template_string = "  {:<36} | {:<20} | {:<55} | {:<19} | {:<19}"
        if args.show_authentication_keys:
            template_string += " | {:<64}"

        print(template_string.format('UUID', 'Name', 'PCE Workload HREF', 'Last Heartbeat', 'Created at', 'Authentication Key' if args.show_authentication_keys else ''))
        for agent in agents:
            print(template_string.format(agent['uuid'],
                                                          agent['name'],
                                                          agent['pce_workload_href'],
                                                          str(datetime.datetime.fromtimestamp(agent['last_heartbeat'])),
                                                          str(datetime.datetime.fromtimestamp(agent["created_at"])),
                                                          agent['authentication_key'] if args.show_authentication_keys else ''
                                                          )
                  )
        exit(0)
    else:
        # unsupported action
        logging.error(f"Unsupported action: {args.action}")
        exit(1)
else:
    # unsupported tool
    logging.error(f"Unsupported tool: {args.tool}")
    exit(1)


