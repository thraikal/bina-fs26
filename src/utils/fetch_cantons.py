import io
import json
import zipfile
from pathlib import Path

import geopandas as gpd
import requests
import certifi

# URL copied from https://www.swisstopo.admin.ch/en/landscape-model-swissboundaries3d
URL = "https://data.geo.admin.ch/ch.swisstopo.swissboundaries3d/swissboundaries3d_2026-01/swissboundaries3d_2026-01_2056_5728.gpkg.zip"
LAYER = "tlm_kantonsgebiet"


def load_cantons_geojson(data_dir: Path) -> dict:
    cache = data_dir / "cantons.geojson"
    if not cache.exists():
        gpkg_bytes = _unzip_gpkg(_download_zip())
        _convert_to_geojson(gpkg_bytes, cache)
    with open(cache, encoding='utf-8') as f:
        return json.load(f)


def _download_zip() -> bytes:
    print("Downloading swissBOUNDARIES3D...")
    response = requests.get(URL, timeout=60, verify=certifi.where())
    response.raise_for_status()
    return response.content


def _unzip_gpkg(zip_bytes: bytes) -> bytes:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        gpkg_name = next(n for n in zf.namelist() if n.endswith(".gpkg"))
        return zf.read(gpkg_name)


def _convert_to_geojson(gpkg_bytes: bytes, dest: Path) -> None:
    gdf = gpd.read_file(io.BytesIO(gpkg_bytes), layer=LAYER).to_crs(4326)
    dest.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(dest, driver="GeoJSON")
    print(f"Saved to {dest}")
