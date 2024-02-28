import sqlite3
import os
import mpip_libs.runtime_env as runtime_env
import logging
import random
import time
from typing import TypedDict, Optional

database_structure_file_path = os.path.dirname(__file__) + '/database.sql'
def database_file_path() -> str:
    return runtime_env.settings_persistent_directory + '/mpip.sqlite3'


def init(create_database_if_not_exists: bool = False):

    # create the database if it doesn't exist
    if not os.path.exists(database_file_path()):
        if create_database_if_not_exists:
            create_database()
        else:
            raise FileNotFoundError(f"The database file {database_file_path()} does not exist.")

    # connect to the database
    conn = sqlite3.connect(database_file_path())

    logging.info('Database connection established')

def new_connection():
    conn = sqlite3.connect(database_file_path())
    conn.row_factory = sqlite3.Row
    return conn

def create_database():
    # create the database
    global conn

    # if the database already exists, do nothing
    if os.path.exists(database_file_path()):
        logging.warning('Database already exists')
        return

    logging.info('Creating database %s', database_file_path())
    conn = sqlite3.connect(database_file_path())
    c = conn.cursor()
    # database structure is defined in database.sql
    with open(database_structure_file_path, 'r') as file:
        c.executescript(file.read())
    conn.commit()
    conn.close()


def database_exists() -> bool:
    return os.path.exists(database_file_path())





