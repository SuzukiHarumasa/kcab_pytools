import os
import sys
import datetime
sys.path.extend('./')
import pandas as pd
import numpy as np
from src.searchconsole import IBSearchConsole

if not os.path.exists('results'):
    os.makedirs('results')

credentials = './credentials/instabase-search-console-7812cfb87607.json'
sc = IbSearchConsole(credentials, ask_to_proceed=False)

top_queries = sc.get_top_queries(params={'rowLimit':100})
top_pages = sc.get_top_pages(params={'rowLimit':100})

top_queries.to_csv(f"results/top_queries_{datetime.datetime.today().strftime('%Y-%m-%d')}.csv")
top_pages.to_csv(f"results/top_pages_{datetime.datetime.today().strftime('%Y-%m-%d')}.csv")

# filters = sc.add_filter('page', 'equals', 'https://www.instabase.jp/tokyo-kaigishitsu')
# top_queries = sc.get_top_queries(dimensions=['query'],
                        # filters=filters,
                        # params={'rowLimit': 100})

# Filters can be layered as such:
filters = sc.add_filter([], 'query', 'contains', '会議室')
filters = sc.add_filter(filters, 'page', 'contains', 'https://www.instabase.jp/tokyo')
top_pages = sc.get_top_pages(dimensions=['query', 'page'],
                        filters=filters,
                        params={'rowLimit': 25000})

# filters = sc.add_filter('query', 'contains', 'レンタルスペース')
# all_queries = sc.get_top_queries(   dimensions=['query', 'page'],
#                                     filters=filters,
#                                     params={
#                                         'startDate': '2020-02-01',
#                                         'endDate': '2020-02-29',
#                                         'rowLimit': 10000},
#                                     get_all=False)

# filters = []
# filters = sc.add_filter([], 'query', 'contains', '渋谷')

# df = sc.compare_top_queries(
#     period1_start='2020-03-08',
#     period1_end='2020-03-14',
#     period2_start='2020-02-23',
#     period2_end='2020-02-29',
#     dimensions=['query', 'page'],
#     filters=filters,
#     params={
#         'rowLimit': 30000
#     },
#     get_all=True
# )

# df_with_importance = sc.most_important_changes_in(df,
#                         changes_col='ctr',
#                         importance_col='impressions_1')


# df1 = sc.get_top_queries(
#     dimensions=['query', 'page'],
#     filters=filters,
#     params={
#         'startDate': '2020-03-01',
#         'endDate': '2020-03-07',
#         'rowLimit': 30000
#     },
#     get_all=True
# )
# df1['startDate'] = '2020-03-01'
# df1['endDate'] = '2020-03-07'

# df2 = sc.get_top_queries(
#     dimensions=['query', 'page'],
#     filters=filters,
#     params={
#         'startDate': '2020-02-23',
#         'endDate': '2020-02-29',
#         'rowLimit': 30000
#     },
#     get_all=True
# )
# df2['startDate'] = '2020-02-23'
# df2['endDate'] = '2020-02-29'


