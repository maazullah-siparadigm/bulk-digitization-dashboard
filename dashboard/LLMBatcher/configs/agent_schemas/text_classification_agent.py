from typing import Annotated, List, Literal, Union

from pydantic import BaseModel, Field, field_validator


class TextClassification(BaseModel):
    has_structured_content: bool = Field(
        description=(
            "True if the crop contains ANY key-value pairs, checkboxes, radio buttons, "
            "signature fields, ordered lists, or unordered lists. False if the crop is "
            "pure prose - paragraphs, sentences, or headings only, with no such elements."
        )
    )


text_classification_schema = TextClassification.model_json_schema()
