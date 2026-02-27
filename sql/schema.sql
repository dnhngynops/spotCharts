-- =============================================================================
-- Spotify Charts / A&R Analytics Platform
-- Schema v2.0
-- =============================================================================
--
-- Design principles:
--
--   1. PIPELINE-FIRST
--      Table structure mirrors the data flow:
--        Selenium scrape → Spotify API enrichment → Supabase write.
--      See Section 7 (playlists / chart tracking) for the write-order summary.
--
--   2. CHARTS AS PLAYLISTS
--      Billboard (and any future external chart) is stored as a playlist row
--      with source_type = 'billboard'. The separate billboard_charts table has
--      been removed; position history lives in playlist_songs.
--
--   3. ALBUMS AS FIRST-CLASS ENTITIES
--      A dedicated albums table normalises the rich album data the pipeline
--      already fetches (_fetch_album_data). Songs carry a FK to albums;
--      album_credits and album_genres hang off albums. The full Spotify track
--      listing is also cached as JSONB (all_tracks) for dashboard use without
--      requiring every track to be individually charted.
--
--   4. CONSISTENT TIMESTAMPTZ
--      All timestamps use "timestamp with time zone" (timestamptz) throughout.
--
--   5. FUTURE-READY CRM SCAFFOLDING
--      Sections 8–12 (companies, representations, discovery, role mapping)
--      exist for the planned A&R enrichment pipeline. They do not need to be
--      written to during the initial Spotify chart collection phase.
--
-- Pipeline write order (for supabase_client.py):
--   1. playlists          — upsert by spotify_playlist_id
--   2. playlist_scrapes   — insert run record (get scrape_id)
--   3. credits            — upsert artists by spotify_id
--   4. credit_genres      — upsert genre ↔ artist links
--   5. albums             — upsert by spotify_id (includes all_tracks JSONB)
--   6. songs              — upsert by spotify_id, FK to album_id
--   7. song_credits       — upsert (song_id, credit_id, role_id)
--   8. song_genres        — upsert genre ↔ song links
--   9. playlist_songs     — insert observation (playlist, song, position, scrape)
--
-- =============================================================================


-- ---------------------------------------------------------------------------
-- 0. VERSIONING
-- ---------------------------------------------------------------------------

CREATE TABLE public.schema_version (
  version    text        NOT NULL,
  applied_at timestamptz DEFAULT now(),
  notes      text,
  CONSTRAINT schema_version_pkey PRIMARY KEY (version)
);

INSERT INTO public.schema_version (version, notes)
VALUES ('2.0.0', 'Pipeline-first schema: albums table, charts-as-playlists, consistent timestamptz');


-- ---------------------------------------------------------------------------
-- 1. FOUNDATION — no foreign-key dependencies on domain tables
-- ---------------------------------------------------------------------------

-- Supabase auth user profiles
CREATE TABLE public.profiles (
  profile_id uuid        NOT NULL DEFAULT gen_random_uuid(),
  user_id    uuid,                               -- links to auth.users
  username   text        UNIQUE,
  email      text,
  full_name  text,
  avatar_url text,
  bio        text,
  role       text,                               -- 'admin', 'analyst', 'viewer'
  preferences jsonb      DEFAULT '{}'::jsonb,
  created_at  timestamptz DEFAULT now(),
  updated_at  timestamptz DEFAULT now(),
  CONSTRAINT profiles_pkey PRIMARY KEY (profile_id)
);

-- Canonical role taxonomy shared across songs, albums, and credits
-- Examples: Artist, Producer, Songwriter, Engineer, A&R, Manager
CREATE TABLE public.roles (
  role_id       integer     NOT NULL GENERATED ALWAYS AS IDENTITY,
  role_name     text        NOT NULL UNIQUE,
  category      text,                            -- 'creative', 'business', 'technical'
  description   text,
  display_order integer     NOT NULL DEFAULT 0,
  created_at    timestamptz DEFAULT now(),
  CONSTRAINT roles_pkey PRIMARY KEY (role_id)
);

-- Genre taxonomy with optional parent ↔ child hierarchy
-- e.g. "Hip-Hop" → parent of "Trap", "Drill", etc.
CREATE TABLE public.genres (
  genre_id        integer     NOT NULL GENERATED ALWAYS AS IDENTITY,
  genre_name      text        NOT NULL UNIQUE,
  parent_genre_id integer,                       -- self-ref added as deferred FK below
  description     text,
  created_at      timestamptz DEFAULT now(),
  CONSTRAINT genres_pkey PRIMARY KEY (genre_id)
);

ALTER TABLE public.genres
  ADD CONSTRAINT genres_parent_genre_id_fkey
  FOREIGN KEY (parent_genre_id) REFERENCES public.genres(genre_id)
  DEFERRABLE INITIALLY DEFERRED;

-- Lookup for representation relationship categories
CREATE TABLE public.representation_types (
  type_id     integer NOT NULL GENERATED ALWAYS AS IDENTITY,
  type_name   text    NOT NULL UNIQUE,           -- 'record_deal', 'management', 'booking', etc.
  category    text    NOT NULL,                  -- 'label', 'management', 'legal', 'booking'
  description text,
  created_at  timestamptz DEFAULT now(),
  CONSTRAINT representation_types_pkey PRIMARY KEY (type_id)
);


-- ---------------------------------------------------------------------------
-- 2. COMPANIES
--    Labels, publishers, management firms, booking agencies, distributors, etc.
--    parent_company_id supports corporate hierarchies (e.g. UMG → Interscope).
-- ---------------------------------------------------------------------------

CREATE TABLE public.companies (
  company_id        integer     NOT NULL GENERATED ALWAYS AS IDENTITY,
  name              text        NOT NULL,
  normalized_name   text        NOT NULL UNIQUE,
  company_types     text[]      DEFAULT '{}'::text[]
                    CHECK (company_types <@ ARRAY[
                      'label','publisher','management','booking',
                      'legal','distribution','production','other'
                    ]::text[]),
  parent_company_id integer,                     -- self-ref; deferred FK below
  website           text,
  email             text,
  phone             text,
  address           text,
  city              text,
  state_province    text,
  postal_code       text,
  country           text,
  founded_date      date,
  description       text,
  logo_url          text,
  social_links      jsonb       DEFAULT '{}'::jsonb,
  metadata          jsonb       DEFAULT '{}'::jsonb,
  created_at        timestamptz DEFAULT now(),
  updated_at        timestamptz DEFAULT now(),
  CONSTRAINT companies_pkey PRIMARY KEY (company_id)
);

ALTER TABLE public.companies
  ADD CONSTRAINT companies_parent_company_id_fkey
  FOREIGN KEY (parent_company_id) REFERENCES public.companies(company_id)
  DEFERRABLE INITIALLY DEFERRED;


-- ---------------------------------------------------------------------------
-- 3. CREDITS
--    Unified entity for every person or act in the music industry:
--    recording artists, producers, songwriters, engineers, managers, A&R, etc.
--    One row per unique person/act; relationships to songs/albums via junctions.
-- ---------------------------------------------------------------------------

CREATE TABLE public.credits (
  credit_id                  bigint      NOT NULL GENERATED ALWAYS AS IDENTITY,
  name                       text        NOT NULL,
  normalized_name            text        NOT NULL UNIQUE,
  credit_category            text
                             CHECK (credit_category IS NULL OR credit_category = ANY (ARRAY[
                               'artist','producer','writer','engineer',
                               'manager','ar','executive','publisher_rep',
                               'label_rep','booking_agent','business_manager','legal','other'
                             ])),
  creative                   boolean     DEFAULT false,

  -- Spotify data (populated from API enrichment on first chart appearance)
  spotify_id                 text        UNIQUE,
  spotify_url                text,
  spotify_uri                text,
  spotify_image_url          text,
  spotify_popularity         integer,
  spotify_followers          integer,

  -- External identifiers (populated by future enrichment pipeline)
  genius_id                  integer,
  musicbrainz_id             text,

  -- Profile / biographical data (from future discovery pipeline)
  real_name                  text,
  bio                        text,
  image_url                  text,
  birth_date                 date,
  birth_place                text,
  website                    text,
  social_links               jsonb,
  metadata                   jsonb,

  -- Computed primary role (from role-mapping pipeline)
  primary_role_id            integer,
  primary_role_confidence    real,
  primary_role_calculated_at timestamptz,
  primary_role_method        text,

  created_at                 timestamptz DEFAULT now(),
  updated_at                 timestamptz DEFAULT now(),

  CONSTRAINT credits_pkey PRIMARY KEY (credit_id),
  CONSTRAINT credits_primary_role_id_fkey
    FOREIGN KEY (primary_role_id) REFERENCES public.roles(role_id)
);

CREATE INDEX idx_credits_spotify_id ON public.credits(spotify_id);


-- ---------------------------------------------------------------------------
-- 4. ALBUMS
--    Populated by the pipeline's _fetch_album_data() enrichment step.
--    Central hub for the A&R dashboard's album profiles feature.
--
--    Relationships:
--      albums  ←→  songs         (songs.album_id FK)
--      albums  ←→  credits       (album_credits junction — artists, exec producers, A&R)
--      albums  ←→  genres        (album_genres junction)
--      albums  →   companies     (label_id — the releasing label)
-- ---------------------------------------------------------------------------

CREATE TABLE public.albums (
  album_id        bigint      NOT NULL GENERATED ALWAYS AS IDENTITY,

  -- Spotify identifiers
  spotify_id      text        NOT NULL UNIQUE,
  spotify_url     text,
  spotify_uri     text,

  -- Core metadata
  name            text        NOT NULL,
  normalized_name text,
  album_type      text        CHECK (album_type IN ('album','single','compilation','ep')),
  release_date    date,
  total_tracks    integer,

  -- Media
  image_url       text,                          -- album art (highest-res from Spotify API)

  -- Industry identifiers (future enrichment)
  upc             text,                          -- Universal Product Code
  label_id        integer,                       -- releasing label

  -- Pipeline cache: full Spotify track listing (all_tracks from _fetch_album_data).
  -- Stored as JSONB so the dashboard album-profile modal works immediately.
  -- Individual tracks are also normalised into songs when they are charted.
  all_tracks      jsonb,

  -- Extended fields for future enrichment
  description     text,
  metadata        jsonb       DEFAULT '{}'::jsonb,

  created_at      timestamptz DEFAULT now(),
  updated_at      timestamptz DEFAULT now(),

  CONSTRAINT albums_pkey    PRIMARY KEY (album_id),
  CONSTRAINT albums_label_id_fkey
    FOREIGN KEY (label_id) REFERENCES public.companies(company_id)
);

CREATE INDEX idx_albums_label_id     ON public.albums(label_id);
CREATE INDEX idx_albums_release_date ON public.albums(release_date DESC NULLS LAST);
CREATE INDEX idx_albums_album_type   ON public.albums(album_type);


-- ---------------------------------------------------------------------------
-- 5. SONGS
--    One row per unique track (keyed by Spotify track ID).
--    Populated and updated by Spotify API enrichment; linked to an album.
-- ---------------------------------------------------------------------------

CREATE TABLE public.songs (
  song_id          bigint      NOT NULL GENERATED ALWAYS AS IDENTITY,

  -- Spotify identifiers
  spotify_id       text        NOT NULL UNIQUE,
  spotify_url      text,
  spotify_uri      text,

  -- Core metadata
  title            text        NOT NULL,
  normalized_title text,
  isrc             text,                          -- International Standard Recording Code

  -- Album relationship
  album_id         bigint,                        -- FK to albums; null until album is upserted

  -- Track-level Spotify metadata (point-in-time snapshot at last enrichment)
  duration_ms      integer,
  explicit         boolean     DEFAULT false,
  popularity       integer,                       -- 0–100
  preview_url      text,
  release_date     date,                          -- mirrors album release_date for fast queries

  created_at       timestamptz DEFAULT now(),
  updated_at       timestamptz DEFAULT now(),

  CONSTRAINT songs_pkey PRIMARY KEY (song_id),
  CONSTRAINT songs_album_id_fkey
    FOREIGN KEY (album_id) REFERENCES public.albums(album_id)
);

CREATE INDEX idx_songs_album_id     ON public.songs(album_id);
CREATE INDEX idx_songs_popularity   ON public.songs(popularity DESC NULLS LAST);
CREATE INDEX idx_songs_release_date ON public.songs(release_date DESC NULLS LAST);


-- ---------------------------------------------------------------------------
-- 6. JUNCTION TABLES — credits, genres attached to songs and albums
-- ---------------------------------------------------------------------------

-- Credits for individual tracks (artists, producers, writers, engineers, etc.)
CREATE TABLE public.song_credits (
  song_credit_id bigint   NOT NULL GENERATED ALWAYS AS IDENTITY,
  song_id        bigint   NOT NULL,
  credit_id      bigint   NOT NULL,
  role_id        integer  NOT NULL,
  raw_role_id    integer,                        -- original scraped role string; FK added later
  created_at     timestamptz DEFAULT now(),
  CONSTRAINT song_credits_pkey PRIMARY KEY (song_credit_id),
  CONSTRAINT song_credits_song_id_fkey   FOREIGN KEY (song_id)   REFERENCES public.songs(song_id),
  CONSTRAINT song_credits_credit_id_fkey FOREIGN KEY (credit_id) REFERENCES public.credits(credit_id),
  CONSTRAINT song_credits_role_id_fkey   FOREIGN KEY (role_id)   REFERENCES public.roles(role_id),
  CONSTRAINT uq_song_credits UNIQUE (song_id, credit_id, role_id)
);

CREATE INDEX idx_song_credits_song_id   ON public.song_credits(song_id);
CREATE INDEX idx_song_credits_credit_id ON public.song_credits(credit_id);

-- Credits at the album level (executive producers, A&R signatories, etc.)
CREATE TABLE public.album_credits (
  album_credit_id bigint   NOT NULL GENERATED ALWAYS AS IDENTITY,
  album_id        bigint   NOT NULL,
  credit_id       bigint   NOT NULL,
  role_id         integer  NOT NULL,
  notes           text,
  created_at      timestamptz DEFAULT now(),
  CONSTRAINT album_credits_pkey PRIMARY KEY (album_credit_id),
  CONSTRAINT album_credits_album_id_fkey  FOREIGN KEY (album_id)  REFERENCES public.albums(album_id),
  CONSTRAINT album_credits_credit_id_fkey FOREIGN KEY (credit_id) REFERENCES public.credits(credit_id),
  CONSTRAINT album_credits_role_id_fkey   FOREIGN KEY (role_id)   REFERENCES public.roles(role_id),
  CONSTRAINT uq_album_credits UNIQUE (album_id, credit_id, role_id)
);

CREATE INDEX idx_album_credits_album_id  ON public.album_credits(album_id);
CREATE INDEX idx_album_credits_credit_id ON public.album_credits(credit_id);

-- Genres for individual songs
-- source examples: 'spotify_artist', 'genius', 'musicbrainz', 'manual'
CREATE TABLE public.song_genres (
  song_genre_id bigint   NOT NULL GENERATED ALWAYS AS IDENTITY,
  song_id       bigint   NOT NULL,
  genre_id      integer  NOT NULL,
  confidence    real,                            -- 0.0–1.0; null = manual assertion
  source        text,
  metadata      jsonb,
  created_at    timestamptz DEFAULT now(),
  CONSTRAINT song_genres_pkey PRIMARY KEY (song_genre_id),
  CONSTRAINT song_genres_song_id_fkey  FOREIGN KEY (song_id)  REFERENCES public.songs(song_id),
  CONSTRAINT song_genres_genre_id_fkey FOREIGN KEY (genre_id) REFERENCES public.genres(genre_id),
  CONSTRAINT uq_song_genres UNIQUE (song_id, genre_id)
);

-- Genres for albums (often derived from song_genres or direct Spotify metadata)
CREATE TABLE public.album_genres (
  album_genre_id bigint   NOT NULL GENERATED ALWAYS AS IDENTITY,
  album_id       bigint   NOT NULL,
  genre_id       integer  NOT NULL,
  confidence     real,
  source         text,
  created_at     timestamptz DEFAULT now(),
  CONSTRAINT album_genres_pkey PRIMARY KEY (album_genre_id),
  CONSTRAINT album_genres_album_id_fkey FOREIGN KEY (album_id)  REFERENCES public.albums(album_id),
  CONSTRAINT album_genres_genre_id_fkey FOREIGN KEY (genre_id)  REFERENCES public.genres(genre_id),
  CONSTRAINT uq_album_genres UNIQUE (album_id, genre_id)
);

-- Genres associated with a credit/artist (from Spotify artist endpoint)
CREATE TABLE public.credit_genres (
  credit_genre_id bigint   NOT NULL GENERATED ALWAYS AS IDENTITY,
  credit_id       bigint   NOT NULL,
  genre_id        integer  NOT NULL,
  confidence      real,
  source          text,
  metadata        jsonb,
  created_at      timestamptz DEFAULT now(),
  CONSTRAINT credit_genres_pkey PRIMARY KEY (credit_genre_id),
  CONSTRAINT credit_genres_credit_id_fkey FOREIGN KEY (credit_id) REFERENCES public.credits(credit_id),
  CONSTRAINT credit_genres_genre_id_fkey  FOREIGN KEY (genre_id)  REFERENCES public.genres(genre_id),
  CONSTRAINT uq_credit_genres UNIQUE (credit_id, genre_id)
);


-- ---------------------------------------------------------------------------
-- 7. PLAYLISTS & CHART TRACKING
--
--    source_type distinguishes Spotify editorial playlists from external charts:
--      'spotify_editorial' — Spotify-curated playlists (primary pipeline source)
--      'spotify_personal'  — user-created playlists
--      'billboard'         — Billboard Hot 100, etc. (replaces billboard_charts)
--      'apple_music'       — Apple Music charts
--      'youtube_music'     — YouTube Music charts
--      'other'             — any other source
--
--    For Billboard: spotify_playlist_id is null; use name + source_type as identity.
--    Position history (previous_position, peak_position, weeks_on_chart) serves
--    both Spotify playlist trend tracking and Billboard-specific chart data.
-- ---------------------------------------------------------------------------

CREATE TABLE public.playlists (
  playlist_id         bigint  NOT NULL GENERATED ALWAYS AS IDENTITY,
  spotify_playlist_id text    UNIQUE,           -- null for non-Spotify sources
  name                text    NOT NULL,
  source_type         text    NOT NULL DEFAULT 'spotify_editorial'
                      CHECK (source_type IN (
                        'spotify_editorial','spotify_personal',
                        'billboard','apple_music','youtube_music','other'
                      )),
  description         text,
  owner               text,
  public              boolean DEFAULT true,
  collaborative       boolean DEFAULT false,
  total_tracks        integer,
  spotify_url         text,
  image_url           text,
  snapshot_id         text,                     -- Spotify snapshot for change detection
  created_at          timestamptz DEFAULT now(),
  updated_at          timestamptz DEFAULT now(),
  CONSTRAINT playlists_pkey PRIMARY KEY (playlist_id)
);

CREATE INDEX idx_playlists_source_type ON public.playlists(source_type);

-- One row per pipeline run (formerly 'runs')
CREATE TABLE public.playlist_scrapes (
  scrape_id       bigint  NOT NULL GENERATED ALWAYS AS IDENTITY,
  scrape_date     timestamptz DEFAULT now(),
  scrape_type     text    DEFAULT 'scheduled'
                  CHECK (scrape_type IN ('scheduled','manual','backfill')),
  status          text    DEFAULT 'in_progress'
                  CHECK (status IN ('in_progress','completed','failed','partial')),
  total_playlists integer,
  total_songs     integer,
  notes           text,
  started_at      timestamptz DEFAULT now(),
  completed_at    timestamptz,
  created_at      timestamptz DEFAULT now(),
  CONSTRAINT playlist_scrapes_pkey PRIMARY KEY (scrape_id)
);

-- Core chart observation: one row per track × playlist × scrape run
CREATE TABLE public.playlist_songs (
  playlist_song_id  bigint   NOT NULL GENERATED ALWAYS AS IDENTITY,
  playlist_id       bigint   NOT NULL,
  song_id           bigint   NOT NULL,
  scrape_id         bigint,

  -- Position data
  position          integer,                    -- rank/position this run
  previous_position integer,                    -- rank in the immediately prior scrape
  peak_position     integer,                    -- best-ever position on this playlist
  weeks_on_chart    integer  DEFAULT 1,         -- consecutive appearances (or total)

  -- Spotify playlist metadata per observation
  added_at          timestamptz,               -- when Spotify says the track was added
  added_by          text,

  created_at        timestamptz DEFAULT now(),

  CONSTRAINT playlist_songs_pkey PRIMARY KEY (playlist_song_id),
  CONSTRAINT playlist_songs_playlist_id_fkey
    FOREIGN KEY (playlist_id) REFERENCES public.playlists(playlist_id),
  CONSTRAINT playlist_songs_song_id_fkey
    FOREIGN KEY (song_id)     REFERENCES public.songs(song_id),
  CONSTRAINT playlist_songs_scrape_id_fkey
    FOREIGN KEY (scrape_id)   REFERENCES public.playlist_scrapes(scrape_id),
  CONSTRAINT uq_playlist_songs UNIQUE (playlist_id, song_id, scrape_id)
);

CREATE INDEX idx_playlist_songs_playlist_id ON public.playlist_songs(playlist_id);
CREATE INDEX idx_playlist_songs_song_id     ON public.playlist_songs(song_id);
CREATE INDEX idx_playlist_songs_scrape_id   ON public.playlist_songs(scrape_id);


-- ---------------------------------------------------------------------------
-- 8. INDUSTRY RELATIONSHIPS (A&R CRM)
--    Not written to by the current Spotify pipeline; populated by future
--    enrichment phases (Genius, AllMusic, manual research, etc.).
-- ---------------------------------------------------------------------------

-- People at companies (an individual credit employed by a company)
CREATE TABLE public.company_staff (
  staff_id        integer NOT NULL GENERATED ALWAYS AS IDENTITY,
  credit_id       bigint  NOT NULL,
  company_id      integer NOT NULL,
  job_title       text    NOT NULL,
  department      text,
  seniority_level text,
  started_at      date,
  ended_at        date,
  is_current      boolean DEFAULT true,
  work_email      text,
  work_phone      text,
  office_location text,
  notes           text,
  created_at      timestamptz DEFAULT now(),
  updated_at      timestamptz DEFAULT now(),
  CONSTRAINT company_staff_pkey PRIMARY KEY (staff_id),
  CONSTRAINT company_staff_credit_id_fkey  FOREIGN KEY (credit_id)  REFERENCES public.credits(credit_id),
  CONSTRAINT company_staff_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(company_id)
);

-- Representation relationships: artist ↔ label, manager, publisher, lawyer, etc.
CREATE TABLE public.representations (
  representation_id       integer NOT NULL GENERATED ALWAYS AS IDENTITY,
  credit_id               bigint  NOT NULL,     -- the represented artist/act
  company_id              integer NOT NULL,     -- the representing firm
  representation_type_id  integer NOT NULL,
  representative_credit_id bigint,             -- specific individual at the company
  started_at              date,
  ended_at                date,
  is_active               boolean DEFAULT true,
  contract_type           text,
  territory               text[],
  verified                boolean DEFAULT false,
  verification_date       timestamptz,
  verification_source     text,
  notes                   text,
  metadata                jsonb   DEFAULT '{}'::jsonb,
  created_at              timestamptz DEFAULT now(),
  updated_at              timestamptz DEFAULT now(),
  CONSTRAINT representations_pkey PRIMARY KEY (representation_id),
  CONSTRAINT representations_credit_id_fkey
    FOREIGN KEY (credit_id)               REFERENCES public.credits(credit_id),
  CONSTRAINT representations_company_id_fkey
    FOREIGN KEY (company_id)              REFERENCES public.companies(company_id),
  CONSTRAINT representations_type_id_fkey
    FOREIGN KEY (representation_type_id)  REFERENCES public.representation_types(type_id),
  CONSTRAINT representations_rep_credit_id_fkey
    FOREIGN KEY (representative_credit_id) REFERENCES public.credits(credit_id)
);

-- Internal teams (A&R analysts, scouts, label departments, etc.)
CREATE TABLE public.teams (
  team_id          bigint  NOT NULL GENERATED ALWAYS AS IDENTITY,
  team_name        text    NOT NULL UNIQUE,
  description      text,
  team_type        text,
  owner_profile_id uuid,
  metadata         jsonb,
  created_at       timestamptz DEFAULT now(),
  updated_at       timestamptz DEFAULT now(),
  CONSTRAINT teams_pkey PRIMARY KEY (team_id),
  CONSTRAINT teams_owner_profile_id_fkey
    FOREIGN KEY (owner_profile_id) REFERENCES public.profiles(profile_id)
);

-- Artists/acts on a team's roster
CREATE TABLE public.rosters (
  roster_id      bigint  NOT NULL GENERATED ALWAYS AS IDENTITY,
  team_id        bigint  NOT NULL,
  credit_id      bigint  NOT NULL,
  role_on_roster text,
  contract_start date,
  contract_end   date,
  active         boolean DEFAULT true,
  notes          text,
  created_at     timestamptz DEFAULT now(),
  updated_at     timestamptz DEFAULT now(),
  CONSTRAINT rosters_pkey PRIMARY KEY (roster_id),
  CONSTRAINT rosters_team_id_fkey   FOREIGN KEY (team_id)   REFERENCES public.teams(team_id),
  CONSTRAINT rosters_credit_id_fkey FOREIGN KEY (credit_id) REFERENCES public.credits(credit_id),
  CONSTRAINT uq_rosters UNIQUE (team_id, credit_id)
);


-- ---------------------------------------------------------------------------
-- 9. ROLE NORMALIZATION PIPELINE
--    Maps raw scraped role strings (e.g. "Rec. Engineer", "Exec. Producer")
--    to canonical entries in the roles table. Populated by enrichment phases.
-- ---------------------------------------------------------------------------

-- Raw role strings as scraped from Genius, AllMusic, liner notes, etc.
CREATE TABLE public.raw_role_names (
  raw_role_id        integer     NOT NULL GENERATED ALWAYS AS IDENTITY,
  raw_role_name      text        NOT NULL UNIQUE,
  normalized_name    text        NOT NULL,
  source_count       integer     DEFAULT 0,
  first_seen_at      timestamptz DEFAULT now(),
  last_seen_at       timestamptz DEFAULT now(),
  primary_role_id    integer,
  mapping_confidence real,
  mapping_method     text,
  mapped_at          timestamptz,
  mapped_by          text,
  needs_review       boolean     DEFAULT true,
  is_ambiguous       boolean     DEFAULT false,
  created_at         timestamptz DEFAULT now(),
  updated_at         timestamptz DEFAULT now(),
  CONSTRAINT raw_role_names_pkey PRIMARY KEY (raw_role_id),
  CONSTRAINT raw_role_names_primary_role_id_fkey
    FOREIGN KEY (primary_role_id) REFERENCES public.roles(role_id)
);

-- Deferred FK from song_credits.raw_role_id (raw_role_names created after song_credits)
ALTER TABLE public.song_credits
  ADD CONSTRAINT song_credits_raw_role_id_fkey
  FOREIGN KEY (raw_role_id) REFERENCES public.raw_role_names(raw_role_id);

-- Keyword/pattern rules for automatic role-name mapping
CREATE TABLE public.role_mapping_patterns (
  pattern_id      integer NOT NULL GENERATED ALWAYS AS IDENTITY,
  primary_role_id integer NOT NULL,
  keyword         text    NOT NULL,
  pattern_type    text    NOT NULL,              -- 'exact', 'contains', 'starts_with', 'regex'
  priority        integer DEFAULT 50,
  created_at      timestamptz DEFAULT now(),
  CONSTRAINT role_mapping_patterns_pkey PRIMARY KEY (pattern_id),
  CONSTRAINT role_mapping_patterns_primary_role_id_fkey
    FOREIGN KEY (primary_role_id) REFERENCES public.roles(role_id)
);

-- Fuzzy/ML suggestions for unmapped raw role names (human review queue)
CREATE TABLE public.role_mapping_suggestions (
  suggestion_id             integer NOT NULL GENERATED ALWAYS AS IDENTITY,
  raw_role_id               integer NOT NULL,
  suggested_primary_role_id integer NOT NULL,
  similarity_score          real    NOT NULL,
  matching_method           text    NOT NULL,
  matched_keywords          text[],
  suggestion_rank           integer,
  reviewed                  boolean DEFAULT false,
  accepted                  boolean,
  reviewed_by               text,
  reviewed_at               timestamptz,
  suggested_at              timestamptz DEFAULT now(),
  CONSTRAINT role_mapping_suggestions_pkey PRIMARY KEY (suggestion_id),
  CONSTRAINT rms_raw_role_id_fkey
    FOREIGN KEY (raw_role_id)               REFERENCES public.raw_role_names(raw_role_id),
  CONSTRAINT rms_suggested_role_id_fkey
    FOREIGN KEY (suggested_primary_role_id) REFERENCES public.roles(role_id)
);


-- ---------------------------------------------------------------------------
-- 10. DISCOVERY PIPELINE
--     Web scraping layer for A&R intelligence: management pages, label rosters,
--     Wikipedia, social media, etc. Populated by future enrichment phases.
-- ---------------------------------------------------------------------------

-- URLs discovered for a credit (roster pages, Wikipedia, socials, etc.)
CREATE TABLE public.discovery_urls (
  discovery_url_id bigint  NOT NULL GENERATED ALWAYS AS IDENTITY,
  credit_id        bigint  NOT NULL,
  url              text    NOT NULL,
  url_category     text    NOT NULL
                   CHECK (url_category IN (
                     'wikipedia','social_media','credit_source','dsp_page',
                     'publication','roster_page','official_website'
                   )),
  url_subcategory  text,
  title            text,
  snippet          text,
  confidence       real    DEFAULT 1.0,
  metadata         jsonb,
  processed        boolean DEFAULT false,
  captured_at      timestamptz DEFAULT now(),
  CONSTRAINT discovery_urls_pkey PRIMARY KEY (discovery_url_id),
  CONSTRAINT discovery_urls_credit_id_fkey
    FOREIGN KEY (credit_id) REFERENCES public.credits(credit_id)
);

-- Structured data extracted from discovered URLs
CREATE TABLE public.discovery_extractions (
  extraction_id             bigint  NOT NULL GENERATED ALWAYS AS IDENTITY,
  credit_id                 bigint  NOT NULL,
  discovery_url_id          bigint,
  extraction_type           text    NOT NULL,
  extracted_value           text    NOT NULL,
  entity_type               text    CHECK (entity_type IN ('company','individual')),
  representation_type       text,
  confidence_score          real,
  classification_confidence real,
  pattern_used              text,
  context_snippet           text,
  indicators                text[],
  extracted_at              timestamptz DEFAULT now(),
  CONSTRAINT discovery_extractions_pkey PRIMARY KEY (extraction_id),
  CONSTRAINT discovery_extractions_credit_id_fkey
    FOREIGN KEY (credit_id)          REFERENCES public.credits(credit_id),
  CONSTRAINT discovery_extractions_url_id_fkey
    FOREIGN KEY (discovery_url_id)   REFERENCES public.discovery_urls(discovery_url_id)
);

-- Audit log for each web-discovery search run
CREATE TABLE public.discovery_search_logs (
  log_id                  bigint  NOT NULL GENERATED ALWAYS AS IDENTITY,
  credit_id               bigint,
  credit_name             text    NOT NULL,
  search_query            text    NOT NULL,
  urls_found              integer DEFAULT 0,
  companies_extracted     integer DEFAULT 0,
  individuals_extracted   integer DEFAULT 0,
  representations_created integer DEFAULT 0,
  success                 boolean DEFAULT true,
  error_message           text,
  search_timestamp        timestamptz DEFAULT now(),
  CONSTRAINT discovery_search_logs_pkey PRIMARY KEY (log_id),
  CONSTRAINT discovery_search_logs_credit_id_fkey
    FOREIGN KEY (credit_id) REFERENCES public.credits(credit_id)
);


-- ---------------------------------------------------------------------------
-- 11. PIPELINE OPERATIONS
--     Tracks enrichment progress per entity so long-running jobs can resume.
-- ---------------------------------------------------------------------------

CREATE TABLE public.processing_progress (
  progress_id   bigint  NOT NULL GENERATED ALWAYS AS IDENTITY,
  phase         text    NOT NULL,               -- 'spotify_enrichment', 'genius_credits', etc.
  entity_type   text    NOT NULL,               -- 'song', 'album', 'credit'
  entity_id     bigint  NOT NULL,
  status        text    NOT NULL
                CHECK (status IN ('pending','in_progress','completed','failed','skipped')),
  iteration     integer DEFAULT 1,
  error_message text,
  metadata      jsonb,
  started_at    timestamptz,
  completed_at  timestamptz,
  created_at    timestamptz DEFAULT now(),
  updated_at    timestamptz DEFAULT now(),
  CONSTRAINT processing_progress_pkey PRIMARY KEY (progress_id),
  CONSTRAINT uq_processing_progress UNIQUE (phase, entity_type, entity_id, iteration)
);

-- Partial index: only index rows that still need work
CREATE INDEX idx_processing_progress_pending
  ON public.processing_progress(phase, entity_type)
  WHERE status IN ('pending','in_progress');


-- ---------------------------------------------------------------------------
-- 12. USER FEATURES
-- ---------------------------------------------------------------------------

-- Named watchlists of credits/artists for A&R tracking
CREATE TABLE public.watchlists (
  watchlist_id   bigint  NOT NULL GENERATED ALWAYS AS IDENTITY,
  profile_id     uuid    NOT NULL,
  watchlist_name text    NOT NULL,
  description    text,
  public         boolean DEFAULT false,
  created_at     timestamptz DEFAULT now(),
  updated_at     timestamptz DEFAULT now(),
  CONSTRAINT watchlists_pkey PRIMARY KEY (watchlist_id),
  CONSTRAINT watchlists_profile_id_fkey
    FOREIGN KEY (profile_id) REFERENCES public.profiles(profile_id)
);

CREATE TABLE public.watchlist_items (
  watchlist_item_id bigint  NOT NULL GENERATED ALWAYS AS IDENTITY,
  watchlist_id      bigint  NOT NULL,
  credit_id         bigint  NOT NULL,
  added_at          timestamptz DEFAULT now(),
  notes             text,
  CONSTRAINT watchlist_items_pkey PRIMARY KEY (watchlist_item_id),
  CONSTRAINT watchlist_items_watchlist_id_fkey
    FOREIGN KEY (watchlist_id) REFERENCES public.watchlists(watchlist_id),
  CONSTRAINT watchlist_items_credit_id_fkey
    FOREIGN KEY (credit_id)    REFERENCES public.credits(credit_id),
  CONSTRAINT uq_watchlist_items UNIQUE (watchlist_id, credit_id)
);
