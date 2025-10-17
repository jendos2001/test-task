from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    HOST: str
    GATEWAY_PORT: int
    ASR_PORT: int
    TTS_WS_URL: str
    LOG_DIR: str
    LOG_FILE_INFO: str
    LOG_FILE_ERROR: str
    REQUEST_TIMEOUT: int
    LOG_LEVEL: str


    class Config:
        env_file = ".env"