
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

load_dotenv()

async def verify_blob_integration():
    print("--- Verifying DataAccessLayer Blob Integration ---")
    
    try:
        from app.core.data_access import get_data_access_layer
        
        dal = get_data_access_layer()
        
        # 1. Test Health Check
        health = dal.health_check()
        print(f"\nHealth Check: {health}")
        if not health.get("blob_available"):
            print("ERROR: Blob Storage not available in DataAccessLayer")
            return
            
        # 2. Test List All Files
        print("\nTesting list_all_files()...")
        files = await dal.list_all_files(limit=3)
        print(f"Found {len(files)} files (limit 3):")
        for f in files:
            print(f"  - {f.get('filename')} (ID: {f.get('file_id')})")
            
        if not files:
            print("Warning: No files found. Upload a file to test properly.")
            
        # 3. Test Retrieval with Query
        # Use a filename from the list if available, else 'csv'
        query = files[0].get('filename') if files else "csv"
        print(f"\nTesting retrieve(query='{query}')...")
        
        result = await dal.retrieve(query, use_rag=False, use_kag=False, use_blob=True)
        
        print(f"Has Data: {result.has_data}")
        print(f"Sources Used: {result.sources_used}")
        print("Blob Results:")
        for res in result.blob_results:
            print(f"  - {res}")
            print(f"    Summary: {res.get_metadata_summary()}")
            
        # 4. Test Context Text Generation
        print("\nGenerated Context Text:")
        print(result.get_context_text())

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_blob_integration())
