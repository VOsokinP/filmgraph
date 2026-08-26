from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    jwt_secret_key : str
    jwt_algorithm : str = "HS256"
    jwt_expire_minutes : int = 60*24*7
    session_secret_key : str
    cookie_secure : bool = False
    recaptcha_enabled : bool = False
    recaptcha_secret_key : str = ""
    recaptcha_min_score : float = 0.5
    recaptcha_timeout_seconds : float = 3.0
    log_level : str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env", env_prefix="")

settings = Settings()