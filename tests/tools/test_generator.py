"""Tests for the GeospatialDataGenerator class."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Polygon, Point
import os

from src.tools.generator import GeospatialDataGenerator

# Define a minimal region query for testing to avoid using the large default dictionary
TEST_REGION_QUERIES = {"test_city": {"city": "Soper", "state": "OK", "country": "USA"}}


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory for tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    # Create cache subdir as the code expects it
    (data_dir / "cache").mkdir()
    return data_dir


@pytest.fixture
def mock_generator_dependencies(monkeypatch, temp_data_dir):
    """Mocks dependencies for GeospatialDataGenerator."""

    # Mock os.path.dirname for the context of DATA_DIR initialization in generator.py
    # self.DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    # We want os.path.dirname(os.path.dirname(__file__)) to become temp_data_dir.parent
    # so that joining "data" results in temp_data_dir.
    original_os_path_dirname = os.path.dirname

    def new_dirname(path):
        # When __file__ (src/tools/generator.py) is passed to dirname twice
        if str(path).endswith(os.path.normpath("src/tools")):
            # This is the result of the first dirname(__file__), i.e., os.path.dirname(os.path.dirname(__file__))
            # Return temp_data_dir.parent here
            return str(temp_data_dir.parent)
        # Fallback to original for all other calls, including the first dirname(__file__)
        return original_os_path_dirname(path)

    monkeypatch.setattr("src.tools.generator.os.path.dirname", new_dirname)
    # os.path.join will then correctly form temp_data_dir path when "data" is appended.

    # Mock ox.features_from_place to return a sample GDF
    mock_poi_gdf = gpd.GeoDataFrame(
        {"name": ["Test POI 1", "Test POI 2"], "geometry": [Point(0.5, 0.5), Point(0.6, 0.6)]}, crs="EPSG:4326"
    )
    mock_ox_features = MagicMock(return_value=mock_poi_gdf)
    monkeypatch.setattr("src.tools.generator.ox.features_from_place", mock_ox_features)

    # Mock ox.geocode_to_gdf
    mock_gdf = gpd.GeoDataFrame(geometry=[Polygon([(0, 0), (1, 1), (1, 0)])], crs="EPSG:4326")
    monkeypatch.setattr("osmnx.geocode_to_gdf", MagicMock(return_value=mock_gdf))

    # Mock ox.graph_from_place
    mock_graph = MagicMock()
    monkeypatch.setattr("osmnx.graph_from_place", MagicMock(return_value=mock_graph))
    monkeypatch.setattr("osmnx.add_edge_speeds", MagicMock(return_value=mock_graph))
    monkeypatch.setattr("osmnx.add_edge_travel_times", MagicMock(return_value=mock_graph))
    monkeypatch.setattr("osmnx.io.save_graph_geopackage", MagicMock())

    # Mock ox.features_from_place for POIs, etc.
    mock_features_gdf = gpd.GeoDataFrame({"name": ["Feature1"]}, geometry=[Point(0.5, 0.5)], crs="EPSG:4326")
    monkeypatch.setattr("osmnx.features_from_place", MagicMock(return_value=mock_features_gdf))

    # Mock geopandas.to_file
    monkeypatch.setattr("geopandas.GeoDataFrame.to_file", MagicMock())

    # Mock matplotlib.pyplot
    monkeypatch.setattr("matplotlib.pyplot.show", MagicMock())
    monkeypatch.setattr("matplotlib.pyplot.savefig", MagicMock())
    monkeypatch.setattr("matplotlib.pyplot.close", MagicMock())

    # Patch the _region_queries to use our test version
    monkeypatch.setattr("src.tools.generator.GeospatialDataGenerator._region_queries", TEST_REGION_QUERIES)
    # Clear caches for clean test runs
    GeospatialDataGenerator._boundary_cache = {}
    GeospatialDataGenerator._graph_cache = {}

    return {
        "mock_gdf": mock_gdf,
        "mock_graph": mock_graph,
        "mock_features_gdf": mock_features_gdf,
        "temp_data_dir": temp_data_dir,
    }


def test_generator_init_new_region(mock_generator_dependencies):
    """Test generator initialization for a new region, expecting boundary load."""
    generator = GeospatialDataGenerator(region="test_city", data_type="points", num_points=10)
    assert generator.region == "test_city"
    assert generator.boundary is not None
    assert generator.graph is not None
    # Check if boundary was cached
    assert "test_city" in GeospatialDataGenerator._boundary_cache
    # Check if ox.geocode_to_gdf was called (indirectly via load_boundary)
    assert GeospatialDataGenerator._region_queries == TEST_REGION_QUERIES  # Ensure patch worked
    # ox.geocode_to_gdf is mocked via monkeypatch, direct assertion on it is tricky
    # Instead, we check the outcome (boundary is loaded)


def test_generator_init_cached_region(mock_generator_dependencies):
    """Test generator initialization for a cached region."""
    # First call to cache the region
    GeospatialDataGenerator(region="test_city", data_type="points", num_points=10)

    # Mock ox.geocode_to_gdf to ensure it's not called for cached data
    with patch("osmnx.geocode_to_gdf") as mock_geocode_again:
        generator_cached = GeospatialDataGenerator(region="test_city", data_type="points", num_points=10)
        assert generator_cached.region == "test_city"
        assert generator_cached.boundary is not None  # Should load from cache
        mock_geocode_again.assert_not_called()


def test_generator_load_boundary_failure_fallback(mock_generator_dependencies, monkeypatch):
    """Test fallback boundary loading when OSMnx fails."""
    monkeypatch.setattr("osmnx.geocode_to_gdf", MagicMock(side_effect=Exception("OSM Error")))
    # Also mock the second attempt in _load_boundary_gdf
    monkeypatch.setattr("osmnx.features_from_place", MagicMock(side_effect=Exception("OSM Features Error")))

    generator = GeospatialDataGenerator(region="test_city")
    assert generator.boundary is not None
    # Check if it's the fallback geometry (very basic check based on number of points in exterior)
    assert len(generator.boundary.geometry.iloc[0].exterior.coords) == 5


def test_generator_generate_data_points(mock_generator_dependencies):
    """Test the generate_data method for 'points' (POIs)."""
    generator = GeospatialDataGenerator(region="soper", data_type="pois", num_points=5)
    generator.generate_data()
    assert isinstance(generator.data, gpd.GeoDataFrame)
    assert not generator.data.empty
    assert "geometry" in generator.data.columns
    # osmnx.features_from_place is mocked via monkeypatch
