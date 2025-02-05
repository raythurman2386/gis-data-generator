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

3. Install the package in development mode:
```bash
pip install -e .
```

## Project Structure

```
gis-data-generator/
├── src/                    # Source code
│   ├── config/            # Configuration files
│   │   └── logging_config.py
│   ├── data/              # Data storage
│   │   ├── cache/        # Cached data
│   │   ├── plots/        # Generated plots
│   │   ├── pois/         # Points of Interest data
│   │   ├── polygons/     # Polygon data
│   │   ├── routes/       # Route data
│   │   └── street_network/ # Street network data
│   ├── tools/             # Core functionality
│   │   ├── generator.py   # Main data generator
│   │   └── batch_generator.py # Batch processing
│   ├── utils/             # Utility functions
│   │   ├── logger.py     # Logging setup
│   │   └── utils.py      # Common utilities
│   └── main.py           # CLI entry point
├── logs/                  # Log files
├── setup.py              # Package setup
└── requirements.txt      # Dependencies
```

## Usage

The GIS Data Generator can be used either as a CLI tool or as a Python package.

### CLI Usage

After installation, you can use the tool in two ways:

1. Using the installed command:
```bash
gis-generator generate --region oklahoma_city
gis-generator batch --batch-size 20 --wait-minutes 30 --data-types pois --data-types routes
```

2. Using Python directly:
```bash
python src/main.py generate --region oklahoma_city
python src/main.py batch --batch-size 20 --wait-minutes 30 --data-types pois --data-types routes
```

Available commands:

1. `generate`: Generate data for a single region
   - Options:
     - `--region`: Region to generate data for (default: oklahoma_city)

2. `batch`: Run batch processing for multiple regions
   - Options:
     - `--batch-size`: Number of regions to process in each batch (default: 20)
     - `--wait-minutes`: Wait time between batches in minutes (default: 30)
     - `--data-types`: Types of data to generate (can be specified multiple times)
       - Available types: pois, routes, polygons

### Python Package Usage

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
