from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mocktail Studio"
    app_env: str = "development"
    database_url: str = "sqlite:///./mocktail_studio.db"
    secret_key: str = "change-me-in-production"
    featured_recipe_min_reviews: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
