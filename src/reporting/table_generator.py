"""
Table Generator — backwards-compatibility shim.

The implementation has moved to src/apps/charts/pdf.py.
This module re-exports TableGenerator so existing imports keep working.
"""
from src.apps.charts.pdf import TableGenerator

__all__ = ['TableGenerator']
