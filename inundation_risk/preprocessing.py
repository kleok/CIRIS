"""
Handles raster clipping, masking, coordinate alignment, etc.
"""

import xarray as xr
import geopandas as gpd
from shapely.geometry import box

def clip_raster_to_shoreline(raster, shoreline_path):
    """Clip raster using shoreline polygons."""
    shoreline = gpd.read_file(shoreline_path)
    if shoreline.crs != raster.rio.crs:
        shoreline = shoreline.to_crs(raster.rio.crs)

    raster_bounds = box(float(raster.x.min()), float(raster.y.min()), float(raster.x.max()), float(raster.y.max()))
    filtered_polygons = shoreline[shoreline.intersects(raster_bounds)]
    return raster.rio.clip(filtered_polygons.geometry.values, filtered_polygons.crs)