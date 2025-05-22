import json
import sys
import traceback
import os
import numpy as np
import rasterio
from utils.mclient import MinioClient


# ------------------------------------------------------------------
# CONFIG – keep the nodata value from the original desktop script
# ------------------------------------------------------------------
OUTPUT_NODATA = -9999
LOCAL_WORKDIR = "/tmp/voc_score"  # local scratch
LOCAL_IN_DIR = os.path.join(LOCAL_WORKDIR, "in")
LOCAL_OUT_DIR = os.path.join(LOCAL_WORKDIR, "out")
os.makedirs(LOCAL_IN_DIR, exist_ok=True)
os.makedirs(LOCAL_OUT_DIR, exist_ok=True)


def run(json_input):
    try:
        # 1. ────────── MinIO session ──────────
        minio_id = json_input["minio"]["id"]
        minio_key = json_input["minio"]["key"]
        minio_skey = json_input["minio"]["skey"]
        minio_endpoint = json_input["minio"]["endpoint_url"]

        mc = MinioClient(
            minio_endpoint, minio_id, minio_key, secure=True, session_token=minio_skey
        )

        # 2. ────────── IO paths & criteria ──────────
        input_paths = json_input["input"]["rasters"]  # list of s3://… rasters
        output_folder = json_input["output"]["scored_files"].rstrip(
            "/"
        )  # s3:// bucket/folder
        criteria_raw = json_input["parameters"]  # {filename : {...} }

        # Transform criteria dict so each filename maps to a **list** of criteria,
        # allowing multi-row cases exactly like the CSV version.
        criteria = {}
        for fname, spec in criteria_raw.items():
            if isinstance(spec, list):
                criteria[fname] = spec
            else:
                criteria[fname] = [spec]  # wrap single row in list

        # storage for global combo
        combo_array = None
        combo_profile = None
        metrics = {}

        # 3. ────────── loop over rasters ──────────
        for fname, crit_list in criteria.items():

            # locate full S3 path for this raster
            s3_path = next((p for p in input_paths if p.endswith(fname)), None)
            if s3_path is None:
                print(f"[WARN] {fname} missing in input list - skipped.")
                continue

            # download to local cache
            local_in = os.path.join(LOCAL_IN_DIR, fname)
            mc.get_object(s3_path=s3_path, local_path=local_in)

            # open raster
            with rasterio.open(local_in) as src:
                profile = src.profile
                data = src.read(1).astype(float)

                # prep output & mask arrays
                out_arr = np.zeros_like(data, dtype=float)
                mask_tot = np.zeros_like(data, dtype=bool)

                # apply every criterion for this raster
                for c in crit_list:
                    vmin = float(c["val_min"])
                    vmax = float(c["val_max"])
                    nval = float(c["new_val"])

                    m = (data >= vmin) & (data <= vmax)
                    out_arr[m] += nval
                    mask_tot |= m

                # set nodata where no rule matched
                out_arr[~mask_tot] = OUTPUT_NODATA

                # update profile (dtype + nodata + compression)
                profile.update(
                    dtype=rasterio.float32, nodata=OUTPUT_NODATA
                )

            # write classified raster locally
            base, ext = os.path.splitext(fname)
            class_name = f"{base}_classificato_test{ext}"
            local_out = os.path.join(LOCAL_OUT_DIR, class_name)

            with rasterio.open(local_out, "w", **profile) as dst:
                dst.write(out_arr.astype(np.float32), 1)

            # upload classified raster
            mc.put_object(s3_path=f"{output_folder}/{class_name}", file_path=local_out)

            # per-file metric (coverage)
            metrics[f"{fname}_coverage"] = round(mask_tot.sum() / data.size * 100, 2)

            # update combo
            if combo_array is None:
                combo_array = np.where(out_arr == OUTPUT_NODATA, 0, out_arr)
                combo_profile = profile.copy()
            else:
                valid = out_arr != OUTPUT_NODATA
                combo_array[valid] += out_arr[valid]

        # 4. ────────── write + upload COMBO_OUT ──────────
        if combo_array is not None:
            combo_profile.update(nodata=OUTPUT_NODATA)
            combo_local = os.path.join(LOCAL_OUT_DIR, "COMBO_OUT.tif")
            with rasterio.open(combo_local, "w", **combo_profile) as dst:
                dst.write(combo_array.astype(np.float32), 1)

            mc.put_object(
                s3_path=f"{output_folder}/COMBO_OUT.tif", file_path=combo_local
            )
        else:
            print("⚠️  No raster processed – COMBO_OUT not created.")

        # 5. ────────── return tool response ──────────
        return {
            "message": "Tool Executed Successfully",
            "output": {
                "scored_files": output_folder  # root with *_classificato + COMBO_OUT
            },
            "metrics": metrics,
            "status": "success",
        }

    except Exception:
        print(traceback.format_exc())
        return {
            "message": "An error occurred during data processing.",
            "error": traceback.format_exc(),
            "status": 500,
        }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise ValueError("Please provide 2 files (input.json output.json).")
    with open(sys.argv[1]) as f_in:
        task_json = json.load(f_in)
    result = run(task_json)
    with open(sys.argv[2], "w") as f_out:
        json.dump(result, f_out, indent=4)
