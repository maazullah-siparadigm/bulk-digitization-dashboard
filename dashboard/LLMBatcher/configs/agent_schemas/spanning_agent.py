from typing import List, Literal, Union
from pydantic import BaseModel, Field, conlist
from typing import List, Literal, Annotated
from pydantic import BaseModel, Field


# Pydantic Schema for Section Spanning Analysis Validation
class SectionGroup(BaseModel):
    section_header: str = Field(..., description="Exact text of the main heading or section title as it appears in the document (e.g., 'Introduction', '3.2 Methodology', 'Table 1: Results')")
    bbox_ids: List[str] = Field(..., min_items=1, description="List of bounding box identifiers that belong to this semantic section. Each ID corresponds to a detected bbox (e.g., ['Page1_S1', 'Page1_S2'])")

class SpanningAnalysisResponse(BaseModel):
    sections: List[SectionGroup] = Field(..., description="List of section groups identified in the page")



section_span_agent_schema = SpanningAnalysisResponse.model_json_schema()