from core.config import settings
from core.database.database_connector import DatabaseConnector

db = DatabaseConnector(url=settings.db_url, echo=settings.db_echo)
