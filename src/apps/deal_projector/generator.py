"""
Deal Projector Generator (planned)

Future Python-side logic for the Deal Projector — rate overrides, scenario
presets, CSV export server-side, etc. The calculator itself is currently
client-side JS in templates/deal_projector/projector.html.
"""
from typing import Dict, List


class DealProjectorGenerator:
    """Server-side generator for Deal Projector data and exports (planned)"""

    def generate_scenario(self, params: Dict) -> Dict:
        """
        Pre-compute a projection scenario server-side.

        Args:
            params: Dict with track/catalog parameters

        Returns:
            Dict with projected metrics
        """
        raise NotImplementedError("Server-side projection not yet implemented")

    def export_csv(self, scenario: Dict, output_path: str) -> str:
        """
        Export a projection scenario to CSV.

        Args:
            scenario: Output from generate_scenario()
            output_path: Path where CSV should be saved

        Returns:
            Path to the generated CSV file
        """
        raise NotImplementedError("CSV export not yet implemented")
