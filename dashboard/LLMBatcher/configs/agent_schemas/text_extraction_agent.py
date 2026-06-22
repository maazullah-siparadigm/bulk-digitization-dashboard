from typing import List, Literal, Union
from pydantic import BaseModel, Field, conlist
from typing import List, Literal, Annotated
from pydantic import BaseModel, Field, field_validator

# Pydantic Schemas for Text Agent


# -------------------------
# Base
# -------------------------

ElementId = Annotated[str, Field()]
RelationId = Annotated[str, Field()]


class BaseElement(BaseModel):
    id: ElementId
    type: str


# -------------------------
# Element Types
# -------------------------

class TextElement(BaseElement):
    type: Literal["text"] = Field(description="Element type identifier. Always 'text' for textual content like paragraphs, headings, sentences")
    content: str = Field(..., description="The actual text content of this element")
    level: int = Field(ge=0, description="Hierarchical level of the text (0=main heading, 1=subheading, 2=paragraph, etc.)" , default=0)


class KeyValueElement(BaseElement):
    type: Literal["key_values"] = Field(description="Element type identifier. Always 'key_values' for structured key-value pairs like forms or metadata")
    key: str = Field(..., description="The key/label part of the key-value pair (e.g., 'Name', 'Date', 'Amount')")
    value: str = Field(..., description="The corresponding value for the key (e.g., 'John Smith', '2023-10-15', '$100.00')")


class CheckboxElement(BaseElement):
    type: Literal["checkbox"] = Field(description="Element type identifier. Always 'checkbox' for checkboxes and radio buttons")
    key: str = Field(..., description="Label or description associated with the checkbox/radio button")
    flag: Literal[0, 1] = Field(description="Selection state: 1 if checked/selected, 0 if unchecked/unselected")
    @field_validator("flag", mode="before")
    @classmethod
    def map_unknown_to_other(cls, v):
        allowed = {0,1}
        if isinstance(v, int) and v not in allowed:
            return 0  # Default to unchecked if invalid flag value
        return v

class RadioElement(BaseElement):
    type: Literal["radio_button"] = Field(description="Element type identifier. Always 'radio_button' for radio buttons")
    key: str = Field(..., description="Label or description associated with the radio button")
    flag: Literal[0, 1] = Field(description="Selection state: 1 if checked/selected, 0 if unchecked/unselected")
    @field_validator("flag", mode="before")
    @classmethod
    def map_unknown_to_other(cls, v):
        allowed = {0,1}
        if isinstance(v, int) and v not in allowed:
            return 0  # Default to unchecked if invalid flag value
        return v

class SignatureElement(BaseElement):
    type: Literal["signature"] = Field(description="Element type identifier. Always 'signature' for signature areas or signature fields")
    key: str = Field(..., description="Label or description associated with the signature field (e.g., 'Patient Signature', 'Doctor Signature', 'Authorized Signature')")
    flag: Literal[0, 1] = Field(description="Signature state: 1 if signed (contains actual signature content), 0 if unsigned (blank signature field)")
    @field_validator("flag", mode="before")
    @classmethod
    def map_unknown_to_other(cls, v):
        allowed = {0,1}
        if isinstance(v, int) and v not in allowed:
            return 0  # Default to unsigned if invalid flag value
        return v

class OrderedListElement(BaseElement):
    type: Literal["ordered"] = Field(description="Element type identifier. Always 'ordered' for numbered/ordered lists")
    items: List[str] = Field(..., description="List of text items in their sequential order")


class UnorderedListElement(BaseElement):
    type: Literal["unordered"] = Field(description="Element type identifier. Always 'unordered' for bulleted/unordered lists")
    items: List[str] = Field(..., description="List of text items without specific ordering")


# -------------------------
# Discriminated Union
# -------------------------

Element = Annotated[
    Union[
        TextElement,
        KeyValueElement,
        CheckboxElement,
        OrderedListElement,
        UnorderedListElement,
        RadioElement,
        SignatureElement
    ],
    Field(discriminator="type"),
]


# -------------------------
# Relationships
# -------------------------

class Relationship(BaseModel):
    id: RelationId
    parent: ElementId
    child: ElementId


# -------------------------
# Root Output Schema
# -------------------------

class ExtractionResult(BaseModel):
    summary: str = Field(
        ...,
        description="Highly concise summary (maximum 50 words) capturing essential textual content without information loss"
    )
    elements: List[Element]
    relationships: List[Relationship] = Field(default = [], description="List of relationships describing visual, structural, and/or semantic hierarchy between elements")





text_extraction_schema= ExtractionResult.model_json_schema()