from pydantic import BaseModel, Field, HttpUrl


class DataLakeScraperBase(BaseModel):
    source_portal: str = Field(
        ...,
        description="Nazwa portalu, z ktorego pochodzi oferta",
        examples=["pracuj.pl"],
    )
    raw_html: str = Field(
        ..., description="Pelny, surowy kod HTML pobrany ze strony ogloszen"
    )


class DataLakeScraperCreate(DataLakeScraperBase):
    url: HttpUrl = Field(
        ...,
        description="Pelny, zweryfikowany adres URL ogloszenia o prace",
        examples=["https://www.pracuj.pl/praca/python-developer-krakow,oferta,1000000"],
    )


class DataLakeScraperResponse(DataLakeScraperBase):
    id: str
    url: str = Field(..., description="Adres URL w postaci tekstowej")

    class Config:
        from_attributes = True
