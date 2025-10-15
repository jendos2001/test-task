from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    HOST: str
    PORT: int
    WS_PATH: str
    MODEL_NAME: str
    CHUNK_MS: int
    GENERATION_TIMEOUT: int
    SAMPLE_RATE: int
    LOG_LEVEL: str
    LOG_DIR: str
    LOG_FILE_INFO: str
    LOG_FILE_ERROR: str
    RECIEVE_TIMEOUT: float

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"