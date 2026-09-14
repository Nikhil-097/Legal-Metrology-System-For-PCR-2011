-- Schema DDL for Legal Metrology Verification System
BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users & Auditors Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    badge_number VARCHAR(50),
    role VARCHAR(50) DEFAULT 'INSPECTOR',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Statutory Rules Catalog
CREATE TABLE IF NOT EXISTS statutory_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_code VARCHAR(50) UNIQUE NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    act_name VARCHAR(100) DEFAULT 'Legal Metrology (Packaged Commodities) Rules 2011',
    description TEXT,
    severity VARCHAR(20) DEFAULT 'MAJOR',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Rule Requirements Matrix
CREATE TABLE IF NOT EXISTS rule_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID REFERENCES statutory_rules(id) ON DELETE CASCADE,
    requirement_code VARCHAR(100) NOT NULL,
    parameter_name VARCHAR(100) NOT NULL,
    min_value NUMERIC(10, 4),
    max_value NUMERIC(10, 4),
    unit VARCHAR(20),
    effective_from DATE DEFAULT '2011-04-01',
    effective_to DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Packaging Inspections / Scans
CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_ref VARCHAR(50) UNIQUE NOT NULL,
    auditor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    brand_name VARCHAR(150),
    commodity_name VARCHAR(150),
    raw_image_url TEXT,
    annotated_image_url TEXT,
    pdp_area_cm2 NUMERIC(10, 2),
    compliance_score INT NOT NULL,
    is_compliant BOOLEAN NOT NULL,
    location_geom GEOMETRY(Point, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Extracted Statutory Declarations
CREATE TABLE IF NOT EXISTS scan_declarations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    net_quantity VARCHAR(100),
    mrp VARCHAR(100),
    has_tax_clause BOOLEAN DEFAULT FALSE,
    unit_sale_price VARCHAR(100),
    mfg_date VARCHAR(100),
    expiry_date VARCHAR(100),
    batch_number VARCHAR(100),
    fssai_license VARCHAR(100),
    country_of_origin VARCHAR(100),
    raw_response JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Itemized Non-Compliance Infractions
CREATE TABLE IF NOT EXISTS scan_violations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    rule_code VARCHAR(50) NOT NULL,
    violation_title VARCHAR(255) NOT NULL,
    description TEXT,
    legal_context TEXT,
    act_reference VARCHAR(255),
    severity VARCHAR(20) DEFAULT 'MAJOR',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Audit Certificates & Reports
CREATE TABLE IF NOT EXISTS inspection_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    report_number VARCHAR(100) UNIQUE NOT NULL,
    pdf_url TEXT,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Fast Query Performance
CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scans_compliance ON scans(is_compliant);
CREATE INDEX IF NOT EXISTS idx_violations_scan_id ON scan_violations(scan_id);
CREATE INDEX IF NOT EXISTS idx_declarations_scan_id ON scan_declarations(scan_id);
CREATE INDEX IF NOT EXISTS idx_requirements_codes_dates ON rule_requirements(requirement_code, effective_from, effective_to);

COMMIT;
