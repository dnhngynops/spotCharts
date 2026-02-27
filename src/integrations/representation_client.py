"""
Representation Client
=====================
CRUD operations for the company / representation layer (A&R CRM).

Tables managed (defined in sql/schema.sql v2.0, seeded via
sql/seed_representation_types.sql):
  - companies             — labels, publishers, management firms, etc.
  - representations       — credit ↔ company relationship links
  - company_staff         — individuals employed by companies

This client is the Python gateway to the representation system.  It will be
used by Phase 4 discovery (future: representation discovery via Google search)
and any enrichment scripts that need to persist company / representation data.

Prerequisites (one-time setup in Supabase):
  1. Apply  sql/schema.sql                     (creates the tables)
  2. Run    sql/seed_representation_types.sql  (seeds representation_types + views)

Usage:
    from src.integrations.representation_client import RepresentationClient

    if RepresentationClient.is_configured():
        client = RepresentationClient()
        company_id, created = client.get_or_create_company("Sony Music", "publisher")
        rep_id = client.create_representation(credit_id, company_id, "publisher")

Ported from: backend copy/phases/phase4/adapters/representation_adapter.py
Key differences from the backend copy's adapter:
  - Uses src.core.config for Supabase credentials (no separate database.connection)
  - Loads representation_type IDs dynamically at init time (no hardcoded ID map)
  - create_company_staff() requires job_title (schema column is NOT NULL)
  - Name normalization delegates to src.utils.name_normalizer.normalize_credit_name
"""

import logging
from typing import Dict, List, Optional, Tuple

from src.core import config
from src.utils.name_normalizer import normalize_credit_name

logger = logging.getLogger(__name__)


# Short key aliases exposed to callers.  Values are the type_name strings
# seeded in the representation_types table by seed_representation_types.sql.
_TYPE_KEY_TO_NAME: Dict[str, str] = {
    'label':        'Record Label',
    'publisher':    'Music Publisher',
    'management':   'Management',
    'booking':      'Booking Agent',
    'legal':        'Legal Representation',
    'business':     'Business Manager',
    'ar':           'A&R',
    'distribution': 'Distribution',
    'sync':         'Sync Licensing',
    'brand':        'Brand Partnerships',
}

VALID_TYPE_KEYS = list(_TYPE_KEY_TO_NAME.keys())


class RepresentationClient:
    """
    CRUD client for the company / representation layer.

    Type keys accepted by create_representation():
        'label', 'publisher', 'management', 'booking', 'legal',
        'business', 'ar', 'distribution', 'sync', 'brand'

    Type IDs are resolved by querying representation_types at init time,
    so they are always correct regardless of row-insertion order.
    """

    @classmethod
    def is_configured(cls) -> bool:
        """Return True when Supabase credentials are present in config."""
        return bool(config.SUPABASE_URL and config.SUPABASE_SERVICE_KEY)

    def __init__(self) -> None:
        if not self.is_configured():
            raise RuntimeError(
                "RepresentationClient: Supabase is not configured. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_KEY in your .env file."
            )
        from supabase import create_client
        self._client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
        self._type_map: Dict[str, int] = self._load_type_map()

    # -------------------------------------------------------------------------
    # Init helpers
    # -------------------------------------------------------------------------

    def _load_type_map(self) -> Dict[str, int]:
        """
        Build {type_key: type_id} by querying the representation_types table.

        Matches rows by type_name (not position/ID), so this is always correct
        even if the seed rows were inserted in a different order.

        Emits a warning for any key whose type_name is not found in the table
        (i.e., seed_representation_types.sql has not been run yet).
        """
        try:
            result = (
                self._client.table('representation_types')
                .select('type_id, type_name')
                .execute()
            )
            name_to_id: Dict[str, int] = {
                r['type_name']: r['type_id'] for r in (result.data or [])
            }
            type_map: Dict[str, int] = {}
            for key, type_name in _TYPE_KEY_TO_NAME.items():
                if type_name in name_to_id:
                    type_map[key] = name_to_id[type_name]
                else:
                    logger.warning(
                        "RepresentationClient: type_name '%s' not found in "
                        "representation_types — run sql/seed_representation_types.sql",
                        type_name,
                    )
            logger.debug("RepresentationClient: loaded %d type mappings", len(type_map))
            return type_map
        except Exception as e:
            logger.error("RepresentationClient: failed to load type map: %s", e)
            return {}

    # -------------------------------------------------------------------------
    # Company operations
    # -------------------------------------------------------------------------

    def get_or_create_company(
        self,
        name: str,
        company_type: str,
    ) -> Tuple[int, bool]:
        """
        Return (company_id, created) for a company.

        Looks up by normalized_name.  If the company already exists, adds
        company_type to its company_types array when not already present.
        If it does not exist, inserts a new row.

        Args:
            name:         Display name  (e.g., "Sony Music Publishing")
            company_type: Type value from the companies.company_types CHECK
                          constraint: 'label', 'publisher', 'management',
                          'booking', 'legal', 'distribution', 'production', 'other'

        Returns:
            (company_id, True)  if newly created
            (company_id, False) if already existed
        """
        normalized = normalize_credit_name(name)
        try:
            result = (
                self._client.table('companies')
                .select('company_id, company_types')
                .eq('normalized_name', normalized)
                .limit(1)
                .execute()
            )
            if result.data:
                company = result.data[0]
                company_id = company['company_id']
                existing_types = company.get('company_types') or []
                if company_type not in existing_types:
                    self._update_company_types(company_id, existing_types, [company_type])
                logger.debug(
                    "RepresentationClient: existing company '%s' (id=%s)", name, company_id
                )
                return (company_id, False)

            # Insert new company
            insert_result = (
                self._client.table('companies')
                .insert({
                    'name': name,
                    'normalized_name': normalized,
                    'company_types': [company_type],
                })
                .execute()
            )
            if not insert_result.data:
                raise RuntimeError(f"Insert returned no data for company '{name}'")
            company_id = insert_result.data[0]['company_id']
            logger.info(
                "RepresentationClient: created company '%s' (id=%s)", name, company_id
            )
            return (company_id, True)

        except Exception as e:
            logger.error(
                "RepresentationClient: get_or_create_company '%s': %s", name, e
            )
            raise

    def get_company_by_name(self, name: str) -> Optional[Dict]:
        """Return the company row for name (normalized lookup), or None."""
        normalized = normalize_credit_name(name)
        try:
            result = (
                self._client.table('companies')
                .select('*')
                .eq('normalized_name', normalized)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(
                "RepresentationClient: get_company_by_name '%s': %s", name, e
            )
            return None

    def get_company_by_id(self, company_id: int) -> Optional[Dict]:
        """Return the company row for company_id, or None."""
        try:
            result = (
                self._client.table('companies')
                .select('*')
                .eq('company_id', company_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(
                "RepresentationClient: get_company_by_id %s: %s", company_id, e
            )
            return None

    # -------------------------------------------------------------------------
    # Representation operations
    # -------------------------------------------------------------------------

    def create_representation(
        self,
        credit_id: int,
        company_id: int,
        representation_type: str,
        representative_credit_id: Optional[int] = None,
        is_active: bool = True,
        verified: bool = False,
    ) -> Optional[int]:
        """
        Create (or return an existing) representation link between credit and company.

        Args:
            credit_id:                 Credit ID of the represented artist/person.
            company_id:                Company ID (label, publisher, etc.).
            representation_type:       Type key — one of VALID_TYPE_KEYS.
            representative_credit_id:  Optional credit_id of the specific individual
                                       at the company handling this relationship.
            is_active:                 Whether this representation is currently active.
            verified:                  Whether the relationship has been manually verified.

        Returns:
            representation_id on success; None on error.
        """
        type_id = self._type_map.get(representation_type)
        if not type_id:
            logger.error(
                "RepresentationClient: unknown representation_type '%s'. "
                "Valid keys: %s",
                representation_type, VALID_TYPE_KEYS,
            )
            return None

        try:
            # Return existing if already present
            existing = (
                self._client.table('representations')
                .select('representation_id')
                .eq('credit_id', credit_id)
                .eq('company_id', company_id)
                .eq('representation_type_id', type_id)
                .limit(1)
                .execute()
            )
            if existing.data:
                rep_id = existing.data[0]['representation_id']
                logger.debug(
                    "RepresentationClient: existing representation "
                    "credit=%s→company=%s (%s) id=%s",
                    credit_id, company_id, representation_type, rep_id,
                )
                return rep_id

            # Insert new
            row: Dict = {
                'credit_id':               credit_id,
                'company_id':              company_id,
                'representation_type_id':  type_id,
                'is_active':               is_active,
                'verified':                verified,
            }
            if representative_credit_id is not None:
                row['representative_credit_id'] = representative_credit_id

            result = self._client.table('representations').insert(row).execute()
            if not result.data:
                logger.warning(
                    "RepresentationClient: insert returned no data "
                    "for credit=%s→company=%s",
                    credit_id, company_id,
                )
                return None

            rep_id = result.data[0]['representation_id']
            logger.info(
                "RepresentationClient: created representation "
                "credit=%s→company=%s (%s) id=%s",
                credit_id, company_id, representation_type, rep_id,
            )
            return rep_id

        except Exception as e:
            logger.error(
                "RepresentationClient: create_representation "
                "credit=%s company=%s: %s",
                credit_id, company_id, e,
            )
            return None

    def get_representations_for_credit(
        self,
        credit_id: int,
        representation_type: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Dict]:
        """
        Return representation rows for a credit, joined with company data.

        Args:
            credit_id:            Credit ID to query.
            representation_type:  Optional type key filter.
            active_only:          If True, only return is_active = true rows.
        """
        try:
            query = (
                self._client.table('representations')
                .select('*, companies(*)')
                .eq('credit_id', credit_id)
            )
            if representation_type:
                type_id = self._type_map.get(representation_type)
                if type_id:
                    query = query.eq('representation_type_id', type_id)
            if active_only:
                query = query.eq('is_active', True)
            return query.execute().data or []
        except Exception as e:
            logger.error(
                "RepresentationClient: get_representations_for_credit %s: %s",
                credit_id, e,
            )
            return []

    def get_credits_for_company(
        self,
        company_id: int,
        representation_type: Optional[str] = None,
    ) -> List[Dict]:
        """
        Return active representation rows for a company, joined with credit data.

        Args:
            company_id:           Company ID to query.
            representation_type:  Optional type key filter.
        """
        try:
            query = (
                self._client.table('representations')
                .select('*, credits(*)')
                .eq('company_id', company_id)
                .eq('is_active', True)
            )
            if representation_type:
                type_id = self._type_map.get(representation_type)
                if type_id:
                    query = query.eq('representation_type_id', type_id)
            return query.execute().data or []
        except Exception as e:
            logger.error(
                "RepresentationClient: get_credits_for_company %s: %s", company_id, e
            )
            return []

    def update_representation_verified(
        self,
        credit_id: int,
        company_id: int,
        verified: bool = True,
    ) -> bool:
        """
        Set the verified flag on all matching representation rows.

        Returns True if at least one row was updated.
        """
        try:
            result = (
                self._client.table('representations')
                .update({'verified': verified})
                .eq('credit_id', credit_id)
                .eq('company_id', company_id)
                .execute()
            )
            return bool(result.data)
        except Exception as e:
            logger.error(
                "RepresentationClient: update_representation_verified "
                "credit=%s company=%s: %s",
                credit_id, company_id, e,
            )
            return False

    # -------------------------------------------------------------------------
    # Company staff operations
    # -------------------------------------------------------------------------

    def create_company_staff(
        self,
        credit_id: int,
        company_id: int,
        job_title: str,
        department: Optional[str] = None,
        is_current: bool = True,
    ) -> Optional[int]:
        """
        Link an individual credit to a company as a staff member.

        Avoids creating duplicate current-employment rows: if a row already
        exists for (credit_id, company_id) with is_current=True, returns its
        existing staff_id.

        Args:
            credit_id:   Individual's credit_id.
            company_id:  Company's company_id.
            job_title:   Job title (required by schema, e.g., "Director of A&R").
            department:  Optional department name.
            is_current:  True if this is an active employment.

        Returns:
            staff_id on success; None on error.
        """
        try:
            existing = (
                self._client.table('company_staff')
                .select('staff_id')
                .eq('credit_id', credit_id)
                .eq('company_id', company_id)
                .eq('is_current', True)
                .limit(1)
                .execute()
            )
            if existing.data:
                staff_id = existing.data[0]['staff_id']
                logger.debug(
                    "RepresentationClient: existing company_staff "
                    "credit=%s company=%s id=%s",
                    credit_id, company_id, staff_id,
                )
                return staff_id

            row: Dict = {
                'credit_id':  credit_id,
                'company_id': company_id,
                'job_title':  job_title,
                'is_current': is_current,
            }
            if department:
                row['department'] = department

            result = self._client.table('company_staff').insert(row).execute()
            if not result.data:
                logger.warning(
                    "RepresentationClient: company_staff insert returned no data"
                )
                return None

            staff_id = result.data[0]['staff_id']
            logger.info(
                "RepresentationClient: created company_staff "
                "credit=%s company=%s id=%s",
                credit_id, company_id, staff_id,
            )
            return staff_id

        except Exception as e:
            logger.error(
                "RepresentationClient: create_company_staff "
                "credit=%s company=%s: %s",
                credit_id, company_id, e,
            )
            return None

    def get_company_staff(
        self,
        company_id: int,
        current_only: bool = True,
    ) -> List[Dict]:
        """Return staff rows for a company, joined with credit data."""
        try:
            query = (
                self._client.table('company_staff')
                .select('*, credits(*)')
                .eq('company_id', company_id)
            )
            if current_only:
                query = query.eq('is_current', True)
            return query.execute().data or []
        except Exception as e:
            logger.error(
                "RepresentationClient: get_company_staff %s: %s", company_id, e
            )
            return []

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_statistics(self) -> Dict:
        """Return system-wide representation statistics."""
        try:
            stats: Dict = {
                'total_companies':          0,
                'total_representations':    0,
                'active_representations':   0,
                'verified_representations': 0,
                'companies_by_type':        {},
                'representations_by_type':  {},
            }

            companies = self._client.table('companies').select('*').execute().data or []
            stats['total_companies'] = len(companies)
            for co in companies:
                for t in (co.get('company_types') or []):
                    stats['companies_by_type'][t] = (
                        stats['companies_by_type'].get(t, 0) + 1
                    )

            all_reps    = self._client.table('representations').select('*').execute().data or []
            active_reps = [r for r in all_reps if r.get('is_active')]

            stats['total_representations']    = len(all_reps)
            stats['active_representations']   = len(active_reps)
            stats['verified_representations'] = sum(1 for r in all_reps if r.get('verified'))

            # Invert type_map for ID→key lookup
            id_to_key = {v: k for k, v in self._type_map.items()}
            for rep in active_reps:
                type_key = id_to_key.get(rep.get('representation_type_id'), 'unknown')
                stats['representations_by_type'][type_key] = (
                    stats['representations_by_type'].get(type_key, 0) + 1
                )

            return stats

        except Exception as e:
            logger.error("RepresentationClient: get_statistics: %s", e)
            return {}

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _update_company_types(
        self,
        company_id: int,
        existing_types: List[str],
        new_types: List[str],
    ) -> None:
        """Merge new_types into the company's company_types array (no-op if unchanged)."""
        merged = list(set(existing_types + new_types))
        if sorted(merged) == sorted(existing_types):
            return
        try:
            self._client.table('companies').update(
                {'company_types': merged}
            ).eq('company_id', company_id).execute()
            logger.debug(
                "RepresentationClient: updated company %s types: %s → %s",
                company_id, existing_types, merged,
            )
        except Exception as e:
            logger.error(
                "RepresentationClient: _update_company_types company=%s: %s",
                company_id, e,
            )
