-- THIS IS SQLITE3 FORMAT

CREATE TABLE lven_agents (
    uuid TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    authentication_key TEXT NOT NULL,
    last_heartbeat INTEGER NOT NULL,
    pce_workload_href TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE lven_agents_ip_addresses (
    agent_uuid TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    FOREIGN KEY (agent_uuid) REFERENCES lven_agents(uuid),
    PRIMARY KEY (agent_uuid, ip_address)
);

CREATE TABLE lven_agent_pairing_keys (
    key TEXT PRIMARY KEY NOT NULL,
    target_switch_href TEXT,
    created_at INTEGER NOT NULL,
    valid_until INTEGER, -- NULL means no expiration
    remaining_uses INTEGER -- 0 means no uses left, NULL means no limit
);
