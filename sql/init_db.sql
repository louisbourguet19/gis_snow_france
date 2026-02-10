-- ========================================
-- Snow Analysis Database Initialization
-- ========================================

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create main snow analysis table
CREATE TABLE IF NOT EXISTS snow_analysis (
    id SERIAL PRIMARY KEY,
    massif_name VARCHAR(100) NOT NULL,
    date_obs DATE NOT NULL,
    snow_percent FLOAT CHECK (snow_percent >= 0 AND snow_percent <= 100),
    snow_area_km2 FLOAT CHECK (snow_area_km2 >= 0),
    geometry GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(massif_name, date_obs)
);

-- Create spatial index on geometry column
CREATE INDEX IF NOT EXISTS sidx_snow_geom 
ON snow_analysis USING GIST (geometry);

-- Create index on massif name and observation date
CREATE INDEX IF NOT EXISTS idx_massif_date 
ON snow_analysis (massif_name, date_obs);

-- Create index on observation date for temporal queries
CREATE INDEX IF NOT EXISTS idx_date 
ON snow_analysis (date_obs);

-- Create index on massif name for filtering
CREATE INDEX IF NOT EXISTS idx_massif_name 
ON snow_analysis (massif_name);

-- Add comment to table
COMMENT ON TABLE snow_analysis IS 'Snow coverage analysis for French Alpine massifs based on HRSI FSC satellite products';

COMMENT ON COLUMN snow_analysis.massif_name IS 'Name of the mountain massif';
COMMENT ON COLUMN snow_analysis.date_obs IS 'Date of satellite observation';
COMMENT ON COLUMN snow_analysis.snow_percent IS 'Average snow coverage percentage (0-100)';
COMMENT ON COLUMN snow_analysis.snow_area_km2 IS 'Total snow-covered area in square kilometers';
COMMENT ON COLUMN snow_analysis.geometry IS 'Massif boundary (MultiPolygon in WGS84)';

-- Create view for latest observations by massif
CREATE OR REPLACE VIEW latest_snow_coverage AS
SELECT DISTINCT ON (massif_name)
    massif_name,
    date_obs,
    snow_percent,
    snow_area_km2,
    geometry
FROM snow_analysis
ORDER BY massif_name, date_obs DESC;

COMMENT ON VIEW latest_snow_coverage IS 'Latest snow coverage observation for each massif';

-- Display initialization status
DO $$
BEGIN
    RAISE NOTICE '✓ Snow analysis database initialized successfully';
    RAISE NOTICE '  - Table: snow_analysis';
    RAISE NOTICE '  - Spatial index: sidx_snow_geom';
    RAISE NOTICE '  - Temporal indexes: idx_date, idx_massif_date';
    RAISE NOTICE '  - View: latest_snow_coverage';
END $$;
