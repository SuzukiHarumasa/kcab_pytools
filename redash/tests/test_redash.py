# Run from top of module
import pandas as pd
import requests
import json
import sys
sys.path.append('./')
from src.redash import Redash

creds = './credentials/secrets.json'
redash = Redash(creds)


def test_redash_query_should_work():
    df = redash.query(2600)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 100


def test_redash_safe_query_should_work():
    df = redash.safe_query(2880,
                           params={'station1': '池袋', 'station2': '渋谷'},
                           limit=100_000)
    assert len(df) > 10_000
