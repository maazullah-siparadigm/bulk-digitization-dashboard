from enum import Enum
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class HandWrittenSignatureElement(BaseModel):
    type: Literal["hand_written_signature"] = Field(description="Element type identifier. Always 'hand_written_signature' for pen/ink signatures written by hand")
    is_signed: bool = Field(..., description="True if the handwritten signature area actually contains a signature, False if the area is blank/unsigned")


class ESignatureElement(BaseModel):
    type: Literal["e_signature"] = Field(description="Element type identifier. Always 'e_signature' for digitally typed, drawn, or inserted signatures (e.g. DocuSign-style signature blocks, typed names in a signature/cursive font, image-pasted signatures)")
    signed_by: Optional[str] = Field(default=None, description="Name of the signer as shown by the e-signature, if legible, otherwise null")


class StampElement(BaseModel):
    type: Literal["stamp"] = Field(description="Element type identifier. Always 'stamp' for notary/company stamps and official seals of authenticity")
    stamp_text: Optional[str] = Field(default=None, description="Legible text within the stamp/seal (issuer or organization name, registration number, date, etc.), otherwise null")


class OtherElement(BaseModel):
    type: Literal["other"] = Field(description="Element type identifier. Always 'other' for any attestation mark that is not a signature or stamp/seal")
    content: str = Field(..., description="Free-form description of the attestation mark")


# -------------------------
# Discriminated Union
# -------------------------

AttestationElement = Annotated[
    Union[
        HandWrittenSignatureElement,
        ESignatureElement,
        StampElement,
        OtherElement,
    ],
    Field(discriminator="type"),
]


# -------------------------
# Root Output Schema
# -------------------------

class AttestationExtractionResult(BaseModel):
    summary: str = Field(
        ...,
        description="Highly concise summary (maximum 50 words) capturing essential attestation content without information loss"
    )
    elements: List[AttestationElement]


attestation_extraction_schema = AttestationExtractionResult.model_json_schema()
