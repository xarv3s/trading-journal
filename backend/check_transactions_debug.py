from app.core.database import SessionLocal
from app.models.all_models import Transaction

db = SessionLocal()
transactions = db.query(Transaction).all()
print(f"Total transactions: {len(transactions)}")
