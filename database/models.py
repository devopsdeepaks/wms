"""
Database Models for WMS System
SQLAlchemy models for relational database integration
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class Product(db.Model):
    """Products table - Master product information"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    msku = Column(String(100), unique=True, nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    opening_stock = Column(Integer, default=0)
    current_stock = Column(Integer, default=0)
    buffer_stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sku_mappings = relationship("SKUMapping", back_populates="product")
    combo_components = relationship("ComboComponent", back_populates="product")
    inventory_movements = relationship("InventoryMovement", back_populates="product")
    sales_records = relationship("SalesRecord", back_populates="product")
    
    def __repr__(self):
        return f'<Product {self.msku}: {self.product_name}>'

class SKUMapping(db.Model):
    """SKU to MSKU mapping table"""
    __tablename__ = 'sku_mappings'
    
    id = Column(Integer, primary_key=True)
    sku = Column(String(100), nullable=False, index=True)
    msku = Column(String(100), ForeignKey('products.msku'), nullable=False)
    platform = Column(String(50), nullable=False)  # Amazon, Flipkart, Meesho
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="sku_mappings")
    
    def __repr__(self):
        return f'<SKUMapping {self.sku} -> {self.msku}>'

class ComboProduct(db.Model):
    """Combo products table"""
    __tablename__ = 'combo_products'
    
    id = Column(Integer, primary_key=True)
    combo_sku = Column(String(100), unique=True, nullable=False, index=True)
    combo_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    components = relationship("ComboComponent", back_populates="combo")
    
    def __repr__(self):
        return f'<ComboProduct {self.combo_sku}: {self.combo_name}>'

class ComboComponent(db.Model):
    """Combo components table - which products are in each combo"""
    __tablename__ = 'combo_components'
    
    id = Column(Integer, primary_key=True)
    combo_id = Column(Integer, ForeignKey('combo_products.id'), nullable=False)
    product_msku = Column(String(100), ForeignKey('products.msku'), nullable=False)
    quantity = Column(Integer, default=1)  # How many of this component in the combo
    
    # Relationships
    combo = relationship("ComboProduct", back_populates="components")
    product = relationship("Product", back_populates="combo_components")
    
    def __repr__(self):
        return f'<ComboComponent {self.combo_id} -> {self.product_msku}>'

class SalesRecord(db.Model):
    """Sales records table - all sales transactions"""
    __tablename__ = 'sales_records'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String(100), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # Amazon, Flipkart, Meesho
    original_sku = Column(String(100), nullable=False)
    msku = Column(String(100), ForeignKey('products.msku'), nullable=False)
    quantity = Column(Integer, nullable=False)
    sale_date = Column(DateTime, nullable=False)
    product_type = Column(String(50), nullable=False)  # Single, Combo_Component, Unknown
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional fields from sales files
    customer_state = Column(String(100))
    fulfillment_center = Column(String(100))
    event_type = Column(String(100))
    disposition = Column(String(100))
    
    # Relationships
    product = relationship("Product", back_populates="sales_records")
    
    def __repr__(self):
        return f'<SalesRecord {self.order_id}: {self.msku} x{self.quantity}>'

class InventoryMovement(db.Model):
    """Inventory movements table - track all stock changes"""
    __tablename__ = 'inventory_movements'
    
    id = Column(Integer, primary_key=True)
    msku = Column(String(100), ForeignKey('products.msku'), nullable=False)
    movement_type = Column(String(50), nullable=False)  # Sale, Adjustment, Restock
    quantity_change = Column(Integer, nullable=False)  # Positive for increase, negative for decrease
    stock_before = Column(Integer, nullable=False)
    stock_after = Column(Integer, nullable=False)
    reference_id = Column(String(100))  # Could be order_id, batch_id, etc.
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="inventory_movements")
    
    def __repr__(self):
        return f'<InventoryMovement {self.msku}: {self.quantity_change}>'

class ProcessingLog(db.Model):
    """Processing logs table - audit trail"""
    __tablename__ = 'processing_logs'
    
    id = Column(Integer, primary_key=True)
    batch_id = Column(String(100), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)
    total_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    processing_time = Column(Float)  # seconds
    status = Column(String(50), nullable=False)  # Success, Failed, Partial
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProcessingLog {self.batch_id}: {self.file_name}>'

class DatabaseConfig:
    """Database configuration constants"""
    
    # SQLite for development (file-based)
    SQLITE_DATABASE_URI = 'sqlite:///wms_database.db'
    
    # PostgreSQL for production (uncomment and configure as needed)
    # POSTGRESQL_DATABASE_URI = 'postgresql://username:password@localhost:5432/wms_db'
    
    # MySQL for production (uncomment and configure as needed)  
    # MYSQL_DATABASE_URI = 'mysql://username:password@localhost:3306/wms_db'

def init_database(app):
    """Initialize database with Flask app"""
    app.config['SQLALCHEMY_DATABASE_URI'] = DatabaseConfig.SQLITE_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
    return db
