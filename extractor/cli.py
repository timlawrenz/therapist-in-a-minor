import click
import logging
import sys
from pathlib import Path
from .discovery import Scanner
from .scaffolding import Scaffolder
from .docling_engine import DoclingEngine

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
        # Set level for the entire 'extractor' package
        logging.getLogger('extractor').setLevel(logging.DEBUG)
        # Also ensure root handler allows it if needed, but basicConfig set root to INFO.
        # We might need to adjust root or just the handler.
        # Generally, logger level filters first. 
        # But if root is INFO, does it block DEBUG from children? 
        # No, child logger level overrides if lower (more verbose).
        # But the handler attached to root (from basicConfig) is set to NOTSET by default? 
        # No, basicConfig sets root logger level. Handlers usually process everything passed to them.
        # Let's set root logger to DEBUG to be safe if 'extractor' logger propagates up.
        logging.getLogger().setLevel(logging.DEBUG)

@cli.command()
@click.option('--source', required=True, type=click.Path(exists=True, file_okay=False, path_type=Path), help='Source directory path')
@click.option('--target', required=True, type=click.Path(path_type=Path), help='Target directory path')
@click.option('--force', is_flag=True, help='Force overwrite of existing processed documents')
def discover(source, target, force):
    """
    Recursively discovers documents and creates a scaffold in the target directory.
    """
    click.echo(f"Discovering from {source} to {target}")
    
    scanner = Scanner(source)
    scaffolder = Scaffolder(source, target)
    
    count = 0
    skipped = 0
    errors = 0
    
    try:
        for source_file in scanner.scan():
            try:
                target_folder = scaffolder.get_target_folder(source_file)
                if not force and scaffolder.is_processed(target_folder):
                    logger.debug(f"Skipping already processed {source_file.relative_to(source)}...")
                    skipped += 1
                    continue

                logger.debug(f"Processing {source_file.relative_to(source)}...")
                scaffolder.create_scaffold(source_file)
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
    click.echo(f"  Successfully processed:   {count}")
    click.echo(f"  Skipped (already exists): {skipped}")
    click.echo(f"  Errors encountered:       {errors}")

@cli.command()
@click.option('--source', required=True, type=click.Path(exists=True, file_okay=True, path_type=Path), help='Source file or directory path')
@click.option('--target', required=True, type=click.Path(path_type=Path), help='Target directory path')
def extract(source, target):
    """
    Extracts text and images from documents using Docling.
    """
    click.echo(f"Extracting from {source} to {target}")
    
    try:
        engine = DoclingEngine()
        scanner = Scanner(source)
        
        count = 0
        errors = 0
        
        files_to_process = scanner.scan()
        
        for source_file in files_to_process:
            if source_file.suffix.lower() != ".pdf":
                logger.debug(f"Skipping non-PDF file: {source_file}")
                continue

            try:
                # Determine output directory (mirror structure)
                if source.is_file():
                    # For a single file, we can put output in target/filename_stem
                    output_dir = target / source_file.stem
                else:
                    # For directory, mirror structure
                    relative_path = source_file.relative_to(source)
                    # Structure: target / rel_path / filename_stem
                    # This puts artifacts in a folder dedicated to the document
                    output_dir = target / relative_path.parent / source_file.stem
                
                output_dir.mkdir(parents=True, exist_ok=True)
                
                logger.info(f"Processing {source_file} -> {output_dir}")
                
                result = engine.convert(source_file)
                
                # Save artifacts
                engine.save_markdown(result, output_dir / f"{source_file.stem}.md")
                engine.save_json(result, output_dir / f"{source_file.stem}.json")
                image_metadata = engine.save_images(result, output_dir / "images")
                engine.generate_manifest(result, output_dir / "manifest.json", image_metadata)
                
                count += 1
            except Exception as e:
                logger.error(f"Error extracting {source_file}: {e}")
                click.echo(f"Error extracting {source_file}: {e}", err=True)
                errors += 1
                
        click.echo(f"Extraction complete.")
        click.echo(f"  Successfully extracted:   {count}")
        click.echo(f"  Errors encountered:       {errors}")
        
    except Exception as e:
        logger.critical(f"Critical error during extraction: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()
