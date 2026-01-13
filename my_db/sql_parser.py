# my_db/sql_parser.py

def parse(command: str):
    """Parse SQL commands"""
    command = command.rstrip(";").strip()

    tokens = command.strip().split()
    
    if not tokens:
        raise ValueError("Empty command")
    
    command_type = tokens[0].upper()
    
    # SHOW TABLES
    if command_type == "SHOW" and len(tokens) > 1 and tokens[1].upper() == "TABLES":
        return {"type": "SHOW_TABLES"}
    
    # DESCRIBE tablename
    elif command_type == "DESCRIBE" or command_type == "DESC":
        if len(tokens) < 2:
            raise ValueError("DESCRIBE requires table name")
        return {
            "type": "DESCRIBE",
            "table": tokens[1]
        }
    
    # CREATE TABLE
    elif command_type == "CREATE" and len(tokens) > 1 and tokens[1].upper() == "TABLE":
        return parse_create_table(command)  # PASS command here!
    
    # INSERT INTO
    elif command_type == "INSERT" and len(tokens) > 1 and tokens[1].upper() == "INTO":
        return parse_insert(command)  
    
    # SELECT
    elif command_type == "SELECT":
        return parse_select(command)  
    
    # UPDATE
    elif command_type == "UPDATE":
        return parse_update(command)
    
    # DELETE column from table
    elif command_type == "DELETE":
        return parse_delete(command)
    
    # delete table
    elif command_type == "DROP" and len(tokens) > 1 and tokens[1].upper() == "TABLE":
        return parse_drop_table(command)
    
    else:
        raise ValueError(f"Unknown command: {command_type}")


def parse_create_table(command):
    """
    Parse: CREATE TABLE tablename (col1 TYPE, col2 TYPE, ...)
    Example: CREATE TABLE suppliers (id INT PRIMARY KEY, name VARCHAR, email VARCHAR)
    """
    try:
        # Split by opening parenthesis
        if "(" not in command:
            raise ValueError("Missing column definitions in parentheses")
        
        # Extract table name
        parts = command.split("(", 1)
        table_part = parts[0].strip().split()
        
        if len(table_part) < 3:
            raise ValueError("Invalid CREATE TABLE syntax")
        
        table_name = table_part[2]  # CREATE TABLE [name]
        
        # Extract columns definition
        columns_str = parts[1].rstrip(");").strip()
        
        # Split columns by comma
        column_defs = [col.strip() for col in columns_str.split(",")]
        
        columns = []
        for col_def in column_defs:
            tokens = col_def.split()
            
            if len(tokens) < 2:
                raise ValueError(f"Invalid column definition: {col_def}")
            
            col_name = tokens[0]
            col_type = tokens[1].upper()
            
            # Check for PRIMARY KEY
            is_primary = "PRIMARY" in col_def.upper() and "KEY" in col_def.upper()
            
            # Check for UNIQUE
            is_unique = "UNIQUE" in col_def.upper()
            
            columns.append({
                "name": col_name,
                "type": col_type,
                "primary_key": is_primary,
                "unique": is_unique
            })
        
        return {
            "type": "CREATE_TABLE",
            "table": table_name,
            "columns": columns
        }
    
    except Exception as e:
        raise ValueError(f"Error parsing CREATE TABLE: {e}")


def parse_insert(command):
    """
    Parse: INSERT INTO tablename VALUES (val1, val2, ...)
    Example: INSERT INTO suppliers VALUES (1, 'TechSupply', 'tech@example.com')
    """
    try:
        if "VALUES" not in command.upper():
            raise ValueError("Missing VALUES keyword")
        
        parts = command.split("VALUES", 1)
        
        # Extract table name
        table_name = parts[0].replace("INSERT INTO", "").replace("insert into", "").strip()
        
        # Extract values
        values_str = parts[1].strip().strip("();")
        
        # Parse values (handle quotes)
        values = []
        current_value = ""
        in_quotes = False
        quote_char = None
        
        for char in values_str:
            if char in ("'", '"') and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == "," and not in_quotes:
                values.append(current_value.strip().strip("'\""))
                current_value = ""
                continue
            else:
                current_value += char
        
        # Add last value
        if current_value.strip():
            values.append(current_value.strip().strip("'\""))
        
        return {
            "type": "INSERT",
            "table": table_name,
            "values": values
        }
    
    except Exception as e:
        raise ValueError(f"Error parsing INSERT: {e}")


def parse_select(command):
    """
    Parse: SELECT * FROM tablename
    Parse: SELECT col1, col2 FROM tablename
    Parse: SELECT * FROM tablename WHERE column = value
    """
    try:
        # command = command.rstrip(";").strip()
        command_upper = command.upper()
        
        if "FROM" not in command_upper:
            raise ValueError("Missing FROM keyword")
        
        parts = command_upper.split("FROM")
        
        # Extract columns
        columns_str = parts[0].replace("SELECT", "").strip()
        columns = "*" if columns_str == "*" else [c.strip() for c in columns_str.split(",")]
        
        # Extract table name and WHERE clause
        table_part = parts[1].strip().split("WHERE")
        table_name = table_part[0].strip()
        
        where_clause = None
        if len(table_part) > 1:
            # Get the WHERE clause from original command (preserve case)
            where_index = command.upper().index("WHERE") + 5
            where_clause = command[where_index:].strip()
        
        return {
            "type": "SELECT",
            "table": table_name,
            "columns": columns,
            "where": where_clause
        }
    
    except Exception as e:
        raise ValueError(f"Error parsing SELECT: {e}")


def parse_update(command):
    """
    Parse: UPDATE tablename SET col = value WHERE condition
    Example: UPDATE suppliers SET email = 'new@email.com' WHERE id = 1
    """
    try:
        command_upper = command.upper()
        
        if "SET" not in command_upper:
            raise ValueError("Missing SET keyword")
        
        # Extract table name (between UPDATE and SET)
        update_to_set = command[:command_upper.index("SET")].strip()
        table_name = update_to_set.replace("UPDATE", "").replace("update", "").strip()
        
        # Get everything after SET
        set_start = command_upper.index("SET") + 3
        rest = command[set_start:].strip()
        
        # Check for WHERE clause
        where_clause = None
        if "WHERE" in rest.upper():
            where_index = rest.upper().index("WHERE")
            set_clause = rest[:where_index].strip()
            where_clause = rest[where_index + 5:].strip()
        else:
            set_clause = rest
        
        # Parse SET clause: "email = 'new@email.com'"
        if "=" not in set_clause:
            raise ValueError("Invalid SET clause format")
        
        set_parts = set_clause.split("=", 1)  # Split only on first =
        column = set_parts[0].strip()
        value = set_parts[1].strip().strip("'\"")
        
        return {
            "type": "UPDATE",
            "table": table_name,
            "column": column,
            "value": value,
            "where": where_clause
        }
    
    except Exception as e:
        raise ValueError(f"Error parsing UPDATE: {str(e)}")


def parse_delete(command):
    """
    Parse: DELETE FROM tablename WHERE condition
    Example: DELETE FROM suppliers WHERE id = 1
    """
    try:
        command_upper = command.upper()
        
        if "FROM" not in command_upper:
            raise ValueError("Missing FROM keyword")
        
        parts = command_upper.split("FROM")
        table_part = parts[1].strip().split("WHERE")
        table_name = table_part[0].strip()
        
        where_clause = None
        if len(table_part) > 1:
            # Get WHERE clause from original command
            where_index = command.upper().index("WHERE") + 5
            where_clause = command[where_index:].strip()
        
        return {
            "type": "DELETE",
            "table": table_name,
            "where": where_clause
        }
    
    except Exception as e:
        raise ValueError(f"Error parsing DELETE: {e}")
    

def parse_drop_table(command):
    """
    Parse: DROP TABLE tablename
    """
    try:
        command_upper = command.upper()
        if "TABLE" not in command_upper:
            raise ValueError("Missing TABLE keyword")

        table_name = command_upper.split("TABLE")[1].strip()
        return {
            "type": "DROP_TABLE",
            "table": table_name
        }
    except Exception as e:
        raise ValueError(f"Error parsing DROP TABLE: {e}")
    
    