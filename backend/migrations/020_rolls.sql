CREATE TABLE IF NOT EXISTS film_rolls (
    code text PRIMARY KEY,
    finish_code text NOT NULL,
    width_mm integer NOT NULL CHECK (width_mm BETWEEN 250 AND 3500),
    edge_damage_mm integer NOT NULL CHECK (edge_damage_mm BETWEEN 0 AND 150),
    pattern text NOT NULL CHECK (pattern IN ('neutral', 'lengthwise')),
    thickness_um integer NOT NULL CHECK (thickness_um BETWEEN 30 AND 300),
    initial_length_mm integer NOT NULL CHECK (initial_length_mm BETWEEN 500 AND 200000),
    consumed_mm integer NOT NULL DEFAULT 0 CHECK (consumed_mm >= 0),
    reserved_mm integer NOT NULL DEFAULT 0 CHECK (reserved_mm >= 0),
    CHECK (width_mm - 2 * edge_damage_mm >= 180),
    CHECK (consumed_mm + reserved_mm <= initial_length_mm)
);
