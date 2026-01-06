"""
Complete end-to-end test: Upload via API + Query AI
"""
import asyncio
import httpx
import os

async def complete_upload_query_test():
    base_url = "http://localhost:8000/api/v1"
    
    # Test CSV content
    test_csv = """Product,Region,Sales,Date
iPhone 15,North America,15000,2025-01-15
Samsung Galaxy,Europe,12000,2025-01-16
Google Pixel,Asia,8000,2025-01-17"""
    
    print("=" * 70)
    print("COMPLETE UPLOAD + QUERY TEST")
    print("=" * 70)
    
    # Step 1: Upload file
    print("\n[1] Uploading test_product_sales.csv...")
    files = {
        'file': ('test_product_sales.csv', test_csv.encode(), 'text/csv')
    }
    
    try:
        async with httpx.AsyncClient() as client:
            upload_resp = await client.post(
                f"{base_url}/files/upload",
                files=files,
                timeout=90.0
            )
            
            if upload_resp.status_code == 200:
                data = upload_resp.json()
                print(f"   ✅ Upload Status: {data['status']}")
                print(f"   ✅ Message: {data['message']}")
                print(f"   ✅ File ID: {data['file_id']}")
            else:
                print(f"   ❌ Upload failed: {upload_resp.status_code}")
                print(f"   {upload_resp.text}")
                return
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        return
    
    # Step 2: Query AI immediately
    print("\n[2] Querying AI about the newly uploaded file...")
    
    queries = [
        "Do you have test_product_sales.csv dataset?",
        "List all my available datasets right now"
    ]
    
    for query in queries:
        print(f"\n   Query: '{query}'")
        try:
            async with httpx.AsyncClient() as client:
                chat_resp = await client.post(
                    f"{base_url}/chat/send",
                    json={"message": query, "agent": "researcher"},
                    timeout=60.0
                )
                
                if chat_resp.status_code == 200:
                    data = chat_resp.json()
                    response = data.get("response", "")
                    
                    if "test_product_sales" in response.lower():
                        print(f"   ✅ AI FOUND test_product_sales.csv!")
                    else:
                        print(f"   ❌ AI DID NOT find test_product_sales.csv")
                    
                    print(f"\n   AI Response:")
                    print(f"   {'-' * 66}")
                    print(f"   {response[:300]}...")
                    print(f"   {'-' * 66}")
                    
                    if data.get("sources"):
                        print(f"\n   Sources: {data['sources'][:3]}")
                else:
                    print(f"   ❌ Query failed: {chat_resp.status_code}")
        except Exception as e:
            print(f"   ❌ Query error: {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(complete_upload_query_test())
