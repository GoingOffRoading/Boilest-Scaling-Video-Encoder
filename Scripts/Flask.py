from flask import Flask, render_template, request
import sqlite3
import subprocess

print ('diagnostic2')

app = Flask(__name__)

print ('diagnostic3')

# Function to connect to the SQLite database
def connect_db():
    return sqlite3.connect(r"/Boilest/DB/Boilest.db")  # Update with your actual database file name

# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def index():
    # Connect to the database
    conn = connect_db()

    # Use a cursor to execute queries
    cursor = conn.cursor()

    # Query 1
    cursor.execute('select count(unique_identifier) as files_processed FROM ffencode_results')  # Update with your actual table name
    result_1 = cursor.fetchone()[0]

    # Query 2
    cursor.execute('select count(unique_identifier) as files_processed FROM ffencode_results')  # Update with your actual column name
    result_2 = cursor.fetchone()[0]

    # Query 3
    cursor.execute('select count(unique_identifier) as files_processed FROM ffencode_results')  # Update with your actual column name
    result_3 = cursor.fetchone()[0]

    # Query 4
    cursor.execute('select count(unique_identifier) as files_processed FROM ffencode_results')  # Update with your actual column name
    result_4 = cursor.fetchone()[0]

    # Query for the first table data
    cursor.execute('SELECT * FROM ffencode_results limit 10')  # Update with your actual table name
    table_data_1 = cursor.fetchall()

    # Query for the second table data
    cursor.execute('SELECT * FROM ffencode_results limit 10')  # Update with your actual another table name
    table_data_2 = cursor.fetchall()

    # Close the database connection
    conn.close()

    if request.method == 'POST' and request.form.get('execute_script'):
        # Execute a Python script when the button is clicked
        subprocess.run(['python', 'your_script.py'])  # Update with your actual script name
        
    print ('diagnostic1')
    
    # Use raw string literal or forward slashes in the file path
    template_path = 'index.html'
    # Or use forward slashes:
    # template_path = "C:/Users/Chase/Documents/GitHub/index.html"

    # Render the template with the retrieved data
    return render_template(template_path, result_1=result_1, result_2=result_2, result_3=result_3, result_4=result_4, 
                           table_data_1=table_data_1, table_data_2=table_data_2)

# Run the Flask app in the Jupyter Notebook
if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple('localhost', 5000, app)
