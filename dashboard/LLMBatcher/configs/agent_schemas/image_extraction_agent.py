from enum import Enum
from typing import List, Literal, Union
from pydantic import BaseModel, Field, field_validator
from LLMBatcher.common.myenums import ImageType


class ImageExtractionResult(BaseModel):
    image_type: ImageType = Field(
        default=ImageType.OTHER,
        description=(
            "Type of image content. Use one of: "
            "'chart' (graphs, plots, diagrams), "
            "'figure' (illustrations, drawings), "
            "'logo' (company logos, brand marks), "
            "'infographic' (data visualizations), "
            "'map' (geographical maps), "
            "'barcode' (1D barcodes), "
            "'qr_code' (QR codes / other 2D matrix codes), "
            "or 'other' (any other visual content)"
        ),
    )

    description: str = Field(
        ...,
        min_length=1,
        description="Comprehensive detailed description of all visible visual content",
    )

    summary: str = Field(
        ...,
        description="Highly concise summary (maximum 50 words) capturing essential visual content without information loss",
    )

    @field_validator("image_type", mode="before")
    @classmethod
    def map_unknown_to_other(cls, v):
        if isinstance(v, str):
            try:
                return ImageType(v)
            except ValueError:
                return ImageType.OTHER
        return v


image_extraction_agent_schema = ImageExtractionResult.model_json_schema()
