CREATE TABLE users (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username text NOT NULL UNIQUE,
    password text NOT NULL,
    role text NOT NULL CHECK (role IN ('admin', 'operator', 'viewer')),
    active boolean NOT NULL DEFAULT true
);
CREATE TABLE audit_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_id text NOT NULL UNIQUE,
    actor text,
    method text NOT NULL,
    path text NOT NULL,
    status smallint NOT NULL,
    happened_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE jobs (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kind text NOT NULL,
    payload jsonb NOT NULL,
    status text NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'succeeded', 'failed')),
    result jsonb,
    error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);
CREATE INDEX jobs_queued ON jobs(id) WHERE status = 'queued';
