"""
Database Setup and Initialization Script
Run this to set up the database for your WMS system
"""

import os
import sys
from flask import Flask

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import init_database
from database.migration import DatabaseMigration

def setup_database():
    """Complete database setup process"""
    print("🚀 Starting WMS Database Setup...")
    
    # Create Flask app
    app = Flask(__name__)
    
    # Initialize database
    print("📊 Initializing database...")
    db = init_database(app)
    
    # Run migration from Excel
    print("📥 Migrating data from Excel...")
    migration = DatabaseMigration(app)
    
    # Check if Excel file exists
    excel_file = 'WMS-04-02.xlsx'
    if os.path.exists(excel_file):
        migration.migrate_from_excel(excel_file)
    else:
        print(f"⚠️ Excel file {excel_file} not found. Database created but no data migrated.")
        print("   Place your Excel file and run migration.py separately.")
    
    print("✅ Database setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run the web application: python wms_web_app.py")
    print("3. Access the application at: http://localhost:5000")

if __name__ == '__main__':
    setup_database()
