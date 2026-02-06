import click
import logging
import os
import sys
from pathlib import Path
from .discovery import Scanner
from .scaffolding import Scaffolder
from .docling_engine import DoclingEngine
from .enrichment_engine import EnrichmentEngine
from .facial_engine import FacialEngine
import json


def _maybe_enable_hang_diagnostics():
    """Optional: enable stack dumps to debug hangs (off by default)."""
    dump_after = os.getenv("EXTRACTOR_DUMP_STACK_AFTER")
    if not dump_after:
        return

    try:
        import faulthandler
        import signal

        faulthandler.enable()
        try:
            faulthandler.register(signal.SIGUSR1)
        except Exception:
            pass

        faulthandler.dump_traceback_later(int(dump_after), repeat=True)
    except Exception:
        return

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
    _maybe_enable_hang_diagnostics()
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
@click.option('--force', is_flag=True, help='Force overwrite of existing processed documents')
def process(source, target, force):
    """Discover + extract in a single step (creates per-doc folder + symlink, then runs extraction)."""
    click.echo(f"Processing from {source} to {target}")

    try:
        engine = DoclingEngine()
        enrichment_engine = EnrichmentEngine()
        facial_engine = FacialEngine()
        scanner = Scanner(source)
        scaffolder = Scaffolder(source if source.is_dir() else source.parent, target)

        count = 0
        errors = 0
        skipped = 0

        for source_file in scanner.scan():
            if source_file.suffix.lower() != ".pdf":
                logger.debug(f"Skipping non-PDF file: {source_file}")
                continue

            try:
                if source.is_file():
                    output_dir = target / source_file.stem
                else:
                    output_dir = scaffolder.get_target_folder(source_file)

                if not force and scaffolder.is_extraction_complete(output_dir, source_file.stem):
                    logger.info(f"Skipping already processed {source_file}")
                    skipped += 1
                    continue

                output_dir.mkdir(parents=True, exist_ok=True)
                try:
                    scaffolder.link_source(source_file, output_dir)
                except Exception as e:
                    logger.debug(f"Failed to link source for {source_file}: {e}")

                logger.info(f"Processing {source_file} -> {output_dir}")

                result = engine.convert(source_file)

                engine.save_markdown(result, output_dir / f"{source_file.stem}.md")
                engine.save_json(result, output_dir / f"{source_file.stem}.json")
                image_metadata = engine.save_images(result, output_dir / "images")

                if image_metadata:
                    logger.info(f"Enriching {len(image_metadata)} images for {source_file.name}...")
                    for img_data in image_metadata:
                        img_path = Path(img_data["path"])

                        description = enrichment_engine.describe_image(img_path)
                        embeddings = enrichment_engine.embed_image(img_path)
                        faces = facial_engine.detect_faces(img_path) if facial_engine.enabled else []

                        img_data["description"] = description
                        img_data["embeddings"] = embeddings
                        img_data["faces"] = faces

                    images_dir = output_dir / "images"
                    with open(images_dir / "image_metadata.json", "w", encoding="utf-8") as f:
                        json.dump(image_metadata, f, indent=2, ensure_ascii=False)

                engine.generate_manifest(result, output_dir / "manifest.json", image_metadata)

                count += 1
            except Exception as e:
                logger.error(f"Error extracting {source_file}: {e}")
                click.echo(f"Error extracting {source_file}: {e}", err=True)
                errors += 1

        click.echo(f"Processing complete.")
        click.echo(f"  Successfully processed:   {count}")
        click.echo(f"  Skipped (already exists): {skipped}")
        click.echo(f"  Errors encountered:       {errors}")

    except Exception as e:
        logger.critical(f"Critical error during processing: {e}")
        sys.exit(1)


@cli.command()
@click.option('--source', required=True, type=click.Path(exists=True, file_okay=True, path_type=Path), help='Source file or directory path')
@click.option('--target', required=True, type=click.Path(path_type=Path), help='Target directory path')
@click.option('--force', is_flag=True, help='Force overwrite of existing processed documents')
def extract(source, target, force):
    """
    Extracts text and images from documents using Docling.
    """
    click.echo(f"Extracting from {source} to {target}")
    
    try:
        engine = DoclingEngine()
        enrichment_engine = EnrichmentEngine()
        facial_engine = FacialEngine() # Initialize FacialEngine
        scanner = Scanner(source)
        scaffolder = Scaffolder(source, target)
        
        count = 0
        errors = 0
        skipped = 0
        
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
                
                # Check for resumption
                if not force and scaffolder.is_extraction_complete(output_dir, source_file.stem):
                    logger.info(f"Skipping already processed {source_file}")
                    skipped += 1
                    continue

                output_dir.mkdir(parents=True, exist_ok=True)
                
                logger.info(f"Processing {source_file} -> {output_dir}")
                
                result = engine.convert(source_file)
                
                # Save artifacts
                engine.save_markdown(result, output_dir / f"{source_file.stem}.md")
                engine.save_json(result, output_dir / f"{source_file.stem}.json")
                image_metadata = engine.save_images(result, output_dir / "images")
                
                # Enrichment
                if image_metadata:
                    logger.info(f"Enriching {len(image_metadata)} images for {source_file.name}...")
                    for img_data in image_metadata:
                        img_path = Path(img_data["path"])
                        
                        description = enrichment_engine.describe_image(img_path)
                        embeddings = enrichment_engine.embed_image(img_path)
                        faces = facial_engine.detect_faces(img_path) if facial_engine.enabled else []

                        img_data["description"] = description
                        img_data["embeddings"] = embeddings
                        img_data["faces"] = faces
                    
                    # Save image_metadata.json
                    images_dir = output_dir / "images"
                    with open(images_dir / "image_metadata.json", "w", encoding="utf-8") as f:
                        json.dump(image_metadata, f, indent=2, ensure_ascii=False)
                
                engine.generate_manifest(result, output_dir / "manifest.json", image_metadata)
                
                count += 1
            except Exception as e:
                logger.error(f"Error extracting {source_file}: {e}")
                click.echo(f"Error extracting {source_file}: {e}", err=True)
                errors += 1
                
        click.echo(f"Extraction complete.")
        click.echo(f"  Successfully extracted:   {count}")
        click.echo(f"  Skipped (already exists): {skipped}")
        click.echo(f"  Errors encountered:       {errors}")
        
    except Exception as e:
        logger.critical(f"Critical error during extraction: {e}")
        sys.exit(1)

if __name__ == '__main__':
    cli()
