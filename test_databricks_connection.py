import os
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient

load_dotenv()

databricks_host = os.getenv('DATABRICKS_HOST')
databricks_token = os.getenv('DATABRICKS_TOKEN')

w = WorkspaceClient(
    host=databricks_host,
    token=databricks_token
)
for cluster in w.clusters.list():
    print(f"Cluster ID: {cluster.cluster_id}, Cluster Name: {cluster.cluster_name}, State: {cluster.state}")
volume_path = "/Volumes/retailanalytic/default/retail_landing"
entries = list(w.files.list_directory_contents(volume_path))

print(f"Volume is accessible. Entries found: {len(entries)}")
for entry in entries:
    print(entry.path)
