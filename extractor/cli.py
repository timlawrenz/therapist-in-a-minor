import click
from pathlib import Path
from .discovery import Scanner
from .scaffolding import Scaffolder

@click.group()
def cli():
    pass

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
    for source_file in scanner.scan():
        click.echo(f"  Processing {source_file.relative_to(source)}...")
        target_folder = scaffolder.create_scaffold(source_file)
        scaffolder.link_source(source_file, target_folder)
        scaffolder.write_manifest(source_file, target_folder)
        count += 1
        
    click.echo(f"Successfully processed {count} documents.")

if __name__ == '__main__':
    cli()