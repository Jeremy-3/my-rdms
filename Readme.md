# 🏪 Inventory Management System - Custom RDBMS

> A lightweight relational database management system (RDBMS) built from Python with a FastAPI web interface for inventory management.

[![Live Demo](https://img.shields.io/badge/demo-live-success)](YOUR-RENDER-URL-HERE)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/Jeremy-3/inventory-rdbms.git)
[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com/)

**Built for:** Pesapal Junior Developer Challenge 2026

---

## 📸 Screenshots

### Dashboard
![Dashboard](images/dashboardIMS.png)
*Main dashboard showing inventory statistics*

### Suppliers Management
![Suppliers](images/suppliersIMS.png)
*Manage suppliers with CRUD operations*

### Products with Foreign Keys
![Products](images/productsIMS.png)
*Products linked to suppliers via foreign key constraints*

---

## 🌟 Project Overview

This project implements a **custom relational database management system** from scratch, demonstrating deep understanding of:

- SQL parsing and execution
- Database constraints (PRIMARY KEY, UNIQUE, FOREIGN KEY)
- Indexing for query optimization
- JOIN operations
- Transaction management
- Web-based CRUD operations

### ✨ Key Features

#### **Database Engine:**
- **SQL Parser** - Parses CREATE, INSERT, SELECT, UPDATE, DELETE, DROP
- **Constraint Enforcement** - PRIMARY KEY, UNIQUE, FOREIGN KEY validation
- **Indexing System** - B-tree-like indexes with automatic maintenance
- **JOIN Operations** - INNER JOIN with index optimization
- **WHERE Clauses** - Supports =, <, >, <=, >=, !=, LIKE operators
- **Interactive REPL** - Command-line interface for direct SQL queries
- **Case-Insensitive** - Table and column name handling

#### **Web Application:**
- **FastAPI Backend** - RESTful API with automatic documentation
- **Inventory Management** - Track products, suppliers, and stock levels
- **Foreign Key Enforcement** - Prevents invalid data relationships
- **Real-time Updates** - Dynamic UI updates without page refresh
- **Responsive Design** - Works on desktop, tablet, and mobile

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.12 or higher
pip (Python package manager)
```

### Installation
```bash
# 1. Clone the repository
git clone https://github.com/Jeremy-3/inventory-rdbms.git
cd inventory-rdbms

# 2. Activate Environment
python3 -m venv venv
source venv/bin/actiavte

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the web application
uvicorn web_app.main:app --reload

# 5. Open your browser
# Visit: http://localhost:8000
```

### Using the REPL
```bash
# Start the interactive shell
python repl.py

# Try these commands:
IMS> CREATE TABLE suppliers (id INT PRIMARY KEY, name VARCHAR, email VARCHAR);
IMS> INSERT INTO suppliers VALUES (1, 'TechSupply', 'tech@example.com');
IMS> SELECT * FROM suppliers;
IMS> SHOW TABLES;
IMS> exit
```
> [!TIP]
> For more commands to test visit inventory-rdms/sample/inventory.sql.
---

## 🛠️ Technical Architecture

### Database Engine Components
```
my_db/
├── database.py      # Core database class with table management
├── sql_parser.py    # SQL command parser (lexical analysis)
├── query.py         # Query executor (CREATE, INSERT, SELECT, etc.)
├── index.py         # Indexing system with maintenance
└── __init__.py
```

### Web Application Structure
```
web_app/
├── main.py          # FastAPI application & database initialization
├── routes.py        # API endpoints for CRUD operations
├── templates/       # HTML templates (Jinja2)
│   ├── index.html   # Dashboard
│   ├── suppliers.html
│   ├── products.html
│   └── inventory.html
└── static/          # CSS and JavaScript
    ├── style.css
    └── script.js
```

---

## 📊 Database Schema

### Tables
```sql
-- Suppliers table
CREATE TABLE suppliers (
    id INT PRIMARY KEY,
    name VARCHAR,
    contact_person VARCHAR,
    email VARCHAR UNIQUE
);

-- Products table with foreign key
CREATE TABLE products (
    id INT PRIMARY KEY,
    cname VARCHAR,
    description VARCHAR,
    price FLOAT,
    supplier_id INT FOREIGN KEY REFERENCES suppliers(id)
);

-- Inventory table with foreign key
CREATE TABLE inventory (
    id INT PRIMARY KEY,
    product_id INT FOREIGN KEY REFERENCES products(id),
    quantity INT,
    warehouse_location VARCHAR,
    last_updated VARCHAR
);
```

### Relationships
```
suppliers (1) ──→ (many) products
products (1) ──→ (1) inventory
```

---

## 🔧 Supported SQL Commands

### Table Operations
```sql
-- Create table with constraints (example)
CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR UNIQUE,
    supplier_id INT FOREIGN KEY REFERENCES suppliers(id)
);

-- Show all tables
SHOW TABLES;

-- Describe table structure
DESCRIBE users;

-- Drop table
DROP TABLE users;
```

### CRUD Operations
```sql
-- Insert data
INSERT INTO suppliers VALUES (1, 'TechSupply', 'John', 'john@tech.com');

-- Select with WHERE
SELECT * FROM suppliers WHERE id = 1;
SELECT * FROM products WHERE price > 100;
SELECT * FROM products WHERE name LIKE '%laptop%';

-- Update records
UPDATE suppliers SET email = 'new@email.com' WHERE id = 1;

-- Delete records
DELETE FROM suppliers WHERE id = 1;
```

### Advanced Features
```sql
-- Create index for faster queries
CREATE INDEX idx_email ON suppliers(email);

-- proceed to search using index
SELECT * FROM suppliers WHERE email = "john@tech.com";

-- Join tables
SELECT products.cname, suppliers.name 
FROM products 
JOIN suppliers ON products.supplier_id = suppliers.id;
```

---

## 🎯 Key Implementation Details

### 1. **Constraint Enforcement**
```python
# Foreign key validation on insert
for col in table["columns"]:
    if col.get("foreign_key"):
        # Check if referenced value exists
        ref_table = db.get_table(fk["ref_table"])
        if not value_exists_in_referenced_table:
            raise ForeignKeyViolation
```

### 2. **Index Maintenance**
```python
# Indexes automatically updated on INSERT/UPDATE/DELETE
def update_indexes_on_insert(db, table_name, row):
    for column, index_data in db.indexes[table_key].items():
        value = row.get(column)
        index_data["map"].setdefault(value, []).append(row)
```

### 3. **Query Optimization**
```python
# Use index when available, otherwise full table scan
if indexed_rows := try_index_lookup(db, table_name, where_clause):
    rows = indexed_rows  # O(1) lookup
else:
    rows = filter_rows(rows, where_clause)  # O(n) scan
```

---

<!-- ## 📈 Performance Comparison

| Operation | Without Index | With Index |
|-----------|---------------|------------|
| SELECT WHERE id=1 (100 rows) | 0.001s | 0.0001s |
| SELECT WHERE id=1 (10,000 rows) | 0.1s | 0.0001s |
| SELECT WHERE id=1 (1M rows) | 10s | 0.0001s |

**Result:** Indexes provide **~100,000x speedup** for large datasets! -->

---

## 🧪 Testing

### Manual Testing via REPL
```bash
python repl.py

# Test constraint enforcement
IMS> CREATE TABLE test (id INT PRIMARY KEY, email VARCHAR UNIQUE);
IMS> INSERT INTO test VALUES (1, 'test@email.com');
IMS> INSERT INTO test VALUES (1, 'other@email.com');
# Should fail: Duplicate PRIMARY KEY

IMS> INSERT INTO test VALUES (2, 'test@email.com');
# Should fail: Duplicate UNIQUE value
```

### Testing via Web Interface

1. Navigate to `http://localhost:8000`
2. Add a supplier
3. Add a product linked to that supplier
4. Try to delete the supplier (should delete orphans (cascade on delete))
5. Add inventory for the product


---

## 🚀 Deployment (Render)

### Option 1: Web Service (FastAPI Only)
```bash
# render.yaml
services:
  - type: web
    name: inventory-rdbms
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn web_app.main:app --host 0.0.0.0 --port $PORT"
```

### Option 2: Manual Deployment

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect GitHub repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn web_app.main:app --host 0.0.0.0 --port $PORT`
6. Deploy!

---

## 📚 Learning Outcomes

Building this project taught me:

1. **Database Internals** - How SQL databases work under the hood
2. **Parser Design** - Lexical analysis and syntax parsing
3. **Data Structures** - Hash tables, B-trees, linked lists
4. **Constraint Systems** - Referential integrity, uniqueness
5. **Query Optimization** - Indexing strategies and performance
6. **Full-Stack Development** - Backend + Frontend integration
7. **Software Architecture** - Separation of concerns, modularity

---

## 🔮 Future Enhancements

- [ ] **Persistent Storage** - Save database to disk
- [ ] **Transactions** - BEGIN, COMMIT, ROLLBACK
- [ ] **Advanced Joins** - LEFT JOIN, RIGHT JOIN, OUTER JOIN
- [ ] **Aggregations** - COUNT, SUM, AVG, GROUP BY
- [ ] **ORDER BY & LIMIT** - Sorting and pagination
- [ ] **Subqueries** - Nested SELECT statements
- [ ] **User Authentication** - Role-based access control
- [ ] **Backup/Restore** - Database export/import

---

## 👨‍💻 Author

**Jeremy Gitau**

- Email: jeremyhizashi@gmail.com
- LinkedIn: [Jeremy Gitau](https://www.linkedin.com/in/jeremy-gitau-656518328/)

---

## 📄 License

This project was created for the **Pesapal Junior Developer Challenge 2026**.

---

## 🙏 Acknowledgments

- **Pesapal** for providing this challenging opportunity
- **FastAPI** for the excellent web framework
- **Python** community for amazing tools and libraries

---

## 📞 Support & Feedback

For questions, issues, or suggestions:

- Open an [issue](https://github.com/Jeremy-3/inventory-rdbms/issues)
- Email: jeremyhizashi@gmail.com

---

<div align="center">

**⭐ If you found this project interesting, please star the repository! ⭐**

Built with ❤️ for the Pesapal Junior Developer Challenge 2026

</div>
