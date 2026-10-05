from enum import Enum
from typing import Annotated, List, Literal, Optional, TypeAlias, Union
from LLMBatcher.common.myenums import ElementType,ImageContentType,MarginaliaType



from pydantic import BaseModel, Field, field_validator

class BaseElement(BaseModel):
    id: str = Field()
    type: ElementType
    parent_id: Optional[str] = Field(
        default=None,
        description=(
            "ID of the element this one is nested under (visual, structural, or "
            "semantic parent). Omit or set null for top-level elements with no "
            "parent in this crop."
        ),
    )


class TextElement(BaseElement):
    type: Literal[ElementType.TEXT] = Field(
        default=ElementType.TEXT,
        description="Element type identifier. Always 'text' for textual content in marginalia",
    )
    content: str = Field(
        ...,
        description="The actual text content found in the marginalia",
    )


class KeyValueElement(BaseElement):
    type: Literal[ElementType.KEY_VALUES] = Field(
        default=ElementType.KEY_VALUES,
        description="Element type identifier. Always 'key_values' for structured pairs in marginalia",
    )
    key: str = Field(
        ...,
        description="The key/label part (e.g., 'Page', 'Date', 'Document ID')",
    )
    value: Union[str, List[str]] = Field(
        ...,
        description="The corresponding value (e.g., '1 of 5', '2023-10-15', 'DOC-123'). Use a list only when the same key legitimately has multiple distinct values; otherwise use a single string.",
    )


class CheckboxElement(BaseElement):
    type: Literal[ElementType.CHECKBOX] = Field(
        default=ElementType.CHECKBOX,
        description="Element type identifier. Always 'checkbox' for checkbox elements in marginalia",
    )
    key: str = Field(
        ...,
        description="Label or description associated with the checkbox",
    )
    flag: Literal[0, 1] = Field(
        description="Selection state: 1 if checked, 0 if unchecked",
    )

    @field_validator("flag", mode="before")
    @classmethod
    def map_unknown_to_other(cls, v):
        if isinstance(v, int) and v not in {0, 1}:
            return 0
        return v


class OrderedListElement(BaseElement):
    type: Literal[ElementType.ORDERED] = Field(
        default=ElementType.ORDERED,
        description="Element type identifier. Always 'ordered' for numbered lists in marginalia",
    )
    items: List[str] = Field(
        ...,
        description="List items in their sequential order",
    )


class UnorderedListElement(BaseElement):
    type: Literal[ElementType.UNORDERED] = Field(
        default=ElementType.UNORDERED,
        description="Element type identifier. Always 'unordered' for bulleted lists in marginalia",
    )
    items: List[str] = Field(
        ...,
        description="List items without specific ordering",
    )


class RadioElement(BaseElement):
    type: Literal[ElementType.RADIO_BUTTON] = Field(
        default=ElementType.RADIO_BUTTON,
        description="Element type identifier. Always 'radio_button' for radio buttons",
    )
    key: str = Field(
        ...,
        description="Label or description associated with the radio button",
    )
    flag: Literal[0, 1] = Field(
        description="Selection state: 1 if checked/selected, 0 if unchecked/unselected",
    )

    @field_validator("flag", mode="before")
    @classmethod
    def map_unknown_to_other(cls, v):
        if isinstance(v, int) and v not in {0, 1}:
            return 0
        return v


class ImageTypeElement(BaseElement):
    type: Literal[ElementType.IMAGE] = Field(
        default=ElementType.IMAGE,
        description="Element type identifier. Always 'image' for image classification",
    )

    content: ImageContentType = Field(
        default=ImageContentType.OTHER,
        description="Type of image found in marginalia. Use one of: 'chart', 'figure', 'logo', 'infographic', 'map', or 'other'",
    )

    description: str = Field(
        ...,
        description="Detailed description of what is shown in the image",
    )

    @field_validator("content", mode="before")
    @classmethod
    def map_unknown_to_other(cls, v):
        if isinstance(v, str):
            try:
                return ImageContentType(v)
            except ValueError:
                return ImageContentType.OTHER
        return v


Element: TypeAlias = Annotated[
    Union[
        TextElement,
        KeyValueElement,
        CheckboxElement,
        RadioElement,
        OrderedListElement,
        UnorderedListElement,
        ImageTypeElement,
    ],
    Field(discriminator="type"),
]


class MarginaliaExtractionResult(BaseModel):
    summary: str = Field(
        ...,
        description="Highly concise summary (maximum 50 words) capturing essential marginalia content without information loss",
    )

    marginalia_type: MarginaliaType = Field(
        ...,
        description="Classification of marginalia position. Use 'header' for content at the top of the page or 'footer' for content at the bottom of the page",
    )

    elements: List[Element] = Field(
        ...,
        description="List of all extracted elements found in the marginalia",
    )

    @field_validator("marginalia_type", mode="before")
    @classmethod
    def map_unknown_to_other(cls, v):
        if isinstance(v, str):
            try:
                return MarginaliaType(v)
            except ValueError:
                return MarginaliaType.HEADER
        return v


marginalia_extraction_schema = MarginaliaExtractionResult.model_json_schema()
