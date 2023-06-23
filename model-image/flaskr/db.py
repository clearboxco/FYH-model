import sqlite3 # TO DELETE

import psycopg2

import click
from flask import current_app,g

def get_db():
    if 'db' not in g:
        print(current_app.config)
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
        
@click.command('init-db')
def init_db_command():
    get_db() # Connect to the database
    click.echo('Initialized the database.')
    
    
    # ISSUE SEEMS TO BE CANNOT LOCATE DB, AS IT IS A VALID DB
    
    
def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    
    
