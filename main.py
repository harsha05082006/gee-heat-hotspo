import ee
import datetime

# ================= AUTH =================
# 🔑 Use service account (required for GitHub Actions)
credentials = ee.ServiceAccountCredentials(
    None,
    'key.json'   # this file is created from GitHub secret
)

ee.Initialize(credentials, project='innate-shape-475500-v8')

print("✅ Earth Engine initialized")

# ================= AOI =================
aoi = ee.Geometry.Point([80.6480, 16.5062]).buffer(5000)

# ================= DATE =================
today = datetime.date.today()
start = today - datetime.timedelta(days=30)

# ================= NDVI =================
s2 = ee.ImageCollection('COPERNICUS/S2_SR') \
    .filterBounds(aoi) \
    .filterDate(str(start), str(today)) \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
    .select(['B4', 'B8']) \
    .median()

ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')

# ================= LST =================
l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
    .filterBounds(aoi) \
    .filterDate(str(start), str(today)) \
    .select('ST_B10') \
    .median()

lst = l8.multiply(0.00341802).add(149.0).subtract(273.15).rename('LST')

# ================= REMOVE WATER =================
waterMask = ndvi.lt(0)
lst_filtered = lst.updateMask(waterMask.Not())

# ================= HOTSPOT LOGIC =================
hotspots = ndvi.lt(0.3).And(lst_filtered.gt(32)).selfMask()

# ================= DATE TAG =================
date_str = today.strftime("%Y-%m-%d")

# ================= EXPORT =================
task = ee.batch.Export.image.toDrive(
    image=hotspots,
    description='Auto_Heat_Hotspots_' + date_str,
    folder='GEE_Output',
    fileNamePrefix='HeatHotspot_' + date_str,
    scale=30,
    region=aoi,
    maxPixels=1e13
)

task.start()

print("✅ Export started successfully 🚀")
