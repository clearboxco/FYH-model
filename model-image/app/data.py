import os
import json

from flask import Blueprint, request, current_app, g, url_for,jsonify
from . import db
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from flask_login import login_required,current_user


bp=Blueprint("data",__name__,url_prefix="/data")


@bp.route("/claps",methods=['GET','POST'])
def access_claps():

    error=None
    output={"error":error}

    sess=db.session
    
    if request.method=='POST':
        post=request.get_json(force=True)
        claps=post['claps']
        
        try:
            with open(os.path.join(current_app.instance_path,'scripts','post_claps.sql')) as f:
                post_claps_sql=f.read()
                
            sess.execute(text(post_claps_sql),{'value1':int(claps)})
            sess.commit()
        except:
            sess.rollback()
            error='Failed to insert claps.'
        
    
    else:
        try:
            with open(os.path.join(current_app.instance_path,'scripts','get_claps.sql')) as f:
                get_claps_sql=f.read()
            claps=sess.execute(text(get_claps_sql)).fetchone()
        except:
            error='Could not fetch claps.'
        
        output['claps']=claps[0]
    
    output['error']=error
    
    return jsonify(output)
                    
                    
        
@bp.route('/searches',methods=['GET','POST'])
@login_required
def get_searches_input():
    
    error=None
    output={'error':error}

    sess=db.session

    if request.method=='POST':
        input_data=request.get_json(force=True)
        
        with open(os.path.join(current_app.instance_path,'scripts','get_searches_output.sql')) as f:
            get_searches_output_sql=f.read()
        
        try:
            value_dict={'value1':int(input_data['s_id'])}
            
            rows=sess.execute(text(get_searches_output_sql),value_dict).fetchall()
            
            records=[]
            
            for row in rows:
                records.append({
                    "s_id":str(row[0]),
                    "h_id":str(row[1]),
                    "time_stamp":str(row[3]),
                    "url":str(row[23]),
                    "price":str(row[10]),
                    "bedrooms":str(row[11]),
                    "bathrooms":str(row[12]),
                    "sqft":str(row[14]),
                    "year_built":str(row[16]),
                    "address":str(row[6]),
                    "state":str(row[8]),
                    "city":str(row[7]),
                    "zip":str(row[9]),
                    "openHouse_st":str(row[21]),
                    "openHouse_et":str(row[22]),
                    "HOA/month":str(row[19]),
                    "days_on_market":str(row[17]),
                    "price_per_sqft":str(row[18]),
                    "rank":str(row[30])   
                })
                
            output['data']=records
        
        except Exception as e:
            error=str(e)
        

    else:
        with open(os.path.join(current_app.instance_path,'scripts','get_searches_input.sql')) as f:
            get_searches_input_sql=f.read()
            
        sess=db.session
        
        try:
            value_dict={'value1':int(current_user.user_id),"value2":current_app.config['NUM_SEARCHES_RETURNED']}
            
            rows=sess.execute(text(get_searches_input_sql),value_dict).fetchall()
            
            records=[]
            
            for row in rows:
                records.append({
                    "s_id":str(row[0]),
                    "time_stamp":str(row[1]),
                    "submission_type":str(row[2]),
                    "city":str(row[3]),
                    "state":str(row[4]),
                    "zip":str(row[5]),
                    "price_max":str(row[6]),
                    "price_min":str(row[7]),
                    "bedrooms":str(row[8]),
                    "bathrooms":str(row[9]),
                    "sqft":str(row[10]),
                    "property_type":str(row[11]),
                    "year_built_max":str(row[12]),
                    "year_built_min":str(row[13]),
                    "u_id":str(row[14]),
                    "rank":str(row[15])
                })
                
            output['data']=records
            
        except Exception as e:
            error=str(e)
        
    output['error']=error
    
    return jsonify(output)

    
    