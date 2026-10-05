from typing import List, Literal, Union
from pydantic import BaseModel, Field, conlist
from typing import List, Literal, Annotated, Optional
from pydantic import BaseModel, Field
from LLMBatcher.common.myenums import SectionTypes

Box2D = Annotated[
    List[int],
    Field(min_length=4, max_length=4, description="Bounding box [y_min, x_min, y_max, x_max]")
]

class Section(BaseModel):
    section_id: str = Field(...,
                            description="Sequential ID for this section within the page: 'S1', 'S2', 'S3', etc. Must be unique within the page.")

    box_2d: Box2D = Field(...,
                          description="Bounding box coordinates [y_min, x_min, y_max, x_max] in normalized scale (0-1000)")

    # Required, with no default
    type: SectionTypes = Field(
        ...,
        description="Section content type. REQUIRED for every section, no exceptions. Must be one of: 'title' (section headings — short standalone lines that introduce a section, numbered like '1.', '2.1', or named like 'Abstract', 'Introduction'; visually distinct — larger/bolder — from body text), 'text' (body paragraphs, lists, key-value pairs), 'image' (figures, photos, diagrams, charts), 'marginalia' (plain, non-interactive headers, footers, page numbers, margin notes — NOT if they contain checkboxes/radio buttons/signature fields/key-value pairs, which are 'text' instead), 'table' (structured data with rows and columns), 'card' (identification cards, driver licenses, badges), 'attestation' (hand-written signatures, e-signatures, stamps, seals), 'scan_code' (barcodes, QR codes, 2D tracking codes)")

    heading_level: Optional[int] = Field(default=None,
                                         description="Only set when type='title'. 1=top-level (Abstract, Introduction, Chapter 1), 2=sub-heading (1.1, Section A), 3=sub-sub-heading (1.1.1). Leave null for all non-title types.")
    parent_id: str = Field(default="",
                           description="The section_id of the section that logically contains or introduces this section. Empty string if this section has no parent (top-level). Only references sections on the same page.")
    continues_from_id: Optional[str] = Field(default=None,
                                             description="Not set by this pass. Filled in afterward by a separate cross-page linking step. Always leave this null.")


class DocumentLayout(BaseModel):
    sections: List[Section]


bbox_agent_schema = DocumentLayout.model_json_schema()
