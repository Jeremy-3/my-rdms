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
    elif command_type == "CREATE" and tokens[1].upper() == "INDEX":
        return parse_create_index(command)
    else:
        raise ValueError(f"Unknown command: {command_type}")


def parse_create_table(command):
    """
    Parse: CREATE TABLE tablename (col1 TYPE, col2 TYPE, ...)
    Example: CREATE TABLE suppliers (id INT PRIMARY KEY, name VARCHAR, email VARCHAR)
    Parse: CREATE TABLE with PRIMARY KEY, UNIQUE, and FOREIGN KEY
    Example: CREATE TABLE products (id INT PRIMARY KEY, name VARCHAR, supplier_id INT FOREIGN KEY REFERENCES suppliers(id))
    """
    try:
        command = command.strip().rstrip(";")

        if "(" not in command:
            raise ValueError("Missing column definitions in parentheses")
        
        # Split table name and column definitions
        head, body = command.split("(", 1)
        table_name = head.split()[2].lower()
        
        # Remove trailing semicolon and closing parenthesis
        last_paren_idx = body.rfind(")")
        if last_paren_idx == -1:
            raise ValueError("Missing closing parenthesis")
        
        columns_str = body[:last_paren_idx].strip()
        
        
        column_defs = []
        current_def = ""
        paren_depth = 0
        
        for char in columns_str:
            if char == '(':
                paren_depth += 1
                current_def += char
            elif char == ')':
                paren_depth -= 1
                current_def += char
            elif char == ',' and paren_depth == 0:
                column_defs.append(current_def.strip())
                current_def = ""
            else:
                current_def += char
        
        # Don't forget the last column
        if current_def.strip():
            column_defs.append(current_def.strip())
        
        columns = []
        foreign_keys = []
        
        for col_def in column_defs:
            tokens = col_def.strip().split()
            
            if len(tokens) < 2:
                raise ValueError(f"Invalid column definition: {col_def}")
            
            col_name = tokens[0]
            col_type = tokens[1].upper()
            col_def_upper = col_def.upper()
            
            is_primary = "PRIMARY KEY" in col_def_upper or "PRIMARY" in col_def_upper and "KEY" in col_def_upper
            is_unique = "UNIQUE" in col_def_upper
            
            # Parse FOREIGN KEY
            fk_info = None
            if "REFERENCES" in col_def_upper:
                # Extract: REFERENCES suppliers(id)
                ref_part = col_def.split("REFERENCES", 1)[1].strip()
                
                if "(" not in ref_part or ")" not in ref_part:
                    raise ValueError(f"Invalid FOREIGN KEY REFERENCES syntax in: {col_def}")
                
                # Parse table_name(column_name)
                ref_table_name = ref_part.split("(")[0].strip().lower()
                ref_column_name = ref_part.split("(")[1].split(")")[0].strip().lower()
                
                fk_info = {
                    "ref_table": ref_table_name,
                    "ref_column": ref_column_name
                }
                
                foreign_keys.append({
                    "column": col_name,
                    "ref_table": ref_table_name,
                    "ref_column": ref_column_name
                })
            
            columns.append({
                "name": col_name,
                "type": col_type,
                "primary_key": is_primary,
                "unique": is_unique,
                "foreign_key": fk_info  
            })
        
        return {
            "type": "CREATE_TABLE",
            "table": table_name,
            "columns": columns,
            "foreign_keys": foreign_keys
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
    Parse: SELECT * FROM tablename JOIN table2 ON a = b
    """
    try:
        # command = command.rstrip(";").strip()
        command_upper = command.upper()
        
        if "FROM" not in command_upper:
            raise ValueError("Missing FROM keyword")
        
        #parts = command_upper.split("FROM")
        
        # select section
        select_part, rest = command_upper.split("FROM",1)
        columns_str = select_part.replace("SELECT","").strip()
        columns = ("*" if columns_str == "*" else [c.strip() for c in columns_str.split(",")])

        rest_upper = rest.upper()

        join = None
        where = None

        # join section
        if "JOIN" in rest_upper:
            from_part ,join_part = rest.split("JOIN",1)
            base_table = from_part.strip().lower()

            join_table_part , on_part = join_part.split("ON",1)
            join_table = join_table_part.strip().lower()

            if "=" not in on_part:
                raise ValueError("JOIN condition must use '=' ")
            
            left_expr, right_expr = on_part.split("=" ,1)

            join ={
                "table":join_table,
                "left":left_expr.strip().lower(),
                "right":right_expr.strip().lower()
            }
        else:
            base_table = rest.strip().lower()

        return{
            "type":"SELECT",
            "table":base_table,
            "columns":columns,
            "join":join,
            "where":where
        }
    except Exception as e:
        raise ValueError(f"Error pasring select: {e}")
    

def parse_update(command):
    """
    Parse: UPDATE tablename SET col = value, col2 = value2 WHERE condition
    Example: UPDATE suppliers SET email = 'new@email.com', name = 'John' WHERE id = 1
    Supports multiple column updates
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
        
        # Parse SET clause with multiple columns: "col1='value1', col2='value2'"
        if "=" not in set_clause:
            raise ValueError("Invalid SET clause format")
        
        # Split by comma, but be careful about quoted values
        set_assignments = []
        current_assignment = ""
        in_quotes = False
        quote_char = None
        
        for char in set_clause:
            if char in ("'", '"') and (not in_quotes or quote_char == char):
                in_quotes = not in_quotes
                quote_char = char if in_quotes else None
            
            if char == ',' and not in_quotes:
                if current_assignment.strip():
                    set_assignments.append(current_assignment.strip())
                current_assignment = ""
            else:
                current_assignment += char
        
        if current_assignment.strip():
            set_assignments.append(current_assignment.strip())
        
        # Parse each assignment
        updates = {}
        for assignment in set_assignments:
            if "=" not in assignment:
                raise ValueError(f"Invalid assignment format: {assignment}")
            
            parts = assignment.split("=", 1)
            column = parts[0].strip()
            value = parts[1].strip().strip("'\"")
            updates[column] = value
        
        return {
            "type": "UPDATE",
            "table": table_name,
            "updates": updates,  # Dictionary of {column: value}
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
    

# indexing tables 
def parse_create_index(command):
    """
    Parse: CREATE INDEX indexname ON tablename(column)
    """
    try:
        parts = command.split()
        index_name = parts[2]

        on_part = command.upper().split("ON", 1)[1].strip()
        table_part, column_part = on_part.split("(", 1)

        table_name = table_part.strip()
        column = column_part.rstrip(")").strip()

        return {
            "type": "CREATE_INDEX",
            "table": table_name,
            "index_name": index_name,
            "column": column
        }

    except Exception as e:
        raise ValueError(f"Error parsing CREATE INDEX: {e}")
