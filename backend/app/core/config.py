from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    database_url: str
    openai_api_key: str
    resend_api_key: str
    from_email: str = "jobs@hnjobs.dev"
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    admin_api_key: str = "changeme"

    model_config = {"env_file": ".env"}


settings = Settings()
