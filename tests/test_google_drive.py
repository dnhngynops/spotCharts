#!/usr/bin/env python3
"""
Test script to verify Google Drive upload functionality
"""

import os
import sys
from datetime import datetime

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.google_drive_client import GoogleDriveClient

def test_google_drive_connection():
    """Test Google Drive authentication and connection"""
    print("=" * 70)
    print("Testing Google Drive Connection")
    print("=" * 70)

    try:
        print("\n1️⃣  Authenticating with Google Drive...")
        drive_client = GoogleDriveClient()
        print("   ✓ Successfully authenticated!")

        print("\n2️⃣  Creating test file...")
        test_file = "test_upload.txt"
        with open(test_file, 'w') as f:
            f.write(f"Test upload from Spotify Charts system\n")
            f.write(f"Timestamp: {datetime.now()}\n")
        print(f"   ✓ Created: {test_file}")

        print("\n3️⃣  Uploading test file to Google Drive...")
        file_id = drive_client.upload_file(test_file)
        print(f"   ✓ Upload successful!")
        print(f"   File ID: {file_id}")

        # Cleanup local test file
        os.remove(test_file)
        print(f"\n4️⃣  Cleanup complete")

        print("\n" + "=" * 70)
        print("✅ Google Drive Test Successful!")
        print("=" * 70)
        print(f"\nYour Google Drive integration is working correctly.")
        print(f"Files will be uploaded to the configured folder.")
        print(f"\nNote: You can delete the test file from Google Drive manually.")

        return True

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease set up Google Drive credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Enable Google Drive API")
        print("3. Create OAuth 2.0 credentials")
        print("4. Download and save as ./credentials/google-drive-credentials.json")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease check your Google Drive configuration:")
        print("- Credentials file exists at the configured path")
        print("- GOOGLE_DRIVE_FOLDER_ID is set in .env")
        print("- You have permission to upload to the folder")
        return False

if __name__ == "__main__":
    success = test_google_drive_connection()
    sys.exit(0 if success else 1)
