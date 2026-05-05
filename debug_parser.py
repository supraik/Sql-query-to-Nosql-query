"""Debug script to inspect sqlparse tokenization and WHERE clause extraction."""

import sqlparse
from sqlparse.tokens import Keyword, DML

def debug_parse(sql):
    """Debug SQL parsing."""
    print(f"\nSQL: {sql}")
    print("-" * 70)
    
    parsed = sqlparse.parse(sql)
    if not parsed:
        print("Failed to parse")
        return
    
    statement = parsed[0]
    tokens = statement.tokens
    
    print(f"Total tokens: {len(tokens)}")
    for i, token in enumerate(tokens):
        ttype_str = str(token.ttype) if token.ttype else "None"
        print(f"  [{i}] Type: {ttype_str:30} | Value: {repr(token.value):30}")
    
    # Extract WHERE clause manually
    print("\nWHERE Clause Extraction:")
    where_seen = False
    where_content = []
    
    for i, token in enumerate(tokens):
        if token.ttype is Keyword and token.value.upper() == "WHERE":
            print(f"  Found WHERE at token {i}")
            where_seen = True
            continue
        
        if where_seen:
            token_upper = token.value.upper()
            if token.ttype is Keyword:
                print(f"  Stopping at keyword: {token_upper}")
                break
            
            if token.value.strip():
                where_content.append(str(token))
                print(f"  Added token {i}: {repr(token.value)}")
    
    if where_content:
        where_clause = "".join(where_content).strip()
        print(f"\nExtracted WHERE clause: {repr(where_clause)}")
    else:
        print("\nNo WHERE clause content found!")

# Test cases
test_queries = [
    "SELECT * FROM users WHERE age = 25",
    "SELECT * FROM users WHERE age > 18 AND age < 65",
    "SELECT * FROM users WHERE status = 'pending' OR status = 'shipped'",
    "SELECT * FROM users WHERE id IN (1, 2, 3)",
]

for query in test_queries:
    debug_parse(query)
