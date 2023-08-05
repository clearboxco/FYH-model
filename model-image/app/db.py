from sqlalchemy import create_engine,URL,Row

from flask import current_app,g


from sqlalchemy.ext.declarative import declarative_base

def get_db():
    if 'db' not in g:
        url=URL.create(
            drivername="postgresql+psycopg2",
            host=current_app.config['ENDPOINT'],
            database=current_app.config['DBNAME'],
            username=current_app.config['USER'],
            password=current_app.config['PASS'],
            port=current_app.config['PORT']
        )
        
        g.db=create_engine(url).connect()
        g.db.row_factory=Row
        
    return g.db


def close_db(e=None):
    db = g.pop('db',None)
    
    if db is not None:
        db.close()
    
    
def init_app(app):
    app.teardown_appcontext(close_db)
    # app.cli.add_command(init_db_command)
    
