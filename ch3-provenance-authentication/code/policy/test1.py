import pandas as pd
import random

data = pd.read_excel('data_for_train.xlsx') 
print(data.head())
for i in range(0,4):
    data = data.drop(['Unnamed: '+str(i)], axis=1)
for i in range(12,18):
    data = data.drop(['Unnamed: '+str(i)], axis=1)
print(data.head())
# with open("datafile.txt", "rb") as f:
#     data = f.read().split('\n')
# random.shuffle(data)

# train_data = data[:50]
# test_data = data[50:]