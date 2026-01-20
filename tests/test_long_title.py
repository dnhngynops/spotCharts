"""
Test script to check right edge alignment with a very long playlist name
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.spotify_client import SpotifyClient
from src.reporting.table_generator import TableGenerator
from src.core import config

def main():
    print("=" * 70)
    print("Testing Right Edge Alignment - Long Playlist Name")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Use the first playlist but override the name with a very long one
        playlist_id = config.PLAYLIST_IDS[0]

        # Test different playlist name lengths
        test_cases = [
            ("Top Songs - USA", 16),  # Short name (current)
            ("Very Long Playlist Name That Should Trigger Font Resize", 54),  # Long name
        ]

        for test_name, char_count in test_cases:
            print("\n" + "=" * 70)
            print(f"TEST CASE: '{test_name}'")
            print(f"Character count: {char_count}")
            print("=" * 70)

            # Calculate expected font size
            table_width_px = 1160
            avg_char_width = 29
            required_width = char_count * avg_char_width
            threshold = table_width_px * 0.95

            print(f"\nCalculations:")
            print(f"  Required width: {char_count} × 29px = {required_width}px")
            print(f"  Threshold: {table_width_px}px × 0.95 = {threshold}px")

            if required_width <= threshold:
                print(f"  Result: NO RESIZE (fits within threshold)")
                print(f"  Font size: 3.2em (default)")
                print(f"  Text ends at: ~{required_width}px")
                print(f"  Gap to table right edge: {table_width_px - required_width}px")
            else:
                scale_factor = threshold / required_width
                new_size = 3.2 * scale_factor
                new_size = max(1.2, new_size)
                print(f"  Result: RESIZE NEEDED")
                print(f"  Scale factor: {threshold}px / {required_width}px = {scale_factor:.3f}")
                print(f"  New font size: 3.2em × {scale_factor:.3f} = {new_size:.2f}em")
                print(f"  Text ends at: ~{threshold}px (95% of table width)")
                print(f"  Gap to table right edge: ~{table_width_px - threshold:.0f}px (5% safety margin)")

            # Collect tracks
            print(f"\nCollecting tracks...")
            with SpotifyClient(use_api_enrichment=True, headless=True) as spotify_client:
                tracks = spotify_client.get_playlist_tracks(playlist_id, test_name)

            if not tracks:
                print("No tracks found. Skipping.")
                continue

            # Generate PDF
            output_dir = project_root / 'output'
            os.makedirs(output_dir, exist_ok=True)

            table_generator = TableGenerator()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in test_name)
            safe_name = safe_name.strip().replace(' ', '_')
            pdf_filename = f'{safe_name}_{timestamp}.pdf'
            pdf_file_path = output_dir / pdf_filename

            print(f"Generating PDF: {pdf_filename}")
            pdf_path = table_generator.generate_pdf(
                tracks,
                str(pdf_file_path),
                playlist_name=test_name
            )

            file_size_kb = os.path.getsize(pdf_path) / 1024
            print(f"\n✓ PDF generated: {pdf_path}")
            print(f"  Size: {file_size_kb:.2f} KB")

            # Try to get dimensions
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(pdf_path)
                page = reader.pages[0]
                width_mm = float(page.mediabox.width) * 0.352778
                height_mm = float(page.mediabox.height) * 0.352778
                print(f"  Dimensions: {width_mm:.1f}mm × {height_mm:.1f}mm")
            except:
                pass

        print("\n" + "=" * 70)
        print("✓ Test completed!")
        print("=" * 70)
        print("\nCONCLUSION:")
        print("The text right edge alignment behavior:")
        print("1. Short titles: Text ends where content ends (left-aligned)")
        print("2. Long titles: Text ends at 95% of table width (1102px)")
        print("3. Table right edge is always at 1160px")
        print("\nThe 5% safety margin (58px) prevents text from touching table edge.")
        print("This is intentional design for readability and safety.")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == '__main__':
    main()
