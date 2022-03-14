import pandas as pd
from googleads import adwords


class GoogleAds:
	def __init__(self, path_to_credentials: str = './secrets/google-ads.yaml'):
		self.path_to_credentials = path_to_credentials
		self.client = adwords.AdWordsClient.LoadFromStorage(path_to_credentials)
		self.targeting_idea_service = self.client.GetService('TargetingIdeaService', version='v201809')

	def get_search_volumes(self, keywords: list,
								offset: int = 0,
								page_size: int = None) -> pd.DataFrame:
		"""
		Input:
			- keywords: list of keywords to get volumes for.
			- offset: int. Default 0. Page offset to use for pagination.
			- page_size: int. Default None. Page size of each page.

		Usage:
			gad = GoogleAds(path_to_credentials)
			keywords = ['レンタルスペース', 'レンタルスタジオ', 'レンタルルーム']
			comb_df = gad.get_search_volumes(keywords)
			comb_df.to_csv("./results/search_volumes.csv")
		"""
		if page_size is None:
			page_size = len(keywords)

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
		page = self.targeting_idea_service.get(selector)

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
		return comb_df.sort_index().T


	def generate_keywords(self, array1: list, array2: list) -> list:
		"""
		Convenience method to generate a combination of keywords
		using elements in array1 and array2.
		Items in array1 come first and items in array2 comes second.

		"""
		return [f'{kw1} {kw2}' for kw1 in set(array1) for kw2 in set(array2)]


