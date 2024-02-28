from typing import TypedDict, Optional
import random
import time
import uuid
from sqlite3 import Connection

class LVENAgentObject(TypedDict):
    uuid: str
    name: str
    pce_workload_href: str
    authentication_key: str # a 64 character string used to authenticate the agent
    last_heartbeat: int
    created_at: int

class LVENAgentNotFound(Exception):
    pass

def row_to_agent(row: dict) -> LVENAgentObject:
    return LVENAgentObject(uuid=row['uuid'], name=row['name'], pce_workload_href=row['pce_workload_href'],
                          created_at=row['created_at'] , last_heartbeat=row['last_heartbeat'], authentication_key=row['authentication_key'])

def uuid_exists(db: Connection, agent_uuid: str) -> bool:
    c = db.cursor()
    c.execute('SELECT * FROM lven_agents WHERE uuid = ?', (agent_uuid,))
    return c.fetchone() is not None

def name_exists(db: Connection, agent_name: str) -> bool:
    c = db.cursor()
    c.execute('SELECT * FROM lven_agents WHERE name = ?', (agent_name,))
    return c.fetchone() is not None

def delete(db: Connection, agent_uuid: str):
    c = db.cursor()
    c.execute('DELETE FROM lven_agents WHERE uuid = ?', (agent_uuid,))
    db.commit()
    # count the number of rows deleted
    if c.rowcount == 0:
        raise ValueError(f"Agent with UUID {agent_uuid} does not exist")

def create(db: Connection, agent_name: str, pce_workload_href: str) -> LVENAgentObject:
    # Generate a UUID for the agent and make sure it doesn't exist
    agent_uuid = str(uuid.uuid4())
    authentication_key = random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=64)
    authentication_key = ''.join(authentication_key)

    while uuid_exists(db, agent_uuid):
        agent_uuid = str(uuid.uuid4())

    c = db.cursor()
    c.execute('INSERT INTO lven_agents (uuid, name, pce_workload_href, last_heartbeat, created_at, authentication_key) VALUES (?, ?, ?, ?, ?, ?)',
              (agent_uuid, agent_name, pce_workload_href, time.time(), time.time(), authentication_key))
    db.commit()

    return get(db, agent_uuid)

def get(db: Connection, agent_uuid: str) -> Optional[LVENAgentObject]:
    c = db.cursor()
    c.execute('SELECT * FROM lven_agents WHERE uuid = ?', (agent_uuid,))
    row = c.fetchone()
    if row is None:
        return None
    return row_to_agent(row)

def get_all(db: Connection) -> list[LVENAgentObject]:
    c = db.cursor()
    c.execute('SELECT * FROM lven_agents')
    rows = c.fetchall()
    return [row_to_agent(row) for row in rows]

def delete_all(db: Connection):
    c = db.cursor()
    c.execute('DELETE FROM lven_agents')
    db.commit()


def heartbeat(db: Connection, agent_uuid: str):
    c = db.cursor()
    c.execute('UPDATE lven_agents SET last_heartbeat = ? WHERE uuid = ?', (time.time(), agent_uuid))
    db.commit()
    if c.rowcount == 0:
        raise LVENAgentNotFound(f"LVEN Agent with UUID '{agent_uuid}' does not exist")