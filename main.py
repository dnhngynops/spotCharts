"""
Main orchestration script for Spotify Charts automation
"""
import os
from datetime import datetime
from src.integrations.spotify_client import SpotifyClient
from src.reporting.table_generator import TableGenerator
from src.reporting.dashboard_generator import DashboardGenerator
from src.integrations.google_drive_client import GoogleDriveClient
from src.integrations.email_client import EmailClient
from src.core import config


def main():
    """Main execution function"""
    print("Starting Spotify Charts automation...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Step 1: Collect tracks from Spotify playlists using Selenium + API enrichment
        print("\n1. Collecting tracks from Spotify playlists...")
        print("   Using Selenium scraping (primary) + Spotify API enrichment")
        # Use headless mode to run browser invisibly (faster and no visible window)
        # API enrichment is enabled by default to add metadata like popularity, preview URLs, etc.
        with SpotifyClient(use_api_enrichment=True, headless=True) as spotify_client:
            tracks = spotify_client.get_all_playlist_tracks(config.PLAYLIST_IDS)
            print(f"   ✓ Collected {len(tracks)} tracks across {len(config.PLAYLIST_IDS)} playlists")

        if not tracks:
            print("   No tracks found. Exiting.")
            return
        
        # Step 2: Generate reports
        print("\n2. Generating reports...")
        table_generator = TableGenerator()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Create output directory if needed
        output_dir = config.REPORT_CONFIG['output_dir']
        os.makedirs(output_dir, exist_ok=True)

        generated_files = []

        # Group tracks by playlist
        from collections import defaultdict
        tracks_by_playlist = defaultdict(list)
        for track in tracks:
            playlist_name = track.get('playlist', 'Unknown Playlist')
            tracks_by_playlist[playlist_name].append(track)

        print(f"   Grouped tracks into {len(tracks_by_playlist)} playlists")

        # Generate HTML dashboard with cross-playlist analytics
        if config.REPORT_CONFIG['formats']['html']:
            print("   Generating HTML dashboard with analytics...")
            dashboard_generator = DashboardGenerator()
            html_filename = f'spotify_charts_dashboard_{timestamp}.html'
            html_file_path = os.path.join(output_dir, html_filename)
            dashboard_generator.generate_dashboard(tracks, html_file_path)
            generated_files.append(html_file_path)
            print(f"   ✓ HTML dashboard saved to: {html_file_path}")

        # Generate separate PDF for each playlist if configured
        if config.REPORT_CONFIG['formats']['pdf']:
            print("   Generating PDF reports (one per playlist)...")

            for playlist_name, playlist_tracks in tracks_by_playlist.items():
                # Sanitize playlist name for filename
                safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in playlist_name)
                safe_name = safe_name.strip().replace(' ', '_')

                pdf_filename = f'{safe_name}_{timestamp}.pdf'
                pdf_file_path = table_generator.generate_pdf(
                    playlist_tracks,
                    pdf_filename,
                    playlist_name=playlist_name
                )
                generated_files.append(pdf_file_path)
                print(f"   ✓ PDF for '{playlist_name}': {pdf_file_path} ({len(playlist_tracks)} tracks, single continuous page)")

        if not generated_files:
            print("   Warning: No report formats enabled in configuration")
            return

        # Step 3: Upload to Google Drive
        print("\n3. Uploading to Google Drive...")
        uploaded_file_ids = []
        try:
            drive_client = GoogleDriveClient()

            # Create date-based folder (e.g., "2026-01-12")
            date_folder_name = datetime.now().strftime('%Y-%m-%d')
            print(f"   Creating/finding date folder: {date_folder_name}")
            date_folder_id = drive_client.get_or_create_folder(date_folder_name)
            print(f"   ✓ Date folder ready (ID: {date_folder_id})")

            # Upload files to the date folder
            for file_path in generated_files:
                file_id = drive_client.upload_file(file_path, folder_id=date_folder_id)
                uploaded_file_ids.append(file_id)
                print(f"   ✓ Uploaded {os.path.basename(file_path)} (ID: {file_id})")
        except Exception as e:
            print(f"   Warning: Failed to upload to Google Drive: {e}")
            print("   Continuing with email notification...")

        # Step 4: Send email notification
        print("\n4. Sending email notification...")
        try:
            email_client = EmailClient()
            email_subject = f"Spotify Charts - {datetime.now().strftime('%Y-%m-%d')}"

            # Build format list for email
            formats_list = []
            if config.REPORT_CONFIG['formats']['html']:
                formats_list.append("HTML")
            if config.REPORT_CONFIG['formats']['pdf']:
                formats_list.append("PDF")
            formats_text = " and ".join(formats_list)

            email_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; background-color: #121212; color: #FFFFFF; padding: 20px;">
                    <h2 style="color: #1DB954;">Spotify Charts Update</h2>
                    <p>Your Spotify charts have been generated and uploaded to Google Drive.</p>
                    <p><strong>Total Tracks:</strong> {len(tracks)}</p>
                    <p><strong>Playlists:</strong> {len(config.PLAYLIST_IDS)}</p>
                    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Formats:</strong> {formats_text}</p>
                    <p>The reports are attached to this email.</p>
                </body>
            </html>
            """
            email_client.send_email(
                subject=email_subject,
                body=email_body,
                attachments=generated_files
            )
            print("   ✓ Email sent successfully")
        except Exception as e:
            print(f"   Warning: Failed to send email: {e}")
        
        # Cleanup (optional - remove local files after upload)
        # Uncomment the lines below if you want to delete local files after upload
        # for file_path in generated_files:
        #     os.remove(file_path)
        
        print("\n✓ Automation completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error during automation: {e}")
        raise


if __name__ == '__main__':
    main()

