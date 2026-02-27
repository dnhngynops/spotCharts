"""
Entity Classifier — Distinguish People from Organizations
=========================================================
Determines whether a Genius credit entry represents a person or an organization
using a hybrid approach: role-based detection first, then name pattern analysis.

Ported from: backend copy/shared/credit_processing/entity_classifier.py

Usage:
    from src.utils.entity_classifier import EntityClassifier, classify_entity

    classifier = EntityClassifier()
    result = classifier.classify("RCA Records", "Label")
    # EntityClassification(entity_type='company', confidence=1.0, method='role_based', ...)

    result = classifier.classify("Max Martin", "Producer")
    # EntityClassification(entity_type='credit', confidence=1.0, method='role_based', ...)
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class EntityClassification:
    """Result of entity classification."""
    entity_type: str   # 'credit' (person) or 'company' (organization)
    confidence: float  # 0.0–1.0
    method: str        # 'role_based' | 'name_pattern' | 'hybrid' | 'default'
    reasoning: str     # human-readable explanation


class EntityClassifier:
    """
    Classify Genius credit entries as people ('credit') or organizations ('company').

    Strategy (applied in order):
      1. Role-Based Detection  — certain roles definitively indicate entity type.
      2. Name Pattern Detection — analyze name for company/person cues (fallback).
      3. Hybrid                — combine both signals when confidence is moderate.
      4. Default               — fall back to 'credit' (person) with low confidence.
    """

    # Roles that ALWAYS indicate a company/organization
    COMPANY_ROLES = {
        'label',
        'publisher',
        'distributor',
        'copyright ©',
        'phonographic copyright ℗',
        'record label',
        'publishing company',
        'management company',
        'booking agency',
    }

    # Roles that ALWAYS indicate a person
    PERSON_ROLES = {
        'writer', 'songwriter', 'producer', 'co-producer', 'executive producer',
        'artist', 'primary artist', 'featuring', 'vocals', 'background vocals',
        'engineer', 'mixing engineer', 'mastering engineer', 'recording engineer',
        'assistant engineer', 'mixing assistant', 'mastering assistant',
        'instrumentalist', 'piano', 'guitar', 'bass', 'drums', 'synthesizer',
        'strings', 'arranger', 'programmer', 'synthesizer programmer',
        'vocal producer', 'additional production', 'additional vocals',
        'choir', 'orchestra', 'composer', 'lyricist',
    }

    # Keywords that suggest an organization name
    COMPANY_INDICATORS = [
        'records', 'music', 'entertainment', 'publishing', 'productions',
        'studio', 'studios', 'label', 'group', 'corporation', 'corp', 'inc',
        'llc', 'ltd', 'limited', 'company', 'co.', 'enterprises', 'industries',
        'media', 'bmg', 'emi', 'universal', 'sony', 'warner', 'atlantic',
        'columbia', 'def jam', 'interscope', 'capitol', 'rca', 'epic', 'republic',
    ]

    # Regex patterns that suggest an individual's name
    PERSON_NAME_PATTERNS = [
        r'^[A-Z][a-z]+ [A-Z][a-z]+$',   # FirstName LastName  (e.g., "Max Martin")
        r'^[A-Z]\. [A-Z][a-z]+$',        # Initial LastName    (e.g., "J. Cole")
        r'^\w+ (?:Jr\.|Sr\.|III|IV)$',   # Name with suffix
    ]

    def __init__(self) -> None:
        self._company_roles_lc = {r.lower() for r in self.COMPANY_ROLES}
        self._person_roles_lc  = {r.lower() for r in self.PERSON_ROLES}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self, name: str, role: str) -> EntityClassification:
        """
        Classify a Genius credit entry as a person or organization.

        Args:
            name: Credit name from Genius  (e.g., "RCA Records", "Max Martin")
            role: Role string from Genius  (e.g., "Label", "Producer")

        Returns:
            EntityClassification with type, confidence, method, and reasoning.
        """
        # 1. Role-based (definitive)
        role_result = self._classify_by_role(role)
        if role_result is not None:
            return role_result

        # 2. Name-pattern (fallback)
        name_result = self._classify_by_name(name)
        if name_result.confidence >= 0.8:
            return name_result

        # 3. Hybrid — moderate confidence from name
        if name_result.confidence >= 0.5:
            return EntityClassification(
                entity_type=name_result.entity_type,
                confidence=round(name_result.confidence * 0.9, 3),
                method='hybrid',
                reasoning=(
                    f"Name pattern suggests {name_result.entity_type}, "
                    f"role '{role}' is ambiguous"
                ),
            )

        # 4. Default to person
        return EntityClassification(
            entity_type='credit',
            confidence=0.4,
            method='default',
            reasoning="Unable to confidently classify — defaulting to credit (person)",
        )

    def classify_batch(
        self,
        entities: List[Tuple[str, str]],
    ) -> List[EntityClassification]:
        """Classify a list of (name, role) tuples."""
        return [self.classify(name, role) for name, role in entities]

    def get_statistics(
        self,
        classifications: List[EntityClassification],
    ) -> Dict:
        """Summarize a batch of classification results."""
        total = len(classifications)
        if not total:
            return {}

        credits_   = sum(1 for c in classifications if c.entity_type == 'credit')
        companies_ = sum(1 for c in classifications if c.entity_type == 'company')
        high       = sum(1 for c in classifications if c.confidence >= 0.9)
        medium     = sum(1 for c in classifications if 0.7 <= c.confidence < 0.9)
        low        = sum(1 for c in classifications if c.confidence < 0.7)

        methods: Dict[str, int] = {}
        for c in classifications:
            methods[c.method] = methods.get(c.method, 0) + 1

        return {
            'total':              total,
            'credits':            credits_,
            'companies':          companies_,
            'credit_percentage':  round(credits_   / total * 100, 1),
            'company_percentage': round(companies_  / total * 100, 1),
            'confidence': {
                'high':             high,
                'medium':           medium,
                'low':              low,
                'high_percentage':  round(high / total * 100, 1),
            },
            'methods': methods,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _classify_by_role(self, role: str) -> Optional[EntityClassification]:
        """Return definitive classification if role is known, else None."""
        role_lc = role.lower().strip()

        if role_lc in self._company_roles_lc:
            return EntityClassification(
                entity_type='company',
                confidence=1.0,
                method='role_based',
                reasoning=f"Role '{role}' always indicates company",
            )

        if role_lc in self._person_roles_lc:
            return EntityClassification(
                entity_type='credit',
                confidence=1.0,
                method='role_based',
                reasoning=f"Role '{role}' always indicates person",
            )

        return None

    def _classify_by_name(self, name: str) -> EntityClassification:
        """Return best-guess classification from name patterns."""
        name_lc = name.lower()

        matched: List[str] = [i for i in self.COMPANY_INDICATORS if i in name_lc]

        if len(matched) >= 2:
            return EntityClassification(
                entity_type='company',
                confidence=0.95,
                method='name_pattern',
                reasoning=f"Name contains company indicators: {', '.join(matched)}",
            )
        if len(matched) == 1:
            return EntityClassification(
                entity_type='company',
                confidence=0.85,
                method='name_pattern',
                reasoning=f"Name contains company indicator: '{matched[0]}'",
            )

        # Person-name regex patterns
        for pattern in self.PERSON_NAME_PATTERNS:
            if re.match(pattern, name):
                return EntityClassification(
                    entity_type='credit',
                    confidence=0.85,
                    method='name_pattern',
                    reasoning="Name matches person name pattern",
                )

        words = name.split()

        if len(words) == 1:
            return EntityClassification(
                entity_type='credit',
                confidence=0.7,
                method='name_pattern',
                reasoning="Single-word name suggests stage name (person)",
            )
        if len(words) == 2:
            return EntityClassification(
                entity_type='credit',
                confidence=0.75,
                method='name_pattern',
                reasoning="Two-word name without company indicators suggests person",
            )

        return EntityClassification(
            entity_type='credit',
            confidence=0.6,
            method='name_pattern',
            reasoning="Multi-word name without clear company indicators — likely person",
        )


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def classify_entity(name: str, role: str) -> EntityClassification:
    """Quick single-entity classification helper (creates a new EntityClassifier)."""
    return EntityClassifier().classify(name, role)
