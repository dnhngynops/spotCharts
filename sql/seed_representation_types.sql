-- =============================================================================
-- Seed: Representation Types + Supplemental Views / Triggers
-- =============================================================================
--
-- Run this ONCE in your Supabase SQL Editor after applying sql/schema.sql.
-- All operations are idempotent — safe to re-run.
--
-- What this adds on top of schema.sql v2.0:
--   1. Seed data for representation_types         (required for RepresentationClient)
--   2. Views: active_representations, company_rosters, credit_representation_summary
--   3. Triggers: updated_at on companies / representations / company_staff
--              + normalize_company_name auto-normalization on companies
--   4. Constraints: date-logic checks on representations / company_staff
-- =============================================================================


-- ---------------------------------------------------------------------------
-- 1. SEED REPRESENTATION TYPES
-- ---------------------------------------------------------------------------
-- These 10 types cover the full scope of A&R representation relationships.
-- RepresentationClient._load_type_map() queries this table at runtime, so
-- no IDs are hardcoded in Python — just use the short key aliases:
--
--   'label'        → Record Label
--   'publisher'    → Music Publisher
--   'management'   → Management
--   'booking'      → Booking Agent
--   'legal'        → Legal Representation
--   'business'     → Business Manager
--   'ar'           → A&R
--   'distribution' → Distribution
--   'sync'         → Sync Licensing
--   'brand'        → Brand Partnerships

INSERT INTO public.representation_types (type_name, category, description) VALUES
    ('Record Label',         'recording',    'Record label representing an artist for recordings'),
    ('Music Publisher',      'publishing',   'Publisher representing songwriting/composition rights'),
    ('Management',           'business',     'Artist/producer management'),
    ('Booking Agent',        'business',     'Live performance booking'),
    ('Legal Representation', 'business',     'Legal counsel'),
    ('Business Manager',     'business',     'Financial and business management'),
    ('A&R',                  'recording',    'Artist & Repertoire representation'),
    ('Distribution',         'recording',    'Distribution deal'),
    ('Sync Licensing',       'publishing',   'Synchronization licensing representation'),
    ('Brand Partnerships',   'business',     'Brand deals and endorsements')
ON CONFLICT (type_name) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 2. HELPER FUNCTION: auto-update updated_at on row changes
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_companies_updated_at     ON public.companies;
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON public.companies
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_representations_updated_at ON public.representations;
CREATE TRIGGER update_representations_updated_at
    BEFORE UPDATE ON public.representations
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_company_staff_updated_at ON public.company_staff;
CREATE TRIGGER update_company_staff_updated_at
    BEFORE UPDATE ON public.company_staff
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


-- ---------------------------------------------------------------------------
-- 3. TRIGGER: Auto-normalize company names
--    Converts "Sony Music Publishing" → "sony+music+publishing"
--    Fires on INSERT or UPDATE of name so normalized_name stays in sync.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.normalize_company_name()
RETURNS TRIGGER AS $$
BEGIN
    NEW.normalized_name = LOWER(
        REGEXP_REPLACE(
            REGEXP_REPLACE(NEW.name, '[^a-zA-Z0-9\s]', '', 'g'),
            '\s+', '+', 'g'
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS normalize_company_name_trigger ON public.companies;
CREATE TRIGGER normalize_company_name_trigger
    BEFORE INSERT OR UPDATE OF name ON public.companies
    FOR EACH ROW EXECUTE FUNCTION public.normalize_company_name();


-- ---------------------------------------------------------------------------
-- 4. DATA-INTEGRITY CONSTRAINTS
-- ---------------------------------------------------------------------------
-- These ensure is_active / is_current stay logically consistent with ended_at.

-- representations: is_active must be consistent with ended_at
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_representation_is_active_consistency'
          AND conrelid = 'public.representations'::regclass
    ) THEN
        ALTER TABLE public.representations
            ADD CONSTRAINT check_representation_is_active_consistency
            CHECK (
                (is_active = true  AND ended_at IS NULL) OR
                (is_active = false AND ended_at IS NOT NULL) OR
                (is_active IS NULL)
            );
    END IF;
END;
$$;

-- representations: date ordering
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_representation_dates'
          AND conrelid = 'public.representations'::regclass
    ) THEN
        ALTER TABLE public.representations
            ADD CONSTRAINT check_representation_dates
            CHECK (ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at);
    END IF;
END;
$$;

-- company_staff: is_current must be consistent with ended_at
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_company_staff_is_current_consistency'
          AND conrelid = 'public.company_staff'::regclass
    ) THEN
        ALTER TABLE public.company_staff
            ADD CONSTRAINT check_company_staff_is_current_consistency
            CHECK (
                (is_current = true  AND ended_at IS NULL) OR
                (is_current = false AND ended_at IS NOT NULL) OR
                (is_current IS NULL)
            );
    END IF;
END;
$$;

-- company_staff: date ordering
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_company_staff_dates'
          AND conrelid = 'public.company_staff'::regclass
    ) THEN
        ALTER TABLE public.company_staff
            ADD CONSTRAINT check_company_staff_dates
            CHECK (ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at);
    END IF;
END;
$$;

-- Partial unique index: one current employment per person per company
CREATE UNIQUE INDEX IF NOT EXISTS idx_company_staff_unique_current
    ON public.company_staff(credit_id, company_id)
    WHERE is_current = true;

-- Additional indexes for representation query patterns
CREATE INDEX IF NOT EXISTS idx_representations_credit_type_active
    ON public.representations(credit_id, representation_type_id, is_active);
CREATE INDEX IF NOT EXISTS idx_representations_company_type_active
    ON public.representations(company_id, representation_type_id, is_active);
CREATE INDEX IF NOT EXISTS idx_representations_verified
    ON public.representations(verified);
CREATE INDEX IF NOT EXISTS idx_companies_types
    ON public.companies USING GIN(company_types);


-- ---------------------------------------------------------------------------
-- 5. VIEWS
-- ---------------------------------------------------------------------------

-- All active representation relationships with full details
CREATE OR REPLACE VIEW public.active_representations AS
SELECT
    r.representation_id,
    c.credit_id,
    c.name                   AS credit_name,
    c.credit_category,
    co.company_id,
    co.name                  AS company_name,
    co.company_types,
    rt.type_name             AS representation_type,
    rt.category              AS representation_category,
    rep.name                 AS representative_name,
    rep.credit_id            AS representative_id,
    r.started_at,
    r.contract_type,
    r.territory,
    r.verified
FROM public.representations r
JOIN public.credits c               ON r.credit_id               = c.credit_id
JOIN public.companies co            ON r.company_id              = co.company_id
JOIN public.representation_types rt ON r.representation_type_id  = rt.type_id
LEFT JOIN public.credits rep        ON r.representative_credit_id = rep.credit_id
WHERE r.is_active = true;

COMMENT ON VIEW public.active_representations IS
    'All active representation relationships with full joined details';

-- Company roster: credits grouped by company + representation type
CREATE OR REPLACE VIEW public.company_rosters AS
SELECT
    co.company_id,
    co.name                                                       AS company_name,
    co.company_types,
    rt.type_name                                                  AS roster_type,
    COUNT(DISTINCT r.credit_id)                                   AS credit_count,
    ARRAY_AGG(DISTINCT c.name ORDER BY c.name)                    AS credits
FROM public.companies co
JOIN public.representations r       ON co.company_id              = r.company_id
JOIN public.representation_types rt ON r.representation_type_id   = rt.type_id
JOIN public.credits c               ON r.credit_id                = c.credit_id
WHERE r.is_active = true
GROUP BY co.company_id, co.name, co.company_types, rt.type_name;

COMMENT ON VIEW public.company_rosters IS
    'Company rosters grouped by representation type (active representations only)';

-- Credit representation summary: per-artist rollup
CREATE OR REPLACE VIEW public.credit_representation_summary AS
SELECT
    c.credit_id,
    c.name                                                              AS credit_name,
    c.credit_category,
    COUNT(DISTINCT r.company_id)                                        AS company_count,
    COUNT(DISTINCT CASE WHEN rt.category = 'recording'  THEN r.company_id END) AS label_count,
    COUNT(DISTINCT CASE WHEN rt.category = 'publishing' THEN r.company_id END) AS publisher_count,
    COUNT(DISTINCT CASE WHEN rt.category = 'business'   THEN r.company_id END) AS business_rep_count,
    ARRAY_AGG(DISTINCT co.name ORDER BY co.name)
        FILTER (WHERE r.is_active = true)                               AS active_companies
FROM public.credits c
LEFT JOIN public.representations r       ON c.credit_id    = r.credit_id
                                        AND r.is_active    = true
LEFT JOIN public.companies co            ON r.company_id   = co.company_id
LEFT JOIN public.representation_types rt ON r.representation_type_id = rt.type_id
GROUP BY c.credit_id, c.name, c.credit_category;

COMMENT ON VIEW public.credit_representation_summary IS
    'Per-credit rollup of representation counts and active company names';


-- ---------------------------------------------------------------------------
SELECT 'seed_representation_types.sql applied successfully!' AS status;
