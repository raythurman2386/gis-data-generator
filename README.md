# GIS Data Generator

A sophisticated Python tool for generating, analyzing, and visualizing geospatial data across major US cities.
This project demonstrates advanced usage of geospatial libraries and data processing techniques.

> Note: This project is in development and overall a collective upskilling project along with the [GIS Playground](https://github.com/raythurman/gis-playground) project.

## Features

- Generate synthetic geospatial data for various US cities
- Create and analyze street networks with centrality metrics
- Generate multiple types of geospatial data:
    - Points of Interest (POIs)
    - Street Networks
    - Routes
    - Polygons (e.g., zones, districts)
- Batch processing capabilities
- Data caching for improved performance
- Comprehensive error handling and logging
- Configurable output formats (GeoJSON, Shapefile, GeoPackage)

## Technologies Used

- Python 3.11+
- GeoPandas
- OSMnx
- NetworkX
- Matplotlib
- Shapely
- Pandas
- NumPy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/raythurman2386/gis-data-generator.git
cd gis-data-generator
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from gis_data_generator import GeospatialDataGenerator

# Generate point data
generator = GeospatialDataGenerator(
    data_type="pois",
    region="seattle",
    num_points=1000
)
generator.generate_data()
generator.plot_data()
generator.save_data(format="geojson")
```

### Batch Processing

```python
from gis_data_generator import batch_process_regions

# Configure batch processing
config = {
    "batch_size": 15,
    "wait_minutes": 15,
    "data_types": ["pois", "streets", "polygons"]
}

# Run batch processing
batch_process_regions(**config)
```

## Data Types

### Points
- Random points within city boundaries
- Configurable number of points
- Attributes include timestamps and random values

### Street Networks
- Real street network data from OpenStreetMap
- Betweenness centrality analysis
- Network statistics and visualization

### Routes
- Generated using real street networks
- Random origin-destination pairs
- Attributes include distance, duration, and vehicle type

### Polygons
- Non-overlapping zones within city boundaries
- Attributes include area, category, and population
- Configurable number and size of polygons

## Available Regions

The generator includes predefined configurations for major US cities across different regions:

- West Coast (Seattle, Portland, San Francisco, Los Angeles)
- Mountain States (Denver, Phoenix, Las Vegas, etc.)
- Midwest (Chicago, Detroit, Minneapolis, etc.)
- Northeast (New York, Boston, Philadelphia, etc.)
- South (Miami, Atlanta, Houston, etc.)
- Non-Contiguous States (Anchorage, Honolulu)

## Output Formats

- GeoJSON (.geojson)
- Shapefile (.shp)
- GeoPackage (.gpkg)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenStreetMap contributors
- OSMnx library developers
- GeoPandas community

## Future Enhancements

- Integration with [GIS Playground](https://github.com/raythurman/gis-playground)
- Integration with scikit-learn for spatial analysis
- Additional data types and attributes
- Support for international cities
- Advanced routing algorithms
- Spatial pattern analysis
- Machine learning integration for pattern generation
