# Interactive SQL-to-MongoDB Transpiler Guide

This guide explains how to use the interactive interfaces for the SQL-to-MongoDB transpiler.

## Available Interfaces

### 1. **Command-Line Interface (CLI)** - `interactive_cli.py`
Interactive terminal-based application for converting SQL to MongoDB queries.

### 2. **Web Interface** - `web_interface.py`
Beautiful web-based GUI with real-time transpilation.

---

## 🖥️ CLI Usage

### Installation

1. Ensure you have Python 3.7+ installed
2. Install required dependencies:
```bash
pip install sqlparse
```

### Running the CLI

```bash
python interactive_cli.py
```

### Features

**Available Commands:**

| Command | Description |
|---------|------------|
| `schema` | Select from pre-configured schemas (e-commerce, employees, simple) |
| `custom` | Create a custom schema interactively |
| `query` | Enter a SQL query and see MongoDB output |
| `examples` | View example queries for current schema |
| `help` | Display all commands |
| `clear` | Clear screen |
| `exit` / `quit` | Exit the application |

### Example Session

```
> schema

AVAILABLE SAMPLE SCHEMAS:
  1. ecommerce ← CURRENT
  2. employees
  3. simple

Select schema (number/name) or press Enter to skip: 1

✓ Schema 'ecommerce' loaded successfully!

> query

ENTER SQL QUERY

SQL> SELECT * FROM users WHERE age > 25 AND status = 'active'

======================================================================
TRANSPILATION RESULT
======================================================================

📝 SQL Query:
   SELECT * FROM users WHERE age > 25 AND status = 'active'

📊 MongoDB Query:
{
  "find": "users_collection",
  "filter": {
    "$and": [
      {
        "user_age": {
          "$gt": 25
        }
      },
      {
        "account_status": {
          "$eq": "active"
        }
      }
    ]
  }
}

======================================================================
```

### Available Sample Schemas

#### 1. **E-Commerce Schema**
Tables: `users`, `products`, `orders`
- Users: id, name, email, age, status, country
- Products: id, name, price, category, stock
- Orders: id, user_id, product_id, quantity, status

#### 2. **Employee Management Schema**
Tables: `employees`, `departments`
- Employees: id, name, email, salary, age, dept_id, status
- Departments: id, name, budget, manager

#### 3. **Simple Schema**
Tables: `users`, `posts`
- Users: id, name, email, age, city
- Posts: id, user_id, title, content, status

---

## 🌐 Web Interface Usage

### Installation

1. Install Flask:
```bash
pip install flask sqlparse
```

2. Ensure the transpiler module is in the same directory

### Running the Web Server

```bash
python web_interface.py
```

**Output:**
```
======================================================================
SQL-to-MongoDB Transpiler - Web Interface
======================================================================

🌐 Opening in browser at: http://localhost:5000
   (Press Ctrl+C to stop)
```

### Features

✨ **Beautiful Web UI**
- Responsive design with gradient styling
- Real-time query transpilation
- Schema visualization
- Example query suggestions

🎯 **Workflow**
1. **Select Schema** - Choose from pre-configured schemas
2. **View Schema Details** - See table and column mappings
3. **Enter SQL Query** - Type your SQL in the query box
4. **Transpile** - Click "Transpile Query" button or press Ctrl+Enter
5. **View MongoDB Output** - See formatted JSON result

### Web Interface Keyboard Shortcuts

- **Ctrl+Enter** - Transpile query (when in query box)
- **Click examples** - Auto-fill query box with example

---

## 📝 Supported SQL Syntax

Both interfaces support:

### SELECT Queries
```sql
SELECT * FROM users
SELECT name, email FROM users WHERE age > 25
```

### WHERE Conditions
```sql
WHERE age = 25                          -- Equality
WHERE age > 25                          -- Comparison
WHERE age > 18 AND age < 65            -- AND operator
WHERE status = 'active' OR status = 'pending'  -- OR operator
WHERE id IN (1, 2, 3)                  -- IN operator
WHERE (age > 21 AND status = 'active') OR country = 'US'  -- Nested
```

### Pagination
```sql
LIMIT 10                                -- Limit results
OFFSET 5                                -- Skip results
LIMIT 10 OFFSET 5                       -- Combined
```

### JOIN Detection
```sql
SELECT * FROM users JOIN orders ON users.id = orders.user_id
```

---

## 🔧 Creating a Custom Schema

### CLI Method

```
> custom

CREATE CUSTOM SCHEMA
----------------------------------------------------------------------

Define your schema:
Enter table mappings (format: sql_table=mongodb_collection)
Press Enter when done.

Table mapping (or press Enter to skip): employees=staff
✓ Added: employees → staff

Table mapping (or press Enter to skip): 

Now define column mappings for each table:
Format: table.sql_column=mongodb_field

Columns for table 'employees':
(Press Enter when done)

  employees: emp_id=_id
  ✓ Added: emp_id → _id

  employees: emp_name=name
  ✓ Added: emp_name → name

  employees: 

✓ Custom schema created successfully!
```

### Direct Python Usage

```python
from sql_to_mongodb_transpiler import SchemaMapping, SQLToMongoDBTranspiler

# Create schema
schema = SchemaMapping()
schema.table_mapping = {
    "employees": "staff_collection"
}
schema.column_mapping = {
    "employees": {
        "emp_id": "_id",
        "emp_name": "name",
        "salary": "annual_salary"
    }
}

# Create transpiler
transpiler = SQLToMongoDBTranspiler(schema)

# Transpile query
result = transpiler.transpile("SELECT * FROM employees WHERE salary > 50000")
print(result)
```

---

## 📊 Output Format

The transpiler returns MongoDB query objects:

### Simple Query Output
```json
{
  "find": "users_collection",
  "filter": {
    "age": {
      "$eq": 25
    }
  }
}
```

### Complex Query Output (Aggregation Pipeline)
```json
{
  "aggregate": "users_collection",
  "pipeline": [
    {
      "$match": {
        "$and": [
          {"age": {"$gt": 18}},
          {"age": {"$lt": 65}}
        ]
      }
    },
    {
      "$limit": 10
    }
  ]
}
```

---

## ❌ Error Handling

Both interfaces provide helpful error messages:

### Common Errors

**"Table 'users' not found in schema mapping."**
- Solution: Select the correct schema or create a custom one with the table

**"Column 'email' not found in table 'users' mapping."**
- Solution: Check schema column mappings

**"Unsupported SQL syntax"**
- Solution: Use only supported SQL features listed above

---

## 💡 Tips & Tricks

### CLI Tips
- Type `examples` to see sample queries for your current schema
- Press `Ctrl+C` to return to main menu
- Use `clear` to organize your screen
- Use `custom` for schemas not in samples

### Web UI Tips
- Click example queries to auto-fill the query box
- Schema loads its columns when selected
- Output updates in real-time
- Responsive design works on mobile browsers

### Best Practices
1. Always select/load a schema first
2. Use exact table and column names from schema
3. Start with simple queries, then add complexity
4. Check the schema details before writing queries
5. Use examples as templates for complex queries

---

## 🐛 Troubleshooting

### CLI doesn't respond
- Make sure you're not in a nested prompt (check `>` symbols)
- Use `Ctrl+C` to interrupt and return to main menu

### Web interface won't start
- Check if port 5000 is in use: `netstat -an | findstr :5000`
- Try different port: Edit `app.run(port=5001)`
- Ensure Flask is installed: `pip install flask`

### Query returns error
- Verify all table/column names match schema exactly (case-sensitive)
- Check that schema is properly loaded
- Review example queries for syntax

### Import errors
- Ensure `sql_to_mongodb_transpiler.py` is in same directory
- Install dependencies: `pip install sqlparse`

---

## 📞 Support

For issues with:
- **Query transpilation**: Check schema mappings and SQL syntax
- **CLI usage**: Type `help` in the application
- **Web interface**: Check browser console (F12 > Console tab)

---

## 🎓 Learn More

See the main documentation files:
- `README.md` - Comprehensive library documentation
- `PROJECT_SUMMARY.md` - Project overview
- `examples.py` - Advanced code examples

