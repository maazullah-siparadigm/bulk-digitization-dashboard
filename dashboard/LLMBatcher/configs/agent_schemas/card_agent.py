from typing import List

from pydantic import BaseModel, Field


class CardField(BaseModel):
    key: str = Field(..., description="Label of the visible field (e.g., 'Name', 'DOB', 'License No.')")
    value: str = Field(..., description="The corresponding value as printed on the card")


class CardExtractionResult(BaseModel):
    extracted_fields: List[CardField] = Field(
        default_factory=list,
        description="All visible key-value fields on the card (name, ID number, date of birth, expiry date, etc.)",
    )

    description: str = Field(
        ...,
        min_length=1,
        description="Comprehensive detailed description of the card's layout and visible content",
    )

    summary: str = Field(
        ...,
        description="Highly concise summary (maximum 50 words) capturing essential card content without information loss",
    )


card_extraction_schema = CardExtractionResult.model_json_schema()
