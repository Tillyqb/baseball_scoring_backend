from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "mysql+pymysql://baseball:baseball@localhost:3306/baseball"
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
