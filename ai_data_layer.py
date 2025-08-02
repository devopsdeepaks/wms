"""
Part 4: AI over Data Layer
Advanced WMS with AI-powered data retrieval, text-to-SQL, calculated fields, and intelligent charts
Uses OpenAI GPT for natural language to SQL conversion and Plotly for dynamic visualizations
"""

import pandas as pd
import sqlite3
import plotly.graph_objs as go
import plotly.express as px
import plotly.utils
from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime, timedelta
import re
from typing import Dict, List, Any
import numpy as np

# Import database components
try:
    from database.models import db, Product, SKUMapping, SalesRecord, InventoryMovement
    from database.service import DatabaseService
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️ Database not available, using SQLite fallback")

class AIDataLayer:
    """AI-powered data layer for intelligent querying and visualization"""
    
    def __init__(self, database_url=None):
        self.database_url = database_url or 'wms_ai_data.db'
        self.conn = None
        self.openai_client = None
        self.setup_database()
        self.setup_ai()
        
        # Sample queries for demonstration
        self.sample_queries = [
            "Show me top 10 selling products this month",
            "Which products have low stock levels?",
            "What are the sales trends for Amazon platform?",
            "Show inventory movement for combo products",
            "Which MSKUs have negative stock?",
            "Compare sales performance across platforms",
            "Show products with highest profit margins",
            "What's the inventory turnover rate?"
        ]
        
        # SQL templates for common queries
        self.sql_templates = {
            "top_selling": """
                SELECT p.product_name, p.msku, SUM(s.quantity) as total_sold
                FROM products p
                JOIN sales_records s ON p.msku = s.msku
                WHERE s.sale_date >= date('now', '-{days} days')
                GROUP BY p.msku, p.product_name
                ORDER BY total_sold DESC
                LIMIT {limit}
            """,
            "low_stock": """
                SELECT product_name, msku, current_stock, buffer_stock,
                       (current_stock - buffer_stock) as stock_difference
                FROM products
                WHERE current_stock < buffer_stock
                ORDER BY stock_difference ASC
            """,
            "platform_sales": """
                SELECT platform, COUNT(*) as order_count, SUM(quantity) as total_quantity
                FROM sales_records
                WHERE sale_date >= date('now', '-{days} days')
                GROUP BY platform
                ORDER BY total_quantity DESC
            """,
            "negative_stock": """
                SELECT product_name, msku, current_stock, opening_stock
                FROM products
                WHERE current_stock < 0
                ORDER BY current_stock ASC
            """,
            "inventory_movement": """
                SELECT p.product_name, im.movement_type, 
                       SUM(im.quantity_change) as total_movement,
                       COUNT(*) as movement_count
                FROM inventory_movements im
                JOIN products p ON im.msku = p.msku
                WHERE im.movement_date >= date('now', '-{days} days')
                GROUP BY p.msku, im.movement_type
                ORDER BY total_movement DESC
            """
        }
    
    def setup_database(self):
        """Setup SQLite database for AI queries"""
        try:
            self.conn = sqlite3.connect(self.database_url, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            
            # Create tables if they don't exist
            self.create_tables()
            
            # Load sample data if tables are empty
            if self.is_database_empty():
                self.load_sample_data()
                
            print(f"✅ AI Database initialized: {self.database_url}")
            
        except Exception as e:
            print(f"❌ Database setup failed: {str(e)}")
    
    def create_tables(self):
        """Create database tables for AI analysis"""
        cursor = self.conn.cursor()
        
        # Products table
        cursor.execute("""
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
        """)
        
        # SKU Mappings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sku_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL,
                msku TEXT NOT NULL,
                platform TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (msku) REFERENCES products(msku)
            )
        """)
        
        # Sales Records table
        cursor.execute("""
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
        """)
        
        # Inventory Movements table
        cursor.execute("""
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
        """)
        
        # Combo Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS combo_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                combo_sku TEXT NOT NULL,
                component_msku TEXT NOT NULL,
                quantity_required INTEGER DEFAULT 1,
                FOREIGN KEY (component_msku) REFERENCES products(msku)
            )
        """)
        
        self.conn.commit()
    
    def setup_ai(self):
        """Setup AI client for text-to-SQL conversion"""
        # For demo purposes, we'll use a simple rule-based approach
        # In production, you would use OpenAI API or similar
        
        # Uncomment and add your OpenAI API key for production use:
        # import openai
        # openai.api_key = "your-openai-api-key-here"
        # self.openai_client = openai
        
        print("✅ AI Layer initialized (Demo mode)")
    
    def is_database_empty(self):
        """Check if database has data"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        return count == 0
    
    def load_sample_data(self):
        """Load sample data for demonstration"""
        try:
            # Load from Excel if available
            if os.path.exists('WMS-04-02.xlsx'):
                self.load_data_from_excel()
            else:
                self.create_sample_data()
        except Exception as e:
            print(f"⚠️ Creating minimal sample data: {str(e)}")
            self.create_sample_data()
    
    def load_data_from_excel(self):
        """Load data from existing Excel file"""
        try:
            # Load inventory data
            inventory_df = pd.read_excel('WMS-04-02.xlsx', sheet_name='Current Inventory ')
            
            # Fix headers (same logic as before)
            if len(inventory_df) > 0:
                first_row = inventory_df.iloc[0]
                new_columns = []
                for val in first_row.values:
                    if pd.notna(val) and str(val).strip():
                        new_columns.append(str(val).strip())
                    else:
                        new_columns.append('Unknown_Column')
                
                inventory_df.columns = new_columns
                inventory_df = inventory_df.drop(0).reset_index(drop=True)
            
            # Insert products
            cursor = self.conn.cursor()
            for _, row in inventory_df.head(100).iterrows():  # Limit for demo
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO products 
                        (product_name, msku, opening_stock, current_stock, buffer_stock, unit_cost, selling_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('Product Name', 'Unknown Product'),
                        row.get('msku', f'MSKU_{len(inventory_df)}'),
                        int(row.get('Opening Stock', 0)) if pd.notna(row.get('Opening Stock')) else 0,
                        int(row.get('Opening Stock', 0)) if pd.notna(row.get('Opening Stock')) else 0,
                        int(row.get('Buffer Stock', 5)) if pd.notna(row.get('Buffer Stock')) else 5,
                        float(np.random.uniform(10, 100)),  # Random cost
                        float(np.random.uniform(15, 150))   # Random price
                    ))
                except Exception as e:
                    continue
            
            # Load SKU mappings
            try:
                mapping_df = pd.read_excel('WMS-04-02.xlsx', sheet_name='Msku With Skus')
                for _, row in mapping_df.head(50).iterrows():
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO sku_mappings (sku, msku, platform)
                            VALUES (?, ?, ?)
                        """, (
                            row.get('sku', ''),
                            row.get('msku', ''),
                            'Mixed'
                        ))
                    except:
                        continue
            except:
                pass
            
            # Generate sample sales data
            self.generate_sample_sales()
            
            self.conn.commit()
            print("✅ Data loaded from Excel file")
            
        except Exception as e:
            print(f"⚠️ Excel loading failed, using sample data: {str(e)}")
            self.create_sample_data()
    
    def create_sample_data(self):
        """Create minimal sample data"""
        cursor = self.conn.cursor()
        
        # Sample products
        sample_products = [
            ("Product A", "MSKU001", 100, 85, 10, 25.0, 40.0),
            ("Product B", "MSKU002", 50, 45, 5, 15.0, 25.0),
            ("Product C", "MSKU003", 200, 180, 20, 35.0, 55.0),
            ("Product D", "MSKU004", 75, 60, 8, 20.0, 32.0),
            ("Product E", "MSKU005", 30, 25, 5, 45.0, 70.0),
        ]
        
        for product in sample_products:
            cursor.execute("""
                INSERT OR REPLACE INTO products 
                (product_name, msku, opening_stock, current_stock, buffer_stock, unit_cost, selling_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, product)
        
        # Sample SKU mappings
        sample_mappings = [
            ("SKU001A", "MSKU001", "Amazon"),
            ("SKU001F", "MSKU001", "Flipkart"),
            ("SKU002A", "MSKU002", "Amazon"),
            ("SKU003M", "MSKU003", "Meesho"),
            ("SKU004F", "MSKU004", "Flipkart"),
        ]
        
        for mapping in sample_mappings:
            cursor.execute("""
                INSERT OR REPLACE INTO sku_mappings (sku, msku, platform)
                VALUES (?, ?, ?)
            """, mapping)
        
        self.generate_sample_sales()
        self.conn.commit()
        print("✅ Sample data created")
    
    def generate_sample_sales(self):
        """Generate sample sales data for the last 30 days"""
        cursor = self.conn.cursor()
        
        # Get all MSKUs
        cursor.execute("SELECT msku, selling_price FROM products")
        products = cursor.fetchall()
        
        platforms = ['Amazon', 'Flipkart', 'Meesho']
        
        # Generate sales for last 30 days
        for days_ago in range(30):
            sale_date = (datetime.now() - timedelta(days=days_ago)).date()
            
            # Random number of sales per day
            num_sales = np.random.randint(1, 8)
            
            for _ in range(num_sales):
                msku_data = np.random.choice(products)
                msku = msku_data[0]
                price = msku_data[1]
                
                quantity = np.random.randint(1, 5)
                platform = np.random.choice(platforms)
                
                cursor.execute("""
                    INSERT INTO sales_records 
                    (order_id, platform, msku, quantity, unit_price, total_amount, sale_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"ORD{np.random.randint(10000, 99999)}",
                    platform,
                    msku,
                    quantity,
                    price,
                    price * quantity,
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
        
        self.conn.commit()
    
    def natural_language_to_sql(self, query: str) -> Dict[str, Any]:
        """Convert natural language query to SQL (rule-based approach)"""
        query_lower = query.lower()
        
        # Simple rule-based matching
        if any(word in query_lower for word in ['top', 'best', 'highest', 'most']):
            if any(word in query_lower for word in ['selling', 'sold', 'sales']):
                return {
                    'sql': self.sql_templates['top_selling'].format(days=30, limit=10),
                    'chart_type': 'bar',
                    'title': 'Top Selling Products (Last 30 Days)'
                }
        
        elif any(word in query_lower for word in ['low stock', 'stock level', 'inventory']):
            return {
                'sql': self.sql_templates['low_stock'],
                'chart_type': 'table',
                'title': 'Low Stock Products'
            }
        
        elif any(word in query_lower for word in ['platform', 'amazon', 'flipkart', 'meesho']):
            return {
                'sql': self.sql_templates['platform_sales'].format(days=30),
                'chart_type': 'pie',
                'title': 'Sales by Platform (Last 30 Days)'
            }
        
        elif any(word in query_lower for word in ['negative', 'shortage']):
            return {
                'sql': self.sql_templates['negative_stock'],
                'chart_type': 'table',
                'title': 'Products with Negative Stock'
            }
        
        elif any(word in query_lower for word in ['movement', 'flow']):
            return {
                'sql': self.sql_templates['inventory_movement'].format(days=7),
                'chart_type': 'stacked_bar',
                'title': 'Inventory Movements (Last 7 Days)'
            }
        
        else:
            # Default query
            return {
                'sql': "SELECT COUNT(*) as total_products FROM products",
                'chart_type': 'metric',
                'title': 'Total Products'
            }
    
    def execute_query(self, sql: str) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        try:
            return pd.read_sql_query(sql, self.conn)
        except Exception as e:
            print(f"SQL Error: {str(e)}")
            return pd.DataFrame()
    
    def add_calculated_fields(self, df: pd.DataFrame, query_context: str) -> pd.DataFrame:
        """Add calculated fields based on the data and context"""
        if df.empty:
            return df
        
        df_calc = df.copy()
        
        # Add common calculated fields
        if 'total_sold' in df_calc.columns and 'unit_price' in df_calc.columns:
            df_calc['revenue'] = df_calc['total_sold'] * df_calc['unit_price']
        
        if 'current_stock' in df_calc.columns and 'buffer_stock' in df_calc.columns:
            df_calc['stock_status'] = df_calc.apply(
                lambda row: 'Critical' if row['current_stock'] < row['buffer_stock'] 
                else 'Low' if row['current_stock'] < row['buffer_stock'] * 2 
                else 'Normal', axis=1
            )
        
        if 'unit_cost' in df_calc.columns and 'selling_price' in df_calc.columns:
            df_calc['profit_margin'] = ((df_calc['selling_price'] - df_calc['unit_cost']) / df_calc['selling_price'] * 100).round(2)
        
        if 'opening_stock' in df_calc.columns and 'current_stock' in df_calc.columns:
            df_calc['stock_change'] = df_calc['current_stock'] - df_calc['opening_stock']
            df_calc['stock_change_pct'] = ((df_calc['stock_change'] / df_calc['opening_stock']) * 100).round(2)
        
        return df_calc
    
    def create_chart(self, df: pd.DataFrame, chart_type: str, title: str) -> dict:
        """Create interactive chart using Plotly"""
        if df.empty:
            return {"error": "No data available for chart"}
        
        try:
            if chart_type == 'bar':
                fig = px.bar(
                    df.head(10), 
                    x=df.columns[0], 
                    y=df.columns[-1],
                    title=title,
                    color=df.columns[-1],
                    color_continuous_scale='viridis'
                )
                
            elif chart_type == 'pie':
                fig = px.pie(
                    df, 
                    names=df.columns[0], 
                    values=df.columns[-1],
                    title=title
                )
                
            elif chart_type == 'line':
                fig = px.line(
                    df, 
                    x=df.columns[0], 
                    y=df.columns[1],
                    title=title,
                    markers=True
                )
                
            elif chart_type == 'scatter':
                fig = px.scatter(
                    df, 
                    x=df.columns[0], 
                    y=df.columns[1],
                    title=title,
                    size=df.columns[2] if len(df.columns) > 2 else None
                )
                
            elif chart_type == 'stacked_bar':
                # Assuming data has categories to stack
                fig = px.bar(
                    df, 
                    x=df.columns[0], 
                    y=df.columns[-1],
                    color=df.columns[1] if len(df.columns) > 2 else None,
                    title=title
                )
                
            elif chart_type == 'heatmap':
                if len(df.columns) >= 3:
                    # Pivot for heatmap
                    pivot_df = df.pivot_table(
                        index=df.columns[0], 
                        columns=df.columns[1], 
                        values=df.columns[2], 
                        aggfunc='sum'
                    ).fillna(0)
                    fig = px.imshow(pivot_df, title=title, aspect="auto")
                else:
                    fig = px.bar(df, x=df.columns[0], y=df.columns[1], title=title)
                    
            else:  # table or metric
                return {
                    "type": "table",
                    "data": df.to_dict('records'),
                    "title": title
                }
            
            # Update layout for better appearance
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12),
                title_font_size=16,
                margin=dict(l=40, r=40, t=60, b=40)
            )
            
            return {
                "type": "chart",
                "chart": json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)),
                "title": title
            }
            
        except Exception as e:
            print(f"Chart creation error: {str(e)}")
            return {
                "type": "table",
                "data": df.to_dict('records'),
                "title": title,
                "error": f"Chart error: {str(e)}"
            }
    
    def process_ai_query(self, user_query: str) -> Dict[str, Any]:
        """Process user query using AI and return results with charts"""
        try:
            # Convert natural language to SQL
            query_info = self.natural_language_to_sql(user_query)
            
            # Execute query
            df = self.execute_query(query_info['sql'])
            
            if df.empty:
                return {
                    "success": False,
                    "message": "No data found for your query",
                    "query": user_query,
                    "sql": query_info['sql']
                }
            
            # Add calculated fields
            df_enhanced = self.add_calculated_fields(df, user_query)
            
            # Create chart
            chart_result = self.create_chart(
                df_enhanced, 
                query_info['chart_type'], 
                query_info['title']
            )
            
            return {
                "success": True,
                "query": user_query,
                "sql": query_info['sql'],
                "data": df_enhanced.to_dict('records'),
                "chart": chart_result,
                "row_count": len(df_enhanced),
                "calculated_fields": [col for col in df_enhanced.columns if col not in df.columns]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": user_query
            }
    
    def get_data_insights(self) -> Dict[str, Any]:
        """Get automated insights from the data"""
        insights = []
        
        try:
            # Top selling products
            top_selling_df = self.execute_query(
                self.sql_templates['top_selling'].format(days=7, limit=5)
            )
            if not top_selling_df.empty:
                top_product = top_selling_df.iloc[0]
                insights.append({
                    "type": "success",
                    "title": "Top Performer",
                    "message": f"{top_product['product_name']} is your best seller with {top_product['total_sold']} units sold this week"
                })
            
            # Low stock alerts
            low_stock_df = self.execute_query(self.sql_templates['low_stock'])
            if not low_stock_df.empty:
                critical_count = len(low_stock_df[low_stock_df['stock_difference'] < -5])
                if critical_count > 0:
                    insights.append({
                        "type": "warning",
                        "title": "Stock Alert",
                        "message": f"{critical_count} products have critically low stock levels"
                    })
            
            # Platform performance
            platform_df = self.execute_query(
                self.sql_templates['platform_sales'].format(days=7)
            )
            if not platform_df.empty:
                best_platform = platform_df.iloc[0]
                insights.append({
                    "type": "info",
                    "title": "Platform Performance",
                    "message": f"{best_platform['platform']} is your top platform with {best_platform['total_quantity']} units sold"
                })
            
            return {"insights": insights}
            
        except Exception as e:
            return {"insights": [], "error": str(e)}
    
    def get_sample_queries(self) -> List[str]:
        """Return sample queries for user reference"""
        return self.sample_queries

# Flask app integration
def create_ai_app():
    """Create Flask app with AI data layer"""
    app = Flask(__name__)
    app.secret_key = 'ai_wms_secret_key'
    
    # Initialize AI data layer
    ai_layer = AIDataLayer()
    
    @app.route('/')
    def ai_dashboard():
        """AI-powered dashboard"""
        return render_template('ai_dashboard.html')
    
    @app.route('/api/ai-query', methods=['POST'])
    def process_ai_query():
        """Process AI query endpoint"""
        data = request.json
        user_query = data.get('query', '')
        
        if not user_query:
            return jsonify({"success": False, "error": "No query provided"})
        
        result = ai_layer.process_ai_query(user_query)
        return jsonify(result)
    
    @app.route('/api/insights')
    def get_insights():
        """Get automated insights"""
        insights = ai_layer.get_data_insights()
        return jsonify(insights)
    
    @app.route('/api/sample-queries')
    def get_sample_queries():
        """Get sample queries"""
        return jsonify({"queries": ai_layer.get_sample_queries()})
    
    @app.route('/api/database-stats')
    def get_database_stats():
        """Get database statistics"""
        try:
            stats = {}
            cursor = ai_layer.conn.cursor()
            
            # Get table counts
            tables = ['products', 'sales_records', 'sku_mappings', 'inventory_movements']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Get date range of sales
            cursor.execute("SELECT MIN(sale_date), MAX(sale_date) FROM sales_records")
            date_range = cursor.fetchone()
            stats['sales_date_range'] = {
                'start': date_range[0],
                'end': date_range[1]
            }
            
            return jsonify({"success": True, "stats": stats})
            
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    
    return app, ai_layer

if __name__ == "__main__":
    app, ai_layer = create_ai_app()
    
    print("🤖 AI Data Layer initialized!")
    print("📊 Features available:")
    print("   - Natural Language to SQL")
    print("   - Calculated Fields")
    print("   - Interactive Charts")
    print("   - Automated Insights")
    print("   - Sample Queries for Testing")
    print("\n🚀 Starting AI WMS Server...")
    print("🌐 Access at: http://localhost:5001")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
