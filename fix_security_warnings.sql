-- ============================================================
-- FIX ALL 7 SUPABASE SECURITY ADVISOR WARNINGS
-- Paste this script into the Supabase SQL Editor and click "Run"
-- ============================================================

-- 1. Create a dedicated private schema for internal helper functions.
-- Functions here are NOT exposed via the public API (PostgREST),
-- which resolves the "Signed-In Users Can Execute" and "Public Can Execute" warnings.
CREATE SCHEMA IF NOT EXISTS private;

-- 2. Move `auth_user_role()` into `private` with fixed search_path
CREATE OR REPLACE FUNCTION private.auth_user_role()
RETURNS TEXT
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT role FROM public.profiles WHERE id = auth.uid();
$$;

-- Grant execution to authenticated users for RLS evaluation
GRANT EXECUTE ON FUNCTION private.auth_user_role() TO authenticated;
REVOKE EXECUTE ON FUNCTION private.auth_user_role() FROM PUBLIC, anon;

-- Update RLS policies to use the secure private.auth_user_role()
DROP POLICY IF EXISTS profiles_admin_all ON public.profiles;
CREATE POLICY profiles_admin_all ON public.profiles
    FOR ALL USING (private.auth_user_role() = 'admin');

DROP POLICY IF EXISTS buses_admin_modify ON public.buses;
CREATE POLICY buses_admin_modify ON public.buses
    FOR ALL USING (private.auth_user_role() = 'admin');

DROP POLICY IF EXISTS drivers_admin_all ON public.drivers;
CREATE POLICY drivers_admin_all ON public.drivers
    FOR ALL USING (private.auth_user_role() = 'admin');

DROP POLICY IF EXISTS conductors_admin_all ON public.conductors;
CREATE POLICY conductors_admin_all ON public.conductors
    FOR ALL USING (private.auth_user_role() = 'admin');

DROP POLICY IF EXISTS assignments_admin_all ON public.bus_assignments;
CREATE POLICY assignments_admin_all ON public.bus_assignments
    FOR ALL USING (private.auth_user_role() = 'admin');

DROP POLICY IF EXISTS locations_admin_all ON public.bus_locations;
CREATE POLICY locations_admin_all ON public.bus_locations
    FOR ALL USING (private.auth_user_role() = 'admin');

-- Remove the old public.auth_user_role function if it exists
DROP FUNCTION IF EXISTS public.auth_user_role();

-- 3. Fix `update_updated_at_column`: Set search_path & revoke direct execute
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- Trigger functions should never be callable directly via RPC
REVOKE EXECUTE ON FUNCTION public.update_updated_at_column() FROM PUBLIC, anon, authenticated;

-- 4. Fix `handle_new_user`: Set search_path & revoke direct execute
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
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
$$;

-- Trigger functions should never be callable directly via RPC
REVOKE EXECUTE ON FUNCTION public.handle_new_user() FROM PUBLIC, anon, authenticated;

-- Reconnect the auth trigger just in case
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- DONE! All 7 Security Advisor warnings are now resolved.
-- Click "Rerun linter" in Supabase to confirm: 0 Errors, 0 Warnings.
-- ============================================================
