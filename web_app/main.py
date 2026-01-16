from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import sys, os

# Add parent directory to path so we can import my_db
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from my_db.database import Database

# database instance
db_instance = Database()

app = FastAPI(
    title="Inventory RDBMS Web Interface",
    description="Custom database engine with web interface",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="web_app/static"), name="static")

# Import and include routes AFTER defining db_instance
from web_app.routes import router
app.include_router(router)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    try:
        # Create tables if not exist
        db_instance.execute("""
            CREATE TABLE suppliers (id INT PRIMARY KEY, name VARCHAR, contact_person VARCHAR, email VARCHAR UNIQUE);
        """)
        db_instance.execute("""
            CREATE TABLE products (id INT PRIMARY KEY, cname VARCHAR, description VARCHAR, price FLOAT, supplier_id INT FOREIGN KEY REFERENCES suppliers(id));
        """)
        db_instance.execute("""
            CREATE TABLE inventory (id INT PRIMARY KEY, product_id INT FOREIGN KEY REFERENCES products(id), quantity INT, warehouse_location VARCHAR, last_updated VARCHAR);
        """)

        # Check for corrupted data and fix it
        suppliers_table = db_instance.get_table("suppliers")
        if suppliers_table:
            rows = suppliers_table.get("rows", [])
            has_corruption = False
            
            # Check for corrupted records (containing SQL syntax in name field)
            for row in rows:
                name = row.get("name", "")
                # Corruption indicator: name contains both quote and "contact_person="
                if "contact_person=" in name and "'" in name:
                    has_corruption = True
                    print(f"⚠️ Detected corrupted data, cleaning database...")
                    break
            
            if has_corruption:
                # Clear all tables and reinitialize
                print("[STARTUP] Clearing corrupted tables...")
                db_instance.tables.clear() 
                
                # Recreate tables
                db_instance.execute("""
                    CREATE TABLE suppliers (id INT PRIMARY KEY, name VARCHAR, contact_person VARCHAR, email VARCHAR UNIQUE);
                """)
                db_instance.execute("""
                    CREATE TABLE products (id INT PRIMARY KEY, cname VARCHAR, description VARCHAR, price FLOAT, supplier_id INT FOREIGN KEY REFERENCES suppliers(id));
                """)
                db_instance.execute("""
                    CREATE TABLE inventory (id INT PRIMARY KEY, product_id INT FOREIGN KEY REFERENCES products(id), quantity INT, warehouse_location VARCHAR, last_updated VARCHAR);
                """)
                
                # Insert fresh sample data
                print("[STARTUP] Reinserting clean sample data...")
                db_instance.execute("INSERT INTO suppliers VALUES (1, 'TechSupply Inc', 'John Doe', 'john@techsupply.com')")
                db_instance.execute("INSERT INTO suppliers VALUES (2, 'Global Electronics', 'Jane Smith', 'jane@globalelec.com')")
                db_instance.execute("INSERT INTO products VALUES (1, 'Laptop Dell XPS', 'High-performance laptop', 1200.50, 1)")
                db_instance.execute("INSERT INTO products VALUES (2, 'Mouse Logitech', 'Wireless mouse', 25.99, 1)")
                db_instance.execute("INSERT INTO inventory VALUES (1, 1, 15, 'Warehouse A', '2026-01-13')")
                db_instance.execute("INSERT INTO inventory VALUES (2, 2, 50, 'Warehouse A', '2026-01-13')")
                print("✓ Database cleaned and sample data restored!")
            elif len(rows) == 0:
                # Tables exist but are empty, insert sample data
                print("[STARTUP] Tables empty, inserting sample data...")
                db_instance.execute("INSERT INTO suppliers VALUES (1, 'TechSupply Inc', 'John Doe', 'john@techsupply.com')")
                db_instance.execute("INSERT INTO suppliers VALUES (2, 'Global Electronics', 'Jane Smith', 'jane@globalelec.com')")
                db_instance.execute("INSERT INTO products VALUES (1, 'Laptop Dell XPS', 'High-performance laptop', 1200.50, 1)")
                db_instance.execute("INSERT INTO products VALUES (2, 'Mouse Logitech', 'Wireless mouse', 25.99, 1)")
                db_instance.execute("INSERT INTO inventory VALUES (1, 1, 15, 'Warehouse A', '2026-01-13')")
                db_instance.execute("INSERT INTO inventory VALUES (2, 2, 50, 'Warehouse A', '2026-01-13')")
                print("✓ Database tables created and sample data inserted!")
            else:
                print("✓ Database tables exist with clean data")

    except Exception as e:
        print(f"Note: {e}") 

# Simple API home
@app.get("/info")
def info():
    return {
        "message": "Inventory Management System API",
        "database": "Custom RDBMS",
        "endpoints": {
            "suppliers": "/suppliers",
            "products": "/products",
            "inventory": "/inventory"
        }
    }
