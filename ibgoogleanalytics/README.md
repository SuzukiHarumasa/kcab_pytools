# Summary
インスタベースのGoogle AnalyticsをAPI経由で取得するためのAPIラッパー。

## 準備手順
1. Google CloudにてService Accountを新しく作る。
2. そのService AccountのメールアドレスをGoogle Analytics上でRead権限を付与する。
3. Service Accountに対してAPI KeyをJSONフォーマットで新規に発行する。発行後ダウンロードされるファイルへのパスが後に必要となる。 `GoogleAnalytics` インスタンスを作成するときにそれを使う。

すでにService Accountがある場合は、Google Cloud上で新たなキーを発行できるので発行して保存すると良い。

## 使い方

過去３０日のセッションとトランスアクションデータを取ってくる
```
# Get session and transaction data for past 30 days
df = ga.get_df(metrics=['ga:sessions'],
          dimensions=['ga:yearMonth', 'ga:pagePath'],
          date_ranges=[{'startDate':'2021-10-30', 'endDate':'2021-10-31'}],
          page_size=1_000_000,
          sort_by='ga:sessions',
          sort_order='DESCENDING',
          filters_expression='ga:pagePath=~\/tokyo-rentalspace')
```

チャートで出すとこんな感じ
```
# Plot for fun
import pandas as pd
import matplotlib.pyplot as plt

df['ga:sessions'].plot(style='o-', label='Sessions')
df['ga:transactions'].plot(style='o-', secondary_y=True, label='Transactions')
plt.title("Sessions and Transactions")
plt.legend()
plt.show()
```

Google Organicのユーザーだけに絞り込みたいときには、 `ga.google_organic` のプロパティを使うと便利。そのセグメントに絞り込んでくれる。
```
df = ga.get_df(	metrics=[{'expression':'ga:sessions'}],
				dimensions=[{'name': 'ga:date'}],
				date_ranges=[{'startDate': '2020-03-01', 'endDate': '2020-03-14'}],
				page_size=100,
				segments=ga.google_organic
            )
df
```

### IbSearchUrlParserの使い方
インスタベースの検索URLをパースして、人間フレンドリーなURLを出してくれる。

```
from lib.redash import Redash
from lib.googleanalytics import IbSearchUrlParser

credentials = PATH_TO_CREDENTIALS
redash = Redash(credentials)
ibsp = IbSearchUrlParser(redash, refresh=False) # use refresh=True to fetch fresh data from Redash

...

data['some_column'].apply(ibsp.get_categories) #=> returns human friendly category names used in the search!
```



## 参考リンク
* [Google Analytics Dimensions Explorer](https://ga-dev-tools.appspot.com/dimensions-metrics-explorer/)
* [Google Auth](https://google-auth.readthedocs.io/en/latest/index.html)
* [batchGetの詳細](https://developers.google.com/analytics/devguides/reporting/core/v4/rest/v4/reports/batchGet)
* [SegmentIdを手に入れるのに便利な queryExplorer](https://ga-dev-tools.appspot.com/query-explorer/)
* [Filterの使い方に関して](https://developers.google.com/analytics/devguides/reporting/core/v3/reference#filters)