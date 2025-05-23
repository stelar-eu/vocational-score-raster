# Vocational Score Raster

Generation of spatial raster maps representing vocational scores across different geographic areas, helping to visualize regional strengths in vocational skills. Turn raw-value rasters (e.g., temperature) into a single, interpretable “score” map that answers a yes/no or suitability question.

This version of VSR has been made compatible with the KLMS Tool Template and can be incorporated withing workflows. The tool is invoked in the form of a Task within a workflow Process via the respective API call. 

## Tool Invocation Example

An example spec for executing an autonomous instance of VSR through the API would be:

```json
{
    "process_id": "f9645b89-34e4-4de2-8ecd-dc10163d9aed",
    "name": "VSR on 1981-2021",
    "image": "petroud/vsr:latest",
    "inputs": {
        "rasters": [
            "d0::owned"
        ]
    },
    "datasets": {
        "d0": "16adb665-77ea-410c-8476-132e34160b53",
        "d1": {
            "name":"vsr-output-exp",
            "owner_org":"abaco-group",
            "notes": "The result of VSR execution on Summer and April Dataset VSR Input",
            "tags":["ABACO","VSR"]
        }
    },
    "parameters": {
        "Tmax_max_summer_1981_1990.tif": {"val_min": 26, "val_max": 28.5, "new_val": 1},
        "Tmax_max_summer_1991_2000.tif": {"val_min": 26, "val_max": 28.5, "new_val": 1},
        "Tmax_max_summer_2001_2010.tif": {"val_min": 26, "val_max": 28.5, "new_val": 1},
        "Tmax_max_summer_2011_2021.tif": {"val_min": 26, "val_max": 28.5, "new_val": 1},
        "Tmin_min_april_1981_1990.tif": {"val_min": 0.5, "val_max": 8, "new_val": 1},
        "Tmin_min_april_1991_2000.tif": {"val_min": 0.5, "val_max": 8, "new_val": 1},
        "Tmin_min_april_2001_2010.tif": {"val_min": 0.5, "val_max": 8, "new_val": 1},
        "Tmin_min_april_2011_2021.tif": {"val_min": 0.5, "val_max": 8, "new_val": 1}
    },
    "outputs": {
        "scored_files": {
            "url": "s3://abaco-bucket/VOCATIONAL_SCORE/output",
            "dataset": "d1",
            "resource": {
                "name": "Scored Classified rasters via VSR",
                "relation": "raster"
            }
        }
    }
}
```

## Tool Input JSON
At runtime the tool expects the following, translated by the API json: 
```json

{
        "input": {
            "rasters": [
                "s3://abaco-bucket/VOCATIONAL_SCORE/input/Tmax_max_summer_1981_1990.tif",
                "s3://abaco-bucket/VOCATIONAL_SCORE/input/Tmax_max_summer_2001_2010.tif",
                "s3://abaco-bucket/VOCATIONAL_SCORE/input/Tmax_max_summer_1991_2000.tif",
                "s3://abaco-bucket/VOCATIONAL_SCORE/input/Tmax_max_summer_2011_2021.tif",
                "s3://abaco-bucket/VOCATIONAL_SCORE/input/Tmin_min_april_1981_1990.tif",
                "s3://abaco-bucket/VOCATIONAL_SCORE/input/Tmin_min_april_2001_2010.tif",
                "s3://abaco-bucket/VOCATIONAL_SCORE/input/Tmin_min_april_2011_2021.tif",
                "s3://abaco-bucket/VOCATIONAL_SCORE/input/Tmin_min_april_1991_2000.tif"
            ]
        },
        "minio": {
            "endpoint_url": "https://minio.stelar.gr",
            "id": "XXXXXXXXXXX",
            "key": "XXXXXXXXXXX",
            "skey": "XXXXXXXXXXX"
        },
        "output": {
            "scored_files": "s3://abaco-bucket/VOCATIONAL_SCORE/output"
        },
        "parameters": {
            "Tmax_max_summer_1981_1990.tif": {
                "new_val": 1,
                "val_max": 28.5,
                "val_min": 26
            },
            "Tmax_max_summer_1991_2000.tif": {
                "new_val": 1,
                "val_max": 28.5,
                "val_min": 26
            },
            "Tmax_max_summer_2001_2010.tif": {
                "new_val": 1,
                "val_max": 28.5,
                "val_min": 26
            },
            "Tmax_max_summer_2011_2021.tif": {
                "new_val": 1,
                "val_max": 28.5,
                "val_min": 26
            },
            "Tmin_min_april_1981_1990.tif": {
                "new_val": 1,
                "val_max": 8,
                "val_min": 0.5
            },
            "Tmin_min_april_1991_2000.tif": {
                "new_val": 1,
                "val_max": 8,
                "val_min": 0.5
            },
            "Tmin_min_april_2001_2010.tif": {
                "new_val": 1,
                "val_max": 8,
                "val_min": 0.5
            },
            "Tmin_min_april_2011_2021.tif": {
                "new_val": 1,
                "val_max": 8,
                "val_min": 0.5
            }
        }
}
```
### `input`

Provide the raw .TIF file paths under the `rasters` input group. List each file path on a new line or within a JSON array, ensuring that every file has a corresponding entry in the `parameters` field.

### `parameters`

In a nutshell, for each Raster .TIF file provided as input, respective criteria per file are populating the `parameters` field. These criteria include:
-    `new_val`: (float) Lower bound of the source-pixel value range to accept (inclusive). 
-    `val_max`: (float) Upper bound of that range (inclusive).	
-    `val_min`: (float) Score (or weight) to add to every pixel that falls inside that range.

According to this criteria each raster is re-classified based to the rule "if pixel is inside the ‘comfort’ temperature window, award with 1"

### `output`

The output field at tool's level defines the output directory where the classified rasters are destined to be written. The tool produces the following output objects:
- A re-classified `_classificato_test.tif` per input file that lands in the bucket 
- The `COMBO_OUT.tif`, a running “combo” raster that sums the classified values from all rasters

## Tool Output JSON
Upon successful execution the tool will propagate the following output to the API. The `metrics` include the coverage (%) of pixels that satisfied the provided parameters for the file and are consired indeed **suitable**.
```json
{
    "message": "Tool Executed Successfully",
    "output": {
        "scored_files": "s3://abaco-bucket/VOCATIONAL_SCORE/output"
    },
    "metrics": {
        "Tmax_max_summer_1981_1990.tif_coverage": 19.87,
        "Tmax_max_summer_1991_2000.tif_coverage": 19.49,
        "Tmax_max_summer_2001_2010.tif_coverage": 13.33,
        "Tmax_max_summer_2011_2021.tif_coverage": 13.33,
        "Tmin_min_april_1981_1990.tif_coverage": 0.0,
        "Tmin_min_april_1991_2000.tif_coverage": 0.0,
        "Tmin_min_april_2001_2010.tif_coverage": 0.0,
        "Tmin_min_april_2011_2021.tif_coverage": 0.0
    },
    "status": "success"
}
```


## How to build 
Alter the `IMGTAG` in Makefile with a repository from your Image Registry and hit 
`make` in your terminal within the same directory.