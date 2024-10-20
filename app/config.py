from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_driver: str
    database_host: str
    database_name: str
    database_password: str
    database_port: int
    database_user: str
    offers_service_base_url: str
    offers_service_fetch_period_seconds: int
    offers_service_refresh_token: str

    model_config = SettingsConfigDict(env_file=".env")
