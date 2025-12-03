import sys
import os
sys.path.append(os.getcwd())

from app.core.database import engine, Base
from app.models.all_models import *

def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init_db()
