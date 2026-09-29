import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class DataLakeScrapper(SQLModel, table=True):
    __tablename__ = "datalake_scraper"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False
    )
    url: str = Field(index=True)
    source_portal: str
    raw_html: str
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
