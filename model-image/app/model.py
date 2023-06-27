import json
import os

import pandas as pd
import numpy as np
import random

from flask import Blueprint, request
from flaskr.db import get_db

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
            deviation=random.randint(0,1,2)
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
    
    execution_string+='"PRICE" < ? AND "PRICE" > ?'
    execution_string+=" AND "
    execution_vars.append(price_max)
    execution_vars.append(price_min)
    
    property_type_logic={
        1:"Single Family Residential",
        2:"Multi-Family (2-4 Unit)",
        3:"Multi-Family (5+ Unit)",
        4:"Townhouse",
        5:"Condo/Co-op",
        6:"Mobile/Manufactured Home",
    }
    
    execution_string+='"PROPERTY TYPE" = ?'
    execution_string+=" AND "
    execution_vars.append(property_type_logic[property_type])
    
    execution_string+='"YEAR BULT" < ? AND "YEAR BUILT" > ?'
    execution_vars.append(year_built_max)
    execution_vars.append(year_built_min)
    
    if (state!="" or state is not None):
        execution_string+=' AND '
        execution_string+='"STATE OR PROVINCE" = ?'
        execution_vars.append(state)
        
    if (city!="" or city is not None):
        execution_string+=' AND '
        execution_string+='"CITY" = ?'
        execution_vars.append(city)
        
    if (zip!="" or zip is not None):
        execution_string+=' AND '
        execution_string+='"ZIP OR POSTAL CODE" = ?'
        execution_vars.append(zip)

    execution_string+=');'
    
    db=get_db()
    db_output=db.execute(execution_string,tuple(execution_vars))

# PART 3: PREPROCESS STREAMED DATA

    #convert to df
    df=pd.read_sql(db_output)
    
    random_state=random.randint(0,999)

    NN_df=df.sample(frac=1, replace=False, random_state=random_state)
    
    
    NN_df=NN_df[['BEDS','BATHS','SQUARE FEET']]
    input_df=pd.Dataframe({'BEDS':[bedrooms],'BATHS':[bathrooms],'SQUARE FEET':[sqft]})
        
    # Define the transformations for each column
    preprocessor = ColumnTransformer(
    transformers=[
        ('minmax_scaler',MinMaxScaler(),['BEDS','BATHS','SQUARE FEET'])
    ])

    # Apply the transformations in a pipeline
    pipeline = Pipeline(steps=[('preprocessor', preprocessor)])

    NN_np=pipeline.fit_transform(df)
    input_np=pipeline.transform(input_df)
        



    # PART 4: RUN MODEL

    def weighted_euclidian(x,y,weights=model_weights):
        
        return euclidean(x,y,weights)


    knn=NearestNeighbors(n_neighbors=NN_np.shape[0],metric=weighted_euclidian)
    knn.fit(data)
    
    distances, indices = knn.kneighbors(input_np)


    def get_top(indices) -> pd.DataFrame:
        df_list=[]
        
        c=0
        for index in indices[0]:
            if c>6:
                break
            
            df_list.append(df.loc[index])
            
            c+=1
            
        return pd.concat(df_list)
    
    
    result_df=get_top(indices)

# PART 5: POST MODEL DATA

    def prepare_model_json(df) ->list[dict]:
        lst=[]
        
        jsn=df.to_json(orient='records')
        parsed=json.load(jsn)
        
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
    
    with open('output.json','w') as f:
        json.dump(output,f)

    

    
    
    
    