# GitHub Secrets Checklist

Use this checklist when setting up GitHub Secrets for the automation workflow.

**Repository**: `YOUR_USERNAME/spotify-charts-automation`
**Location**: Settings → Secrets and variables → Actions → New repository secret

---

## ✅ Secrets to Configure (15 total; PLAYLIST_5_ID optional)

### 1. Spotify API (2 secrets)

- [ ] **SPOTIFY_CLIENT_ID**
  - Value: `{YOUR_SPOTIFY_CLIENT_ID}`
  - Get from: https://developer.spotify.com/dashboard

- [ ] **SPOTIFY_CLIENT_SECRET**
  - Value: `{YOUR_SPOTIFY_CLIENT_SECRET}`
  - Get from: https://developer.spotify.com/dashboard

---

### 2. Playlist IDs (5 secrets; 5th optional)

- [ ] **PLAYLIST_1_ID**
  - Value: `37i9dQZEVXbLp5XoPON0wI`
  - Name: Top Songs - USA

- [ ] **PLAYLIST_2_ID**
  - Value: `37i9dQZEVXbNG2KDcFcKOF`
  - Name: Top Songs - Global

- [ ] **PLAYLIST_3_ID**
  - Value: `37i9dQZEVXbKCOlAmDpukL`
  - Name: Top Albums - USA

- [ ] **PLAYLIST_4_ID**
  - Value: `37i9dQZEVXbJcin9K8o4a8`
  - Name: Top Albums - Global

- [ ] **PLAYLIST_5_ID** (optional)
  - Value: Your fifth playlist ID from Spotify (Share → Copy link to playlist; ID is the last part of the URL)
  - Leave empty or omit if you only use 4 playlists

---

### 3. Google Drive (2 secrets)

- [ ] **GOOGLE_DRIVE_CREDENTIALS**
  - Value: **Full JSON content** from `credentials/google-drive-credentials.json`
  - **Important**: Copy the entire file content including all `{}` braces
  - Example:
    ```json
    {
      "installed": {
        "client_id": "424761898050-...",
        "project_id": "spotifycharts-...",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "GOCSPX-...",
        "redirect_uris": ["http://localhost"]
      }
    }
    ```

- [ ] **GOOGLE_DRIVE_FOLDER_ID**
  - Value: `1cP-vP2xv30qjVJZj1gg-CmhJXEgFJ1Gj`
  - Get from: Your Google Drive folder URL

---

### 4. Email Configuration (6 secrets)

- [ ] **EMAIL_SMTP_SERVER**
  - Value: `smtp.gmail.com` (for Gmail)
  - Or: Your custom SMTP server

- [ ] **EMAIL_SMTP_PORT**
  - Value: `587` (TLS)
  - Or: `465` (SSL)

- [ ] **EMAIL_USERNAME**
  - Value: `{YOUR_EMAIL@gmail.com}`
  - Full email address

- [ ] **EMAIL_PASSWORD**
  - Value: `{YOUR_APP_PASSWORD}`
  - **For Gmail**: Use App Password (not regular password)
  - Generate at: https://myaccount.google.com/apppasswords

- [ ] **EMAIL_TO**
  - Value: `danbutwithanh@gmail.com`
  - Recipient email address

---

## 🔐 Security Tips

1. **Gmail App Password**: If using Gmail, you MUST use an App Password, not your regular password
   - Go to: https://myaccount.google.com/apppasswords
   - Generate new app password
   - Use that 16-character password

2. **Google Drive Credentials**: Make sure to copy the ENTIRE JSON file
   - Include opening `{` and closing `}`
   - Include all nested objects
   - Don't modify or format the JSON

3. **Never Commit Secrets**:
   - ✅ Store in GitHub Secrets
   - ❌ Never commit to repository
   - ❌ Never share in issues or PRs

---

## 📋 Quick Copy Template

Use this template to gather all values before adding to GitHub:

```
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=

PLAYLIST_1_ID=37i9dQZEVXbLp5XoPON0wI
PLAYLIST_2_ID=37i9dQZEVXbNG2KDcFcKOF
PLAYLIST_3_ID=37i9dQZEVXbKCOlAmDpukL
PLAYLIST_4_ID=37i9dQZEVXbJcin9K8o4a8
PLAYLIST_5_ID=

GOOGLE_DRIVE_CREDENTIALS={PASTE FULL JSON HERE}
GOOGLE_DRIVE_FOLDER_ID=1cP-vP2xv30qjVJZj1gg-CmhJXEgFJ1Gj

EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=
EMAIL_PASSWORD=
EMAIL_TO=danbutwithanh@gmail.com
```

---

## 🧪 Testing

After adding all secrets:

1. Go to **Actions** tab
2. Click **Spotify Charts Automation**
3. Click **Run workflow** → **Run workflow**
4. Monitor execution
5. Verify reports appear in Google Drive
6. Verify email received

---

## ❓ Common Issues

### "Secret not found" error
- Double-check secret name spelling (case-sensitive)
- Ensure secret is added to repository (not organization)

### Google Drive authentication fails
- Verify JSON is valid (use JSONLint.com)
- Ensure entire JSON content is copied
- Check for extra spaces or line breaks

### Email sending fails
- For Gmail, ensure App Password is used (not regular password)
- Enable "Less secure app access" if using regular SMTP
- Verify SMTP server and port are correct

### Workflow doesn't run
- Check if repository is active (push a commit)
- Verify workflow file is in `.github/workflows/` directory
- Ensure Actions are enabled in repository settings

---

**Next Steps**:
1. ✅ Fill in all required secrets in GitHub (14–15 with optional PLAYLIST_5_ID)
2. ✅ Run manual test workflow
3. ✅ Verify reports generated and uploaded
4. ✅ Wait for Thursday 11 PM PST automatic run

**Schedule**: Every Thursday at 11:00 PM PST (7:00 AM UTC Friday)
