import os
import json
import azure.functions as func
from azure.cosmos import CosmosClient, exceptions as cosmos_exceptions
from azure.storage.blob import BlobServiceClient

# Environment variables - matches archive function conventions
COSMOS_ENDPOINT = os.environ["COSMOS_ENDPOINT"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
COSMOS_DB_NAME = os.environ["COSMOS_DB_NAME"]
COSMOS_CONTAINER_NAME = os.environ["COSMOS_CONTAINER_NAME"]
BLOB_CONN_STRING = os.environ["BLOB_CONN_STRING"]
BLOB_CONTAINER_NAME = os.environ["BLOB_CONTAINER_NAME"]

# Setup Cosmos client
cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = cosmos_client.get_database_client(COSMOS_DB_NAME)
container = database.get_container_client(COSMOS_CONTAINER_NAME)

# Setup Blob client
blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONN_STRING)
blob_container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

def main(req: func.HttpRequest) -> func.HttpResponse:
    # Assume route: /api/records/{id}
    record_id = req.route_params.get("id")
    if not record_id:
        return func.HttpResponse("Missing 'id' in URL.", status_code=400)

    # Try Cosmos DB first
    try:
        record = container.read_item(item=record_id, partition_key=record_id)
        return func.HttpResponse(json.dumps(record), mimetype="application/json", status_code=200)
    except cosmos_exceptions.CosmosResourceNotFoundError:
        pass  # Not in DB, try archive
    except Exception as e:
        # Log error, but continue to try archived layer
        print(f"CosmosDB error: {e}")

    # Fallback: Try Blob Storage for cold
    blob_name = f"{record_id}.json"
    blob_client = blob_container_client.get_blob_client(blob_name)
    try:
        blob_data = blob_client.download_blob().readall()
        record = json.loads(blob_data)
        return func.HttpResponse(json.dumps(record), mimetype="application/json", status_code=200, headers={"X-Archived":"true"})
    except Exception as e:
        print(f"Blob not found or error: {e}")
        return func.HttpResponse("Record not found.", status_code=404)
