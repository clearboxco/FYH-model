import json
import os

import pandas as pd
import numpy as np
import random

from flask import Blueprint, request
from .db import get_db

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler
from sklearn.neighbors import NearestNeighbors

from scipy.spatial.distance import euclidean



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


    #I'm Feeling Lucky
    if submission_type==1:
        if bedrooms==0:
            bedrooms=random.randint(2,9)
        if bathrooms==0:
            deviation=random.randint(0,2)
            if random.randint(0,1) % 2 ==0:
                bathrooms=bedrooms+deviation
            else:
                bathrooms=bedrooms-deviation
            if bathrooms<1:
                bathrooms=1
        if sqft==0:
            sqft=random.randint(450,10000)

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
    
    
# PART 3: STREAM DATA
    
    execution_vars=[]
    execution_string='SELECT * FROM houses WHERE('
    
    execution_string+=f'"PRICE" < {price_max} AND "PRICE" > {price_min}'
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
    
    execution_string+=f'"PROPERTY TYPE" = {property_type_logic[property_type]}'
    execution_string+=" AND "
    execution_vars.append(property_type_logic[property_type])
    
    execution_string+=f'"YEAR BUILT" < {year_built_max} AND "YEAR BUILT" > {year_built_min}'
    execution_vars.append(year_built_max)
    execution_vars.append(year_built_min)
    
    if (state!="" and state is not None):
        execution_string+=' AND '
        execution_string+=f'"STATE OR PROVINCE" = \'{state.upper()}\''
        execution_vars.append(state.upper())
        
    if (city!="" and city is not None):
        execution_string+=' AND '
        execution_string+=f'"CITY" = \'{city.capitalize()}\''
        execution_vars.append(city.capitalize())
        
    if (zip!="" and zip is not None):
        execution_string+=' AND '
        execution_string+=f'"ZIP OR POSTAL CODE" = {zip}'
        execution_vars.append(zip)

    execution_string+=');'
    
    db=get_db()

# PART 3: PREPROCESS STREAMED DATA

    #convert to df
    df=pd.read_sql_query(execution_string,db)
    
    random_state=random.randint(0,999)

    sampled_df=df.sample(frac=1, replace=False, random_state=random_state)
    
    NN_df=sampled_df[['BEDS','BATHS','SQUARE FEET']]
    
    input_df=pd.DataFrame({'BEDS':[bedrooms],'BATHS':[bathrooms],'SQUARE FEET':[sqft]})
        
    # Define the transformations for each column
    preprocessor = ColumnTransformer(
    transformers=[
        ('minmax_scaler',MinMaxScaler(),['BEDS','BATHS','SQUARE FEET'])
    ])

    # Apply the transformations in a pipeline
    pipeline = Pipeline(steps=[('preprocessor', preprocessor)])

    NN_np=pipeline.fit_transform(NN_df)
    input_np=pipeline.transform(input_df)
        



    # PART 4: RUN MODEL

    def weighted_euclidian(x,y,weights=model_weights):
        
        return euclidean(x,y,weights)


    knn=NearestNeighbors(n_neighbors=NN_np.shape[0],metric=weighted_euclidian)
    knn.fit(NN_np)
    
    distances, indices = knn.kneighbors(input_np)


    def get_top(df,indices) -> pd.DataFrame:
        top=6
        
        if indices[0].shape[0]<6:
            top=indices[0].shape[0]
            
        return df.iloc[indices[0][0:top]]
            
    
    
    result_df=get_top(sampled_df,indices)

# PART 5: POST MODEL DATA

    def prepare_model_json(df:pd.DataFrame) ->list[dict]:
        lst=[]
        
        jsn=df.to_json(orient='records')
        parsed=json.loads(jsn)
        
        for li in parsed:
            h={
                "url":li["URL (SEE https://www.redfin.com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)"],
                "price":li["PRICE"],
                "bedrooms":li["BEDS"],
                "bathrooms":li["BATHS"],
                "sqft":li["SQUARE FEET"],
                "year_built":li["YEAR BUILT"],
                "address":li["ADDRESS"],
                "state":li["STATE OR PROVINCE"],
                "city":li["CITY"],
                "zip":li["ZIP OR POSTAL CODE"],
                "openHouse_st":li["NEXT OPEN HOUSE START TIME"],
                "openHouse_et":li["NEXT OPEN HOUSE END TIME"],
                "HOA/month":li["HOA/MONTH"],
                "days_on_market":li["DAYS ON MARKET"]     
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
    
    
    
    