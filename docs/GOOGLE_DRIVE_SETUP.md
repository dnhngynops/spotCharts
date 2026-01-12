# Google Drive Integration Setup Guide

This guide will help you set up Google Drive integration for automatic report uploads with date-based folder organization.

## Overview

The system automatically:
1. Creates a date-based folder (e.g., "2026-01-12") in your Google Drive
2. Uploads all reports (HTML + PDFs) to that folder
3. Organizes reports by date for easy tracking

## Prerequisites

- Google account
- Access to Google Cloud Console
- Write permissions to the target Google Drive folder

## Step-by-Step Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **NEW PROJECT**
3. Enter project name: `Spotify Charts` (or any name)
4. Click **CREATE**

### Step 2: Enable Google Drive API

1. In your project, go to **APIs & Services > Library**
2. Search for "Google Drive API"
3. Click on it and click **ENABLE**

### Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. Select **External** user type
3. Click **CREATE**

Fill in the required fields:
- **App name**: `Spotify Charts Automation`
- **User support email**: Your email
- **Developer contact**: Your email

4. Click **SAVE AND CONTINUE**
5. Skip **Scopes** (click **SAVE AND CONTINUE**)
6. **Test users** section:
   - Click **+ ADD USERS**
   - Add your email: `danhnguyen32704@gmail.com`
   - Click **SAVE**
7. Click **SAVE AND CONTINUE**
8. Review and click **BACK TO DASHBOARD**

**Important**: Your app is now in "Testing" mode. Only test users can authenticate.

### Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Application type: **Desktop app**
4. Name: `Spotify Charts Desktop`
5. Click **CREATE**
6. Click **DOWNLOAD JSON** (downloads as `client_secret_*.json`)
7. Rename the file to `google-drive-credentials.json`
8. Move it to `./credentials/google-drive-credentials.json`

### Step 5: Get Your Google Drive Folder ID

1. Open [Google Drive](https://drive.google.com/)
2. Create or navigate to your folder (e.g., "Spotify Charts Reports")
3. Open the folder
4. Copy the Folder ID from the URL:
   ```
   https://drive.google.com/drive/folders/1cP-vP2xv30qjVJZj1gg-CmhJXEgFJ1Gj
                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                            This is your Folder ID
   ```

### Step 6: Configure Environment Variables

Update your `.env` file:

```bash
# Google Drive API
GOOGLE_DRIVE_CREDENTIALS_PATH=./credentials/google-drive-credentials.json
GOOGLE_DRIVE_FOLDER_ID=1cP-vP2xv30qjVJZj1gg-CmhJXEgFJ1Gj  # Your folder ID
```

### Step 7: First-Time Authentication

Run the test script:

```bash
python tests/test_google_drive_date_folders.py
```

**What happens:**
1. A browser window opens
2. You'll see a warning: "Google hasn't verified this app"
3. Click **Advanced** → **Go to Spotify Charts (unsafe)**
4. Click **Continue**
5. Select your Google account
6. Click **Allow** to grant permissions
7. The browser closes
8. A token file is saved: `./credentials/token.pickle`

**Note**: This is safe - you're authenticating your own app that you created.

### Step 8: Verify It Works

The test will:
- Create a date folder (e.g., "2026-01-12")
- Upload test files
- Show you the folder structure

Expected output:
```
✅ Test Successful!

📁 Folder Structure:
   Your Main Folder/
   └── 2026-01-12/
       ├── test_report.html
       └── test_Top_Songs_USA.txt
```

## Troubleshooting

### Error 403: access_denied

**Problem**: Your Google account is not added as a test user.

**Solution**:
1. Go to **OAuth consent screen**
2. Scroll to **Test users**
3. Click **+ ADD USERS**
4. Add your email
5. Try again

### Error: Credentials not found

**Problem**: JSON file is missing or in wrong location.

**Solution**:
- Verify file exists: `ls ./credentials/google-drive-credentials.json`
- Check path in `.env` matches actual location

### Error: Folder not found

**Problem**: Invalid `GOOGLE_DRIVE_FOLDER_ID`.

**Solution**:
- Double-check folder ID from Google Drive URL
- Ensure you have write permission to the folder
- Make sure folder exists and is not deleted

### Token expired

**Problem**: The token file is invalid.

**Solution**:
```bash
rm ./credentials/token.pickle
python tests/test_google_drive_date_folders.py
```

Re-authenticate when prompted.

## Folder Structure

After running the system, your Google Drive will look like:

```
Your Main Folder (ID: 1cP-vP2xv30qjVJZj1gg-CmhJXEgFJ1Gj)/
├── 2026-01-11/
│   ├── spotify_charts_20260111_153020.html
│   ├── Top_Songs_-_USA_20260111_153020.pdf
│   ├── Top_Songs_-_Global_20260111_153020.pdf
│   ├── Top_Albums_-_USA_20260111_153020.pdf
│   └── Top_Albums_-_Global_20260111_153020.pdf
│
├── 2026-01-12/
│   ├── spotify_charts_20260112_090000.html
│   ├── Top_Songs_-_USA_20260112_090000.pdf
│   ├── Top_Songs_-_Global_20260112_090000.pdf
│   ├── Top_Albums_-_USA_20260112_090000.pdf
│   └── Top_Albums_-_Global_20260112_090000.pdf
│
└── 2026-01-13/
    └── ...
```

## Running the Full System

Once Google Drive is configured, run:

```bash
python main.py
```

This will:
1. ✅ Collect tracks from 4 Spotify playlists (200 tracks)
2. ✅ Generate 1 HTML + 4 PDF reports
3. ✅ Create today's date folder in Google Drive
4. ✅ Upload all 5 files to the date folder
5. ✅ Send email notification with files attached

## Security Notes

- **Credentials file**: Never commit `google-drive-credentials.json` to git (already in `.gitignore`)
- **Token file**: Never commit `token.pickle` to git (already in `.gitignore`)
- **Testing mode**: Your app is in testing mode - only test users can authenticate
- **Production**: To allow anyone to use it, publish your app (requires Google verification)

## Next Steps

1. ✅ Complete OAuth setup (add test user)
2. ✅ Run test script to verify Google Drive works
3. ✅ Run full system: `python main.py`
4. ✅ Verify reports in Google Drive
5. ✅ (Optional) Set up automated scheduling with GitHub Actions

## Support

If you encounter issues:
1. Check the [Google Cloud Console](https://console.cloud.google.com/) for errors
2. Verify test user is added
3. Delete token and re-authenticate
4. Review Google Drive API quotas (should be sufficient for this use case)

---

**Your Google Drive integration is now configured!** 🎉

Reports will automatically organize by date in your specified folder.
