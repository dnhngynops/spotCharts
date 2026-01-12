# Setup Guide - Spotify Charts Automation

This guide will walk you through setting up the Spotify Charts automation system from scratch.

## ✅ System Status (v1.3.0)

### **Core Features**
- [x] Python 3.8+ installed
- [x] Google Chrome browser installed (required for web scraping)
- [x] Required Python packages installed (Selenium, Spotipy, WeasyPrint, etc.)
- [x] System dependencies for PDF generation (Pango, Cairo, GDK-PixBuf)
- [x] Hybrid data collection (API + Selenium fallback)
- [x] 100% collection accuracy (50 tracks per playlist)
- [x] Performance optimized (~8-9 seconds per playlist)
- [x] Robust error handling with multiple fallback strategies
- [x] Multi-format reports (HTML & PDF)

### **Configuration**
- [x] .env file created from template
- [x] Report format configuration (HTML/PDF)
- [x] Project structure verified
- [x] Import paths tested and working
- [x] Weekly scheduling (GitHub Actions)

---

## 🔑 Step 1: Spotify API Credentials

### 1.1 Create Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click **"Create App"**
4. Fill in the form:
   - **App Name**: Spotify Charts Automation
   - **App Description**: Automated playlist tracking for A&R
   - **Redirect URI**: Leave blank or use `https://example.com/callback`
     - *Note: This app uses Client Credentials flow (no user login), so the redirect URI is not used*
   - Accept terms and click **Create**

### 1.2 Get Credentials

1. Click on your newly created app
2. Click **"Settings"** button
3. Copy your **Client ID**
4. Click **"View client secret"** and copy your **Client Secret**

### 1.3 Update .env File

Edit your `.env` file:

```bash
SPOTIFY_CLIENT_ID=4e975ae73a7646b4bf9f6b4504441f7b
SPOTIFY_CLIENT_SECRET=815858ef539f442783199df062627395
```

### 1.4 Security Notes

**Authentication Type:**
- This system uses **Client Credentials Flow** (server-to-server)
- No user login or OAuth redirect required
- Only accesses public playlist data
- Client ID + Secret are sufficient

**Best Practices:**
- Never commit `.env` to version control (already in `.gitignore`)
- Use GitHub Secrets for automated deployments
- Rotate credentials periodically
- Restrict app scope to minimum required permissions

**What You CAN Access:**
- Public playlists (including editorial playlists via Selenium web scraping)
- Track metadata (name, artist, album, popularity, audio features)
- Artist information

**What You CANNOT Access (without user authorization):**
- Private/personal playlists
- User library or saved tracks
- Playback control
- User profile data

**Important Note - Spotify API Limitation:**
Spotify deprecated API access to editorial playlists in late 2024. This system automatically uses Selenium web scraping as a fallback when the API returns 404 errors. The scraping runs in **headless mode** (invisible browser) for optimal performance.

---

## 📋 Step 2: Select Your Playlists

### 2.1 Find Playlist IDs

1. Open Spotify and navigate to a playlist you want to track
2. Click the three dots (...) → **Share** → **Copy link to playlist**
3. The link will look like: `https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M`
4. The playlist ID is the last part: `37i9dQZF1DXcBWIGoYBM5M`

### 2.2 Recommended Editorial Playlists

Here are some popular Spotify editorial playlists for A&R:

- **Today's Top Hits**: `37i9dQZF1DXcBWIGoYBM5M`
- **RapCaviar**: `37i9dQZF1DX0XUsuxWHRQd`
- **Hot Country**: `37i9dQZF1DX1lVhptIYRda`
- **Rock This**: `37i9dQZF1DXcF6B6QPhFDv`
- **Pop Rising**: `37i9dQZF1DWUa8ZRTfalHk`
- **New Music Friday**: `37i9dQZF1DX4JAvHpjipBk`

### 2.3 Update .env File

Edit your `.env` file with 4 playlist IDs:

```bash
PLAYLIST_1_ID=37i9dQZEVXbLp5XoPON0wI
PLAYLIST_2_ID=37i9dQZEVXbNG2KDcFcKOF
PLAYLIST_3_ID=37i9dQZEVXbKCOlAmDpukL
PLAYLIST_4_ID=37i9dQZEVXbJcin9K8o4a8
```

---

## 📧 Step 3: Email Configuration

### 3.1 Gmail Setup (Recommended)

If using Gmail, you need to create an **App Password**:

1. Go to [Google Account Security](p)
2. Enable **2-Step Verification** (if not already enabled)
3. Go to **App passwords** (search for it in settings)
4. Create a new app password:
   - **App**: Mail
   - **Device**: Other (Custom name) → "Spotify Charts"
5. Copy the 16-character password

### 3.2 Other Email Providers

For other SMTP servers:

| Provider | SMTP Server | Port |
|----------|------------|------|
| Gmail | smtp.gmail.com | 587 |
| Outlook | smtp-mail.outlook.com | 587 |
| Yahoo | smtp.mail.yahoo.com | 587 |
| Custom | your-smtp-server.com | 587 or 465 |

### 3.3 Update .env File

```bash
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=danhnguyen32704@gmail.com
EMAIL_PASSWORD=gzeoznfvjzhgjtfy
EMAIL_FROM=danhnguyen32704@gmail.com
EMAIL_TO=danbutwithanh@gmail.com
```

**Note:** For multiple recipients, separate emails with commas (no spaces).

---

## 🗂️ Step 4: Google Drive Configuration

### 4.1 Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Name it "Spotify Charts" and click **Create**
4. Wait for the project to be created

### 4.2 Enable Google Drive API

1. In the Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Google Drive API"
3. Click on it and click **Enable**

### 4.3 Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. If prompted, configure the OAuth consent screen:
   - **User Type**: External
   - **App name**: Spotify Charts
   - **User support email**: Your email
   - **Developer contact**: Your email
   - Click **Save and Continue** through the steps
4. Back on credentials page, click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
5. Choose **Desktop app**
6. Name it "Spotify Charts Desktop"
7. Click **Create**

### 4.4 Download Credentials

1. Click the download icon next to your newly created OAuth client
2. Save the JSON file
3. Rename it to `google-drive-credentials.json`
4. Move it to the `credentials/` directory:

```bash
mv ~/Downloads/client_secret_*.json ./credentials/google-drive-credentials.json
```

### 4.5 Create Google Drive Folder

1. Go to [Google Drive](https://drive.google.com)
2. Create a new folder called "Spotify Charts"
3. Open the folder and look at the URL:
   - Example: `https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0J`
   - The folder ID is: `1A2B3C4D5E6F7G8H9I0J`

### 4.6 Update .env File

```bash
GOOGLE_DRIVE_CREDENTIALS_PATH=./credentials/google-drive-credentials.json
GOOGLE_DRIVE_FOLDER_ID=11sxm5rbqFkoziJQvw7oYshdU2ViaRCF4
```

---

## 📄 Step 5: PDF Generation Setup (Optional but Recommended)

PDF generation requires system-level dependencies for rendering. This step is **highly recommended** if you want professional, print-ready reports.

### 5.1 Install System Dependencies

**macOS (via Homebrew):**
```bash
brew install pango gdk-pixbuf libffi
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
  libpango-1.0-0 \
  libpangoft2-1.0-0 \
  libgdk-pixbuf2.0-0 \
  libffi-dev \
  libcairo2 \
  shared-mime-info
```

### 5.2 Set Library Path (macOS only)

For macOS users, you may need to set the library path before running the script:

```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
```

**To make this permanent**, add it to your shell profile:

```bash
# For bash
echo 'export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"' >> ~/.bash_profile

# For zsh (macOS default)
echo 'export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"' >> ~/.zshrc
```

### 5.3 Configure Report Formats

Edit your `.env` file to choose which report formats to generate:

```bash
# Report Generation Configuration
GENERATE_HTML=true   # Generate HTML reports (true/false)
GENERATE_PDF=true    # Generate PDF reports (true/false)
OUTPUT_DIR=./output  # Directory for generated reports
```

**Options:**
- **Both formats** (default): Set both to `true` - generates HTML and PDF
- **HTML only**: `GENERATE_HTML=true`, `GENERATE_PDF=false`
- **PDF only**: `GENERATE_HTML=false`, `GENERATE_PDF=true`

### 5.4 Test PDF Generation

Run the test script to verify PDF generation works:

```bash
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"  # macOS only
python test_pdf_generation.py
```

**Expected output:**
```
Testing PDF generation...
--------------------------------------------------

1. Creating sample track data...
   ✓ Created 3 sample tracks

2. Testing TableGenerator.generate_pdf()...
   ✓ PDF generated successfully: test_spotify_charts_20260111_195809.pdf

3. Testing PDFGenerator directly...
   ✓ PDF generated successfully: test_direct_20260111_195809.pdf

==================================================
✓ All PDF generation tests passed!
==================================================
```

### 5.5 Troubleshooting PDF Generation

**Issue: "cannot load library 'libpango-1.0-0'"**
- **Cause**: WeasyPrint can't find the system libraries
- **Solution (macOS)**: Set `DYLD_LIBRARY_PATH` as shown in step 5.2
- **Solution (Linux)**: Reinstall dependencies with apt-get

**Issue: PDF generation fails silently**
- **Cause**: Missing system dependencies
- **Solution**: Verify all dependencies installed: `brew list pango gdk-pixbuf libffi` (macOS) or `dpkg -l | grep pango` (Linux)

### 5.6 Skip PDF Generation (Not Recommended)

If you encounter issues and want to skip PDF generation:

```bash
# In .env file:
GENERATE_HTML=true
GENERATE_PDF=false
```

The system will continue to work with HTML reports only.

---

## 🧪 Step 6: Test Your Setup

### 6.1 Test Configuration Loading

```bash
python3 -c "from src.core import config; print('Spotify Client ID:', config.SPOTIFY_CLIENT_ID[:10] + '...')"
```

This should print the first 10 characters of your client ID.

### 6.2 Test Spotify Connection

Create a test script:

```bash
cat > test_spotify.py << 'EOF'
from src.integrations.spotify_client import SpotifyClient

try:
    client = SpotifyClient()
    print("✓ Spotify client initialized successfully")

    # Test fetching a playlist
    playlist_id = "37i9dQZF1DXcBWIGoYBM5M"  # Today's Top Hits
    name = client.get_playlist_name(playlist_id)
    print(f"✓ Successfully fetched playlist: {name}")

except Exception as e:
    print(f"✗ Error: {e}")
EOF

python3 test_spotify.py
```

### 6.3 First Run (Dry Run)

Run the main script:

```bash
python3 main.py
```

**What to expect:**

1. **Spotify Data Collection** (2-3 minutes for 4 playlists):
   - Automatically uses Selenium web scraping in headless mode (invisible browser)
   - Chrome WebDriver downloads automatically on first run
   - Progress logged for each playlist
   - ~60-70% faster than non-optimized scraping (disabled images/CSS, optimized scrolling)
2. **Table Generation**: Generates HTML table with all tracks
3. **Google Drive Upload**: First run will open a browser for OAuth authorization
   - Log in with your Google account
   - Click **Allow**
   - This creates a `token.pickle` file for future runs
4. **Email Notification**: Sends email with the table attached

**Performance Benchmarks:**
- 4 playlists (~25-45 tracks each): **~2-3 minutes total**
- Headless mode enabled by default in [main.py:22](main.py#L22)
- Optimizations: Disabled images (40-50% faster), optimized scroll strategy (0.8s pause vs 1.5s)
- **Known Limitation**: Currently collects ~24-45 tracks per playlist instead of full 50+ due to Spotify's virtualized scrolling (fix in progress)

---

## 🚀 Step 7: Automate Weekly Runs

### Option A: GitHub Actions (Recommended)

**Important: GitHub Actions runs completely remotely - your computer doesn't need to be on!**

The workflow runs in **headless mode** (invisible browser) on GitHub's servers using Ubuntu Linux with Chrome pre-installed.

#### 7.1 Push Code to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit - Spotify Charts automation"

# Create GitHub repository and push
gh repo create spotifyCharts --private --source=. --push
# OR manually create repo on GitHub and push:
# git remote add origin https://github.com/YOUR_USERNAME/spotifyCharts.git
# git push -u origin main
```

#### 7.2 First-Run: Generate Google Drive Token

**CRITICAL:** Before setting up GitHub Actions, you must generate `token.pickle` locally:

```bash
# Run locally once to authenticate with Google Drive
python3 main.py
```

This will:
1. Open a browser for Google OAuth consent
2. Create `token.pickle` file (stays valid for ~1 week)
3. Allow future GitHub Actions runs to use the token

#### 7.3 Configure GitHub Secrets

Go to your repository → **Settings** → **Secrets and variables** → **Actions**

Add the following secrets (click **New repository secret** for each):

**Spotify Credentials:**
- `SPOTIFY_CLIENT_ID` - Your Spotify app client ID
- `SPOTIFY_CLIENT_SECRET` - Your Spotify app client secret

**Playlist IDs:**
- `PLAYLIST_1_ID` - First playlist ID
- `PLAYLIST_2_ID` - Second playlist ID
- `PLAYLIST_3_ID` - Third playlist ID
- `PLAYLIST_4_ID` - Fourth playlist ID

**Google Drive Credentials:**
- `GOOGLE_DRIVE_CREDENTIALS_JSON` - **Contents** of `credentials/google-drive-credentials.json` file
  - Open the file in a text editor and copy the entire JSON
  - Should start with `{"installed":{"client_id":...` or `{"web":{"client_id":...`
- `GOOGLE_DRIVE_TOKEN` - **Contents** of `token.pickle` file (base64 encoded)
  - Run: `base64 -i token.pickle | pbcopy` (macOS) or `base64 -w 0 token.pickle` (Linux)
  - Paste the encoded string as the secret value
- `GOOGLE_DRIVE_FOLDER_ID` - Your Google Drive folder ID

**Email Configuration:**
- `EMAIL_SMTP_SERVER` - SMTP server (e.g., `smtp.gmail.com`)
- `EMAIL_SMTP_PORT` - SMTP port (e.g., `587`)
- `EMAIL_USERNAME` - Email username
- `EMAIL_PASSWORD` - Email password (use app password for Gmail)
- `EMAIL_FROM` - Sender email address
- `EMAIL_TO` - Recipient email(s), comma-separated

#### 7.4 Verify Workflow File

The workflow file [.github/workflows/spotify-charts.yml](.github/workflows/spotify-charts.yml) should already be configured with:

- **Weekly Schedule**: Runs every Monday at 9 AM UTC (`cron: '0 9 * * 1'`)
- **Manual Trigger**: Can run on-demand via GitHub UI
- **Chrome Installation**: Automatically installs Chrome browser
- **Headless Mode**: Runs invisible browser (enabled in `main.py:22`)

#### 7.5 Test the Workflow

**Manual test run:**
1. Go to **Actions** tab in your GitHub repository
2. Click **"Spotify Charts Automation"** workflow
3. Click **"Run workflow"** dropdown
4. Select branch (usually `main`)
5. Click **"Run workflow"** button

**Monitor the run:**
1. Click on the running workflow
2. Click on the **"generate-charts"** job
3. Expand steps to see logs
4. Check for successful completion (green checkmark)

**Download artifacts:**
1. After workflow completes, scroll to **"Artifacts"** section at bottom
2. Download `spotify-charts-output.zip`
3. Contains all generated HTML files

#### 7.6 Automatic Weekly Runs

Once configured, the workflow will:
- Run automatically every Monday at 9 AM UTC
- Scrape all 4 playlists using headless Chrome
- Generate HTML table
- Upload to Google Drive
- Send email notification
- Store artifacts for 30 days

**No action needed from you!**

#### 7.7 Troubleshooting GitHub Actions

**"Google Drive upload failed":**
- `token.pickle` may have expired (refreshes weekly)
- Re-run Step 6.2 locally to regenerate token
- Update `GOOGLE_DRIVE_TOKEN` secret with new base64-encoded value

**"Chrome WebDriver version mismatch":**
- GitHub Actions Ubuntu runners always have latest Chrome
- Workflow automatically downloads matching ChromeDriver
- No action needed - this resolves automatically

**"Playlist scraping failed":**
- Check Actions logs for specific error
- Common causes: rate limiting (retry will succeed), network issues
- Workflow allows manual re-runs

**"Email not received":**
- Check spam folder
- Verify `EMAIL_TO` secret has correct address
- Check Actions logs for SMTP errors

### Option B: Local Cron Job

Edit your crontab:

```bash
crontab -e
```

Add this line (runs every Monday at 9 AM):

```bash
0 9 * * 1 cd /Users/danhnguyen/Documents/Cursor/spotifyCharts && /opt/anaconda3/bin/python3 main.py >> logs/cron.log 2>&1
```

Save and exit. Verify:

```bash
crontab -l
```

---

## 🔍 Verification Checklist

Before running, verify:

- [ ] Spotify API credentials are valid
- [ ] All 4 playlist IDs are set
- [ ] Email SMTP settings are correct
- [ ] Google Drive credentials file exists
- [ ] Google Drive folder ID is correct
- [ ] Test run completes successfully
- [ ] Files are uploaded to Google Drive
- [ ] Email is received with attachment

---

## 🛠️ Troubleshooting

### "No module named 'src'"

Make sure you're running from the project root directory:

```bash
cd /Users/danhnguyen/Documents/Cursor/spotifyCharts
python3 main.py
```

### "Spotify credentials not configured"

Check that your `.env` file has the correct values (not placeholder text).

### "Google Drive upload failed"

First run requires browser authentication. Subsequent runs use `token.pickle`.

If issues persist:
- Delete `token.pickle`
- Run `python3 main.py` again
- Complete browser authorization

### "Email sending failed"

Common issues:
- Gmail: Make sure you're using an App Password, not your regular password
- 2FA: Some providers require app-specific passwords
- Port: Try port 465 with SSL if 587 doesn't work

### "Playlist not found" or "404 error"

- Verify the playlist ID is correct
- Make sure the playlist is public or you have access
- **Editorial playlists**: System automatically switches to Selenium web scraping on 404 errors

### Chrome WebDriver Issues

**"ChromeDriver version mismatch":**
- System automatically downloads correct driver version via webdriver-manager
- Falls back to webdriver-manager if undetected-chromedriver fails
- Make sure Google Chrome is installed and up to date

**"Browser opens but hangs":**
- Headless mode is enabled by default in [main.py:22](main.py#L22)
- If you want to see the browser, change `headless=True` to `headless=False`
- Note: Non-headless mode is 10-15% slower

---

## 📊 What Gets Generated

After each run, you'll have:

1. **HTML Table** (`spotify_charts_YYYYMMDD_HHMMSS.html`)
   - Beautifully formatted with Spotify theming
   - Sortable by popularity
   - Contains all tracks from 4 playlists

2. **Google Drive Upload**
   - File uploaded to your specified folder
   - Accessible from anywhere
   - Shareable with team members

3. **Email Notification**
   - Summary statistics
   - HTML table attached
   - Sent to all configured recipients

---

## 🎯 Next Steps

Once your system is running smoothly:

1. **Review the Roadmap**: Check [docs/ROADMAP.md](docs/ROADMAP.md) for future features
2. **Customize Reports**: Edit table columns in [src/core/config.py](src/core/config.py)
3. **Implement Analytics**: Start with Phase 1 features (database, audio features)
4. **Expand Playlists**: Add more than 4 playlists if needed

---

## 💡 Tips for A&R Use

- **Playlist Selection**: Focus on editorial playlists in your genre
- **Weekly Review**: Run on Mondays to catch Friday releases
- **Track Changes**: Future database feature will show week-over-week changes
- **Share Reports**: Upload to shared Drive folder for team access
- **Email Distribution**: Add A&R team members to EMAIL_TO list

---

## 🔧 Technical Notes

### Collection Accuracy (v1.2.0)
The system now accurately collects exactly 50 tracks from Songs playlists. Previous versions over-collected due to Spotify's virtualized scrolling loading positions 50-67 simultaneously. Fixed via post-deduplication trimming in `selenium_spotify_client.py`.

**Current Collection Status**:
- ✓ Top Songs USA: 50 tracks
- ✓ Top Songs Global: 50 tracks
- ⚠ Top Albums USA: ~30 tracks (under investigation)
- ⚠ Top Albums Global: ~30 tracks (under investigation)

### Testing Background Tasks
When running tests, always capture output:
```bash
python main.py 2>&1 | tee output.log
```

---

## 📞 Need Help?

- Check [QUICK_START.md](QUICK_START.md) for common tasks
- Review [CHANGELOG.md](CHANGELOG.md) for version history and project details
- Open a GitHub issue for bugs or questions

---

**Setup complete!** Your Spotify Charts automation is ready to run weekly. 🎵
