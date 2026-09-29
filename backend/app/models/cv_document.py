from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class CVDocumentLake(SQLModel, table=True):
    __tablename__ = "cv_document_lake"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    original_filename: str = Field(
        description="Oryginalna nazwa pliku przekazana przez użytkownika"
    )
    storage_path: str = Field(
        description="Fizyczna ścieżka do pliku na dysku/wolumenie serwera"
    )
    file_size_bytes: int = Field(description="Rozmiar pliku w bajtach")
    mime_type: str = Field(default="application/pdf", description="Typ MIME pliku")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Znacznik czasu zapisania pliku w Data Lake",
    )
