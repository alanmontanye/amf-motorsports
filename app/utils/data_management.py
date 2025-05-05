"""Utilities for managing data backup and restore"""
import json
from datetime import datetime, date
import os
from app.models import ATV, Part, Image, Storage, Expense, Sale
from app import db

# Helper function to format datetime objects
def _format_date(date_obj):
    if date_obj is None:
        return None
    if isinstance(date_obj, (datetime, date)):
        return date_obj.strftime('%Y-%m-%d')
    return str(date_obj)

def export_data(export_path=None):
    """Export all data from the application to a JSON file"""
    if export_path is None:
        # Create a backup directory if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_path = os.path.join(backup_dir, f'backup_{timestamp}.json')
    
    # Helper function to serialize objects to JSON
    def serialize(obj):
        if isinstance(obj, (datetime, date)):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return str(obj)
    
    data = {
        'atvs': [],
        'parts': [],
        'images': [],
        'storages': [],
        'expenses': [],
        'sales': []
    }
    
    # Export ALL ATVs including deleted ones
    for atv in ATV.query.all():
        atv_data = {
            'id': atv.id,
            'make': atv.make,
            'model': atv.model,
            'year': atv.year,
            'vin': atv.vin,  # Add the VIN field
            'status': atv.status,
            'purchase_date': _format_date(atv.purchase_date),
            'purchase_price': atv.purchase_price,
            'purchase_location': atv.purchase_location,
            'description': atv.description,
            'total_earnings': getattr(atv, 'total_earnings', None),
            # Add hours tracking fields
            'acquisition_hours': getattr(atv, 'acquisition_hours', 0),
            'repair_hours': getattr(atv, 'repair_hours', 0),
            'selling_hours': getattr(atv, 'selling_hours', 0),
            'total_hours': getattr(atv, 'total_hours', 0),
            'created_at': serialize(atv.created_at),
            'updated_at': serialize(atv.updated_at)
        }
        data['atvs'].append(atv_data)
    
    # Export Parts
    for part in Part.query.all():
        part_data = {
            'id': part.id,
            'name': part.name,
            'part_number': part.part_number,
            'condition': part.condition,
            'location': part.location,
            'storage_id': part.storage_id,
            'status': part.status,
            'source_price': part.source_price,
            'list_price': part.list_price,
            'sold_price': part.sold_price,
            'sold_date': serialize(part.sold_date) if part.sold_date else None,
            'shipping_cost': part.shipping_cost,
            'platform_fees': part.platform_fees,
            'platform': part.platform,
            'listing_url': part.listing_url,
            'atv_id': part.atv_id,
            'description': part.description,
            'created_at': serialize(part.created_at),
            'updated_at': serialize(part.updated_at)
        }
        data['parts'].append(part_data)
    
    # Export Images
    for image in Image.query.all():
        image_data = {
            'id': image.id,
            'filename': image.filename,
            'atv_id': image.atv_id,
            'part_id': image.part_id,
            'created_at': serialize(image.created_at),
            'description': image.description,
            'image_type': image.get('image_type', 'general')  # Add the image_type field
        }
        data['images'].append(image_data)
    
    # Export Storage Locations
    for storage in Storage.query.all():
        storage_data = {
            'id': storage.id,
            'name': storage.name,
            'description': storage.description,
            'created_at': serialize(storage.created_at),
            'updated_at': serialize(storage.updated_at)
        }
        data['storages'].append(storage_data)
    
    # Export Expenses
    for expense in Expense.query.all():
        expense_data = {
            'id': expense.id,
            'date': serialize(expense.date) if expense.date else None,
            'amount': expense.amount,
            'category': expense.category,
            'description': expense.description,
            'atv_id': expense.atv_id,
            'created_at': serialize(expense.created_at)
        }
        data['expenses'].append(expense_data)
    
    # Export Sales
    for sale in Sale.query.all():
        sale_data = {
            'id': sale.id,
            'date': serialize(sale.date) if sale.date else None,
            'amount': sale.amount,
            'platform': sale.platform,
            'fees': sale.fees,
            'shipping_cost': sale.shipping_cost,
            'net_amount': sale.net_amount,
            'type': sale.type,
            'atv_id': sale.atv_id,
            'description': sale.description,
            'created_at': serialize(sale.created_at)
        }
        data['sales'].append(sale_data)
    
    # Save to file
    with open(export_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return export_path

def import_data(import_path, clear_existing=False):
    """Import data from a JSON file"""
    # Read the JSON file
    with open(import_path, 'r') as f:
        data = json.load(f)
    
    # Ensure purchase_date is properly formatted
    for atv_data in data.get('atvs', []):
        if 'purchase_date' in atv_data and atv_data['purchase_date']:
            # Handle various date formats
            try:
                if isinstance(atv_data['purchase_date'], str):
                    # Try parsing different formats
                    for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                        try:
                            atv_data['purchase_date'] = datetime.strptime(atv_data['purchase_date'], fmt).date()
                            break
                        except ValueError:
                            continue
            except Exception as e:
                print(f"Error parsing purchase_date: {e}")
                atv_data['purchase_date'] = datetime.now().date()
    
    if clear_existing:
        # Drop all existing data by deleting all records instead of dropping tables
        # This avoids conflicts with the automatic table creation
        try:
            # Delete in reverse order of dependencies
            db.session.query(Sale).delete()
            db.session.query(Expense).delete()
            db.session.query(Image).delete()
            db.session.query(Part).delete()
            db.session.query(ATV).delete()
            db.session.query(Storage).delete()
            db.session.commit()
            print("All existing data deleted successfully")
        except Exception as e:
            db.session.rollback()
            print(f"Error clearing database: {str(e)}")
            raise
    
    try:
        # Import Storage Locations first (they have no dependencies)
        for storage_data in data['storages']:
            storage = Storage(
                id=storage_data['id'],
                name=storage_data['name'],
                description=storage_data['description']
            )
            if storage_data['created_at']:
                storage.created_at = datetime.fromisoformat(storage_data['created_at'])
            if storage_data['updated_at']:
                storage.updated_at = datetime.fromisoformat(storage_data['updated_at'])
            db.session.add(storage)
        db.session.commit()
        print(f"Imported {len(data['storages'])} storage locations")
        
        # Import ATVs
        for atv_data in data['atvs']:
            atv = ATV(
                id=atv_data['id'],
                make=atv_data['make'],
                model=atv_data['model'],
                year=atv_data['year'],
                vin=atv_data.get('vin', ''),
                status=atv_data['status'],
                purchase_price=atv_data['purchase_price'],
                purchase_location=atv_data['purchase_location'],
                description=atv_data['description'],
                total_earnings=atv_data.get('total_earnings', 0),
                # Add hours tracking fields with defaults if not present in backup
                acquisition_hours=atv_data.get('acquisition_hours', 0),
                repair_hours=atv_data.get('repair_hours', 0),
                selling_hours=atv_data.get('selling_hours', 0),
                total_hours=atv_data.get('total_hours', 0)
            )
            if atv_data['purchase_date']:
                atv.purchase_date = atv_data['purchase_date']
            if atv_data.get('created_at'):
                try:
                    if isinstance(atv_data['created_at'], str):
                        atv.created_at = datetime.strptime(atv_data['created_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    else:
                        atv.created_at = atv_data['created_at']
                except:
                    atv.created_at = datetime.now()
            if atv_data.get('updated_at'):
                try:
                    if isinstance(atv_data['updated_at'], str):
                        atv.updated_at = datetime.strptime(atv_data['updated_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    else:
                        atv.updated_at = atv_data['updated_at']
                except:
                    atv.updated_at = datetime.now()
            db.session.add(atv)
        db.session.commit()
        print(f"Imported {len(data['atvs'])} ATVs")
        
        # Import Parts
        for part_data in data['parts']:
            part = Part(
                id=part_data['id'],
                name=part_data['name'],
                part_number=part_data['part_number'],
                condition=part_data['condition'],
                location=part_data['location'],
                storage_id=part_data['storage_id'],
                status=part_data['status'],
                source_price=part_data['source_price'],
                list_price=part_data['list_price'],
                sold_price=part_data['sold_price'],
                shipping_cost=part_data['shipping_cost'],
                platform_fees=part_data['platform_fees'],
                platform=part_data['platform'],
                listing_url=part_data['listing_url'],
                atv_id=part_data['atv_id'],
                description=part_data['description']
            )
            if part_data['sold_date']:
                part.sold_date = datetime.fromisoformat(part_data['sold_date'])
            if part_data.get('created_at'):
                try:
                    if isinstance(part_data['created_at'], str):
                        part.created_at = datetime.strptime(part_data['created_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    else:
                        part.created_at = part_data['created_at']
                except:
                    part.created_at = datetime.now()
            if part_data.get('updated_at'):
                try:
                    if isinstance(part_data['updated_at'], str):
                        part.updated_at = datetime.strptime(part_data['updated_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    else:
                        part.updated_at = part_data['updated_at']
                except:
                    part.updated_at = datetime.now()
            db.session.add(part)
        db.session.commit()
        print(f"Imported {len(data['parts'])} parts")
        
        # Import Images
        for image_data in data['images']:
            image = Image(
                id=image_data['id'],
                filename=image_data['filename'],
                atv_id=image_data['atv_id'],
                part_id=image_data['part_id'],
                description=image_data['description'],
                image_type=image_data.get('image_type', 'general')  
            )
            if image_data['created_at']:
                try:
                    if isinstance(image_data['created_at'], str):
                        image.created_at = datetime.strptime(image_data['created_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    else:
                        image.created_at = image_data['created_at']
                except:
                    image.created_at = datetime.now()
            db.session.add(image)
        db.session.commit()
        print(f"Imported {len(data['images'])} images")
        
        # Import Expenses
        for expense_data in data['expenses']:
            expense = Expense(
                id=expense_data['id'],
                amount=expense_data['amount'],
                category=expense_data['category'],
                description=expense_data['description'],
                atv_id=expense_data['atv_id']
            )
            if expense_data['date']:
                expense.date = datetime.fromisoformat(expense_data['date'])
            if expense_data.get('created_at'):
                try:
                    if isinstance(expense_data['created_at'], str):
                        expense.created_at = datetime.strptime(expense_data['created_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    else:
                        expense.created_at = expense_data['created_at']
                except:
                    expense.created_at = datetime.now()
            db.session.add(expense)
        db.session.commit()
        print(f"Imported {len(data['expenses'])} expenses")
        
        # Import Sales
        for sale_data in data['sales']:
            sale = Sale(
                id=sale_data['id'],
                amount=sale_data['amount'],
                platform=sale_data['platform'],
                fees=sale_data['fees'],
                shipping_cost=sale_data['shipping_cost'],
                net_amount=sale_data['net_amount'],
                type=sale_data['type'],
                atv_id=sale_data['atv_id'],
                description=sale_data['description']
            )
            if sale_data['date']:
                sale.date = datetime.fromisoformat(sale_data['date'])
            if sale_data.get('created_at'):
                try:
                    if isinstance(sale_data['created_at'], str):
                        sale.created_at = datetime.strptime(sale_data['created_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    else:
                        sale.created_at = sale_data['created_at']
                except:
                    sale.created_at = datetime.now()
            db.session.add(sale)
        db.session.commit()
        print(f"Imported {len(data['sales'])} sales")
    except Exception as e:
        db.session.rollback()
        print(f"Error importing data: {str(e)}")
        raise
