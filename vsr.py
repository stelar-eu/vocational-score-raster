import rasterio
import numpy as np
import pandas as pd
import os

# CONFIGURATION
csv_path = r"C:\Users\s.parisi\OneDrive - diagramgroup.it\STELAR\zonazione\criteri.csv"  # CRITERIA CSV FILE
input_dir = r"C:\Users\s.parisi\OneDrive - diagramgroup.it\STELAR\zonazione\input"  # INPUT RASTER PATH
output_dir = r"C:\Users\s.parisi\OneDrive - diagramgroup.it\STELAR\zonazione\output"  # OUTPUT RASTER PATH
output_nodata = -9999  # NODATA VALUE

############################################################

# Read CSV
# The CSV must have at least the columns: filename, val_min, val_max, new_val
criteri = pd.read_csv(csv_path)

# Create output folder if it doesn't exist
os.makedirs(output_dir, exist_ok=True)
2
# To accumulate the sum of all outputs
combo_array = None
combo_profilo = None

# List of classified raster files
output_raster_files = []

# Iterate over each group of criteria grouped by filename
for filename, group in criteri.groupby("filename"):
    input_raster_path = os.path.join(input_dir, filename)
    if not os.path.isfile(input_raster_path):
        print(f"File not found: {filename}, skipping.")
        continue

    # Prepare output path
    name, ext = os.path.splitext(filename)
    output_raster_path = os.path.join(output_dir, f"{name}_classificato{ext}")

    # Open the input raster
    with rasterio.open(input_raster_path) as src:
        profilo = src.profile
        dati = src.read(1).astype(float)
        # Set new dtype and nodata
        profilo.update(dtype=rasterio.float32, nodata=output_nodata)
        # Output array and validity mask
        output = np.zeros_like(dati, dtype=float)
        maschera_tot = np.zeros_like(dati, dtype=bool)

    # Apply each criterion in the group
    for _, row in group.iterrows():
        val_min = row["val_min"]
        val_max = row["val_max"]
        new_val = row["new_val"]
        # build the mask and add new_val
        mask = (dati >= val_min) & (dati <= val_max)
        output[mask] += new_val
        maschera_tot |= mask

    # Pixels not assigned become nodata
    output[~maschera_tot] = output_nodata

    # Write the classified raster
    with rasterio.open(output_raster_path, "w", **profilo) as dst:
        dst.write(output.astype(np.float32), 1)

    print(f"Created: {output_raster_path}")
    output_raster_files.append(output_raster_path)

    # Update COMBO_OUT
    if combo_array is None:
        # start from scratch: replace nodata with 0 to sum
        combo_array = np.where(output == output_nodata, 0, output)
        combo_profilo = profilo.copy()
    else:
        valid = output != output_nodata
        combo_array[valid] += output[valid]

# Save final COMBO_OUT
if combo_array is not None:
    combo_out_path = os.path.join(output_dir, "COMBO_OUT.tif")
    # optional NaN sanitization
    combo_array[np.isnan(combo_array)] = 0
    combo_profilo.update(nodata=output_nodata)
    with rasterio.open(combo_out_path, "w", **combo_profilo) as dst:
        dst.write(combo_array.astype(np.float32), 1)
    print(f"\n✅ COMBO_OUT created: {combo_out_path}")
else:
    print("⚠️ NO RASTER ELABORATED. COMBO_OUT NOT CREATED.")
