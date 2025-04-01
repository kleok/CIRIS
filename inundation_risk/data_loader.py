"""
Handles loading of GeoJSONs, DEMs, and NetCDF SLR datasets.
"""
import os
import geopandas as gpd
from shapely import Polygon
import xarray as xr
import numpy as np
import zipfile
import tempfile
import rioxarray
import pandas as pd
from shapely.geometry import Point

# --- Function to extract and load CSV from a ZIP file ---
def extract_csv_from_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        csv_filename = [f for f in zip_ref.namelist() if f.endswith('.csv')][0]
        with zip_ref.open(csv_filename) as file:
            return pd.read_csv(file)

def Prepare_DEM(DEM_zip_paths, output_dir, CH_region_name):
    DEM_path = os.path.join(output_dir, '{}_DEM.tif'.format(CH_region_name))

    dem_xr_tiles = []

    for DEM_zip_path in DEM_zip_paths:
        # Open the ZIP file and locate the .tif inside the DEM folder
        with zipfile.ZipFile(DEM_zip_path, 'r') as zip_ref:
            # Find the .tif file inside the DEM folder
            tif_filename = [
                f for f in zip_ref.namelist()
                if f.endswith(".tif") and "DEM/" in f
            ][0]
            # Extract the .tif file to a temporary location
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_ref.extract(tif_filename, path=temp_dir)
                tif_path = os.path.join(temp_dir, tif_filename)
                
                # Load the raster using rioxarray
                dem = rioxarray.open_rasterio(tif_path)
                dem_xr_tiles.append(dem)

    # Merge the two tiles
    combined = xr.combine_by_coords(dem_xr_tiles, combine_attrs="override")

    # Optional: Write to new GeoTIFF
    combined.rio.to_raster(DEM_path)

    return DEM_path

def EGMS_zips_to_gdf(land_def_zip_paths, bbox, output_dir):
    # --- Load and merge CSVs ---
    dfs = [extract_csv_from_zip(zip_path) for zip_path in land_def_zip_paths]
    merged_df = pd.concat(dfs, ignore_index=True)
    # --- Convert to GeoDataFrame in EPSG:3035 ---
    geometry = [Point(xy) for xy in zip(merged_df.easting, merged_df.northing)]
    land_def_gdf = gpd.GeoDataFrame(merged_df, geometry=geometry, crs="EPSG:3035")

    # --- Reproject to EPSG:4326 ---
    land_def_gdf = land_def_gdf.to_crs(epsg=4326)

    # --- Crop using bounding box ---
    land_def_gdf = land_def_gdf[
        (land_def_gdf.geometry.y >= bbox['lat_min']) & (land_def_gdf.geometry.y <= bbox['lat_max']) &
        (land_def_gdf.geometry.x >= bbox['lon_min']) & (land_def_gdf.geometry.x <= bbox['lon_max'])
    ]
    # --- Data transformation ---
    # Rename columns
    land_def_gdf = land_def_gdf.rename(columns={'height': 'Elevation', 'mean_velocity': 'Velocity'})

    # Extract Longitude and Latitude from geometry
    land_def_gdf['Longitude'] = land_def_gdf.geometry.x
    land_def_gdf['Latitude'] = land_def_gdf.geometry.y

    # Drop unwanted columns
    columns_to_drop = [
        'pid', 'easting', 'northing', 'height', 'rmse', 'mean_velocity',
        'mean_velocity_std', 'acceleration', 'acceleration_std',
        'seasonality', 'seasonality_std'
    ]
    land_def_gdf = land_def_gdf.drop(columns=columns_to_drop, errors='ignore')

    # Add empty columns
    land_def_gdf['Incidence Angle'] = None
    land_def_gdf['Temporal Coherence'] = None

    # Reorder columns
    date_columns = [col for col in land_def_gdf.columns if col.isdigit()]
    new_column_order = [
        'Longitude', 'Latitude', 'Elevation', 'Velocity',
        'Incidence Angle', 'Temporal Coherence'
    ] + date_columns
    land_def_gdf = land_def_gdf[new_column_order]

    # Reconstruct GeoDataFrame with updated geometry
    land_def_gdf = gpd.GeoDataFrame(
        land_def_gdf,
        geometry=gpd.points_from_xy(land_def_gdf.Longitude, land_def_gdf.Latitude),
        crs="EPSG:4326"
    )

    land_def_gdf_path = os.path.join(output_dir,"land_def.geojson")
    # --- Optional: Save to file ---
    land_def_gdf.to_file(os.path.join(output_dir,"land_def.geojson"), driver="GeoJSON")

    print("Processing complete. GeoDataFrame ready.")
    return land_def_gdf_path


def load_land_definition(path):
    """Load land deformation vector file and calculate bounding box as GeoDataFrame."""
    gdf = gpd.read_file(path)
    lon_min, lat_min, lon_max, lat_max = gdf.total_bounds
    bbox = Polygon([
        (lon_min, lat_min), (lon_min, lat_max),
        (lon_max, lat_max), (lon_max, lat_min),
        (lon_min, lat_min)
    ])
    return gdf, gpd.GeoDataFrame({'geometry': [bbox]}, crs='EPSG:4326')

def get_slr_value(slr_path, point):
    """Extract 10-year sea level rise trend from NetCDF at given point."""
    slr_ds = xr.open_dataset(slr_path)
    slr_point = slr_ds.sel(latitude=point.y, longitude=point.x, method='nearest')
    slr_value = slr_point.trend_GIA_TPA_corrected.values * 10 / 1000  # mm/yr to m/10yrs
    if np.isnan(slr_value):
        buffer = 0.4
        slr_value = slr_ds.sel(latitude=slice(point.y-buffer,point.y+buffer), longitude=slice(point.x-buffer,point.x+buffer)).trend_GIA_TPA_corrected.mean().values * 10 / 1000  # mm/yr to m/10yrs
    return slr_value
