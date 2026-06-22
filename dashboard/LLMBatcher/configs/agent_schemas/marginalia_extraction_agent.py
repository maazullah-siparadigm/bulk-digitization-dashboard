from typing import List, Literal, Union, TypeAlias
from pydantic import BaseModel, Field, conlist
from typing import List, Literal, Annotated
from pydantic import BaseModel, Field, field_validator



# =====================================================
# Base
# =====================================================
class BaseElement(BaseModel):

    id: str = Field()
    type: str


# =====================================================
# TEXT ELEMENTS
# =====================================================

class TextElement(BaseElement):
    type: Literal["text"] = Field(description="Element type identifier. Always 'text' for textual content in marginalia")
    content: str = Field(..., description="The actual text content found in the marginalia")
    level: int = Field(ge=0, description="Hierarchical level of the text (0=main, 1=secondary, etc.)" , default=0)


class KeyValueElement(BaseElement):
    type: Literal["key_values"] = Field(description="Element type identifier. Always 'key_values' for structured pairs in marginalia")
    key: str = Field(..., description="The key/label part (e.g., 'Page', 'Date', 'Document ID')")
    value: str = Field(..., description="The corresponding value (e.g., '1 of 5', '2023-10-15', 'DOC-123')")


class CheckboxElement(BaseElement):
    type: Literal["checkbox"] = Field(description="Element type identifier. Always 'checkbox' for checkbox elements in marginalia")
    key: str = Field(..., description="Label or description associated with the checkbox")
    flag: Literal[0, 1] = Field(description="Selection state: 1 if checked, 0 if unchecked")
    @field_validator("flag", mode="before")
    @classmethod
    def map_unknown_to_other(cls, v):
        allowed = {0,1}
        if isinstance(v, int) and v not in allowed:
            return 0  # Default to unchecked if invalid flag value
        return v

class OrderedListElement(BaseElement):
    type: Literal["ordered"] = Field(description="Element type identifier. Always 'ordered' for numbered lists in marginalia")
    items: List[str] = Field(..., description="List items in their sequential order")


class UnorderedListElement(BaseElement):
    type: Literal["unordered"] = Field(description="Element type identifier. Always 'unordered' for bulleted lists in marginalia")
    items: List[str] = Field(..., description="List items without specific ordering")



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



# =====================================================
# IMAGE ELEMENTS
# =====================================================

class ImageTypeElement(BaseElement):
    type: Literal["image", "logo", "image_type"] = Field(description="Element type identifier. Always 'image' for image classification")
    content: Literal["chart", "figure", "logo", "infographic", "map", "other"] = Field(description="Type of image found in marginalia. Use one of: 'chart', 'figure', 'logo', 'infographic', 'map', or 'other'" , default="other")
    description:str = Field(description="Detailed description of what is shown in the image", default="")
    @field_validator("content", mode="before")
    @classmethod
    def map_unknown_to_other(cls, v):
        allowed = {"chart", "figure", "logo", "infographic", "map", "other"}
        if isinstance(v, str) and v not in allowed:
            return "other"
        return v

# class ImageDescriptionElement(BaseElement):
#     type: Literal["image_description"] = Field(description="Element type identifier. Always 'image_description' for image content description")
#     content: str = Field(..., description="Detailed description of what is shown in the image")


# =====================================================
# Pylance-safe discriminated union (TypeAlias)
# =====================================================

Element: TypeAlias = Annotated[
    Union[
        TextElement,
        KeyValueElement,
        CheckboxElement,
        RadioElement,
        OrderedListElement,
        UnorderedListElement,
        ImageTypeElement,
        # ImageDescriptionElement,
    ],
    Field(discriminator="type"),
]


# =====================================================
# Relationships
# =====================================================

class Relationship(BaseModel):
    id: str = Field()
    parent: str = Field()
    child: str = Field()


# =====================================================
# Root Schema
# =====================================================

class MarginaliaExtractionResult(BaseModel):
    summary: str = Field(
        ...,
        description="Highly concise summary (maximum 50 words) capturing essential marginalia content without information loss"
    )
    marginalia_type: Literal["header", "footer"] = Field(..., description="Classification of marginalia position. Use 'header' for content at the top of the page or 'footer' for content at the bottom of the page")
    elements: List[Element] = Field(..., description="List of all extracted elements found in the marginalia")
    relationships: List[Relationship] = Field(default=[], description="Hierarchical relationships between elements (parent-child connections)")
    @field_validator("marginalia_type", mode="before")
    @classmethod
    def map_unknown_to_other(cls, v):
        allowed = {"header", "footer"}
        if isinstance(v, str) and v not in allowed:
            return "header"  # Default to header if invalid marginalia type
        return v    
    

marginalia_extraction_schema=MarginaliaExtractionResult.model_json_schema()