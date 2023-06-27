import sqlite3 # TO DELETE

import psycopg2

import click
from flask import current_app,g

def get_db():
    if 'db' not in g:
        g.db=sqlite3.connect( # REPLACE WITH PSYCOPG2 EQUIVALENT
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory=sqlite3.Row
        
    return g.db


def close_db(e=None):
    db = g.pop('db',None)
    
    if db is not None:
        db.close()
        
    
    
def init_app(app):
    app.teardown_appcontext(close_db)
    # app.cli.add_command(init_db_command)
    
    
