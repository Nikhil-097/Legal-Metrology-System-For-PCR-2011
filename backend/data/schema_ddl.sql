-- ============================================================================
-- Legal Metrology (Packaged Commodities) Compliance Engine - DDL Schema
-- ============================================================================

BEGIN;

-- Enable PostGIS for spatial inspection coordinate tracking (Optional)
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Official Gazette Documents Registry[cite: 3]
CREATE TABLE IF NOT EXISTS legal_documents (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    notification_number TEXT UNIQUE NOT NULL,
    publication_date DATE NOT NULL,
    effective_date DATE NOT NULL,
    source_url TEXT,
    role TEXT NOT NULL DEFAULT 'amendment', -- 'baseline_consolidated', 'amendment', 'corrigendum'
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Master Rule Inventory (Rules 1-34)[cite: 3]
CREATE TABLE IF NOT EXISTS legal_rules (
    id BIGSERIAL PRIMARY KEY,
    rule_number TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    principal_effective_from DATE NOT NULL DEFAULT '2011-04-01'
);

-- 3. Temporal Rule Versions (Tracks Changes Across Effective Dates)[cite: 3]
CREATE TABLE IF NOT EXISTS rule_versions (
    id BIGSERIAL PRIMARY KEY,
    rule_id BIGINT NOT NULL REFERENCES legal_rules(id) ON DELETE CASCADE,
    version_label TEXT NOT NULL,
    operative_text TEXT,
    effective_from DATE NOT NULL,
    effective_to DATE, -- NULL indicates active rule version
    source_document_id BIGINT REFERENCES legal_documents(id) ON DELETE SET NULL,
    legal_status TEXT DEFAULT 'active',
    verification_status TEXT DEFAULT 'verified',
    UNIQUE(rule_id, version_label)
);

-- 4. Machine-Checkable Requirements (Regex, Units, Error Mapping)[cite: 3]
CREATE TABLE IF NOT EXISTS rule_requirements (
    id BIGSERIAL PRIMARY KEY,
    rule_version_id BIGINT REFERENCES rule_versions(id) ON DELETE CASCADE,
    requirement_code TEXT NOT NULL,
    description TEXT NOT NULL,
    field_name TEXT NOT NULL,
    regex_pattern TEXT,
    allowed_units TEXT[],
    severity TEXT NOT NULL DEFAULT 'HIGH', -- 'HIGH', 'MEDIUM', 'LOW'
    machine_checkable BOOLEAN NOT NULL DEFAULT TRUE,
    is_ecommerce_rule BOOLEAN NOT NULL DEFAULT FALSE,
    is_multipack_rule BOOLEAN NOT NULL DEFAULT FALSE,
    effective_from DATE NOT NULL,
    effective_to DATE,
    UNIQUE(rule_version_id, requirement_code)
);

-- 5. Rule 7 Font Size and Principal Display Panel (PDP) Rules Matrix
CREATE TABLE IF NOT EXISTS font_size_rules (
    id BIGSERIAL PRIMARY KEY,
    pdp_area_min_cm2 NUMERIC NOT NULL DEFAULT 0,
    pdp_area_max_cm2 NUMERIC, -- NULL represents open upper bound (> 500 cm2)
    weight_volume_threshold_g_ml NUMERIC NOT NULL DEFAULT 200,
    min_font_height_mm_small_pack NUMERIC NOT NULL,
    min_font_height_mm_large_pack NUMERIC NOT NULL,
    min_font_height_mm_blown_moulded NUMERIC,
    effective_from DATE NOT NULL DEFAULT '2011-04-01',
    effective_to DATE
);

-- 6. Schedules Inventory (Schedules 1-7)[cite: 3]
CREATE TABLE IF NOT EXISTS schedules (
    id BIGSERIAL PRIMARY KEY,
    schedule_number INTEGER NOT NULL UNIQUE,
    title TEXT NOT NULL
);

-- 7. First Schedule: Maximum Permissible Error (MPE) Entries[cite: 3]
CREATE TABLE IF NOT EXISTS schedule_entries (
    id BIGSERIAL PRIMARY KEY,
    schedule_id BIGINT NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    entry_key TEXT NOT NULL,
    quantity_min NUMERIC NOT NULL DEFAULT 0,
    quantity_max NUMERIC, -- NULL represents 'infinity' / open-ended upper bound
    unit TEXT NOT NULL,
    percentage_error NUMERIC,
    absolute_error NUMERIC,
    formula TEXT,
    effective_from DATE NOT NULL DEFAULT '2011-04-01',
    effective_to DATE,
    notes TEXT
);

-- 8. Rule 26 Statutory Exemptions Table[cite: 3]
CREATE TABLE IF NOT EXISTS legal_exemptions (
    id BIGSERIAL PRIMARY KEY,
    exemption_code TEXT NOT NULL UNIQUE,
    rule_reference TEXT NOT NULL DEFAULT 'Rule 26',
    category_name TEXT NOT NULL,
    condition_description TEXT NOT NULL,
    min_quantity NUMERIC,
    max_quantity NUMERIC,
    unit TEXT,
    exempt_from_fields TEXT[] NOT NULL, -- Array of fields exempt from compliance check
    effective_from DATE NOT NULL DEFAULT '2011-04-01',
    effective_to DATE,
    notes TEXT
);

-- 9. Inspection Scan Records & Verification History
CREATE TABLE IF NOT EXISTS scan_records (
    id BIGSERIAL PRIMARY KEY,
    inspector_id TEXT NOT NULL,
    brand_name TEXT,
    commodity_name TEXT,
    pdp_area_cm2 NUMERIC,
    raw_ocr_payload JSONB,
    extracted_fields JSONB,
    violations JSONB,
    overall_compliance_score NUMERIC(5,2),
    is_compliant BOOLEAN NOT NULL DEFAULT FALSE,
    image_storage_path TEXT NOT NULL,
    location_point GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Performance Optimization Indexes[cite: 3]
CREATE INDEX IF NOT EXISTS idx_rule_versions_dates ON rule_versions(rule_id, effective_from, effective_to);[cite: 3]
CREATE INDEX IF NOT EXISTS idx_requirements_codes_dates ON rule_requirements(requirement_code, effective_from, effective_to);[cite: 3]
CREATE INDEX IF NOT EXISTS idx_requirements_flags ON rule_requirements(is_ecommerce_rule, is_multipack_rule);[cite: 3]
CREATE INDEX IF NOT EXISTS idx_schedule_entries_qty ON schedule_entries(schedule_id, quantity_min, quantity_max);[cite: 3]
CREATE INDEX IF NOT EXISTS idx_exemptions_code ON legal_exemptions(exemption_code);[cite: 3]
CREATE INDEX IF NOT EXISTS idx_scan_records_date ON scan_records(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scan_records_compliance ON scan_records(is_compliant);

COMMIT;