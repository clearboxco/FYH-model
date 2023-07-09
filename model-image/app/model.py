import json
import os

import pandas as pd
import numpy as np

from flask import Blueprint, request, current_app
from .db import get_db
from sqlalchemy import text

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.neighbors import NearestNeighbors

from scipy.spatial.distance import euclidean
from scipy.stats import norm



# NEED TO SETUP POSTER LOGGING AND SEND TO DB FOR USER INFO


bp = Blueprint('fyh-model',__name__,url_prefix='/fyh-model')

@bp.route('/post', methods=['POST'])
def post_endpoint():
    
    # PART 1: READ IN JSON DATA
    input_data = request.get_json(force=True)
    
    submission_type=input_data['submission_type']
    
    filters=input_data['filters']

    price_max=filters['price']['max']
    price_min=filters['price']['min']
    
    property_type=filters["property_type"]
    
    state=filters['location']['state']
    city=filters['location']['city']
    zip=filters['location']['zip']
    
    year_built_max=filters['year_built']['max']
    year_built_min=filters['year_built']['min']


    data=input_data['data']
    
    bedrooms=data['bedrooms']
    bathrooms=data['bathrooms']
    sqft=data['sqft']

# PART 2: CONFIGURE MODEL SETTINGS

    def configure_model_weights(submission_type,bds,bas,sqft):
        bd_weight=1
        ba_weight=1
        sqft_weight=1
        
        #Proper Submit w/ no value
        if submission_type==2:
            if bds==0:
                bd_weight=0
            if bas==0:
                ba_weight=0
            if sqft==0:
                sqft_weight=0
                
        return np.array([bd_weight,ba_weight,sqft_weight])

    model_weights=configure_model_weights(submission_type,bedrooms,bathrooms,sqft)
    
    
    with open(os.path.join(current_app.instance_path,'scripts','tables.txt'),'r') as f:
        lines=f.readlines()
    
    sql_tables=[str(line.strip()) for line in lines]
    
    with open(os.path.join(current_app.instance_path,'scripts','columns.txt'),'r') as f:
        lines=f.readlines()
    
    sql_columns=[str(line.strip()) for line in lines]
    
    
# PART 3: STREAM DATA
    
    execution_vars=[]
    execution_string=f'SELECT * FROM {sql_tables[2]} WHERE('
    
    execution_string+=f'"{sql_columns[25]}" < {price_max} AND "{sql_columns[25]}" > {price_min}'
    execution_string+=" AND "
    execution_vars.append(price_max)
    execution_vars.append(price_min)
    
    property_type_logic={
        1:"'Single Family Residential'",
        2:"'Multi-Family (2-4 Unit)'",
        3:"'Multi-Family (5+ Unit)'",
        4:"'Townhouse'",
        5:"'Condo/Co-op'",
        6:"'Mobile/Manufactured Home'",
    }
    
    execution_string+=f'{sql_columns[13]} = {property_type_logic[property_type]}'
    execution_string+=" AND "
    execution_vars.append(property_type_logic[property_type])
    
    execution_string+=f'"{sql_columns[26]}" < {year_built_max} AND "{sql_columns[26]}" > {year_built_min}'
    execution_vars.append(year_built_max)
    execution_vars.append(year_built_min)
    
    if (state!="" and state is not None):
        execution_string+=' AND '
        execution_string+=f'"{sql_columns[16]}" = \'{state.upper()}\''
        execution_vars.append(state.upper())
        
    if (city!="" and city is not None):
        execution_string+=' AND '
        execution_string+=f'"{sql_columns[15]}" = \'{city.capitalize()}\''
        execution_vars.append(city.capitalize())
        
    if (zip!="" and zip is not None):
        execution_string+=' AND '
        execution_string+=f'"{sql_columns[24]}" = {zip}'
        execution_vars.append(zip)

    execution_string+=');'
    
    db=get_db()

# PART 4: PREPROCESS STREAMED DATA

    #convert to df
    df=pd.read_sql_query(text(execution_string),db)
    
    # Alter to potential use values based on normal disribution of values

    #I'm Feeling Lucky

    random_state=np.random.randint(0,999)
    
    if submission_type==1:
        np.random.seed(random_state)
        if bedrooms==0:
            bedrooms_probabilities=df[sql_columns[0]].value_counts(normalize=True)
            bedrooms=np.random.choice(bedrooms_probabilities.index,p=bedrooms_probabilities.values)
        if bathrooms==0:
            bathrooms_probabilities=df[sql_columns[1]].value_counts(normalize=True)
            bathrooms=np.random.choice(bathrooms_probabilities.index,p=bathrooms_probabilities.values)
        if sqft==0:
            sqft_probabilities=df[sql_columns[3]].value_counts(normalize=True)
            sqft=np.random.choice(sqft_probabilities.index,p=sqft_probabilities.values)
            
            
            
            


    sampled_df=df.sample(frac=1, replace=False, random_state=random_state)
    
    NN_df=sampled_df[[f'{sql_columns[0]}',f'{sql_columns[1]}',f'{sql_columns[3]}']]
    
    input_df=pd.DataFrame({f'{sql_columns[0]}':[bedrooms],f'{sql_columns[1]}':[bathrooms],f'{sql_columns[3]}':[sqft]})
        
    # Define the transformations for each column
    preprocessor = ColumnTransformer(
    transformers=[
        ('minmax_scaler',MinMaxScaler(),[f'{sql_columns[0]}',f'{sql_columns[1]}',f'{sql_columns[3]}'])
    ])

    # Apply the transformations in a pipeline
    pipeline = Pipeline(steps=[('preprocessor', preprocessor)])

    NN_np=pipeline.fit_transform(NN_df)
    input_np=pipeline.transform(input_df)
        



# PART 5: RUN MODEL

    def weighted_euclidian(x,y,weights=model_weights):
        
        return euclidean(x,y,weights)


    knn=NearestNeighbors(n_neighbors=NN_np.shape[0],metric=weighted_euclidian)
    knn.fit(NN_np)
    
    distances, indices = knn.kneighbors(input_np)


    def get_top(df,indices) -> pd.DataFrame:
        top=15
        
        if indices[0].shape[0]<top:
            top=indices[0].shape[0]
            
        return df.iloc[indices[0][0:top]]
            
    
    
    result_df=get_top(sampled_df,indices)

# PART 6: POST MODEL DATA

    def prepare_model_json(df:pd.DataFrame) ->list[dict]:
        lst=[]
        
        jsn=df.to_json(orient='records')
        parsed=json.loads(jsn)
        
        for li in parsed:
            h={
                "time_stamp":li[sql_columns[11]],
                "url":li[sql_columns[22]],
                "price":li[sql_columns[25]],
                "bedrooms":li[f"{sql_columns[0]}"],
                "bathrooms":li[f"{sql_columns[1]}"],
                "sqft":li[f"{sql_columns[3]}"],
                "year_built":li[sql_columns[26]],
                "address":li[sql_columns[14]],
                "state":li[sql_columns[16]],
                "city":li[sql_columns[15]],
                "zip":li[sql_columns[24]],
                "openHouse_st":li[sql_columns[20]],
                "openHouse_et":li[sql_columns[21]],
                "HOA/month":li[sql_columns[18]],
                "days_on_market":li[sql_columns[27]],
                "price_per_sqft":li[sql_columns[17]]     
            }
        
            lst.append(h)
            h={}
            
        return lst

    output={
        "user":input_data["user"],
        "date":"",
        "model":"FYH",
        "random_state":random_state,
        "data":prepare_model_json(result_df)
    }
    
    with open('../output.json','w') as f:
        json.dump(output,f,indent=4)

    
    return '',204 # No Content; Valid Return
    
    
    
    