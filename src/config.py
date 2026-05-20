from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    todoist_client_secret: str
    supabase_url: str
    supabase_service_role_key: str
    database_url: str
    redis_url: str = "redis://localhost:6379"
    litellm_base_url: str = "http://localhost:4000"
    litellm_master_key: str = "sk-litellm-local-dev"
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""


settings = Settings()
