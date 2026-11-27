CREATE TABLE IF NOT EXISTS window_profiles (
    code text PRIMARY KEY,
    exhibit text NOT NULL,
    finish_code text NOT NULL,
    width_mm integer NOT NULL CHECK (width_mm BETWEEN 250 AND 5000),
    height_mm integer NOT NULL CHECK (height_mm BETWEEN 250 AND 5000),
    bevel_left_mm integer NOT NULL CHECK (bevel_left_mm BETWEEN 0 AND 400),
    bevel_right_mm integer NOT NULL CHECK (bevel_right_mm BETWEEN 0 AND 400),
    bleed_mm integer NOT NULL CHECK (bleed_mm BETWEEN 5 AND 80),
    pattern_axis text NOT NULL CHECK (pattern_axis IN ('any', 'vertical')),
    allow_seam boolean NOT NULL,
    revision integer NOT NULL DEFAULT 1 CHECK (revision >= 1),
    CHECK (width_mm - bevel_left_mm - bevel_right_mm >= 120),
    CHECK (height_mm > GREATEST(bevel_left_mm, bevel_right_mm))
);
