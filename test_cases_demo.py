"""
Comprehensive Test Cases and Expected Outputs for SQL-to-MongoDB Transpiler

This file demonstrates all supported SQL operations with expected MongoDB outputs.
Run this to see real examples of transpilation in action.
"""

import json
from sql_to_mongodb_transpiler import (
    SchemaMapping,
    SQLToMongoDBTranspiler,
    UnsupportedSQLException,
    SchemaMappingException,
    InvalidQueryException,
)


def print_test_case(test_name, sql, expected_output, actual_output, passed):
    """Pretty print test case results."""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"\n{'='*80}")
    print(f"{status} | {test_name}")
    print(f"{'='*80}")
    print(f"\nSQL Query:")
    print(f"   {sql}")
    print(f"\nExpected Output:")
    print(f"   {json.dumps(expected_output, indent=2)}")
    print(f"\nActual Output:")
    print(f"   {json.dumps(actual_output, indent=2)}")
    print(f"{'='*80}")


def create_test_schema():
    """Create schema for testing."""
    schema = SchemaMapping()
    
    schema.table_mapping = {
        "users": "users_collection",
        "orders": "orders_collection",
        "products": "products_collection",
    }
    
    schema.column_mapping = {
        "users": {
            "id": "_id",
            "name": "full_name",
            "email": "email_address",
            "age": "user_age",
            "status": "account_status",
        },
        "orders": {
            "id": "_id",
            "user_id": "customer_id",
            "product_id": "product_reference",
            "quantity": "order_quantity",
            "amount": "total_amount",
        },
        "products": {
            "id": "_id",
            "name": "product_name",
            "price": "product_price",
            "category": "product_category",
        },
    }
    
    return schema


def test_select_all():
    """Test Case 1: SELECT all records"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 1: SELECT ALL RECORDS")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "SELECT * FROM users"
    
    expected = {
        "collection": "users_collection",
        "type": "find",
        "filter": {},
        "projection": None,
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = (actual["collection"] == expected["collection"] and 
                 actual["filter"] == expected["filter"])
        print_test_case("SELECT * FROM users", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("SELECT * FROM users", sql, expected, str(e), False)
        return False


def test_select_specific_columns():
    """Test Case 2: SELECT specific columns"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 2: SELECT SPECIFIC COLUMNS")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "SELECT name, email FROM users"
    
    expected = {
        "collection": "users_collection",
        "type": "find",
        "filter": {},
        "projection": {
            "full_name": 1,
            "email_address": 1,
        },
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = (actual["collection"] == expected["collection"] and 
                 "full_name" in actual.get("projection", {}))
        print_test_case("SELECT specific columns", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("SELECT specific columns", sql, expected, str(e), False)
        return False


def test_select_where_single_condition():
    """Test Case 3: SELECT with WHERE (single condition)"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 3: SELECT WITH WHERE (SINGLE CONDITION)")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "SELECT * FROM users WHERE age = 25"
    
    expected = {
        "collection": "users_collection",
        "type": "find",
        "filter": {
            "user_age": {
                "$eq": 25
            }
        },
        "projection": None,
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = ("user_age" in actual["filter"] and 
                 "$eq" in actual["filter"]["user_age"])
        print_test_case("SELECT WHERE age = 25", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("SELECT WHERE age = 25", sql, expected, str(e), False)
        return False


def test_select_where_and_condition():
    """Test Case 4: SELECT with WHERE AND condition"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 4: SELECT WITH WHERE (AND CONDITION)")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "SELECT * FROM users WHERE age > 18 AND age < 65"
    
    expected = {
        "collection": "users_collection",
        "type": "find",
        "filter": {
            "user_age": {
                "$gt": 18,
                "$lt": 65
            }
        },
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = ("user_age" in actual["filter"] and 
                 "$gt" in actual["filter"]["user_age"] and
                 "$lt" in actual["filter"]["user_age"])
        print_test_case("SELECT WHERE age > 18 AND age < 65", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("SELECT WHERE age > 18 AND age < 65", sql, expected, str(e), False)
        return False


def test_select_where_or_condition():
    """Test Case 5: SELECT with WHERE OR condition"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 5: SELECT WITH WHERE (OR CONDITION)")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "SELECT * FROM users WHERE status = 'active' OR status = 'pending'"
    
    expected = {
        "collection": "users_collection",
        "type": "find",
        "filter": {
            "$or": [
                {"account_status": {"$eq": "active"}},
                {"account_status": {"$eq": "pending"}}
            ]
        },
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = ("$or" in actual["filter"] and 
                 len(actual["filter"]["$or"]) == 2)
        print_test_case("SELECT WHERE status OR", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("SELECT WHERE status OR", sql, expected, str(e), False)
        return False


def test_select_where_in_operator():
    """Test Case 6: SELECT with WHERE IN operator"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 6: SELECT WITH WHERE (IN OPERATOR)")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "SELECT * FROM orders WHERE product_id IN (1, 2, 3)"
    
    expected = {
        "collection": "orders_collection",
        "type": "find",
        "filter": {
            "product_reference": {
                "$in": [1, 2, 3]
            }
        },
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = ("product_reference" in actual["filter"] and 
                 "$in" in actual["filter"]["product_reference"])
        print_test_case("SELECT WHERE IN", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("SELECT WHERE IN", sql, expected, str(e), False)
        return False


def test_select_with_limit():
    """Test Case 7: SELECT with LIMIT"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 7: SELECT WITH LIMIT")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "SELECT * FROM users LIMIT 10"
    
    expected = {
        "collection": "users_collection",
        "type": "find",
        "filter": {},
        "limit": 10,
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = (actual.get("limit") == 10)
        print_test_case("SELECT LIMIT", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("SELECT LIMIT", sql, expected, str(e), False)
        return False


def test_select_with_limit_offset():
    """Test Case 8: SELECT with LIMIT and OFFSET"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 8: SELECT WITH LIMIT AND OFFSET")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "SELECT * FROM users LIMIT 10 OFFSET 5"
    
    expected = {
        "collection": "users_collection",
        "type": "aggregation",
        "pipeline": [
            {"$skip": 5},
            {"$limit": 10}
        ],
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = (actual["type"] == "aggregation" and 
                 "pipeline" in actual)
        print_test_case("SELECT LIMIT OFFSET", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("SELECT LIMIT OFFSET", sql, expected, str(e), False)
        return False


def test_insert_basic():
    """Test Case 9: INSERT statement"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 9: INSERT BASIC")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "INSERT INTO users (name, email, age) VALUES ('John Doe', 'john@example.com', 28)"
    
    expected = {
        "collection": "users_collection",
        "type": "insert",
        "document": {
            "full_name": "John Doe",
            "email_address": "john@example.com",
            "user_age": 28
        }
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = (actual["type"] == "insert" and 
                 actual["document"]["full_name"] == "John Doe")
        print_test_case("INSERT basic", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("INSERT basic", sql, expected, str(e), False)
        return False


def test_insert_multiple_records():
    """Test Case 10: INSERT with multiple values"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 10: INSERT WITH MULTIPLE VALUES")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "INSERT INTO products (name, price, category) VALUES ('Laptop', 999.99, 'Electronics')"
    
    expected = {
        "collection": "products_collection",
        "type": "insert",
        "document": {
            "product_name": "Laptop",
            "product_price": 999.99,
            "product_category": "Electronics"
        }
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = (actual["type"] == "insert" and 
                 actual["document"]["product_price"] == 999.99)
        print_test_case("INSERT multiple values", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("INSERT multiple values", sql, expected, str(e), False)
        return False


def test_update_basic():
    """Test Case 11: UPDATE basic"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 11: UPDATE BASIC")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "UPDATE users SET name = 'Jane Doe' WHERE id = 1"
    
    expected = {
        "collection": "users_collection",
        "type": "update",
        "filter": {
            "_id": {"$eq": 1}
        },
        "update": {
            "$set": {
                "full_name": "Jane Doe"
            }
        }
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = (actual["type"] == "update" and 
                 actual["update"]["$set"]["full_name"] == "Jane Doe" and
                 "_id" in actual["filter"])
        print_test_case("UPDATE basic", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("UPDATE basic", sql, expected, str(e), False)
        return False


def test_update_multiple_fields():
    """Test Case 12: UPDATE multiple fields"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 12: UPDATE MULTIPLE FIELDS")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "UPDATE users SET name = 'Jane Doe', age = 30, status = 'active' WHERE id = 5"
    
    expected = {
        "collection": "users_collection",
        "type": "update",
        "filter": {
            "_id": {"$eq": 5}
        },
        "update": {
            "$set": {
                "full_name": "Jane Doe",
                "user_age": 30,
                "account_status": "active"
            }
        }
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = (actual["type"] == "update" and 
                 len(actual["update"]["$set"]) == 3)
        print_test_case("UPDATE multiple fields", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("UPDATE multiple fields", sql, expected, str(e), False)
        return False


def test_update_with_where_condition():
    """Test Case 13: UPDATE with WHERE condition"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 13: UPDATE WITH WHERE CONDITION")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "UPDATE users SET status = 'inactive' WHERE age > 65"
    
    expected = {
        "collection": "users_collection",
        "type": "update",
        "filter": {
            "user_age": {"$gt": 65}
        },
        "update": {
            "$set": {
                "account_status": "inactive"
            }
        }
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = (actual["type"] == "update" and 
                 "user_age" in actual["filter"])
        print_test_case("UPDATE with WHERE", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("UPDATE with WHERE", sql, expected, str(e), False)
        return False


def test_delete_basic():
    """Test Case 14: DELETE basic"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 14: DELETE BASIC")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "DELETE FROM users WHERE id = 10"
    
    expected = {
        "collection": "users_collection",
        "type": "delete",
        "filter": {
            "_id": {"$eq": 10}
        }
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = (actual["type"] == "delete" and 
                 "_id" in actual["filter"])
        print_test_case("DELETE basic", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("DELETE basic", sql, expected, str(e), False)
        return False


def test_delete_with_condition():
    """Test Case 15: DELETE with complex condition"""
    print("\n\n" + "=" * 80)
    print("TEST CASE 15: DELETE WITH CONDITION")
    print("=" * 80)
    
    schema = create_test_schema()
    transpiler = SQLToMongoDBTranspiler(schema)
    
    sql = "DELETE FROM users WHERE age > 70 AND status = 'inactive'"
    
    expected = {
        "collection": "users_collection",
        "type": "delete",
        "filter": {
            "user_age": {"$gt": 70},
            "account_status": {"$eq": "inactive"}
        }
    }
    
    try:
        actual = transpiler.transpile(sql)
        passed = (actual["type"] == "delete" and 
                 "user_age" in actual["filter"])
        print_test_case("DELETE with condition", sql, expected, actual, passed)
        return passed
    except Exception as e:
        print_test_case("DELETE with condition", sql, expected, str(e), False)
        return False


def main():
    """Run all test cases."""
    print("\n\n")
    print("=" * 80)
    print(" " * 15 + "SQL-TO-MONGODB TRANSPILER - TEST CASES")
    print(" " * 14 + "With Expected Outputs and Demonstrations")
    print("=" * 80)
    
    tests = [
        ("SELECT All Records", test_select_all),
        ("SELECT Specific Columns", test_select_specific_columns),
        ("SELECT WHERE Single", test_select_where_single_condition),
        ("SELECT WHERE AND", test_select_where_and_condition),
        ("SELECT WHERE OR", test_select_where_or_condition),
        ("SELECT WHERE IN", test_select_where_in_operator),
        ("SELECT LIMIT", test_select_with_limit),
        ("SELECT LIMIT OFFSET", test_select_with_limit_offset),
        ("INSERT Basic", test_insert_basic),
        ("INSERT Multiple", test_insert_multiple_records),
        ("UPDATE Basic", test_update_basic),
        ("UPDATE Multiple Fields", test_update_multiple_fields),
        ("UPDATE with WHERE", test_update_with_where_condition),
        ("DELETE Basic", test_delete_basic),
        ("DELETE with Condition", test_delete_with_condition),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[FAIL] Test '{name}' crashed: {str(e)}")
            results.append((name, False))
    
    # Summary
    print("\n\n" + "=" * 80)
    print(" " * 30 + "TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} | {name}")
    
    print("=" * 80)
    print(f"Total: {total} | Passed: {passed} | Failed: {total - passed} | Success Rate: {passed/total*100:.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()
