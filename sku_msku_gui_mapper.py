"""
SKU to MSKU Mapper with GUI
Complete solution for Part 1: Data Cleaning and Management
Handles combo products, inventory tracking, and provides user-friendly interface
"""

import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os
from datetime import datetime
import threading

class SKUMapperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SKU to MSKU Mapper - WMS System")
        self.root.geometry("800x600")
        
        # Data storage
        self.mapping_data = None
        self.combo_data = None
        self.current_inventory = None
        self.processed_files = []
        
        # Load mapping data on startup
        self.load_mapping_data()
        
        # Create GUI
        self.create_widgets()
        
    def load_mapping_data(self):
        """Load SKU-MSKU mapping and combo data from Excel"""
        try:
            # Load main mapping
            self.mapping_data = pd.read_excel('WMS-04-02.xlsx', sheet_name='Msku With Skus')
            
            # Load combo data
            self.combo_data = pd.read_excel('WMS-04-02.xlsx', sheet_name='Combos skus')
            
            # Load current inventory
            self.current_inventory = pd.read_excel('WMS-04-02.xlsx', sheet_name='Current Inventory ')
            
            # Create combo mapping dictionary
            self.combo_mapping = self.create_combo_mapping()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load mapping data: {str(e)}")
    
    def create_combo_mapping(self):
        """Create a dictionary mapping combo SKUs to their component MSKUs"""
        combo_map = {}
        for _, row in self.combo_data.iterrows():
            combo_sku = row['Combo ']
            if pd.notna(combo_sku):
                components = []
                for i in range(1, 15):  # SKU1 to SKU14
                    sku_col = f'SKU{i}'
                    if sku_col in row and pd.notna(row[sku_col]):
                        components.append(row[sku_col])
                if components:
                    combo_map[combo_sku] = components
        return combo_map
    
    def create_widgets(self):
        """Create the GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="SKU to MSKU Mapper", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status indicators
        mapping_status = "✅ Loaded" if self.mapping_data is not None else "❌ Failed"
        combo_status = "✅ Loaded" if self.combo_data is not None else "❌ Failed"
        inventory_status = "✅ Loaded" if self.current_inventory is not None else "❌ Failed"
        
        ttk.Label(status_frame, text=f"SKU-MSKU Mapping: {mapping_status}").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(status_frame, text=f"Combo Products: {combo_status}").grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        ttk.Label(status_frame, text=f"Current Inventory: {inventory_status}").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        
        # File processing frame
        file_frame = ttk.LabelFrame(main_frame, text="File Processing", padding="10")
        file_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # File selection
        ttk.Label(file_frame, text="Select sales files to process:").grid(row=0, column=0, sticky=tk.W)
        
        # Buttons frame
        buttons_frame = ttk.Frame(file_frame)
        buttons_frame.grid(row=1, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(buttons_frame, text="Select CSV Files", 
                  command=self.select_files).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(buttons_frame, text="Process Folder", 
                  command=self.process_folder).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(buttons_frame, text="Process Selected Files", 
                  command=self.process_files).pack(side=tk.LEFT, padx=(0, 10))
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.handle_combos = tk.BooleanVar(value=True)
        self.update_inventory = tk.BooleanVar(value=True)
        self.create_reports = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Handle Combo Products", 
                       variable=self.handle_combos).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="Update Inventory", 
                       variable=self.update_inventory).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        ttk.Checkbutton(options_frame, text="Create Analysis Reports", 
                       variable=self.create_reports).grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        
        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="Ready to process files...")
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Processing Log", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def map_sku_to_msku(self, sku):
        """Map single SKU to MSKU, handling combos"""
        # Check if it's a combo first
        if self.handle_combos.get() and sku in self.combo_mapping:
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
            
            self.log_message(f"Processing {os.path.basename(file_path)} - Platform: {platform}")
            
            # Get SKU column based on platform
            sku_column = self.get_sku_column(df.columns.tolist(), platform)
            if not sku_column:
                self.log_message(f"❌ No SKU column found in {file_path}")
                return None
                
            # Process each row
            processed_rows = []
            inventory_changes = {}
            
            for _, row in df.iterrows():
                sku = row[sku_column]
                quantity = row.get('Quantity', 1)
                
                if pd.isna(sku) or quantity <= 0:
                    continue
                    
                mapping_result = self.map_sku_to_msku(sku)
                
                if mapping_result['type'] == 'combo':
                    # Handle combo product
                    for component_msku in mapping_result['components']:
                        combo_row = row.copy()
                        combo_row['Original_SKU'] = sku
                        combo_row['MSKU'] = component_msku
                        combo_row['Quantity'] = quantity  # Each component gets the full quantity
                        combo_row['Product_Type'] = 'Combo_Component'
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
                    processed_rows.append(new_row)
            
            # Create output dataframe
            output_df = pd.DataFrame(processed_rows)
            
            # Save processed file
            output_path = file_path.replace('.csv', '_Mapped_Enhanced.csv')
            output_df.to_csv(output_path, index=False)
            
            self.log_message(f"✅ Saved: {os.path.basename(output_path)}")
            
            # Update inventory if requested
            if self.update_inventory.get():
                self.update_inventory_tracking(inventory_changes, file_path)
                
            # Create reports if requested
            if self.create_reports.get():
                self.create_file_reports(output_df, file_path)
                
            return output_df
            
        except Exception as e:
            self.log_message(f"❌ Error processing {file_path}: {str(e)}")
            return None
    
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
    
    def update_inventory_tracking(self, inventory_changes, file_path):
        """Update inventory tracking"""
        try:
            # Create inventory update record
            update_record = {
                'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Source_File': os.path.basename(file_path),
                'MSKU': list(inventory_changes.keys()),
                'Quantity_Sold': list(inventory_changes.values())
            }
            
            # Save to inventory log
            log_path = 'inventory_updates_log.csv'
            log_df = pd.DataFrame(update_record)
            
            if os.path.exists(log_path):
                existing_log = pd.read_csv(log_path)
                combined_log = pd.concat([existing_log, log_df], ignore_index=True)
            else:
                combined_log = log_df
                
            combined_log.to_csv(log_path, index=False)
            self.log_message(f"📊 Updated inventory log: {len(inventory_changes)} MSKUs affected")
            
        except Exception as e:
            self.log_message(f"⚠️ Warning: Could not update inventory: {str(e)}")
    
    def create_file_reports(self, df, file_path):
        """Create analysis reports for the processed file"""
        try:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Sales by MSKU report
            sales_report = df.groupby('MSKU')['Quantity'].sum().reset_index()
            sales_report = sales_report.sort_values('Quantity', ascending=False)
            sales_report.to_csv(f"{base_name}_sales_by_msku.csv", index=False)
            
            # Combo analysis report
            combo_report = df[df['Product_Type'] == 'Combo_Component']
            if not combo_report.empty:
                combo_analysis = combo_report.groupby(['Original_SKU', 'MSKU'])['Quantity'].sum().reset_index()
                combo_analysis.to_csv(f"{base_name}_combo_analysis.csv", index=False)
                
            self.log_message(f"📈 Created analysis reports for {base_name}")
            
        except Exception as e:
            self.log_message(f"⚠️ Warning: Could not create reports: {str(e)}")
    
    def select_files(self):
        """Select individual CSV files"""
        files = filedialog.askopenfilenames(
            title="Select Sales CSV Files",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if files:
            self.process_files_list(files)
    
    def process_folder(self):
        """Process entire Sales 7 days folder"""
        if os.path.exists('Sales 7 days'):
            self.process_sales_folder('Sales 7 days')
        else:
            messagebox.showerror("Error", "Sales 7 days folder not found")
    
    def process_files(self):
        """Process files based on current selection"""
        if os.path.exists('Sales 7 days'):
            self.process_sales_folder('Sales 7 days')
        else:
            messagebox.showinfo("Info", "Please select files or ensure 'Sales 7 days' folder exists")
    
    def process_files_list(self, files):
        """Process a list of files"""
        def process():
            self.progress_bar.start()
            self.progress_var.set("Processing files...")
            
            try:
                for i, file_path in enumerate(files):
                    self.progress_var.set(f"Processing file {i+1}/{len(files)}: {os.path.basename(file_path)}")
                    self.process_sales_file(file_path)
                
                self.log_message(f"🎉 Completed processing {len(files)} files")
                messagebox.showinfo("Success", f"Successfully processed {len(files)} files!")
                
            except Exception as e:
                self.log_message(f"❌ Error during batch processing: {str(e)}")
                messagebox.showerror("Error", f"Error during processing: {str(e)}")
            finally:
                self.progress_bar.stop()
                self.progress_var.set("Ready to process files...")
        
        # Run in separate thread to prevent GUI freezing
        threading.Thread(target=process, daemon=True).start()
    
    def process_sales_folder(self, folder_path):
        """Process all CSV files in the sales folder"""
        files_to_process = []
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.csv') and not file.startswith('Mapped_'):
                    files_to_process.append(os.path.join(root, file))
        
        if files_to_process:
            self.process_files_list(files_to_process)
        else:
            messagebox.showinfo("Info", "No CSV files found to process")

def main():
    root = tk.Tk()
    app = SKUMapperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
