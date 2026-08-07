CREATE TABLE IF NOT EXISTS weather.location_cache
(
    location_key TEXT PRIMARY KEY,

    latitude DOUBLE PRECISION NOT NULL,

    longitude DOUBLE PRECISION NOT NULL,

    display_name TEXT,

    nws_office TEXT,

    nws_grid_x INTEGER,

    nws_grid_y INTEGER,

    payload JSONB NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


COMMENT ON TABLE weather.location_cache IS
'Caches geocoding results and NWS grid point metadata';

