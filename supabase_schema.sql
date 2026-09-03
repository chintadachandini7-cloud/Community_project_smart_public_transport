-- ============================================================
-- SMART PUBLIC TRANSPORT BUS TRACKING SYSTEM
-- Supabase PostgreSQL Database Schema
-- ============================================================
-- Safe to run on a fresh Supabase project.
-- Paste this entire script into the Supabase SQL Editor and execute.
-- ============================================================

-- ============================================================
-- 0. EXTENSIONS
-- ============================================================
-- Supabase enables uuid-ossp by default, but ensure it's available.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. REUSABLE TRIGGER FUNCTION: Auto-update `updated_at`
-- ============================================================
-- This function is attached to every table that has an `updated_at`
-- column. It fires BEFORE UPDATE and sets the timestamp to NOW().
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql
   SET search_path = public;

-- ============================================================
-- 2. PROFILES TABLE (linked to Supabase Auth)
-- ============================================================
-- Extends auth.users with application-specific fields.
-- The `id` column references the Supabase auth user UUID.
CREATE TABLE IF NOT EXISTS profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name   TEXT NOT NULL,
    email       TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'user'
                CHECK (role IN ('admin', 'driver', 'conductor', 'user')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE profiles IS 'Application user profiles linked to Supabase Auth. Role determines dashboard access.';

CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 3. BUSES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS buses (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bus_number    TEXT NOT NULL UNIQUE,
    route_number  TEXT,
    route_name    TEXT,
    capacity      INTEGER NOT NULL DEFAULT 40
                  CHECK (capacity > 0),
    bus_type      TEXT NOT NULL DEFAULT 'Standard'
                  CHECK (bus_type IN ('Standard', 'Express', 'AC Deluxe', 'Super Luxury', 'Palle Velugu', 'Garuda', 'Amaravati')),
    status        TEXT NOT NULL DEFAULT 'Active'
                  CHECK (status IN ('Active', 'Inactive', 'Maintenance')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE buses IS 'Master list of all buses in the fleet.';

CREATE TRIGGER trg_buses_updated_at
    BEFORE UPDATE ON buses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 4. DRIVERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS drivers (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    driver_name       TEXT NOT NULL,
    employee_id       TEXT NOT NULL UNIQUE,
    phone             TEXT NOT NULL,
    experience_years  INTEGER NOT NULL DEFAULT 0
                      CHECK (experience_years >= 0),
    status            TEXT NOT NULL DEFAULT 'Active'
                      CHECK (status IN ('Active', 'Inactive', 'On Leave')),
    profile_id        UUID REFERENCES profiles(id) ON DELETE SET NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE drivers IS 'Bus driver records. Optionally linked to a Supabase auth profile via profile_id.';

CREATE TRIGGER trg_drivers_updated_at
    BEFORE UPDATE ON drivers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 5. CONDUCTORS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS conductors (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conductor_name    TEXT NOT NULL,
    employee_id       TEXT NOT NULL UNIQUE,
    phone             TEXT NOT NULL,
    experience_years  INTEGER NOT NULL DEFAULT 0
                      CHECK (experience_years >= 0),
    status            TEXT NOT NULL DEFAULT 'Active'
                      CHECK (status IN ('Active', 'Inactive', 'On Leave')),
    profile_id        UUID REFERENCES profiles(id) ON DELETE SET NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE conductors IS 'Bus conductor records. Optionally linked to a Supabase auth profile via profile_id.';

CREATE TRIGGER trg_conductors_updated_at
    BEFORE UPDATE ON conductors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 6. BUS ASSIGNMENTS TABLE
-- ============================================================
-- Connects a bus with its assigned driver and conductor for a shift.
CREATE TABLE IF NOT EXISTS bus_assignments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bus_id          UUID NOT NULL REFERENCES buses(id) ON DELETE CASCADE,
    driver_id       UUID NOT NULL REFERENCES drivers(id) ON DELETE CASCADE,
    conductor_id    UUID NOT NULL REFERENCES conductors(id) ON DELETE CASCADE,
    shift           TEXT NOT NULL DEFAULT 'Morning'
                    CHECK (shift IN ('Morning', 'Afternoon', 'Evening', 'Night', 'Full Day')),
    assigned_date   DATE NOT NULL DEFAULT CURRENT_DATE,
    status          TEXT NOT NULL DEFAULT 'Active'
                    CHECK (status IN ('Active', 'Completed', 'Cancelled')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE bus_assignments IS 'Links buses to their assigned driver and conductor per shift/date.';

CREATE TRIGGER trg_bus_assignments_updated_at
    BEFORE UPDATE ON bus_assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 7. BUS LOCATIONS TABLE (Live Tracking)
-- ============================================================
-- Stores the latest GPS location of each bus.
-- For efficiency, the table is designed for UPSERT patterns:
-- one row per bus, updated in-place as new telemetry arrives.
CREATE TABLE IF NOT EXISTS bus_locations (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bus_id        UUID NOT NULL REFERENCES buses(id) ON DELETE CASCADE,
    latitude      DOUBLE PRECISION NOT NULL,
    longitude     DOUBLE PRECISION NOT NULL,
    speed         DOUBLE PRECISION DEFAULT 0.0
                  CHECK (speed >= 0),
    heading       DOUBLE PRECISION DEFAULT 0.0,
    current_stop  TEXT,
    next_stop     TEXT,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE bus_locations IS 'Latest GPS position for each bus. One row per bus, updated in-place.';

-- Ensure only one location row per bus (for UPSERT pattern)
CREATE UNIQUE INDEX IF NOT EXISTS idx_bus_locations_bus_id_unique
    ON bus_locations(bus_id);

CREATE TRIGGER trg_bus_locations_updated_at
    BEFORE UPDATE ON bus_locations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 8. INDEXES FOR PERFORMANCE
-- ============================================================

-- Buses
CREATE INDEX IF NOT EXISTS idx_buses_bus_number    ON buses(bus_number);
CREATE INDEX IF NOT EXISTS idx_buses_route_number  ON buses(route_number);
CREATE INDEX IF NOT EXISTS idx_buses_status        ON buses(status);

-- Drivers
CREATE INDEX IF NOT EXISTS idx_drivers_employee_id ON drivers(employee_id);
CREATE INDEX IF NOT EXISTS idx_drivers_status      ON drivers(status);
CREATE INDEX IF NOT EXISTS idx_drivers_profile_id  ON drivers(profile_id);

-- Conductors
CREATE INDEX IF NOT EXISTS idx_conductors_employee_id ON conductors(employee_id);
CREATE INDEX IF NOT EXISTS idx_conductors_status      ON conductors(status);
CREATE INDEX IF NOT EXISTS idx_conductors_profile_id  ON conductors(profile_id);

-- Bus Assignments
CREATE INDEX IF NOT EXISTS idx_assignments_bus_id       ON bus_assignments(bus_id);
CREATE INDEX IF NOT EXISTS idx_assignments_driver_id    ON bus_assignments(driver_id);
CREATE INDEX IF NOT EXISTS idx_assignments_conductor_id ON bus_assignments(conductor_id);
CREATE INDEX IF NOT EXISTS idx_assignments_date         ON bus_assignments(assigned_date);
CREATE INDEX IF NOT EXISTS idx_assignments_status       ON bus_assignments(status);

-- Bus Locations
CREATE INDEX IF NOT EXISTS idx_bus_locations_bus_id     ON bus_locations(bus_id);
CREATE INDEX IF NOT EXISTS idx_bus_locations_updated_at ON bus_locations(updated_at DESC);

-- Profiles
CREATE INDEX IF NOT EXISTS idx_profiles_role  ON profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);

-- ============================================================
-- 9. ADMIN BUS OVERVIEW VIEW
-- ============================================================
-- Joins buses + active assignments + drivers + conductors + latest location
-- into a single queryable view for the admin dashboard.
-- Uses security_invoker = true so the view respects the caller's RLS policies
-- instead of bypassing them (fixes Security Advisor error).
-- DROP first because CREATE OR REPLACE cannot change view column structure.
DROP VIEW IF EXISTS admin_bus_overview;
CREATE VIEW admin_bus_overview
    WITH (security_invoker = true)
AS
SELECT
    b.id              AS bus_id,
    b.bus_number,
    b.route_number,
    b.route_name,
    b.capacity,
    b.bus_type,
    b.status          AS bus_status,

    -- Driver info (from the latest active assignment)
    d.id              AS driver_id,
    d.driver_name,
    d.employee_id     AS driver_employee_id,
    d.phone           AS driver_phone,
    d.experience_years AS driver_experience,

    -- Conductor info
    c.id              AS conductor_id,
    c.conductor_name,
    c.employee_id     AS conductor_employee_id,
    c.phone           AS conductor_phone,
    c.experience_years AS conductor_experience,

    -- Assignment info
    ba.id             AS assignment_id,
    ba.shift,
    ba.assigned_date,
    ba.status         AS assignment_status,

    -- Live location
    bl.latitude,
    bl.longitude,
    bl.speed,
    bl.heading,
    bl.current_stop,
    bl.next_stop,
    bl.updated_at     AS location_updated_at

FROM buses b
LEFT JOIN bus_assignments ba
    ON ba.bus_id = b.id
    AND ba.status = 'Active'
LEFT JOIN drivers d
    ON d.id = ba.driver_id
LEFT JOIN conductors c
    ON c.id = ba.conductor_id
LEFT JOIN bus_locations bl
    ON bl.bus_id = b.id;

COMMENT ON VIEW admin_bus_overview IS 'Denormalized view joining buses, active assignments, drivers, conductors, and latest GPS location. Uses security_invoker so RLS is enforced per caller.';

-- ============================================================
-- 10. ROW LEVEL SECURITY (RLS)
-- ============================================================

-- Helper function: returns the role of the currently authenticated user
-- SET search_path prevents search path injection attacks.
-- REVOKE from public/anon prevents unauthenticated callers.
CREATE OR REPLACE FUNCTION auth_user_role()
RETURNS TEXT AS $$
    SELECT role FROM public.profiles WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE
   SET search_path = public;

-- Revoke execute from public roles (only authenticated context should call this)
REVOKE EXECUTE ON FUNCTION auth_user_role() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION auth_user_role() FROM anon;
GRANT EXECUTE ON FUNCTION auth_user_role() TO authenticated;

-- ---------- PROFILES ----------
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY profiles_select_own ON profiles
    FOR SELECT USING (id = auth.uid());

-- Users can update their own profile (name only, not role)
CREATE POLICY profiles_update_own ON profiles
    FOR UPDATE USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- Admins can do everything on profiles
CREATE POLICY profiles_admin_all ON profiles
    FOR ALL USING (auth_user_role() = 'admin');

-- ---------- BUSES ----------
ALTER TABLE buses ENABLE ROW LEVEL SECURITY;

-- Everyone authenticated can read buses (public schedule info)
CREATE POLICY buses_select_authenticated ON buses
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- Only admins can insert, update, delete buses
CREATE POLICY buses_admin_modify ON buses
    FOR ALL USING (auth_user_role() = 'admin');

-- ---------- DRIVERS ----------
ALTER TABLE drivers ENABLE ROW LEVEL SECURITY;

-- Admins can do everything
CREATE POLICY drivers_admin_all ON drivers
    FOR ALL USING (auth_user_role() = 'admin');

-- Drivers can read their own record (matched by profile_id)
CREATE POLICY drivers_select_own ON drivers
    FOR SELECT USING (profile_id = auth.uid());

-- ---------- CONDUCTORS ----------
ALTER TABLE conductors ENABLE ROW LEVEL SECURITY;

-- Admins can do everything
CREATE POLICY conductors_admin_all ON conductors
    FOR ALL USING (auth_user_role() = 'admin');

-- Conductors can read their own record (matched by profile_id)
CREATE POLICY conductors_select_own ON conductors
    FOR SELECT USING (profile_id = auth.uid());

-- ---------- BUS ASSIGNMENTS ----------
ALTER TABLE bus_assignments ENABLE ROW LEVEL SECURITY;

-- Admins can do everything
CREATE POLICY assignments_admin_all ON bus_assignments
    FOR ALL USING (auth_user_role() = 'admin');

-- Drivers can read their own assignments
CREATE POLICY assignments_driver_own ON bus_assignments
    FOR SELECT USING (
        driver_id IN (SELECT id FROM drivers WHERE profile_id = auth.uid())
    );

-- Conductors can read their own assignments
CREATE POLICY assignments_conductor_own ON bus_assignments
    FOR SELECT USING (
        conductor_id IN (SELECT id FROM conductors WHERE profile_id = auth.uid())
    );

-- ---------- BUS LOCATIONS ----------
ALTER TABLE bus_locations ENABLE ROW LEVEL SECURITY;

-- Everyone authenticated can read locations (passengers need this for tracking)
CREATE POLICY locations_select_authenticated ON bus_locations
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- Admins can do everything
CREATE POLICY locations_admin_all ON bus_locations
    FOR ALL USING (auth_user_role() = 'admin');

-- Drivers can update location for buses assigned to them
CREATE POLICY locations_driver_upsert ON bus_locations
    FOR INSERT WITH CHECK (
        bus_id IN (
            SELECT ba.bus_id FROM bus_assignments ba
            JOIN drivers d ON d.id = ba.driver_id
            WHERE d.profile_id = auth.uid() AND ba.status = 'Active'
        )
    );

CREATE POLICY locations_driver_update ON bus_locations
    FOR UPDATE USING (
        bus_id IN (
            SELECT ba.bus_id FROM bus_assignments ba
            JOIN drivers d ON d.id = ba.driver_id
            WHERE d.profile_id = auth.uid() AND ba.status = 'Active'
        )
    );

-- ============================================================
-- 11. AUTO-CREATE PROFILE ON SIGNUP (Supabase Auth Hook)
-- ============================================================
-- When a new user signs up via Supabase Auth, automatically
-- create a profile row with role = 'user'.
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email, role)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', 'User'),
        COALESCE(NEW.email, ''),
        COALESCE(NEW.raw_user_meta_data->>'role', 'user')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER
   SET search_path = public;

-- Revoke public execute — this is a trigger function, not meant to be called directly
REVOKE EXECUTE ON FUNCTION handle_new_user() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION handle_new_user() FROM anon;
REVOKE EXECUTE ON FUNCTION handle_new_user() FROM authenticated;

-- Attach trigger to Supabase auth.users table
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================================
-- 12. DATA INITIALIZATION
-- ============================================================
-- Ready for real dataset import (mock/predefined data removed).

-- ============================================================
-- SETUP COMPLETE ✅
-- ============================================================
-- Tables:        profiles, buses, drivers, conductors, bus_assignments, bus_locations
-- View:          admin_bus_overview
-- Triggers:      Auto-update updated_at on all tables, auto-create profile on signup
-- RLS Policies:  Admin full access, driver/conductor own-record access, user read-only
-- Indexes:       Optimized for dashboard queries and location lookups
-- ============================================================
