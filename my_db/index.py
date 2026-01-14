# my_db/index.py

def create_index(db, table_name, index_name, column):
    """
    Create an index on a table column
    
    Args:
        db: Database instance
        table_name: Name of the table
        index_name: Name for the index
        column: Column to index
    
    Returns:
        Success/error message
    """
    table = db.get_table(table_name)

    if not table:
        return f"Error: Table '{table_name}' does not exist"

    # Lowercase for comparison
    column_lower = column.lower()
    
    # Find the ACTUAL column name as stored in table schema
    actual_column_name = None
    for col in table["columns"]:
        if col["name"].lower() == column_lower:
            actual_column_name = col["name"]
            break
    
    if not actual_column_name:
        return f"Error: Column '{column}' does not exist in table '{table_name}'"

    # DEBUG: Print what we're looking for
    print(f"[DEBUG] Creating index on column: '{actual_column_name}'")
    print(f"[DEBUG] First row keys: {list(table['rows'][0].keys()) if table['rows'] else 'No rows'}")
    
    # Build index using the ACTUAL column name from rows
    index_map = {}
    for row in table["rows"]:
        # Try to get value with actual case
        value = row.get(actual_column_name)
        
        # DEBUG: Show what we found
        print(f"[DEBUG] Row: {row}, Looking for '{actual_column_name}', Found: '{value}'")
        
        if value is not None:
            index_map.setdefault(value, []).append(row)

    # Store index with LOWERCASE column name as key
    table_key = table_name.lower()
    if table_key not in db.indexes:
        db.indexes[table_key] = {}

    # KEY POINT: Use column_lower as the dictionary key!
    db.indexes[table_key][column_lower] = {
        "name": index_name,
        "column": actual_column_name,
        "map": index_map,
    }

    actual_table_name = db.get_table_name(table_name)
    
    # DEBUG: Show what was created
    print(f"[DEBUG] Index created: table_key='{table_key}', column_key='{column_lower}'")
    print(f"[DEBUG] Index map: {index_map}")
    
    return f"✓ Index '{index_name}' created on column '{actual_column_name}' in table '{actual_table_name}'."


def update_indexes_on_insert(db, table_name, row):
    """Update all indexes when a row is inserted"""
    table_key = table_name.lower()
    if table_key in db.indexes:
        for column, index_data in db.indexes[table_key].items():
            actual_col = index_data["column"]
            value = row.get(actual_col)
            if value is not None:
                index_data["map"].setdefault(value, []).append(row)


def update_indexes_on_update(db, table_name, rows_to_update, column, new_value):
    """Update indexes when rows are updated"""
    table_key = table_name.lower()
    column_lower = column.lower()
    
    if table_key in db.indexes and column_lower in db.indexes[table_key]:
        index_data = db.indexes[table_key][column_lower]
        actual_col = index_data["column"]
        
        # Remove old values from index
        for row in rows_to_update:
            old_value = row.get(actual_col)
            if old_value in index_data["map"]:
                index_data["map"][old_value].remove(row)
                if not index_data["map"][old_value]:
                    del index_data["map"][old_value]
        
        # Update rows and add new values to index
        for row in rows_to_update:
            row[actual_col] = new_value
            index_data["map"].setdefault(new_value, []).append(row)


def update_indexes_on_delete(db, table_name, rows_to_delete):
    """Update all indexes when rows are deleted"""
    table_key = table_name.lower()
    if table_key in db.indexes:
        for column, index_data in db.indexes[table_key].items():
            actual_col = index_data["column"]
            for row in rows_to_delete:
                value = row.get(actual_col)
                if value in index_data["map"]:
                    index_data["map"][value].remove(row)
                    if not index_data["map"][value]:
                        del index_data["map"][value]

def lookup_by_index(db, table_name, column, value):
    """
    Attempt to fetch matching rows using an index.
    """
    table_key = table_name.lower()
    column_key = column.lower()

    table_indexes = db.indexes.get(table_key)
    if not table_indexes:
        return None

    index_data = table_indexes.get(column_key)
    if not index_data:
        return None

    return index_data["map"].get(value, [])