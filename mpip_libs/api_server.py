from flask import Flask
from flask import request
import mpip_libs.database as database
from mpip_libs.database import LVENAgent, LVENPairingKey
import mpip_libs.ilo_api as ilo_api
import time
import waitress
import logging


app = Flask(__name__)

def start_server(developer_mode: bool = False):
    if developer_mode:
        app.run()
    else:
        waitress.serve(app, listen='*:9111')


@app.route('/agent/pair', methods=['POST'])
def agent_register():
    db = database.new_connection()

    # check if an agent name was provided
    if 'agent_name' not in request.json:
        return 'Agent name not provided', 400

    agent_name = request.json['agent_name']
    #does the agent name already exist?
    if database.LVENAgent.name_exists(db, agent_name):
        return 'Agent name already exists', 400

    # check if an activation key was provided
    if 'pairing_key' not in request.json:
        return 'Activation key not provided', 400

    #does the activation key exist?
    activation_key: LVENPairingKey.PairingKeyObject = database.LVENPairingKey.get_single(db, request.json['pairing_key'])
    if activation_key is None:
        return 'Activation key does not exist', 400

    #is the activation key still valid?
    if activation_key['valid_until'] is not None and activation_key['valid_until'] < int(time.time()):
        return 'Activation key has expired', 400

    #does it still have enough use counts?
    if activation_key['remaining_uses'] is not None and activation_key['remaining_uses'] <= 0:
        return 'Activation key has no more uses left', 400

    # does the agent_name exists in the PCE?
    pce_workloads = ilo_api.find_unmanaged_workloads_with_specific_name(agent_name)
    if len(pce_workloads) == 0:
        return 'Agent name does not exist in the PCE or is already managed', 400
    if len(pce_workloads) > 1:
        return 'Agent name exists more than once in the PCE', 400

    workload_href = pce_workloads[0]['href']

    if activation_key['target_switch_href'] is not None:
        # does the switch still exist in the PCE?
        switch = ilo_api.find_switch_from_href_or_name(activation_key['target_switch_href'])
        if switch is None:
            return 'Target switch does not exist in the PCE', 400
        # is the workload_href already bound to the switch?
        if ilo_api.find_if_workload_is_already_assigned_to_a_switch_port(workload_href, activation_key['target_switch_href']):
            return 'Workload is already bound to the switch', 400

        # bind the workload to the switch
        logging.info('Binding workload {workload_href} to switch {activation_key["target_switch_href"]}')
        ilo_api.bind_workload_to_switch(workload_href, activation_key['target_switch_href'])


    # create the agent
    agent = database.LVENAgent.create(db, agent_name, pce_workload_href=workload_href)

    # decrease the use count of the activation key
    if activation_key['remaining_uses'] is not None:
        database.LVENPairingKey.decrease_use_count(db, activation_key['key'])

    return {'agent_uuid': agent['uuid'], 'authentication_key': agent['authentication_key'] }, 200


@app.route('/agent/<agent_uuid>/heartbeat', methods=['POST'])
def agent_heartbeat(agent_uuid: str):
    db = database.new_connection()

    #does the agent uuid exist?
    agent: LVENAgent.LVENAgentObject = database.LVENAgent.get(db, agent_uuid)
    if agent is None:
        return 'Agent UUID does not exist', 404

    #is the authentication key correct?
    if 'authentication_key' not in request.json:
        return 'Authentication key not provided', 403
    if request.json['authentication_key'] != agent['authentication_key']:
        return 'Authentication key is incorrect', 403

    # update the last heartbeat
    database.LVENAgent.heartbeat(db, agent_uuid)

    return {'action': 'agent_heartbeat','status': 'success'}, 200

@app.route('/agent/<agent_uuid>/active_policies', methods=['POST'])
def agent_active_policies(agent_uuid: str):
    db = database.new_connection()

    #does the agent uuid exist?
    agent: LVENAgent.LVENAgentObject = database.LVENAgent.get(db, agent_uuid)
    if agent is None:
        return 'Agent UUID does not exist', 404

    #is the authentication key correct?
    if 'authentication_key' not in request.json:
        return 'Authentication key not provided', 403
    if request.json['authentication_key'] != agent['authentication_key']:
        return 'Authentication key is incorrect', 403

    # get the active policies
    active_policies = ilo_api.get_workload_active_policies(agent['pce_workload_href'])

    return active_policies, 200







