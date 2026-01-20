"""
Pytest configuration for Spotify Charts tests.

This file ensures the project root is in the Python path so that
`from src.` imports work correctly when running tests.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
