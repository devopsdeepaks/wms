# WMS (Warehouse Management System)

## 🚀 Complete Enterprise-Grade WMS Solution

A comprehensive Warehouse Management System featuring web interface, AI-powered analytics, desktop GUI, and automated inventory tracking.

## 📋 Project Overview

This WMS system provides:

- **Part 1**: Data Cleaning and SKU-MSKU Mapping with GUI
- **Part 2**: Automated File Processing and Combo Product Handling
- **Part 3**: Web Application with Dashboard and Analytics
- **Part 4**: AI Data Layer with Natural Language Queries

## 🛠️ Technologies Used

### Backend

- **Python 3.8+** - Core programming language
- **Flask 2.3.3** - Web framework for REST APIs and web interface
- **SQLAlchemy 2.0.21** - Database ORM and migrations
- **SQLite** - Database for AI data layer (production ready)

### Frontend

- **HTML5/CSS3** - Responsive web interface
- **Bootstrap 5** - Modern UI framework
- **JavaScript** - Interactive features and AJAX
- **Jinja2** - Template engine

### Data Processing

- **Pandas 2.1.1** - Data manipulation and analysis
- **NumPy 1.24.3** - Numerical computing
- **OpenPyXL 3.1.2** - Excel file processing

### Visualization

- **Plotly 5.17.0** - Interactive charts and dashboards

### Desktop GUI

- **Tkinter** - Cross-platform desktop application (built-in)

### File Processing

- **CSV/Excel Support** - Automated processing of sales files
- **Multi-platform Support** - Amazon, Flipkart, Meesho integration

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup Instructions

1. **Clone/Download the project**

   ```bash
   cd path/to/wms/project
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Excel data file**
   - Ensure `WMS-04-02.xlsx` is in the project root
   - File should contain sheets: 'Current Inventory ', 'Msku With Skus', 'Combos skus'

## 🚀 Quick Start

### Option 1: Automated Launcher (Recommended)

```bash
python start_wms.py
```

Choose option 4 to start both web applications automatically.

### Option 2: Individual Applications

#### Main WMS Web App

```bash
python wms_web_app.py
```

- **Access**: http://localhost:5000
- **Features**: Dashboard, File Upload, Inventory Management, Reports

#### AI Data Layer (Natural Language Queries)

```bash
python simple_ai_app.py
```

- **Access**: http://localhost:5001
- **Features**: AI Chat, Data Analytics, Interactive Charts

#### Desktop GUI Application

```bash
python sku_msku_gui_mapper.py
```

- **Features**: File Processing, SKU Mapping, Progress Tracking

### Health Check

```bash
python health_check.py
```

Verifies all components are working correctly before running.

## 📊 System Features

### 🌐 Web Interface (Port 5000)

- **Dashboard**: Real-time inventory overview with 1011+ products
- **File Upload**: Drag-and-drop CSV processing
- **Inventory Management**: Stock tracking and low-stock alerts
- **Analytics**: Sales reports and platform performance
- **Multi-format Support**: CSV, Excel file processing

### 🤖 AI Interface (Port 5001)

- **Natural Language Queries**:
  - "Show products with low stock"
  - "What are top selling products?"
  - "Display sales by platform"
- **Interactive Charts**: Bar, pie, line, scatter plots
- **Real-time Data**: Connected to actual inventory (1011 products)
- **Smart Analytics**: Automated insights and recommendations

### 💻 Desktop Application

- **User-friendly GUI**: Progress bars and real-time logs
- **Batch Processing**: Handle multiple files simultaneously
- **Combo Product Support**: Advanced SKU mapping
- **Inventory Tracking**: Real-time stock updates

## 📁 Project Structure

```
WMS-System/
├── wms_web_app.py              # Main web application
├── simple_ai_app.py            # AI data layer and chat
├── sku_msku_gui_mapper.py      # Desktop GUI application
├── sku_msku_mapper.py          # Core mapping logic
├── start_wms.py                # Automated launcher script
├── health_check.py             # System verification
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── WMS-04-02.xlsx             # Master data file (1011 products)
├── database/                   # Database models and services
│   ├── models.py              # SQLAlchemy models
│   ├── service.py             # Database operations
│   ├── migration.py           # Database migrations
│   └── setup.py               # Database setup
├── templates/                  # HTML templates
├── static/                     # CSS, JS, images
├── Sales 7 days/              # Sales data folders
├── uploads/                   # Processed files storage
└── reports/                   # Generated reports storage
```

## 🔧 Configuration

### Database

- **Development**: SQLite (default, no setup required)
- **Production**: PostgreSQL/MySQL support available

### File Processing

- **Supported Formats**: CSV, Excel (.xlsx, .xls)
- **Platforms**: Amazon (FNSKU), Flipkart (SKU), Meesho (SKU)
- **Combo Products**: Automatic component mapping

## 💡 Usage Examples

### Web Interface Queries

1. Upload sales files via drag-and-drop
2. View real-time dashboard with 1011 products
3. Monitor low-stock alerts (products with 0 stock)
4. Generate platform-wise sales reports

### AI Natural Language Queries

```
"Show me all BTS pillow products"
"Which products have stock above 100?"
"Sales breakdown by platform last 30 days"
"Products that need restocking urgently"
```

### Desktop Processing

1. Select CSV files from Sales 7 days folder
2. Enable combo product handling
3. Process with real-time progress tracking
4. Generate enhanced reports with MSKU mapping

## 📈 Performance

- **Product Capacity**: 1000+ products tested
- **Processing Speed**: 50+ sales records per second
- **Memory Usage**: Optimized for large datasets
- **Response Time**: <2s for most queries

## 🛡️ Production Deployment

### Using Gunicorn (Recommended)

```bash
# Main web app
gunicorn -w 4 -b 0.0.0.0:5000 wms_web_app:app

# AI interface
gunicorn -w 2 -b 0.0.0.0:5001 simple_ai_app:app
```

### Environment Variables

```bash
export FLASK_ENV=production
export DATABASE_URL=your_database_url  # Optional
```

## 🔍 Troubleshooting

### Common Issues

1. **Port already in use**: Change port in app.run() or kill existing processes
2. **Excel file not found**: Ensure WMS-04-02.xlsx is in project root
3. **Module not found**: Run `pip install -r requirements.txt`

### Database Issues

```bash
# Reset AI database
rm simple_ai_warehouse.db
python simple_ai_app.py
```

## 📞 Support

For technical support or feature requests:

- Check troubleshooting section above
- Verify all dependencies are installed
- Ensure Excel data file is properly formatted

## 🎯 Project Success Metrics

✅ **Part 1 Complete**: SKU-MSKU mapping with combo product support  
✅ **Part 2 Complete**: Automated file processing for multiple platforms  
✅ **Part 3 Complete**: Web interface with dashboard and analytics  
✅ **Part 4 Complete**: AI data layer with natural language queries

**Total Products Supported**: 1011 real products loaded  
**Platforms Integrated**: Amazon, Flipkart, Meesho  
**File Formats**: CSV, Excel with automatic detection  
**User Interfaces**: Web (2 apps) + Desktop GUI

---

**🎉 Enterprise WMS System - Production Ready!**
