import pandas as pd
from ibgoogleads import GoogleAds

gad = GoogleAds('./secrets/google-ads.yaml')

string1 = """
ポップアップストア
ライブハウス
ギャラリー
展示会場
"""
array1 = string1.strip().split('\n')

string2 = """
東京
渋谷
新宿
池袋
大阪
名古屋
"""
array2 = string2.strip().split('\n')
keywords = gad.generate_keywords(array1, array2)

comb_df = pd.DataFrame()
BATCH_SIZE = 600
# for batch in range(0, 1800, 600):
for batch in range(0, len(keywords), BATCH_SIZE):
    print(f"Querying {batch}...")
    df = gad.get_search_volumes(keywords[batch:batch+BATCH_SIZE])
    comb_df = comb_df.append(df)


# from googleads import adwords


# PAGE_SIZE = 100


# def main(client):
#   # Initialize appropriate service.
#   campaign_service = client.GetService('CampaignService', version='v201809')

#   # Construct selector and get all campaigns.
# offset = 0
# selector = {
#     'fields': ['Id', 'Name', 'Status'],
#     'paging': {
#         'startIndex': str(offset),
#         'numberResults': str(PAGE_SIZE)
#     }
# }

# more_pages = True
# while more_pages:
# page = campaign_service.get(selector)

# # Display results.
# if 'entries' in page:
#     for campaign in page['entries']:
#     print('Campaign with id "%s", name "%s", and status "%s" was '
#             'found.' % (campaign['id'], campaign['name'],
#                         campaign['status']))
# else:
#     print('No campaigns were found.')
# offset += PAGE_SIZE
# selector['paging']['startIndex'] = str(offset)
# more_pages = offset < int(page['totalNumEntries'])


# if __name__ == '__main__':
#   adwords_client = adwords.AdWordsClient.LoadFromStorage("./secrets/google-ads.yaml")
#   main(adwords_client)


