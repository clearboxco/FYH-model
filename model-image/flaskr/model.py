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

# PART 2: CONFIGURE MODEL SETTINGS
    def configure_model_weights(submission_type,bds,bas,sqft):
        bd_weight=1
        ba_weight=1
        sqft_weight=1
        
        if submission_type==2:
            if bds==0:
                bd_weight=0
            if bas==0:
                ba_weight=0
            if sqft==0:
                sqft_weight=0
                
        return np.array([bd_weight,ba_weight,sqft_weight])

    weights=configure_model_weights(submission_type,bedrooms,bathrooms,sqft)
    
    # CONTINUE HERE!!!!!!!!!!!!!!!!!!!!!!!!!

# PART 3: PREPROCESS STREAMED DATA

def shuffle_data(df:pd.DataFrame):
    random_state=random.randint(0,999)
    
    df.sample(frac=1, replace=False, random_state=random_state)
    
    return random_state

def preprocess_data():
    NN_df=df[['BEDS','BATHS','SQUARE FEET']]
    input_df=pd.Dataframe({'BEDS':[bedrooms],'BATHS':[bathrooms],'SQUARE FEET':[sqft]})
    
    # Define the transformations for each column
    preprocessor = ColumnTransformer(
    transformers=[
        ('minmax_scaler',MinMaxScaler(),['BEDS','BATHS','SQUARE FEET'])
    ])

    # Apply the transformations in a pipeline
    pipeline = Pipeline(steps=[('preprocessor', preprocessor)])

    NN_np=pipeline.fit_transform(NN_df)
    input_np=pipeline.transform(input_df)
    
    
    return NN_np


# PART 4: RUN MODEL

def weighted_euclidian(x,y):
    weights=np.array(bd_weight,ba_weight,sqft_weight)
    
    return euclidean

def create_model(input,data:np.array):
    knn=NearestNeighbors(n_neighbors=data.shape[0],metric=weighted_euclidian)
    knn.fit(data)
    
    distances, indices = knn.kneighbors(input)
    
    return distances, indices


def get_top(indices) -> pd.DataFrame:
    df_list=[]
    
    c=0
    for index in indices[0]:
        if c>6:
            break
        
        df_list.append(df.loc[index])
        
        c+=1
        
    return pd.concat(df_list)
        
        
        
    


# PART 5: POST MODEL DATA

def prepare_json():
    