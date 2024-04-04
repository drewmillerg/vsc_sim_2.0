"""This retrieves all of the data and does the ML regression for the forecast functionality
in the GUI."""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split 
from sklearn.linear_model import LinearRegression
from sklearn import metrics
import vsc_data as vd

DAYS = 90

def get_data():
    vd.DAYS = DAYS
    df = vd.get_interactions_table()
    df['DATE'] = pd.to_datetime(df['DATE'])
    df['date_delta'] = (df['DATE'] - df['DATE'].max())  / np.timedelta64(1,'D')
    return df

def train_model(df):
    X = df['date_delta'].values.reshape(-1,1)
    y = df['DAILYINTERACTIONCOUNT'].values.reshape(-1,1)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
    regressor = LinearRegression()  
    regressor.fit(X_train, y_train)
    
    # Print the intercept and slope
    print('Intercept:', regressor.intercept_)
    print('Slope:', regressor.coef_)
    
    return regressor, X_test, y_test

def predict_model(regressor, X_test, y_test):
    y_pred = regressor.predict(X_test)
    
    # Compare the actual versus predicted values
    df_compare = pd.DataFrame({'Actual': y_test.flatten(), 'Predicted': y_pred.flatten()})
    print(df_compare)
    
    # Print error metrics
    print('Mean Absolute Error:', metrics.mean_absolute_error(y_test, y_pred))
    print('Mean Squared Error:', metrics.mean_squared_error(y_test, y_pred))
    print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(y_test, y_pred)))
    
    return y_pred

def future_forecast(regressor, df):
    future_dates = pd.date_range(start=df['DATE'].max()+ pd.DateOffset(1), periods=60)
    future_date_deltas = (future_dates - df['DATE'].max()) / np.timedelta64(1,'D')
    future_interactions = regressor.predict(future_date_deltas.values.reshape(-1,1))
    future_df = pd.DataFrame({'date_delta': future_date_deltas, 'predicted_interactions': future_interactions.flatten()})
    
    # Print future forecast
    print(future_df)
    
    return future_df

def plot_data(X, y, regressor, future_df):
    plt.figure(figsize=(10,5))
    plt.scatter(X, y, color='gray', label='Past Actual')
    plt.plot(X, regressor.predict(X), color='blue', linewidth=2, label='Past Predicted')
    plt.plot(future_df['date_delta'], future_df['predicted_interactions'], color='red', linewidth=2, label='Future Forecast')
    plt.title('Actual vs Predicted')
    plt.xlabel('date_delta')
    plt.ylabel('DAILYINTERACTIONCOUNT')
    plt.legend()
    plt.show()

if __name__ == "__main__":
    df = get_data()
    regressor, X_test, y_test = train_model(df)
    y_pred = predict_model(regressor, X_test, y_test)
    future_df = future_forecast(regressor, df)
    print(future_df.head())
    plot_data(df['date_delta'].values.reshape(-1,1), df['DAILYINTERACTIONCOUNT'].values.reshape(-1,1), regressor, future_df)