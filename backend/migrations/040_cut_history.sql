CREATE TABLE IF NOT EXISTS scrap_observations (
    observation_code text PRIMARY KEY,
    source_sheet uuid UNIQUE REFERENCES cut_receipts(sheet_id),
    feed_mm integer NOT NULL CHECK (feed_mm > 0),
    usable_width_mm integer NOT NULL CHECK (usable_width_mm > 0),
    cross_web_mm integer NOT NULL CHECK (cross_web_mm > 0),
    bevel_mm integer NOT NULL CHECK (bevel_mm >= 0),
    thickness_um integer NOT NULL CHECK (thickness_um > 0),
    panels integer NOT NULL CHECK (panels IN (1, 2)),
    loss_mm integer NOT NULL CHECK (loss_mm >= 0)
);
