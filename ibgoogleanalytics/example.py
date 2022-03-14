import pandas as pd
import matplotlib.pyplot as plt

from src.googleanalytics import GoogleAnalytics

credentials = './credentials/tidal-plasma-270110-aa109d2737fe.json'
ga = GoogleAnalytics(credentials)

# Get session and transaction data for past 7 days
df = ga.get_df(['ga:sessions', 'ga:transactionRevenue'],
               ['ga:date'],
               [{'startDate': '31daysAgo', 'endDate': 'yesterday'}],
               sort_by='ga:date',
               sort_order='ASCENDING',)
df.index = pd.to_datetime(df['ga:date'])
df.drop('ga:date', axis=1, inplace=True)

# Plot for fun
df['ga:sessions'].plot(style='o-', label='Sessions')
df['ga:transactionRevenue'].plot(
    style='o-', secondary_y=True, label='Transactions')
plt.title("Sessions and Transactions")
plt.legend()
plt.show()
