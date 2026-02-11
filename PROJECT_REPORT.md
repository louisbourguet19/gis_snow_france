# Project Submission - Alpine Snow Cover Analysis

**Course:** Geospatial Databases  
**Institution:** FER  
**Team Members:** Louis Bourguet, Francois Proust  
**Submission Date:** February 2026

---

## What We Built

We created a complete geospatial analysis system to study how climate change affects snow cover in the French Alps. The project uses satellite data, PostGIS database, and QGIS visualization tools.

## Main Components

### 1. Data Pipeline (ETL)

- **Acquisition:** Downloads satellite imagery from Copernicus (European Space Agency)
- **Processing:** Calculates snow coverage statistics for 10 Alpine massifs
- **Storage:** Loads data into PostGIS for spatial queries

### 2. Database

- PostGIS database running in Docker
- Schema designed for temporal geospatial data
- Optimized indexes for spatial and temporal queries

### 3. Visualization

- QGIS maps showing snow coverage by massif
- Temporal comparison (2005 vs 2025)
- Color-coded by snow percentage

## Key Findings

Our analysis revealed dramatic snow loss across all Alpine massifs:

- **Average decline:** 45% over 20 years (2005-2025)
- **Most affected:** Mercantour (-42%), Queyras (-35%)
- **Least affected:** Aravis (-19%), but still significant

## Technologies

- **Backend:** Python 3.9 (GeoPandas, Rasterio, Rasterstats)
- **Database:** PostgreSQL 16 + PostGIS 3.4
- **Infrastructure:** Docker
- **Visualization:** QGIS 3.x
- **Data Source:** Copernicus HRSI FSC products

## Challenges We Faced

1. **Copernicus API complexity** - Had to read extensive documentation to understand STAC API
2. **Coordinate systems** - Managing different projections (WGS84 vs raster CRS)
3. **Large raster files** - Memory management for processing
4. **Docker networking** - Connecting Python scripts to PostGIS container

## What We Learned

- Real-world experience with geospatial databases
- ETL pipeline design and implementation  
- Working with satellite imagery and STAC catalogs
- PostGIS spatial operations and indexing
- QGIS advanced visualization techniques

## How to Run

See README.md for detailed installation and usage instructions.

Quick start:
```bash
./setup.sh
python scripts/etl_pipeline.py
```

Then visualize in QGIS (connection details in README).

## Future Work

If we continued this project, we would:
- Add more temporal data (monthly instead of yearly)
- Include elevation analysis (snow line migration)
- Build a web dashboard with Leaflet or Mapbox
- Add statistical significance tests

## References

- Copernicus HRSI Documentation
- PostGIS Tutorial (official docs)
- QGIS Training Manual
- Python Geospatial Libraries docs

---

**Note:** All code written by our team. Data from Copernicus (public, free for education).
