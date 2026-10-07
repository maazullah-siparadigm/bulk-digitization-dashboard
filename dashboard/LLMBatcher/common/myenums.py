from enum import Enum


class NodeLabelsEnum(str, Enum):
    """Top-level node labels for document hierarchy."""
    FILE = "FILE"
    DOCUMENT = "DOCUMENT"
    SECTION = "SECTION"


class SectionBlocksEnum(str, Enum):
    """Block-level labels within a section."""
    TEXT = "TEXT_BLOCK"
    IMAGE = "IMAGE_BLOCK"
    TABLE = "TABLE_BLOCK"
    MARGINALIA = "MARGINALIA_BLOCK"
    CARD = "CARD_BLOCK"
    ATTESTATION = "ATTESTATION_BLOCK"
    SCAN_CODE = "SCAN_CODE_BLOCK"

class TextBlockFeaturesEnum(str, Enum):
    # LINES = "LINES"
    KVPS = "KVPS_ELEMENT"
    CHOCIES = "CHOICES_ELEMENT"
    PARAGRAPHS = "PARAGRAPH_ELEMENT"
    ITEMS = "ITEMS_ELEMENT"
    SIGNATURE = "SIGNATURE_ELEMENT"
    
# class MarginaliaTypesEnum(str, Enum):
#     FOOTNOTE = "footnote"
#     ENDNOTE = "endnote"
#     SIDENOTE = "sidenote"
#     ANNOTATION = "annotation"
#     COMMENT = "comment"
#     REFERENCE = "reference"
#     HEADER = "header"
#     FOOTER = "footer"
#     OTHER = "other"
    
class TableBlockFeaturesEnum(str, Enum):
    CELLS = "CELL_ELEMENT"
    



class NodeTypes(str, Enum):
    code = "code"
    llm = "llm"
    compute = "compute"


class TaskStatus(str, Enum):
    pending = "PENDING"
    marked_for_processing = "MARKED_FOR_PROC"
    submitted = "SUBMITTED"
    started = "STARTED"
    processing = "PROCESSING"
    # started = "STARTED"
    handoff_pending = "HANDOFF_PENDING"
    completed = "COMPLETED"
    failed = "FAILED"


class LLMRequestStatus(str, Enum):
    pending = "PENDING"
    submitted = "SUBMITTED"
    started = "STARTED"
    complete = "COMPLETE"
    failed = "FAILED"


class BatchStatus(str, Enum):
    pending = "PENDING"
    submitted = "SUBMITTED"
    completed = "COMPLETED"
    failed = "FAILED"
    cancelled = "CANCELLED"
    expired = "EXPIRED"


class BatchRequestStatus(str, Enum):
    pending = "PENDING"
    submitted = "SUBMITTED"
    success = "SUCCESS"
    failed = "FAILED"


class TaskTypes(str, Enum):
    compute = "COMPUTE"
    agent = "AGENT"
    start = "START"
    end = "END"
    router = "ROUTER"
    # No queue: released by a periodic barrier worker, then handled by the orchestrator.
    barrier = "BARRIER"


class SectionTypes(str, Enum):
    text = "text"
    table = "table"
    image = "image"
    marginalia = "marginalia"
    # New Added
    title = "title"
    card = "card"
    attestation = "attestation"
    scan_code = "scan_code"


class SectionGroupTypes(str, Enum):
    merged = "MERGED"
    individual = "INDIVIDUAL"


class TableTypes(str, Enum):
    simple_table = "SIMPLE_TABLE"
    complex_table = "COMPLEX_TABLE"


class FalseTableTypes(str, Enum):
    kvp = "kvp"
    list_ = "list"
    list_with_selection = "list_with_selection"

class Stages(str, Enum):
    start = "START"
    
    load_pdf = "LOAD_PDF"
    ocr = "OCR"
    qc = "QC"
    bbox_agent = "BBOX_AGENT"
    
    bbox_correction = "BBOX_CORRECTION"
    
    annotate_image = "ANNOTATE_IMAGE"
    # One per page. Holds build_page_pairs back until every page has settled.
    page_barrier = "PAGE_BARRIER"

    # The cross-page phase. Every page waits at its page_barrier until the whole
    # document has settled - annotated or rejected by QC; a failed page never settles
    # and stops the document - because a page's partner cannot be known while any
    # earlier page is still in flight.
    # ngl_donut_ai gets that barrier for free: link_all_pages (core.py:1383) runs
    # after the per-page gather has already returned.

    # One per-document compute task, no LLM call. Resolves which pages pair with
    # which (donut's _prev_nonempty_page, core.py:1386) and builds what each pair
    # needs judged: the section trees and candidate ids printed into the prompt
    # (_find_continuation_candidates, core.py:1240) and the stitched image
    # (_stitch_pages_top_to_bottom, core.py:1113). All of it lands on Page.
    build_page_pairs = "BUILD_PAGE_PAIRS"

    # One agent task per pair that has candidates. Task.page_id is the LATER page;
    # that page's Page.prev_page_id names the earlier half. Pages whose candidate_ids
    # come back empty never get a task at all - donut skips the call outright
    # (core.py:1396), and so do we.
    link_page_continuity_agent = "LINK_PAGE_CONTINUITY_AGENT"
    # One per completed link. Holds build_cross_page_hierarchy back until every linking
    # task has completed or failed.
    hierarchy_barrier = "HIERARCHY_BARRIER"

    # build_cross_page_hierarchy is a single per-document compute task, no LLM call.
    build_cross_page_hierarchy = "BUILD_CROSS_PAGE_HIERARCHY"

    section_span_agent = "SECTION_SPAN_AGENT"
    semantic_grouping_and_extraction_blocks = "semantic_grouping_and_extraction_blocks"
    
    section_cropping = "SECTION_CROPPING"
    
    router = "ROUTER"

    text_classification_agent = "TEXT_CLASSIFICATION_AGENT"
    text_router = "TEXT_ROUTER"

    text_extraction_agent = "TEXT_EXTRACTION_AGENT"
    content_extraction_using_ocr = "CONTENT_EXTRACTION_USING_OCR"
    image_extraction_agent = "IMAGE_EXTRACTION_AGENT"
    marginalia_extraction_agent = "MARGINALIA_EXTRACTION_AGENT"
    attestation_extraction_agent = "ATTESTATION_EXTRACTION_AGENT"
    table_classification_agent = "TABLE_CLASSIFICATION_AGENT"
    
    table_router = "TABLE_ROUTER"
    table_extraction_simple_agent = "TABLE_EXTRACTION_SIMPLE_AGENT"
    table_extraction_agent = "TABLE_EXTRACTION_AGENT"
    table_extraction_multipage_simple_agent = "TABLE_EXTRACTION_MULTIPAGE_SIMPLE_AGENT"
    table_extraction_multipage_agent = "TABLE_EXTRACTION_MULTIPAGE_AGENT"
    
    end = "END"
    
    # STAGES BELOW ARE NOT BEING USED BUT ARE KEPT HERE BECAUSE THE ENUMS ARE USED IN SOME CASES
    table_renderer = "TABLE_RENDERER"
    table_verification_agent = "TABLE_VERIFICATION_AGENT"
    annotate_pdf = "ANNOTATE_PDF"


class UploadedFileStatus(str, Enum):
    pending = "PENDING"
    uploaded = "UPLOADED"
    failed = "FAILED"
    deleted = "DELETED"


class ThinkingLevels(str, Enum):
    MINIMAL = "MINIMAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"



class ImageType(str, Enum):
    CHART = "chart"
    FIGURE = "figure"
    LOGO = "logo"
    INFOGRAPHIC = "infographic"
    MAP = "map"
    BARCODE = "barcode"
    QR_CODE = "qr_code"
    OTHER = "other"


class ImageContentType(str, Enum):
    CHART = "chart"
    FIGURE = "figure"
    LOGO = "logo"
    INFOGRAPHIC = "infographic"
    MAP = "map"
    OTHER = "other"





class ElementType(str, Enum):
    # For Marginalia
    TEXT = "text"
    KEY_VALUES = "key_values"
    CHECKBOX = "checkbox"
    RADIO_BUTTON = "radio_button"
    ORDERED = "ordered"
    UNORDERED = "unordered"
    IMAGE = "image"




class MarginaliaType(str, Enum):
    HEADER = "header"
    FOOTER = "footer"
    OTHER = "other"




class CodeType(str, Enum):
    BARCODE = "barcode"
    QR_CODE = "qr_code"
    OTHER = "other"
