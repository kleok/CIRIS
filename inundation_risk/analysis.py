"""
Performs final analysis to compute inundation risk percentage.
"""

from datetime import datetime, timedelta
import numpy as np
import xarray as xr
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
import pandas as pd
import numpy as np
import geopandas as gpd


def calc_velocities(gdf, apply_ITRF2014=False):
    # Assume gdf is your GeoDataFrame and date_columns are identified
    date_columns = [col for col in gdf.columns if col.isdigit() and len(col) == 8]
    X = pd.to_datetime(date_columns, format="%Y%m%d")
    X_days = (X - X.min()).days.values.reshape(-1, 1)
    X_flat = X_days.flatten()

    # Initialize list to store corrected velocities
    velocities = []

    for _, row in gdf.iterrows():
        y = row[date_columns].values.astype(float)

        # Fit 2nd order polynomial regression
        poly_model = make_pipeline(PolynomialFeatures(2), LinearRegression()).fit(X_days, y)

        # Estimate slope (velocity) by taking derivative at midpoint
        mid_day = np.mean(X_flat)
        a = poly_model.named_steps['linearregression'].coef_[2]
        b = poly_model.named_steps['linearregression'].coef_[1]
        slope = 2 * a * mid_day + b

        # Convert slope (mm/day) to mm/year
        velocity_mm_per_year = slope * 365.25

        if apply_ITRF2014: # check 10.1109/IGARSS53475.2024.10640435
            # Apply correction based on latitude
            latitude = row["Latitude"]
            correction = -2e-4 * latitude + 0.04 * latitude - 0.87
            velocity_mm_per_year = velocity_mm_per_year + correction

        velocities.append(velocity_mm_per_year)

    # Add new column to GeoDataFrame
    gdf["Velocity (mm/year)"] = velocities
    return gdf


from datetime import datetime

def project_displacement_from_reference(gdf, reference_year=2011, future_offset=10, velocity_column="Velocity (mm/year)"):
    """
    Projects ground level displacement from a reference year to (today + offset years).

    Parameters:
    - gdf: GeoDataFrame containing the velocity data
    - reference_year: Year to start the projection from (e.g., 2011)
    - future_offset: Number of years from today to project forward (e.g., 10)
    - velocity_column: Column name with velocities in mm/year

    Returns:
    - GeoDataFrame with a new column 'Projected Displacement reference_year <future_year> (mm)'
    """
    current_year = datetime.now().year
    future_year = current_year + future_offset
    total_years = future_year - reference_year

    # Calculate displacement
    displacement = gdf[velocity_column] * total_years
    gdf['Projected_Level_m_10yr'] = displacement/1000
    return gdf

def compute_rslr(land_df, slr_value):
    """Compute Relative Sea Level Rise (RSLR)."""
    land_df['rslr'] = slr_value - land_df['Projected_Level_m_10yr']
    return land_df[['rslr', 'geometry']]


def compute_inundation_risk(rslr, dem, min_valid=5, max_window=9):
    """Compute inundation risk with adaptive window-based replacement of negative values."""
    dem_data = np.squeeze(dem.band_data)
    valid = (~np.isnan(rslr)) & (~np.isnan(dem_data)) & (dem_data != 0)
    risk = rslr.where(valid) / dem_data
    risk_data = risk.data.copy()

    nrows, ncols = risk_data.shape

    # Output array
    output = risk_data.copy()

    for i in range(nrows):
        for j in range(ncols):
            val = risk_data[i, j]

            # Only process negative values
            if val < 0 and not np.isnan(val):
                found = False
                for w in range(3, max_window + 1, 2):  # Odd sizes: 3, 5, 7, ...
                    half = w // 2
                    rmin = max(i - half, 0)
                    rmax = min(i + half + 1, nrows)
                    cmin = max(j - half, 0)
                    cmax = min(j + half + 1, ncols)

                    window = risk_data[rmin:rmax, cmin:cmax]
                    positives = window[window > 0]

                    if len(positives) >= min_valid:
                        output[i, j] = positives.mean()
                        found = True
                        break  # stop growing window

                if not found:
                    output[i, j] = np.nan  # fallback if no valid region found

    # Assign modified data back
    risk.data = output
    risk = risk.clip(min=0, max=1)
    return (risk * 100).round().astype("float32")