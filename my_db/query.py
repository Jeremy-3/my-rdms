# my_db/query.py
import re
from my_db.index import create_index,update_indexes_on_insert,update_indexes_on_delete,update_indexes_on_update,lookup_by_index

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
        if parsed.get("join"):
            return select_with_join(parsed,db)
        else:
            return select_from(parsed,db)
    
    elif query_type == "UPDATE":
        return update_table(parsed, db)
    
    elif query_type == "DELETE":
        return delete_from(parsed, db)
    
    elif query_type == "DROP_TABLE":
        return drop_table(parsed, db)
    
    elif query_type == "CREATE_INDEX":
        return create_index(
            db,
            parsed["table"],
            parsed["index_name"],
            parsed["column"]
        )
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
        "rows": [],
        "foreign_keys":parsed.get("foreign_keys",[])
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
    # check for foreign key constraints
    for col in table["columns"]:
        fk = col.get("foreign_key")
        if fk:
            fk_value = row[col["name"]]
            
            # Skip NULL values (FK can be optional)
            if fk_value is None or str(fk_value).upper() == "NULL":
                continue
            
            # Get referenced table
            ref_table = db.get_table(fk["ref_table"])
            if not ref_table:
                return f"Error: Referenced table '{fk['ref_table']}' does not exist"
            
            # Check if the foreign key value exists in referenced table
            ref_col = fk["ref_column"]
            value_exists = False
            
            for ref_row in ref_table["rows"]:
                if str(ref_row.get(ref_col)) == str(fk_value):
                    value_exists = True
                    break
            
            if not value_exists:
                return f"Error: FOREIGN KEY constraint violated - value '{fk_value}' not found in {fk['ref_table']}.{ref_col}"
            
    table["rows"].append(row)

    update_indexes_on_insert(db,table_name,row)
    
    actual_name = db.get_table_name(table_name)
                
    return f"✓ 1 row inserted into '{actual_name}'."



def select_with_join(parsed, db):
    base_table_name = parsed["table"]
    join_info = parsed["join"]

    base_table = db.get_table(base_table_name)
    join_table = db.get_table(join_info["table"])

    if not base_table or not join_table:
        return "Error: One or more tables do not exist"

    # Split qualified columns: products.id → (products, id)
    left_table, left_col = join_info["left"].split(".")
    right_table, right_col = join_info["right"].split(".")

    results = []

    for row in base_table["rows"]:
        key = row.get(left_col)

        matches = lookup_by_index(
            db=db,
            table_name=join_info["table"],
            column=right_col,
            value=key
        )

        if matches is None:
            # No index → fallback scan
            matches = [
                r for r in join_table["rows"]
                if r.get(right_col) == key
            ]

        for match in matches:
            combined = {
                f"{base_table_name}.{k}": v for k, v in row.items()
            }
            combined.update({
                f"{join_info['table']}.{k}": v for k, v in match.items()
            })
            results.append(combined)

    return results


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
    # if where_clause:
    #     rows = filter_rows(rows, where_clause)
    if where_clause:
        indexed_rows = try_index_lookup(db, table_name, where_clause)
        if indexed_rows is not None:
            rows = indexed_rows
            print(f"[DEBUG] Used index on {table_name}")
        else:
            rows = filter_rows(rows, where_clause)
            print("[DEBUG] Full table scan")
            print("[DEBUG] Available indexes:", db.indexes)
    
    # Format output
    if not rows:
        return "No rows found."
    
    # Print table
    return format_table(rows, columns, table["columns"])

def try_index_lookup(db, table_name, where_clause):
    if "=" not in where_clause:
        return None  # Only handle equality for index lookup
    
    #column, value = where_clause.split("=", 1)

    parts = where_clause.split("=",1)
    if len(parts) !=2:
        return None
    
    column, value = parts
    column = column.strip().lower()
    value = value.strip().strip("'\"")  # Remove quotes if any

    table_key = table_name.lower()
    table_indexes = db.indexes.get(table_key)

    if not table_indexes:
        return None

    index = table_indexes.get(column)

    if not index:
        return None  # No index found for this column
    
    return index["map"].get(value, [])



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
    """Describe table structure including PK, UNIQUE, and FOREIGN KEY"""
    table_name = parsed.get("table")
    
    if not table_name:
        return "Error: Missing table name"
    
    table = db.get_table(table_name)
    if not table:
        return f"Error: Table '{table_name}' does not exist"
    
    actual_name = db.get_table_name(table_name)
    columns = table["columns"]
    
    output = [f"\nTable: {actual_name}", "=" * 70]
    output.append(f"{'Column':<20} {'Type':<15} {'Constraints'}")
    output.append("=" * 70)
    
    for col in columns:
        constraints = []
        
        if col.get("primary_key"):
            constraints.append("PRIMARY KEY")
        
        if col.get("unique"):
            constraints.append("UNIQUE")
        
        # Check for FK
        fk = col.get("foreign_key")
        if fk:
            constraints.append(f"FK → {fk['ref_table']}.{fk['ref_column']}")
        
        constraint_str = ", ".join(constraints) if constraints else "-"
        output.append(f"{col['name']:<20} {col['type']:<15} {constraint_str}")
    
    output.append("=" * 70)
    output.append(f"Total rows: {len(table['rows'])}")
    
    return "\n".join(output)


def filter_rows(rows, where_clause):
    """Enhanced WHERE filtering with multiple operators"""
    
    where_upper = where_clause.upper()

    if "LIKE" in where_upper:
        operator = "LIKE"
        parts = where_clause.split(" LIKE ", 1) if " LIKE " in where_clause else where_clause.split(" like ", 1)
    elif ">=" in where_clause:
        operator = ">="
        parts = where_clause.split(">=")
    elif "<=" in where_clause:
        operator = "<="
        parts = where_clause.split("<=")
    elif "!=" in where_clause:
        operator = "!="
        parts = where_clause.split("!=")
    elif "<>" in where_clause:
        operator = "!="
        parts = where_clause.split("<>")
    elif ">" in where_clause:
        operator = ">"
        parts = where_clause.split(">")
    elif "<" in where_clause:
        operator = "<"
        parts = where_clause.split("<")
    elif "=" in where_clause:
        operator = "="
        parts = where_clause.split("=")
    else:
        raise ValueError(f"Unsupported WHERE operator in: {where_clause}")
    
    col_name = parts[0].strip()
    value = parts[1].strip().strip("'\"")
    
    # Filter based on operator
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

def format_table(rows, columns=None, schema_columns=None):
    """
    rows: list[dict]
    columns: "*" or list of column names
    """

    if not rows:
        return "No rows found."

    # Determine columns
    if columns == "*" or columns is None:
        headers = list(rows[0].keys())
    else:
        headers = columns

    # Calculate column widths
    col_widths = {}
    for h in headers:
        max_width = len(h)
        for row in rows:
            value = str(row.get(h, ""))
            max_width = max(max_width, len(value))
        col_widths[h] = max_width

    # Build header
    header_line = " | ".join(h.ljust(col_widths[h]) for h in headers)
    separator = "-" * len(header_line)

    # Build rows
    row_lines = []
    for row in rows:
        line = " | ".join(
            str(row.get(h, "")).ljust(col_widths[h]) for h in headers
        )
        row_lines.append(line)

    return "\n".join([header_line, separator] + row_lines + [f"\n{len(rows)} row(s) returned."])

def update_table(parsed, db):
    """UPDATE tablename SET col = value, col2 = value2 WHERE condition"""
    table_name = parsed["table"]
    updates = parsed.get("updates", {})  # Dictionary of {column: value}
    where_clause = parsed.get("where")
    
    # Backwards compatibility: handle old single-column format
    if not updates and "column" in parsed and "value" in parsed:
        updates = {parsed["column"]: parsed["value"]}
    
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
    
    # Update rows - ACTUALLY UPDATE THE DATA
    for row in rows_to_update:
        for column, value in updates.items():
            row[column] = value  # Update each column
    
    # Update indexes for each column
    for column, value in updates.items():
        update_indexes_on_update(db, table_name, rows_to_update, column, value)
    
    actual_name = db.get_table_name(table_name)
    return f"✓ {len(rows_to_update)} row(s) updated in '{actual_name}'."

def delete_from(parsed, db):
    """DELETE FROM tablename WHERE condition"""
    table_name = parsed["table"]
    where_clause = parsed.get("where")

    table = db.get_table(table_name)
    if not table:
        return f"Error: Table '{table_name}' does not exist"

    rows = table["rows"]

    # Determine rows to delete (ALWAYS COPY)
    if where_clause:
        rows_to_delete = filter_rows(rows, where_clause)
    else:
        rows_to_delete = rows[:]

    if not rows_to_delete:
        return "0 row(s) deleted."

    # === FOREIGN KEY HANDLING (ON DELETE SET NULL) ===
    for other_table_name, other_table in db.tables.items():
        for col in other_table["columns"]:
            fk = col.get("foreign_key")
            if not fk:
                continue

            if fk["ref_table"] != table_name:
                continue

            fk_column = col["name"]
            ref_column = fk["ref_column"]

            for deleted_row in rows_to_delete:
                deleted_value = deleted_row.get(ref_column)

                for row in other_table["rows"]:
                    if row.get(fk_column) == deleted_value:
                        row[fk_column] = None

                        update_indexes_on_update(
                            db,
                            other_table_name,
                            [row],
                            fk_column,
                            None
                        )

    # Update indexes for deleted rows
    update_indexes_on_delete(db, table_name, rows_to_delete)

    # Delete rows safely
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


