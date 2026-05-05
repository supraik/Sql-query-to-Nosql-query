"""
SQL-to-MongoDB Transpiler Library

A robust translation layer that converts standard SQL strings into MongoDB query 
dictionaries or aggregation pipelines using the sqlparse library.

Author: CodexSystem
Date: 2026
"""

import json
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Parenthesis, Comparison
from sqlparse.tokens import Keyword, DML


# =====================================================================
# CUSTOM EXCEPTIONS
# =====================================================================

class TranspilerException(Exception):
    """Base exception for transpiler errors."""
    pass


class UnsupportedSQLException(TranspilerException):
    """Raised when SQL syntax is not supported."""
    pass


class SchemaMappingException(TranspilerException):
    """Raised when schema mapping fails."""
    pass


class InvalidQueryException(TranspilerException):
    """Raised when query structure is invalid."""
    pass


# =====================================================================
# ENUMS AND CONSTANTS
# =====================================================================

class DMLAction(Enum):
    """Supported DML actions."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


# Operator translation mapping
OPERATOR_MAPPING = {
    "=": "$eq",
    "==": "$eq",
    "!=": "$ne",
    "<>": "$ne",
    ">": "$gt",
    "<": "$lt",
    ">=": "$gte",
    "<=": "$lte",
    "IN": "$in",
    "NOT IN": "$nin",
    "LIKE": "$regex",
    "NOT LIKE": "$not",
}

LOGICAL_OPERATORS = {"AND", "OR"}


# =====================================================================
# DATA CLASSES
# =====================================================================

@dataclass
class SchemaMapping:
    """Defines table and column mappings between SQL and MongoDB."""
    
    table_mapping: Dict[str, str] = field(default_factory=dict)  # SQL table -> MongoDB collection
    column_mapping: Dict[str, Dict[str, str]] = field(default_factory=dict)  # table -> {SQL column -> MongoDB field}
    
    def get_collection(self, sql_table: str) -> str:
        """Get MongoDB collection name from SQL table."""
        if sql_table not in self.table_mapping:
            raise SchemaMappingException(f"Table '{sql_table}' not found in schema mapping.")
        return self.table_mapping[sql_table]
    
    def get_field(self, sql_table: str, sql_column: str) -> str:
        """Get MongoDB field name from SQL column."""
        if sql_table not in self.column_mapping:
            raise SchemaMappingException(f"Table '{sql_table}' not found in schema mapping.")
        
        table_columns = self.column_mapping[sql_table]
        if sql_column not in table_columns and sql_column != "*":
            raise SchemaMappingException(
                f"Column '{sql_column}' not found in table '{sql_table}' mapping."
            )
        
        return table_columns.get(sql_column, sql_column)


# =====================================================================
# QUERY PARSER
# =====================================================================

class QueryParser:
    """Parses SQL queries and extracts tokens and components."""
    
    def __init__(self, sql: str):
        """Initialize parser with SQL string."""
        self.sql = sql
        self.parsed = sqlparse.parse(sql)
        
        if not self.parsed:
            raise InvalidQueryException("Failed to parse SQL query.")
        
        self.statement = self.parsed[0]
        self.tokens = self.statement.tokens
    
    def get_dml_action(self) -> DMLAction:
        """Identify and return the DML action (SELECT, INSERT, UPDATE, DELETE)."""
        for token in self.tokens:
            if token.ttype is DML:
                action_str = token.value.upper().strip()
                try:
                    return DMLAction[action_str]
                except KeyError:
                    raise UnsupportedSQLException(f"Unsupported DML action: {action_str}")
        
        raise InvalidQueryException("No DML action found in query.")
    
    def extract_from_clause(self) -> str:
        """Extract table name from FROM clause."""
        from_seen = False
        
        for token in self.tokens:
            if token.ttype is Keyword and token.value.upper() == "FROM":
                from_seen = True
                continue
            
            if from_seen:
                if token.ttype is Keyword:
                    break
                
                value = token.value.strip()
                if value and value.upper() not in ("WHERE", "ORDER", "LIMIT", "OFFSET", "GROUP", "HAVING"):
                    return value
        
        raise InvalidQueryException("No table found in FROM clause.")
    
    def extract_where_clause(self) -> Optional[str]:
        """Extract WHERE clause content."""
        for token in self.tokens:
            value = str(token).strip()
            # Check if token contains WHERE clause
            if value.upper().startswith("WHERE "):
                # Extract condition after "WHERE "
                condition = value[6:].strip()  # Skip "WHERE "
                return condition if condition else None
        
        return None
    
    def extract_limit_clause(self) -> Optional[int]:
        """Extract LIMIT clause value."""
        limit_seen = False
        
        for token in self.tokens:
            if token.ttype is Keyword and token.value.upper() == "LIMIT":
                limit_seen = True
                continue
            
            if limit_seen and token.ttype is not Keyword:
                try:
                    return int(token.value.strip())
                except ValueError:
                    pass
        
        return None
    
    def extract_offset_clause(self) -> Optional[int]:
        """Extract OFFSET clause value."""
        offset_seen = False
        
        for token in self.tokens:
            if token.ttype is Keyword and token.value.upper() == "OFFSET":
                offset_seen = True
                continue
            
            if offset_seen and token.ttype is not Keyword:
                try:
                    return int(token.value.strip())
                except ValueError:
                    pass
        
        return None
    
    def extract_select_columns(self) -> List[str]:
        """Extract columns from SELECT clause."""
        select_seen = False
        columns = []
        
        for token in self.tokens:
            if token.ttype is DML and token.value.upper() == "SELECT":
                select_seen = True
                continue
            
            if select_seen:
                if token.ttype is Keyword and token.value.upper() in ("FROM", "WHERE", "ORDER", "LIMIT"):
                    break
                
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        columns.append(identifier.value.strip())
                elif isinstance(token, Identifier):
                    columns.append(token.value.strip())
                elif token.ttype is None and token.value.strip() not in ("", ","):
                    columns.append(token.value.strip())
        
        return columns if columns else ["*"]
    
    def has_join(self) -> bool:
        """Check if query contains JOIN clause."""
        for token in self.tokens:
            if token.ttype is Keyword and "JOIN" in token.value.upper():
                return True
        return False
    
    def extract_join_info(self) -> Optional[Dict[str, Any]]:
        """Extract JOIN information (simplified support)."""
        if not self.has_join():
            return None
        
        # Simplified JOIN extraction
        sql_upper = self.sql.upper()
        if "JOIN" not in sql_upper:
            return None
        
        # This is a simplified extraction; production code would need more robust parsing
        try:
            join_idx = sql_upper.find("JOIN")
            on_idx = sql_upper.find("ON", join_idx)
            
            if on_idx == -1:
                raise UnsupportedSQLException("JOIN requires ON clause.")
            
            return {
                "type": "lookup",
                "has_join": True
            }
        except Exception as e:
            raise UnsupportedSQLException(f"Failed to parse JOIN clause: {str(e)}")


# =====================================================================
# WHERE CLAUSE PARSER
# =====================================================================

class WhereClauseParser:
    """Recursively parses WHERE clause conditions."""
    
    def __init__(self, schema: SchemaMapping, table_name: str):
        """Initialize parser."""
        self.schema = schema
        self.table_name = table_name
    
    def parse(self, where_clause: str) -> Dict[str, Any]:
        """Parse WHERE clause into MongoDB query dict."""
        if not where_clause or not where_clause.strip():
            return {}
        
        return self._parse_condition(where_clause)
    
    def _parse_condition(self, condition: str) -> Dict[str, Any]:
        """Recursively parse a condition (handles AND/OR)."""
        condition = condition.strip()
        
        # Remove outer parentheses if they exist
        if condition.startswith("(") and condition.endswith(")"):
            condition = condition[1:-1].strip()
        
        # Check for OR operator (lower precedence)
        or_parts = self._split_by_operator(condition, "OR")
        if len(or_parts) > 1:
            or_conditions = [self._parse_condition(part.strip()) for part in or_parts]
            return {"$or": or_conditions}
        
        # Check for AND operator (higher precedence)
        and_parts = self._split_by_operator(condition, "AND")
        if len(and_parts) > 1:
            and_result = {}
            for part in and_parts:
                parsed = self._parse_condition(part.strip())
                and_result.update(parsed)
            return and_result
        
        # Parse simple comparison
        return self._parse_simple_condition(condition)
    
    def _split_by_operator(self, condition: str, operator: str) -> List[str]:
        """Split condition by operator, respecting parentheses."""
        parts = []
        current = []
        paren_level = 0
        i = 0
        
        while i < len(condition):
            if condition[i] == "(":
                paren_level += 1
                current.append(condition[i])
            elif condition[i] == ")":
                paren_level -= 1
                current.append(condition[i])
            elif paren_level == 0 and condition[i:i + len(operator)].upper() == operator:
                if current:
                    parts.append("".join(current).strip())
                    current = []
                i += len(operator) - 1
            else:
                current.append(condition[i])
            
            i += 1
        
        if current:
            parts.append("".join(current).strip())
        
        return parts if len(parts) > 1 else [condition]
    
    def _parse_simple_condition(self, condition: str) -> Dict[str, Any]:
        """Parse a simple comparison condition."""
        condition = condition.strip()
        
        # Try different operators (sorted by length to match longer operators first)
        for op in sorted(OPERATOR_MAPPING.keys(), key=len, reverse=True):
            # Create a case-insensitive search for the operator
            condition_upper = condition.upper()
            op_upper = op.upper()
            
            # Find the position of the operator
            op_pos = -1
            for i in range(len(condition_upper) - len(op_upper) + 1):
                if condition_upper[i:i + len(op_upper)] == op_upper:
                    # Make sure it's not part of another word (for operators like IN)
                    before_ok = (i == 0 or not condition_upper[i-1].isalnum())
                    after_ok = (i + len(op_upper) >= len(condition_upper) or not condition_upper[i + len(op_upper)].isalnum())
                    if before_ok and after_ok:
                        op_pos = i
                        break
            
            if op_pos != -1:
                column = condition[:op_pos].strip()
                value = condition[op_pos + len(op):].strip()
                
                # Remove quotes from value
                if (value.startswith("'") and value.endswith("'")) or \
                   (value.startswith('"') and value.endswith('"')):
                    value = value[1:-1]
                
                # Convert to appropriate type
                try:
                    if value.upper() in ("TRUE", "FALSE"):
                        value = value.upper() == "TRUE"
                    elif value.isdigit():
                        value = int(value)
                    elif self._is_float(value):
                        value = float(value)
                except (ValueError, AttributeError):
                    pass
                
                mongo_field = self.schema.get_field(self.table_name, column)
                mongo_op = OPERATOR_MAPPING.get(op, "$eq")
                
                if op.upper() == "IN":
                    # Handle IN operator
                    values = [v.strip().strip("'\"") for v in value.strip("()").split(",")]
                    try:
                        values = [int(v) if v.isdigit() else v for v in values]
                    except (ValueError, AttributeError):
                        pass
                    return {mongo_field: {mongo_op: values}}
                else:
                    return {mongo_field: {mongo_op: value}}
        
        raise InvalidQueryException(f"Could not parse condition: {condition}")
    
    def _is_float(self, value: str) -> bool:
        """Check if string is a float."""
        try:
            float(value)
            return "." in value
        except ValueError:
            return False


# =====================================================================
# MONGO GENERATOR
# =====================================================================

class MongoGenerator:
    """Generates MongoDB queries and aggregation pipelines."""
    
    def __init__(self, schema: SchemaMapping):
        """Initialize generator with schema mapping."""
        self.schema = schema
    
    def generate_select(
        self,
        table: str,
        columns: List[str],
        where_clause: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        has_join: bool = False,
    ) -> Dict[str, Any]:
        """Generate MongoDB query for SELECT statement."""
        collection = self.schema.get_collection(table)
        
        # Build query dict
        query: Dict[str, Any] = {
            "collection": collection,
            "type": "aggregation" if (has_join or offset) else "find",
        }
        
        # Build projection
        if columns != ["*"]:
            projection = {self.schema.get_field(table, col): 1 for col in columns}
            query["projection"] = projection
        else:
            query["projection"] = None
        
        # Build filter
        if where_clause:
            parser = WhereClauseParser(self.schema, table)
            query["filter"] = parser.parse(where_clause)
        else:
            query["filter"] = {}
        
        # Build aggregation pipeline if needed
        if has_join or offset:
            pipeline = []
            
            # Match stage
            if query["filter"]:
                pipeline.append({"$match": query["filter"]})
            
            # Skip stage (must come before limit)
            if offset:
                pipeline.append({"$skip": offset})
            
            # Limit stage
            if limit:
                pipeline.append({"$limit": limit})
            
            # Project stage
            if columns != ["*"]:
                project_stage = {col: 1 for col in columns}
                project_stage["_id"] = 1
                pipeline.append({"$project": project_stage})
            
            query["pipeline"] = pipeline
            del query["projection"]
        else:
            # For simple find queries
            if limit:
                query["limit"] = limit
        
        return query
    
    def generate_insert(
        self,
        table: str,
        document: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate MongoDB query for INSERT statement."""
        collection = self.schema.get_collection(table)
        
        # Map SQL columns to MongoDB fields
        mapped_doc = {}
        for col, value in document.items():
            mongo_field = self.schema.get_field(table, col)
            mapped_doc[mongo_field] = value
        
        return {
            "collection": collection,
            "type": "insert",
            "document": mapped_doc,
        }
    
    def generate_delete(
        self,
        table: str,
        where_clause: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate MongoDB query for DELETE statement."""
        collection = self.schema.get_collection(table)
        
        filter_dict = {}
        if where_clause:
            parser = WhereClauseParser(self.schema, table)
            filter_dict = parser.parse(where_clause)
        
        return {
            "collection": collection,
            "type": "delete",
            "filter": filter_dict,
        }
    
    def generate_update(
        self,
        table: str,
        updates: Dict[str, Any],
        where_clause: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate MongoDB query for UPDATE statement."""
        collection = self.schema.get_collection(table)
        
        # Map SQL columns to MongoDB fields
        mapped_updates = {}
        for col, value in updates.items():
            mongo_field = self.schema.get_field(table, col)
            mapped_updates[mongo_field] = value
        
        filter_dict = {}
        if where_clause:
            parser = WhereClauseParser(self.schema, table)
            filter_dict = parser.parse(where_clause)
        
        return {
            "collection": collection,
            "type": "update",
            "filter": filter_dict,
            "update": {"$set": mapped_updates},
        }


# =====================================================================
# MAIN TRANSPILER
# =====================================================================

class SQLToMongoDBTranspiler:
    """Main transpiler class for converting SQL to MongoDB queries."""
    
    def __init__(self, schema: SchemaMapping):
        """Initialize transpiler with schema mapping."""
        self.schema = schema
        self.parser: Optional[QueryParser] = None
        self.generator = MongoGenerator(schema)
    
    def transpile(self, sql: str) -> Dict[str, Any]:
        """
        Transpile SQL query to MongoDB query.
        
        Args:
            sql: SQL query string
        
        Returns:
            Dictionary containing MongoDB query information
        
        Raises:
            TranspilerException: If transpilation fails
        """
        try:
            self.parser = QueryParser(sql)
            action = self.parser.get_dml_action()
            
            if action == DMLAction.SELECT:
                return self._transpile_select()
            elif action == DMLAction.INSERT:
                return self._transpile_insert()
            elif action == DMLAction.UPDATE:
                return self._transpile_update()
            elif action == DMLAction.DELETE:
                return self._transpile_delete()
            else:
                raise UnsupportedSQLException(f"Unsupported DML action: {action}")
        
        except TranspilerException:
            raise
        except Exception as e:
            raise TranspilerException(f"Transpilation failed: {str(e)}")
    
    def _transpile_select(self) -> Dict[str, Any]:
        """Transpile SELECT statement."""
        if not self.parser:
            raise InvalidQueryException("Parser not initialized")
        
        table = self.parser.extract_from_clause()
        columns = self.parser.extract_select_columns()
        where_clause = self.parser.extract_where_clause()
        limit = self.parser.extract_limit_clause()
        offset = self.parser.extract_offset_clause()
        has_join = self.parser.has_join()
        
        return self.generator.generate_select(
            table=table,
            columns=columns,
            where_clause=where_clause,
            limit=limit,
            offset=offset,
            has_join=has_join,
        )
    
    def _transpile_insert(self) -> Dict[str, Any]:
        """Transpile INSERT statement."""
        raise UnsupportedSQLException("INSERT statement transpilation not yet implemented")
    
    def _transpile_update(self) -> Dict[str, Any]:
        """Transpile UPDATE statement."""
        raise UnsupportedSQLException("UPDATE statement transpilation not yet implemented")
    
    def _transpile_delete(self) -> Dict[str, Any]:
        """Transpile DELETE statement."""
        raise UnsupportedSQLException("DELETE statement transpilation not yet implemented")


# =====================================================================
# TEST SUITE
# =====================================================================

class TestSuite:
    """Comprehensive test suite for the transpiler."""
    
    def __init__(self):
        """Initialize test suite with schema."""
        self.schema = self._create_test_schema()
        self.transpiler = SQLToMongoDBTranspiler(self.schema)
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def _create_test_schema(self) -> SchemaMapping:
        """Create test schema mapping."""
        schema = SchemaMapping()
        
        # Table mappings
        schema.table_mapping = {
            "users": "users_collection",
            "orders": "orders_collection",
            "products": "products_collection",
        }
        
        # Column mappings
        schema.column_mapping = {
            "users": {
                "id": "_id",
                "name": "user_name",
                "email": "user_email",
                "age": "user_age",
            },
            "orders": {
                "id": "_id",
                "user_id": "customer_id",
                "amount": "total_amount",
                "status": "order_status",
            },
            "products": {
                "id": "_id",
                "name": "product_name",
                "price": "product_price",
                "stock": "quantity_in_stock",
            },
        }
        
        return schema
    
    def run_all_tests(self) -> None:
        """Run all tests."""
        print("\n" + "="*70)
        print("SQL-TO-MONGODB TRANSPILER TEST SUITE")
        print("="*70 + "\n")
        
        self.test_simple_select()
        self.test_select_with_where_single_condition()
        self.test_select_with_where_and_conditions()
        self.test_select_with_where_or_conditions()
        self.test_select_with_where_nested_conditions()
        self.test_select_with_limit()
        self.test_select_with_limit_and_offset()
        self.test_select_specific_columns()
        self.test_select_with_in_operator()
        self.test_select_with_comparison_operators()
        self.test_error_handling()
        
        self._print_summary()
    
    def test_simple_select(self) -> None:
        """Test: Simple SELECT * FROM table."""
        test_name = "Simple SELECT"
        sql = "SELECT * FROM users"
        
        try:
            result = self.transpiler.transpile(sql)
            
            assert result["collection"] == "users_collection"
            assert result["type"] == "find"
            assert result["filter"] == {}
            assert result["projection"] is None
            
            self._log_test(test_name, True, sql, result)
        except Exception as e:
            self._log_test(test_name, False, sql, str(e))
    
    def test_select_with_where_single_condition(self) -> None:
        """Test: SELECT with WHERE clause (single condition)."""
        test_name = "SELECT with WHERE (single condition)"
        sql = "SELECT * FROM users WHERE age = 25"
        
        try:
            result = self.transpiler.transpile(sql)
            
            assert result["collection"] == "users_collection"
            assert "user_age" in result["filter"]
            assert result["filter"]["user_age"]["$eq"] == 25
            
            self._log_test(test_name, True, sql, result)
        except Exception as e:
            self._log_test(test_name, False, sql, str(e))
    
    def test_select_with_where_and_conditions(self) -> None:
        """Test: SELECT with WHERE clause (AND conditions)."""
        test_name = "SELECT with WHERE (AND conditions)"
        sql = "SELECT * FROM users WHERE age > 18 AND age < 65"
        
        try:
            result = self.transpiler.transpile(sql)
            
            assert result["collection"] == "users_collection"
            assert "user_age" in result["filter"]
            
            self._log_test(test_name, True, sql, result)
        except Exception as e:
            self._log_test(test_name, False, sql, str(e))
    
    def test_select_with_where_or_conditions(self) -> None:
        """Test: SELECT with WHERE clause (OR conditions)."""
        test_name = "SELECT with WHERE (OR conditions)"
        sql = "SELECT * FROM users WHERE age < 18 OR age > 65"
        
        try:
            result = self.transpiler.transpile(sql)
            
            assert result["collection"] == "users_collection"
            assert "$or" in result["filter"]
            
            self._log_test(test_name, True, sql, result)
        except Exception as e:
            self._log_test(test_name, False, sql, str(e))
    
    def test_select_with_where_nested_conditions(self) -> None:
        """Test: SELECT with complex nested WHERE conditions."""
        test_name = "SELECT with nested WHERE conditions"
        sql = "SELECT * FROM users WHERE (age > 18 AND age < 65) OR name = 'John'"
        
        try:
            result = self.transpiler.transpile(sql)
            
            assert result["collection"] == "users_collection"
            assert "$or" in result["filter"]
            
            self._log_test(test_name, True, sql, result)
        except Exception as e:
            self._log_test(test_name, False, sql, str(e))
    
    def test_select_with_limit(self) -> None:
        """Test: SELECT with LIMIT clause."""
        test_name = "SELECT with LIMIT"
        sql = "SELECT * FROM users LIMIT 10"
        
        try:
            result = self.transpiler.transpile(sql)
            
            assert result["collection"] == "users_collection"
            assert result["limit"] == 10
            
            self._log_test(test_name, True, sql, result)
        except Exception as e:
            self._log_test(test_name, False, sql, str(e))
    
    def test_select_with_limit_and_offset(self) -> None:
        """Test: SELECT with LIMIT and OFFSET (requires aggregation pipeline)."""
        test_name = "SELECT with LIMIT and OFFSET"
        sql = "SELECT * FROM users LIMIT 10 OFFSET 5"
        
        try:
            result = self.transpiler.transpile(sql)
            
            assert result["collection"] == "users_collection"
            assert result["type"] == "aggregation"
            assert "pipeline" in result
            
            pipeline = result["pipeline"]
            stages = [list(stage.keys())[0] for stage in pipeline]
            assert "$skip" in stages
            assert "$limit" in stages
            
            self._log_test(test_name, True, sql, result)
        except Exception as e:
            self._log_test(test_name, False, sql, str(e))
    
    def test_select_specific_columns(self) -> None:
        """Test: SELECT specific columns."""
        test_name = "SELECT specific columns"
        sql = "SELECT name, email FROM users"
        
        try:
            result = self.transpiler.transpile(sql)
            
            assert result["collection"] == "users_collection"
            assert "projection" in result
            assert "user_name" in result["projection"]
            assert "user_email" in result["projection"]
            
            self._log_test(test_name, True, sql, result)
        except Exception as e:
            self._log_test(test_name, False, sql, str(e))
    
    def test_select_with_in_operator(self) -> None:
        """Test: SELECT with IN operator."""
        test_name = "SELECT with IN operator"
        sql = "SELECT * FROM users WHERE id IN (1, 2, 3)"
        
        try:
            result = self.transpiler.transpile(sql)
            
            assert result["collection"] == "users_collection"
            assert "_id" in result["filter"]
            assert "$in" in result["filter"]["_id"]
            
            self._log_test(test_name, True, sql, result)
        except Exception as e:
            self._log_test(test_name, False, sql, str(e))
    
    def test_select_with_comparison_operators(self) -> None:
        """Test: SELECT with various comparison operators."""
        test_name = "SELECT with comparison operators"
        
        test_cases = [
            ("SELECT * FROM orders WHERE amount > 100", "$gt"),
            ("SELECT * FROM orders WHERE amount >= 100", "$gte"),
            ("SELECT * FROM orders WHERE amount < 100", "$lt"),
            ("SELECT * FROM orders WHERE amount <= 100", "$lte"),
            ("SELECT * FROM orders WHERE amount != 0", "$ne"),
        ]
        
        for sql, expected_op in test_cases:
            try:
                result = self.transpiler.transpile(sql)
                
                assert result["collection"] == "orders_collection"
                assert "total_amount" in result["filter"]
                assert expected_op in result["filter"]["total_amount"]
                
                self._log_test(test_name, True, sql, result)
            except Exception as e:
                self._log_test(test_name, False, sql, str(e))
    
    def test_error_handling(self) -> None:
        """Test: Error handling for invalid queries."""
        test_name = "Error handling"
        
        invalid_queries = [
            ("", InvalidQueryException),
            ("INVALID SQL", (UnsupportedSQLException, InvalidQueryException)),  # Can be either
            ("SELECT * FROM nonexistent_table", SchemaMappingException),
        ]
        
        for sql, expected_exception in invalid_queries:
            try:
                result = self.transpiler.transpile(sql)
                self._log_test(test_name, False, sql, f"Expected exception but succeeded")
            except Exception as e:
                # Check if we got the expected exception
                if isinstance(expected_exception, tuple):
                    is_expected = isinstance(e, expected_exception)
                else:
                    is_expected = isinstance(e, expected_exception)
                
                if is_expected:
                    self._log_test(test_name, True, sql, f"Correctly raised {type(e).__name__}")
                else:
                    self._log_test(test_name, False, sql, f"Expected {expected_exception} but got {type(e).__name__}: {str(e)}")
    
    def _log_test(self, test_name: str, passed: bool, sql: str, result: Any) -> None:
        """Log test result."""
        status = "[PASS]" if passed else "[FAIL]"
        self.tests_passed += 1 if passed else 0
        self.tests_failed += 0 if passed else 1
        
        self.test_results.append({
            "name": test_name,
            "passed": passed,
            "sql": sql,
            "result": result,
        })
        
        print(f"{status}: {test_name}")
        print(f"  SQL: {sql}")
        if passed:
            print(f"  Result: {json.dumps(result, indent=2, default=str)[:200]}...")
        else:
            print(f"  Error: {result}")
        print()
    
    def _print_summary(self) -> None:
        """Print test summary."""
        total = self.tests_passed + self.tests_failed
        percentage = (self.tests_passed / total * 100) if total > 0 else 0
        
        print("="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Success Rate: {percentage:.1f}%")
        print("="*70 + "\n")


# =====================================================================
# USAGE EXAMPLE
# =====================================================================

def main() -> None:
    """Run example usage and test suite."""
    
    # Create schema mapping
    schema = SchemaMapping()
    schema.table_mapping = {
        "users": "users_collection",
        "orders": "orders_collection",
    }
    schema.column_mapping = {
        "users": {
            "id": "_id",
            "name": "user_name",
            "email": "user_email",
            "age": "user_age",
        },
        "orders": {
            "id": "_id",
            "user_id": "customer_id",
            "amount": "total_amount",
            "status": "order_status",
        },
    }
    
    # Create transpiler
    transpiler = SQLToMongoDBTranspiler(schema)
    
    # Example 1: Simple SELECT
    print("\n" + "="*70)
    print("EXAMPLE 1: Simple SELECT")
    print("="*70)
    sql1 = "SELECT * FROM users"
    result1 = transpiler.transpile(sql1)
    print(f"SQL: {sql1}")
    print(f"MongoDB Query:\n{json.dumps(result1, indent=2, default=str)}\n")
    
    # Example 2: SELECT with WHERE clause
    print("="*70)
    print("EXAMPLE 2: SELECT with WHERE (multiple conditions)")
    print("="*70)
    sql2 = "SELECT name, email FROM users WHERE age > 18 AND age < 65"
    result2 = transpiler.transpile(sql2)
    print(f"SQL: {sql2}")
    print(f"MongoDB Query:\n{json.dumps(result2, indent=2, default=str)}\n")
    
    # Example 3: SELECT with OR conditions
    print("="*70)
    print("EXAMPLE 3: SELECT with WHERE (OR conditions)")
    print("="*70)
    sql3 = "SELECT * FROM orders WHERE status = 'pending' OR status = 'shipped'"
    result3 = transpiler.transpile(sql3)
    print(f"SQL: {sql3}")
    print(f"MongoDB Query:\n{json.dumps(result3, indent=2, default=str)}\n")
    
    # Example 4: SELECT with LIMIT and OFFSET
    print("="*70)
    print("EXAMPLE 4: SELECT with LIMIT and OFFSET (aggregation pipeline)")
    print("="*70)
    sql4 = "SELECT * FROM users LIMIT 5 OFFSET 10"
    result4 = transpiler.transpile(sql4)
    print(f"SQL: {sql4}")
    print(f"MongoDB Query:\n{json.dumps(result4, indent=2, default=str)}\n")
    
    # Run test suite
    test_suite = TestSuite()
    test_suite.run_all_tests()


if __name__ == "__main__":
    main()
