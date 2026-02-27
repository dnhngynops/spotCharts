"""
PDF Generator — backwards-compatibility shim.

The implementation has moved to src/apps/charts/pdf.py.
This module re-exports PDFGenerator so existing imports keep working.
"""
from src.apps.charts.pdf import PDFGenerator

__all__ = ['PDFGenerator']
