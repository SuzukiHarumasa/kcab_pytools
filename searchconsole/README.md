# Search Console API CLI Tool
## 目的
インスタベースのサチコデータをAPI経由で取得できるツールです。
まだ開発中なので色々不具合あるかと思います。

## とりあえず便利なの
サチコ上では1000件しかデータが取れないが、APIだと5000件まで取れる。
それ以上は一度に取得できないので、 `startRow` をインクリメントしながら、パジネーションしをして複数回に分けて取りに行くことになる。
それ以上のデータに関しては、Googleは毎日一日分のデータを取ってくることをおすすめしている。

```
import sys
import pandas as pd
sys.path.append('/Users/suzukiharumasa/kcab/')

from kcab_pytools.searchconsole import IbSearchConsole
credentials = '../../kcab_pytools/client_secret_dota.json'
site = 'https://www.maneo.jp/media/' 
sc = IbSearchConsole(credentials, site)
```

フィルターを使った例
```
filters = sc.add_filter('page', 'equals', 'https://www.maneo.jp/media/cr-metaverse-crypto/')
top_queries = sc.get_top_queries(dimensions=['query'],
                        filters=filters,
                        params={'rowLimit': 100})
```

フィルターを複数重ねることもできる。
論理的に正しいフィルターのリストになっているかのチェックはしていないので注意。
```
filters = sc.add_filter('query', 'contains', '会議室')
filters = sc.add_filter('page', 'contains', 'https://www.instabase.jp/tokyo', filters)
top_pages = sc.get_top_pages(dimensions=['query', 'page'],
                        filters=filters,
                        params={'rowLimit': 100})
```

日付を指定する場合
```
top_pages = sc.get_top_pages(dimensions = ['date', 'page','query'],params={'startDate' : '2021-04-01', 'endDate' : '2021-08-31'},get_all=True)

top_pages['key_0'] = pd.to_datetime(top_pages['key_0'])
top_pages = top_pages.sort_values('key_0').reset_index(drop = True)

```
## TODO
[Projectsを使って管理してみてる。](https://github.com/rebaseinc/ib-analysis/projects/1)

## 参考
* https://developers.google.com/webmaster-tools/search-console-api-original/v3/quickstart/quickstart-python
* https://github.com/googleapis/google-api-python-client/blob/master/samples/searchconsole/search_analytics_api_sample.py

## TO READ
* https://github.com/benpowis/Google-Search-Console-bulk-query-to-GBQ/blob/master/search_console_query_to_GBQ.py
* https://medium.com/@singularbean/google-search-console-data-into-google-bigquery-3e794127fa08