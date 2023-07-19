import os

from flask import Flask,url_for
from flask_session import Session
from flask_cors import CORS, cross_origin

def create_app(test_config=None):
    # create and configure the app
    appl = Flask(__name__, instance_relative_config=True)
    """
    app.config.from_mapping(
        SECRET_KEY='dev', # SECRET KEYS IN PUBLISHED APPS IS STUPID; wiLL OS.GETNV
        DATABASE=os.path.join(app.instance_path, 'fyh-database.db'),
    )
    """
    
    # ensure the instance folder exists
    try:
        os.makedirs(appl.instance_path)
    except OSError:
        pass

    if test_config is None:
        # load the instance config, if it exists, when not testing
        appl.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        appl.config.from_mapping(test_config)
    
    Session(appl)

    #registering dependencies
    from . import db
    from . import celery_setup as cs
    db.init_app(appl)
    cs.celery_init_app(appl) # Could not get celery to work for windows... ugh

    with appl.app_context():        
        # registering blueprints
        from . import auth
        from . import model
        from . import data
        appl.register_blueprint(auth.bp)
        appl.register_blueprint(model.bp)
        appl.register_blueprint(data.bp)



    
    return appl

if __name__ == "__main__":
    app=create_app()
    app.run(debug=True)
    
