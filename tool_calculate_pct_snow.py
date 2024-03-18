# takes mask raster for a particular date and the contour polygon layer,
# then does zonal statistics to table for each mask. Combines the two tables
# into one and joins it to the polygon layer. Finally, exports the table as csv.

from os.path import join
from pathlib import Path
from typing import NamedTuple

import arcpy
import arcpy.sa

# geodatabase of project
arcpy.env.workspace = "E:/sensing/hood_snow/gis/hood_snow.gdb"
# the elevation polygons. rings is far superior to levels.
CONTOURS = "contour_rings"
# CONTOURS = "contour_levels"
# Get a list of every raster's path
RASTER = [str(p) for p in Path(r"E:\sensing\hood_snow\data\images").glob("*_masks.tif")]


class ZonalStatsTables(NamedTuple):
    """Group the resulting table names for convenience."""
    snow: str
    usable: str
    usable_snow: str


def zonal_stats(contour_zones: str, raster_name: str,
                zone_field: str = "OBJECTID",
                snow_band: str = "snow_mask",
                usable_band: str = "usable_snow_mask") -> ZonalStatsTables:
    """Create 3 tables of zonal stats from the zones in contour_zones and
    the data in raster_name. The field in `contour_zones` is specified with `zone_field`.
    `snow_band` should be the band name containing
    the snow mask, and `usable_band` should be the name of the band containing
    the usable snow area mask.
    """

    tables = ZonalStatsTables(
        snow="in_memory/snow",
        usable="in_memory/usable",
        usable_snow="in_memory/usable_snow")

    snow = arcpy.Raster(join(raster_name, snow_band))
    usable = arcpy.Raster(join(raster_name, usable_band))
    usable_snow = snow * usable  # raster calculator in a python script

    arcpy.sa.ZonalStatisticsAsTable(
        in_zone_data=contour_zones,
        zone_field=zone_field,
        in_value_raster=snow,
        statistics_type="Sum",
        out_table=tables.snow)

    arcpy.sa.ZonalStatisticsAsTable(
        in_zone_data=contour_zones,
        zone_field=zone_field,
        in_value_raster=usable,
        statistics_type="Sum",
        out_table=tables.usable)

    arcpy.sa.ZonalStatisticsAsTable(
        in_zone_data=contour_zones,
        zone_field=zone_field,
        in_value_raster=usable_snow,
        statistics_type="Sum",
        out_table=tables.usable_snow)

    return tables


def join_data(contours: str, tables: ZonalStatsTables) -> str:
    """
    Join the tables from zonal stats step to contours. Return the name
    of the new *temporary* table with all the data.
    """

    joined_table = "in_memory/contours"

    arcpy.CopyFeatures_management(in_features=contours, out_feature_class=joined_table)

    for table in tables:
        joined_table = arcpy.AddJoin_management(
            in_layer_or_view=joined_table,
            in_field="OBJECTID",
            join_table=table,
            join_field="OBJECTID_1")

    data_table = "in_memory/data_table"
    arcpy.CopyFeatures_management(joined_table, data_table)
    return data_table


def finalize_data_table(table: str) -> str:
    """ 
    Calculate the percent snow, creating a new field. Remove redundant fields
    and rename others to better names.
    """
    # arcpy.AddMessage([f.baseName for f in arcpy.ListFields(table)])

    # fields without cleaning are:
    # ['OBJECTID', 'Shape', 'contours_ContourMin', 'contours_ContourMax', 'contours_Shape_Length', 'contours_Shape_Area',
    # 'snow_OBJECTID', 'snow_OBJECTID_1', 'snow_COUNT', 'snow_AREA', 'snow_SUM',
    # 'usable_OBJECTID', 'usable_OBJECTID_1', 'usable_COUNT', 'usable_AREA', 'usable_SUM',
    # 'usable_snow_OBJECTID', 'usable_snow_OBJECTID_1', 'usable_snow_COUNT', 'usable_snow_AREA', 'usable_snow_SUM']
    keep = ['contours_ContourMin', 'contours_ContourMax',
            'snow_COUNT', 'snow_AREA', 'snow_SUM',
            'usable_COUNT', 'usable_AREA', 'usable_SUM',
            'usable_snow_COUNT', 'usable_snow_AREA', 'usable_snow_SUM']
    arcpy.DeleteField_management(
        in_table=table,
        method="KEEP_FIELDS",
        drop_field=keep)

    # rename some kept fields
    for old, new in [('contours_ContourMin', 'contour_min'), ('contours_ContourMax', 'contour_max')]:
        arcpy.AlterField_management(in_table=table, field=old, new_field_name=new)

    arcpy.CalculateField_management(
        in_table=table,
        field="pct_snow",
        field_type="FLOAT",
        expression="!snow_SUM!/!snow_COUNT!")

    arcpy.CalculateField_management(
        in_table=table,
        field="pct_usable",
        field_type="FLOAT",
        expression="!usable_SUM!/!usable_COUNT!")

    arcpy.CalculateField_management(
        in_table=table,
        field="pct_usable_snow",
        field_type="FLOAT",
        expression="(!usable_snow_SUM!)/!usable_SUM!")  # i think this is it

    return table


if __name__ == "__main__":
    for raster in RASTER:
        csv_path = Path(raster).with_suffix(".csv")
        # csv_path = csv_path.with_stem(csv_path.stem + "_levels") # tag using contour_levels
        csv_path.unlink(missing_ok=True)  # remove csv to prevent export error

        arcpy.Delete_management("in_memory")  # clear memory workspace

        stats_tables = zonal_stats(CONTOURS, raster)
        data_table = join_data(CONTOURS, stats_tables)
        finalize_data_table(data_table)  # alters table

        arcpy.ExportTable_conversion(data_table, str(csv_path))
        arcpy.AddMessage(f"wrote {csv_path}")
