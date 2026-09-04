-- ============================================================
-- Supabase Schema: Routes & Stops for APSRTC GTFS Dataset
-- Run this in your Supabase SQL Editor if you wish to host
-- all 2,900+ routes and 55,000+ stops directly in Supabase Postgres.
-- ============================================================

-- 1. Routes Table
CREATE TABLE IF NOT EXISTS public.routes (
    id BIGSERIAL PRIMARY KEY,
    route_name TEXT NOT NULL,
    source TEXT NOT NULL,
    destination TEXT NOT NULL,
    operator TEXT DEFAULT 'APSRTC',
    service_type TEXT DEFAULT 'Standard',
    data_source TEXT DEFAULT 'OFFICIAL',
    source_name TEXT DEFAULT 'APSRTC GTFS Open Data',
    source_type TEXT DEFAULT 'Government Transit Feed',
    source_url TEXT,
    verified_at DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index on route_name, source, destination for fast search
CREATE INDEX IF NOT EXISTS idx_routes_name ON public.routes (route_name);
CREATE INDEX IF NOT EXISTS idx_routes_source_dest ON public.routes (source, destination);

-- 2. Stops Table
CREATE TABLE IF NOT EXISTS public.stops (
    id BIGSERIAL PRIMARY KEY,
    route_id BIGINT REFERENCES public.routes(id) ON DELETE CASCADE,
    stop_name TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    stop_order INTEGER NOT NULL,
    area_type TEXT,
    scheduled_arrival_time TIME,
    data_source TEXT DEFAULT 'OFFICIAL',
    source_name TEXT DEFAULT 'APSRTC GTFS Open Data',
    source_type TEXT DEFAULT 'Government Transit Feed',
    source_url TEXT,
    verified_at DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for route stop lookups and spatial queries
CREATE INDEX IF NOT EXISTS idx_stops_route_id ON public.stops (route_id);
CREATE INDEX IF NOT EXISTS idx_stops_route_order ON public.stops (route_id, stop_order);
CREATE INDEX IF NOT EXISTS idx_stops_lat_lon ON public.stops (latitude, longitude);

-- 3. Enable Row Level Security (RLS) & Public Read Access
ALTER TABLE public.routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stops ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access on routes"
    ON public.routes FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "Allow public read access on stops"
    ON public.stops FOR SELECT
    TO anon, authenticated
    USING (true);
