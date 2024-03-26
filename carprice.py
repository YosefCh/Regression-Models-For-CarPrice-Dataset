# -*- coding: utf-8 -*-
"""CarPrice.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1xvAYE8GceD5rqHw0-moMUYK7DXIRsOSn
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.model_selection import cross_val_predict
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import seaborn as sns

df = pd.read_csv('CarPrice_Assignment.csv')

# this allows us to see all the columns
pd.set_option('display.max_columns', None)
df

# drop the ID column which will confuse the model
df = df.drop('car_ID', axis=1)

"""__The red boxes near some features are of no significance.__


![Car_Index.png](attachment:Car_Index.png)

# Things to consider:

1) When eyeballing the dataset I discovered that some columns are really numeric but for some reason had the numbers written as text. This can be fixed by manually changing them to numbers or by using one_hot_encoding. It is probably better to change to numbers since the values have order and aren't simply different categories as would be the case if we used one hot encoding.

2) The name column which has 147 different values so using encoding would give us an enormous amount of features so we will apply basic categories of luxury, midsize, compact car etc..., in place of the names.

3) Normalize df if necesarry.
"""

df.info()

"""__Get unique values of columns that label numbers as words. These will be changed to numeric values using a map function__"""

door_num = df['doornumber'].unique()
cylndr_num = df['cylindernumber'].unique()
print(door_num, '\n', cylndr_num)

"""__Once values are known, create dict with those values to use with map__"""

# in pandas the map works even without a function applied to each value.
door_cylinder_dict = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'eight': 8, 'twelve': 12}
df['doornumber'] = df['doornumber'].map(door_cylinder_dict)
df['cylindernumber'] = df['cylindernumber'].map(door_cylinder_dict)
df

"""__Drive Wheel column has four wheel drive as 'fwd' and '4wd'. We will change those to one value__"""

drive_dict = {'rwd': 'rwd', 'fwd': 'fwd', '4wd': 'fwd'}
df['drivewheel'] = df['drivewheel'].map(drive_dict)
df['drivewheel'].unique()

"""__Modify the df by removing the CarName column which has too many unique values to use with one_hot_encoding and assign general ratings in place of make and model.__"""

# the apply function is similar to map, but is used for a pandas column. The [0] is to stop after the first occurence of the delimiter (here a space, which is after
# the company name since that is what we will be using for the rating.)
df['C'] = df['CarName'].apply(lambda x: x.split(' ')[0])

# get unique names as keys for a dict to store rating for each company
companies = df['C'].unique()

# start with an empty value for each key (company)
rating_dict = {}
for i in companies:
  rating_dict[i] = None

# lists for ratings
lux = ['jaguar', 'porsche', 'porcshce', 'audi', 'alfa-romero', 'volvo', 'bmw']
# spelling mistakes and doubles are the way the data was entered
mid = ['chevrolet', 'saab', 'dodge', 'toyota', 'toyouta', 'volkswagen', 'vokswagen', 'vw', 'maxda', 'mazda', 'honda', 'Nissan', 'nissan', 'buick', 'subaru']
# the remaining names are economy

for i in rating_dict:
  if i in lux:
    rating_dict[i] = 4
  elif i in mid:
    rating_dict[i] = 2
  else:
    rating_dict[i] = 1

df['Class'] = df['C'].map(rating_dict)
df = df.drop(['CarName', 'C'], axis=1)
df

df.info()

"""## __Encoding__

__Encode the dataset with Boolean (dummy) values.__
"""

for col in df.columns:

# if the column is not numeric (integer or float)
    if df[col].dtype == 'object':
        df = pd.get_dummies(df, columns=[col], prefix='is')

"""### __We will transform the data with scaling to get a feel for which features are closely correlated with 'price'.__

__Two notes of caution:__

__1:__ We are naming this __df_encoded__ to differentiate between the original df. This is becuase df_encoded is scaled completely meaning every row of the dataset is scaled. This can cause a problem known as __data leakage__ which occurs when running a model on a dataset and the test data has already been scaled to the training data. This effectively gives the model a sneak preview of the test data which makes the scoring of the model a lot less reliable to extrapolate to how the model will perform on other data.

(One can wonder that maybe on the contrary every time we run the model we should retrain it with the test data, however, in a real-world scenario, you won’t have access to future data when you’re training your model. The goal is to build a model that can make accurate predictions on future data based on the patterns it learned from the past data (training set). If you constantly retrain your model with the test data, you’re assuming that you’ll always have access to future data when making predictions, which is not the case.) Therefore we will use the original __df__ when running the models.

__2:__ The heatmaps show correlation but not causation so it isn't a certainty that the results are entirely accurate. So we will try to run the models at first with the features which seem closely correlated and then with all features.
"""

scaler = MinMaxScaler()

# in pandas the copy function is like a DEEP COPY and changes made to the copy will not affect the original
df_encoded = df.copy()
for col in df_encoded.columns:

# we will exclude the columns that are dummies since once they were transformed to True and False they are equivalent to 0 and 1, so they will be considered
# like an int.
     if col[:2] != 'is':
        df_encoded[col] = scaler.fit_transform(df_encoded[[col]])

df_encoded

correlation_matrix = df_encoded.corr()

# You can adjust the size as needed. A large size is neede to see this heatmap.
plt.figure(figsize=(25, 25))
sns.heatmap(correlation_matrix, annot=True, fmt=".1f", cmap='coolwarm')

# move x-axis labels to top
plt.gca().xaxis.tick_top()

# rotate x-axis labels for readability
plt.xticks(rotation=90)
plt.show()

"""## __Creating heatmaps of squared and cubed values__

Perhaps the correlation will be differnt when squared or cubed.

We are not including the True/False columns since they will be unaffected by the squaring and cubing.
"""

# Create new DataFrames for squared and cubed values
df_squared = pd.DataFrame()
df_cubed = pd.DataFrame()

for col in df.columns:
    if col[:2] != 'is' and col != 'price':
        df_squared[col + '_squared'] = df_encoded[col] ** 2
        df_cubed[col + '_cubed'] = df_encoded[col] ** 3

# Add the target value to the new DataFrames
df_squared['price'] = df['price']
df_cubed['price'] = df['price']

# Now create heatmaps
plt.figure(figsize=(10, 7))
sns.heatmap(df_squared.corr(), annot=True, fmt=".1f", cmap='coolwarm')
plt.title('Heatmap of Squared Values')
plt.xticks(rotation=90)
plt.show()

plt.figure(figsize=(10, 7))
sns.heatmap(df_cubed.corr(), annot=True, fmt=".1f", cmap='coolwarm')
plt.title('Heatmap of Cubed Values')
plt.xticks(rotation=90)
plt.show()

"""### Get the columns that are more closely correlated with price


"""

# Calculate correlation matrices
correlation_matrix = df_encoded.corr()
corr_squared = df_squared.corr()
corr_cubed = df_cubed.corr()

# Get 'price' correlations
price_corr = correlation_matrix['price']
price_corr_squared = corr_squared['price']
price_corr_cubed = corr_cubed['price']

CUTOFF = .60

# assign a correlation score to each column. Average out the columns that has values for squared and cubed as well
# initialize a dictionary to hold the column indexes with the correlations
avg_col_correlations = {}

for i, v  in enumerate(price_corr):
# if the current iteration is smaller than the length of the squred or cubed lists than it contains values that can be averaged
    if i <= len(price_corr_squared) - 1:
        avg_col_correlations[i] = np.mean([price_corr[i], price_corr_squared[i], price_corr_cubed[i]])
    else:
        avg_col_correlations[i] = price_corr[i]

# list of indexes of columns that are closer than the cutoff
closely_corr_cols = [corr for corr in avg_col_correlations if abs(avg_col_correlations[corr]) >= CUTOFF]

"""__We are setting up two dataframes; one with all columns and one with only select cols. We must also use a try and except since every time the cell above is run with the cells below (if we want to change the cutoff) this cell is recalculated which will cause an error since the dataframes no longer have 'price' in them.__"""

# see above for why we need to use a try and except.
try:
    select_df = df.iloc[:, closely_corr_cols]
    select_df = select_df.loc[:, select_df.columns != 'price']
    y = df['price']
    df = df.loc[:, df.columns != 'price']
except Exception:
    pass

"""### __Linear regression iterating through both datasets and differnt amounts of folds__"""

# create an instance of linear regression
lin_reg = LinearRegression()

# create a pipeline to be used with cross validation
pipeline = Pipeline([
    ('standardizer', MinMaxScaler()),
    ('regressor', lin_reg)
])

# we will be iterating through both the full dataset and the trimmed dataset with only closely correlated columns
datasets = [df, select_df]

# list of folds for cross validation
folds = list(range(3, 100, 10))

# list to hold to hold best model error metrics
best_reg_model = [0] * 3

# initialize a count variable to use to display the correct dataset name. We could not use the actual names of the datasets in the list since when using the if
# statement an error was encountered since the names of datasets don't have truth values.
count = 1

for j in folds:
    for i in datasets:
        lin_reg_values = cross_val_predict(pipeline, i, y, cv=j)
        lin_reg_R2 = r2_score(y, lin_reg_values)
        lin_reg_rmse = mean_squared_error(y, lin_reg_values, squared=False)
        lin_reg_mae = mean_absolute_error(y, lin_reg_values)
        if count % 2 == 0:
            dataset = 'df_with_select_cols'
        else:
            dataset = 'full_df'

# find best R squared and store the error metrics for that model by comparing each metric with the previous value. We use R_squared as the primary error metric
        if lin_reg_R2 > best_reg_model[0]:
            best_reg_model[0] = lin_reg_R2
            best_reg_model[1] = lin_reg_rmse
            best_reg_model[2] = lin_reg_mae

        print(f"Dataset: {dataset} ---- Folds: {j}")
        print(f"R_squared: {lin_reg_R2: .2f}  RMSE: {lin_reg_rmse: .0f} MAE: {lin_reg_mae: .0f}")
        print('')
        count += 1
print(f"BEST REG MODEL {best_reg_model}")

"""#### __Polynomial regression.__ We will iterate through degrees of polynomial equations, folds for cross validation, and a cutoff point for how closely correlated a column must be to the target (price). We have an acceptable R squared value of .6 as well. For the polynommial approach only the closely correlated dataset had success. The full dataset was useless. __(This cell can take a few minutes to run)__"""

degrees = [2, 3, 4]
folds = list(range(3, 100, 20))
poly_cutoff = [i/100 for i in range(70, 85, 4)]
rf_reg_values = LinearRegression()
acceptable_R_2 = .6
best_poly_model = [0] * 3

for degree in degrees:
    for j in folds:
        for cutoff in poly_cutoff:
            poly_closely_corr_cols = [corr for corr in avg_col_correlations if abs(avg_col_correlations[corr]) >= cutoff]
            poly_df = df.iloc[:, poly_closely_corr_cols]
            poly_df = poly_df.loc[:, poly_df.columns != 'price']
            pipeline = Pipeline([
                ('standardizer', MinMaxScaler()),
                ('poly', PolynomialFeatures(degree)),
                ('regressor', LinearRegression())
            ])
            poly_reg_values = cross_val_predict(pipeline, poly_df, y, cv=j)
            poly_reg_R2 = r2_score(y, poly_reg_values)
            poly_reg_rmse = mean_squared_error(y, poly_reg_values, squared=False)
            poly_reg_mae = mean_absolute_error(y, poly_reg_values)

            # find best R squared and store the error metrics for that model
            if poly_reg_R2 > best_poly_model[0]:
                best_poly_model[0] = poly_reg_R2
                best_poly_model[1] = poly_reg_rmse
                best_poly_model[2] = poly_reg_mae

            if poly_reg_R2 >= acceptable_R_2:
                print(f"Degree: {degree} ---- Cutoff: {cutoff} ---- Folds: {j}")
                print(f"R_squared: {poly_reg_R2: .2f}  RMSE: {poly_reg_rmse: .0f} MAE: {poly_reg_mae: .0f}")
                print('')

print(f"BEST POLY MODEL: {best_poly_model}")

"""## __Random Forest Regression.__
 This algorithm can handle the whole dataset. Make sure to add the n_jobs parameter to -1 as this will use multiple cores on your machine and will speed up performance
"""

best_rf_model = [0] * 3

for i in folds:
      rand_forest = RandomForestRegressor(n_estimators=100, n_jobs=-1)
      pipeline = Pipeline([
                ('standardizer', MinMaxScaler()),
                ('regressor', rand_forest)
            ])
      rf_reg_values = cross_val_predict(pipeline, df, y, cv=i)
      rf_reg_R2 = r2_score(y, rf_reg_values)
      rf_reg_rmse = mean_squared_error(y, rf_reg_values, squared=False)
      rf_reg_mae = mean_absolute_error(y, rf_reg_values)


      if rf_reg_R2 > best_rf_model[0]:
                best_rf_model[0] = rf_reg_R2
                best_rf_model[1] = rf_reg_rmse
                best_rf_model[2] = rf_reg_mae

      if rf_reg_R2 >= acceptable_R_2:
                print(f"Folds: {i}")
                print(f"R_squared: {rf_reg_R2: .2f}  RMSE: {rf_reg_rmse: .0f} MAE: {rf_reg_mae: .0f}")
                print('')

print(f"BEST RANDOM FOREST MODEL: {best_rf_model}")

"""## __Gradient Boosting Regression__"""

best_grb_model = [0] * 3
for i in folds:
      grb = GradientBoostingRegressor()
      pipeline = Pipeline([
                ('standardizer', MinMaxScaler()),
                ('regressor', rand_forest)
            ])
      grb_reg_values = cross_val_predict(pipeline, df, y, cv=i)
      grb_reg_R2 = r2_score(y, grb_reg_values)
      grb_reg_rmse = mean_squared_error(y, grb_reg_values, squared=False)
      grb_reg_mae = mean_absolute_error(y, grb_reg_values)


      if grb_reg_R2 > best_grb_model[0]:
                best_grb_model[0] = grb_reg_R2
                best_grb_model[1] = grb_reg_rmse
                best_grb_model[2] = grb_reg_mae

      if rf_reg_R2 >= acceptable_R_2:
                print(f"Folds: {i}")
                print(f"R_squared: {grb_reg_R2: .2f}  RMSE: {grb_reg_rmse: .0f} MAE: {grb_reg_mae: .0f}")
                print('')

print(f"BEST GRADIENT BOOST MODEL: {best_grb_model}")

# create master list with best models for all regression algorithms
best_models = [best_reg_model, best_poly_model, best_rf_model, best_grb_model]

"""## __Summary of results and visualazations__"""

# Create labels for the grouped bar plot
labels = ['Linear Regression', 'Polynomial Regression', 'Random Forest', 'Gradient Boost']

print('SUMMARY OF RESULTS:', '\n')

# format all values in lists to two decimal spaces
formatted_error_metrics = [[round(x, 2) for x in model] for model in best_models]

# display results by outputting actual errors and the errors scaled to the value of 'price'.
for i in range(len(formatted_error_metrics)):
    print(labels[i])
    print(f"R Squared: {formatted_error_metrics[i][0]}", end='    ')
    print(f"RMSE: ${formatted_error_metrics[i][1]:,} ({(formatted_error_metrics[i][1]/y.mean()) * 100:.0f}% of mean car price)", end='    ')
    print(f"MAE: ${formatted_error_metrics[i][2]:,} ({(formatted_error_metrics[i][2]/y.mean()) * 100:.0f}% of mean car price)", '\n')

# get all the R squared, rmse, and mae values in individual lists. Rmse and mae must be scaled to be displayed on the same plot.
r_squared = [model[0] for model in best_models]
rmse = [model[1]/y.mean() for model in best_models]
mae = [model[2]/y.mean() for model in best_models]

# position the bars and labels on the X axis
x = np.arange(len(labels))
# bar width
width = 0.2

# create a figure and subplots
fig, ax = plt.subplots(figsize=(10, 3))

# use 'x' to have each group of bars evenly spaced
rects1 = ax.bar(x - width, r_squared, width, label='R-squared')
rects2 = ax.bar(x, rmse, width, label='RMSE')
rects3 = ax.bar(x + width, mae, width, label='MAE')

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Scores')
ax.set_title('Scores by model and metric')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.legend()

fig.tight_layout()


plt.show()