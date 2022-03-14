import pandas as pd
import numpy as np
import re
from urllib.parse import urlparse
import warnings
from typing import List


class IbUrlFilter:
    categories = ['categories', 'kominka', 'rentalspace', 'shooting', 'caferesto', 'gallery', 'popupstore', 'livehouse',
                  'sportsfacility', 'otherspace', 'rooftop', 'event-hall', 'music-studio', 'housestudio', 'workspace',
                  'kaigishitsu', 'kitchen', 'seminar-kaijo', 'dance-studio', 'salon', 'event-space', 'self-desk']
    prefectures = ['fukushima', 'shiga', 'nara', 'wakayama', 'fukuoka', 'nigata', 'toyama', 'ishikawa',
                   'fukui', 'nagano', 'gifu', 'hokkaido', 'aomori', 'iwate', 'miyagi', 'akita', 'yamagata',
                   'shizuoka', 'mie', 'tottori', 'shimane', 'okayama', 'hiroshima', 'yamaguchi', 'tokushima',
                   'kagawa', 'ehime', 'kochi', 'saga', 'nagasaki', 'kumamoto', 'oita', 'miyazaki', 'kagoshima',
                   'okinawa', 'yamanashi', 'tokyo', 'kanagawa', 'saitama', 'chiba', 'tochigi', 'gunma',
                   'ibaraki', 'aichi', 'osaka', 'kyoto', 'hyogo']
    areas = ['chiba-chiba', 'osaka-osaka', 'saitama-saitama', 'kanagawa-yokohama', 'hiroshima-hiroshima',
             'miyagi-sendai', 'shizuoka-shizuoka', 'shizuoka-hamamatsu', 'aichi-nagoya', 'kanagawa-kawasaki',
             'kyoto-kyoto', 'okayama-okayama', 'fukuoka-kitakyushu', 'fukuoka-fukuoka', 'kumamoto-kumamoto',
             'nigata-nigata', 'osaka-sakai', 'hokkaido-sapporo', 'kanagawa-sagamihara', 'hyogo-kobe']

    @classmethod
    def istoppage(cls, values):
        return values.str.match(r'^(https\:\/\/www\.instabase\.jp)?\/$')

    @classmethod
    def isgeneric(cls, values: pd.Series, exclude_homepage: bool = True) -> np.ndarray:
        """
        Checks if input Series strings match generic page url patterns.
        Returns boolean array of results.
        """
        # Exclude top pages first by replacing them with the 'exclude' marker.
        if exclude_homepage:
            values = values.apply(lambda x: 'exclude' if x ==
                                  'https://www.instabase.jp/' or x == '/' else x)

        # Define patterns to filter out
        patterns_to_filter_list = cls.categories + ['list', 'matome', 'space', 'rooms', 'insurance',
                                                    'reviews', 'lines', 'privacy', 'legal', 'blog',
                                                    'owners', 'owner', 'partner', 'exclude']
        patterns_to_filter = r'.*(\?\w+|' + \
            r'|'.join(patterns_to_filter_list).replace('-', r'\-') + r').*'
        patterns_to_filter_compiled = re.compile(patterns_to_filter)

        return ~values.str.match(patterns_to_filter_compiled).values.ravel()

    @classmethod
    def iscategory(cls, values):
        return values.str.match(r'.*(' + r'|'.join(cls.categories) + r').*')

    @classmethod
    def get_categories(cls, values):
        return values.str.extract(r'.*(' + r'|'.join(cls.categories) + r').*')

    @classmethod
    def isfeature(cls, values):
        return values.str.match(r'.*\/list\/.*')

    @classmethod
    def get_features(cls, values):
        return values.str.extract(r'.*\/list\/([\w\-]+).*')

    @classmethod
    def isspace(cls, values):
        return values.str.match(r'.*\/space\/\d+.*')

    @classmethod
    def get_spaces(cls, values):
        return values.str.extract(r'.*(\/space\/\d+).*')

    @classmethod
    def ismatome(cls, values):
        return values.str.match(r'.*\/matome\/\d+.*')

    @classmethod
    def get_matomes(cls, values):
        return values.str.extract(r'.*(\/matome\/\d+).*')

    @classmethod
    def isreview(cls, values):
        return values.str.match(r'.*\/reviews\/\d+.*')

    @classmethod
    def get_reviews(cls, values):
        return values.str.extract(r'.*(\/reviews\/\d+).*')

    @classmethod
    def isowner(cls, values):
        return values.str.match(r'.*\/owners\/\d+.*')

    @classmethod
    def get_owners(cls, values):
        return values.str.extract(r'.*(\/owners\/\d+).*')

    @classmethod
    def get_page_types(cls, values):
        cls._check_if_values_are_paths(values)

        def determine_page_type(string):
            if re.match(r'.*(' + '|'.join(cls.categories) + ').*', string):
                return 'category'
            elif re.match(r'.*\/list\/.*', string):
                return 'feature'
            elif re.match(r'.*\/space\/\d+.*', string):
                return 'space'
            elif re.match(r'.*\/matome\/.*', string):
                return 'matome'
            elif re.match(r'.*\/(' + r'|'.join(cls.prefectures) + r')' + r'(\-w\d+|\-s\d+)?$', string) or re.match(r'^\/(' + r'|'.join(cls.areas) + r')$', string):
                return 'generic'
            elif re.match(r'.*\/reviews\/.*', string):
                return 'reviews'
            elif re.match(r'.*\/owners\/.*', string):
                return 'owners'
            elif re.match(r'.*\/guides\/.*', string):
                return 'guides'
            elif re.match(r'^(https\:\/\/www\.instabase\.jp)?\/?$', string):
                return 'toppage'
            else:
                return 'other'

        return values.apply(determine_page_type)

    @classmethod
    def get_area_types(cls, values):
        def determine_area_type(string):
            if re.match(r'.*s\d+.*', string):
                return 'station'
            elif re.match(r'.*w\d+.*', string):
                return 'ward'
            elif re.match(r'.*(' + '|'.join(cls.areas).replace('-', r'\-') + r').*', string):
                return 'area'
            elif re.match(r'.*(' + '|'.join(cls.prefectures) + r').*', string):
                return 'prefecture'
            else:
                return 'noarea'

        return values.apply(determine_area_type)

    @classmethod
    def get_prefectures(cls, values):
        cls._check_if_values_are_paths(values)
        return values.str.extract(r'^\/(' + r'|'.join(cls.prefectures) + r').*')

    @classmethod
    def get_areas(cls, values):
        cls._check_if_values_are_paths(values)
        return values.str.extract(r'^\/(' + r'|'.join(cls.areas).replace('-', r'\-') + r').*')

    @classmethod
    def get_wards(cls, values):
        return values.str.extract(r'.*(w\d+).*')

    @classmethod
    def get_stations(cls, values):
        return values.str.extract(r'.*(s\d+).*')

    @classmethod
    def _check_if_values_are_paths(cls, values: List[str]):
        "Checks if values are PATHs. Raises error if they include the DOMAIN, too."
        # Sample first 100 values to speed up check
        netloc_with_value = [len(urlparse(value).netloc)
                             != 0 for value in values[:100]]
        if sum(netloc_with_value) > 0:
            warnings.warn(
                "Some values appear to contain the domain. Please remove domain values from strings.")
