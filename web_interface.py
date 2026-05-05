"""
Web-based Interface for SQL-to-MongoDB Transpiler

Run this Flask app to access the transpiler via a web browser.
"""

from flask import Flask, render_template_string, request, jsonify
import json
from sql_to_mongodb_transpiler import (
    SchemaMapping,
    SQLToMongoDBTranspiler,
    UnsupportedSQLException,
    SchemaMappingException,
    InvalidQueryException,
)

app = Flask(__name__)

# Sample schemas
SAMPLE_SCHEMAS = {
    "ecommerce": {
        "tables": {
            "users": "users_collection",
            "products": "products_collection",
            "orders": "orders_collection",
        },
        "columns": {
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
        },
    },
    "employees": {
        "tables": {
            "employees": "employees_collection",
            "departments": "departments_collection",
        },
        "columns": {
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
        },
    },
    "simple": {
        "tables": {
            "users": "users",
            "posts": "posts",
        },
        "columns": {
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
        },
    },
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SQL to MongoDB Transpiler</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: 'MS Sans Serif', Arial, sans-serif;
            background-color: #c0c0c0;
            color: #000;
            margin: 8px;
        }
        
        h1 {
            background-color: #000080;
            color: #fff;
            padding: 4px;
            margin: 0;
            font-size: 16px;
        }
        
        .window {
            background-color: #c0c0c0;
            border: 2px outset #dfdfdf;
            border-right-color: #808080;
            border-bottom-color: #808080;
            padding: 4px;
            margin-bottom: 8px;
        }
        
        .title-bar {
            background: linear-gradient(90deg, #000080, #1084d7);
            color: #fff;
            padding: 2px 2px;
            margin: -4px -4px 4px -4px;
            font-weight: bold;
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        label {
            display: block;
            margin-top: 8px;
            margin-bottom: 4px;
            font-weight: bold;
            font-size: 12px;
        }
        
        select, textarea, input {
            font-family: 'MS Sans Serif', Arial, sans-serif;
            font-size: 11px;
            background-color: #fff;
            color: #000;
            border: 2px inset #dfdfdf;
            border-right-color: #808080;
            border-bottom-color: #808080;
            padding: 3px;
            width: 100%;
            box-sizing: border-box;
        }
        
        textarea {
            min-height: 100px;
            resize: vertical;
            font-family: 'Courier New', monospace;
        }
        
        button {
            background-color: #c0c0c0;
            border: 2px outset #dfdfdf;
            border-right-color: #808080;
            border-bottom-color: #808080;
            color: #000;
            padding: 4px 12px;
            font-family: 'MS Sans Serif', Arial, sans-serif;
            font-size: 11px;
            cursor: pointer;
            margin-top: 8px;
            width: 100%;
        }
        
        button:active {
            border-style: inset;
            border-color: #808080 #dfdfdf #dfdfdf #808080;
        }
        
        button:hover {
            background-color: #dfdfdf;
        }
        
        .output-box {
            background-color: #fff;
            border: 2px inset #dfdfdf;
            border-right-color: #808080;
            border-bottom-color: #808080;
            padding: 4px;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            min-height: 150px;
            max-height: 300px;
            overflow: auto;
            white-space: pre-wrap;
            word-break: break-word;
            margin-top: 8px;
        }
        
        .schema-display {
            background-color: #fff;
            border: 2px inset #dfdfdf;
            border-right-color: #808080;
            border-bottom-color: #808080;
            padding: 4px;
            font-family: 'Courier New', monospace;
            font-size: 11px;
            max-height: 200px;
            overflow: auto;
            margin-top: 8px;
        }
        
        .schema-table {
            margin-bottom: 8px;
        }
        
        .schema-table strong {
            color: #000080;
            display: block;
            margin-bottom: 2px;
        }
        
        .schema-column {
            margin-left: 12px;
            color: #000;
            font-size: 10px;
        }
        
        .examples {
            background-color: #fff;
            border: 2px inset #dfdfdf;
            border-right-color: #808080;
            border-bottom-color: #808080;
            padding: 4px;
            margin-top: 8px;
            font-size: 11px;
        }
        
        .examples strong {
            display: block;
            margin-bottom: 4px;
            color: #000080;
        }
        
        .examples div {
            margin-bottom: 2px;
            color: #000;
            cursor: pointer;
            padding: 2px;
        }
        
        .examples div:hover {
            background-color: #000080;
            color: #fff;
        }
        
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-bottom: 8px;
        }
        
        .grid.full {
            grid-column: 1 / -1;
        }
        
        .no-output {
            color: #808080;
            text-align: center;
            padding: 20px;
            font-size: 12px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        
        .grid-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }
        
        .grid-full {
            grid-column: 1 / -1;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="window">
            <div class="title-bar">
                <span>SQL to MongoDB Transpiler</span>
                <span>___ [ ] X</span>
            </div>
            <p style="margin: 4px; font-size: 11px;">Convert SQL queries to MongoDB format</p>
        </div>
        
        <div class="grid-container">
            <!-- Schema Selection Panel -->
            <div class="window">
                <div class="title-bar">
                    <span>Schema Setup</span>
                </div>
                
                <label>Select Database Schema:</label>
                <select id="schema_select">
                    <option value="">-- Choose Schema --</option>
                    <option value="ecommerce">E-Commerce Database</option>
                    <option value="employees">Employee Management</option>
                    <option value="simple">Simple Database</option>
                </select>
                
                <button onclick="loadSchema()">Load Schema</button>
                
                <div id="schema_display" class="schema-display" style="display: none;"></div>
                
                <div id="examples_section" class="examples" style="display: none;">
                    <strong>Example Queries:</strong>
                    <div onclick="setQuery('SELECT * FROM users')">> SELECT * FROM users</div>
                    <div onclick="setQuery('SELECT * FROM users WHERE age > 25')">> WHERE clause</div>
                    <div onclick="setQuery('SELECT * FROM users WHERE age > 18 AND age < 65')">> AND condition</div>
                    <div onclick="setQuery('SELECT * FROM users WHERE status = \\'active\\' OR status = \\'pending\\'');">> OR condition</div>
                    <div onclick="setQuery('SELECT * FROM users LIMIT 10 OFFSET 5')">> Pagination</div>
                </div>
            </div>
            
            <!-- Query Input Panel -->
            <div class="window">
                <div class="title-bar">
                    <span>SQL Query Input</span>
                </div>
                
                <label>Enter your SQL Query:</label>
                <textarea id="sql_query" placeholder="SELECT * FROM users WHERE age > 25"></textarea>
                
                <button onclick="transpileQuery()">Transpile to MongoDB</button>
            </div>
            
            <!-- Output Panel -->
            <div class="window grid-full">
                <div class="title-bar">
                    <span>MongoDB Query Output</span>
                </div>
                
                <div id="output_section" style="display: none;">
                    <div id="output_box" class="output-box"></div>
                </div>
                <div id="no_output" class="no-output">
                    Load a schema and enter a SQL query, then click "Transpile to MongoDB"
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentSchema = null;
        
        function loadSchema() {
            const schemaName = document.getElementById('schema_select').value;
            if (!schemaName) {
                alert('Please select a schema');
                return;
            }
            
            fetch('/api/schema/' + schemaName)
                .then(r => r.json())
                .then(data => {
                    currentSchema = data;
                    displaySchema(data);
                    document.getElementById('examples_section').style.display = 'block';
                    document.getElementById('no_output').style.display = 'none';
                    alert('Schema loaded successfully!');
                });
        }
        
        function displaySchema(schema) {
            let html = '';
            for (let table in schema.columns) {
                html += '<div class="schema-table">';
                html += '<strong>' + table + ' -&gt; ' + schema.tables[table] + '</strong>';
                for (let col in schema.columns[table]) {
                    html += '<div class="schema-column">' + col + ' -&gt; ' + schema.columns[table][col] + '</div>';
                }
                html += '</div>';
            }
            document.getElementById('schema_display').innerHTML = html;
            document.getElementById('schema_display').style.display = 'block';
        }
        
        function setQuery(query) {
            document.getElementById('sql_query').value = query;
        }
        
        function transpileQuery() {
            const schemaName = document.getElementById('schema_select').value;
            const query = document.getElementById('sql_query').value;
            
            if (!schemaName) {
                alert('Please load a schema first');
                return;
            }
            
            if (!query) {
                alert('Please enter a SQL query');
                return;
            }
            
            fetch('/api/transpile', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    schema: schemaName,
                    query: query
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    showOutput('ERROR: ' + data.error, true);
                } else {
                    showOutput(JSON.stringify(data.result, null, 2), false);
                }
            })
            .catch(err => {
                showOutput('ERROR: ' + err.message, true);
            });
        }
        
        function showOutput(content, isError) {
            const box = document.getElementById('output_box');
            box.textContent = content;
            if (isError) {
                box.style.color = '#c00';
                box.style.backgroundColor = '#fee';
            } else {
                box.style.color = '#000';
                box.style.backgroundColor = '#fff';
            }
            document.getElementById('output_section').style.display = 'block';
            document.getElementById('no_output').style.display = 'none';
        }
    </script>
</body>
</html>
"""


def create_schema(schema_name):
    """Create SchemaMapping from sample data."""
    schema_data = SAMPLE_SCHEMAS[schema_name]
    schema = SchemaMapping()
    schema.table_mapping = schema_data["tables"]
    schema.column_mapping = schema_data["columns"]
    return schema


@app.route("/")
def index():
    """Serve the web interface."""
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/schema/<schema_name>")
def get_schema(schema_name):
    """Get schema details."""
    if schema_name not in SAMPLE_SCHEMAS:
        return jsonify({"error": "Schema not found"}), 404
    return jsonify(SAMPLE_SCHEMAS[schema_name])


@app.route("/api/transpile", methods=["POST"])
def transpile():
    """Transpile SQL query to MongoDB."""
    data = request.json
    schema_name = data.get("schema")
    query = data.get("query")
    
    if not schema_name or not query:
        return jsonify({"error": "Missing schema or query"}), 400
    
    if schema_name not in SAMPLE_SCHEMAS:
        return jsonify({"error": "Schema not found"}), 404
    
    try:
        schema = create_schema(schema_name)
        transpiler = SQLToMongoDBTranspiler(schema)
        result = transpiler.transpile(query)
        return jsonify({"result": result})
    except (UnsupportedSQLException, SchemaMappingException, InvalidQueryException) as e:
        return jsonify({"error": str(e)})
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SQL-to-MongoDB Transpiler - Web Interface")
    print("="*70)
    print("\n🌐 Opening in browser at: http://localhost:5000")
    print("   (Press Ctrl+C to stop)\n")
    app.run(debug=True, host="localhost", port=5000)
