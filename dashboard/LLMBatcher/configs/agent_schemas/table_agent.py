from typing import List, Literal, Union
from pydantic import BaseModel, Field, conlist
from typing import List, Literal, Annotated
from pydantic import BaseModel, Field


class TableExtractionResult(BaseModel):
    summary: str = Field(
        ...,
        min_length=1,
        description="Highly concise summary (maximum 50 words) capturing essential table content without information loss"
    )
    corrected_html: str = Field(
        ...,
        min_length=1,
        description="Complete corrected HTML table code including <style> block if needed"
    )
    
    
table_extraction_schema = TableExtractionResult.model_json_schema()