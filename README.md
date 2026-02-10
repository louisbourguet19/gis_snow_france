# Alpine Snow Cover Analysis Project

**Authors:** Louis Bourguet & [Partner Name]  
**Institution:** FER  
**Course:** Geospatial Databases  
**Date:** February 2026

## Project Overview

This project analyzes snow cover evolution in the French Alpine massifs over a 20-year period (2005-2025) using satellite imagery and geospatial databases. We built a complete ETL pipeline to process raster data and store results in PostGIS for visualization in QGIS.

## Objectives

- Download and process satellite snow cover data (HRSI FSC products)
- Calculate zonal statistics for 10 major Alpine massifs
- Store temporal geospatial data in PostGIS
- Visualize climate change impact on snow coverage

## Technologies Used

- **Database:** PostGIS 16 (Docker)
- **Backend:** Python 3.9
- **Geospatial Libraries:** GeoPandas, Rasterio, Rasterstats
- **Data Source:** Copernicus Data Space Ecosystem
- **Visualization:** QGIS

## Project Structure

```
snow/
├── docker-compose.yml      # PostGIS configuration
├── .env                    # Environment variables (not in git!)
├── scripts/
│   ├── acquire_data.py     # Download satellite data from Copernicus
│   ├── process_raster.py   # Calculate snow statistics per massif
│   ├── ingest_to_db.py     # Load data into PostGIS
│   └── etl_pipeline.py     # Main ETL orchestrator
├── sql/
│   └── init_db.sql         # Database schema definition
├── data/
│   ├── massifs/            # GeoJSON geometries of massifs
│   └── rasters/            # Downloaded satellite imagery
└── venv/                   # Python virtual environment
```

## Installation

### 1. Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.8 or higher
- Copernicus account (free): https://dataspace.copernicus.eu/

### 2. Setup

```bash
# Clone the repository
git clone [your-repo]
cd snow

# Run the setup script
./setup.sh

# Or manually:
# 1. Start PostGIS
docker-compose up -d

# 2. Create Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt

# 3. Configure credentials
cp .env.example .env
# Edit .env with your Copernicus credentials
```

### 3. Database Connection

```
Host: localhost
Port: 5432
Database: snowdb
User: postgres
Password: (see .env file)
```

## Usage

### Run the ETL Pipeline

```bash
# Activate Python environment
source venv/bin/activate

# Run the complete pipeline
python scripts/etl_pipeline.py
```

The pipeline will:
1. Download HRSI FSC satellite data from Copernicus
2. Process rasters to calculate snow statistics
3. Insert results into PostGIS database

### Visualize in QGIS

1. Open QGIS
2. Add PostGIS connection (see credentials above)
3. Load the `snow_analysis` layer
4. Style by `snow_percent` field using graduated colors

## Database Schema

```sql
CREATE TABLE snow_analysis (
    id SERIAL PRIMARY KEY,
    massif_name VARCHAR(100) NOT NULL,
    date_obs DATE NOT NULL,
    snow_percent FLOAT,              -- Percentage of snow cover (0-100)
    snow_area_km2 FLOAT,             -- Snow-covered area in km²
    geometry GEOMETRY(MultiPolygon, 4326),
    UNIQUE(massif_name, date_obs)
);
```

## Results

Our analysis shows a significant decrease in snow coverage across all 10 Alpine massifs:

- **2005 average:** 63% snow coverage
- **2025 average:** 35% snow coverage
- **Overall decline:** 45% over 20 years

Most affected massifs:
- Mercantour: -42%
- Queyras: -35%
- Écrins: -33%

## Known Issues

- Copernicus API sometimes slow → retry if download fails
- Need to configure `.env` before running pipeline
- Docker must be running before starting

## Future Improvements

- Add more temporal data points (monthly instead of yearly)
- Include elevation analysis
- Automated change detection
- Web-based dashboard

## References

- Copernicus HRSI Documentation: https://land.copernicus.eu/pan-european/biophysical-parameters/high-resolution-snow-and-ice-monitoring
- PostGIS Documentation: https://postgis.net/docs/
- QGIS Tutorials: https://www.qgistutorials.com/

## License

Educational project for FER course. Data from Copernicus (EU).
# gis_snow_france
