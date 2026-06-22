from enum import Enum


class NodeLabelsEnum(str, Enum):
    """Top-level node labels for document hierarchy."""
    DOCUMENT = "DOCUMENT"
    SECTION = "SECTION"


class SectionBlocksEnum(str, Enum):
    """Block-level labels within a section."""
    TEXT = "TEXT_BLOCK"
    IMAGE = "IMAGE_BLOCK"
    TABLE = "TABLE_BLOCK"
    MARGINALIA = "MARGINALIA_BLOCK"

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


class SectionTypes(str, Enum):
    text = "text"
    table = "table"
    image = "image"
    marginalia = "marginalia"


class SectionGroupTypes(str, Enum):
    merged = "MERGED"
    individual = "INDIVIDUAL"
    

class Stages(str, Enum):
    start = "START"
    
    load_pdf = "LOAD_PDF"
    ocr = "OCR"
    qc = "QC"
    bbox_agent = "BBOX_AGENT"
    
    bbox_correction = "BBOX_CORRECTION"
    annotate_pdf = "ANNOTATE_PDF"
    
    annotate_image = "ANNOTATE_IMAGE"
    
    section_span_agent = "SECTION_SPAN_AGENT"
    semantic_grouping_and_extraction_blocks = "semantic_grouping_and_extraction_blocks"
    
    section_cropping = "SECTION_CROPPING"
    
    router = "ROUTER"

    text_extraction_agent = "TEXT_EXTRACTION_AGENT"
    table_extraction_agent = "TABLE_EXTRACTION_AGENT"
    table_renderer = "TABLE_RENDERER"
    table_verification_agent = "TABLE_VERIFICATION_AGENT"
    image_extraction_agent = "IMAGE_EXTRACTION_AGENT"
    marginalia_extraction_agent = "MARGINALIA_EXTRACTION_AGENT"
    
    end = "END"



class UploadedFileStatus(str, Enum):
    pending = "PENDING"
    uploaded = "UPLOADED"
    failed = "FAILED"
    deleted = "DELETED"


class ThinkingLevels(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


