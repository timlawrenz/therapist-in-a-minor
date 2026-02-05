import click
import logging
import sys
from pathlib import Path
from .discovery import Scanner
from .scaffolding import Scaffolder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

@click.group()
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def cli(verbose):
    if verbose:
        logger.setLevel(logging.DEBUG)

@cli.command()
@click.option('--source', required=True, type=click.Path(exists=True, file_okay=False, path_type=Path), help='Source directory path')
@click.option('--target', required=True, type=click.Path(path_type=Path), help='Target directory path')
def discover(source, target):
    """
    Recursively discovers documents and creates a scaffold in the target directory.
    """
    click.echo(f"Discovering from {source} to {target}")
    
    scanner = Scanner(source)
    scaffolder = Scaffolder(source, target)
    
    count = 0
    errors = 0
    
    try:
        for source_file in scanner.scan():
            try:
                logger.debug(f"Processing {source_file.relative_to(source)}...")
                target_folder = scaffolder.create_scaffold(source_file)
                scaffolder.link_source(source_file, target_folder)
                scaffolder.write_manifest(source_file, target_folder)
                count += 1
            except Exception as e:
                logger.error(f"Error processing {source_file}: {e}")
                click.echo(f"Error processing {source_file}: {e}", err=True)
                errors += 1
    except Exception as e:
        logger.critical(f"Critical error during discovery: {e}")
        sys.exit(1)
        
    click.echo(f"Processing complete.")
    click.echo(f"  Successfully processed: {count}")
    click.echo(f"  Errors encountered:     {errors}")

if __name__ == '__main__':
    cli()
