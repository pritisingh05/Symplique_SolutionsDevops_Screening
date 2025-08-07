import os
from datetime import datetime, timedelta, timezone
import azure.functions as func
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient, StandardBlobTier

# Environment variables
COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
COSMOS_DB_NAME = os.environ["COSMOS_DB_NAME"]
COSMOS_CONTAINER_NAME = os.environ["COSMOS_CONTAINER_NAME"]
BLOB_CONN_STRING = os.environ["BLOB_CONN_STRING"]
BLOB_CONTAINER_NAME = os.environ["BLOB_CONTAINER_NAME"]

def main(mytimer: func.TimerRequest) -> None:
    utc_now = datetime.now(timezone.utc)
    cutoff_date = utc_now - timedelta(days=90)

    cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = cosmos_client.get_database_client(COSMOS_DB_NAME)
    container = database.get_container_client(COSMOS_CONTAINER_NAME)

    query = "SELECT * FROM c WHERE c.timestamp < @cutoff"
    items = list(container.query_items(
        query=query,
        parameters=[{"name": "@cutoff", "value": cutoff_date.isoformat()}],
        enable_cross_partition_query=True
    ))

    blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONN_STRING)
    blob_container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

    count = 0
    for item in items:
        blob_name = f"{item['id']}.json"
        blob_client = blob_container_client.get_blob_client(blob_name)
        blob_data = str(item).encode("utf-8")

        # Upload blob to cold tier
        blob_client.upload_blob(blob_data, overwrite=True, standard_blob_tier=StandardBlobTier.COLD)

        # Optionally delete the item or mark as archived in Cosmos DB
        container.delete_item(item, partition_key=item["partitionKey"])
        count += 1

    print(f"Archived {count} records to blob storage cold tier.")
