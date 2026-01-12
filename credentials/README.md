# Credentials Directory

Place your Google Drive API credentials JSON file here.

## Setup Instructions

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Choose "Desktop app" as the application type
6. Download the JSON file
7. Rename it to `google-drive-credentials.json` and place it in this directory

**Note:** The `token.pickle` file will be automatically generated after the first authentication and should be kept secure (it's already in `.gitignore`).

