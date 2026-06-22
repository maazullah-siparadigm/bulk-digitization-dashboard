from typing import List, Literal, Union
from pydantic import BaseModel, Field, conlist
from typing import List, Literal, Annotated
from pydantic import BaseModel, Field
from LLMBatcher.common.myenums import SectionTypes



Box2D = Annotated[
    List[int],
    Field(min_length=4, max_length=4, description="Bounding box [y_min, x_min, y_max, x_max]")
]

class Section(BaseModel):
    box_2d: Box2D = Field(
        ...,
        description="Bounding box coordinates [y_min, x_min, y_max, x_max] in normalized scale (0-1000)"
    )

    label: str = Field(
        default="Section",
        description="Short name, max 4 words (e.g., 'Introduction', 'Figure 1', 'Header', 'Footer')"
    )

    type: SectionTypes = Field(
        default=SectionTypes.text,
        description=(
            "Section content type. Must be one of: "
            "'text' (paragraphs, titles, lists, key-value pairs), "
            "'image' (figures, photos, diagrams, charts), "
            "'marginalia' (headers, footers, page numbers, margin notes), "
            "'table' (structured data with rows and columns)"
        )
    )

class DocumentLayout(BaseModel):
    sections: List[Section]



bbox_agent_schema = DocumentLayout.model_json_schema()
