from typing import List, Optional

from pydantic import BaseModel, Field


class SectionContinuation(BaseModel):
    section_id: str = Field(
        ...,
        description=(
            "The exact id label printed on the CURRENT page image (e.g. 'Page3_S5') "
            "for a section that continues from the previous page."
        ),
    )
    continues_from_id: str = Field(
        ...,
        description=(
            "The exact id label printed on the PREVIOUS page image (e.g. 'Page2_S9') "
            "for the specific section whose content this one continues."
        ),
    )


class PageLinkage(BaseModel):
    """Two independent judgments about the CURRENT page relative to the PREVIOUS
    page (both shown in one stitched image, section ids printed on their boxes):
    whether it starts a new, unrelated document, and - only when it doesn't -
    which of its candidate sections continue text cut off on the previous page."""

    is_new_document: bool = Field(
        default=False,
        description=(
            "True only if the current page clearly begins a different, unrelated document "
            "from the previous page. Judge holistically: template/branding, content type, "
            "whether current-page text picks up mid-thought vs. starts fresh, persisting "
            "identifiers (case/order/invoice numbers), and page numbering. No single signal "
            "is decisive alone - page numbering especially is weak evidence by itself. Text "
            "picking up mid-thought from the previous page always means False, regardless of "
            "any other signal."
        ),
    )
    new_document_reason: Optional[str] = Field(
        default=None,
        description=(
            "One short phrase naming what changed, only when is_new_document is True "
            "(e.g. 'different letterhead, page number reset to 1'). Null when "
            "is_new_document is False."
        ),
    )
    continuations: List[SectionContinuation] = Field(
        default_factory=list,
        description=(
            "Current-page sections that continue a specific previous-page section. Empty "
            "when none continue, and always empty when is_new_document is True."
        ),
    )


page_linkage_schema = PageLinkage.model_json_schema()
