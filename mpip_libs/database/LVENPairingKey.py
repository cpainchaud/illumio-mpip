from typing import TypedDict, Optional
import random
import time
from sqlite3 import Connection
import logging

class PairingKeyObject(TypedDict):
    key: str # the pairing itself, a 32 character string
    target_switch_href: Optional[str] # the HREF of the switch the key is will create an association with the Workload
    valid_until: int # 0 means the key will never expire, timestamp when the key will expire
    remaining_uses: Optional[int]  # None means unlimited, 0 means the key is no longer valid
    created_at: int # the timestamp when the key was created


class LVENPairingKeyDoesNotExist(Exception):
    pass

def row_to_pairing_key(row: dict) -> PairingKeyObject:
    return PairingKeyObject(key=row['key'], valid_until=row['valid_until'], remaining_uses=row['remaining_uses'], created_at=row['created_at'],
                             target_switch_href=row['target_switch_href'])

def create(db: Connection, valid_for: Optional[int], uses_count: Optional[int], target_switch_href: Optional[str]) -> PairingKeyObject:
    if uses_count == 0:
        raise ValueError('uses_count cannot be 0')

    pairing_key = random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=32)
    pairing_key = ''.join(pairing_key)

    expiration_time = (int(time.time())+valid_for) if valid_for is not None else None

    c = db.cursor()
    c.execute('INSERT INTO lven_agent_pairing_keys (key, valid_until, remaining_uses, created_at, target_switch_href) VALUES (?, ?, ?, ?, ?)',
              (pairing_key, expiration_time, uses_count, int(time.time()),
               target_switch_href))
    db.commit()

    return get_single(db, pairing_key)

def delete(db: Connection, pairing_key: str):
    c = db.cursor()
    c.execute('DELETE FROM lven_agent_pairing_keys WHERE key = ?', (pairing_key,))
    db.commit()
    if c.rowcount == 0:
        raise LVENPairingKeyDoesNotExist(f"LVEN Pairing key '{pairing_key}' does not exist")

def exists(db: Connection, pairing_key: str) -> bool:
    c = db.cursor()
    c.execute('SELECT * FROM lven_agent_pairing_keys WHERE key = ?', (pairing_key,))
    return c.fetchone() is not None

def get_single(db: Connection, pairing_key: str) -> Optional[PairingKeyObject]:
    c = db.cursor()
    c.execute('SELECT * FROM lven_agent_pairing_keys WHERE key = ?', (pairing_key,))
    row = c.fetchone()
    if row is None:
        return None
    return row_to_pairing_key(row)

def get_all(db: Connection) -> list[PairingKeyObject]:
    c = db.cursor()
    c.execute('SELECT * FROM lven_agent_pairing_keys')
    rows = c.fetchall()
    return [row_to_pairing_key(row) for row in rows]

def decrease_use_count(db: Connection, pairing_key: str):
    # remaining_uses is allowed to be None, so we need to check for that
    c = db.cursor()
    c.execute('SELECT remaining_uses FROM lven_agent_pairing_keys WHERE key = ?', (pairing_key,))
    row = c.fetchone()
    if row is None:
        raise LVENPairingKeyDoesNotExist(f"LVEN Pairing key '{pairing_key}' does not exist")
    if row['remaining_uses'] is None:
        return
    c.execute('UPDATE lven_agent_pairing_keys SET remaining_uses = remaining_uses - 1 WHERE key = ?', (pairing_key,))
    db.commit()
