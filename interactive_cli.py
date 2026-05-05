"""
Interactive SQL-to-MongoDB Transpiler CLI

User-friendly command-line interface for converting SQL queries to MongoDB queries.
"""

import json
import sys
from typing import Optional
from sql_to_mongodb_transpiler import (
    SchemaMapping,
    SQLToMongoDBTranspiler,
    UnsupportedSQLException,
    SchemaMappingException,
    InvalidQueryException,
)


class InteractiveTranspiler:
    """Interactive CLI for SQL-to-MongoDB transpiler."""
    
    def __init__(self):
        """Initialize the transpiler."""
        self.transpiler = None
        self.schema = None
        self.sample_schemas = self._create_sample_schemas()
        self.current_schema_name = None
    
    def _create_sample_schemas(self) -> dict:
        """Create sample schemas for quick testing."""
        schemas = {}
        
        # Schema 1: E-Commerce
        ecommerce = SchemaMapping()
        ecommerce.table_mapping = {
            "users": "users_collection",
            "products": "products_collection",
            "orders": "orders_collection",
        }
        ecommerce.column_mapping = {
            "users": {
                "id": "_id",
                "name": "full_name",
                "email": "email_address",
                "age": "user_age",
                "status": "account_status",
                "country": "country_code",
            },
            "products": {
                "id": "_id",
                "name": "product_name",
                "price": "product_price",
                "category": "product_category",
                "stock": "inventory_count",
            },
            "orders": {
                "id": "_id",
                "user_id": "user_reference",
                "product_id": "product_reference",
                "quantity": "order_quantity",
                "status": "order_status",
            },
        }
        schemas["ecommerce"] = ecommerce
        
        # Schema 2: Employee Management
        employees = SchemaMapping()
        employees.table_mapping = {
            "employees": "employees_collection",
            "departments": "departments_collection",
        }
        employees.column_mapping = {
            "employees": {
                "id": "_id",
                "name": "full_name",
                "email": "work_email",
                "salary": "annual_salary",
                "age": "employee_age",
                "dept_id": "department_id",
                "status": "employment_status",
            },
            "departments": {
                "id": "_id",
                "name": "dept_name",
                "budget": "dept_budget",
                "manager": "department_manager",
            },
        }
        schemas["employees"] = employees
        
        # Schema 3: Simple Users
        simple = SchemaMapping()
        simple.table_mapping = {
            "users": "users",
            "posts": "posts",
        }
        simple.column_mapping = {
            "users": {
                "id": "_id",
                "name": "name",
                "email": "email",
                "age": "age",
                "city": "city",
            },
            "posts": {
                "id": "_id",
                "user_id": "user_id",
                "title": "title",
                "content": "content",
                "status": "status",
            },
        }
        schemas["simple"] = simple
        
        return schemas
    
    def display_welcome(self):
        """Display welcome screen."""
        print("\n" + "="*70)
        print("  SQL-to-MongoDB Transpiler - Interactive CLI")
        print("="*70)
        print("\nWelcome! This tool converts SQL queries to MongoDB queries.")
        print("\nType 'help' for commands or 'schema' to select a schema.\n")
    
    def display_help(self):
        """Display help information."""
        print("\n" + "-"*70)
        print("AVAILABLE COMMANDS:")
        print("-"*70)
        print("  schema      - List and select a sample schema")
        print("  custom      - Create a custom schema")
        print("  query       - Enter a SQL query to transpile")
        print("  examples    - Show query examples")
        print("  help        - Show this help message")
        print("  clear       - Clear screen")
        print("  exit/quit   - Exit the application")
        print("-"*70 + "\n")
    
    def display_schemas(self):
        """Display available sample schemas."""
        print("\n" + "-"*70)
        print("AVAILABLE SAMPLE SCHEMAS:")
        print("-"*70)
        for i, (name, _) in enumerate(self.sample_schemas.items(), 1):
            marker = " ← CURRENT" if name == self.current_schema_name else ""
            print(f"  {i}. {name}{marker}")
        print("-"*70 + "\n")
        
        choice = input("Select schema (number/name) or press Enter to skip: ").strip()
        
        if not choice:
            return
        
        if choice.isdigit():
            schemas_list = list(self.sample_schemas.keys())
            idx = int(choice) - 1
            if 0 <= idx < len(schemas_list):
                schema_name = schemas_list[idx]
                self.schema = self.sample_schemas[schema_name]
                self.transpiler = SQLToMongoDBTranspiler(self.schema)
                self.current_schema_name = schema_name
                print(f"\n✓ Schema '{schema_name}' loaded successfully!")
                self._display_schema_details()
            else:
                print("✗ Invalid selection!")
        else:
            if choice in self.sample_schemas:
                self.schema = self.sample_schemas[choice]
                self.transpiler = SQLToMongoDBTranspiler(self.schema)
                self.current_schema_name = choice
                print(f"\n✓ Schema '{choice}' loaded successfully!")
                self._display_schema_details()
            else:
                print("✗ Schema not found!")
    
    def _display_schema_details(self):
        """Display details of current schema."""
        if not self.schema:
            return
        
        print("\nSchema Details:")
        print("-" * 40)
        
        for table, collection in self.schema.table_mapping.items():
            print(f"\nTable: {table} → Collection: {collection}")
            if table in self.schema.column_mapping:
                columns = self.schema.column_mapping[table]
                for sql_col, mongo_field in columns.items():
                    print(f"  • {sql_col} → {mongo_field}")
    
    def display_examples(self):
        """Display example queries."""
        print("\n" + "-"*70)
        print("EXAMPLE QUERIES:")
        print("-"*70)
        
        if not self.schema:
            print("No schema selected! Please select a schema first.")
            return
        
        examples = [
            ("Simple SELECT", "SELECT * FROM users"),
            ("Specific columns", "SELECT name, email FROM users"),
            ("WHERE clause", "SELECT * FROM users WHERE age > 25"),
            ("AND condition", "SELECT * FROM users WHERE age > 18 AND age < 65"),
            ("OR condition", "SELECT * FROM users WHERE status = 'active' OR status = 'pending'"),
            ("IN operator", "SELECT * FROM users WHERE country IN ('US', 'CA', 'UK')"),
            ("Complex nested", "SELECT * FROM users WHERE (age > 21 AND status = 'active') OR country = 'US'"),
            ("LIMIT", "SELECT * FROM users LIMIT 10"),
            ("LIMIT OFFSET", "SELECT * FROM users LIMIT 10 OFFSET 5"),
        ]
        
        for i, (desc, query) in enumerate(examples, 1):
            print(f"\n{i}. {desc}:")
            print(f"   {query}")
        
        print("\n" + "-"*70 + "\n")
    
    def create_custom_schema(self):
        """Create a custom schema interactively."""
        print("\n" + "-"*70)
        print("CREATE CUSTOM SCHEMA")
        print("-"*70)
        
        self.schema = SchemaMapping()
        
        # Add tables
        print("\nDefine your schema:")
        print("Enter table mappings (format: sql_table=mongodb_collection)")
        print("Press Enter when done.\n")
        
        while True:
            mapping = input("Table mapping (or press Enter to skip): ").strip()
            if not mapping:
                break
            
            if "=" not in mapping:
                print("✗ Invalid format! Use: sql_table=mongodb_collection")
                continue
            
            sql_table, mongo_coll = mapping.split("=", 1)
            self.schema.table_mapping[sql_table.strip()] = mongo_coll.strip()
            print(f"✓ Added: {sql_table.strip()} → {mongo_coll.strip()}")
        
        # Add column mappings
        print("\nNow define column mappings for each table:")
        print("Format: table.sql_column=mongodb_field\n")
        
        for table in self.schema.table_mapping.keys():
            self.schema.column_mapping[table] = {}
            print(f"\nColumns for table '{table}':")
            print("(Press Enter when done)\n")
            
            while True:
                mapping = input(f"  {table}: ").strip()
                if not mapping:
                    break
                
                if "=" not in mapping:
                    print("  ✗ Invalid format! Use: sql_column=mongodb_field")
                    continue
                
                sql_col, mongo_field = mapping.split("=", 1)
                self.schema.column_mapping[table][sql_col.strip()] = mongo_field.strip()
                print(f"  ✓ Added: {sql_col.strip()} → {mongo_field.strip()}")
        
        self.transpiler = SQLToMongoDBTranspiler(self.schema)
        self.current_schema_name = "custom"
        print("\n✓ Custom schema created successfully!")
    
    def transpile_query(self):
        """Interactive query input and transpilation."""
        if not self.transpiler:
            print("✗ No schema loaded! Please select or create a schema first.")
            return
        
        print("\n" + "-"*70)
        print("ENTER SQL QUERY")
        print("-"*70)
        print("Type your SQL query (or 'back' to return):\n")
        
        query = input("SQL> ").strip()
        
        if query.lower() == "back":
            return
        
        if not query:
            print("✗ Please enter a query!")
            return
        
        try:
            result = self.transpiler.transpile(query)
            self._display_result(query, result)
        except (UnsupportedSQLException, SchemaMappingException, InvalidQueryException) as e:
            print(f"\n✗ Error: {str(e)}")
        except Exception as e:
            print(f"\n✗ Unexpected error: {str(e)}")
    
    def _display_result(self, sql_query: str, result: dict):
        """Display transpilation result."""
        print("\n" + "="*70)
        print("TRANSPILATION RESULT")
        print("="*70)
        
        print("\n📝 SQL Query:")
        print(f"   {sql_query}")
        
        print("\n📊 MongoDB Query:")
        print(json.dumps(result, indent=2))
        
        print("\n" + "="*70 + "\n")
    
    def run(self):
        """Main CLI loop."""
        self.display_welcome()
        
        while True:
            try:
                command = input("\n> ").strip().lower()
                
                if command in ("exit", "quit", "q"):
                    print("\nGoodbye! 👋\n")
                    break
                elif command == "help" or command == "?":
                    self.display_help()
                elif command == "schema":
                    self.display_schemas()
                elif command == "custom":
                    self.create_custom_schema()
                elif command == "query":
                    self.transpile_query()
                elif command == "examples":
                    self.display_examples()
                elif command == "clear":
                    self._clear_screen()
                elif command == "":
                    continue
                else:
                    # Treat as direct SQL query if contains SELECT
                    if "select" in command.lower():
                        result = self.transpiler.transpile(command)
                        self._display_result(command, result)
                    else:
                        print("✗ Unknown command! Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.\n")
            except Exception as e:
                print(f"✗ Error: {str(e)}")
    
    def _clear_screen(self):
        """Clear the screen."""
        os_clear = 'cls' if sys.platform == 'win32' else 'clear'
        import os
        os.system(os_clear)


def main():
    """Entry point."""
    cli = InteractiveTranspiler()
    cli.run()


if __name__ == "__main__":
    main()
