"""
ETL Pipeline Orchestrator
Main script that coordinates the entire ETL workflow:
1. Data Acquisition from Copernicus
2. Raster Processing (zonal statistics)
3. Database Ingestion to PostGIS
"""

import sys
import logging
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import modules
import acquire_data
import process_raster
import ingest_to_db


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main ETL pipeline orchestration"""
    
    print("\n" + "="*60)
    print("❄️  SNOW ANALYSIS ETL PIPELINE")
    print("="*60 + "\n")
    
    try:
        # Step 1: Data Acquisition
        print("\n🚀 STEP 1/3: Data Acquisition")
        print("-" * 60)
        
        logger.info("Starting data acquisition from Copernicus...")
        metadata = acquire_data.main()
        
        if not metadata or not metadata.get('downloaded_files'):
            logger.warning("No data downloaded. Check your credentials and AOI settings.")
            return
        
        logger.info(f"✓ Acquired {len(metadata['downloaded_files'])} files")
        
        # Step 2: Raster Processing
        print("\n🚀 STEP 2/3: Raster Processing")
        print("-" * 60)
        
        logger.info("Starting raster processing...")
        results = process_raster.main()
        
        if results is None or len(results) == 0:
            logger.error("No results from raster processing")
            return
        
        logger.info(f"✓ Processed {len(results)} observations")
        
        # Step 3: Database Ingestion
        print("\n🚀 STEP 3/3: Database Ingestion")
        print("-" * 60)
        
        logger.info("Starting database ingestion...")
        ingest_to_db.main()
        
        logger.info("✓ Data ingested successfully")
        
        # Success summary
        print("\n" + "="*60)
        print("✅ ETL PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n📊 Summary:")
        print(f"   • Files processed: {len(metadata['downloaded_files'])}")
        print(f"   • Observations: {len(results)}")
        print(f"   • Unique massifs: {results['massif_name'].nunique()}")
        print(f"   • Date range: {results['date_obs'].min()} to {results['date_obs'].max()}")
        print("\n🎯 Next Steps:")
        print("   1. Open QGIS")
        print("   2. Add PostGIS connection (localhost:5432)")
        print("   3. Load 'snow_analysis' layer")
        print("   4. Visualize snow coverage by massif and date")
        print("\n" + "="*60 + "\n")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error("Make sure all required files are in place:")
        logger.error("  - data/massifs/alpine_massifs.geojson")
        logger.error("  - .env file with credentials")
        sys.exit(1)
        
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        logger.error("Check that PostGIS container is running:")
        logger.error("  docker-compose ps")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
