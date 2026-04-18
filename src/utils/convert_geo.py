import geopandas as gpd
from pathlib import Path

ROOT = Path(__file__).parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_OUT = ROOT / "data"

# file 'swissboundaries3d_2026-01_2056_5728.gpkg.zip' downloaded from:
# https://www.swisstopo.admin.ch/en/landscape-model-swissboundaries3d
gdf_lv95 = gpd.read_file(DATA_RAW / "swissBOUNDARIES3D_1_5_LV95_LN02.gpkg", layer="tlm_kantonsgebiet")
gdf_wgs84 = gdf_lv95.to_crs(4326)
gdf_wgs84.to_file(DATA_OUT / "cantons.geojson", driver="GeoJSON")