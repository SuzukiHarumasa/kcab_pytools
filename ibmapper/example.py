from .ibmapper import IbMapper

shapefile = './data/japan_rvis_h25/japan_rvis_h25.shp'
mapper = IbMapper(shapefile, encoding='shift-jis')

mapper.data.head()

m = mapper.map_series('東京都')







