# 🌊 Inundation Risk Tool for Coastal Heritage 🏛️

Welcome to the **Inundation Risk Tool** — a Python-based toolkit designed to analyze and visualize flood risk in coastal areas, especially those rich in **cultural heritage**. Built with robust geospatial libraries and interpolation techniques, this tool empowers researchers, planners, and policymakers to better understand potential impacts of sea level rise. 🌍🌡️

---

## 🚀 Features

- 📍 **Geospatial Data Processing** using `rasterio`, `rioxarray`, and `shapely`
- 🗺️ **Clipping and Masking** of Digital Elevation Models (DEMs)
- 🌊 **Sea Level Rise Interpolation** using Inverse Distance Weighting (IDW)
- ⚠️ **Flood Risk Analysis** with percentage-based inundation metrics
- 🧪 **Utilities & Preprocessing** tools for real-world geodata
- 🧾 **Outputs** in both GeoTIFF and NetCDF formats

---

## 🧭 Project Structure

```
inundation_risk/
├── __init__.py
├── analysis.py          # Risk analysis functions
├── data_loader.py       # Load and manage input geospatial data
├── interpolation.py     # Interpolation methods (e.g. IDW)
├── preprocessing.py     # DEM clipping and masking
├── utils.py             # Helper functions
notebooks/
└── generate_inundation_risk.ipynb  # Interactive usage notebook
requirements.txt
README.md
```

---

## 🛠️ Installation & Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/CIRIS.git
   cd inundation-risk-tool
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the notebook:
   ```bash
   jupyter notebook notebooks/generate_inundation_risk.ipynb
   ```

---

## 🧠 Requirements

The tool uses the following Python libraries:

- `numpy`, `pandas`
- `geopandas`, `shapely`
- `rasterio`, `rioxarray`, `xarray`
- `scipy`, `sklearn`
- Plus standard libraries like `os`, `datetime`, `zipfile`, `tempfile`

---

## 📸 Example Output

The tool outputs georeferenced raster layers highlighting the areas at risk of inundation under projected sea level rise scenarios.

---

## 💶 Funding

The **THETIDA** project has received funding from the **European Union's Horizon Europe** programme under grant agreement **101095253**.

🌐 Learn more at: [https://cordis.europa.eu/project/id/101095253](https://cordis.europa.eu/project/id/101095253)

---

## 📬 Contact

For questions, collaborations, or feedback, feel free to open an issue or reach out to the project maintainers.

