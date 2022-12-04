# See examples at: https://developers.google.com/webmaster-tools/search-console-api-original/v3/quickstart/quickstart-python
# Another example: https://github.com/googleapis/google-api-python-client/blob/master/samples/searchconsole/search_analytics_api_sample.py

import datetime
from typing import Callable
import pandas as pd
import numpy as np

from apiclient.discovery import build
from google.oauth2 import service_account


class IbSearchConsole:
    """
    Search Console API accepts requests of the following format:

    {
        "startDate": string,
        "endDate": string,
        "dimensions": [
            string
        ],
        "searchType": string,
        "dimensionFilterGroups": [
            {
                "groupType": string,
                "filters": [
                {
                    "dimension": string,
                    "operator": string,
                    "expression": string
                }
                ]
            }
        ],
        "aggregationType": string,
        "rowLimit": integer,
        "startRow": integer
    }
    See the following link for more information: https://developers.google.com/webmaster-tools/search-console-api-original/v3/searchanalytics/query#dimensionFilterGroups.filters.dimension

    """

    metrics: list = ['clicks', 'impressions', 'ctr', 'position']
    metrics_agg_dict: dict = {'clicks': 'sum',
                              'impressions': 'sum', 'ctr': 'mean', 'position': 'mean'}

    def __init__(self, credentials, ask_to_proceed=False):
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials)
        self.scoped_credentials = self.credentials.with_scopes(
            ['https://www.googleapis.com/auth/webmasters.readonly'])
        self.refresh_token()
        try:
            self.get_site_list()
        except:
            pass
        self.property_uri = 'https://www.maneo.jp/saas/'
        self.default_query_params = {
            'startDate': (datetime.datetime.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d'),
            'endDate': (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
            'startRow': 0,
            'rowLimit': 5000,
        }
        self.ask_to_proceed = ask_to_proceed
        print("Default query params set. startDate and endDate are set to the past 30 days by default. Overwrite as needed.")

    def refresh_token(self):
        self.api = build('searchconsole', 'v1',
                         credentials=self.scoped_credentials)

    @property
    def list_dimensions(self):
        "Returns list of legal values for dimensions."
        return ['country', 'device', 'page', 'query', 'searchAppearance', 'date']

    @property
    def list_operators(self):
        "Returns list of legal values for operators."
        return ['contains', 'equals', 'notContains', 'notEquals']

    @property
    def list_devices(self):
        "Returns list of legal values for device."
        return ['DESKTOP', 'MOBILE', 'TABLET']

    @property
    def list_metrics(self):
        "Returns list of metrics the API returns."
        return ['clicks', 'ctr', 'impressions', 'position']

    def get_site_list(self):
        self.site_list = self.api.sites().list().execute()
        self.verified_sites_urls = [s['siteUrl'] for s in self.site_list['siteEntry']
                                    if s['permissionLevel'] != 'siteUnverifiedUser'
                                    and s['siteUrl'][:4] == 'http']
        print('Verified site urls:\n\t- ' +
              '\n\t- '.join(self.verified_sites_urls))

    def get_sitemaps(self, site_url):
        try:
            self.sitemaps = self.api.sitemaps().list(siteUrl=site_url).execute()
            if 'sitemap' in self.sitemaps:
                sitemap_urls = [s['path'] for s in self.sitemaps['sitemap']]
                print(f"Sitemap for {site_url} -> ")
                print('\t' + '\n '.join(sitemap_urls))
        except Exception as e:
            print(e)
            
    #めちゃくちゃ重要
    def get(self, dimensions=['query'], filters=[], params={}, get_all=False):
        "Gets top 10 queries for the date range, sorted by click count, descending."

        self.req = self.build_request([
            {'dimensions': dimensions},
            {'dimensionFilterGroups': [{'filters': filters}]},
            params,
        ])

        if get_all:
            self.res = self.execute_request_all(self.req)
            response_rows = []
            for response in self.res:
                response_rows.extend(response['rows'])
        else:
            response = self.execute_request(request=self.req)
            response_rows = response['rows']

        return self.to_df(response_rows)

    def get_top_queries(self, dimensions=['query'], filters=[], params={}, get_all=False):
        "Convenience method for fetching top queries."
        return self.get(dimensions=dimensions,
                        filters=filters,
                        params=params,
                        get_all=get_all)

    def get_top_pages(self, dimensions=['page'], filters=[], params={}, get_all=False):
        "Convenience method for fetching top pages."
        return self.get(dimensions=dimensions,
                        filters=filters,
                        params=params,
                        get_all=get_all)
        
    # response = webmasters.searchanalytics().query(siteUrl=site, body=body).execute()
    def execute_request(self, request={}, property_uri=None):
        """Executes a searchAnalytics.query request.
        Args:
            service: The webmasters service to use when executing the query.
            property_uri: The site or app URI to request data for.
            request: The request to be executed.
        Returns:
            An array of response rows.
        """
        self.req = request
        property_uri = property_uri or self.property_uri
        self.req['rowLimit'] = 5000 if self.req['rowLimit'] > 5000 else self.req['rowLimit']
        self.response = self.api.searchanalytics().query(
            siteUrl=property_uri, body=self.req).execute()

        tot_rows_fetched = 0
        if 'rows' in self.response:
            rows_fetched = len(self.response['rows'])
            tot_rows_fetched += rows_fetched
        else:
            print(f"The request did not return any rows.")
        return self.response

    def execute_request_all(self, request):
        """Loops execute_request until the required number of rows are fetched.
        Input:
            - Request object
        Output:
            - A list of responses from API
        """

        assert 'rowLimit' in request.keys(), "Request does not include a rowLimit."
        self.req = request
        row_limit = self.req['rowLimit']

        if row_limit > 5000:
            self.req['rowLimit'] = 5000

        all_responses = []
        rows_fetched = 0
        index = 0

        while True:
            self.response = self.execute_request(
                request=self.build_request([
                    self.req,
                    {'startRow': index}
                ])
            )
            if 'rows' in self.response:
                rows_fetched = len(self.response['rows'])
                index += rows_fetched
                all_responses.append(self.response)

                print(
                    f"Got {rows_fetched} rows. Total of {index} rows fetched.")

                if rows_fetched < 5000:  # the max rows that can be fetched at once through the API.
                    print(
                        "There seems to be no more rows to be fetched. Completing the query.")
                    break
                else:
                    if index >= row_limit:
                        print("The rowLimit was reached. Completing the query.")
                        break
                    else:
                        if self.ask_to_proceed:
                            if input("Continue? [Y/n] ") in ('Y', 'y'):
                                continue
                            else:
                                break
            else:
                print(
                    f"No more rows were fetched. Ending query with {rows_fetched} rows.")
                break
        return all_responses

    def build_request(self, params=[]):
        """
        Combines a list of params into a single request dictionary.
        The default_query_params is overwritten by the key-values stored in the dictionaries within params.

        Args:
            params: A list of dictionaries used to overwrite default_query_params.
        Returns:
            A request dictionary.
        Usage:
            request = sc.build_request([
                {'startDate': '2019-01-01'},
                {'dimensions': ['query']}
            ])
        """
        # Make sure params is of type list so that we can iterate over items.
        params = params if type(params) is list else [params]

        # Begin by copying the default_query_params
        self.req = self.default_query_params.copy()

        for param_dic in params:
            self.req.update(param_dic)
        return self.req

    def add_filter(self, filters=[], dimension=None, operator=None, expression=None):
        """Creates a filter dictionary and returns a list of filters.
        If the method is supplied with a 'filters' object, the method will add to that filters object and
        return the resulting list.
        Input:
            - dimension: e.g., 'query'
            - operator: e.g., 'contains'
            - expression: e.g., '仮想通貨'
        Output:
            - list of dictionary filters: e.g., [{'dimension':'query',
                                                    'operator':'contains',
                                                    'expression':'仮想通貨'}]
        """
        assert all([dimension, operator, expression]
                   ), "Dimension, operator, or expression was empty."

        new_filter = {
            'dimension': dimension,
            'operator': operator,
            'expression': expression
        }
        filters.append(new_filter)
        return filters

    def to_df(self, response_rows):
        """Returns a DataFrame version of response.
        Input:
            - response_rows: the rows returned from the response.
        Output:
            - Pandas DataFrame version of the response.
        """

        assert len(response_rows) > 0, "Response should not be empty."
        assert 'keys' in response_rows[0], "Response item did not have the key 'keys'."

        df = pd.DataFrame(response_rows)

        # Split keys into separate columns if key has multiple dimensions in it.
        keys = np.array(df['keys'].tolist())
        if len(keys[0]) > 1:
            # Keep track of key columns so that we can put them back into order later.
            for ix in range(len(keys[0])):
                df[f'key_{ix}'] = keys[:, ix]
            df.drop('keys', axis=1, inplace=True)
        else:
            df['keys'] = df['keys'].apply(lambda x: x[0])

        df['startDate'] = self.req['startDate']
        df['endDate'] = self.req['endDate']

        # Get columns so that we can get columns in the right order.
        date_cols = [col for col in df.columns if col.endswith('Date')]
        key_cols = [col for col in df.columns if col.startswith('key')]
        metric_cols = self.list_metrics
        col_order = date_cols + key_cols + metric_cols

        # Return DataFrame with col_order
        return df[col_order]

    def get_dates_with_data(self, params={}):
        """Run to learn which dates have data.
        E.g., start_date and end_date can be formated as '2020-03-31'"""
        self.req = self.build_request([
            {'dimensions': ['date']},
            params,
        ])
        response = self.execute_request(request=self.req)
        return self.to_df(response['rows'])

    def get_top_searchappearance(self, params={}):
        # Group by total number of Search Appearance count.
        # Note: It is not possible to use searchAppearance with other
        # dimensions.
        self.req = self.build_request([{
            'dimensions': ['searchAppearance'],
        },
            params
        ])
        response = self.execute_request(request=self.req)
        return self.to_df(response['rows'])

    def compare_top_queries(self, period1_start=None, period1_end=None,
                            period2_start=None, period2_end=None,
                            dimensions=['query'], filters=[], params={}, get_all=False):

        # Set the periods to compare
        assert (period1_start != None) & (
            period1_end != None), "Period 1 is required."

        period1_start_as_datetime = datetime.datetime.strptime(
            period1_start, '%Y-%m-%d')
        period1_end_as_datetime = datetime.datetime.strptime(
            period1_end, '%Y-%m-%d')

        if period2_start is None or period2_end is None:
            period2_start = (period1_start_as_datetime -
                             datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            period2_end = (period1_end_as_datetime -
                           datetime.timedelta(days=7)).strftime('%Y-%m-%d')

        # Fetch responses as Data Frames
        params.update({
            'startDate': period1_start,
            'endDate': period1_end
        })
        df1 = self.get_top_queries(
            dimensions=dimensions,
            filters=filters,
            params=params,
            get_all=True
        )

        params.update({
            'startDate': period2_start,
            'endDate': period2_end
        })
        df2 = self.get_top_queries(
            dimensions=dimensions,
            filters=filters,
            params=params,
            get_all=True
        )

        # Return merged Data Frame
        cols1 = [col for col in df1.columns if col.startswith('key')]
        cols2 = [col for col in df2.columns if col.startswith('key')]
        df = pd.merge(df1, df2, how='outer', left_on=cols1,
                      right_on=cols2, suffixes=['_1', '_2'])

        return df

    def _compute_relative_importance(self, df, importance_col):
        return (df[importance_col] / df[importance_col].sum()).fillna(0)

    def most_important_changes_in(self, df, changes_col='clicks', importance_col='clicks_1'):
        """
        Returns the most important changes in changes_col, weighted by the importance_col.
        The method excludes rows with values of np.inf, which are treated as "new comers",
        and np.nan which are treated as "drops".

        Inputs:
            - df: DataFrame
            - importance_col: the DataFrame column to use for weighting; e.g., 'clicks_1'
        Output:
            - DataFrame with the most important changes
        Usage:
            - e.g., df_with_importance = sc.most_important_changes_in(df,
                                            changes_col='clicks',
                                            importance_col='impressions_1')
        """

        assert changes_col in self.list_metrics, f"changes_col is invalid. Choose from {self.list_metrics}"
        assert importance_col in df.columns, "importance_col not found in df.columns"

        df = df.copy()
        df['importance'] = self._compute_relative_importance(
            df, importance_col)

        df['log_change'] = np.log(
            df[f'{changes_col}_1'] / df[f'{changes_col}_2']) * df['importance']

        # Drop rows with np.inf or np.nan
        df.drop(df[df['log_change'] == np.inf].index, inplace=True)
        df.drop(df[df['log_change'] == -np.inf].index, inplace=True)
        df.dropna(inplace=True)

        df.sort_values('log_change', ascending=False, inplace=True)

        return df
