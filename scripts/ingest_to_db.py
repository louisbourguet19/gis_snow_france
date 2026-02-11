"""
Database Ingestion Module
Loads processed snow statistics into PostGIS database
"""

import os
from pathlib import Path
from typing import Optional

import geopandas as gpd
import psycopg2
from psycopg2 import sql as psycopg_sql
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class DatabaseIngestor:
    """Handles data ingestion into PostGIS"""
    
    def __init__(self):
        # Database connection parameters
        self.db_host = os.getenv("POSTGRES_HOST", "localhost")
        self.db_port = os.getenv("POSTGRES_PORT", "5432")
        self.db_name = os.getenv("POSTGRES_DB", "snowdb")
        self.db_user = os.getenv("POSTGRES_USER", "postgres")
        self.db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
        
        # Data file (local path)
        project_dir = Path(__file__).parent.parent
        self.data_file = project_dir / "data" / "processed_stats.geojson"
        
        # SQLAlchemy connection string
        self.connection_string = (
            f"postgresql://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    def test_connection(self) -> bool:
        """Test database connection"""
        
        print("Testing database connection...")
        
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT PostGIS_Version();")
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"   Connected to PostGIS")
            print(f"   Version: {version}")
            
            return True
            
        except Exception as e:
            print(f"   Connection failed: {e}")
            return False
    
    def load_processed_data(self) -> Optional[gpd.GeoDataFrame]:
        """Load processed statistics from file"""
        
        if not self.data_file.exists():
            raise FileNotFoundError(
                f"Processed data file not found: {self.data_file}\n"
                "Please run process_raster.py first"
            )
        
        print(f"\nLoading processed data from: {self.data_file}")
        
        gdf = gpd.read_file(self.data_file)
        
        print(f"   Loaded {len(gdf)} observations")
        print(f"   Columns: {list(gdf.columns)}")
        
        return gdf
    
    def ingest_data(self, gdf: gpd.GeoDataFrame, if_exists: str = 'replace') -> None:
        """
        Ingest data into PostGIS
        
        Args:
            gdf: GeoDataFrame to ingest
            if_exists: How to handle existing table ('replace', 'append', 'fail')
        """
        
        print(f"\n{'='*60}")
        print("Starting Database Ingestion")
        print(f"{'='*60}\n")
        
        # Ensure CRS is set
        if gdf.crs is None:
            gdf.set_crs("EPSG:4326", inplace=True)
        
        # Convert date_obs to proper datetime if it's not already
        if 'date_obs' in gdf.columns:
            gdf['date_obs'] = gpd.pd.to_datetime(gdf['date_obs'])
        
        # Create SQLAlchemy engine
        engine = create_engine(self.connection_string)
        
        # Ingest to PostGIS
        table_name = "snow_analysis"
        
        print(f"Ingesting to table: {table_name}")
        print(f"   Mode: {if_exists}")
        
        try:
            gdf.to_postgis(
                name=table_name,
                con=engine,
                if_exists=if_exists,
                index=False,
                dtype={'geometry': 'Geometry'}
            )
            
            print(f"   Ingested {len(gdf)} rows")
            
            # Get table statistics
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                total_rows = result.fetchone()[0]
                
                result = conn.execute(text(
                    f"SELECT COUNT(DISTINCT massif_name) FROM {table_name}"
                ))
                unique_massifs = result.fetchone()[0]
                
                result = conn.execute(text(
                    f"SELECT MIN(date_obs), MAX(date_obs) FROM {table_name}"
                ))
                date_range = result.fetchone()
            
            print(f"\nDatabase Statistics:")
            print(f"   Total rows: {total_rows}")
            print(f"   Unique massifs: {unique_massifs}")
            print(f"   Date range: {date_range[0]} to {date_range[1]}")
            
        except Exception as e:
            print(f"   Ingestion failed: {e}")
            raise
        
        finally:
            engine.dispose()
        
        print(f"\n{'='*60}")
        print("Ingestion complete!")
        print(f"{'='*60}\n")
    
    def create_indexes(self) -> None:
        """Create additional indexes for performance"""
        
        print("\nCreating indexes...")
        
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            
            cursor = conn.cursor()
            
            # Spatial index (if not already created)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS sidx_snow_geom 
                ON snow_analysis USING GIST (geometry)
            """)
            
            # Index on massif name and date
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_massif_date 
                ON snow_analysis (massif_name, date_obs)
            """)
            
            # Index on date only
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_date 
                ON snow_analysis (date_obs)
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("   Indexes created successfully")
            
        except Exception as e:
            print(f"   Index creation warning: {e}")


def main():
    """Main entry point"""
    
    ingestor = DatabaseIngestor()
    
    # Test connection
    if not ingestor.test_connection():
        raise ConnectionError("Cannot connect to database")
    
    # Load processed data
    gdf = ingestor.load_processed_data()
    
    # Ingest data
    ingestor.ingest_data(gdf, if_exists='append')
    
    # Create indexes
    ingestor.create_indexes()
    
    print("\nDatabase ingestion complete! Ready for QGIS connection.")


if __name__ == "__main__":
    main()
