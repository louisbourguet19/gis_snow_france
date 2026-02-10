"""
Data Acquisition Module
Connects to Copernicus Data Space Ecosystem (CDSE) via STAC API
Downloads HRSI FSC (High Resolution Snow & Ice - Fractional Snow Cover) products
"""

import os
import json
from datetime import datetime
from typing import List, Dict
from pathlib import Path

from pystac_client import Client
import requests
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class CopernicusDataAcquisition:
    """Handles satellite imagery acquisition from Copernicus CDSE"""
    
    STAC_API_URL = "https://catalogue.dataspace.copernicus.eu/stac"
    COLLECTION_ID = "HRSI-SWS-FSC"  # Fractional Snow Cover collection
    
    def __init__(self):
        self.username = os.getenv("CDSE_USERNAME")
        self.password = os.getenv("CDSE_PASSWORD")
        self.aoi_bbox = self._parse_bbox(os.getenv("AOI_BBOX", "5.5,44.0,7.5,46.0"))
        self.cloud_cover_max = int(os.getenv("CLOUD_COVER_MAX", "20"))
        
        # Output directory for downloaded data (local path)
        project_dir = Path(__file__).parent.parent
        self.output_dir = project_dir / "data" / "rasters"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata cache
        self.metadata_file = project_dir / "data" / "acquisition_metadata.json"
        
    def _parse_bbox(self, bbox_str: str) -> List[float]:
        """Parse bounding box from string 'west,south,east,north'"""
        return [float(x) for x in bbox_str.split(",")]
    
    def _get_access_token(self) -> str:
        """Authenticate with CDSE and get access token"""
        auth_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        
        data = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
            "client_id": "cdse-public"
        }
        
        response = requests.post(auth_url, data=data)
        response.raise_for_status()
        
        return response.json()["access_token"]
    
    def search_products(self, date_range: str) -> List[Dict]:
        """
        Search for HRSI FSC products
        
        Args:
            date_range: Date range in format "YYYY-MM-DD/YYYY-MM-DD"
        
        Returns:
            List of STAC items matching criteria
        """
        print(f"\n🔍 Searching for products in date range: {date_range}")
        print(f"   AOI Bounding Box: {self.aoi_bbox}")
        
        # Connect to STAC catalog
        catalog = Client.open(self.STAC_API_URL)
        
        # Search for items
        search = catalog.search(
            collections=[self.COLLECTION_ID],
            bbox=self.aoi_bbox,
            datetime=date_range,
            max_items=100
        )
        
        items = list(search.items())
        
        # Filter by cloud coverage if available
        filtered_items = []
        for item in items:
            cloud_cover = item.properties.get("eo:cloud_cover", 0)
            if cloud_cover <= self.cloud_cover_max:
                filtered_items.append(item)
        
        print(f"   ✓ Found {len(items)} products, {len(filtered_items)} after cloud filter (<{self.cloud_cover_max}%)")
        
        return filtered_items
    
    def download_product(self, item) -> str:
        """
        Download FSC product (COG file)
        
        Args:
            item: STAC item
        
        Returns:
            Path to downloaded file
        """
        # Get the FSC asset (Cloud Optimized GeoTIFF)
        asset_key = "fsc"  # Fractional Snow Cover
        
        if asset_key not in item.assets:
            # Try alternative keys
            possible_keys = ["data", "visual", "thumbnail"]
            for key in possible_keys:
                if key in item.assets:
                    asset_key = key
                    break
        
        asset = item.assets.get(asset_key)
        if not asset:
            print(f"   ⚠ No suitable asset found for item {item.id}")
            return None
        
        # Download URL
        download_url = asset.href
        
        # Create filename
        item_date = item.properties.get("datetime", "unknown")
        if isinstance(item_date, str):
            item_date = datetime.fromisoformat(item_date.replace("Z", "+00:00"))
        
        filename = f"fsc_{item_date.strftime('%Y%m%d')}_{item.id[:8]}.tif"
        output_path = self.output_dir / filename
        
        # Skip if already downloaded
        if output_path.exists():
            print(f"   ⏭ Already downloaded: {filename}")
            return str(output_path)
        
        print(f"   ⬇ Downloading: {filename}")
        
        try:
            # Get access token for authenticated download
            token = self._get_access_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            # Stream download
            response = requests.get(download_url, headers=headers, stream=True)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"   ✓ Downloaded: {filename}")
            return str(output_path)
            
        except Exception as e:
            print(f"   ✗ Error downloading {filename}: {e}")
            return None
    
    def acquire_data(self, date_ranges: List[str]) -> Dict:
        """
        Main acquisition workflow
        
        Args:
            date_ranges: List of date ranges to process
        
        Returns:
            Dictionary with metadata about acquired products
        """
        metadata = {
            "acquisition_date": datetime.now().isoformat(),
            "aoi_bbox": self.aoi_bbox,
            "date_ranges": {},
            "downloaded_files": []
        }
        
        for date_range in date_ranges:
            print(f"\n{'='*60}")
            print(f"Processing date range: {date_range}")
            print(f"{'='*60}")
            
            # Search for products
            items = self.search_products(date_range)
            
            # Download products
            downloaded = []
            for item in items:
                file_path = self.download_product(item)
                if file_path:
                    downloaded.append({
                        "file_path": file_path,
                        "item_id": item.id,
                        "datetime": item.properties.get("datetime"),
                        "cloud_cover": item.properties.get("eo:cloud_cover", 0)
                    })
            
            metadata["date_ranges"][date_range] = {
                "total_found": len(items),
                "downloaded": len(downloaded)
            }
            metadata["downloaded_files"].extend(downloaded)
        
        # Save metadata
        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✓ Acquisition complete!")
        print(f"  Total files downloaded: {len(metadata['downloaded_files'])}")
        print(f"  Metadata saved to: {self.metadata_file}")
        print(f"{'='*60}\n")
        
        return metadata


def main():
    """Main entry point"""
    
    # Get date ranges from environment
    date_range_1 = os.getenv("DATE_RANGE_1", "2024-01-01/2024-01-31")
    date_range_2 = os.getenv("DATE_RANGE_2", "2025-01-01/2025-01-31")
    
    date_ranges = [date_range_1, date_range_2]
    
    # Initialize acquisition
    acquirer = CopernicusDataAcquisition()
    
    # Acquire data
    metadata = acquirer.acquire_data(date_ranges)
    
    return metadata


if __name__ == "__main__":
    main()
