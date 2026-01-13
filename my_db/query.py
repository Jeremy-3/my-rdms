# my_db/query.py
import re

def execute_query(parsed, db):
    """Execute parsed SQL commands"""
    
    query_type = parsed["type"]
    
    if query_type == "SHOW_TABLES":
        return show_tables(db)
    
    elif query_type == "DESCRIBE":
        return describe_table(parsed, db)
    
    elif query_type == "CREATE_TABLE":
        return create_table(parsed, db)
    
    elif query_type == "INSERT":
        return insert_into(parsed, db)
    
    elif query_type == "SELECT":
        return select_from(parsed, db)
    
    elif query_type == "UPDATE":
        return update_table(parsed, db)
    
    elif query_type == "DELETE":
        return delete_from(parsed, db)
    
    elif query_type == "DROP_TABLE":
        return drop_table(parsed, db)
    else:
        raise ValueError(f"Unknown query type: {query_type}")


def create_table(parsed, db):
    """CREATE TABLE tablename (columns...)"""
    table_name = parsed["table"].lower()  # Store as lowercase
    columns = parsed["columns"]
    
    if db.table_exists(table_name):
        return f"Error: Table '{table_name}' already exists"
    
    db.tables[table_name] = {
        "columns": columns,
        "rows": []
    }
    
    return f"✓ Table '{table_name}' created successfully."


def insert_into(parsed, db):
    """INSERT INTO tablename VALUES (...)"""
    table_name = parsed["table"]
    values = parsed["values"]
    
    # Use case-insensitive lookup
    table = db.get_table(table_name)
    
    if not table:
        return f"Error: Table '{table_name}' does not exist"
    
    # Create row as dictionary
    row = {}
    for i, col in enumerate(table["columns"]):
        row[col["name"]] = values[i] if i < len(values) else None

    # check PRIMARY KEY constraint
    for col in table["columns"]:
        if col.get("primary_key"):
            pk_col = col["name"]
            pk_value = row[pk_col]

            for existing_row in table["rows"]:
                if existing_row.get(pk_col) == pk_value:
                    actual_name = db.get_table_name(table_name)
                    return f"Error: Duplicate PRIMARY KEY value '{pk_value}' for column '{pk_col}' in table '{actual_name}'"
                
    # check unique constraints
    for col in table["columns"]:
        if col.get("unique"):
            unique_col = col["name"]
            unique_value = row[unique_col]

            for existing_row in table["rows"]:
                if existing_row.get(unique_col) == unique_value:
                    actual_name = db.get_table_name(table_name)
                    return f"Error: Duplicate UNIQUE value '{unique_value}' for column '{unique_col}' in table '{actual_name}'"
    
    table["rows"].append(row)
    
    actual_name = db.get_table_name(table_name)
    return f"✓ 1 row inserted into '{actual_name}'."


def select_from(parsed, db):
    """SELECT * FROM tablename [WHERE ...]"""
    table_name = parsed["table"]
    columns = parsed["columns"]
    where_clause = parsed.get("where")
    
    # Use case-insensitive lookup
    table = db.get_table(table_name)
    
    if not table:
        return f"Error: Table '{table_name}' does not exist"
    
    rows = table["rows"]
    
    # Filter by WHERE clause if present
    if where_clause:
        rows = filter_rows(rows, where_clause)
    
    # Format output
    if not rows:
        return "No rows found."
    
    # Print table
    return format_table(rows, columns, table["columns"])


def show_tables(db):
    """Show all tables"""
    if not db.tables:
        return "No tables in database."
    
    output = ["Tables in the database:"]
    for table_name in db.tables.keys():
        row_count = len(db.tables[table_name]["rows"])
        output.append(f"- {table_name} ({row_count} rows)")
    
    return "\n".join(output)


def describe_table(parsed, db):
    """Describe table structure"""
    table_name = parsed["table"]
    
    # Use case-insensitive lookup
    table = db.get_table(table_name)
    
    if not table:
        return f"Error: Table '{table_name}' does not exist"
    
    actual_name = db.get_table_name(table_name)
    columns = table["columns"]
    
    output = [f"\nTable: {actual_name}", "-" * 50]
    output.append(f"{'Column':<20} {'Type':<15} {'Constraints'}")
    output.append("-" * 50)
    
    for col in columns:
        constraints = "PRIMARY KEY" if col.get("primary_key") else ""
        output.append(f"{col['name']:<20} {col['type']:<15} {constraints}")
    
    output.append("-" * 50)
    output.append(f"Total rows: {len(table['rows'])}")
    
    return "\n".join(output)


def filter_rows(rows, where_clause):
    """Simple WHERE filtering with multiple operators)"""
    # determine operator
    if ">=" in where_clause:
        operator = ">="
    elif "<=" in where_clause:
        operator = "<="
    elif "!=" in where_clause or "<>" in where_clause:
        operator = "!="
    elif "=" in where_clause:
        operator = "="
    elif ">" in where_clause:
        operator = ">"  
    elif "<" in where_clause:
        operator = "<"
    elif "LIKE" in where_clause.upper():
        operator = "LIKE"
        parts = where_clause.split(" LIKE ", 1) if " LIKE " in where_clause else where_clause.split(" like ", 1)
    else:
        raise ValueError(f"Unsupported WHERE clause operator in: {where_clause}")
    
    # Split condition
    # if operator == "LIKE":
    #     parts = where_clause.split("LIKE")
    # else:
    #     parts = where_clause.split(operator)

    col_name = parts[0].strip()
    value = parts[1].strip().strip("'\"")  # Remove quotes if any

    # Filter rows based on operator
    filtered = []
    for row in rows:
        row_value = str(row.get(col_name, ""))
        if operator == "=":
            if row_value == value:
                filtered.append(row)
        elif operator == "!=":
            if row_value != value:
                filtered.append(row)
        elif operator == ">":
            try:
                if float(row_value) > float(value):
                    filtered.append(row)
            except ValueError:
                if row_value > value: 
                    filtered.append(row)
        elif operator == "<":
            try:
                if float(row_value) < float(value):
                    filtered.append(row)
            except ValueError:
                if row_value < value:
                    filtered.append(row)
        elif operator == ">=":
            try:
                if float(row_value) >= float(value):
                    filtered.append(row)
            except ValueError:
                if row_value >= value:
                    filtered.append(row)
        elif operator == "<=":
            try:
                if float(row_value) <= float(value):
                    filtered.append(row)
            except ValueError:
                if row_value <= value:
                    filtered.append(row)
        elif operator == "LIKE":
            pattern = value.replace("%", ".*").replace("_", ".")
            if re.search(f"^{pattern}$", row_value, re.IGNORECASE):
                filtered.append(row)
    return filtered


def format_table(rows, selected_cols, all_columns):
    """Format rows as a pretty table"""
    if not rows:
        return "No rows found."
    
    # Determine which columns to show
    if selected_cols == "*":
        cols_to_show = [col["name"] for col in all_columns]
    else:
        cols_to_show = selected_cols
    
    # Build output
    output = []
    
    # Header
    header = " | ".join(cols_to_show)
    output.append(header)
    output.append("-" * len(header))
    
    # Rows
    for row in rows:
        row_values = [str(row.get(col, "NULL")) for col in cols_to_show]
        output.append(" | ".join(row_values))
    
    output.append(f"\n{len(rows)} row(s) returned.")
    
    return "\n".join(output)


def update_table(parsed, db):
    """UPDATE tablename SET col = value WHERE condition"""
    table_name = parsed["table"]
    column = parsed["column"]
    value = parsed["value"]
    where_clause = parsed.get("where")
    
    # Get table (case-insensitive)
    table = db.get_table(table_name)
    
    if not table:
        return f"Error: Table '{table_name}' does not exist"
    
    # Get all rows
    all_rows = table["rows"]
    
    # Filter rows if WHERE clause exists
    if where_clause:
        rows_to_update = filter_rows(all_rows, where_clause)
    else:
        rows_to_update = all_rows
    
    # Check if no rows match
    if not rows_to_update:
        return "0 row(s) updated."
    
    # Update rows
    updated_count = 0
    for row in rows_to_update:
        if column in row:
            row[column] = value
            updated_count += 1
    
    actual_name = db.get_table_name(table_name)
    return f"✓ {updated_count} row(s) updated in '{actual_name}'."

def delete_from(parsed, db):
    """DELETE FROM tablename WHERE condition"""
    table_name = parsed["table"]
    where_clause = parsed.get("where")
    
    # Use case-insensitive lookup
    table = db.get_table(table_name)
    
    if not table:
        return f"Error: Table '{table_name}' does not exist"
    
    rows = table["rows"]
    
    # Filter by WHERE clause if present
    if where_clause:
        rows_to_delete = filter_rows(rows, where_clause)
    else:
        rows_to_delete = rows
    
    # Delete rows
    for row in rows_to_delete:
        rows.remove(row)
    
    actual_name = db.get_table_name(table_name)
    return f"✓ {len(rows_to_delete)} row(s) deleted from '{actual_name}'."


def drop_table(parsed, db): 
    """DROP TABLE tablename"""
    table_name = parsed["table"]
    
    # Use case-insensitive lookup
    actual_name = db.get_table_name(table_name)
    
    if not actual_name:
        return f"Error: Table '{table_name}' does not exist"
    
    del db.tables[actual_name]
    
    return f"✓ Table '{actual_name}' dropped successfully."