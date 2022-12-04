import sys

sys.path.append('/Users/suzukiharumasa/kcab/kcab_pytools')

import pandas as pd
from gsheets import GSheets

# インスタンスを生成
creds = '/Users/suzukiharumasa/kcab/kcab_pytools/py-tools-341712-6978522c6ff8.json'
gs = GSheets(creds)

# 例としてdfを作成
df = pd.DataFrame({'name': ['John', 'Bob', 'Marry'],
                   'age': [13, 47, 32]})

# dfを保存。
# フォルダを指定しなければ、デフォルトで Rebase Inc. Team の共有フォルダに保存。
# https://drive.google.com/drive/folders/0BxpY8IQbguQWa3V5blloRWFjMzA
sheets = gs.save_df(df, title='Sample title')
gs.share(sheets, ["alex.ishida@rebase.co.jp"])

print(f"Saved results to: {sheets.url}.")

# 最後に保存したシートを開くメソッド。
gs.open()


# 既存のシートをキーで指定して開く
sheets = gs.gc.open_by_key('1xQKb96BEth5IkYXMHQbzKW5uOmjJWyLh6FqNDUrvgyw')
sheets

# シートの中身を確認
sheet = sheets.worksheets()[0]
content = sheet.get_values()
content

#シートの中身をデータフレーム化
df = pd.DataFrame(content, columns = content[0]).drop(0)

# シートから重複する行を削除（全ての列の値が重複しているかをチェック）
gs.drop_duplicates(sheet)

# シートにある行に新たなな行を追加
gs.concat(df, sheet)

# シートの中身をdfで全て置き換える
gs.update(sheet, df)
