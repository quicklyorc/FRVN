from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = Field(default="{{PROJECT_NAME}}")
    env: str = Field(default="dev")
    log_level: str = Field(default="info")
    backend_port: int = Field(default=8000)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()



