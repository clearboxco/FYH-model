import functools
import os
import json

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)


from werkzeug.security import check_password_hash, generate_password_hash

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from .db import get_db


bp = Blueprint('auth',__name__,url_prefix='/auth')

@bp.route('/register',methods=['GET','POST'])
def register():
    post=request.get_json(force=True)
    
    username=post['username']
    password=post['password']
    
    db=get_db()
    error=None
    
    if not username:
        error = 'Username is required.'
    elif not username:
        error='Password is required.'
            
    if error is None:
        try:
            with open(os.path.join(current_app.instance_path,'scripts','insert_user.sql')) as f:
                insert_user_sql=f.read()
                
            db.execute(text(insert_user_sql),{'value1':username,'value2':generate_password_hash(password)})
            db.commit()
        except IntegrityError:
            db.rollback()
            error = f"User {username} is already registered."

    
    return json.dumps({"error":error})
        
        
        
@bp.route('/login',methods=['GET','POST'])
def login():
    
    post=request.get_json(force=True)
    
    username=post['username']
    password=post['password']
    
    db=get_db()
    error = None
    
    with open(os.path.join(current_app.instance_path,'scripts','select_user.sql')) as f:
                select_user_sql=f.read()
    
    user = db.execute(text(select_user_sql),{'value1':username}).fetchone()
    
    if user is None:
        error = 'Incorrect username.'
    elif not check_password_hash(user[2],password):
        error='Incorrect password.'

    if error is None:
        session.clear()
        session['user_id']=user[0]
        
    return json.dumps({"error":error})
        
        
@bp.before_app_request
def load_logged_in_user():
    user_id=session.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        with open(os.path.join(current_app.instance_path,'scripts','get_confirmed_user.sql')) as f:
            get_confirmed_user_sql=f.read()
        g.user = get_db().execute(text(get_confirmed_user_sql),{'value1':int(user_id)}).fetchone()
        
        
@bp.route('/logout',methods=['GET'])
def logout():
    session.clear()
    return ''
    
    
    
@bp.route('/reset',methods=['POST'])
def reset_password():
    pass
    
    


@bp.route('/update',methods=['POST'])
def change_password():
    error=None
    
    if g.user is not None:
        
        post=request.get_json(force=True)
        password=post['password']
        
        with open(os.path.join(current_app.instance_path,'scripts','update_password.sql')) as f:
            update_password_sql=f.read()
            
        db=get_db()
        
        try:
            db.execute(text(update_password_sql),{'value1':generate_password_hash(password),'value2':g.user[0]})
            db.commit()
        except IntegrityError:
            db.rollback()
    else:
        error="Invalid request."       
            
    json.dumps({"error":error})
    

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return None
        
        return view(**kwargs)
    
    return wrapped_view

    
    
            
            
        