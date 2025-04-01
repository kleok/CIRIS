"""
Misc utilities
"""

import xarray as xr
import rioxarray
import os
from rasterio.transform import from_origin
import rasterio
from rasterio.enums import ColorInterp
from rasterio.io import MemoryFile
import numpy as np
import os

def build_transform(x_coords, y_coords):
    return from_origin(
        x_coords[0],
        y_coords[0],
        abs(x_coords[1] - x_coords[0]),
        abs(y_coords[1] - y_coords[0])
    )

def save_colormapped_tif(array, transform, crs, output_path, nodata_value=255):
    """
    Save a single-band array as a GeoTIFF with an embedded color table.

    Parameters:
        array (2D np.ndarray): The data (e.g., 0–100 values)
        transform (Affine): GeoTransform
        crs (str or CRS): Coordinate system (e.g., 'EPSG:4326')
        output_path (str): Output TIFF path
    """
    # Convert to uint8 if not already
    array = np.clip(np.round(array), 0, 100)
    array = np.where(np.isnan(array), nodata_value, array)
    data = array.astype("uint8")

    # Build a color map (0–100)
    colormap = {
        0: (255, 255, 255),      # white
        25: (255, 255, 0),       # yellow
        50: (255, 165, 0),       # orange
        75: (255, 0, 0),         # red
        100: (128, 0, 0),        # dark red
    }

    # Interpolate missing values
    for i in range(101):
        if i not in colormap:
            # Linear interpolate between nearest keys
            lower = max(k for k in colormap if k <= i)
            upper = min(k for k in colormap if k >= i)
            if lower == upper:
                colormap[i] = colormap[lower]
            else:
                f = (i - lower) / (upper - lower)
                colormap[i] = tuple(int(colormap[lower][j] * (1 - f) + colormap[upper][j] * f) for j in range(3))

    # Write to TIFF with colormap
    with rasterio.open(
        output_path, 'w',
        driver='GTiff',
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype='uint8',
        crs=crs,
        transform=transform,
        nodata=nodata_value
    ) as dst:
        dst.write(data, 1)
        dst.write_colormap(1, colormap)
        dst.set_band_description(1, "Inundation Risk")
        dst.colorinterp = [ColorInterp.palette]

    print(f"✅ Color-mapped GeoTIFF saved to: {output_path}")