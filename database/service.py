"""
Database Service Layer
Handles all database operations for WMS system
"""

from datetime import datetime
from sqlalchemy import func, desc
from database.models import db, Product, SKUMapping, ComboProduct, ComboComponent, SalesRecord, InventoryMovement, ProcessingLog

class DatabaseService:
    """Service layer for database operations"""
    
    @staticmethod
    def get_product_by_msku(msku):
        """Get product by MSKU"""
        return Product.query.filter_by(msku=msku).first()
    
    @staticmethod
    def get_all_products(limit=None, offset=None):
        """Get all products with optional pagination"""
        query = Product.query.order_by(Product.product_name)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        return query.all()
    
    @staticmethod
    def search_products(search_term, limit=100):
        """Search products by name or MSKU"""
        return Product.query.filter(
            (Product.product_name.ilike(f'%{search_term}%')) |
            (Product.msku.ilike(f'%{search_term}%'))
        ).limit(limit).all()
    
    @staticmethod
    def get_low_stock_products(threshold=10):
        """Get products with low stock"""
        return Product.query.filter(Product.current_stock < threshold).all()
    
    @staticmethod
    def get_negative_stock_products():
        """Get products with negative stock"""
        return Product.query.filter(Product.current_stock < 0).all()
    
    @staticmethod
    def map_sku_to_msku(sku):
        """Map SKU to MSKU using database"""
        mapping = SKUMapping.query.filter_by(sku=sku).first()
        if mapping:
            return mapping.msku
        return None
    
    @staticmethod
    def get_combo_components(combo_sku):
        """Get components of a combo product"""
        combo = ComboProduct.query.filter_by(combo_sku=combo_sku).first()
        if combo:
            components = ComboComponent.query.filter_by(combo_id=combo.id).all()
            return [(comp.product_msku, comp.quantity) for comp in components]
        return []
    
    @staticmethod
    def is_combo_product(sku):
        """Check if SKU is a combo product"""
        return ComboProduct.query.filter_by(combo_sku=sku).first() is not None
    
    @staticmethod
    def record_sale(order_id, platform, original_sku, msku, quantity, sale_date, product_type, **kwargs):
        """Record a sales transaction"""
        try:
            sales_record = SalesRecord(
                order_id=order_id,
                platform=platform,
                original_sku=original_sku,
                msku=msku,
                quantity=quantity,
                sale_date=sale_date,
                product_type=product_type,
                customer_state=kwargs.get('customer_state'),
                fulfillment_center=kwargs.get('fulfillment_center'),
                event_type=kwargs.get('event_type'),
                disposition=kwargs.get('disposition')
            )
            db.session.add(sales_record)
            return sales_record
        except Exception as e:
            print(f"Error recording sale: {str(e)}")
            return None
    
    @staticmethod
    def update_inventory(msku, quantity_change, movement_type='Sale', reference_id=None, notes=None):
        """Update inventory and record movement"""
        try:
            product = Product.query.filter_by(msku=msku).first()
            if not product:
                return False, f"Product {msku} not found"
            
            stock_before = product.current_stock
            stock_after = stock_before + quantity_change  # quantity_change is negative for sales
            
            # Update product stock
            product.current_stock = stock_after
            product.updated_at = datetime.utcnow()
            
            # Record inventory movement
            movement = InventoryMovement(
                msku=msku,
                movement_type=movement_type,
                quantity_change=quantity_change,
                stock_before=stock_before,
                stock_after=stock_after,
                reference_id=reference_id,
                notes=notes
            )
            db.session.add(movement)
            
            return True, f"Updated {msku}: {stock_before} -> {stock_after}"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating inventory: {str(e)}"
    
    @staticmethod
    def process_sales_file_to_db(processed_df, file_name, platform):
        """Process sales data and save to database"""
        try:
            batch_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"
            total_records = len(processed_df)
            successful_records = 0
            failed_records = 0
            start_time = datetime.now()
            
            inventory_changes = {}
            
            for _, row in processed_df.iterrows():
                try:
                    # Record the sale
                    sales_record = DatabaseService.record_sale(
                        order_id=row.get('Order ID', f"ORDER_{datetime.now().timestamp()}"),
                        platform=platform,
                        original_sku=row.get('Original_SKU', row.get('SKU', '')),
                        msku=row.get('MSKU', ''),
                        quantity=int(row.get('Quantity', 1)),
                        sale_date=row.get('Sale Date', datetime.now()),
                        product_type=row.get('Product_Type', 'Single'),
                        customer_state=row.get('Customer State'),
                        fulfillment_center=row.get('Fulfillment Center'),
                        event_type=row.get('Event Type'),
                        disposition=row.get('Disposition')
                    )
                    
                    if sales_record:
                        # Track inventory changes
                        msku = row.get('MSKU', '')
                        quantity = int(row.get('Quantity', 1))
                        
                        if msku in inventory_changes:
                            inventory_changes[msku] += quantity
                        else:
                            inventory_changes[msku] = quantity
                        
                        successful_records += 1
                    else:
                        failed_records += 1
                        
                except Exception as e:
                    print(f"Error processing row: {str(e)}")
                    failed_records += 1
                    continue
            
            # Apply inventory changes
            for msku, total_quantity in inventory_changes.items():
                success, message = DatabaseService.update_inventory(
                    msku=msku,
                    quantity_change=-total_quantity,  # Negative because it's a sale
                    movement_type='Sale',
                    reference_id=batch_id,
                    notes=f"Sales from {file_name}"
                )
                if not success:
                    print(f"Warning: {message}")
            
            # Record processing log
            processing_time = (datetime.now() - start_time).total_seconds()
            status = "Success" if failed_records == 0 else ("Partial" if successful_records > 0 else "Failed")
            
            log = ProcessingLog(
                batch_id=batch_id,
                file_name=file_name,
                platform=platform,
                total_records=total_records,
                successful_records=successful_records,
                failed_records=failed_records,
                processing_time=processing_time,
                status=status
            )
            db.session.add(log)
            
            db.session.commit()
            
            return {
                "status": "success",
                "batch_id": batch_id,
                "total_records": total_records,
                "successful_records": successful_records,
                "failed_records": failed_records,
                "processing_time": processing_time,
                "inventory_changes": len(inventory_changes)
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def get_dashboard_stats():
        """Get dashboard statistics from database"""
        try:
            stats = {
                "total_products": Product.query.count(),
                "total_combos": ComboProduct.query.count(),
                "total_mappings": SKUMapping.query.count(),
                "low_stock_count": Product.query.filter(Product.current_stock < 10).count(),
                "negative_stock_count": Product.query.filter(Product.current_stock < 0).count(),
                "total_sales_records": SalesRecord.query.count()
            }
            
            # Stock distribution for charts
            stock_distribution = {
                "negative": Product.query.filter(Product.current_stock < 0).count(),
                "low": Product.query.filter(Product.current_stock.between(1, 9)).count(),
                "normal": Product.query.filter(Product.current_stock.between(10, 99)).count(),
                "high": Product.query.filter(Product.current_stock >= 100).count()
            }
            
            stats["stock_distribution"] = stock_distribution
            return stats
            
        except Exception as e:
            print(f"Error getting dashboard stats: {str(e)}")
            return {
                "total_products": 0,
                "total_combos": 0,
                "total_mappings": 0,
                "low_stock_count": 0,
                "negative_stock_count": 0,
                "total_sales_records": 0,
                "stock_distribution": {"negative": 0, "low": 0, "normal": 0, "high": 0}
            }
    
    @staticmethod
    def get_recent_sales(limit=100):
        """Get recent sales records"""
        return SalesRecord.query.order_by(desc(SalesRecord.processed_at)).limit(limit).all()
    
    @staticmethod
    def get_inventory_movements(msku=None, limit=100):
        """Get inventory movements"""
        query = InventoryMovement.query.order_by(desc(InventoryMovement.created_at))
        if msku:
            query = query.filter_by(msku=msku)
        return query.limit(limit).all()
    
    @staticmethod
    def get_processing_logs(limit=50):
        """Get processing logs"""
        return ProcessingLog.query.order_by(desc(ProcessingLog.created_at)).limit(limit).all()
    
    @staticmethod
    def get_sales_analytics(days=7):
        """Get sales analytics for specified days"""
        from datetime import timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Sales by platform
        platform_sales = db.session.query(
            SalesRecord.platform,
            func.sum(SalesRecord.quantity).label('total_quantity'),
            func.count(SalesRecord.id).label('total_orders')
        ).filter(
            SalesRecord.sale_date.between(start_date, end_date)
        ).group_by(SalesRecord.platform).all()
        
        # Top selling products
        top_products = db.session.query(
            SalesRecord.msku,
            Product.product_name,
            func.sum(SalesRecord.quantity).label('total_sold')
        ).join(Product, SalesRecord.msku == Product.msku).filter(
            SalesRecord.sale_date.between(start_date, end_date)
        ).group_by(SalesRecord.msku, Product.product_name).order_by(
            desc('total_sold')
        ).limit(10).all()
        
        return {
            "platform_sales": [
                {"platform": p.platform, "quantity": p.total_quantity, "orders": p.total_orders}
                for p in platform_sales
            ],
            "top_products": [
                {"msku": p.msku, "name": p.product_name, "sold": p.total_sold}
                for p in top_products
            ]
        }
