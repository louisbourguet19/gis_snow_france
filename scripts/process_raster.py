"""
Raster Processing Module
Processes downloaded HRSI FSC (Fractional Snow Cover) rasters
Computes zonal statistics for each mountain massif
"""

import os
import json
from pathlib import Path
from typing import Dict, List

import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterstats import zonal_stats
import numpy as np
import pandas as pd
from shapely.geometry import mapping


class RasterProcessor:
    """Process snow cover rasters and compute statistics by massif"""
    
    def __init__(self):
        project_dir = Path(__file__).parent.parent
        self.data_dir = project_dir / "data"
        self.rasters_dir = self.data_dir / "rasters"
        self.massifs_file = self.data_dir / "massifs" / "alpine_massifs.geojson"
        self.metadata_file = self.data_dir / "acquisition_metadata.json"
        self.output_file = self.data_dir / "processed_stats.geojson"
        
    def load_massifs(self) -> gpd.GeoDataFrame:
        """Load mountain massifs geometries"""
        
        if not self.massifs_file.exists():
            raise FileNotFoundError(
                f"Massifs file not found: {self.massifs_file}\n"
                "Please ensure alpine_massifs.geojson is present in data/massifs/"
            )
        
        print(f"Loading massifs from: {self.massifs_file}")
        massifs_gdf = gpd.read_file(self.massifs_file)
        
        # Ensure CRS is WGS84 (EPSG:4326)
        if massifs_gdf.crs is None:
            massifs_gdf.set_crs("EPSG:4326", inplace=True)
        elif massifs_gdf.crs.to_epsg() != 4326:
            massifs_gdf = massifs_gdf.to_crs("EPSG:4326")
        
        print(f"   Loaded {len(massifs_gdf)} massifs")
        
        return massifs_gdf
    
    def get_raster_files(self) -> List[Dict]:
        """Get list of downloaded raster files from metadata"""
        
        if not self.metadata_file.exists():
            raise FileNotFoundError(
                f"Metadata file not found: {self.metadata_file}\n"
                "Please run acquire_data.py first"
            )
        
        with open(self.metadata_file, "r") as f:
            metadata = json.load(f)
        
        return metadata.get("downloaded_files", [])
    
    def calculate_zonal_stats(
        self, 
        raster_path: str, 
        massifs_gdf: gpd.GeoDataFrame
    ) -> gpd.GeoDataFrame:
        """
        Calculate zonal statistics for each massif
        
        Args:
            raster_path: Path to FSC raster file
            massifs_gdf: GeoDataFrame of massifs
        
        Returns:
            GeoDataFrame with statistics added
        """
        
        print(f"\n   Processing: {Path(raster_path).name}")
        
        try:
            with rasterio.open(raster_path) as src:
                # Get raster metadata
                raster_crs = src.crs
                raster_transform = src.transform
                raster_resolution = src.res[0]  # Assuming square pixels
                
                # Reproject massifs if needed
                massifs_proj = massifs_gdf.copy()
                if massifs_proj.crs != raster_crs:
                    massifs_proj = massifs_proj.to_crs(raster_crs)
                
                # Calculate zonal statistics
                # FSC values are typically 0-100 (percentage)
                stats = zonal_stats(
                    massifs_proj.geometry,
                    raster_path,
                    stats=['mean', 'sum', 'count'],
                    nodata=255,  # Common nodata value for HRSI products
                    all_touched=True
                )
                
                # Add statistics to GeoDataFrame
                stats_df = pd.DataFrame(stats)
                
                # Calculate snow-covered area
                # Area = count of snow pixels × resolution²
                # Convert to km²
                stats_df['snow_area_km2'] = (
                    stats_df['sum'] / 100.0 *  # Convert percentage to fraction
                    stats_df['count'] *  # Number of pixels
                    (raster_resolution ** 2) /  # Pixel area in m²
                    1_000_000  # Convert m² to km²
                )
                
                # Rename columns
                stats_df['snow_percent'] = stats_df['mean']
                
                # Combine with original GeoDataFrame
                result_gdf = massifs_gdf.copy()
                result_gdf['snow_percent'] = stats_df['snow_percent']
                result_gdf['snow_area_km2'] = stats_df['snow_area_km2']
                
                # Handle NaN values (massifs outside raster extent)
                result_gdf['snow_percent'].fillna(0.0, inplace=True)
                result_gdf['snow_area_km2'].fillna(0.0, inplace=True)
                
                print(f"      Computed stats for {len(result_gdf)} massifs")
                print(f"      - Resolution: {raster_resolution:.2f}m")
                print(f"      - Mean snow %: {result_gdf['snow_percent'].mean():.1f}%")
                
                return result_gdf
                
        except Exception as e:
            print(f"      Error processing {raster_path}: {e}")
            return None
    
    def process_all_rasters(self) -> gpd.GeoDataFrame:
        """
        Process all downloaded rasters
        
        Returns:
            Combined GeoDataFrame with all observations
        """
        
        print(f"\n{'='*60}")
        print("Starting Raster Processing")
        print(f"{'='*60}\n")
        
        # Load massifs
        massifs_gdf = self.load_massifs()
        
        # Get raster files
        raster_files = self.get_raster_files()
        
        if not raster_files:
            raise ValueError("No raster files found in metadata")
        
        print(f"\nProcessing {len(raster_files)} raster files...\n")
        
        # Process each raster
        all_results = []
        
        for raster_info in raster_files:
            raster_path = raster_info['file_path']
            observation_date = raster_info['datetime']
            
            # Extract date
            if isinstance(observation_date, str):
                obs_date = pd.to_datetime(observation_date).date()
            else:
                obs_date = observation_date
            
            # Calculate stats
            result_gdf = self.calculate_zonal_stats(raster_path, massifs_gdf)
            
            if result_gdf is not None:
                # Add observation date
                result_gdf['date_obs'] = obs_date
                result_gdf['item_id'] = raster_info['item_id']
                
                all_results.append(result_gdf)
        
        # Combine all results
        if not all_results:
            raise ValueError("No results to combine")
        
        combined_gdf = pd.concat(all_results, ignore_index=True)
        
        # Clean up columns
        # Keep only necessary columns
        keep_cols = ['massif_name', 'date_obs', 'snow_percent', 'snow_area_km2', 'geometry']
        
        # Check which columns exist
        available_cols = [col for col in keep_cols if col in combined_gdf.columns]
        
        # If massif_name doesn't exist, try 'name'
        if 'massif_name' not in combined_gdf.columns:
            if 'name' in combined_gdf.columns:
                combined_gdf['massif_name'] = combined_gdf['name']
                available_cols.append('massif_name')
        
        combined_gdf = combined_gdf[available_cols]
        
        # Convert date to string for GeoJSON compatibility
        if 'date_obs' in combined_gdf.columns:
            combined_gdf['date_obs'] = combined_gdf['date_obs'].astype(str)
        
        # Save to file
        combined_gdf.to_file(self.output_file, driver='GeoJSON')
        
        print(f"\n{'='*60}")
        print("Processing complete!")
        print(f"  Total observations: {len(combined_gdf)}")
        print(f"  Unique massifs: {combined_gdf['massif_name'].nunique()}")
        print(f"  Date range: {combined_gdf['date_obs'].min()} to {combined_gdf['date_obs'].max()}")
        print(f"  Output saved to: {self.output_file}")
        print(f"{'='*60}\n")
        
        return combined_gdf


def main():
    """Main entry point"""
    
    processor = RasterProcessor()
    results = processor.process_all_rasters()
    
    return results


if __name__ == "__main__":
    main()
