"""
Script to generate PDF reports for all 4 playlists with consistent title sizing
"""
import os
from datetime import datetime
from src.integrations.spotify_client import SpotifyClient
from src.reporting.table_generator import TableGenerator
from src.core import config


def main():
    """Generate PDFs for all playlists"""
    print("=" * 80)
    print("Generating PDF Reports for All Playlists")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Step 1: Collect tracks from all playlists
        print("STEP 1: Collecting tracks from Spotify playlists...")
        print("Using Selenium scraping (primary) + Spotify API enrichment\n")

        with SpotifyClient(use_api_enrichment=True, headless=True) as spotify_client:
            tracks = spotify_client.get_all_playlist_tracks(config.PLAYLIST_IDS)
            print(f"✓ Collected {len(tracks)} tracks across {len(config.PLAYLIST_IDS)} playlists\n")

        if not tracks:
            print("✗ No tracks found. Exiting.")
            return

        # Step 2: Generate PDFs
        print("=" * 80)
        print("STEP 2: Generating PDF reports (one per playlist)...")
        print("=" * 80)

        # Group tracks by playlist
        from collections import defaultdict
        tracks_by_playlist = defaultdict(list)
        for track in tracks:
            playlist_name = track.get('playlist', 'Unknown Playlist')
            tracks_by_playlist[playlist_name].append(track)

        print(f"\nGrouped tracks into {len(tracks_by_playlist)} playlists\n")

        # Create output directory
        output_dir = config.REPORT_CONFIG['output_dir']
        os.makedirs(output_dir, exist_ok=True)

        # Generate PDF for each playlist
        table_generator = TableGenerator()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        generated_pdfs = []

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
            generated_pdfs.append(pdf_file_path)
            
            file_size_kb = os.path.getsize(pdf_file_path) / 1024
            print(f"✓ PDF for '{playlist_name}': {pdf_file_path}")
            print(f"  - Tracks: {len(playlist_tracks)}")
            print(f"  - Size: {file_size_kb:.1f} KB")
            print(f"  - Format: Single continuous page")
            print()

        print("=" * 80)
        print("✓ All PDFs generated successfully!")
        print("=" * 80)
        print(f"\nGenerated {len(generated_pdfs)} PDF files:")
        for pdf_path in generated_pdfs:
            print(f"  - {pdf_path}")

    except Exception as e:
        print(f"\n✗ Error during PDF generation: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()
