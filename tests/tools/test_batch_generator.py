"""Tests for the batch_generator script."""

import pytest
from unittest.mock import patch, MagicMock, call

from src.tools.batch_generator import process_region, batch_process_regions, DATA_CONFIGS
from src.tools.generator import GeospatialDataGenerator  # For _region_queries

# Define a smaller set of regions for testing batch processing
TEST_BATCH_REGIONS = {"batch_city1": {}, "batch_city2": {}, "batch_city3": {}}


@pytest.fixture
def mock_geospatial_data_generator(monkeypatch):
    """Mocks the GeospatialDataGenerator class and its methods."""
    mock_instance = MagicMock(spec=GeospatialDataGenerator)
    mock_instance.data_type = None
    mock_instance.num_points = 0
    mock_instance.generate_data = MagicMock()
    mock_instance.plot_data = MagicMock()
    mock_instance.save_data = MagicMock()

    # Mock the class constructor to return our mock_instance
    mock_class = MagicMock(return_value=mock_instance)
    monkeypatch.setattr("src.tools.batch_generator.GeospatialDataGenerator", mock_class)

    # Set _region_queries on the mock_class itself, as batch_process_regions
    # will access it via the mocked GeospatialDataGenerator in its own module scope.
    mock_class._region_queries = TEST_BATCH_REGIONS

    return mock_class, mock_instance


def test_process_region_single_data_type(mock_geospatial_data_generator):
    """Test process_region for a single data type."""
    mock_class, mock_instance = mock_geospatial_data_generator
    region_name = "batch_city1"
    data_type_to_process = "pois"

    process_region(region_name, data_types=[data_type_to_process])

    # Check GeospatialDataGenerator was instantiated for the region
    mock_class.assert_called_once_with(region=region_name)

    # Check methods were called on the instance
    assert mock_instance.data_type == data_type_to_process
    assert mock_instance.num_points == DATA_CONFIGS[data_type_to_process]["num_points"]
    mock_instance.generate_data.assert_called_once()
    mock_instance.plot_data.assert_called_once()
    mock_instance.save_data.assert_called_once_with(format=DATA_CONFIGS[data_type_to_process]["format"])


def test_process_region_multiple_data_types(mock_geospatial_data_generator):
    """Test process_region for multiple data types."""
    mock_class, mock_instance = mock_geospatial_data_generator
    region_name = "batch_city2"
    data_types_to_process = ["pois", "routes"]

    process_region(region_name, data_types=data_types_to_process)

    mock_class.assert_called_once_with(region=region_name)
    assert mock_instance.generate_data.call_count == len(data_types_to_process)
    assert mock_instance.plot_data.call_count == len(data_types_to_process)
    assert mock_instance.save_data.call_count == len(data_types_to_process)

    expected_save_calls = []
    for dt in data_types_to_process:
        expected_save_calls.append(call(format=DATA_CONFIGS[dt]["format"]))
    mock_instance.save_data.assert_has_calls(expected_save_calls, any_order=False)


def test_process_region_generator_exception(mock_geospatial_data_generator, caplog):
    """Test process_region when the generator itself raises an exception during instantiation."""
    mock_class, _ = mock_geospatial_data_generator
    mock_class.side_effect = Exception("Init failed")
    region_name = "batch_city_fail"

    process_region(region_name, data_types=["pois"])
    assert f"Error processing region {region_name}: Init failed" in caplog.text


def test_process_region_data_type_exception(mock_geospatial_data_generator, caplog):
    """Test process_region when a specific data type processing fails."""
    mock_class, mock_instance = mock_geospatial_data_generator
    mock_instance.generate_data.side_effect = [None, Exception("Generate failed"), None]  # Fails on 2nd data type
    region_name = "batch_city_partial_fail"
    data_types_to_process = ["pois", "routes", "polygons"]

    process_region(region_name, data_types=data_types_to_process)

    # Ensure it attempts all, logs error for 'routes', and continues
    assert mock_instance.generate_data.call_count == len(data_types_to_process)
    assert f"Error processing routes for {region_name}: Generate failed" in caplog.text
    # Check that save_data was called for pois and polygons but not for routes (or rather, less times)
    assert mock_instance.save_data.call_count == 2


@patch("src.tools.batch_generator.time.sleep")  # Mock time.sleep
def test_batch_process_regions_logic(mock_sleep: MagicMock, mock_geospatial_data_generator, caplog):
    """Test the batching logic of batch_process_regions."""
    mock_class, mock_instance = mock_geospatial_data_generator

    # Using TEST_BATCH_REGIONS which has 3 regions
    batch_size = 2
    wait_minutes = 1  # Small wait for testing
    data_types = ["pois"]

    batch_process_regions(batch_size=batch_size, wait_minutes=wait_minutes, data_types=data_types)

    # Expected calls to process_region (which in turn calls Generator)
    # Total regions = 3, batch_size = 2. So, 2 batches.
    # Batch 1: batch_city1, batch_city2
    # Batch 2: batch_city3
    assert mock_class.call_count == len(TEST_BATCH_REGIONS)  # Generator init per region

    # Check calls to generator methods (e.g., save_data, one per region per data_type)
    assert mock_instance.save_data.call_count == len(TEST_BATCH_REGIONS) * len(data_types)

    # Check that sleep was called once (after the first batch)
    mock_sleep.assert_called_once_with(wait_minutes * 60)

    assert f"Starting batch processing of {len(TEST_BATCH_REGIONS)} regions" in caplog.text
    assert "Starting batch 1/2" in caplog.text  # Check without leading newline
    assert "Starting batch 2/2" in caplog.text  # Check without leading newline
    assert "All regions have been processed!" in caplog.text


def test_batch_process_invalid_data_type(mock_geospatial_data_generator):
    """Test batch_process_regions with an invalid data type."""
    with pytest.raises(ValueError) as excinfo:
        batch_process_regions(data_types=["invalid_type"])
    assert "Invalid data types: {'invalid_type'}" in str(excinfo.value)


# Further tests could include:
# - Different batch sizes and total regions (e.g., total regions < batch_size)
# - No data_types specified (should use all from DATA_CONFIGS)
