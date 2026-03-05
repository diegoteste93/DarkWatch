from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "DarkWatch"
    database_url: str = "postgresql+psycopg2://darkwatch:darkwatch@postgres:5432/darkwatch"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    leakradar_api_key: str = ""
    leakradar_base_url: str = "https://api.leakradar.io"

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "alerts@darkwatch.local"
    smtp_starttls: bool = True


settings = Settings()
