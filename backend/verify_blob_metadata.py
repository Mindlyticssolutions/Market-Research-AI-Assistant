
import os
import sys
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

load_dotenv()

CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_STORAGE_CONTAINER")

def list_blobs_with_metadata():
    if not CONNECTION_STRING:
        print("Error: AZURE_STORAGE_CONNECTION_STRING not found in .env")
        return

    try:
        blob_service_client = BlobServiceClient.from_connection_string(CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        
        if not container_client.exists():
            print(f"Container '{CONTAINER_NAME}' does not exist.")
            return

        print(f"Listing blobs in container: {CONTAINER_NAME}")
        blobs = container_client.list_blobs(include=["metadata"])
        
        count = 0
        for blob in blobs:
            count += 1
            print(f"\n--- Blob {count} ---")
            print(f"Name: {blob.name}")
            print(f"Start Metadata:")
            if blob.metadata:
                for k, v in blob.metadata.items():
                    print(f"  {k}: {v}")
            else:
                print("  (No metadata found)")
            print("End Metadata")
            
            if count >= 3:
                print("\n(Showing first 3 blobs only)")
                break
                
        if count == 0:
            print("No blobs found in container.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_blobs_with_metadata()
