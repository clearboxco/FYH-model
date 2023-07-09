import functools
import os
import json

from .db import get_db

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)

from werkzeug.security import check_password_hash, generate_password_hash

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError




bp = Blueprint('auth',__name__,url_prefix='/auth')

@bp.route('/register',methods=['POST'])
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
        trans=db.begin()
        try:
            with open(os.path.join(current_app.instance_path,'scripts','insert.sql')) as f:
                insert_sql=f.read()
                
            db.execute(text(insert_sql),{'value1':username,'value2':generate_password_hash(password)},trans=trans)
            trans.commit()
        except IntegrityError:
            trans.rollback()
            error = f"User {username} is already registered."

    
    return json.dumps({"error":error})
        
        
        
@bp.route('/login',methods=['POST'])
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
        g.user = get_db().execute(text(get_confirmed_user_sql),{'value1':user_id}).fetchone()
        
        
@bp.route('/logout')
def logout():
    session.clear()
    
        