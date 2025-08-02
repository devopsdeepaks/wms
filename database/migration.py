"""
Database Migration Utility
Migrate data from Excel to relational database
"""

import pandas as pd
from datetime import datetime
import os
import sys

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db, Product, SKUMapping, ComboProduct, ComboComponent

class DatabaseMigration:
    """Handles migration from Excel to database"""
    
    def __init__(self, app):
        self.app = app
        
    def migrate_from_excel(self, excel_file_path='WMS-04-02.xlsx'):
        """Main migration function"""
        with self.app.app_context():
            try:
                print("🚀 Starting database migration from Excel...")
                
                # Step 1: Load Excel data
                excel_data = self.load_excel_data(excel_file_path)
                
                # Step 2: Migrate products
                self.migrate_products(excel_data['inventory'])
                
                # Step 3: Migrate SKU mappings
                self.migrate_sku_mappings(excel_data['mappings'])
                
                # Step 4: Migrate combo products
                self.migrate_combo_products(excel_data['combos'])
                
                print("✅ Database migration completed successfully!")
                self.print_migration_summary()
                
            except Exception as e:
                print(f"❌ Migration failed: {str(e)}")
                db.session.rollback()
                raise
    
    def load_excel_data(self, excel_file_path):
        """Load data from Excel file"""
        print("📊 Loading Excel data...")
        
        try:
            # Load inventory data
            inventory_df = pd.read_excel(excel_file_path, sheet_name='Current Inventory ')
            
            # Fix headers (as in your working code)
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
                
                # Convert numeric columns
                for col in inventory_df.columns:
                    if col not in ['Product Name', 'msku']:
                        inventory_df[col] = pd.to_numeric(inventory_df[col], errors='coerce').fillna(0)
            
            # Load SKU mappings
            mappings_df = pd.read_excel(excel_file_path, sheet_name='Msku With Skus')
            
            # Load combo data
            combos_df = pd.read_excel(excel_file_path, sheet_name='Combos skus')
            
            print(f"✅ Loaded: {len(inventory_df)} products, {len(mappings_df)} mappings, {len(combos_df)} combos")
            
            return {
                'inventory': inventory_df,
                'mappings': mappings_df,
                'combos': combos_df
            }
            
        except Exception as e:
            print(f"❌ Error loading Excel data: {str(e)}")
            raise
    
    def migrate_products(self, inventory_df):
        """Migrate products from inventory sheet"""
        print("📦 Migrating products...")
        
        migrated_count = 0
        
        for _, row in inventory_df.iterrows():
            try:
                product_name = row.get('Product Name', 'Unknown Product')
                msku = row.get('msku', '')
                opening_stock = int(row.get('Opening Stock', 0))
                buffer_stock = int(row.get('Buffer Stock', 0))
                
                if not msku or pd.isna(msku):
                    continue
                
                # Check if product already exists
                existing_product = Product.query.filter_by(msku=msku).first()
                if existing_product:
                    # Update existing product
                    existing_product.product_name = product_name
                    existing_product.opening_stock = opening_stock
                    existing_product.current_stock = opening_stock
                    existing_product.buffer_stock = buffer_stock
                    existing_product.updated_at = datetime.utcnow()
                else:
                    # Create new product
                    product = Product(
                        msku=msku,
                        product_name=product_name,
                        opening_stock=opening_stock,
                        current_stock=opening_stock,
                        buffer_stock=buffer_stock
                    )
                    db.session.add(product)
                
                migrated_count += 1
                
                if migrated_count % 100 == 0:
                    print(f"   📦 Migrated {migrated_count} products...")
                    
            except Exception as e:
                print(f"   ⚠️ Error migrating product {row.get('msku', 'Unknown')}: {str(e)}")
                continue
        
        db.session.commit()
        print(f"✅ Migrated {migrated_count} products")
    
    def migrate_sku_mappings(self, mappings_df):
        """Migrate SKU mappings"""
        print("🔗 Migrating SKU mappings...")
        
        migrated_count = 0
        
        for _, row in mappings_df.iterrows():
            try:
                sku = row.get('sku', '')
                msku = row.get('msku', '')
                
                if not sku or not msku or pd.isna(sku) or pd.isna(msku):
                    continue
                
                # Detect platform based on SKU format
                platform = self.detect_platform_from_sku(sku)
                
                # Check if mapping already exists
                existing_mapping = SKUMapping.query.filter_by(sku=sku, msku=msku).first()
                if not existing_mapping:
                    mapping = SKUMapping(
                        sku=sku,
                        msku=msku,
                        platform=platform
                    )
                    db.session.add(mapping)
                    migrated_count += 1
                
                if migrated_count % 100 == 0:
                    print(f"   🔗 Migrated {migrated_count} mappings...")
                    
            except Exception as e:
                print(f"   ⚠️ Error migrating mapping {row.get('sku', 'Unknown')}: {str(e)}")
                continue
        
        db.session.commit()
        print(f"✅ Migrated {migrated_count} SKU mappings")
    
    def migrate_combo_products(self, combos_df):
        """Migrate combo products and their components"""
        print("🎁 Migrating combo products...")
        
        migrated_combos = 0
        migrated_components = 0
        
        for _, row in combos_df.iterrows():
            try:
                combo_sku = row.get('Combo ', '')
                if not combo_sku or pd.isna(combo_sku):
                    continue
                
                # Create combo product
                existing_combo = ComboProduct.query.filter_by(combo_sku=combo_sku).first()
                if not existing_combo:
                    combo_product = ComboProduct(
                        combo_sku=combo_sku,
                        combo_name=f"Combo - {combo_sku}"
                    )
                    db.session.add(combo_product)
                    db.session.flush()  # Get the ID
                    combo_id = combo_product.id
                    migrated_combos += 1
                else:
                    combo_id = existing_combo.id
                
                # Add components
                for i in range(1, 15):  # SKU1 to SKU14
                    sku_col = f'SKU{i}'
                    if sku_col in row and pd.notna(row[sku_col]):
                        component_sku = row[sku_col]
                        
                        # Find the MSKU for this component SKU
                        sku_mapping = SKUMapping.query.filter_by(sku=component_sku).first()
                        if sku_mapping:
                            # Check if component already exists
                            existing_component = ComboComponent.query.filter_by(
                                combo_id=combo_id, 
                                product_msku=sku_mapping.msku
                            ).first()
                            
                            if not existing_component:
                                component = ComboComponent(
                                    combo_id=combo_id,
                                    product_msku=sku_mapping.msku,
                                    quantity=1
                                )
                                db.session.add(component)
                                migrated_components += 1
                
                if migrated_combos % 10 == 0:
                    print(f"   🎁 Migrated {migrated_combos} combos...")
                    
            except Exception as e:
                print(f"   ⚠️ Error migrating combo {row.get('Combo ', 'Unknown')}: {str(e)}")
                continue
        
        db.session.commit()
        print(f"✅ Migrated {migrated_combos} combo products with {migrated_components} components")
    
    def detect_platform_from_sku(self, sku):
        """Detect platform based on SKU format"""
        sku_str = str(sku).upper()
        if 'FNSKU' in sku_str or len(sku_str) == 10:
            return 'Amazon'
        elif 'FSN' in sku_str:
            return 'Flipkart'
        elif 'MEESHO' in sku_str:
            return 'Meesho'
        else:
            return 'Unknown'
    
    def print_migration_summary(self):
        """Print migration summary"""
        print("\n📊 Migration Summary:")
        print(f"   Products: {Product.query.count()}")
        print(f"   SKU Mappings: {SKUMapping.query.count()}")
        print(f"   Combo Products: {ComboProduct.query.count()}")
        print(f"   Combo Components: {ComboComponent.query.count()}")

def run_migration():
    """Standalone migration runner"""
    from flask import Flask
    from database.models import init_database
    
    # Create Flask app for migration
    app = Flask(__name__)
    db_instance = init_database(app)
    
    # Run migration
    migration = DatabaseMigration(app)
    migration.migrate_from_excel()

if __name__ == '__main__':
    run_migration()
