# This is script may only work with sentinelhub.__version__ >= '3.4.0'
#
# Run this script in the root project folder "hood_snow".
# It expects a file with a UTMZ10N geojson area of interest,
# and a json file containing search result data from the
# senthub_search.py script. Sentinel Hub credentials are in util.py
# (don't check them into git!).
#
# this script requires the environment (venv) described in requirements.txt

import json
import shutil
import tarfile
from pathlib import Path

from sentinelhub import (CRS, BBox, DataCollection, Geometry, MimeType,
                         MosaickingOrder, SentinelHubRequest, SHConfig)

from senthub_util import Scripts, extract_dates, get_config, read_aoi

# Credentials
config = get_config()

# query configuration
hood_aoi = read_aoi("hood_aoi_32610.geojson")
resolution = (10, 10)  # meters per pixel (because UTM geometry); degrees per px if WGS84
search_results = extract_dates("search_results_max.json")
# download locations
download_root = Path("data")  # root of all data
download_root.mkdir(exist_ok=True)
download_dst_dir = Path(download_root, "downloads")  # downloaded data
download_dst_dir.mkdir(exist_ok=True)
final_dst_dir = Path(download_root, "images")  # folder where images will be copied
final_dst_dir.mkdir(exist_ok=True)
download_index = Path(download_root, "download_index.json")  # map download dir to date

if not download_index.exists():
    download_index.write_text(json.dumps({}))
dl_index = json.loads(download_index.read_text())


# do a separate request for each date in the results.
# there might be a more efficient way to do this using the batch api,
# but this was enough for my purposes
for date, clouds in search_results.items():

    # used to low-tech filter and reduce requested dataset during script testing
    # if not date.startswith("2017-11-24"):
    #     continue

    # create the request
    request = SentinelHubRequest(
        evalscript=Scripts.final_data_request_script,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                mosaicking_order=MosaickingOrder.LEAST_CC,
                time_interval=(date, date)),
        ],
        responses=[
            SentinelHubRequest.output_response('spectral', MimeType.TIFF),
            SentinelHubRequest.output_response('masks', MimeType.TIFF),
        ],
        # bbox=bbox,
        geometry=hood_aoi,
        # size=[1332, 1362],
        resolution=resolution,
        config=config,
        data_folder=download_dst_dir)

    # submit and save result
    print(f"{date} has {len(clouds)} images with average {sum(clouds)/len(clouds):0.2f}% cloud cover.")
    response = request.get_data(save_data=True, show_progress=True)
    # script only has 1 download (tiff or tar), but do the list thing anyway
    downloads = [Path(download_dst_dir, f).resolve() for f in request.get_filename_list()]

    # because I requested 2 files (spectral and masks), it comes in a tar archive.
    # this untars the files and copies them to their final destinations, keeping
    # the originally downloaded data. This also writes a list of the original
    # folders for each requested date so I can find specific original data if necessary
    for d in downloads:
        dl_index[d.parent.name] = date  # save just the hash or whatever
        # extract
        if d.suffix.lower() == ".tar":
            print(f" got a tar")
            # extract files
            with tarfile.open(d) as tar:
                tar.extractall(d.parent)
                srcs = [Path(d.parent, name) for name in tar.getnames()]
            # d.unlink()  # DELETE tar file
        else:
            print(f" got an image (or something else)")
            srcs = [d]

        # copy
        for src in srcs:
            dst = Path(final_dst_dir, f"{date}_{src.name}")
            print(f" {src} -> {dst}")
            shutil.copy(src, dst)

# write folder index
download_index.write_text(json.dumps(dl_index))
