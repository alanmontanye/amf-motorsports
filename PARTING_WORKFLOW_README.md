# ATV Parting Workflow Implementation Guide

This document provides instructions for safely implementing the new parting workflow features in the AMF Motorsports application. These features include ATV parting status tracking, bulk part addition, quick part editing, tote-based filtering, and a parting dashboard.

## 🛡️ CRITICAL DATA SAFETY CONSIDERATIONS 🛡️

**IMPORTANT: The production database contains approximately 50 ATVs that represent days of work. This data MUST be preserved at all costs.**

- Always back up the database before performing any migrations
- Test all changes in a staging environment first
- Run the data migration scripts carefully in the correct order
- Validate data integrity after each step

## Migration Steps

### 1. Backup the Database

```bash
# For SQLite
cp amf_motorsports.db amf_motorsports_backup_$(date +%Y%m%d).db

# For PostgreSQL (on Render)
pg_dump -U username -d database_name > amf_motorsports_backup_$(date +%Y%m%d).sql
```

### 2. Apply Database Migration

The migration file `migrations/add_parting_fields.py` will add the necessary parting_status and machine_id fields to the ATV model without disrupting existing data.

```bash
# Run the migration (depends on your migration system)
flask db upgrade
```

### 3. Initialize Parting Data for Existing ATVs

Run the initialization script to ensure all existing ATVs have valid parting_status and machine_id values:

```bash
python scripts/initialize_parting_data.py
```

### 4. Deploy New Templates and Routes

The following new files have been created:
- `app/atv/parting.py` - Parting status management routes
- `app/atv/parts_bulk.py` - Bulk part addition routes
- `app/atv/quick_edit.py` - Quick inline editing routes
- `app/templates/atv/parting/dashboard.html` - Parting dashboard template
- `app/templates/atv/parts/bulk_add.html` - Bulk part addition template
- `app/templates/atv/parts/quick_edit.html` - Full page quick edit template
- `app/templates/atv/parts/quick_edit_form.html` - Quick edit form template

### 5. Blueprint Registration

The `app/atv/__init__.py` file has been updated to register the new blueprints:
- `parting_bp` - For parting status management
- `parts_bulk_bp` - For bulk part addition
- `quick_edit_bp` - For quick part editing

### 6. Navigation Updates

The navigation now includes a link to the new Parting Dashboard, which provides an overview of ATVs in various parting stages.

## New Features

### ATV Parting Status

ATVs now have a parting_status field with three possible values:
- `whole` - The ATV is intact and not being parted out
- `parting_out` - The ATV is in the process of being parted out
- `parted_out` - The ATV has been fully parted out

The ATV index page has been updated with filtering controls for these statuses.

### Bulk Part Addition

The new bulk part addition feature allows adding multiple parts to an ATV at once with shared tote and storage location values. This significantly speeds up the parting workflow.

### Quick Part Editing

Parts can now be edited inline via AJAX, providing a faster way to update part information without navigating away from the parts list page.

### Tote-Based Filtering

The parts list page now includes filtering controls for totes, making it easier to manage parts by their physical storage location.

### Parting Dashboard

The new parting dashboard provides an overview of the parting process, showing:
- ATVs in various parting stages
- Part counts by status
- ATVs with the most parts
- Recently parted ATVs

## Troubleshooting

If you encounter any issues during implementation:

1. Check the application logs for errors
2. Verify database migration was applied correctly
3. Ensure all new blueprints are registered
4. Check that all templates are in the correct locations
5. Restore from backup if necessary

For any data integrity concerns, contact technical support immediately.

## Data Safety Measures

The implementation includes several safeguards:
- Confirmation dialogs for status changes
- Validation of part data before saving
- Transaction-based database updates
- Auto-generation of machine IDs
- Intelligent defaults for parting status

Always prioritize data safety over feature implementation.
