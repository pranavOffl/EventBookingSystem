from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: int
    
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_EXPIRY: int = 3600
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    ACCESS_TOKEN_EXPIRY: int = 30 # 30 minutes
    REFRESH_TOKEN_EXPIRY: int = 60 * 24 * 7 # 7 days
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    @property
    def async_db_uri(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def sync_db_uri(self) -> str:
        return f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()
