"""
Report generation — backwards-compatibility shim.

Implementations have moved to src/apps/charts/.
"""
from src.apps.charts.pdf import TableGenerator
from src.apps.charts.generator import DashboardGenerator

__all__ = ['TableGenerator', 'DashboardGenerator']
