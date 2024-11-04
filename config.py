from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    secret_key: str
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 4320

    class Config:
        env_file = ".env"

settings = Settings()