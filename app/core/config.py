from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    APP_NAME: str = "PackSure AI"
    DATABASE_URL: str = "sqlite:///./packsure.db"
    MAX_UPLOAD_MB: int = 10
    TESSERACT_CMD: str = ""
    CORS_ORIGINS: str = ""
    UPLOAD_DIR: str = "uploads"
    REPORT_DIR: str = "reports"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    @property
    def cors_origins(self):
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]
        
    @property
    def database_url(self) -> str:
        """Resolve relative SQLite paths against the project, not the shell CWD."""
        prefix = "sqlite:///"
        if not self.DATABASE_URL.startswith(prefix):
            return self.DATABASE_URL
        filename = self.DATABASE_URL[len(prefix):]
        if not filename or filename == "memory:" or filename.startswith("file:"):
            return self.DATABASE_URL
        return f"{prefix}{self.project_path(filename).as_posix()}"
        
    @property
    def upload_dir(self) -> Path:
        return self.project_path(self.UPLOAD_DIR)
        
    @property
    def report_dir(self) -> Path:
        return self.project_path(self.REPORT_DIR)
        
    @property
    def frontend_dir(self) -> Path:
        return PROJECT_ROOT / "frontend"
        
    def project_path(self, value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else PROJECT_ROOT / path

settings = Settings()