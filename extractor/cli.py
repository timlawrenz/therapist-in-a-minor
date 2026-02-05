import click

@click.group()
def cli():
    pass

@cli.command()
@click.option('--source', required=True, help='Source directory path')
@click.option('--target', required=True, help='Target directory path')
def discover(source, target):
    click.echo(f"Discovering from {source} to {target}")

if __name__ == '__main__':
    cli()
