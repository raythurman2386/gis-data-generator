import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.tools.hydrologic_analysis import download_dem_for_aoi, FILE_CONFIG


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Path:
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@patch("src.tools.hydrologic_analysis.s3dep.get_dem")
def test_download_dem_single_file(mock_get_dem: MagicMock, temp_project_dir: Path):
    """Test DEM download when a single file is returned."""
    mock_dem_file = temp_project_dir / "input_dem" / "dem_tile_1.tif"
    mock_dem_file.parent.mkdir(parents=True, exist_ok=True)
    mock_dem_file.touch()
    mock_get_dem.return_value = [mock_dem_file]

    bbox = (-90.0, 30.0, -89.0, 31.0)
    dem_path = download_dem_for_aoi(bbox, temp_project_dir / FILE_CONFIG["input_dem_dir"])

    assert dem_path == str(mock_dem_file)
    mock_get_dem.assert_called_once_with(bbox, temp_project_dir / FILE_CONFIG["input_dem_dir"], res=10)


@patch("src.tools.hydrologic_analysis.rasterio")
@patch("src.tools.hydrologic_analysis.s3dep.get_dem")
def test_download_dem_multiple_files_merge(mock_get_dem: MagicMock, mock_rasterio: MagicMock, temp_project_dir: Path):
    """Test DEM download and merge when multiple files are returned."""
    input_dem_dir = temp_project_dir / FILE_CONFIG["input_dem_dir"]
    input_dem_dir.mkdir(parents=True, exist_ok=True)

    mock_dem_file1 = input_dem_dir / "dem_tile_1.tif"
    mock_dem_file2 = input_dem_dir / "dem_tile_2.tif"
    mock_dem_file1.touch()
    mock_dem_file2.touch()

    mock_get_dem.return_value = [mock_dem_file1, mock_dem_file2]

    mock_src1 = MagicMock()
    mock_src1.meta = {
        "driver": "GTiff",
        "dtype": "float32",
        "nodata": -9999.0,
        "width": 10,
        "height": 10,
        "count": 1,
        "crs": "EPSG:4326",
        "transform": "some_transform",
    }
    mock_src2 = MagicMock()
    mock_src2.meta = mock_src1.meta

    def side_effect_open(path, mode="r", **kwargs):
        if str(path) == str(mock_dem_file1) and mode == "r":
            return mock_src1
        elif str(path) == str(mock_dem_file2) and mode == "r":
            return mock_src2
        elif str(path) == str(input_dem_dir / FILE_CONFIG["merged_dem"]) and mode == "w":
            mock_write_dst = MagicMock()
            mock_dest = MagicMock()
            mock_write_dst.__enter__.return_value = mock_dest
            mock_write_dst.__exit__.return_value = None
            return mock_write_dst
        # Fallback for any other unmocked open calls, or if mode doesn't match
        raise FileNotFoundError(f"Unexpected file open: {path} with mode {mode} and kwargs {kwargs}")

    mock_rasterio.open.side_effect = side_effect_open
    mock_rasterio.merge.merge.return_value = (MagicMock(), MagicMock())  # mosaic, out_trans

    bbox = (-90.0, 30.0, -89.0, 31.0)
    dem_path = download_dem_for_aoi(bbox, input_dem_dir)

    expected_merged_path = input_dem_dir / FILE_CONFIG["merged_dem"]
    assert dem_path == str(expected_merged_path)
    mock_get_dem.assert_called_once_with(bbox, input_dem_dir, res=10)
    mock_rasterio.merge.merge.assert_called_once()
    found_write_call = False
    for call_args in mock_rasterio.open.call_args_list:
        args, kwargs = call_args
        if args[0] == str(expected_merged_path) and args[1] == "w":
            if kwargs.get("driver") == "GTiff":  # Ensure other critical parts of meta if necessary
                found_write_call = True
                break
    assert found_write_call, f"Expected rasterio.open to be called to write {expected_merged_path}"


@patch("src.tools.hydrologic_analysis.s3dep.get_dem")
def test_download_dem_no_files_found(mock_get_dem: MagicMock, temp_project_dir: Path):
    """Test DEM download when no files are returned by s3dep.get_dem."""
    mock_get_dem.return_value = []  # Simulate no files downloaded

    bbox = (-90.0, 30.0, -89.0, 31.0)
    input_dem_dir = temp_project_dir / FILE_CONFIG["input_dem_dir"]
    dem_path = download_dem_for_aoi(bbox, input_dem_dir)

    assert dem_path is None
    mock_get_dem.assert_called_once_with(bbox, input_dem_dir, res=10)


@patch("src.tools.hydrologic_analysis.s3dep.get_dem")
def test_download_dem_s3dep_exception(mock_get_dem: MagicMock, temp_project_dir: Path):
    """Test DEM download when s3dep.get_dem raises an exception."""
    mock_get_dem.side_effect = Exception("Network error")

    bbox = (-90.0, 30.0, -89.0, 31.0)
    input_dem_dir = temp_project_dir / FILE_CONFIG["input_dem_dir"]
    dem_path = download_dem_for_aoi(bbox, input_dem_dir)

    assert dem_path is None
    mock_get_dem.assert_called_once_with(bbox, input_dem_dir, res=10)
