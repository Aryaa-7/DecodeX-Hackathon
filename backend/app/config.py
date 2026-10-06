import os
from dataclasses import dataclass
@dataclass
class Settings:
    mongodb_uri: str = os.getenv("MONGODB_URI","mongodb://localhost:27017")
    mongodb_database: str = os.getenv("MONGODB_DATABASE","atms")
    solver_time_limit_s: int = int(os.getenv("SOLVER_TIME_LIMIT_S","30"))
    solver_workers: int = int(os.getenv("SOLVER_WORKERS","8"))
    notification_reminder_minutes: int = int(os.getenv("NOTIFICATION_REMINDER_MINUTES","10"))
settings = Settings()
