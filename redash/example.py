from lib.ib_pytools.redash import Redash

creds_file = ""
redash = Redash(creds_file)

df = redash.query(2600)

df2 = redash.safe_query(2880,
                        params={'station1': '池袋', 'station2': '新宿'},
                        limit=100_000)
