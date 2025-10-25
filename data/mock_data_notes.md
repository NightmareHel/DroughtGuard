# Mock Data Notes

## Data Structure

### features.csv
Contains regional features for prediction:
- `region`: Region name
- `ndvi_anomaly`: Normalized Difference Vegetation Index anomaly
- `rainfall_anomaly`: Rainfall anomaly (percentage)
- `food_price_inflation`: Food price inflation rate

### kenya_regions.geojson
GeoJSON file containing Kenya administrative boundaries for map visualization.

## Data Generation
Mock data was generated for demonstration purposes. In production, replace with:
- Real NDVI data from Google Earth Engine
- Rainfall data from meteorological services
- Food price data from market monitoring systems
