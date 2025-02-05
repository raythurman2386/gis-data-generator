import click
from src.tools.generator import main as generator
from src.tools.batch_generator import batch_process_regions
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@click.group()
def cli():
    """GIS Data Generator CLI tool for generating synthetic GIS data."""
    pass


@cli.command()
@click.option('--region', default='oklahoma_city', help='Region to generate data for')
def generate(region):
    """Generate GIS data for a single region."""
    generator(region=region)


@cli.command()
@click.option('--batch-size', default=20, help='Number of regions to process in each batch')
@click.option('--wait-minutes', default=30, help='Wait time between batches in minutes')
@click.option('--data-types', default=['pois', 'routes', 'polygons'], multiple=True, help='Types of data to generate')
def batch(batch_size, wait_minutes, data_types):
    """Generate GIS data for multiple regions in batches."""
    batch_process_regions(
        batch_size=batch_size,
        wait_minutes=wait_minutes,
        data_types=list(data_types)
    )


if __name__ == "__main__":
    cli()
