"""
Test script to verify archive endpoints work correctly.
Run this with the backend server running (uvicorn app.main:app --reload)
"""
import asyncio
import httpx


async def test_archive_endpoints():
    """Test creating and retrieving archives via API"""
    base_url = "http://localhost:8000"

    print("\n" + "="*60)
    print("TESTING ARCHIVE ENDPOINTS")
    print("="*60 + "\n")

    async with httpx.AsyncClient() as client:
        # Test 1: Get existing archives (should work even if empty)
        print("Test 1: GET /api/session-review/archives")
        try:
            response = await client.get(f"{base_url}/api/session-review/archives")
            print(f"  Status: {response.status_code}")
            archives = response.json()
            print(f"  Found {len(archives)} archive(s)")
            if archives:
                for i, archive in enumerate(archives, 1):
                    print(f"    Archive {i}: {archive['title']}")
            print("  ✓ PASS\n")
        except Exception as e:
            print(f"  ✗ FAIL: {e}\n")
            return

        # Test 2: Create a new archive
        print("Test 2: POST /api/session-review/archive")
        try:
            archive_data = {
                "title": "Test Archive from Script",
                "notes": "This is a test archive created by the test script to verify functionality.",
                "original_date": "2026-01-04"
            }
            response = await client.post(
                f"{base_url}/api/session-review/archive",
                json=archive_data
            )
            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                created_archive = response.json()
                print(f"  Created archive:")
                print(f"    ID: {created_archive['id']}")
                print(f"    Title: {created_archive['title']}")
                print(f"    Archived At: {created_archive['archived_at']}")
                print("  ✓ PASS\n")

                archive_id = created_archive['id']
            else:
                print(f"  ✗ FAIL: Expected 200, got {response.status_code}")
                print(f"  Response: {response.text}\n")
                return
        except Exception as e:
            print(f"  ✗ FAIL: {e}\n")
            return

        # Test 3: Verify archive appears in list
        print("Test 3: Verify archive appears in GET /api/session-review/archives")
        try:
            response = await client.get(f"{base_url}/api/session-review/archives")
            archives = response.json()

            found = any(a['id'] == archive_id for a in archives)
            if found:
                print(f"  Found newly created archive (ID: {archive_id}) in list")
                print("  ✓ PASS\n")
            else:
                print(f"  ✗ FAIL: Archive (ID: {archive_id}) not found in list")
                print(f"  Archives in list: {[a['id'] for a in archives]}\n")
                return
        except Exception as e:
            print(f"  ✗ FAIL: {e}\n")
            return

        # Test 4: Get specific archive
        print(f"Test 4: GET /api/session-review/archives/{archive_id}")
        try:
            response = await client.get(f"{base_url}/api/session-review/archives/{archive_id}")
            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                archive = response.json()
                print(f"  Retrieved archive: {archive['title']}")
                print("  ✓ PASS\n")
            else:
                print(f"  ✗ FAIL: Expected 200, got {response.status_code}\n")
                return
        except Exception as e:
            print(f"  ✗ FAIL: {e}\n")
            return

    print("="*60)
    print("ALL TESTS PASSED!")
    print("="*60 + "\n")
    print("Archive endpoints are working correctly.")
    print("The frontend should now be able to:")
    print("  1. Create archives successfully")
    print("  2. Retrieve all archives")
    print("  3. Display archives in the UI")
    print()


if __name__ == "__main__":
    print("\nMake sure the backend server is running:")
    print("  cd backend")
    print("  .\\venv\\Scripts\\Activate.ps1")
    print("  uvicorn app.main:app --reload")
    print()
    input("Press Enter when server is ready...")

    asyncio.run(test_archive_endpoints())
