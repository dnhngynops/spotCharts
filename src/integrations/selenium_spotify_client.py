"""
Selenium-based Spotify Playlist Collector

Fallback collector that uses browser automation to extract playlist metadata
and tracks directly from the Spotify web player. Designed for editorial
playlists that are not available through the public Spotify Web API.
"""
import re
import time
import logging
import base64
import os
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.common.action_chains import ActionChains
except ImportError as exc:
    raise ImportError(
        "Selenium dependencies not installed. Install with:\n"
        "    pip install selenium undetected-chromedriver\n"
    ) from exc

from src.utils.browser import ChromeDriverManager

LOGGER = logging.getLogger(__name__)


class SeleniumSpotifyClient:
    """
    Collect Spotify playlist data via Selenium automation.

    Args:
        headless: Run Chrome in headless mode (default: False)
        chrome_profile_path: Optional Chrome profile directory to reuse
            authenticated session
        wait_timeout: Seconds to wait for critical elements
        scroll_pause: Delay between lazy-load scroll operations
        max_scroll_attempts: Max scroll attempts before stopping
    """

    TRACK_ROW_SELECTOR = '[data-testid="tracklist-row"]'

    def __init__(
        self,
        headless: Optional[bool] = False,
        chrome_profile_path: Optional[str] = None,
        wait_timeout: int = 25,
        scroll_pause: float = 0.8,  # Reduced from 1.5s for faster scraping
        max_scroll_attempts: int = 80,  # Increased to allow more scrolling
        max_scroll_time: int = 600,  # Maximum time in seconds for scrolling (10 minutes)
        logger: Optional[logging.Logger] = None,
    ):
        self.headless = headless if headless is not None else False
        self.wait_timeout = wait_timeout
        self.scroll_pause = scroll_pause
        self.max_scroll_attempts = max_scroll_attempts
        self.max_scroll_time = max_scroll_time
        self.logger = logger or LOGGER
        self._manager = ChromeDriverManager(
            headless=self.headless,
            profile_path=chrome_profile_path,
            logger=self.logger,
        )
        self._driver = None

    def get_playlist_tracks(
        self, playlist_id: str, playlist_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Collect playlist tracks for the given Spotify playlist ID.

        Args:
            playlist_id: Spotify playlist ID
            playlist_name: Optional playlist name (for logging)

        Returns:
            List of track dictionaries compatible with existing table_generator
        """
        playlist_url = self._normalize_reference(playlist_id)
        driver = self._manager.get_driver()
        self._driver = driver

        self.logger.info(f"Navigating to playlist: {playlist_url}")
        driver.get(playlist_url)

        self._dismiss_cookie_banner(driver)

        # CRITICAL: Focus window immediately after page load
        # This ensures the window is active before any scrolling operations
        try:
            driver.execute_script("window.focus();")
            driver.switch_to.window(driver.current_window_handle)
            time.sleep(0.5)
            self.logger.debug("Window focused after page load")
        except Exception as e:
            self.logger.warning(f"Could not focus window after page load: {e}")

        wait = WebDriverWait(driver, self.wait_timeout)
        try:
            self.logger.info(f"Waiting for track list to load (timeout: {self.wait_timeout}s)...")
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, self.TRACK_ROW_SELECTOR)
                )
            )
            self.logger.info("Track list found, proceeding...")
        except TimeoutException as exc:
            # Try to get page source for debugging
            try:
                page_title = driver.title
                current_url = driver.current_url
                self.logger.error(f"Page title: {page_title}, URL: {current_url}")
            except:
                pass
            raise TimeoutException(
                f"Timed out after {self.wait_timeout}s waiting for playlist track list. "
                "Ensure you're logged into Spotify or playlist is public. "
                f"URL: {playlist_url}"
            ) from exc

        # Wait for page to render
        self.logger.info("Waiting for page to fully render...")
        time.sleep(3)
        self.logger.info("Page loaded, extracting tracks...")

        # Focus window
        try:
            driver.execute_script("window.focus();")
            driver.switch_to.window(driver.current_window_handle)
            time.sleep(0.5)
        except Exception as e:
            self.logger.warning(f"Could not focus window: {e}")

        # Get playlist metadata
        self.logger.info("Extracting playlist metadata...")
        metadata = self._extract_playlist_metadata(driver, playlist_id, playlist_url)
        self.logger.info(f"Playlist: {metadata.get('playlist_name', playlist_id)}, Expected tracks: {metadata.get('expected_track_count', 'unknown')}")
        
        self.logger.info("Locating scroll container...")
        scroll_container = self._locate_scroll_container(driver)
        self.logger.info("Scroll container found, starting track collection...")

        # Collect tracks
        raw_tracks = self._collect_tracks(
            driver, scroll_container, metadata.get("expected_track_count")
        )

        # Convert to format compatible with existing system
        tracks = self._convert_to_standard_format(raw_tracks, metadata)

        self.logger.info(
            f"Collected {len(tracks)} tracks from playlist '{metadata.get('playlist_name', playlist_id)}'"
        )
        return tracks

    def close(self):
        """Close the browser session"""
        self._manager.close()

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------

    @staticmethod
    def _normalize_reference(reference: str) -> str:
        """Convert playlist ID or URL to full URL"""
        if reference.startswith("http"):
            return reference.split("?")[0]
        return f"https://open.spotify.com/playlist/{reference}"

    def _dismiss_cookie_banner(self, driver):
        """Click cookie banner if present"""
        selectors = [
            'button[id="onetrust-accept-btn-handler"]',
            'button[data-testid="cookie-banner-accept-button"]',
            'button[data-testid="consent-accept-button"]',
        ]
        for selector in selectors:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                element.click()
                time.sleep(0.5)
                return
            except Exception:
                continue

    def _extract_playlist_metadata(
        self, driver, playlist_id: str, playlist_url: str
    ) -> Dict:
        """Extract playlist name, description, and other metadata"""
        name = self._first_text(
            driver,
            [
                '[data-testid="entityTitle"]',
                'h1[class*="Title"]',
                'h1[data-encore-id="type"]',
            ],
        )

        description = self._first_text(
            driver,
            [
                '[data-testid="entityDescription"]',
                '[data-testid="entityDescription"] span',
                'div[data-testid="description"]',
            ],
        )

        stats_text = self._first_text(
            driver,
            [
                '[data-testid="followers-count"]',
                '[data-testid="entityStats"]',
                'span[class*="Stat"]',
            ],
        )

        expected_track_count = None
        if stats_text:
            patterns = [r"(\d+)\s+songs", r"(\d+)\s+tracks", r"(\d+)\s+items"]
            for pattern in patterns:
                match = re.search(pattern, stats_text.lower())
                if match:
                    expected_track_count = int(match.group(1))
                    break

        # Extract playlist cover image via screenshot (more reliable than URL extraction)
        playlist_image_base64 = None
        try:
            # Wait a moment for page to fully render
            time.sleep(1)
            
            # Find the playlist cover photo container
            try:
                # Try primary selector for cover photo container
                cover_container = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="entityCoverPhoto"]'))
                )
                # Take screenshot of the cover container
                screenshot_bytes = cover_container.screenshot_as_png
                if screenshot_bytes:
                    # Convert to base64 data URI for embedding in HTML
                    playlist_image_base64 = f"data:image/png;base64,{base64.b64encode(screenshot_bytes).decode('utf-8')}"
                    self.logger.debug(f"Screenshot taken of playlist cover image ({len(screenshot_bytes)} bytes)")
            except Exception as e:
                self.logger.debug(f"Could not find cover container: {e}")
                # Fallback: try alternative selectors
                try:
                    cover_selectors = [
                        'div[data-testid="entityCoverPhoto"]',
                        'div[data-testid="cover-art"]',
                        'img[data-testid="entityCoverPhoto"]',
                    ]
                    for selector in cover_selectors:
                        try:
                            element = driver.find_element(By.CSS_SELECTOR, selector)
                            screenshot_bytes = element.screenshot_as_png
                            if screenshot_bytes:
                                playlist_image_base64 = f"data:image/png;base64,{base64.b64encode(screenshot_bytes).decode('utf-8')}"
                                self.logger.debug(f"Screenshot taken via fallback selector {selector}")
                                break
                        except Exception:
                            continue
                except Exception:
                    pass
        except Exception as e:
            self.logger.debug(f"Could not screenshot playlist image: {e}")

        return {
            "playlist_id": playlist_id,
            "playlist_name": name or playlist_id,
            "description": description,
            "spotify_url": playlist_url,
            "expected_track_count": expected_track_count,
            "playlist_image": playlist_image_base64,  # Base64 data URI from screenshot
        }

    def _locate_scroll_container(self, driver):
        """Find the scrollable container for the track list"""
        selectors = [
            'div[data-testid="playlist-tracklist"]',
            'div[data-testid="scroll-wrapper"]',
            'div[data-overlayscrollbars-viewport]',
        ]

        # First, try to find a container that is actually scrollable
        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elements:
                try:
                    # Check if this element is actually scrollable
                    scroll_height = driver.execute_script("return arguments[0].scrollHeight;", elem)
                    client_height = driver.execute_script("return arguments[0].clientHeight;", elem)

                    if scroll_height > client_height:
                        # This element is scrollable!
                        self.logger.debug(
                            f"Found scrollable container: {selector} "
                            f"(scrollHeight: {scroll_height}, clientHeight: {client_height})"
                        )
                        return elem
                except Exception as e:
                    # Element might be stale or not accessible, try next
                    continue

        # Fallback: use old behavior if no scrollable container found
        # This handles edge cases where the container becomes scrollable after initial load
        self.logger.warning("No scrollable container found, using fallback selection")
        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                return elements[-1]

        raise RuntimeError("Could not locate playlist scroll container")

    def _ensure_window_focused(self, driver, container):
        """Ensure browser window is focused for scrolling"""
        try:
            driver.execute_script("window.focus();")
            time.sleep(0.5)

            try:
                container.click()
            except Exception:
                try:
                    body = driver.find_element(By.TAG_NAME, "body")
                    body.click()
                except Exception:
                    pass

            try:
                actions = ActionChains(driver)
                actions.move_to_element(container).click().perform()
            except Exception:
                pass

            time.sleep(0.5)
        except Exception as e:
            self.logger.warning(f"Could not ensure window focus: {e}")

    def _scroll_container(self, driver, container, scroll_amount):
        """
        Scroll the container with fallback strategies

        Args:
            driver: Selenium WebDriver instance
            container: The scroll container element
            scroll_amount: Amount to scroll in pixels

        Returns:
            bool: True if scroll was successful, False otherwise
        """
        # Strategy 1: Scroll the container directly
        try:
            driver.execute_script(
                f"arguments[0].scrollTop += {scroll_amount};", container
            )
            time.sleep(0.3)

            # Verify scroll actually happened
            new_scroll = driver.execute_script("return arguments[0].scrollTop;", container)
            if new_scroll > 0:
                return True
        except Exception as e:
            self.logger.debug(f"Container scroll failed: {e}")

        # Strategy 2: Scroll using scrollBy on the container
        try:
            driver.execute_script(
                f"arguments[0].scrollBy(0, {scroll_amount});", container
            )
            time.sleep(0.3)
            return True
        except Exception as e:
            self.logger.debug(f"scrollBy on container failed: {e}")

        # Strategy 3: Scroll the window/body as last resort
        try:
            self.logger.warning("Container scroll failed, trying window scroll as fallback")
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(0.3)
            return True
        except Exception as e:
            self.logger.error(f"All scroll strategies failed: {e}")
            return False

    def _collect_tracks(
        self, driver, container, expected_count: Optional[int]
    ) -> List[Dict]:
        """Extract all tracks using progressive scroll strategy"""
        collected: List[Tuple[str, Dict]] = []
        seen_keys: set[str] = set()

        # Optimized scroll parameters for speed
        base_scroll_increment = 1200  # Base increment
        scroll_increment = [base_scroll_increment]  # Use list for mutable reference
        scroll_wait = self.scroll_pause  # Reduced wait time
        max_scroll_attempts = self.max_scroll_attempts

        # Ensure window focused
        self._ensure_window_focused(driver, container)

        # Reset to top
        driver.execute_script("arguments[0].scrollTop = 0;", container)
        time.sleep(2)

        highest_position = [0]

        def add_tracks_from_rows(rows: Sequence) -> int:
            new_count = 0
            for row in rows:
                parsed = self._parse_track_row(row)
                if not parsed:
                    continue
                key, track, position = parsed
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                collected.append((key, track))
                if position:
                    highest_position[0] = max(highest_position[0], position)
                new_count += 1
            return new_count

        consecutive_no_new_tracks = 0
        max_consecutive_no_new = 8  # Increased to allow more scrolling for virtualized content
        target_position = expected_count if expected_count else 50  # Target position to reach
        
        # Track start time for overall timeout
        import time as time_module
        scroll_start_time = time_module.time()

        for scroll_attempt in range(max_scroll_attempts):
            # Check overall timeout
            elapsed_time = time_module.time() - scroll_start_time
            if elapsed_time > self.max_scroll_time:
                self.logger.warning(
                    f"Scrolling timeout reached ({elapsed_time:.1f}s > {self.max_scroll_time}s). "
                    f"Stopping with {len(collected)} tracks collected. Highest position: {highest_position[0]}"
                )
                break
            
            # Check if we've reached the target position
            if highest_position[0] >= target_position:
                self.logger.info(
                    f"Reached target position {target_position}. Highest position: {highest_position[0]}, "
                    f"Total tracks: {len(collected)}"
                )
                # Continue for a few more scrolls to ensure we got everything
                if scroll_attempt > 5:  # Only break if we've done some scrolling
                    break
            
            time.sleep(scroll_wait)

            rows = driver.find_elements(By.CSS_SELECTOR, self.TRACK_ROW_SELECTOR)
            new_items = add_tracks_from_rows(rows)

            elapsed = time_module.time() - scroll_start_time
            self.logger.info(
                f"Scroll {scroll_attempt + 1}/{max_scroll_attempts} ({elapsed:.1f}s): "
                f"Visible: {len(rows)}, New: {new_items}, Total: {len(collected)}, "
                f"Highest position: {highest_position[0]}"
            )

            # Check if we have collected all target positions (for top 50 playlists)
            if target_position == 50:
                collected_positions = set([t[1].get('position') for t in collected if t[1].get('position')])
                if len(collected_positions) >= 50 and max(collected_positions) >= 50:
                    self.logger.info(
                        f"SUCCESS: Collected all 50 positions! Total tracks: {len(collected)}. "
                        f"Stopping early at {elapsed:.1f}s"
                    )
                    break

            if new_items == 0:
                consecutive_no_new_tracks += 1
                self.logger.debug(f"No new tracks this scroll (consecutive: {consecutive_no_new_tracks}/{max_consecutive_no_new})")
            else:
                consecutive_no_new_tracks = 0

            # Check if at bottom (improved detection for virtualized scrolling)
            # Wrap in try-except to handle stale container element
            try:
                scroll_height = driver.execute_script(
                    "return arguments[0].scrollHeight;", container
                )
                client_height = driver.execute_script(
                    "return arguments[0].clientHeight;", container
                )
                current_scroll = driver.execute_script(
                    "return arguments[0].scrollTop;", container
                )
                max_scroll = scroll_height - client_height
            except Exception as e:
                self.logger.warning(f"Container became stale, re-locating: {e}")
                new_container = self._locate_scroll_container(driver)

                # Validate the new container is actually scrollable
                try:
                    is_scrollable = driver.execute_script(
                        "return arguments[0].scrollHeight > arguments[0].clientHeight;",
                        new_container
                    )
                    if not is_scrollable:
                        self.logger.error(
                            "Re-located container is not scrollable! "
                            "This may cause under-collection. Continuing anyway..."
                        )
                except:
                    pass  # If validation fails, continue anyway

                container = new_container
                continue

            at_bottom = max_scroll > 0 and current_scroll >= max_scroll - 100

            # Stop if we've scrolled multiple times without finding new tracks AND we're at the bottom
            # AND we've reached the target position
            # This handles virtualized lists where scrollHeight keeps growing
            if consecutive_no_new_tracks >= max_consecutive_no_new and at_bottom:
                if highest_position[0] >= target_position:
                    self.logger.info(
                        f"Stopped scrolling: {consecutive_no_new_tracks} consecutive scrolls "
                        f"with no new tracks AND at bottom AND reached position {highest_position[0]}. "
                        f"Total: {len(collected)}, Scroll: {current_scroll}/{max_scroll}"
                    )
                    break
                else:
                    self.logger.info(
                        f"At bottom but only reached position {highest_position[0]}/{target_position}. "
                        f"Continuing to scroll more aggressively..."
                    )
                    # Scroll more aggressively when near bottom but haven't reached target
                    scroll_increment[0] = 2000  # Larger scroll to trigger more loading
            elif consecutive_no_new_tracks >= max_consecutive_no_new:
                self.logger.info(
                    f"Warning: {consecutive_no_new_tracks} consecutive scrolls with no new tracks, "
                    f"but not at bottom yet (scroll: {current_scroll}/{max_scroll}). "
                    f"Highest position: {highest_position[0]}/{target_position}. Continuing..."
                )
                # Reset to base increment when not at bottom
                scroll_increment[0] = base_scroll_increment

            # Ensure focused before scroll
            self._ensure_window_focused(driver, container)

            # Scroll down using robust scrolling method with fallback strategies
            try:
                scroll_success = self._scroll_container(driver, container, scroll_increment[0])

                if not scroll_success:
                    self.logger.warning("Scroll failed using all strategies, attempting container re-location")
                    new_container = self._locate_scroll_container(driver)

                    # Validate the new container is actually scrollable
                    try:
                        is_scrollable = driver.execute_script(
                            "return arguments[0].scrollHeight > arguments[0].clientHeight;",
                            new_container
                        )
                        if not is_scrollable:
                            self.logger.error(
                                "Re-located container is not scrollable! "
                                "This may cause under-collection. Continuing anyway..."
                            )
                    except:
                        pass  # If validation fails, continue anyway

                    container = new_container
                    continue

                # Check if we're at the actual bottom after scrolling (with tolerance for rounding)
                time.sleep(0.2)  # Brief wait for scroll to register
                new_scroll_height = driver.execute_script("return arguments[0].scrollHeight;", container)
                new_current_scroll = driver.execute_script("return arguments[0].scrollTop;", container)
                new_max_scroll = new_scroll_height - client_height
            except Exception as e:
                self.logger.warning(f"Container became stale during scroll, re-locating: {e}")
                new_container = self._locate_scroll_container(driver)

                # Validate the new container is actually scrollable
                try:
                    is_scrollable = driver.execute_script(
                        "return arguments[0].scrollHeight > arguments[0].clientHeight;",
                        new_container
                    )
                    if not is_scrollable:
                        self.logger.error(
                            "Re-located container is not scrollable! "
                            "This may cause under-collection. Continuing anyway..."
                        )
                except:
                    pass  # If validation fails, continue anyway

                container = new_container
                continue

            if new_max_scroll > 0 and new_current_scroll >= new_max_scroll - 50:
                # We're at or near the bottom, check if scrollHeight is still growing
                if new_scroll_height <= scroll_height:
                    self.logger.info(
                        f"Reached true bottom of container. ScrollHeight: {new_scroll_height}, "
                        f"Current scroll: {new_current_scroll}, Max scroll: {new_max_scroll}"
                    )
                    break
                # If scrollHeight increased, continue scrolling (virtualized list still loading)

        # Deduplicate by position, but also keep tracks without positions
        deduplicated: Dict[int, Dict] = {}
        tracks_without_position: List[Dict] = []
        seen_track_ids: set = set()  # Track all seen track IDs globally

        collected.sort(key=lambda item: (item[1].get("position", 9999), item[1].get("track_name", "")))

        for _, track in collected:
            track_id = track.get("track_id")
            position = track.get("position")

            if position and position > 0:
                if position not in deduplicated:
                    deduplicated[position] = track
                    if track_id:
                        seen_track_ids.add(track_id)
                else:
                    # If duplicate position, keep the one with more data (track_id, etc.)
                    existing = deduplicated[position]
                    if track.get("track_id") and not existing.get("track_id"):
                        deduplicated[position] = track
                        if track_id:
                            seen_track_ids.add(track_id)
            else:
                # Deduplicate tracks without positions by track_id
                if track_id and track_id not in seen_track_ids:
                    tracks_without_position.append(track)
                    seen_track_ids.add(track_id)
                elif not track_id:
                    # Keep tracks without IDs (rare edge case)
                    tracks_without_position.append(track)

        # Combine tracks with positions and tracks without positions
        tracks = [deduplicated[pos] for pos in sorted(deduplicated.keys())]

        # FIX (v1.2.0): Post-deduplication trimming for Top 50 playlists
        # Issue: Virtualized scrolling can load positions 50-67 simultaneously in single scroll,
        # causing over-collection before early exit check runs. This ensures exactly 50 tracks returned.
        if target_position == 50 and len(deduplicated) >= 50:
            # Check if we have all positions 1-50
            positions_collected = set(deduplicated.keys())
            if all(pos in positions_collected for pos in range(1, 51)):
                # We have all 50 positions, trim to exactly 50 tracks
                tracks = [deduplicated[pos] for pos in range(1, 51)]
                self.logger.info(
                    f"SUCCESS: Collected all 50 target positions! "
                    f"Trimmed from {len(deduplicated)} tracks with positions + {len(tracks_without_position)} without positions "
                    f"to exactly 50 tracks (positions 1-50)"
                )

                # Reassign positions sequentially (already 1-50)
                for index, track in enumerate(tracks, start=1):
                    original_position = track.get("position")
                    track["position"] = index
                    if original_position:
                        track["original_position"] = original_position

                return tracks

        # Default behavior: include all tracks
        # Add tracks without positions at the end
        tracks.extend(tracks_without_position)

        # Reassign positions sequentially based on original order
        for index, track in enumerate(tracks, start=1):
            original_position = track.get("position")
            track["position"] = index
            # Keep original position for reference
            if original_position:
                track["original_position"] = original_position

        self.logger.info(
            f"Deduplication: {len(collected)} raw -> {len(tracks)} unique tracks "
            f"({len(deduplicated)} with positions, {len(tracks_without_position)} without positions)"
        )

        return tracks

    def _parse_track_row(self, row) -> Optional[Tuple[str, Dict, Optional[int]]]:
        """Parse a single track row into a track dictionary"""
        try:
            position = self._extract_position(row)

            # Track link and URL
            track_link = None
            for link in row.find_elements(By.CSS_SELECTOR, 'a[href*="/track/"]'):
                href = link.get_attribute("href") or ""
                if "/track/" in href:
                    track_link = link
                    break

            track_url = (
                track_link.get_attribute("href").split("?")[0] if track_link else None
            )
            track_id = self._extract_track_id(track_url) if track_url else None

            # Track name
            track_name = None
            if track_link:
                track_name = track_link.text.strip()
            if not track_name:
                aria_label = row.get_attribute("aria-label") or ""
                if aria_label.startswith("Play "):
                    track_name = aria_label.replace("Play ", "").split(" by ")[0].strip()
            if not track_name:
                track_name = "Unknown Track"

            # Artist names with URLs for hyperlinking
            artist_links = row.find_elements(By.CSS_SELECTOR, 'a[href*="/artist/"]')
            artists = []
            for link in artist_links:
                name = link.text.strip()
                if name:
                    href = link.get_attribute("href") or ""
                    artist_url = href.split("?")[0] if href else None
                    artist_id = href.split("/artist/")[-1] if "/artist/" in href else None
                    artists.append({
                        "name": name,
                        "url": artist_url,
                        "id": artist_id
                    })
            if not artists:
                artists = [{"name": "Unknown Artist", "url": None, "id": None}]

            # For backwards compatibility, also store as comma-separated string
            artist_names = [a["name"] for a in artists]

            # Album name and URL
            album_element = self._first_element(
                row,
                [
                    'a[href*="/album/"]',
                    '[data-testid="tracklist-row-album-name"]',
                ],
            )
            album_name = album_element.text.strip() if album_element else None
            
            # Extract album URL if album element is a link
            album_url = None
            if album_element:
                try:
                    href = album_element.get_attribute("href")
                    if href and "/album/" in href:
                        album_url = href.split("?")[0]  # Remove query parameters
                except Exception:
                    pass

            # Explicit flag
            explicit = bool(row.find_elements(By.CSS_SELECTOR, 'span[aria-label="Explicit"]'))

            track = {
                "position": position or 0,
                "track_id": track_id or "",
                "track_name": track_name,
                "artist": ", ".join(artist_names),  # String for backwards compatibility
                "artists": artists,  # List with URLs for hyperlinking
                "album": album_name,
                "album_url": album_url,  # Album URL for hyperlinking
                "duration_ms": None,  # Not available via scraping
                "duration": None,
                "popularity": None,  # Not available via scraping
                "spotify_url": track_url,
                "explicit": explicit,
            }

            key_parts = [
                f"{position:04d}" if position else "",
                track_id or "",
                track_name,
            ]
            key = "|".join(part for part in key_parts if part)

            return key or track_name, track, position

        except Exception as e:
            # Stale element or any other error during parsing, skip this row
            return None

    def _extract_position(self, row) -> Optional[int]:
        """Extract track position from row"""
        try:
            attr = row.get_attribute("aria-rowindex")
            if attr and attr.isdigit():
                return int(attr)
        except Exception:
            # Element became stale, return None
            return None

        selectors = [
            '[data-testid="tracklist-row-index"]',
            'span[data-testid="index"]',
            'span',
        ]
        for selector in selectors:
            try:
                elems = row.find_elements(By.CSS_SELECTOR, selector)
                for elem in elems:
                    try:
                        text = elem.text.strip()
                        if text.isdigit():
                            return int(text)
                    except Exception:
                        # Element became stale, continue
                        continue
            except Exception:
                continue
        return None

    @staticmethod
    def _extract_track_id(track_url: str) -> Optional[str]:
        """Extract track ID from Spotify URL"""
        if "/track/" not in track_url:
            return None
        return track_url.split("/track/")[-1]

    def _convert_to_standard_format(
        self, raw_tracks: List[Dict], metadata: Dict
    ) -> List[Dict]:
        """Convert scraped tracks to standard format matching API client"""
        playlist_name = metadata.get("playlist_name", "Unknown Playlist")
        playlist_image = metadata.get("playlist_image")

        for track in raw_tracks:
            # Add playlist name
            track["playlist"] = playlist_name
            
            # Add playlist image to all tracks
            if playlist_image:
                track["playlist_image"] = playlist_image

            # Format duration if needed (not available from scraping)
            if not track.get("duration"):
                track["duration"] = "N/A"

            # Add missing fields expected by table generator
            if "release_date" not in track:
                track["release_date"] = None
            if "album_image" not in track:
                track["album_image"] = None

        return raw_tracks

    def _first_text(
        self,
        context,
        selectors: Sequence[str],
        *,
        text_contains: Optional[str] = None,
    ) -> Optional[str]:
        """Find first element matching selectors and return its text"""
        element = self._first_element(context, selectors, text_contains=text_contains)
        if element:
            return element.text.strip()
        return None

    def _first_element(
        self,
        context,
        selectors: Sequence[str],
        *,
        text_contains: Optional[str] = None,
    ):
        """Find first element matching any of the given selectors"""
        for selector in selectors:
            try:
                element = context.find_element(By.CSS_SELECTOR, selector)
            except Exception:
                continue
            if element is None:
                continue
            if text_contains and text_contains not in (element.text or ""):
                continue
            return element
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
