# Uses the sentinel hub search API to find all data in the mt hood study area,
# including any cloud cover (cloudy data removed in later step).
#
# result can be loaded into ArcGIS when the extra FeatureCollection wrapper
# is added to make the result (semi?) correct geojson.
#
# this script requires the environment (venv) described in requirements.txt

import json
from pathlib import Path

from sentinelhub import (CRS, BBox, DataCollection, Geometry,
                         SentinelHubCatalog, SHConfig)

import senthub_util as util

# Credentials
config = util.get_config()

# search params
hood_poly = util.read_aoi("hood_aoi_32610.geojson")
time_interval = "2014-07-01", "2024-03-01"
cloud_percent = 100
result_file = "search_results_max.json"

catalog = SentinelHubCatalog(config)

# do actual search
search_iterator = catalog.search(
    DataCollection.SENTINEL2_L2A,
    geometry=hood_poly,
    time=time_interval,
    filter=f"eo:cloud_cover < {cloud_percent}")

results = list(search_iterator)
print("Total number of results:", len(results))

# save results
with Path(result_file).open('w') as file:
    geojson = '{"type": "FeatureCollection","features":'+json.dumps(results, indent=2)+'}'
    file.write(geojson)
