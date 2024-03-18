# this script provides some useful functions and the javascript
# for the processing api.

import json
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from sentinelhub import CRS, Geometry, SHConfig


def get_config() -> SHConfig:
    """Create and return config with client id and secret."""
    config = SHConfig()
    config.sh_client_id = "YOUR_CLIDENT_ID"
    config.sh_client_secret = "YOUR_CLIENT_SECRET"  # cannot recover this
    return config


def read_aoi(filename: str, feature_index: int = 0) -> Geometry:
    """ Read AOI/study area outline from geojson """
    p = Path(filename).resolve()
    data: dict = json.loads(p.read_text())
    geom = data["features"][feature_index]["geometry"]
    crs = data["crs"]["properties"]["name"]  # ie epsg string
    return Geometry(geometry=geom, crs=CRS(crs))


def extract_dates(result_file: str) -> dict[str, list[float]]:
    """ 
    Get the dates and cloud cover(s) for each item in the
    results obtained via the sentinel hub search api.
    """
    data: dict = json.loads(Path(result_file).read_text())
    all_dates = {}
    for result in data["features"]:
        props = result["properties"]
        day = str(datetime.fromisoformat(props["datetime"]).date())
        cloud = props["eo:cloud_cover"]
        all_dates.setdefault(day, []).append(cloud)
    return all_dates


class Scripts(StrEnum):
    default_script = """
//VERSION=3

function setup() {
  return {
    input: ["B02", "B03", "B04"],
    output: { bands: 3 }
  };
}

function evaluatePixel(sample) {
  return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
}
"""

    # this is the processing script used for my final big data request
    final_data_request_script = """
//VERSION=3

function setup() {
  return {
    input: ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12", "SCL", "SNW", "CLD", "CLP", "CLM", "dataMask"],
    output: [
        {id: "spectral", bands: 12, sampleType: "UINT8" },
        {id: "masks", bands: 7, sampleType: "UINT8" }
    ]
  };
}

/**
 * Uses NDSI and NDVI to create a mask for snow (1) or not snow (0).
 */
function snow_mask(sample) {
    var NDSI = (sample.B03 - sample.B11) / (sample.B03 + sample.B11);
    var NDVI = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
        function si(a) {
            // a = NDSI
            // if NDSI >= 0.4 then YES
            // else if NDVI in [0.075, 0.125] then YES
            // else NO
            return (a>=0.4) ? 1 : (Math.abs(NDVI - 0.1) <= 0.025 ? 1 : 0);
        }
    
        function br(a) {
            //  a = GREEN band
            // if GREEN > 0.3 then YES
            // else NO
            return a>0.3;
        }
    return si(NDSI) && br(sample.B03);
}

/**
 * Uses cloud probability (CLD) and NDVI to create a mask for whether a
 * pixel is usable and should be included in the snow calculations (1) or not (0).
 */
function usable_snow_mask(sample) {
    // var NDSI = (sample.B03 - sample.B11) / (sample.B03 + sample.B11);
    var NDVI = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
    return sample.CLD < 50.0 && NDVI <= 0.0 
}

function evaluatePixel(sample) {
  return { 
    spectral: [255*sample.B01, 255*sample.B02, 255*sample.B03, 255*sample.B04, 255*sample.B05, 255*sample.B06, 
        255*sample.B07, 255*sample.B08, 255*sample.B8A, 255*sample.B09, 255*sample.B11, 255*sample.B12],
    masks: [snow_mask(sample), usable_snow_mask(sample),
        sample.SCL, sample.SNW, sample.CLD, sample.CLM, sample.dataMask]
    };
}
"""

    snow_classifier_script = """
//VERSION=3
function setup () {
    return{
        input:["B02", "B03", "B04", "B08", "B11", "dataMask"],
        output:{bands: 4}
    }        
}

function evaluatePixel(sample) {
    var NDSI = (sample.B03 - sample.B11) / (sample.B03 + sample.B11);
    var NDVI = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
    var gain = 2.5;
        function si(a) {
            return (a>=0.4) ? 1 : (Math.abs(NDVI - 0.1) <= 0.025 ? 1 : 0);
        }
    
        function br(a) {
            return a>0.3;
        }
    var v = si(NDSI) && br(sample.B03);
return (v==1) ? [0,0.6,1, sample.dataMask] : [...[sample.B04, sample.B03, sample.B02].map(a => gain * a), sample.dataMask]
}
"""
