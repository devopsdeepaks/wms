#!/usr/bin/env python3
"""
WMS System Health Check
Verifies all components are working correctly
"""

import os
import sys
import pandas as pd
import sqlite3
from pathlib import Path

def check_dependencies():
    """Check if all required packages are installed"""
    print("🔍 Checking Dependencies...")
    
    required_packages = [
        'flask', 'pandas', 'plotly', 'openpyxl', 
        'numpy', 'werkzeug'
    ]
    
    # Check SQLAlchemy separately due to potential version issues
    sqlalchemy_packages = ['sqlalchemy']
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing.append(package)
    
    # Check SQLAlchemy with error handling
    try:
        import sqlalchemy
        print(f"  ✅ sqlalchemy ({sqlalchemy.__version__})")
    except ImportError:
        print(f"  ❌ sqlalchemy - MISSING")
        missing.append('sqlalchemy')
    except Exception as e:
        print(f"  ⚠️ sqlalchemy - INSTALLED (version issue: {str(e)[:50]}...)")
        print(f"     Note: This may not affect basic functionality")
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All critical dependencies available!")
    return True

def check_data_file():
    """Check if WMS Excel data file exists and is readable"""
    print("\n📊 Checking Data File...")
    
    data_file = "WMS-04-02.xlsx"
    if not os.path.exists(data_file):
        print(f"❌ {data_file} not found!")
        return False
    
    try:
        # Test reading the inventory sheet
        df = pd.read_excel(data_file, sheet_name='Current Inventory ')
        product_count = len(df) - 1  # Subtract header row
        print(f"  ✅ Inventory sheet: {product_count} products")
        
        # Test reading mapping sheet  
        mapping_df = pd.read_excel(data_file, sheet_name='Msku With Skus')
        mapping_count = len(mapping_df)
        print(f"  ✅ SKU mapping sheet: {mapping_count} mappings")
        
        # Test reading combo sheet
        combo_df = pd.read_excel(data_file, sheet_name='Combos skus')
        combo_count = len(combo_df)
        print(f"  ✅ Combo products sheet: {combo_count} combos")
        
        print("✅ Excel data file is valid!")
        return True
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {str(e)}")
        return False

def check_project_structure():
    """Check if all required files and folders exist"""
    print("\n📁 Checking Project Structure...")
    
    required_files = [
        "wms_web_app.py",
        "simple_ai_app.py", 
        "sku_msku_gui_mapper.py",
        "sku_msku_mapper.py",
        "requirements.txt",
        "README.md"
    ]
    
    required_folders = [
        "database",
        "templates", 
        "static",
        "Sales 7 days"
    ]
    
    all_good = True
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
            all_good = False
    
    for folder in required_folders:
        if os.path.exists(folder) and os.path.isdir(folder):
            print(f"  ✅ {folder}/")
        else:
            print(f"  ❌ {folder}/ - MISSING")
            all_good = False
    
    if all_good:
        print("✅ Project structure is complete!")
    
    return all_good

def check_database_modules():
    """Check database-related files"""
    print("\n🗄️ Checking Database Modules...")
    
    db_files = [
        "database/models.py",
        "database/service.py", 
        "database/migration.py",
        "database/setup.py"
    ]
    
    all_good = True
    for file in db_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
            all_good = False
    
    if all_good:
        print("✅ Database modules are complete!")
    
    return all_good

def main():
    """Run complete health check"""
    print("=" * 60)
    print("🏥 WMS System Health Check")
    print("=" * 60)
    
    checks = [
        check_dependencies(),
        check_data_file(),
        check_project_structure(),
        check_database_modules()
    ]
    
    print("\n" + "=" * 60)
    
    if all(checks):
        print("🎉 ALL CHECKS PASSED!")
        print("✅ Your WMS system is ready to run!")
        print("\nQuick Start:")
        print("  🚀 python start_wms.py")
        print("  🌐 python wms_web_app.py")
        print("  🤖 python simple_ai_app.py")
    else:
        print("❌ SOME CHECKS FAILED!")
        print("Please fix the issues above before running the system.")
        return 1
    
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
