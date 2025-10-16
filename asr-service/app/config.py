from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    HOST: str
    ASR_PORT: int
    ASR_MODEL_NAME: str
    LOG_LEVEL: str
    LOG_DIR: str
    LOG_FILE_INFO: str
    LOG_FILE_ERROR: str
    MAX_DUARTION: int
    REQUEST_TIMEOUT: float

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
