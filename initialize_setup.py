from core.db_manager import DatabaseManager
import os

def main():
    # Ensure the data folder exists
    if not os.path.exists('data'):
        os.makedirs('data')
        print("Created 'data' directory.")

    db = DatabaseManager()
    db.setup_database()
    print("Optimization: Everything is ready to go!")

if __name__ == "__main__":
    main()