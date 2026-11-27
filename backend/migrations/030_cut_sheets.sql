CREATE TABLE IF NOT EXISTS cut_sheets (
    id uuid PRIMARY KEY,
    window_code text NOT NULL REFERENCES window_profiles(code),
    window_revision integer NOT NULL CHECK (window_revision >= 1),
    roll_code text NOT NULL REFERENCES film_rolls(code),
    orientation text NOT NULL CHECK (orientation IN ('upright', 'sideways')),
    usable_width_mm integer NOT NULL CHECK (usable_width_mm >= 180),
    feed_mm integer NOT NULL CHECK (feed_mm > 0),
    predicted_loss_mm integer NOT NULL CHECK (predicted_loss_mm >= 0),
    allowance_mm integer NOT NULL CHECK (allowance_mm = feed_mm + predicted_loss_mm),
    geometry jsonb NOT NULL,
    metrics jsonb NOT NULL,
    state text NOT NULL DEFAULT 'draft' CHECK (state IN ('draft', 'issued', 'cut', 'void')),
    issued_order bigint,
    issued_at timestamptz,
    void_reason text,
    CHECK ((issued_at IS NULL) = (issued_order IS NULL)),
    CHECK (state NOT IN ('issued', 'cut') OR issued_at IS NOT NULL),
    CHECK ((state = 'void') = (void_reason IS NOT NULL))
);
CREATE SEQUENCE IF NOT EXISTS cut_sheet_issue_order;
CREATE UNIQUE INDEX IF NOT EXISTS unique_cut_issue_order ON cut_sheets (issued_order);
CREATE UNIQUE INDEX IF NOT EXISTS one_issued_cut_per_window ON cut_sheets (window_code) WHERE state = 'issued';
CREATE INDEX IF NOT EXISTS cut_sheets_issue_queue ON cut_sheets (roll_code, issued_order) WHERE state = 'issued';

CREATE TABLE IF NOT EXISTS cut_panels (
    sheet_id uuid REFERENCES cut_sheets(id) ON DELETE CASCADE,
    panel_no integer CHECK (panel_no IN (1, 2)),
    cross_web_mm integer NOT NULL CHECK (cross_web_mm > 0),
    advance_mm integer NOT NULL CHECK (advance_mm > 0),
    PRIMARY KEY (sheet_id, panel_no)
);

CREATE TABLE IF NOT EXISTS cut_receipts (
    sheet_id uuid PRIMARY KEY REFERENCES cut_sheets(id),
    segment_from_mm integer NOT NULL CHECK (segment_from_mm >= 0),
    segment_to_mm integer NOT NULL CHECK (segment_to_mm > segment_from_mm),
    measured_loss_mm integer NOT NULL CHECK (measured_loss_mm >= 0),
    released_reserve_mm integer NOT NULL CHECK (released_reserve_mm >= 0),
    cut_by text NOT NULL,
    cut_at timestamptz NOT NULL DEFAULT now()
);
