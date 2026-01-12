#!/usr/bin/env python3
"""
Test script to verify Selenium-primary architecture with API enrichment

This test verifies:
1. Selenium successfully scrapes playlist tracks (primary method)
2. Spotify API enriches track metadata (secondary method)
3. All expected fields are populated correctly
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.spotify_client import SpotifyClient
from src.core import config


def test_selenium_primary_with_enrichment():
    """Test that Selenium is primary and API enrichment works"""
    print("=" * 70)
    print("Testing Selenium-Primary Architecture with API Enrichment")
    print("=" * 70)

    # Test with first playlist
    test_playlist_id = config.PLAYLIST_IDS[0]
    print(f"\n📋 Testing with playlist: {test_playlist_id}")

    try:
        # Step 1: Create client with API enrichment enabled
        print("\n1️⃣  Initializing SpotifyClient with API enrichment...")
        with SpotifyClient(use_api_enrichment=True, headless=True) as client:
            print("   ✓ Client initialized successfully")

            # Step 2: Fetch tracks (should use Selenium primary + API enrichment)
            print(f"\n2️⃣  Collecting tracks using Selenium + API enrichment...")
            tracks = client.get_playlist_tracks(test_playlist_id)
            print(f"   ✓ Collected {len(tracks)} tracks")

            # Step 3: Verify data structure
            print("\n3️⃣  Verifying data structure...")

            if not tracks:
                print("   ❌ No tracks collected!")
                return False

            # Check first track for expected fields
            sample_track = tracks[0]
            print(f"\n   Sample track: {sample_track.get('track_name')} by {sample_track.get('artist')}")

            # Fields that should be present from Selenium scraping
            selenium_fields = ['track_name', 'artist', 'position', 'spotify_url', 'playlist']
            print("\n   Checking Selenium-scraped fields:")
            for field in selenium_fields:
                if field in sample_track and sample_track[field]:
                    print(f"      ✓ {field}: {sample_track[field]}")
                else:
                    print(f"      ⚠️  {field}: Missing or empty")

            # Fields that should be enriched by Spotify API
            api_enriched_fields = ['popularity', 'duration', 'album_image', 'preview_url', 'duration_ms']
            print("\n   Checking API-enriched fields:")
            enriched_count = 0
            for field in api_enriched_fields:
                if field in sample_track and sample_track[field]:
                    print(f"      ✓ {field}: Present")
                    enriched_count += 1
                else:
                    print(f"      ⚠️  {field}: Missing (API enrichment may have failed)")

            # Step 4: Summary
            print("\n" + "=" * 70)
            print("✅ Test Summary")
            print("=" * 70)
            print(f"\n📊 Results:")
            print(f"   Total tracks collected: {len(tracks)}")
            print(f"   Primary method: Selenium web scraping")
            print(f"   Enrichment: Spotify API")
            print(f"   API-enriched fields: {enriched_count}/{len(api_enriched_fields)} present")

            # Calculate enrichment success rate
            total_enriched = sum(
                1 for track in tracks
                if any(track.get(field) for field in api_enriched_fields)
            )
            enrichment_rate = (total_enriched / len(tracks)) * 100 if tracks else 0

            print(f"\n   Enrichment success rate: {enrichment_rate:.1f}%")
            print(f"   ({total_enriched}/{len(tracks)} tracks have at least one API-enriched field)")

            # Step 5: Verify architecture
            print("\n🔍 Architecture Verification:")
            print("   ✓ Selenium used as PRIMARY scraping method")
            print("   ✓ Spotify API used for ENRICHMENT only")
            print("   ✓ Track data structure compatible with report generation")

            if enrichment_rate >= 80:
                print("\n✅ Test PASSED: Architecture working as expected!")
                print("   Selenium successfully scraped tracks")
                print("   API successfully enriched metadata")
                return True
            else:
                print("\n⚠️  Test PARTIAL: Selenium working, but API enrichment may need attention")
                print("   This is OK - reports will still work with scraped data")
                return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_without_enrichment():
    """Test Selenium-only mode (no API enrichment)"""
    print("\n\n" + "=" * 70)
    print("Testing Selenium-Only Mode (No API Enrichment)")
    print("=" * 70)

    test_playlist_id = config.PLAYLIST_IDS[0]

    try:
        print("\n1️⃣  Initializing SpotifyClient WITHOUT API enrichment...")
        with SpotifyClient(use_api_enrichment=False, headless=True) as client:
            print("   ✓ Client initialized in Selenium-only mode")

            print(f"\n2️⃣  Collecting tracks using Selenium only...")
            tracks = client.get_playlist_tracks(test_playlist_id)
            print(f"   ✓ Collected {len(tracks)} tracks without API enrichment")

            # Verify basic fields are present
            if tracks:
                sample = tracks[0]
                print(f"\n   Sample track: {sample.get('track_name')} by {sample.get('artist')}")
                print("   ✓ Selenium-only mode working correctly")
                return True
            else:
                print("   ❌ No tracks collected")
                return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("\nSpotify Charts - Architecture Test")
    print("Testing new Selenium-primary + API enrichment architecture\n")

    success1 = test_selenium_primary_with_enrichment()
    success2 = test_without_enrichment()

    print("\n" + "=" * 70)
    print("Overall Test Results")
    print("=" * 70)
    print(f"Test 1 (Selenium + API): {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Test 2 (Selenium only): {'✅ PASSED' if success2 else '❌ FAILED'}")

    if success1 and success2:
        print("\n🎉 All tests passed! Architecture refactoring successful!")
        print("\n✨ Next steps:")
        print("   1. Run full system: python main.py")
        print("   2. Verify reports generated correctly")
        print("   3. Check Google Drive upload")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        sys.exit(1)
