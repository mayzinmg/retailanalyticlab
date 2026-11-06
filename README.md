# Retail Analytics & AI Lab

A hands-on data engineering project using synthetic point-of-sale receipts. It follows a small sales batch from Azure SQL into Databricks and uses the same Gold table to power an hourly sales dashboard and a read-only MCP tool.

## Demo result

On 5 November 2026, between noon and 1 PM Singapore time, Harbour Café recorded **$600.00 in sales across 30 receipts**, with an **average basket value of $20.00**. The dashboard and the Codex MCP tool call agreed on sales and receipt count.

## Data flow

| Stage | What it does |
| --- | --- |
| Azure SQL → landing | A local Python script queries a bounded batch from the synthetic sales database and uploads a CSV to a Databricks volume. |
| Bronze | A Databricks notebook loads the landed receipt rows into a Delta table. |
| Silver | The notebook converts the amount to a decimal, keeps sale time in Singapore local time, parses arrival time as UTC, and checks receipt key uniqueness. |
| Gold | The notebook groups receipts by location, local date, and hour to calculate sales, receipt count, and average basket value. |
| Dashboard and MCP | The Databricks dashboard and `get_hourly_sales` read the same Gold table. Codex calls the tool through a local MCP server. |

Arrival time determines when a receipt is eligible for extraction. Sale time determines which hour gets the revenue.

## Run the lab

### 1. Set up Python and access

You’ll need Python, a Microsoft ODBC Driver for SQL Server, an Azure SQL lab database containing synthetic receipts, and a Databricks workspace with a writable volume and access to a SQL warehouse. The demo used Databricks Free Edition.

From an active virtual environment, install the Python dependencies:

```powershell
python -m pip install pyodbc python-dotenv pandas databricks-sdk databricks-sql-connector "mcp>=1,<2"
```

Create a local `.env` using the setting names expected by your scripts. Example values:

```dotenv
DRIVER={ODBC Driver 18 for SQL Server}
server=tcp:<azure-sql-hostname>,1433
database=<synthetic-lab-database>
db_user=<read-only-user>
password=<local-secret>
DATABRICKS_HOST=https://<workspace-hostname>
DATABRICKS_SERVER_HOSTNAME=<workspace-hostname>
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/<warehouse-id>
DATABRICKS_TOKEN=<local-secret>
```

Copy the warehouse hostname and HTTP path from **SQL Warehouses → Connection details**. Keep `.env` and generated receipt files out of Git.

### 2. Load and verify the sales batch

1. Set the landing volume path in your local script and notebook. The path format is `/Volumes/<catalog>/<schema>/<volume>`.
2. Run `python test_databricks_connection.py` to verify volume access, then `python test_sql_connection.py` to extract and upload the batch.
3. Open the Databricks notebook from `notebooks/` and run the Bronze, Silver, and Gold cells in order. Set the CSV filename and table references to match your workspace.
4. Verify the Gold row for local hour `12`. It should show `600.0000` in sales and `30` receipts for the demo fixture.
5. Create a Databricks dashboard dataset from the Gold table. Add a bar chart with `LocalHour` on the X-axis and the sum of `TotalSales` on the Y-axis.

### 3. Call the read-only sales tool

`retail_tools.py` exposes `get_hourly_sales(location_id, sale_date, local_hour)` over MCP using STDIO. The tool uses a parameterized Gold-table query and distinguishes a missing row from a recorded zero.

Run the local MCP smoke test:

```powershell
python test_mcp_stdio.py
```

The client should discover `get_hourly_sales` and return `found: true`, `total_sales: "600.0000"`, and `receipt_count: 30` for the demo inputs.

To reproduce the Codex CLI demo, register the server from the project root and start a fresh session:

```powershell
codex mcp add retail-lab -- "$PWD\.venv\Scripts\python.exe" "$PWD\retail_tools.py"
codex
```

In Codex, check `/mcp` and ask it to call `get_hourly_sales` for your synthetic location ID on `2026-11-05` at local hour `12`. Compare the answer with the dashboard.

## Next milestone

Load more dates and locations, then use that history to build and evaluate a sales forecast. A later iteration can test late-arriving receipts, replay-safe incremental loads, and alerts that check data freshness before reporting a shortfall.

