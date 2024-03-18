# Seasonal Snowline Fluctuations on Mt Hood
Using Sentinel-2 imagery to locate and track the location of the snowline on Mt Hood over 7 years. This is my final project for PCC's GEO246 (Remote Sensing).

## Sources

|Data        |Source
|---|---|
|DEM         |National Map 3DEP
|imagery     |SentinelHub
|snotel      |USDA
|weather     |NWAC

## Misc stats

|Stat                |Info
|---|---
|data dates:         |2017-01-03 to 2024-02-21
|number dates:       |443
|timespan:           |2605 days (7.13 years)
|data size:          |5 GiB
|download time:      |108 min (about 15s/request)
|processing time:    |80 min (about 11s/raster)

## Public github items
- sentinel hub data request (uses venv from requirements.txt)
    - senthub_request.py
    - senthub_search.py
    - senthub_util.py
- arcpy processing (uses arcgis conda env)
    - tool_calculate_pct_snow.py
    - tool_pct_clouds_by_date.py
    - tool_rename_bands.py
- analysis notebooks (uses arcgis conda env)
    - explore.ipynb
    - visualization.ipynb
- data
    - prepared_data.csv
    - prepared_weather.csv
- other
    - poster.png
    - hood_aoi_32610.geojson
    - requirements.txt
    - README.md (github)

# Validation / verification

Information used:
```
snowtel 651     https://wcc.sc.egov.usda.gov/nwcc/site?sitenum=651
                45.316667, -121.716667
                1635m (5370ft)
                1980-present
                snow water equiv, min, max, mean temp, total precip, accum precip
NWAC ski telem  https://nwac.us/data-portal/location/mt-hood/
                ski lifts at TL, MHM, SB
                various elev
                2016-present
                temp, wind, humidity, precip, snow depth, pressure
```

# Issues
## Mask classification values

- 'usable' area:
    - NDVI        <= 0.0
    - Cloud Prob  <  50%

_NOTE_ NDVI <= 0 seems to work well for winter/snow covered conditions, but undercounts 'usable' area (by ignoring bare pumice) in the summer. < 0.15-0.18 would have worked better for summer. The consequence of this overestimating the `pct_usable_snow`.

(Note: 'usuable' renamed 'countable' in poster.)

## Sudden drops in snowline chart

In 2020, 2021, and 2023 there are odd spots in the snowline chart where the elevation suddenly becomes 1300m even though the heatmap shows nothing of the sort. The issue is that in those times, there _is no elevation with > 0.4 snow_, so `.gt().idxmax()` returns the first index of the year (which corresponds to 1300m generally) instead of a meaningful result. A lower snow threshold _should_ solve this issue.