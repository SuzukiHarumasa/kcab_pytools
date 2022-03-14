# Google Ads API

RebaseのGoogle AdsアカウントのAPIを叩くことができる。
レポーティングAPIの利用のみ開放されているので、広告の編集などはまだAPI経由ではできない。

まずはクレデンシャルが必要なので、 @alex か @eguchan に聞いて手に入れて欲しい。

# Examples

```
import pandas as pd
from googleads import adwords
path_to_credentials = './secrets/google-ads.yaml'
client = adwords.AdWordsClient.LoadFromStorage(path_to_credentials)
targeting_idea_service = client.GetService('TargetingIdeaService', version='v201809')

def get_search_volumes(keywords, offset=0, page_size=10):
	selector = {
		'ideaType': 'KEYWORD',
		'requestType': 'STATS'
	}
	selector['requestedAttributeTypes'] = [
		'KEYWORD_TEXT', 'SEARCH_VOLUME', 'TARGETED_MONTHLY_SEARCHES']
	selector['paging'] = {
		'startIndex': str(offset),
		'numberResults': str(page_size)
	}
	selector['searchParameters'] = [{
		'xsi_type': 'RelatedToQuerySearchParameter',
		'queries': keywords
	}]
	page = targeting_idea_service.get(selector)

	comb_df = pd.DataFrame()
	for entry in page['entries']:
		keyword = entry['data'][0]['value']['value']
		monthly_vol = entry['data'][1]['value']['value']
		mean_search_volume = entry['data'][2]['value']['value']
		rows = []
		for row in monthly_vol:
			rows.append((row.year, row.month, row.count))
		df = pd.DataFrame(rows, columns=['year', 'month', keyword])
		df['yearMonth'] = df['year'].astype(str) + df['month'].astype(str).str.zfill(2)
		df.set_index('yearMonth', inplace=True)
		df.drop(['year', 'month'], axis=1, inplace=True)
		df.loc['mean'] = mean_search_volume

		comb_df = pd.concat([comb_df, df], axis=1)

	# Return a Data Frame with keywords as rows
	return comb_df.T


keywords = ['レンタルスペース', 'レンタルスタジオ', 'レンタルルーム']
comb_df = get_search_volumes(keywords)
comb_df.to_csv("./results/search_volumes.csv")

```