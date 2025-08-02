"""
Part 3: Integration and Finalization - Web Application
Combines Part 1 (SKU Mapping) + Part 2 (Inventory Automation) into a unified web interface
Uses Flask for backend and modern HTML/CSS/JS for frontend
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
import pandas as pd
import os
import json
from datetime import datetime
import threading
import time
from werkzeug.utils import secure_filename
import plotly.graph_objs as go
import plotly.utils

app = Flask(__name__)
app.secret_key = 'wms_automation_secret_key_2025'

# Configuration
UPLOAD_FOLDER = 'uploads'
REPORTS_FOLDER = 'reports'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

class WMSProcessor:
    def __init__(self):
        self.mapping_data = None
        self.combo_data = None
        self.current_inventory = None
        self.combo_mapping = {}
        self.load_wms_data()
        
    def load_wms_data(self):
        """Load all WMS data from Excel file"""
        try:
            # Load SKU-MSKU mapping
            self.mapping_data = pd.read_excel('WMS-04-02.xlsx', sheet_name='Msku With Skus')
            
            # Load combo data
            self.combo_data = pd.read_excel('WMS-04-02.xlsx', sheet_name='Combos skus')
            
            # Load current inventory - fix header issue
            self.current_inventory = pd.read_excel('WMS-04-02.xlsx', sheet_name='Current Inventory ')
            
            # Fix inventory headers - the headers are in the first row of data
            if self.current_inventory is not None and len(self.current_inventory) > 0:
                # Use first row as headers
                first_row = self.current_inventory.iloc[0]
                new_columns = []
                for val in first_row.values:
                    if pd.notna(val) and str(val).strip():
                        new_columns.append(str(val).strip())
                    else:
                        new_columns.append('Unknown_Column')
                
                # Set new columns and remove the header row
                self.current_inventory.columns = new_columns
                self.current_inventory = self.current_inventory.drop(0).reset_index(drop=True)
                
                # Convert numeric columns to proper types
                for col in self.current_inventory.columns:
                    if col not in ['Product Name', 'msku']:
                        self.current_inventory[col] = pd.to_numeric(self.current_inventory[col], errors='coerce').fillna(0)
                
                print(f"✅ Fixed inventory headers: {list(self.current_inventory.columns)[:5]}")
                print(f"✅ Inventory data shape: {self.current_inventory.shape}")
            
            # Create combo mapping
            self.combo_mapping = self.create_combo_mapping()
            
            return True
        except Exception as e:
            print(f"Error loading WMS data: {str(e)}")
            return False
    
    def create_combo_mapping(self):
        """Create combo mapping dictionary"""
        combo_map = {}
        for _, row in self.combo_data.iterrows():
            combo_sku = row['Combo ']
            if pd.notna(combo_sku):
                components = []
                for i in range(1, 15):
                    sku_col = f'SKU{i}'
                    if sku_col in row and pd.notna(row[sku_col]):
                        components.append(row[sku_col])
                if components:
                    combo_map[combo_sku] = components
        return combo_map
    
    def detect_platform(self, columns):
        """Detect platform based on column names"""
        columns_str = ' '.join(columns).upper()
        if 'FNSKU' in columns_str or 'FULFILLMENT CENTER' in columns_str:
            return 'Amazon'
        elif 'ORDER ITEM ID' in columns_str or 'FSN' in columns_str:
            return 'Flipkart'
        elif 'SUB ORDER NO' in columns_str:
            return 'Meesho'
        else:
            return 'Unknown'
    
    def get_sku_column(self, columns, platform):
        """Get the appropriate SKU column for the platform"""
        if platform == 'Amazon':
            if 'FNSKU' in columns:
                return 'FNSKU'
            elif 'MSKU' in columns:
                return 'MSKU'
        elif platform in ['Flipkart', 'Meesho']:
            if 'SKU' in columns:
                return 'SKU'
        return None
    
    def map_sku_to_msku(self, sku):
        """Map SKU to MSKU, handling combos"""
        # Check if it's a combo first
        if sku in self.combo_mapping:
            return {'type': 'combo', 'components': self.combo_mapping[sku]}
        
        # Regular SKU mapping
        result = self.mapping_data[self.mapping_data['sku'] == sku]
        if not result.empty:
            return {'type': 'single', 'msku': result.iloc[0]['msku']}
        else:
            return {'type': 'not_found', 'msku': 'Mapping Not Found'}
    
    def process_sales_file(self, file_path):
        """Process a single sales file"""
        try:
            df = pd.read_csv(file_path)
            platform = self.detect_platform(df.columns.tolist())
            
            # Get SKU column
            sku_column = self.get_sku_column(df.columns.tolist(), platform)
            if not sku_column:
                return None, {}, f"No SKU column found for platform {platform}"
            
            processed_rows = []
            inventory_changes = {}
            
            for _, row in df.iterrows():
                sku = row[sku_column]
                quantity = row.get('Quantity', 1)
                
                if pd.isna(sku) or quantity <= 0:
                    continue
                
                # Filter Amazon records
                if platform == 'Amazon':
                    if row.get('Event Type') != 'Shipments' or row.get('Disposition') != 'SELLABLE':
                        continue
                
                mapping_result = self.map_sku_to_msku(sku)
                
                if mapping_result['type'] == 'combo':
                    # Handle combo product
                    for component_msku in mapping_result['components']:
                        combo_row = row.copy()
                        combo_row['Original_SKU'] = sku
                        combo_row['MSKU'] = component_msku
                        combo_row['Quantity'] = quantity
                        combo_row['Product_Type'] = 'Combo_Component'
                        combo_row['Platform'] = platform
                        processed_rows.append(combo_row)
                        
                        # Track inventory changes
                        if component_msku in inventory_changes:
                            inventory_changes[component_msku] += quantity
                        else:
                            inventory_changes[component_msku] = quantity
                            
                elif mapping_result['type'] == 'single':
                    # Handle single product
                    new_row = row.copy()
                    new_row['MSKU'] = mapping_result['msku']
                    new_row['Product_Type'] = 'Single'
                    new_row['Platform'] = platform
                    processed_rows.append(new_row)
                    
                    # Track inventory changes
                    msku = mapping_result['msku']
                    if msku in inventory_changes:
                        inventory_changes[msku] += quantity
                    else:
                        inventory_changes[msku] = quantity
                        
                else:
                    # Not found
                    new_row = row.copy()
                    new_row['MSKU'] = 'Mapping Not Found'
                    new_row['Product_Type'] = 'Unknown'
                    new_row['Platform'] = platform
                    processed_rows.append(new_row)
            
            return pd.DataFrame(processed_rows), inventory_changes, None
            
        except Exception as e:
            return None, {}, str(e)
    
    def update_inventory(self, inventory_changes):
        """Update inventory based on sales"""
        if not inventory_changes:
            return {"status": "warning", "message": "No inventory changes to apply"}
        
        # Find MSKU and quantity columns using actual column names
        msku_column = 'msku' if 'msku' in self.current_inventory.columns else None
        quantity_column = 'Opening Stock' if 'Opening Stock' in self.current_inventory.columns else None
        
        # If exact matches not found, search for similar columns
        if not msku_column:
            for col in self.current_inventory.columns:
                if isinstance(col, str) and 'msku' in col.lower():
                    msku_column = col
                    break
        
        if not quantity_column:
            for col in self.current_inventory.columns:
                if isinstance(col, str) and any(word in col.lower() for word in ['stock', 'quantity', 'qty']):
                    quantity_column = col
                    break
        
        if not msku_column or not quantity_column:
            return {"status": "error", "message": "Could not find MSKU or quantity columns"}
        
        updated_items = 0
        warnings = []
        
        for msku, quantity_sold in inventory_changes.items():
            mask = self.current_inventory[msku_column] == msku
            if mask.any():
                current_qty = self.current_inventory.loc[mask, quantity_column].iloc[0]
                new_qty = current_qty - quantity_sold
                
                self.current_inventory.loc[mask, quantity_column] = new_qty
                updated_items += 1
                
                if new_qty < 0:
                    warnings.append(f"{msku}: Negative stock ({new_qty})")
                elif new_qty < 5:
                    warnings.append(f"{msku}: Low stock ({new_qty})")
            else:
                warnings.append(f"MSKU not found: {msku}")
        
        return {
            "status": "success",
            "message": f"Updated {updated_items} inventory items",
            "warnings": warnings,
            "updated_items": updated_items
        }
    
    def get_dashboard_data(self):
        """Get data for dashboard visualization"""
        try:
            # Basic statistics
            total_products = len(self.current_inventory) if self.current_inventory is not None else 0
            total_combos = len(self.combo_mapping)
            total_mappings = len(self.mapping_data) if self.mapping_data is not None else 0
            
            # Low stock analysis
            low_stock_count = 0
            negative_stock_count = 0
            
            if self.current_inventory is not None:
                # Look for quantity columns - check for Opening Stock column specifically
                quantity_col = None
                if 'Opening Stock' in self.current_inventory.columns:
                    quantity_col = 'Opening Stock'
                else:
                    # Look for other stock/quantity columns
                    for col in self.current_inventory.columns:
                        if isinstance(col, str):
                            col_lower = col.lower()
                            if any(word in col_lower for word in ['stock', 'quantity', 'qty']):
                                quantity_col = col
                                break
                
                if quantity_col is not None:
                    # Ensure column is numeric
                    self.current_inventory[quantity_col] = pd.to_numeric(self.current_inventory[quantity_col], errors='coerce').fillna(0)
                    
                    # Calculate stock statistics
                    stock_values = self.current_inventory[quantity_col]
                    low_stock_count = len(stock_values[stock_values < 10])
                    negative_stock_count = len(stock_values[stock_values < 0])
                else:
                    print("Warning: No stock column found in inventory data")
            
            return {
                "total_products": total_products,
                "total_combos": total_combos,
                "total_mappings": total_mappings,
                "low_stock_count": low_stock_count,
                "negative_stock_count": negative_stock_count
            }
        except Exception as e:
            print(f"Error getting dashboard data: {str(e)}")
            return {
                "total_products": 0,
                "total_combos": 0,
                "total_mappings": 0,
                "low_stock_count": 0,
                "negative_stock_count": 0
            }
        except Exception as e:
            return {"error": str(e)}

# Global processor instance
wms_processor = WMSProcessor()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def dashboard():
    """Main dashboard page"""
    dashboard_data = wms_processor.get_dashboard_data()
    return render_template('dashboard.html', data=dashboard_data)

@app.route('/upload')
def upload_page():
    """File upload page"""
    return render_template('upload.html')

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    if 'files' not in request.files:
        return jsonify({"status": "error", "message": "No files uploaded"})
    
    files = request.files.getlist('files')
    uploaded_files = []
    
    for file in files:
        if file.filename == '':
            continue
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            uploaded_files.append({"name": filename, "path": filepath})
    
    return jsonify({
        "status": "success", 
        "message": f"Uploaded {len(uploaded_files)} files",
        "files": uploaded_files
    })

@app.route('/api/process', methods=['POST'])
def process_files():
    """Process uploaded files"""
    data = request.json
    file_paths = data.get('files', [])
    
    if not file_paths:
        return jsonify({"status": "error", "message": "No files to process"})
    
    results = []
    total_inventory_changes = {}
    
    for file_info in file_paths:
        file_path = file_info['path']
        processed_df, inventory_changes, error = wms_processor.process_sales_file(file_path)
        
        if error:
            results.append({
                "file": file_info['name'],
                "status": "error",
                "message": error
            })
            continue
        
        if processed_df is not None and not processed_df.empty:
            # Save processed file
            output_filename = f"processed_{file_info['name']}"
            output_path = os.path.join(REPORTS_FOLDER, output_filename)
            processed_df.to_csv(output_path, index=False)
            
            # Combine inventory changes
            for msku, qty in inventory_changes.items():
                if msku in total_inventory_changes:
                    total_inventory_changes[msku] += qty
                else:
                    total_inventory_changes[msku] = qty
            
            results.append({
                "file": file_info['name'],
                "status": "success",
                "processed_rows": len(processed_df),
                "inventory_changes": len(inventory_changes),
                "output_file": output_filename
            })
        else:
            results.append({
                "file": file_info['name'],
                "status": "error",
                "message": "No data processed"
            })
    
    # Update inventory
    inventory_result = wms_processor.update_inventory(total_inventory_changes)
    
    return jsonify({
        "status": "success",
        "file_results": results,
        "inventory_update": inventory_result,
        "total_changes": len(total_inventory_changes)
    })

@app.route('/api/dashboard-data')
def get_dashboard_data():
    """Get dashboard data for visualization"""
    try:
        dashboard_data = wms_processor.get_dashboard_data()
        
        # Create charts data
        charts_data = {}
        
        if wms_processor.current_inventory is not None:
            # Find stock column - prioritize Opening Stock
            inventory_df = wms_processor.current_inventory.copy()
            qty_col = None
            
            if 'Opening Stock' in inventory_df.columns:
                qty_col = 'Opening Stock'
            else:
                # Look for other stock columns
                for col in inventory_df.columns:
                    if isinstance(col, str) and any(word in col.lower() for word in ['stock', 'quantity', 'qty']):
                        qty_col = col
                        break
            
            if qty_col is not None:
                # Convert to numeric and clean data
                inventory_df[qty_col] = pd.to_numeric(inventory_df[qty_col], errors='coerce').fillna(0)
                
                # Stock categories for chart
                categories = ['Negative Stock', 'Low Stock (1-9)', 'Normal Stock (10-99)', 'High Stock (100+)']
                counts = [
                    len(inventory_df[inventory_df[qty_col] < 0]),
                    len(inventory_df[(inventory_df[qty_col] >= 1) & (inventory_df[qty_col] <= 9)]),
                    len(inventory_df[(inventory_df[qty_col] >= 10) & (inventory_df[qty_col] <= 99)]),
                    len(inventory_df[inventory_df[qty_col] >= 100])
                ]
                
                charts_data['stock_distribution'] = {
                    'labels': categories,
                    'values': counts
                }
        
        dashboard_data['charts'] = charts_data
        return jsonify(dashboard_data)
    except Exception as e:
        print(f"Error in dashboard data: {str(e)}")
        return jsonify({
            "total_products": 0,
            "total_combos": 0,
            "total_mappings": 0,
            "low_stock_count": 0,
            "negative_stock_count": 0,
            "charts": {}
        })

@app.route('/inventory')
def inventory_page():
    """Inventory management page"""
    return render_template('inventory.html')

@app.route('/api/inventory')
def get_inventory():
    """Get current inventory data"""
    try:
        if wms_processor.current_inventory is None:
            return jsonify({"status": "error", "message": "No inventory data available"})
        
        # Get a copy of the inventory data
        inventory_df = wms_processor.current_inventory.copy()
        
        # Clean and prepare data
        if len(inventory_df) > 0:
            # Convert any numeric columns to proper numbers
            for col in inventory_df.columns:
                if col not in ['Product Name', 'msku']:  # Keep text columns as text
                    inventory_df[col] = pd.to_numeric(inventory_df[col], errors='coerce').fillna(0)
        
        # Convert to dict for JSON serialization (limit for performance)
        inventory_data = inventory_df.head(500).to_dict('records')
        
        return jsonify({
            "status": "success",
            "data": inventory_data,
            "total_records": len(inventory_df),
            "columns": list(inventory_df.columns)
        })
    except Exception as e:
        print(f"Error in get_inventory: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to load inventory: {str(e)}"})

@app.route('/reports')
def reports_page():
    """Reports page"""
    # Get list of generated reports
    reports = []
    if os.path.exists(REPORTS_FOLDER):
        for filename in os.listdir(REPORTS_FOLDER):
            if filename.endswith('.csv'):
                file_path = os.path.join(REPORTS_FOLDER, filename)
                file_stats = os.stat(file_path)
                reports.append({
                    'name': filename,
                    'size': file_stats.st_size,
                    'modified': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    return render_template('reports.html', reports=reports)

@app.route('/api/export-inventory')
def export_inventory():
    """Export current inventory"""
    if wms_processor.current_inventory is None:
        return jsonify({"status": "error", "message": "No inventory data available"})
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"inventory_export_{timestamp}.csv"
    filepath = os.path.join(REPORTS_FOLDER, filename)
    
    wms_processor.current_inventory.to_csv(filepath, index=False)
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/api/combo-analysis')
def combo_analysis():
    """Get combo products analysis"""
    combo_data = []
    for combo_sku, components in wms_processor.combo_mapping.items():
        combo_data.append({
            'combo_sku': combo_sku,
            'components': components,
            'component_count': len(components)
        })
    
    return jsonify({
        "status": "success",
        "total_combos": len(combo_data),
        "combo_data": combo_data[:50]  # Limit for performance
    })

if __name__ == '__main__':
    print("🚀 Starting WMS Web Application...")
    print("📊 Dashboard: http://localhost:5000")
    print("📁 Upload: http://localhost:5000/upload")
    print("📦 Inventory: http://localhost:5000/inventory")
    print("📈 Reports: http://localhost:5000/reports")
    app.run(debug=True, host='0.0.0.0', port=5000)
