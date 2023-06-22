# TEMPORARY STREAM IN DATA TO GENERATE LOCAL CSV

# WILL BE DEPRECATED IN FINAL MODEL

import os
import sys

import pandas as pd
import numpy as np

from sqlalchemy import create_engine

aws_bucket=os.getenv('AWS_RE_BUCKET')
aws_key=os.getenv('AWS_RE_BUCKET_KEY')
aws_secret=os.getenv('AWS_RE_BUCKET_SECRET')

date=str(sys.argv[1])
state="CA"
states=['AL',
 'NE',
 'AK',
 'NV',
 'AZ',
 'NH',
 'AR',
 'NJ',
 'CA',
 'NM',
 'CO',
 'NY',
 'CT',
 'NC',
 'DE',
 'ND',
 'DC',
 'OH',
 'FL',
 'OK',
 'GA',
 'OR',
 'HI',
 'PA',
 'ID',
 'PR',
 'IL',
 'RI',
 'IN',
 'SC',
 'IA',
 'SD',
 'KS',
 'TN',
 'KY',
 'TX',
 'LA',
 'UT',
 'ME',
 'VT',
 'MD',
 'VA',
 'MA',
 'VI',
 'MI',
 'WA',
 'MN',
 'WV',
 'MS',
 'WI',
 'MO',
 'WY',
 'MT',
]

df_list=[]
for st in states:
    try:
        df = pd.read_parquet(path=aws_bucket+f"/{date}/{st}.parquet",storage_options={"key":aws_key,"secret":aws_secret})
        df_list.append(df)
    except:
        pass
    
df=pd.concat(df_list)

df=df.applymap(lambda x: np.nan if x=='nan' else x)

prop_types=['Single Family Residential', 'Mobile/Manufactured Home','Townhouse', 'Multi-Family (2-4 Unit)', 'Condo/Co-op','Multi-Family (5+ Unit)']

df=df[df['PROPERTY TYPE'].isin(prop_types)]

df=df.dropna(subset=['ADDRESS','CITY','STATE OR PROVINCE','ZIP OR POSTAL CODE','PROPERTY TYPE','PRICE','BEDS','BATHS','SQUARE FEET','YEAR BUILT','URL (SEE https://www.redfin.com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)'],axis=0).reset_index(drop=True).apply(lambda row: pd.to_numeric(row,errors='ignore'))

engine = create_engine("sqlite:///C:\\Users\\rsher\\Documents\\Projects\\PriceYourHome\\model-public\\model-image\\instance\\fyh-database.db")

df.to_sql("houses",engine)