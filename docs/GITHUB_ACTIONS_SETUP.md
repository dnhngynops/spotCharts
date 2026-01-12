# GitHub Actions Setup Guide

This guide explains how to configure GitHub Actions to automatically run the Spotify Charts automation every **Thursday at 11 PM PST**.

---

## Schedule Configuration

The workflow is configured to run:
- **Day**: Every Thursday
- **Time**: 11:00 PM PST (Pacific Standard Time)
- **UTC Time**: 7:00 AM UTC Friday (PST is UTC-8)
- **Cron Expression**: `0 7 * * 5` (7 AM UTC every Friday)

**Note**: GitHub Actions uses UTC time. Since PST is UTC-8, Thursday 11 PM PST = Friday 7 AM UTC.

---

## Step 1: Push Your Code to GitHub

1. **Initialize Git repository** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Spotify Charts automation v1.5.0"
   ```

2. **Create GitHub repository**:
   - Go to [GitHub.com](https://github.com/new)
   - Create a new repository (e.g., `spotify-charts-automation`)
   - Do NOT initialize with README, .gitignore, or license (we already have these)

3. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/spotify-charts-automation.git
   git branch -M main
   git push -u origin main
   ```

---

## Step 2: Configure GitHub Secrets

GitHub Secrets store sensitive credentials securely. The workflow needs the following secrets:

### 2.1 Navigate to Repository Settings

1. Go to your GitHub repository
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**

### 2.2 Add Required Secrets

Add each of the following secrets one by one:

#### Spotify API Credentials

| Secret Name | Value | Where to Find |
|-------------|-------|---------------|
| `SPOTIFY_CLIENT_ID` | Your Spotify Client ID | [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) |
| `SPOTIFY_CLIENT_SECRET` | Your Spotify Client Secret | Same as above |

#### Playlist IDs

| Secret Name | Value | Example |
|-------------|-------|---------|
| `PLAYLIST_1_ID` | Top Songs - USA playlist ID | `37i9dQZEVXbLp5XoPON0wI` |
| `PLAYLIST_2_ID` | Top Songs - Global playlist ID | `37i9dQZEVXbNG2KDcFcKOF` |
| `PLAYLIST_3_ID` | Top Albums - USA playlist ID | `37i9dQZEVXbKCOlAmDpukL` |
| `PLAYLIST_4_ID` | Top Albums - Global playlist ID | `37i9dQZEVXbJcin9K8o4a8` |

#### Google Drive Configuration

| Secret Name | Value | Where to Find |
|-------------|-------|---------------|
| `GOOGLE_DRIVE_CREDENTIALS` | **Full JSON content** of your credentials file | Copy entire contents of `credentials/google-drive-credentials.json` |
| `GOOGLE_DRIVE_FOLDER_ID` | Your Google Drive folder ID | From folder URL: `1cP-vP2xv30qjVJZj1gg-CmhJXEgFJ1Gj` |

**Important**: For `GOOGLE_DRIVE_CREDENTIALS`, copy the **entire JSON file content**, including all braces `{}`. Example:
```json
{
  "installed": {
    "client_id": "424761898050-...",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_SECRET_HERE",
    "redirect_uris": ["http://localhost"]
  }
}
```

#### Email Configuration

| Secret Name | Value | Example |
|-------------|-------|---------|
| `EMAIL_SMTP_SERVER` | SMTP server address | `smtp.gmail.com` |
| `EMAIL_SMTP_PORT` | SMTP port | `587` |
| `EMAIL_USERNAME` | Your email address | `your-email@gmail.com` |
| `EMAIL_PASSWORD` | Email password or app password | For Gmail, use [App Password](https://support.google.com/accounts/answer/185833) |
| `EMAIL_TO` | Recipient email address | `recipient@gmail.com` |

---

## Step 3: Verify Secrets Configuration

After adding all secrets, you should have **14 secrets** in total:

1. ✅ SPOTIFY_CLIENT_ID
2. ✅ SPOTIFY_CLIENT_SECRET
3. ✅ PLAYLIST_1_ID
4. ✅ PLAYLIST_2_ID
5. ✅ PLAYLIST_3_ID
6. ✅ PLAYLIST_4_ID
7. ✅ GOOGLE_DRIVE_CREDENTIALS
8. ✅ GOOGLE_DRIVE_FOLDER_ID
9. ✅ EMAIL_SMTP_SERVER
10. ✅ EMAIL_SMTP_PORT
11. ✅ EMAIL_USERNAME
12. ✅ EMAIL_PASSWORD
13. ✅ EMAIL_TO

---

## Step 4: Test the Workflow

### Manual Test Run

Before waiting for the scheduled run, test the workflow manually:

1. Go to your GitHub repository
2. Click **Actions** tab
3. Click **Spotify Charts Automation** workflow (left sidebar)
4. Click **Run workflow** button (right side)
5. Select branch: `main`
6. Click **Run workflow**

### Monitor Execution

1. Click on the running workflow to see live logs
2. Watch each step execute:
   - ✅ Checkout repository
   - ✅ Install dependencies
   - ✅ Run automation
   - ✅ Upload reports to Google Drive
   - ✅ Send email notification

### Verify Results

After successful execution:
1. **Check Google Drive**: New folder with today's date should contain 5 reports
2. **Check Email**: You should receive an email with attached reports
3. **Check GitHub Actions**: Green checkmark indicates success

---

## Step 5: Understand the Schedule

### When Will It Run?

- **Day**: Every Thursday
- **Time**: 11:00 PM PST (Pacific Standard Time)
- **Your local time**: Thursday 11:00 PM PST
- **Server time (UTC)**: Friday 7:00 AM UTC

### Cron Expression Breakdown

```yaml
cron: '0 7 * * 5'
       │ │ │ │ │
       │ │ │ │ └─── Day of week (5 = Friday in UTC)
       │ │ │ └───── Month (1-12, * = every month)
       │ │ └─────── Day of month (1-31, * = every day)
       │ └───────── Hour (0-23, 7 = 7 AM UTC)
       └─────────── Minute (0-59, 0 = on the hour)
```

### Why Friday in UTC?

Because PST is 8 hours behind UTC:
- Thursday 11:00 PM PST = Friday 7:00 AM UTC

---

## Troubleshooting

### Workflow Not Running

**Problem**: Workflow doesn't run at scheduled time

**Solutions**:
1. **Check repository activity**: GitHub may disable workflows in inactive repos
2. **Verify schedule**: Confirm cron expression is correct
3. **Check Actions**: Go to Actions tab, ensure workflow is enabled
4. **Repository access**: GitHub Actions must be enabled in repository settings

### Authentication Errors

**Problem**: Google Drive or Spotify API authentication fails

**Solutions**:
1. **Verify secrets**: Double-check all secret values are correct
2. **Google Drive token**: You may need to re-authenticate locally first
3. **API credentials**: Ensure credentials haven't expired

### Chrome/Selenium Issues

**Problem**: Selenium can't find Chrome or browser fails to start

**Solutions**:
1. The workflow uses `browser-actions/setup-chrome@latest` to install Chrome
2. Chrome runs in headless mode (no GUI needed)
3. Check logs for specific Selenium errors

### WeasyPrint Library Errors

**Problem**: PDF generation fails with library errors

**Solutions**:
1. The workflow pre-installs all required libraries:
   - libpango-1.0-0
   - libpangoft2-1.0-0
   - libgdk-pixbuf2.0-0
2. Ubuntu environment has these libraries available
3. No macOS-specific library path issues

---

## Advanced Configuration

### Change Schedule

To change the schedule, edit `.github/workflows/spotify-charts-automation.yml`:

```yaml
schedule:
  - cron: '0 7 * * 5'  # Current: Thursday 11 PM PST
```

**Examples**:

| Description | Cron Expression | PST Time |
|-------------|----------------|----------|
| Every Monday 9 AM PST | `0 17 * * 1` | Monday 9:00 AM |
| Every Friday 6 PM PST | `0 2 * * 6` | Friday 6:00 PM |
| Daily at midnight PST | `0 8 * * *` | Daily 12:00 AM |
| Every Sunday 10 AM PST | `0 18 * * 0` | Sunday 10:00 AM |

**PST to UTC Conversion**:
- PST = UTC - 8 hours
- Example: 11 PM PST = 11 PM + 8 hours = 7 AM UTC (next day)

### Add Notifications

To get notified on failures, you can:

1. **Email on failure**: Already included in workflow
2. **Slack notifications**: Add Slack webhook secret and action
3. **GitHub notifications**: Automatically enabled (check your email)

### Multiple Schedules

Run at multiple times:

```yaml
schedule:
  - cron: '0 7 * * 5'   # Thursday 11 PM PST
  - cron: '0 17 * * 1'  # Monday 9 AM PST
```

---

## Workflow Features

### What Happens During Each Run

1. **Checkout Code**: Downloads latest code from repository
2. **Setup Environment**: Installs Python 3.11, Chrome, system libraries
3. **Install Dependencies**: Installs Python packages from requirements.txt
4. **Configure Credentials**: Sets up .env file and Google Drive credentials
5. **Run Automation**:
   - Collect 200 tracks from 4 playlists (Selenium + API enrichment)
   - Generate 1 HTML + 4 PDF reports
   - Upload to Google Drive (date-based folder)
   - Send email notification with attachments
6. **Error Handling**: Uploads logs if anything fails

### Execution Time

- **Average runtime**: ~3-4 minutes
- **Selenium scraping**: ~2 minutes (4 playlists)
- **Report generation**: ~30 seconds
- **Upload & email**: ~30 seconds

### Cost

- **GitHub Actions**: Free for public repositories
- **GitHub Actions**: 2,000 minutes/month free for private repositories
- **This workflow**: ~4 minutes per run = ~16 minutes/month (4 runs)
- **Conclusion**: Well within free tier limits

---

## Security Best Practices

### Protect Your Secrets

1. ✅ **Never commit credentials** to repository
2. ✅ **Use GitHub Secrets** for all sensitive data
3. ✅ **Rotate credentials** periodically
4. ✅ **Use app passwords** instead of real passwords (Gmail)
5. ✅ **Limit API permissions** to minimum required

### Repository Settings

1. **Private repository**: Consider making repo private if it contains business logic
2. **Branch protection**: Require reviews for changes to main branch
3. **Required checks**: Make workflow required before merging PRs

---

## Monitoring & Maintenance

### Check Workflow Status

1. **Actions tab**: View all workflow runs
2. **Email notifications**: GitHub sends email on failures
3. **Google Drive**: Verify new date folder appears each week
4. **Email inbox**: Confirm weekly report emails arrive

### Regular Maintenance

- **Weekly**: Verify reports generated correctly
- **Monthly**: Check GitHub Actions usage (should be minimal)
- **Quarterly**: Rotate API credentials and passwords
- **Yearly**: Update dependencies in requirements.txt

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Cron Expression Generator](https://crontab.guru/)
- [GitHub Actions Pricing](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions)
- [Spotify API Documentation](https://developer.spotify.com/documentation/web-api)
- [Google Drive API Documentation](https://developers.google.com/drive/api/guides/about-sdk)

---

## Quick Reference Commands

### View workflow locally
```bash
cat .github/workflows/spotify-charts-automation.yml
```

### Test locally before pushing
```bash
# Set library path (macOS only)
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"

# Run the automation
python main.py
```

### Push workflow to GitHub
```bash
git add .github/workflows/spotify-charts-automation.yml
git commit -m "Add GitHub Actions workflow for weekly automation"
git push origin main
```

### Check workflow status (GitHub CLI)
```bash
# Install GitHub CLI: https://cli.github.com/
gh workflow list
gh run list --workflow=spotify-charts-automation.yml
gh run view  # View latest run
```

---

**Last Updated**: 2026-01-12
**Workflow Version**: 1.0
**Schedule**: Every Thursday at 11 PM PST (7 AM UTC Friday)
