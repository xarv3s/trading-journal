from app.core.database import engine, Base
from app.models.all_models import DailyAccountValue, WeeklyAccountValue

def create_tables():
    print("Creating tables...")
    # This will create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    create_tables()
