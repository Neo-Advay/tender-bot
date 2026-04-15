
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.tender import Base, Tender
from core.config_loader import load_config

class DatabaseManager:
    def __init__(self):
        # Load the path from our config.yaml
        config = load_config()
        db_path = config['database']['path']
        
        # Connect to SQLite (it will create the file if it doesn't exist)
        self.engine = create_engine(f"sqlite:///{db_path}")
        
        # Create a session factory
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    def setup_database(self):
        """Creates the tables based on our models."""
        Base.metadata.create_all(self.engine)
        print("Database tables created successfully.")

    def save_tender(self, tender_data):
        """Saves a single tender or updates it if it exists."""
        session = self.Session()
        try:
            # Try to find if it already exists by its external_id
            existing = session.query(Tender).filter_by(external_id=tender_data.external_id).first()
            
            if existing:
                # Update attributes if needed (e.g., if description changed)
                for key, value in tender_data.__dict__.items():
                    if not key.startswith('_'):
                        setattr(existing, key, value)
            else:
                session.add(tender_data)
                
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error saving tender: {e}")
        finally:
            session.close()