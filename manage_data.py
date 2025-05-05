"""Command-line interface for data management"""
import click
from app import create_app
from app.utils.data_management import export_data, import_data

app = create_app()

@click.group()
def cli():
    """Data management commands for AMF Motorsports"""
    pass

@cli.command()
@click.option('--output', '-o', help='Output file path (optional, defaults to backups/backup_TIMESTAMP.json)')
def backup(output):
    """Export all data to a JSON file"""
    with app.app_context():
        output_path = export_data(output)
        click.echo(f'Data exported to: {output_path}')

@cli.command()
@click.argument('input_file')
@click.option('--clear/--no-clear', default=False, help='Clear existing data before import')
def restore(input_file, clear):
    """Import data from a JSON file"""
    if clear:
        if not click.confirm('This will delete all existing data. Are you sure?'):
            return
    
    with app.app_context():
        import_data(input_file, clear)
        click.echo('Data imported successfully!')

if __name__ == '__main__':
    cli()
