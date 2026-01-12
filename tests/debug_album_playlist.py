"""
Debug script to investigate Album playlist HTML structure
"""
import time
from selenium.webdriver.common.by import By
from src.utils.browser import ChromeDriverManager

# Album playlist (Top Albums - USA)
ALBUM_PLAYLIST_URL = "https://open.spotify.com/playlist/37i9dQZEVXbKCOlAmDpukL"

# Songs playlist (Top Songs - USA) for comparison
SONGS_PLAYLIST_URL = "https://open.spotify.com/playlist/37i9dQZEVXbLp5XoPON0wI"

def debug_playlist_structure(url, playlist_name):
    """Debug the playlist structure"""
    print(f"\n{'='*80}")
    print(f"Debugging: {playlist_name}")
    print(f"URL: {url}")
    print('='*80)

    manager = ChromeDriverManager(headless=False)  # Visible browser for debugging
    driver = manager.get_driver()

    try:
        driver.get(url)
        time.sleep(5)  # Wait for page load

        # Check for all possible scroll containers
        selectors = [
            'div[data-testid="playlist-tracklist"]',
            'div[data-testid="scroll-wrapper"]',
            'div[data-overlayscrollbars-viewport]',
            'div[role="presentation"]',
            'main',
        ]

        print("\nScroll Container Analysis:")
        print("-" * 80)

        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"\nSelector: {selector}")
            print(f"  Count: {len(elements)}")

            for i, elem in enumerate(elements):
                try:
                    scroll_height = driver.execute_script("return arguments[0].scrollHeight;", elem)
                    client_height = driver.execute_script("return arguments[0].clientHeight;", elem)
                    scroll_top = driver.execute_script("return arguments[0].scrollTop;", elem)
                    overflow_y = driver.execute_script("return window.getComputedStyle(arguments[0]).overflowY;", elem)

                    print(f"  Element {i}:")
                    print(f"    scrollHeight: {scroll_height}")
                    print(f"    clientHeight: {client_height}")
                    print(f"    scrollTop: {scroll_top}")
                    print(f"    overflowY: {overflow_y}")
                    print(f"    isScrollable: {scroll_height > client_height}")
                except Exception as e:
                    print(f"  Element {i}: Error - {e}")

        # Count visible tracks
        track_rows = driver.find_elements(By.CSS_SELECTOR, '[data-testid="tracklist-row"]')
        print(f"\nVisible track rows: {len(track_rows)}")

        # Check for virtualization indicators
        print("\nVirtualization Check:")
        virtual_indicators = [
            '[data-virtualized="true"]',
            '[data-virtual="true"]',
            '.virtual-list',
            '.ReactVirtualized__Grid',
        ]

        for selector in virtual_indicators:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"  Found: {selector} ({len(elements)} elements)")

        print("\nPress Enter to close browser...")
        input()

    finally:
        manager.close()

if __name__ == '__main__':
    # Debug both playlists to compare
    print("This script will open playlists in a visible browser to debug scroll containers.")
    print("Check the console output to see the differences between Albums and Songs playlists.")

    debug_playlist_structure(SONGS_PLAYLIST_URL, "Top Songs - USA (Working)")
    debug_playlist_structure(ALBUM_PLAYLIST_URL, "Top Albums - USA (Problematic)")

    print("\n" + "="*80)
    print("Debugging Complete")
    print("="*80)
