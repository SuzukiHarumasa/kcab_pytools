import numpy as np
import pandas as pd
import geopandas as gpd
import folium
import branca.colormap as cm

# try:
#     import importlib.resources as pkg_resources
# except ImportError:
#     # Try backported to PY<37 `importlib_resources`.
#     import importlib_resources as pkg_resources
# from .geodata import prefectures
# from .geodata import wards

# import pkgutil

# prefectures_shapefile = pkgutil.get_data(__name__, "geodata/prefectures/prefectures.shp")
# wards_shapefile = pkgutil.get_data(__name__, "geodata/wards/wards.shp")

import pkg_resources
prefectures_shapefile = pkg_resources.resource_filename(__name__, "geodata/prefectures/prefectures.shp")
wards_shapefile = pkg_resources.resource_filename(__name__, "geodata/wards/wards.shp")

# prefectures_shapefile = pkg_resources.read_text(prefectures, 'prefectures.shp')
# wards_shapefile = pkg_resources.read_text(wards, 'wards.shp')

class IbMapper:
    COORDS = {"東京": [35.6762, 139.6503]}

    def __init__(self):
        self.pref_data = gpd.read_file(prefectures_shapefile)
        self.ward_data = gpd.read_file(wards_shapefile)

        print("Geo data loaded...")

    def Map(self, center=None, location=None, **kwargs):
        if center is not None:
            location = self.__class__.COORDS[center]

        params = {
            "location": location,
            "zoom_start": 9,
            "zoom_control": True
        }
        params.update(kwargs)
        return folium.Map(**params)

    def plot_wards(self, df, value_col, prefecture=None, ward=None,
                cmap='BuPu_09', layername='市区町村', tooltip_fields=None,
                colorbar=False, layercontrol=False, **kwargs):
        """
        Maps data to wards.
        The DataFrame must have a column `ward` or `JCODE` as a key_col to match with the polygon data.

        Inputs:
            - TBD: Add inputs here.

        """

        assert df.index.name in ('ward', 'JCODE'), \
            "Index name must be `ward`, or `JCODE`."

        layername = f'{value_col} by {layername}'

        m = self.Map(center='東京', **kwargs)
        m = self.add_layer(m, df, value_col, plot_by='ward', prefecture=prefecture, ward=ward,
                            cmap=cmap, layername=layername, tooltip_fields=tooltip_fields,
                            colorbar=colorbar, layercontrol=layercontrol)
        return m

    def plot_prefectures(self, df, value_col, prefecture=None, ward=None,
                cmap='BuPu_09', layername='都道府県', tooltip_fields=None,
                colorbar=False, layercontrol=False, **kwargs):
        """
        Maps data to prefectures.
        The DataFrame must have a column `prefecture` as a key_col to match with the polygon data."""

        assert df.index.name == 'prefecture', "Index name must be `prefecture`."

        layername = f'{value_col} by {layername}'

        m = self.Map(center='東京', **kwargs)
        m = self.add_layer(m, df, value_col, plot_by='prefecture', prefecture=prefecture, ward=ward,
                            cmap=cmap, layername=layername, tooltip_fields=tooltip_fields,
                            colorbar=colorbar, layercontrol=layercontrol)
        return m

    def add_layer(self, m, df, value_col, plot_by='ward', prefecture=None, ward=None,
                        cmap='BuPu_09', layername="", tooltip_fields=None,
                        colorbar=False, layercontrol=False):
        """
        Adds a Choropleth layer to the map specified by `m`.
        Layer will be colored according to the values specified by `value_col` in `df`.
        Choose a plot mode from (`ward`, `prefecture`).
        """
        # Make sure that the key column is formatted as a str.
        df = df.copy()
        key_col = df.index.name
        df.reset_index(inplace=True)
        df[key_col] = df[key_col].astype(str)

        # Prepare polygon data.
        if plot_by == 'ward':
            plot_by_title = '市区町村'
            polydata = self.ward_data.copy()
        elif plot_by == 'prefecture':
            plot_by_title = '都道府県'
            polydata = self.pref_data.copy()
        else:
            raise Exception("plot_by must be either `ward` or `prefecture`.")

        # Check whether to filter the data by user-provided filtering parameters prefecture and ward.
        if prefecture is not None:
            polydata = polydata[polydata['prefecture'].str.match(prefecture)]
        if ward is not None:
            polydata = polydata[polydata['ward'].str.match(ward)]

        # Inner merge data with polygon data. This drops any wards without data.
        polydata = polydata.merge(df, how='inner', left_on=key_col, right_on=key_col)

        # Make sure that no values are nan.
        if plot_by == 'ward':
            polydata.drop(polydata[polydata["JCODE"].isna()].index, axis=0, inplace=True)
        elif plot_by == 'prefecture':
            polydata.drop(polydata[polydata["prefecture"].isna()].index, axis=0, inplace=True)
        polydata.drop(polydata[polydata[value_col].isna()].index, axis=0, inplace=True)

        # Specify tooltip fields.
        if tooltip_fields is None:
            tooltip_fields = [value_col]
        else:
            tooltip_fields = [value_col] + tooltip_fields

        # Specify coloring scheme.
        linear = self._colorfunc(polydata[value_col], cmap=cmap)

        # Set layername if nothing is provided.
        if layername == "":
            layername = f'{value_col} by {plot_by_title}'

        folium.GeoJson(
            data=polydata.to_json(),
            name=layername,
            smooth_factor=1,
            style_function=lambda feature: {
                'fillColor': linear(feature['properties'][value_col]),
                'fillOpacity': 0.7,
                'color': 'grey',
                'weight': 1,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['prefecture', plot_by] + tooltip_fields,
                aliases=['都道府県', plot_by_title] + tooltip_fields,
                labels=True,
                sticky=True,
                localize=True),
            highlight_function=lambda x: {'weight':2, 'fillOpacity':0.9}
        ).add_to(m)

        if colorbar:
            linear.caption = value_col
            linear.add_to(m)

        if layercontrol:
            folium.LayerControl().add_to(m)

        return m


    def _colorfunc(self, series, cmap='BuPu_09', vmin=None, vmax=None):
        vmin = vmin or series.quantile(0.05)
        vmax = vmax or series.quantile(0.95)
        return getattr(cm.linear, cmap).scale(vmin, vmax).to_step(10)

