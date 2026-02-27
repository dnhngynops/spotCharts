"""
Dashboard Generator — backwards-compatibility shim.

The implementation has moved to src/apps/charts/generator.py.
This module re-exports DashboardGenerator so existing imports keep working.
"""
from src.apps.charts.generator import DashboardGenerator

__all__ = ['DashboardGenerator']
