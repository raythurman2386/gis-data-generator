import click
from src.tools.generator import main as generator
from src.tools.batch_generator import batch_process_regions
from src.utils.logger import setup_logger
from src.tools.hydrologic_analysis import run_full_workflow_os

logger = setup_logger(__name__)


@click.group()
def cli():
    """GIS Data Generator CLI tool for generating synthetic GIS data."""
    pass


@cli.command()
@click.option("--region", default="oklahoma_city", help="Region to generate data for")
def generate(region):
    """Generate GIS data for a single region."""
    generator(region=region)


@cli.command()
@click.option("--batch-size", default=20, help="Number of regions to process in each batch")
@click.option("--wait-minutes", default=30, help="Wait time between batches in minutes")
@click.option("--data-types", default=["pois", "routes", "polygons"], multiple=True, help="Types of data to generate")
def batch(batch_size, wait_minutes, data_types):
    """Generate GIS data for multiple regions in batches."""
    batch_process_regions(batch_size=batch_size, wait_minutes=wait_minutes, data_types=list(data_types))


@cli.command()
@click.option(
    "--bbox", nargs=4, type=float, required=True, help="Bounding box in format: min_lon min_lat max_lon max_lat"
)
@click.option(
    "--project-dir",
    required=True,
    type=click.Path(file_okay=False, dir_okay=True, writable=True, resolve_path=True),
    help="Directory to save project outputs.",
)
@click.option("--resolution", default=10, type=int, help="DEM resolution in meters.")
@click.option("--threshold", default=5000, type=int, help="Stream network accumulation threshold.")
def hydrologic_analysis(bbox, project_dir, resolution, threshold):
    """Run the full hydrologic analysis workflow."""
    run_full_workflow_os(bbox=bbox, project_dir=project_dir, dem_resolution=resolution, stream_threshold=threshold)


if __name__ == "__main__":
    cli()
