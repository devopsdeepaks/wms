"""
Part 4 Setup Script: AI over Data Layer
Comprehensive setup for AI-powered WMS with text-to-SQL capabilities
"""

import os
import sys
import subprocess
import sqlite3
import pandas as pd
from datetime import datetime

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"🤖 {title}")
    print("="*60)

def print_status(message, status="info"):
    """Print status message"""
    icons = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
    print(f"{icons.get(status, 'ℹ️')} {message}")

def check_python_version():
    """Check Python version compatibility"""
    print_header("Python Version Check")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - Compatible", "success")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+", "error")
        return False

def install_requirements():
    """Install required packages"""
    print_header("Installing AI Dependencies")
    
    try:
        # Install basic requirements
        basic_packages = [
            "flask==2.3.3",
            "pandas==2.1.1", 
            "numpy==1.24.3",
            "plotly==5.17.0",
            "sqlalchemy==2.0.21"
        ]
        
        for package in basic_packages:
            print_status(f"Installing {package.split('==')[0]}...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print_status(f"Installed {package.split('==')[0]}", "success")
            else:
                print_status(f"Failed to install {package}", "error")
                
        return True
    except Exception as e:
        print_status(f"Installation error: {str(e)}", "error")
        return False

def setup_ai_database():
    """Setup AI database with sample data"""
    print_header("Setting up AI Database")
    
    try:
        # Create database connection
        conn = sqlite3.connect('wms_ai_data.db')
        cursor = conn.cursor()
        
        print_status("Creating database tables...")
        
        # Create tables
        tables = {
            "products": """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    msku TEXT UNIQUE NOT NULL,
                    opening_stock INTEGER DEFAULT 0,
                    current_stock INTEGER DEFAULT 0,
                    buffer_stock INTEGER DEFAULT 5,
                    unit_cost REAL DEFAULT 0.0,
                    selling_price REAL DEFAULT 0.0,
                    category TEXT DEFAULT 'General',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "sales_records": """
                CREATE TABLE IF NOT EXISTS sales_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT,
                    platform TEXT NOT NULL,
                    msku TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL DEFAULT 0.0,
                    total_amount REAL DEFAULT 0.0,
                    sale_date DATE NOT NULL,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (msku) REFERENCES products(msku)
                )
            """,
            "sku_mappings": """
                CREATE TABLE IF NOT EXISTS sku_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku TEXT NOT NULL,
                    msku TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (msku) REFERENCES products(msku)
                )
            """,
            "inventory_movements": """
                CREATE TABLE IF NOT EXISTS inventory_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    msku TEXT NOT NULL,
                    movement_type TEXT NOT NULL,
                    quantity_change INTEGER NOT NULL,
                    movement_date DATE NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (msku) REFERENCES products(msku)
                )
            """
        }
        
        for table_name, table_sql in tables.items():
            cursor.execute(table_sql)
            print_status(f"Created {table_name} table", "success")
        
        # Check if we need sample data
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            print_status("Loading sample data...")
            load_sample_data(cursor)
        else:
            print_status("Database already has data", "info")
        
        conn.commit()
        conn.close()
        
        print_status("AI Database setup complete", "success")
        return True
        
    except Exception as e:
        print_status(f"Database setup error: {str(e)}", "error")
        return False

def load_sample_data(cursor):
    """Load sample data into database"""
    import random
    from datetime import datetime, timedelta
    
    # Sample products
    products = [
        ("Wireless Headphones", "MSKU001", 100, 85, 10, 25.0, 50.0, "Electronics"),
        ("Bluetooth Speaker", "MSKU002", 75, 65, 8, 15.0, 35.0, "Electronics"),
        ("Phone Case", "MSKU003", 200, 180, 20, 5.0, 15.0, "Accessories"),
        ("USB Cable", "MSKU004", 150, 140, 15, 3.0, 10.0, "Accessories"),
        ("Laptop Stand", "MSKU005", 50, 45, 5, 20.0, 45.0, "Office"),
        ("Mouse Pad", "MSKU006", 80, 75, 8, 8.0, 18.0, "Office"),
        ("Power Bank", "MSKU007", 60, 55, 6, 18.0, 40.0, "Electronics"),
        ("Screen Cleaner", "MSKU008", 120, 110, 12, 4.0, 12.0, "Accessories"),
        ("Desk Organizer", "MSKU009", 40, 35, 4, 12.0, 28.0, "Office"),
        ("LED Strip", "MSKU010", 90, 80, 9, 22.0, 48.0, "Electronics")
    ]
    
    for product in products:
        cursor.execute("""
            INSERT OR REPLACE INTO products 
            (product_name, msku, opening_stock, current_stock, buffer_stock, unit_cost, selling_price, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, product)
    
    # Sample SKU mappings
    platforms = ["Amazon", "Flipkart", "Meesho"]
    for i, (_, msku, *_) in enumerate(products):
        for j, platform in enumerate(platforms):
            if random.random() > 0.3:  # Not all products on all platforms
                sku = f"SKU{i+1:03d}{platform[0]}"
                cursor.execute("""
                    INSERT OR REPLACE INTO sku_mappings (sku, msku, platform)
                    VALUES (?, ?, ?)
                """, (sku, msku, platform))
    
    # Sample sales data for last 30 days
    for days_ago in range(30):
        sale_date = (datetime.now() - timedelta(days=days_ago)).date()
        
        # Random number of sales per day
        num_sales = random.randint(2, 8)
        
        for _ in range(num_sales):
            product = random.choice(products)
            msku = product[1]
            unit_price = product[6]  # selling_price
            quantity = random.randint(1, 5)
            platform = random.choice(platforms)
            
            cursor.execute("""
                INSERT INTO sales_records 
                (order_id, platform, msku, quantity, unit_price, total_amount, sale_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"ORD{random.randint(10000, 99999)}",
                platform,
                msku,
                quantity,
                unit_price,
                unit_price * quantity,
                sale_date
            ))
            
            # Add inventory movement
            cursor.execute("""
                INSERT INTO inventory_movements 
                (msku, movement_type, quantity_change, movement_date, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                msku,
                'Sale',
                -quantity,
                sale_date,
                f"Sale to {platform}"
            ))

def create_demo_files():
    """Create demo and documentation files"""
    print_header("Creating Demo Files")
    
    # Create demo script
    demo_script = """#!/usr/bin/env python3
\"\"\"
Demo Script for AI Data Layer
Run this to see AI capabilities in action
\"\"\"

from ai_data_layer import AIDataLayer

def main():
    print("🤖 AI Data Layer Demo")
    print("=" * 40)
    
    # Initialize AI layer
    ai = AIDataLayer()
    
    # Demo queries
    demo_queries = [
        "Show me top 5 selling products",
        "Which products have low stock?",
        "What are sales by platform?",
        "Show inventory movements this week"
    ]
    
    for query in demo_queries:
        print(f"\\n🔍 Query: {query}")
        result = ai.process_ai_query(query)
        
        if result['success']:
            print(f"✅ Found {result['row_count']} results")
            if result['calculated_fields']:
                print(f"➕ Added fields: {', '.join(result['calculated_fields'])}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    print("\\n🎉 Demo complete!")

if __name__ == "__main__":
    main()
"""
    
    with open('ai_demo.py', 'w') as f:
        f.write(demo_script)
    
    print_status("Created ai_demo.py", "success")
    
    # Create README
    readme_content = """# Part 4: AI over Data Layer

## 🤖 Features

### Text-to-SQL Capabilities
- Natural language query processing
- Intelligent SQL generation
- Support for complex analytical queries

### Calculated Fields
- Automatic profit margin calculation
- Stock status indicators  
- Performance metrics
- Trend analysis

### Interactive Charts
- Dynamic Plotly visualizations
- Multiple chart types (bar, pie, line, scatter)
- Real-time data updates
- Export capabilities

### AI Insights
- Automated pattern detection
- Performance alerts
- Trend identification
- Recommendation engine

## 🚀 Quick Start

1. **Install Dependencies:**
   ```bash
   pip install -r requirements_ai.txt
   ```

2. **Setup Database:**
   ```bash
   python setup_part4.py
   ```

3. **Run AI Application:**
   ```bash
   python ai_data_layer.py
   ```

4. **Access Interface:**
   - Open: http://localhost:5001
   - Try queries like "Show top selling products"

## 📊 Sample Queries

- "Show me top 10 selling products this month"
- "Which products have low stock levels?"
- "What are the sales trends for Amazon platform?"
- "Show inventory movement for combo products"
- "Which MSKUs have negative stock?"
- "Compare sales performance across platforms"

## 🔧 Technical Stack

- **Backend:** Flask + SQLAlchemy
- **Database:** SQLite (production: PostgreSQL/MySQL)
- **AI Layer:** Rule-based + OpenAI API (optional)
- **Visualization:** Plotly.js
- **Frontend:** Bootstrap 5 + JavaScript

## 🎯 Architecture

```
User Query → AI Parser → SQL Generator → Database → Results + Charts
```

## 📈 Advanced Features

### OpenAI Integration (Optional)
Add your OpenAI API key to enable advanced AI features:
```python
openai.api_key = "your-api-key-here"
```

### Custom Calculated Fields
The system automatically adds:
- Profit margins
- Stock status indicators
- Performance ratios
- Trend calculations

### Chart Types
- Bar charts for comparisons
- Pie charts for distributions  
- Line charts for trends
- Tables for detailed data
- Heatmaps for correlations

## 🔒 Security Notes

- Input sanitization for SQL injection prevention
- Query validation and limits
- User access controls (for production)
- Data privacy compliance
"""
    
    with open('README_AI.md', 'w') as f:
        f.write(readme_content)
    
    print_status("Created README_AI.md", "success")

def verify_setup():
    """Verify the complete setup"""
    print_header("Verifying Setup")
    
    checks = [
        ("ai_data_layer.py", "AI Data Layer script"),
        ("templates/ai_dashboard.html", "AI Dashboard template"),
        ("wms_ai_data.db", "AI Database"),
        ("ai_demo.py", "Demo script"),
        ("README_AI.md", "Documentation")
    ]
    
    all_good = True
    for file_path, description in checks:
        if os.path.exists(file_path):
            print_status(f"{description} - Found", "success")
        else:
            print_status(f"{description} - Missing", "error")
            all_good = False
    
    return all_good

def main():
    """Main setup function"""
    print_header("WMS Part 4: AI Data Layer Setup")
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_requirements():
        print_status("Failed to install requirements", "error")
        return False
    
    # Setup database
    if not setup_ai_database():
        print_status("Failed to setup database", "error")
        return False
    
    # Create demo files
    create_demo_files()
    
    # Verify setup
    if verify_setup():
        print_header("Setup Complete! 🎉")
        print_status("All components installed successfully", "success")
        print("\n📋 Next Steps:")
        print("1. Run: python ai_data_layer.py")
        print("2. Open: http://localhost:5001")
        print("3. Try: 'Show top selling products'")
        print("4. Demo: python ai_demo.py")
        
        return True
    else:
        print_status("Setup incomplete - please check errors above", "error")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
