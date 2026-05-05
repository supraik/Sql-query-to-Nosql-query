"""
Advanced Usage Examples for SQL-to-MongoDB Transpiler

This file demonstrates real-world usage patterns and advanced features.
"""

import json
from sql_to_mongodb_transpiler import (
    SchemaMapping,
    SQLToMongoDBTranspiler,
    QueryParser,
    WhereClauseParser,
    MongoGenerator,
)


def example_1_basic_setup():
    """Example 1: Basic transpiler setup and simple queries."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Setup and Simple Queries")
    print("="*70 + "\n")
    
    # Create schema mapping
    schema = SchemaMapping()
    schema.table_mapping = {
        "employees": "employees_collection",
        "departments": "departments_collection",
    }
    schema.column_mapping = {
        "employees": {
            "id": "_id",
            "name": "full_name",
            "email": "work_email",
            "salary": "annual_salary",
            "dept_id": "department_id",
        },
        "departments": {
            "id": "_id",
            "name": "dept_name",
            "budget": "dept_budget",
        },
    }
    
    # Create transpiler
    transpiler = SQLToMongoDBTranspiler(schema)
    
    # Test queries
    queries = [
        "SELECT * FROM employees",
        "SELECT name, email FROM employees",
        "SELECT * FROM employees WHERE salary > 50000",
    ]
    
    for query in queries:
        result = transpiler.transpile(query)
        print(f"SQL: {query}")
        print(f"MongoDB:\n{json.dumps(result, indent=2)}\n")


def example_2_where_clause_patterns():
    """Example 2: Various WHERE clause patterns."""
    print("\n" + "="*70)
    print("EXAMPLE 2: WHERE Clause Patterns")
    print("="*70 + "\n")
    
    schema = SchemaMapping()
    schema.table_mapping = {"users": "users"}
    schema.column_mapping = {
        "users": {
            "id": "_id",
            "age": "user_age",
            "status": "account_status",
            "country": "country_code",
        }
    }
    
    transpiler = SQLToMongoDBTranspiler(schema)
    
    patterns = [
        ("Simple equality", "SELECT * FROM users WHERE status = 'active'"),
        ("Greater than", "SELECT * FROM users WHERE age > 18"),
        ("AND condition", "SELECT * FROM users WHERE age > 18 AND age < 65"),
        ("OR condition", "SELECT * FROM users WHERE status = 'active' OR status = 'pending'"),
        ("IN operator", "SELECT * FROM users WHERE country IN ('US', 'CA', 'UK')"),
        ("Complex nested", "SELECT * FROM users WHERE (age > 21 AND status = 'active') OR country = 'US'"),
    ]
    
    for description, query in patterns:
        result = transpiler.transpile(query)
        print(f"{description}:")
        print(f"  SQL: {query}")
        print(f"  Filter: {json.dumps(result['filter'], indent=4)}\n")


def example_3_pagination():
    """Example 3: Pagination with LIMIT and OFFSET."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Pagination (LIMIT and OFFSET)")
    print("="*70 + "\n")
    
    schema = SchemaMapping()
    schema.table_mapping = {"products": "products"}
    schema.column_mapping = {
        "products": {
            "id": "_id",
            "name": "product_name",
            "price": "product_price",
            "category": "product_category",
        }
    }
    
    transpiler = SQLToMongoDBTranspiler(schema)
    
    queries = [
        ("LIMIT only", "SELECT * FROM products LIMIT 10"),
        ("LIMIT with OFFSET", "SELECT * FROM products LIMIT 10 OFFSET 20"),
        ("With WHERE and pagination", "SELECT * FROM products WHERE price > 50 LIMIT 5 OFFSET 10"),
    ]
    
    for description, query in queries:
        result = transpiler.transpile(query)
        print(f"{description}:")
        print(f"  SQL: {query}")
        if result['type'] == 'aggregation':
            print(f"  Type: Aggregation Pipeline")
            print(f"  Pipeline: {json.dumps(result['pipeline'], indent=4)}")
        else:
            print(f"  Type: Find Query")
            print(f"  Filter: {json.dumps(result['filter'], indent=4)}")
        print()


def example_4_column_selection():
    """Example 4: Selecting specific columns with projections."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Column Selection and Projections")
    print("="*70 + "\n")
    
    schema = SchemaMapping()
    schema.table_mapping = {"customers": "customers_collection"}
    schema.column_mapping = {
        "customers": {
            "id": "_id",
            "first_name": "fname",
            "last_name": "lname",
            "email": "contact_email",
            "phone": "phone_number",
            "address": "mailing_address",
        }
    }
    
    transpiler = SQLToMongoDBTranspiler(schema)
    
    queries = [
        "SELECT first_name, last_name FROM customers",
        "SELECT first_name, email FROM customers WHERE id = 1",
        "SELECT * FROM customers",
    ]
    
    for query in queries:
        result = transpiler.transpile(query)
        print(f"SQL: {query}")
        print(f"Projection: {json.dumps(result['projection'], indent=2)}\n")


def example_5_complex_business_logic():
    """Example 5: Complex real-world business logic."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Complex Business Logic")
    print("="*70 + "\n")
    
    schema = SchemaMapping()
    schema.table_mapping = {
        "orders": "orders",
        "customers": "customers",
    }
    schema.column_mapping = {
        "orders": {
            "id": "_id",
            "customer_id": "cust_id",
            "amount": "order_amount",
            "status": "order_status",
            "date": "created_date",
        },
        "customers": {
            "id": "_id",
            "name": "customer_name",
            "tier": "customer_tier",
            "country": "country_code",
        }
    }
    
    transpiler = SQLToMongoDBTranspiler(schema)
    
    # Real-world business queries
    business_queries = [
        ("High-value pending orders", 
         "SELECT * FROM orders WHERE status = 'pending' AND amount > 10000"),
        
        ("Premium tier customers in specific regions",
         "SELECT * FROM customers WHERE tier = 'premium' AND country IN ('US', 'CA', 'UK')"),
        
        ("Recent orders needing processing",
         "SELECT * FROM orders WHERE status = 'pending' OR status = 'processing' LIMIT 50 OFFSET 0"),
        
        ("Orders with complex business rules",
         "SELECT * FROM orders WHERE (amount > 5000 AND status = 'pending') OR (amount > 100000 AND status = 'shipped')"),
    ]
    
    for description, query in business_queries:
        result = transpiler.transpile(query)
        print(f"Query: {description}")
        print(f"SQL: {query}")
        print(f"MongoDB Query Type: {result['type']}")
        print(f"Filter: {json.dumps(result['filter'], indent=2)}")
        if result['type'] == 'aggregation':
            print(f"Pipeline: {json.dumps(result.get('pipeline', []), indent=2)}")
        print()


def example_6_error_handling():
    """Example 6: Error handling and edge cases."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Error Handling")
    print("="*70 + "\n")
    
    schema = SchemaMapping()
    schema.table_mapping = {"users": "users"}
    schema.column_mapping = {
        "users": {
            "id": "_id",
            "name": "user_name",
            "age": "user_age",
        }
    }
    
    transpiler = SQLToMongoDBTranspiler(schema)
    
    # Test cases with expected errors
    test_cases = [
        ("Valid query", "SELECT * FROM users"),
        ("Unmapped table", "SELECT * FROM unknown_table"),
        ("Invalid SQL", "INVALID SQL SYNTAX"),
    ]
    
    for description, query in test_cases:
        try:
            result = transpiler.transpile(query)
            print(f"[PASS] {description}")
            print(f"  Result: Success\n")
        except Exception as e:
            print(f"[FAIL] {description}")
            print(f"  Exception: {type(e).__name__}")
            print(f"  Message: {str(e)}\n")


def example_7_debug_tokenization():
    """Example 7: Debugging tokenization for complex queries."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Debug Tokenization")
    print("="*70 + "\n")
    
    sql = "SELECT name, age FROM users WHERE age > 18 AND status = 'active' LIMIT 10"
    
    print(f"Query: {sql}\n")
    
    parser = QueryParser(sql)
    
    print(f"DML Action: {parser.get_dml_action().value}")
    print(f"Table: {parser.extract_from_clause()}")
    print(f"Columns: {parser.extract_select_columns()}")
    print(f"WHERE Clause: {parser.extract_where_clause()}")
    print(f"LIMIT: {parser.extract_limit_clause()}")
    print(f"OFFSET: {parser.extract_offset_clause()}")
    print(f"Has JOINs: {parser.has_join()}")


def example_8_manual_where_parsing():
    """Example 8: Manual WHERE clause parsing for debugging."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Manual WHERE Clause Parsing")
    print("="*70 + "\n")
    
    schema = SchemaMapping()
    schema.table_mapping = {"products": "products"}
    schema.column_mapping = {
        "products": {
            "id": "_id",
            "price": "product_price",
            "stock": "quantity_in_stock",
            "status": "product_status",
        }
    }
    
    where_parser = WhereClauseParser(schema, "products")
    
    # Test various WHERE clause patterns
    conditions = [
        "price > 100",
        "price > 50 AND price < 200",
        "status = 'active' OR status = 'discontinued'",
        "(price > 100 AND stock > 10) OR status = 'clearance'",
    ]
    
    for condition in conditions:
        result = where_parser.parse(condition)
        print(f"Condition: {condition}")
        print(f"MongoDB Query: {json.dumps(result, indent=2)}\n")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("SQL-TO-MONGODB TRANSPILER - ADVANCED USAGE EXAMPLES")
    print("="*70)
    
    example_1_basic_setup()
    example_2_where_clause_patterns()
    example_3_pagination()
    example_4_column_selection()
    example_5_complex_business_logic()
    example_6_error_handling()
    example_7_debug_tokenization()
    example_8_manual_where_parsing()
    
    print("\n" + "="*70)
    print("All examples completed successfully!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
