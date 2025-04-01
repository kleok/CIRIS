"""
Inverse Distance Weighted Interpolation module
"""

import numpy as np
from scipy.spatial import cKDTree
import xarray as xr

def interpolate_rslr(rslr_gdf, dem_xr, dem_bbox):
    """Interpolate RSLR values across DEM using Inverse Distance Weighting."""
    cropped_dem = dem_xr.rio.clip(dem_bbox.geometry.values, dem_bbox.crs)
    coastal_mask = np.squeeze(cropped_dem.band_data < 5)
    x_coords, y_coords = cropped_dem.x.values, cropped_dem.y.values
    xx, yy = np.meshgrid(x_coords, y_coords)
    grid_points = np.vstack((xx.ravel(), yy.ravel())).T

    known_points = np.array([rslr_gdf.geometry.x, rslr_gdf.geometry.y]).T
    values = rslr_gdf['rslr'].values

    tree = cKDTree(known_points)
    distances, indices = tree.query(grid_points, k=8)
    weights = 1 / (distances + 1e-8)
    weights /= weights.sum(axis=1, keepdims=True)
    interpolated = np.sum(values[indices] * weights, axis=1)
    interpolated_raster = interpolated.reshape(xx.shape)

    rslr_raster = xr.DataArray(
        interpolated_raster,
        dims=["y", "x"],
        coords={"x": x_coords, "y": y_coords},
        name="rslr"
    )
    return rslr_raster.where(coastal_mask)