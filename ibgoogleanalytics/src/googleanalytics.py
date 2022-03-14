from apiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd
import numpy as np
from retry import retry

class GoogleAnalytics:
	"""
	Wrapper for the Google Analytics API v4.
	See for reference:
		* https://developers.google.com/analytics/devguides/reporting/core/v4/rest/v4/reports/batchGet
		* https://ga-dev-tools.appspot.com/dimensions-metrics-explorer/
		* https://ga-dev-tools.appspot.com/query-explorer/ # Especially useful for getting segmentId
	"""
	def __init__(self, credentials, ga_view_id: str):
		self.credentials = service_account.Credentials.from_service_account_file(credentials)
		self.scoped_credentials = self.credentials.with_scopes(['https://www.googleapis.com/auth/analytics.readonly'])
		self.api = build('analyticsreporting', 'v4', credentials=self.scoped_credentials)
		view_id_dic = {"こどものみらい":"?","マネオ":"238474972","おすすめセレクト":"234650494"}
		self.ga_view_id = view_id_dic[ga_view_id]
		self.req = ""
		self.res = []

	def get_all(self, *args, **kwargs) -> pd.DataFrame:
		self.reset()

		batch_size = 100000

		df = self.get_df(*args, **kwargs)
		dfs = df
		while len(df) == batch_size:
			try:
				df = self.get_df(*args, offset=str(batch_size), **kwargs)
				dfs = pd.concat([dfs, df], axis=0)
				print(".", end='')
			except:
				print("Something went wrong. Returning intermediate resluts.")
				break
		return dfs

	@retry(tries=3, delay=2, backoff=2)
	def get_df(self, 	metrics:list =['ga:sessions'],
					dimensions:list =['ga:date'],
					date_ranges:list =[{'startDate': '7daysAgo', 'endDate': 'today'}],
					sort_by=None,
					sort_order=None,
					page_size:int =100000,
					offset:str ='0',
					segments:list =[],
					filters_expression="") -> pd.DataFrame:
		"A method that simplifies how to specify metrics and dimensions variables."
		metrics = [{'expression': metric} for metric in metrics]
		dimensions = [{'name': dim} for dim in dimensions]

		res = self.get_res(metrics=metrics,
					dimensions=dimensions,
					date_ranges=date_ranges,
					sort_by=sort_by,
					sort_order=sort_order,
					page_size=page_size,
					offset=offset,
					segments=segments,
					filters_expression=filters_expression)

		return self.to_df(res)

	def get_res(self, 	metrics=[{'expression': 'ga:sessions'}],
					dimensions=[{'name': 'ga:date'}],
					date_ranges=[{'startDate': '7daysAgo', 'endDate': 'today'}],
					sort_by=None,
					sort_order=None,
					page_size=100000,
					offset='0',
					segments=[],
					filters_expression="") -> pd.DataFrame:
		"""
		Gets data from Google Analytics through the API.

		Input:
			- metrics: list of dictionaries specifying the metrics you want.
			- dimensions: list of dictionaries specifying the dimensions you want.
			- date_ranges: list of dictionaries specifying the date ranges you want.
			- sort_by: the name of the metric to sort results by. If none is supplied, then the first metric will be used.
			- sort_order: choose from 'ASCENDING' or 'DESCENDING'. If none is supplied, 'DESCENDING' will be used.
			- page_size: the number of rows you want. Default is set to the maximum of 100,000 rows.
			- offset: a string specifying the offset. Must be a integer formatted as a string. Default is '0'.
			- segments: optional.
			- filters_expression: optional.
			A string specifying dimensions/metrics conditions to filter. For example, to filter in Firefox users only, use 'ga:browser=~^Firefox'.
			See also: https://developers.google.com/analytics/devguides/reporting/core/v3/reference#filters

		Output:
			- Pandas DataFrame.

		"""

		# Supply default values for the API request.
		assert len(metrics) > 0, "Metrics is empty. Specify at least one metric."
		if sort_by is None:
			sort_by = metrics[0]['expression']
		else:
			if type(sort_by) == list:
				sort_by = sort_by.pop(0)

		if sort_order is None:
			sort_order = 'DESCENDING'
		assert sort_order in ('ASCENDING', 'DESCENDING'), "Invalid sort order. Choose from 'ASCENDING' or 'DESCENDING'."

		if offset != '0':
			offset = str(offset) # Coerce the offset (called `pageToken`) to a string, according to the API.

		if segments:
			# Make sure that `ga:segment` is added to the dimensions list.
			if {'name': 'ga:segment'} not in dimensions:
				dimensions.append({'name': 'ga:segment'})

		self.req = {
			'reportRequests': [{
				'viewId': self.ga_view_id,
				'dateRanges': date_ranges,
				'metrics': metrics,
				'dimensions': dimensions,
				'pageSize': page_size, # Maximum allowed under API
				'pageToken': offset,
				'orderBys': [
					{
						'fieldName': sort_by,
						'orderType': 'VALUE',
						'sortOrder': sort_order
					}
				],
				'hideTotals': True,
  				'hideValueRanges': True,
				'segments': segments,
				'filtersExpression': filters_expression
			}]
		}
		try:
			res = self.api.reports().batchGet(body=self.req).execute()
			self.res.append(res)
		except Exception as e:
			res = e
			print(res)
			self.res.append(res)

		return res

	def reset(self):
		self.res = []
		self.req = ""

	def to_df(self, res=None):
		"""
		Converts a JSON res object into a Pandas DataFrame.
		Input:
			- res: optional JSON Google Analytics API v4 response object. If not supplied, self.res is used instead.
		Output:
			- df: a Pandas DataFrame version of the response object.
		"""

		if res is None: res = self.res[-1]

		dimensions = res['reports'][0]['columnHeader']['dimensions']
		columns = [header['name'] for header in res['reports'][0]['columnHeader']['metricHeader']['metricHeaderEntries']]
		data = res['reports'][0]['data']['rows']
		df = pd.DataFrame(data)

		# Split dimensions as separate columns. If dimensions is a single value, then save a single column.
		keys = np.array(df['dimensions'].tolist())
		for ix, dim in enumerate(dimensions):
			df[dim] = keys[:, ix]
		df.drop('dimensions', axis=1, inplace=True)

		# Split metrics as separate columns. If metrics is a single value per row, then save that value.
		df['metrics'] = df.metrics.apply(lambda x: x[0]['values'])
		values = np.array(df['metrics'].tolist())
		for ix, col in enumerate(columns):
			df[col] = values[:, ix].astype(float)
		df.drop('metrics', axis=1, inplace=True)

		# Add date columns.
		date_ranges = self.req['reportRequests'][0]['dateRanges'][0]
		df['startDate'] = date_ranges['startDate']
		df['endDate'] = date_ranges['endDate']

		# Sort values by the first dimensions column
		df.sort_values(dimensions[0], inplace=True)

		# Store DataFrame for convenience.
		self.df = df

		return self.df

	@property
	def google_organic(self):
		"""
		Returns segments list for source=google and medium=organic users.
		"""
		segments = [
			{
				"dynamicSegment": {
					"name": "googleOrganic",
					"userSegment": {
						"segmentFilters": [{
							"not": 'false',
							"simpleSegment": {
								"orFiltersForSegment": [{
									"segmentFilterClauses": [{
										"dimensionFilter": {
											"dimensionName": "ga:sourceMedium",
											"expressions": ["google / organic"]
										}
									}]
								}]
							}
						}]
					}
				}
			}
		]
		return segments