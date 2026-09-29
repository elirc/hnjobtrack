from supabase import create_client, Client
from app.core.config import settings

supabase_admin: Client = create_client(
    settings.supabase_url, settings.supabase_service_role_key
)

supabase_public: Client = create_client(
    settings.supabase_url, settings.supabase_anon_key
)


def get_supabase_admin() -> Client:
    return supabase_admin


def get_supabase_public() -> Client:
    return supabase_public
