from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


from LLMBatcher.common.myenums import CodeType

class ScanCodeExtractionResult(BaseModel):
    code_type: CodeType = Field(
        default=CodeType.OTHER,
        description=(
            "Type of scan code. Use one of: "
            "'barcode' (1D barcodes), "
            "'qr_code' (QR codes / other 2D matrix codes), "
            "or 'other' (any other tracking code)"
        ),
    )

    decoded_value: Optional[str] = Field(
        default=None,
        description=(
            "Human-readable text printed near or under the code (e.g. a barcode's printed "
            "digit string), if visible. This is NOT actual barcode/QR decoding — only "
            "printed text the model can read. Null if no such text is visible."
        ),
    )

    description: str = Field(
        ...,
        min_length=1,
        description="Comprehensive detailed description of the code's visual appearance and surrounding context",
    )

    summary: str = Field(
        ...,
        description="Highly concise summary (maximum 50 words) capturing essential scan-code content without information loss",
    )

    @field_validator("code_type", mode="before")
    @classmethod
    def map_unknown_to_other(cls, v):
        if isinstance(v, str):
            try:
                return CodeType(v)
            except ValueError:
                return CodeType.OTHER
        return v


scan_code_extraction_schema = ScanCodeExtractionResult.model_json_schema()
