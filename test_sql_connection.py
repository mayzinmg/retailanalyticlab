import os
from dotenv import load_dotenv
import csv
import pandas as pd
from databricks.sdk import WorkspaceClient

load_dotenv()

driver = os.getenv('DRIVER')
server = os.getenv('server')
database = os.getenv('database')
db_user = os.getenv('db_user')
password = os.getenv('password')
databricks_host = os.getenv('DATABRICKS_HOST')
databricks_token = os.getenv('DATABRICKS_TOKEN')
volume_path = "/Volumes/retailanalytic/default/retail_landing"

print (f"db_user: {db_user}")
print (f"driver: {driver}")
print (f"database: {database}")
conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={db_user};PWD={password};Encrypt=no;'
try:
    import pyodbc
    conn = pyodbc.connect(conn_str)
    print("Connection successful!")
    with conn.cursor() as cursor:
        cursor.execute("SELECT DB_NAME();")
        current_db = cursor.fetchone()[0]
        print("Current database:", current_db)

        locationid='E1000000-0000-0000-0000-000000000001'
        receipt_count = 0
        total_sales = 0
        cursor.execute("""
        SELECT m.*
        FROM dbo.SalesMaster AS m
        INNER JOIN dbo.Location AS l ON m.LocationId = l.LocationId
        WHERE l.LocationId = ?
        AND m.IngestedAtUtc BETWEEN ? AND ?;
        """, (locationid, '2026-11-05T04:00:00', '2026-11-05T05:00:00'))  # Replace 'YourTableName' with an actual table name
        rows = cursor.fetchall()
        for row in rows:
           receipt_count+= 1
           total_sales += row.TotalAmount  
        print(f"Total receipts for location {locationid}: {receipt_count}")
        print(f"Total sales for location {locationid}: {total_sales}")
    localcsv = "sales_data.csv"
    colums=[column[0] for column in cursor.description]
    print(f"Columns: {colums}")
    df=pd.DataFrame.from_records([tuple(row) for row in rows], columns=colums)
    df.to_csv(localcsv, index=False, quoting=csv.QUOTE_NONNUMERIC)

    databricks_host = os.getenv('DATABRICKS_HOST')
    databricks_token = os.getenv('DATABRICKS_TOKEN')

    w = WorkspaceClient(
        host=databricks_host,
        token=databricks_token
    )
    # Reuse the WorkspaceClient setup from your connection test
    w.files.upload_from(f"{volume_path}/{localcsv}", localcsv)    
    response=w.files.download(f"{volume_path}/{localcsv}")
    with response.contents as stream:
        df = pd.read_csv(stream, header=0, encoding="utf-8")
 
    print(f"Downloaded file content:\n{df.head()}")
    total_sum = df['TotalAmount'].sum()

    # Total number of rows
    row_count = len(df)  # or df.shape[0]

    print(f"Total Amount: {total_sum}")
    print(f"Row Count: {row_count}")

except Exception as e:
    print("An error occurred:")
    print(e)