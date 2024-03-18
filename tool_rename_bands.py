# This arcgis pro script tool renames the raster bands of each raster
# in a folder. Each raster with the same number of bands as the new
# band list will be have its bands renamed. Rasters with a band count
# mismatch will be skipped.

from itertools import chain
from pathlib import Path

import arcpy


def get_rasters(folder: str, globs: list[str] = ["*.tif", "*.tiff"]) -> list[Path]:
    """Find all rasters in `folder` that match the glob patterns."""
    dir = Path(folder).resolve()
    rasters_paths = list(chain(*[dir.glob(pattern) for pattern in globs]))
    return rasters_paths


def rename_rasters(raster_paths: list[Path], new_bands: list[str]):
    """
    Rename the bands of each raster to the names in `new_bands`. This requires
    each raster to have the same number of bands, and also the same number of
    bands as items in `new_bands`. Any errors encountered will skip the
    problem raster and continue to the next raster.
    """
    for p in raster_paths:
        raster = arcpy.Raster(str(p))  # str required
        num_bands = raster.bandCount
        if len(new_bands) != num_bands:
            arcpy.AddWarning(f"could not rename bands in {raster}: band count mismatch")
            continue

        arcpy.AddMessage(f"renaming bands in {raster}")
        arcpy.AddMessage(f" old bands: {raster.bandNames}")
        for old, new in zip(raster.bandNames, new_bands):
            # apparently renameBand() can't rename a band if the old and new names are the same
            try:
                if old != new:
                    raster.renameBand(old, new)
            except:
                arcpy.AddWarning(f"  failed to rename {old} -> {new}: skipping")
        arcpy.AddMessage(f" new bands: {raster.bandNames}")


def undelimit(delimited: str) -> list[str]:
    """Makes a list from a comma or semicolon delimited string."""
    return [s.strip() for s in delimited.replace(",", ";").split(";")]


if __name__ == "__main__":
    RASTER_FOLDER = 0
    NEW_BAND_DELIMITED = 1
    GLOBS_DELIMITED = 2

    raster_folder = arcpy.GetParameterAsText(RASTER_FOLDER)  # folder input
    new_bands_delimited: str = arcpy.GetParameterAsText(NEW_BAND_DELIMITED)  # str input
    globs_delimited: str = arcpy.GetParameterAsText(GLOBS_DELIMITED)  # str input, optional

    # uncomment and change these to use the script 'stand alone'
    # raster_folder = "E:/sensing/hood_snow/data/images"
    # globs_delimited = "*_spectral.tif"
    # new_bands_delimited = "B1, B2, B3, B4, B5, B6, B7, B8, B8A, B9, B11, B12"

    new_bands = undelimit(new_bands_delimited)
    globs = undelimit(globs_delimited)

    rasters = get_rasters(raster_folder, globs=globs)
    arcpy.AddMessage(f"found {len(rasters)} in {raster_folder}")
    arcpy.AddMessage(f"new bands: {new_bands}")
    rename_rasters(rasters, new_bands)
