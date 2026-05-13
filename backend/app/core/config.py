import os
from pydantic_settings import BaseSettings

_env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/eim_agent_qa"
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/api/v1"
    DASHSCOPE_MODEL_VL: str = "qwen-vl-max"
    DASHSCOPE_MODEL_TEXT: str = "qwen-max"
    DASHSCOPE_MODEL_EMBEDDING: str = "text-embedding-v3"

    model_config = {
        "env_file": _env_file,
        "env_file_encoding": "utf-8",
    }


settings = Settings()
