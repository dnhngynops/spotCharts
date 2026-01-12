#!/usr/bin/env python3
"""
Test script to verify Google Drive upload with date-based folder organization
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.google_drive_client import GoogleDriveClient
from src.core import config

def test_date_folder_upload():
    """Test Google Drive upload with date-based folder creation"""
    print("=" * 70)
    print("Testing Google Drive Upload with Date Folders")
    print("=" * 70)

    try:
        # Step 1: Authenticate
        print("\n1️⃣  Authenticating with Google Drive...")
        drive_client = GoogleDriveClient()
        print("   ✓ Successfully authenticated!")
        print(f"   Base folder ID: {config.GOOGLE_DRIVE_FOLDER_ID}")

        # Step 2: Create date folder
        date_folder_name = datetime.now().strftime('%Y-%m-%d')
        print(f"\n2️⃣  Creating/finding date folder: {date_folder_name}")
        date_folder_id = drive_client.get_or_create_folder(date_folder_name)
        print(f"   ✓ Date folder ready!")
        print(f"   Folder ID: {date_folder_id}")

        # Step 3: Create test files
        print(f"\n3️⃣  Creating test files...")
        test_files = []

        # Create a test HTML file
        html_file = "test_report.html"
        with open(html_file, 'w') as f:
            f.write(f"""
            <html>
                <head><title>Test Report</title></head>
                <body>
                    <h1>Spotify Charts Test Report</h1>
                    <p>Generated: {datetime.now()}</p>
                    <p>This is a test upload to verify date folder organization.</p>
                </body>
            </html>
            """)
        test_files.append(html_file)

        # Create test PDF file (mock)
        pdf_file = "test_Top_Songs_USA.txt"  # Using .txt to simulate
        with open(pdf_file, 'w') as f:
            f.write(f"Test PDF file for Top Songs - USA\n")
            f.write(f"Generated: {datetime.now()}\n")
        test_files.append(pdf_file)

        print(f"   ✓ Created {len(test_files)} test files")

        # Step 4: Upload files to date folder
        print(f"\n4️⃣  Uploading files to date folder...")
        uploaded_ids = []

        for test_file in test_files:
            file_id = drive_client.upload_file(test_file, folder_id=date_folder_id)
            uploaded_ids.append(file_id)
            print(f"   ✓ Uploaded {test_file} (ID: {file_id})")

        # Step 5: Cleanup local files
        print(f"\n5️⃣  Cleaning up local test files...")
        for test_file in test_files:
            os.remove(test_file)
        print(f"   ✓ Cleanup complete")

        # Success summary
        print("\n" + "=" * 70)
        print("✅ Test Successful!")
        print("=" * 70)
        print(f"\n📊 Summary:")
        print(f"   Base Folder: {config.GOOGLE_DRIVE_FOLDER_ID}")
        print(f"   Date Folder: {date_folder_name} (ID: {date_folder_id})")
        print(f"   Files Uploaded: {len(uploaded_ids)}")

        print(f"\n📁 Folder Structure:")
        print(f"   Your Main Folder/")
        print(f"   └── {date_folder_name}/")
        for i, test_file in enumerate(test_files):
            print(f"       {'├──' if i < len(test_files)-1 else '└──'} {os.path.basename(test_file)}")

        print(f"\n💡 View your files at:")
        print(f"   https://drive.google.com/drive/folders/{date_folder_id}")

        print(f"\n✨ The system will now create a new date folder each day!")
        print(f"   Example structure:")
        print(f"   Your Main Folder/")
        print(f"   ├── 2026-01-11/")
        print(f"   │   ├── spotify_charts_20260111.html")
        print(f"   │   ├── Top_Songs_-_USA_20260111.pdf")
        print(f"   │   └── ...")
        print(f"   ├── 2026-01-12/")
        print(f"   │   ├── spotify_charts_20260112.html")
        print(f"   │   └── ...")
        print(f"   └── ...")

        return True

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n📝 Setup Instructions:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Enable Google Drive API")
        print("3. Create OAuth 2.0 credentials (Desktop app)")
        print("4. Download and save as ./credentials/google-drive-credentials.json")
        print("5. Update GOOGLE_DRIVE_FOLDER_ID in .env file")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔍 Troubleshooting:")
        print("- Verify credentials file exists")
        print("- Check GOOGLE_DRIVE_FOLDER_ID in .env")
        print("- Ensure you have write permission to the folder")
        print("- Make sure folder ID is correct (from URL after /folders/)")
        return False

if __name__ == "__main__":
    success = test_date_folder_upload()
    sys.exit(0 if success else 1)
