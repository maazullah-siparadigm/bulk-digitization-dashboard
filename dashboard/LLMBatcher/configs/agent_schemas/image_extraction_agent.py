from typing import List, Literal, Union
from pydantic import BaseModel, Field, conlist
from typing import List, Literal, Annotated
from pydantic import BaseModel, Field, field_validator


class ImageExtractionResult(BaseModel):

    image_type: Literal["chart", "figure", "logo", "infographic", "map", "other"] = Field(default="other", description="Type of image content. Use one of: 'chart' (graphs, plots, diagrams), 'figure' (illustrations, drawings), 'logo' (company logos, brand marks), 'infographic' (data visualizations), 'map' (geographical maps), or 'other' (any other visual content)")

    description: str = Field(
        ...,
        min_length=1,
        description="Comprehensive detailed description of all visible visual content"
    )
    
    summary: str = Field(
        ...,
        description="Highly concise summary (maximum 50 words) capturing essential visual content without information loss"
    )
    @field_validator("image_type", mode="before")
    @classmethod
    def map_unknown_to_other(cls, v):
        allowed = {"chart", "figure", "logo", "infographic", "map", "other"}
        if isinstance(v, str) and v not in allowed:
            return "other"
        return v
    
    
image_extraction_agent_schema = ImageExtractionResult.model_json_schema()