import pandas as pd 
import os, fnmatch

# Init empty DataFrame for loading data
bts_df = pd.DataFrame()

# Read list of files in raw_data folder
listOfFiles = os.listdir('./raw_data')
# Take only .csv file
pattern = "*.csv"

# Load raw data to DataFrame
for files in listOfFiles:
    if fnmatch.fnmatch(files, pattern):
        cur_df = pd.read_csv("./raw_data/{}".format(files))
        bts_df = bts_df.append(cur_df)

# Convert time from unix timestamp to integer
bts_df["unix_timestamp"] = pd.to_datetime(bts_df["reading_time"]).astype(int)

# Normalize timestamp data
mean_time = bts_df["unix_timestamp"].mean()
min_time = bts_df["unix_timestamp"].min()
bts_df["norm_time"] = (bts_df["unix_timestamp"]-mean_time)/(3600*1000000000)

# Sort data and remove unnecessary features 
bts_df = bts_df.sort_values(by=['norm_time'])
bts_df.drop(["reading_time"], axis='columns', inplace=True)

# Group data by station ID and parameter ID
# -> making prediction on individual parameters for each station
bts_df_grouped = bts_df.groupby(["station_id","parameter_id"])

# Processing grouped data
for key,item in bts_df_grouped:
    sub_data = bts_df_grouped.get_group(key)
    # Normalize value in each group
    mean_val = sub_data['value'].mean()
    sub_data['norm_value'] = sub_data['value']-mean_val
    max_val = sub_data['norm_value'].max()
    sub_data['norm_value'] = sub_data['norm_value']/max_val
    sub_data.sort_values(by=['norm_time']).to_csv("./data_grouped/{}_{}_.csv".format(key[0],key[1]), index=False)
    print("Finish: {}".format(key))
