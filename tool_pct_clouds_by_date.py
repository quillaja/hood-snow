# uses the cloud mask (CLM) band of the mask rasters to determine the
# percent cloud cover (which is equal to the binary mask's mean value)
# that is actually in the Hood AOI, for each date. The date, mean, and other
# statistics are written to a csv file.

import csv
from os.path import join
from pathlib import Path

import arcpy

RASTER = [str(p) for p in Path(r"E:\sensing\hood_snow\data\images").glob("*_masks.tif")]
OUTFILE = "E:/sensing/hood_snow/data/clouds.csv"


def raster_stats(raster_name: str, cloud_mask_band: str = "CLM") -> dict:
    """
    Return the percent cloud cover of the raster based on the cloud mask band.
    """
    r = arcpy.Raster(join(raster_name, cloud_mask_band))
    # computeStatistics() gives list of dict with stats, presumably one dict
    # per band. This just needs the first one.
    return r.computeStatistics()[0]


if __name__ == "__main__":
    data: list[dict] = []
    for raster in RASTER:
        stats = raster_stats(raster)
        date = Path(raster).stem.removesuffix("_masks")
        stats["date"] = date
        data.append(stats)

    with Path(OUTFILE).open("w", newline="") as file:
        w = csv.DictWriter(file, fieldnames=data[0].keys())
        w.writeheader()
        w.writerows(data)

    arcpy.AddMessage(f"wrote {OUTFILE}")
