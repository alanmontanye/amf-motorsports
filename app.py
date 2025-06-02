from app import create_app, db
from app.models import ATV, Expense, Sale, Part, Image, EbayListing

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'ATV': ATV,
        'Expense': Expense,
        'Sale': Sale,
        'Part': Part,
        'Image': Image,
        'EbayListing': EbayListing
    }
