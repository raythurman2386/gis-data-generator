from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import geopandas as gpd
import networkx as nx
import numpy as np
import rasterio
import rasterio.merge
import seamless_3dep as s3dep
from pysheds.grid import Grid
from shapely.geometry import Point, shape
from src.utils.logger import setup_logger

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Centralized dictionary for file paths and names
FILE_CONFIG = {
    "logs_dir": "logs",
    "log_file": "hydrologic_analysis_os.log",
    "input_dem_dir": "input_dem",
    "merged_dem": "dem_merged.tif",
    "pysheds_outputs_dir": "pysheds_outputs",
    "flow_accumulation": "flow_accumulation.tif",
    "flow_direction": "flow_direction_d8.tif",
    "stream_network": "stream_network.gpkg",
    "pour_points": "pour_points.gpkg",
    "sub_catchments": "sub_catchments.gpkg",
}


# -----------------------------------------------------------------------------
# Logging configuration
# -----------------------------------------------------------------------------
logger = setup_logger(__name__, log_dir=FILE_CONFIG["logs_dir"])


# -----------------------------------------------------------------------------
# Stage 1: Automated DEM Acquisition
# -----------------------------------------------------------------------------
def download_dem_for_aoi(
    bbox: Tuple[float, float, float, float],
    output_dir: Path,
    resolution: int = 10,
) -> Optional[str]:
    """
    Downloads a DEM for a given bounding box using the Seamless3DEP library.

    Args:
        bbox (Tuple[float, float, float, float]): The bounding box coordinates.
        output_dir (Path): The output directory.
        resolution (int, optional): The DEM resolution. Defaults to 10.

    Returns:
        Optional[str]: The path to the downloaded DEM file or None if failed.
    """
    logger.info(f"Starting DEM download for BBOX: {bbox}")
    data_dir = output_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    try:
        tiff_files = s3dep.get_dem(bbox, data_dir, res=resolution)
        if not tiff_files:
            raise Exception("No DEM files were downloaded. AOI may be outside data coverage.")
        logger.info("Successfully downloaded %s DEM tile(s).", len(tiff_files))

        if len(tiff_files) > 1:
            merged_dem_path = data_dir / FILE_CONFIG["merged_dem"]
            src_files_to_mosaic = [rasterio.open(f) for f in tiff_files]
            mosaic, out_trans = rasterio.merge.merge(src_files_to_mosaic)

            out_meta = src_files_to_mosaic[0].meta.copy()
            out_meta.update(
                {
                    "driver": "GTiff",
                    "height": mosaic.shape[1],
                    "width": mosaic.shape[2],
                    "transform": out_trans,
                }
            )

            with rasterio.open(str(merged_dem_path), "w", **out_meta) as dest:
                dest.write(mosaic)

            logger.info("Merged DEM tiles into: %s", merged_dem_path)
            return str(merged_dem_path)
        else:
            dem_path = str(tiff_files[0])
            logger.info("DEM available at: %s", dem_path)
            return dem_path

    except Exception as e:
        logger.error("DEM download failed: %s", e, exc_info=True)
        return None


# -----------------------------------------------------------------------------
# Stage 2 & 3: Core Hydrology & Stream Network with PySheds
# -----------------------------------------------------------------------------
def perform_core_hydrology(dem_path: str, project_dir: str, stream_threshold: int) -> Dict[str, Any]:
    """Performs the core hydrologic processing using PySheds."""
    logger.info("Starting core hydrologic analysis with PySheds...")

    with rasterio.open(dem_path) as src:
        dem_crs = src.crs

    grid = Grid.from_raster(dem_path)
    dem = grid.read_raster(dem_path)

    logger.info("Step 1: Filling sinks...")
    filled_dem = grid.fill_depressions(dem)

    logger.info("Step 2: Resolving flats...")
    inflated_dem = grid.resolve_flats(filled_dem)

    logger.info("Step 3: Calculating D8 flow direction...")
    fdir = grid.flowdir(inflated_dem)

    logger.info("Step 4: Calculating flow accumulation...")
    acc = grid.accumulation(fdir)

    logger.info("Step 5: Extracting stream network...")
    streams = grid.extract_river_network(fdir, acc > stream_threshold)

    output_dir = Path(project_dir) / FILE_CONFIG["pysheds_outputs_dir"]
    output_dir.mkdir(exist_ok=True)

    grid.to_raster(acc, str(output_dir / FILE_CONFIG["flow_accumulation"]))
    grid.to_raster(fdir, str(output_dir / FILE_CONFIG["flow_direction"]))

    stream_network_path = None
    if streams["features"]:
        stream_network_path = str(output_dir / FILE_CONFIG["stream_network"])
        gdf = gpd.GeoDataFrame.from_features(streams["features"])
        gdf.crs = dem_crs
        gdf.to_file(stream_network_path, driver="GPKG")
    else:
        logger.warning("No streams were extracted at the given threshold.")

    logger.info("Core hydrology complete. Outputs saved in 'pysheds_outputs'.")

    return {
        "grid": grid,
        "fdir": fdir,
        "acc": acc,
        "stream_network_path": stream_network_path,
        "crs": dem_crs,
    }


# -----------------------------------------------------------------------------
# Stage 4: Hydrolocation (Pour Point) Identification
# -----------------------------------------------------------------------------
def find_pour_points_with_networkx(
    stream_network_path: Optional[str], project_dir: str, crs: Any
) -> Tuple[Optional[str], List[Tuple[float, float]]]:
    """Identifies stream junctions and termini using NetworkX and GeoPandas."""
    if not stream_network_path:
        logger.warning("No stream network available. Skipping pour point identification.")
        return None, []

    logger.info("Identifying all pour points (junctions and termini) using NetworkX...")

    streams_gdf = gpd.read_file(stream_network_path)
    output_path = Path(project_dir) / FILE_CONFIG["pysheds_outputs_dir"] / FILE_CONFIG["pour_points"]

    G = nx.DiGraph()
    logger.debug("Reading stream features and building a complete graph...")

    for _, row in streams_gdf.iterrows():
        line = row.geometry
        for i in range(len(line.coords) - 1):
            start_node = line.coords[i]
            end_node = line.coords[i + 1]
            G.add_edge(start_node, end_node)

    logger.info(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

    junction_nodes, termini_nodes = [], []
    for node in G.nodes():
        if G.in_degree(node) >= 2:
            junction_nodes.append(node)
        elif G.in_degree(node) == 0:
            termini_nodes.append(node)

    logger.info(f"Found {len(junction_nodes)} junctions and {len(termini_nodes)} termini.")

    points_data = []
    for node in junction_nodes:
        points_data.append({"geometry": Point(node), "point_type": "JUNCTION"})
    for node in termini_nodes:
        points_data.append({"geometry": Point(node), "point_type": "TERMINUS"})

    if not points_data:
        logger.warning("No pour points were identified from the graph.")
        return None, []

    pour_points_gdf = gpd.GeoDataFrame(points_data, crs=crs)
    pour_points_gdf.to_file(str(output_path), driver="GPKG")

    x_coords = pour_points_gdf.geometry.x.tolist()
    y_coords = pour_points_gdf.geometry.y.tolist()

    logger.info("Pour points feature class created: %s", output_path)
    return str(output_path), (x_coords, y_coords)


# -----------------------------------------------------------------------------
# Stage 5: Watershed and Sub-catchment Delineation
# -----------------------------------------------------------------------------
def delineate_sub_catchments(
    hydrology_data: Dict[str, Any],
    pour_point_coords: Tuple[List[float], List[float]],
    project_dir: str,
    crs: Any,
) -> Optional[str]:
    """Delineates all sub-catchments from a set of pour points."""
    logger.info("Starting sub-catchment delineation from all pour points...")

    grid = hydrology_data["grid"]
    fdir = hydrology_data["fdir"]
    acc = hydrology_data["acc"]
    x, y = pour_point_coords

    # Reshape coordinates for snap_to_mask, which expects a (N, 2) array of points
    pour_points_array = np.array(list(zip(x, y)))
    snapped_pour_points = grid.snap_to_mask(acc > 0, pour_points_array)

    all_catchments_shapes = []
    logger.info(f"Delineating catchments for {len(snapped_pour_points)} initial pour points...")
    successfully_delineated_count = 0

    for i, (x_snap, y_snap) in enumerate(snapped_pour_points):
        # Delineate the catchment for a single pour point
        catchment = grid.catchment(x=x_snap, y=y_snap, fdir=fdir)
        # Polygonize the catchment, converting boolean to uint8 for rasterio
        shapes = grid.polygonize(catchment.astype(np.uint8))

        # Collect all parts of the catchment for the current pour point
        polygons_for_this_point = []
        for geom, value in shapes:
            if value == 1:  # The catchment area
                polygons_for_this_point.append(shape(geom))

        if polygons_for_this_point:
            all_catchments_shapes.extend(polygons_for_this_point)
            successfully_delineated_count += 1
        else:
            logger.warning(
                f"No valid catchment polygon found for pour point {i + 1} at coordinates ({x_snap}, {y_snap})."
            )

    logger.info(
        f"Successfully delineated {successfully_delineated_count} catchments out of {len(snapped_pour_points)} snapped pour points."
    )
    if not all_catchments_shapes:
        logger.warning("No sub-catchments could be delineated and saved.")
        return None

    # Create a GeoDataFrame from all the collected catchment polygons
    sub_catchments_gdf = gpd.GeoDataFrame(geometry=all_catchments_shapes, crs=crs)

    output_path = Path(project_dir) / FILE_CONFIG["pysheds_outputs_dir"] / FILE_CONFIG["sub_catchments"]
    sub_catchments_gdf.to_file(str(output_path), driver="GPKG")
    logger.info("Sub-catchment delineation complete. Output: %s", output_path)
    return str(output_path)


# -----------------------------------------------------------------------------
# Main Workflow Execution
# -----------------------------------------------------------------------------
def run_full_workflow_os(
    bbox: Tuple[float, float, float, float],
    project_dir: str,
    dem_resolution: int,
    stream_threshold: int,
) -> None:
    """Executes the entire automated hydrologic analysis workflow."""
    try:
        dem_output_dir = Path(project_dir) / FILE_CONFIG["input_dem_dir"]
        input_dem_path = download_dem_for_aoi(bbox, dem_output_dir, dem_resolution)
        if not input_dem_path:
            logger.info("\nWorkflow halted due to DEM acquisition failure.")
            return

        hydrology_data = perform_core_hydrology(input_dem_path, project_dir, stream_threshold)

        dem_crs = hydrology_data["crs"]
        pour_points_path, pour_point_coords = find_pour_points_with_networkx(
            hydrology_data["stream_network_path"], project_dir, crs=dem_crs
        )

        if pour_points_path:
            delineate_sub_catchments(hydrology_data, pour_point_coords, project_dir, crs=dem_crs)
        else:
            logger.warning("No pour points found, skipping sub-catchment delineation.")

    except Exception as e:
        logger.exception("An unexpected Python error occurred: %s", e)
    finally:
        logger.info("Open-source hydrologic analysis workflow has finished.")
