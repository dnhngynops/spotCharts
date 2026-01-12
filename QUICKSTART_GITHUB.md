# Quick Start: GitHub Actions Setup

Get your Spotify Charts automation running on GitHub in **5 simple steps**.

---

## 🚀 Step 1: Push to GitHub (2 minutes)

```bash
# Initialize git if needed
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Spotify Charts automation v1.5.0"

# Create GitHub repo at: https://github.com/new
# Then push:
git remote add origin https://github.com/YOUR_USERNAME/spotify-charts-automation.git
git branch -M main
git push -u origin main
```

---

## 🔐 Step 2: Add GitHub Secrets (5 minutes)

Go to: **Your Repo → Settings → Secrets and variables → Actions**

### Click "New repository secret" and add each of these 14 secrets:

#### Spotify (2 secrets)
```
SPOTIFY_CLIENT_ID = (from https://developer.spotify.com/dashboard)
SPOTIFY_CLIENT_SECRET = (from same place)
```

#### Playlists (4 secrets)
```
PLAYLIST_1_ID = 37i9dQZEVXbLp5XoPON0wI
PLAYLIST_2_ID = 37i9dQZEVXbNG2KDcFcKOF
PLAYLIST_3_ID = 37i9dQZEVXbKCOlAmDpukL
PLAYLIST_4_ID = 37i9dQZEVXbJcin9K8o4a8
```

#### Google Drive (2 secrets)
```
GOOGLE_DRIVE_CREDENTIALS = (paste ENTIRE JSON from credentials/google-drive-credentials.json)
GOOGLE_DRIVE_FOLDER_ID = 1cP-vP2xv30qjVJZj1gg-CmhJXEgFJ1Gj
```

#### Email (6 secrets)
```
EMAIL_SMTP_SERVER = smtp.gmail.com
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = your-email@gmail.com
EMAIL_PASSWORD = (Gmail App Password from https://myaccount.google.com/apppasswords)
EMAIL_TO = danbutwithanh@gmail.com
```

**📝 Tip**: Use the [Secrets Checklist](docs/SECRETS_CHECKLIST.md) as a reference!

---

## 🧪 Step 3: Test the Workflow (3 minutes)

1. Go to **Actions** tab in your GitHub repo
2. Click **Spotify Charts Automation** (left sidebar)
3. Click **Run workflow** button (right side)
4. Select branch: `main`
5. Click **Run workflow** (green button)

**Watch it run**:
- ✅ Setup environment (~1 min)
- ✅ Run automation (~2-3 min)
- ✅ Upload to Google Drive (~10 sec)
- ✅ Send email (~5 sec)

---

## ✅ Step 4: Verify Results (1 minute)

Check three places:

1. **GitHub Actions**: Should show ✅ green checkmark
2. **Google Drive**: New `2026-01-12` folder with 5 files
3. **Email**: Check inbox for report email with attachments

---

## 📅 Step 5: Wait for Automatic Run

**Your automation is now live!**

- **Schedule**: Every Thursday at 11:00 PM PST
- **Next run**: Check "Actions" tab for next scheduled run
- **No action needed**: Just wait for reports to arrive in your inbox!

---

## 🎉 You're Done!

Your Spotify Charts automation will now run automatically every Thursday at 11 PM PST.

### What happens each week:

```
Thursday 11:00 PM PST
    ↓
GitHub Actions starts workflow
    ↓
Collects 200 tracks (4 playlists × 50 tracks)
    ↓
Generates 1 HTML + 4 PDF reports
    ↓
Creates date folder in Google Drive (e.g., "2026-01-19")
    ↓
Uploads all 5 reports to folder
    ↓
Emails reports to: danbutwithanh@gmail.com
    ↓
Done! ✅
```

---

## 📚 Need Help?

- **Full setup guide**: [docs/GITHUB_ACTIONS_SETUP.md](docs/GITHUB_ACTIONS_SETUP.md)
- **Secrets checklist**: [docs/SECRETS_CHECKLIST.md](docs/SECRETS_CHECKLIST.md)
- **Architecture docs**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Troubleshooting**: See "Troubleshooting" section in setup guide

---

## 🔧 Advanced: Change Schedule

Want to run at a different time? Edit `.github/workflows/spotify-charts-automation.yml`:

```yaml
schedule:
  - cron: '0 7 * * 5'  # Current: Thursday 11 PM PST
```

**Examples**:

| Description | Cron | PST Time |
|-------------|------|----------|
| Monday 9 AM PST | `0 17 * * 1` | Mon 9:00 AM |
| Friday 6 PM PST | `0 2 * * 6` | Fri 6:00 PM |
| Daily midnight PST | `0 8 * * *` | Daily 12:00 AM |

**Remember**: PST = UTC - 8 hours

---

## ❓ Common Issues

### "Secret not found"
- Check spelling (case-sensitive!)
- Ensure secret is in repository (not organization)

### Google Drive auth fails
- Paste ENTIRE JSON (including `{}`)
- Verify JSON is valid at [JSONLint.com](https://jsonlint.com)

### Email not sending
- Use Gmail App Password (not regular password)
- Generate at: https://myaccount.google.com/apppasswords

### Workflow doesn't run
- Push a commit to activate repository
- Check workflow file is in `.github/workflows/`
- Enable Actions in repo settings

---

**Next Scheduled Run**: Thursday, 11:00 PM PST
**Execution Time**: ~3-4 minutes
**Cost**: FREE (within GitHub Actions free tier)
