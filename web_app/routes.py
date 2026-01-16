from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from web_app.main import db_instance as db
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Helper function to escape SQL strings
def escape_sql_string(value):
    """Escape single quotes in SQL strings"""
    if isinstance(value, str):
        return value.replace("'", "''")
    return str(value)

router = APIRouter()

# Templates
templates = Jinja2Templates(directory="web_app/templates")

# Fix corrupted data endpoint (temporary)
@router.get("/fix-data")
async def fix_corrupted_data():
    """Fix corrupted supplier data from failed update"""
    try:
        # Delete the corrupted record
        db.execute("DELETE FROM suppliers WHERE id=1;")
        # Re-insert with correct data
        db.execute("INSERT INTO suppliers VALUES (1, 'TechSupply Inc', 'John Doe', 'john@techsupply.com');")
        return {"status": "success", "message": "Data fixed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# HOME / DASHBOARD

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    suppliers = get_table_data("suppliers", ["id", "name", "contact_person", "email"])
    products = get_table_data("products", ["id", "cname", "description", "price", "supplier_id"])
    inventory = get_table_data("inventory", ["id", "product_id", "quantity", "warehouse_location", "last_updated"])
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "suppliers_count": len(suppliers),
            "products_count": len(products),
            "inventory_count": len(inventory)
        }
    )

# insert id automatically
def get_next_id(table_name):
    """Get the next available ID by checking the actual table data"""
    try:
        # Access the database tables directly
        table = db.get_table(table_name)
        print(f"[DEBUG] Table '{table_name}': {table}")
        
        if table is None:
            print(f"[DEBUG] Table does not exist yet, returning 1")
            return 1
        
        rows = table.get("rows", [])
        print(f"[DEBUG] Rows in {table_name}: {rows}")
        
        if not rows:
            print(f"[DEBUG] No rows found, returning 1")
            return 1
        
        # Find max ID from all rows
        max_id = 0
        for row in rows:
            if isinstance(row, dict) and "id" in row:
                try:
                    id_val = int(row["id"])
                    max_id = max(max_id, id_val)
                except (ValueError, TypeError):
                    pass
        
        next_id = max_id + 1
        print(f"[DEBUG] Max ID: {max_id}, returning {next_id}")
        return next_id
    except Exception as e:
        print(f"[DEBUG] Error in get_next_id: {e}")
        return 1


def parse_table_result(result_string):
    """
    Parse the formatted table string from database and return list of tuples.
    Handles the ASCII table format returned by format_table()
    """
    if isinstance(result_string, str):
        if "No rows found" in result_string:
            return []
        
        lines = result_string.strip().split("\n")
        if len(lines) < 3:  # Need at least header, separator, and one data row
            return []
        
        # Extract header
        header_line = lines[0]
        headers = [h.strip() for h in header_line.split("|")]
        
        # Parse data rows (skip header and separator)
        data_rows = []
        for line in lines[2:]:
            # Skip the row count line at the end
            if "row(s) returned" in line:
                break
            # Skip empty/whitespace lines
            if not line.strip():
                continue
            
            values = [v.strip() for v in line.split("|")]
            if values and any(values):  # Only add if has non-empty values
                data_rows.append(values)
        
        return data_rows
    return []


def get_table_data(table_name, columns=None):
    """
    Get table data directly from the database object without parsing formatted output.
    Returns a list of lists in the format [col1, col2, ...]
    """
    try:
        table = db.get_table(table_name)
        if table is None:
            print(f"[DEBUG] Table '{table_name}' does not exist")
            return []
        
        rows = table.get("rows", [])
        if not rows:
            print(f"[DEBUG] No rows in {table_name}")
            return []
        
        # If no columns specified, get all columns in order
        if columns is None:
            columns = table.get("columns", [])
        
        print(f"[DEBUG] Table '{table_name}' columns: {columns}")
        print(f"[DEBUG] Table '{table_name}' rows: {rows}")
        
        # Convert each row dict to a list in the specified column order
        result = []
        for row in rows:
            row_data = [row.get(col) for col in columns]
            result.append(row_data)
        
        print(f"[DEBUG] Converted result: {result}")
        return result
    except Exception as e:
        print(f"[DEBUG] Error in get_table_data: {e}")
        return []



# SUPPLIERS CRUD

@router.get("/suppliers", response_class=HTMLResponse)
async def suppliers_list(request: Request):
    suppliers = get_table_data("suppliers", ["id", "name", "contact_person", "email"])
    return templates.TemplateResponse("suppliers.html", {"request": request, "suppliers": suppliers, "edit_supplier": None})

@router.get("/suppliers/edit/{supplier_id}", response_class=HTMLResponse)
async def edit_supplier_form(request: Request, supplier_id: int):
    suppliers = get_table_data("suppliers", ["id", "name", "contact_person", "email"])
    edit_supplier = None
    for s in suppliers:
        if s[0] == supplier_id:
            edit_supplier = s
            break
    return templates.TemplateResponse("suppliers.html", {"request": request, "suppliers": suppliers, "edit_supplier": edit_supplier})

@router.post("/suppliers/add")
async def add_supplier(
    name: str = Form(...),
    contact_person: str = Form(...),
    email: str = Form(...)
):
    new_id = get_next_id("suppliers")
    # Escape SQL strings to prevent injection
    name_escaped = escape_sql_string(name)
    contact_escaped = escape_sql_string(contact_person)
    email_escaped = escape_sql_string(email)
    sql = f"INSERT INTO suppliers VALUES ({new_id}, '{name_escaped}', '{contact_escaped}', '{email_escaped}');"
    print(f"[DEBUG] Executing SQL: {sql}")
    result = db.execute(sql)
    print(f"[DEBUG] Insert result: {result}")
    return RedirectResponse("/suppliers", status_code=303)

@router.post("/suppliers/update/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    name: str = Form(...),
    contact_person: str = Form(...),
    email: str = Form(...)
):
    print(f"\n[DEBUG] ===== UPDATE SUPPLIER ENDPOINT =====")
    print(f"[DEBUG] Supplier ID: {supplier_id}")
    print(f"[DEBUG] Name: {name}")
    print(f"[DEBUG] Contact Person: {contact_person}")
    print(f"[DEBUG] Email: {email}")
    
    # Escape SQL strings to prevent injection
    name_escaped = escape_sql_string(name)
    contact_escaped = escape_sql_string(contact_person)
    email_escaped = escape_sql_string(email)
    
    sql = f"UPDATE suppliers SET name='{name_escaped}', contact_person='{contact_escaped}', email='{email_escaped}' WHERE id={supplier_id};"
    print(f"[DEBUG] Executing SQL: {sql}")
    
    try:
        result = db.execute(sql)
        print(f"[DEBUG] Update result: {result}")
        print(f"[DEBUG] Update successful!")
    except Exception as e:
        print(f"[DEBUG] Error during update: {str(e)}")
        print(f"[DEBUG] Error type: {type(e)}")
        import traceback
        traceback.print_exc()
    
    return RedirectResponse("/suppliers", status_code=303)

@router.post("/suppliers/delete/{supplier_id}")
async def delete_supplier(supplier_id: int):
    sql = f"DELETE FROM suppliers WHERE id={supplier_id};"
    db.execute(sql)
    return RedirectResponse("/suppliers", status_code=303)


# PRODUCTS CRUD
@router.get("/products", response_class=HTMLResponse)
async def products_list(request: Request):
    products = get_table_data("products", ["id", "cname", "description", "price", "supplier_id"])
    suppliers = get_table_data("suppliers", ["id", "name"])
    print(f"[DEBUG] Final suppliers for template: {suppliers}")
    return templates.TemplateResponse(
        "products.html",
        {"request": request, "products": products, "suppliers": suppliers, "edit_product": None}
    )

@router.get("/products/edit/{product_id}", response_class=HTMLResponse)
async def edit_product_form(request: Request, product_id: int):
    products = get_table_data("products", ["id", "cname", "description", "price", "supplier_id"])
    suppliers = get_table_data("suppliers", ["id", "name"])
    edit_product = None
    for p in products:
        if p[0] == product_id:
            edit_product = p
            break
    return templates.TemplateResponse(
        "products.html",
        {"request": request, "products": products, "suppliers": suppliers, "edit_product": edit_product}
    )

@router.post("/products/add")
async def add_product(
    cname: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    supplier_id: int = Form(...)
):
    new_id = get_next_id("products")
    # Escape SQL strings to prevent injection
    cname_escaped = escape_sql_string(cname)
    description_escaped = escape_sql_string(description)
    sql = f"INSERT INTO products VALUES ({new_id}, '{cname_escaped}', '{description_escaped}', {price}, {supplier_id});"
    db.execute(sql)
    return RedirectResponse("/products", status_code=303)

@router.post("/products/update/{product_id}")
async def update_product(
    product_id: int,
    cname: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    supplier_id: int = Form(...)
):
    print(f"\n[DEBUG] ===== UPDATE PRODUCT ENDPOINT =====")
    print(f"[DEBUG] Product ID: {product_id}")
    print(f"[DEBUG] Name (cname): {cname}")
    print(f"[DEBUG] Description: {description}")
    print(f"[DEBUG] Price: {price}")
    print(f"[DEBUG] Supplier ID: {supplier_id}")
    
    # Escape SQL strings to prevent injection
    cname_escaped = escape_sql_string(cname)
    description_escaped = escape_sql_string(description)
    
    sql = f"UPDATE products SET cname='{cname_escaped}', description='{description_escaped}', price={price}, supplier_id={supplier_id} WHERE id={product_id};"
    print(f"[DEBUG] Executing SQL: {sql}")
    
    try:
        result = db.execute(sql)
        print(f"[DEBUG] Update result: {result}")
        print(f"[DEBUG] Update successful!")
    except Exception as e:
        print(f"[DEBUG] Error during update: {str(e)}")
        print(f"[DEBUG] Error type: {type(e)}")
        import traceback
        traceback.print_exc()
    
    return RedirectResponse("/products", status_code=303)

@router.post("/products/delete/{product_id}")
async def delete_product(product_id: int):
    sql = f"DELETE FROM products WHERE id={product_id};"
    db.execute(sql)
    return RedirectResponse("/products", status_code=303)


# INVENTORY CRUD
@router.get("/inventory", response_class=HTMLResponse)
async def inventory_list(request: Request):
    inventory = get_table_data("inventory", ["id", "product_id", "quantity", "warehouse_location", "last_updated"])
    products = get_table_data("products", ["id", "cname"])
    print(f"[DEBUG] Final products for template: {products}")
    return templates.TemplateResponse(
        "inventory.html",
        {"request": request, "inventory": inventory, "products": products, "edit_inventory": None}
    )

@router.get("/inventory/edit/{inventory_id}", response_class=HTMLResponse)
async def edit_inventory_form(request: Request, inventory_id: int):
    inventory = get_table_data("inventory", ["id", "product_id", "quantity", "warehouse_location", "last_updated"])
    products = get_table_data("products", ["id", "cname"])
    edit_inventory = None
    for inv in inventory:
        if inv[0] == inventory_id:
            edit_inventory = inv
            break
    return templates.TemplateResponse(
        "inventory.html",
        {"request": request, "inventory": inventory, "products": products, "edit_inventory": edit_inventory}
    )

@router.post("/inventory/add")
async def add_inventory(
    product_id: int = Form(...),
    quantity: int = Form(...),
    warehouse_location: str = Form(...),
    last_updated: str = Form(...)
):
    new_id = get_next_id("inventory")
    # Escape SQL strings to prevent injection
    warehouse_escaped = escape_sql_string(warehouse_location)
    last_updated_escaped = escape_sql_string(last_updated)
    sql = f"INSERT INTO inventory VALUES ({new_id}, {product_id}, {quantity}, '{warehouse_escaped}', '{last_updated_escaped}');"
    db.execute(sql)
    return RedirectResponse("/inventory", status_code=303)

@router.post("/inventory/update/{inventory_id}")
async def update_inventory(
    inventory_id: int,
    product_id: int = Form(...),
    quantity: int = Form(...),
    warehouse_location: str = Form(...),
    last_updated: str = Form(...)
):
    print(f"\n[DEBUG] ===== UPDATE INVENTORY ENDPOINT =====")
    print(f"[DEBUG] Inventory ID: {inventory_id}")
    print(f"[DEBUG] Product ID: {product_id}")
    print(f"[DEBUG] Quantity: {quantity}")
    print(f"[DEBUG] Warehouse Location: {warehouse_location}")
    print(f"[DEBUG] Last Updated: {last_updated}")
    
    # Escape SQL strings to prevent injection
    warehouse_escaped = escape_sql_string(warehouse_location)
    last_updated_escaped = escape_sql_string(last_updated)
    
    sql = f"UPDATE inventory SET product_id={product_id}, quantity={quantity}, warehouse_location='{warehouse_escaped}', last_updated='{last_updated_escaped}' WHERE id={inventory_id};"
    print(f"[DEBUG] Executing SQL: {sql}")
    
    try:
        result = db.execute(sql)
        print(f"[DEBUG] Update result: {result}")
        print(f"[DEBUG] Update successful!")
    except Exception as e:
        print(f"[DEBUG] Error during update: {str(e)}")
        print(f"[DEBUG] Error type: {type(e)}")
        import traceback
        traceback.print_exc()
    
    return RedirectResponse("/inventory", status_code=303)

@router.post("/inventory/delete/{inventory_id}")
async def delete_inventory(inventory_id: int):
    sql = f"DELETE FROM inventory WHERE id={inventory_id};"
    db.execute(sql)
    return RedirectResponse("/inventory", status_code=303)
