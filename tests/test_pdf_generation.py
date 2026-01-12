"""
Test script for PDF generation functionality

This script tests the PDF pipeline with sample data to ensure
weasyprint is properly configured and PDFs are generated correctly.
"""
from datetime import datetime
from src.reporting.table_generator import TableGenerator
from src.reporting.pdf_generator import PDFGenerator


def create_sample_tracks():
    """Create sample track data for testing"""
    return [
        {
            'position': 1,
            'track_id': 'sample_id_1',
            'track_name': 'Test Track 1',
            'artist': 'Test Artist 1',
            'album': 'Test Album 1',
            'duration': '3:45',
            'popularity': 95,
            'spotify_url': 'https://open.spotify.com/track/sample1',
            'playlist': 'Test Playlist',
            'explicit': False
        },
        {
            'position': 2,
            'track_id': 'sample_id_2',
            'track_name': 'Test Track 2',
            'artist': 'Test Artist 2',
            'album': 'Test Album 2',
            'duration': '4:12',
            'popularity': 88,
            'spotify_url': 'https://open.spotify.com/track/sample2',
            'playlist': 'Test Playlist',
            'explicit': True
        },
        {
            'position': 3,
            'track_id': 'sample_id_3',
            'track_name': 'Test Track 3',
            'artist': 'Test Artist 3',
            'album': 'Test Album 3',
            'duration': '3:20',
            'popularity': 82,
            'spotify_url': 'https://open.spotify.com/track/sample3',
            'playlist': 'Test Playlist',
            'explicit': False
        }
    ]


def test_pdf_generation():
    """Test PDF generation with sample data"""
    print("Testing PDF generation...")
    print("-" * 50)

    # Create sample data
    print("\n1. Creating sample track data...")
    tracks = create_sample_tracks()
    print(f"   ✓ Created {len(tracks)} sample tracks")

    # Test PDF generation via TableGenerator
    print("\n2. Testing TableGenerator.generate_pdf()...")
    try:
        table_generator = TableGenerator()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f'test_spotify_charts_{timestamp}.pdf'

        pdf_path = table_generator.generate_pdf(tracks, pdf_filename)
        print(f"   ✓ PDF generated successfully: {pdf_path}")
    except Exception as e:
        print(f"   ✗ Failed to generate PDF: {e}")
        return False

    # Test direct PDF generation
    print("\n3. Testing PDFGenerator directly...")
    try:
        pdf_generator = PDFGenerator()
        pdf_filename2 = f'test_direct_{timestamp}.pdf'

        pdf_path2 = pdf_generator.generate_pdf_report(tracks, pdf_filename2)
        print(f"   ✓ PDF generated successfully: {pdf_path2}")
    except Exception as e:
        print(f"   ✗ Failed to generate PDF: {e}")
        return False

    print("\n" + "=" * 50)
    print("✓ All PDF generation tests passed!")
    print("=" * 50)
    print("\nGenerated files:")
    print(f"  - {pdf_path}")
    print(f"  - {pdf_path2}")
    print("\nYou can now open these PDFs to verify formatting.")

    return True


if __name__ == '__main__':
    test_pdf_generation()
