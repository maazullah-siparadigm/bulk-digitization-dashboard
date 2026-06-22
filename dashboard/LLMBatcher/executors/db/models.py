from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    Float,
    String,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    UUID,
    Boolean,
    Enum,
    UniqueConstraint

)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func


import uuid

from LLMBatcher.common.myenums import SectionTypes, Stages, TaskTypes \
                                    , TaskStatus, LLMRequestStatus \
                                    , BatchRequestStatus, BatchStatus \
                                    , SectionGroupTypes


Base = declarative_base()

class Cases(Base):
    __tablename__ = "cases"

    __table_args__ = (
        UniqueConstraint("case_code", "case_prefix", name="uq_case_code_prefix"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    case_code = Column(String(50), nullable=False)
    case_prefix = Column(String(20), nullable=False)

    Addendum = Column(Text, nullable=True)
    Requisition = Column(Text, nullable=True)
    Office_Visit_Note = Column(Text, nullable=True)
    Consent = Column(Text, nullable=True)
    Billing_Admin = Column(Text, nullable=True)
    Insurance = Column(Text, nullable=True)
    Insurance_Approval = Column(Text, nullable=True)
    Patient_Demographics = Column(Text, nullable=True)
    Send_Out = Column(Text, nullable=True)
    Tiger_Screenshot = Column(Text, nullable=True)
    Case_Report = Column(Text, nullable=True)
    Historical_Report = Column(Text, nullable=True)
    Histopathology_Report = Column(Text, nullable=True)
    Flow_Cytometry_Report = Column(Text, nullable=True)
    Cytogenetics_Report = Column(Text, nullable=True)
    Molecular_Report = Column(Text, nullable=True)
    CBC_Lab_Report = Column(Text, nullable=True)
    Radiology_Report = Column(Text, nullable=True)
    IHC_Report = Column(Text, nullable=True)
    Screening_Report = Column(Text, nullable=True)
    Slide_Request = Column(Text, nullable=True)
    Others = Column(Text, nullable=True)
    Final_Report = Column(Text, nullable=True)

    total_documents = Column(Integer, nullable=True)
    total_pages = Column(Integer, nullable=True)

    specimen = Column(String(255), nullable=True)


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("case_code", "doc_type", "document_name", name="uq_case_doc_name"),
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_name = Column(String(255), nullable=False)
    case_code = Column(String(100), nullable=False)
    case_prefix = Column(String(20), nullable=False)
    case_year = Column(String(10), nullable=False)
    doc_type = Column(String(100), nullable=False)
    dest_path = Column(Text, nullable=False)
    num_pages = Column(Integer, nullable=False)

    file_size_bytes = Column(BigInteger, nullable=True)
    created_date = Column(DateTime(timezone=True), nullable=True)
    modified_date = Column(DateTime(timezone=True), nullable=True)
    
    digitization_completed = Column(Boolean, nullable=False, default=False)
    response_created = Column(Boolean, nullable=False, default=False)
    images_deleted = Column(Boolean, nullable=False, default=False)

class DigitizedDocument(Base):
    __tablename__ = "digitizeddocuments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


    document_name = Column(String(255), nullable=False)
    digitized_path = Column(Text, nullable=False)

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )
    document = relationship("Document")

class Image(Base):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )
    image_path = Column(String(255), nullable=False)
    width = Column(Integer, nullable = False)
    height = Column(Integer, nullable = False)
    # file_hash = Column(String(64), nullable=False, index=True)

    document = relationship("Document")

class TableSection(Base):
    __tablename__ = "tablesections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    summary = Column(Text, nullable=False, default="")
    table_html = Column(Text, nullable=False)
    verified_html = Column(Text, nullable=True)
    skip_verification = Column(Boolean, nullable=False, default=False)

    extraction_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("extractionsectionblocks.id"),
        nullable=False,
        index=True
    )
    table_rendered_image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("images.id"),
        nullable=True,
        index=True
    )
    extraction_block = relationship("ExtractionSectionBlock")
    table_rendered_image = relationship("Image")


class ImageSection(Base):
    __tablename__ = "imagesections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    response = Column(JSON, nullable=False)

    # image_type = Column(String(200), nullable=False)
    # description = Column(Text, nullable=False)

    extraction_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("extractionsectionblocks.id"),
        nullable=False,
        index=True
    )
    extraction_block = relationship("ExtractionSectionBlock")


class TextSection(Base):
    __tablename__ = "textsections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    response = Column(JSON, nullable=False)


    # summary = Column(Text, nullable=False)
    # elements = Column(JSON, nullable=False)
    # relationships = Column(JSON, nullable=False)

    extraction_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("extractionsectionblocks.id"),
        nullable=False,
        index=True
    )
    extraction_block = relationship("ExtractionSectionBlock")


class MarginaliaSection(Base):
    __tablename__ = "marginaliasections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    response = Column(JSON, nullable=False)


    # marginalia_type = Column(String(200), nullable=False)
    # elements = Column(JSON, nullable=False)
    # relationships = Column(JSON, nullable=False)

    extraction_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("extractionsectionblocks.id"),
        nullable=False,
        index=True
    )
    extraction_block = relationship("ExtractionSectionBlock")

class SpanningSectionResponse(Base):
    __tablename__ = "spanningsectionresponses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    page_index = Column(Integer, nullable=False)

    response = Column(JSON, nullable = False)

    page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id"),
        nullable=False,
        index=True
    )


    page = relationship("Page")

class SemanticSectionGroup(Base):
    __tablename__ = "semanticsectiongroups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    section_name = Column(Text, nullable=False)
    section_number = Column(Integer, nullable=False)
    semantic_section_type = Column(Enum(SectionGroupTypes, name = "section_group_types"), nullable=False, index=False)
    page_index = Column(Integer, nullable=False)

    all_bbox_mappings = Column(JSON, nullable = False)

    page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id"),
        nullable=False,
        index=True
    )

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )


    page = relationship("Page")
    document = relationship("Document")


class ExtractionSectionBlock(Base):
    __tablename__ = "extractionsectionblocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    section_name = Column(Text, nullable=False)
    section_block_type = Column(Enum(SectionGroupTypes, name = "section_group_types"), nullable=False, index=False)
    block_type = Column(Enum(SectionTypes, name = "section_types"), nullable=False, index=True)
    page_index = Column(Integer, nullable=False)
    block_info = Column(JSON, nullable=False)



    image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("images.id"),
        nullable=True,
        index=True
    )

    # page_id = Column(
    #     UUID(as_uuid=True),
    #     ForeignKey("pages.id"),
    #     nullable=False,
    #     index=True
    # )

    semantic_section_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("semanticsectiongroups.id"),
        nullable=False,
        index=True
    )

    image = relationship("Image")
    # page = relationship("Page")
    semantic_section_group = relationship("SemanticSectionGroup")

class Section(Base):
    __tablename__ = "sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    extraction_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("extractionsectionblocks.id"),
        nullable=True,
        index=True
    )

    page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id"),
        nullable=False,
        index=True
    )


    document = relationship("Document")
    extraction_block = relationship("ExtractionSectionBlock")
    page = relationship("Page")


    label = Column(Text, nullable=False)
    section_type = Column(Enum(SectionTypes, name = "section_types"), nullable=False, index=True)
    
    section_id = Column(String(100), nullable=False)
    page_index = Column(Integer, nullable=False)
    
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id"),
        nullable=True,
        index=True
    )

    extraction_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("extractionsectionblocks.id"),
        nullable=True,
        index=True
    )

    parent_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id"),
        nullable=True,
        index=True
    )

    case_code = Column(String(100), nullable=False)

    
    prev_stage_name = Column(Enum(Stages, name = "stages"), nullable=True, index=True)
    stage_name = Column(Enum(Stages, name = "stages"), nullable=False, index=True)
    next_stage_name = Column(Enum(Stages, name = "stages"), nullable=True, index=True)
    
    task_type = Column(Enum(TaskTypes, name = "task_types"), nullable=False, index=True)

    status = Column(Enum(TaskStatus, name = "task_status"), nullable=False, index=True)
    invalidate_chain = Column(Boolean, nullable=False, default=False) 

    retries = Column(Integer, default=0)
    failure_message = Column(Text, nullable=True)

    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    created_time = Column(DateTime(timezone=True), server_default=func.now())
    updated_time = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


    document = relationship("Document")
    page = relationship("Page")
    extraction_block = relationship("ExtractionSectionBlock")
    parent_task = relationship(
        "Task",
        remote_side=[id]
    )


    def __repr__(self):
        return (
            f"<Request id={self.id} "
            f"doc={self.document_id} "
            f"stage={self.stage_name} "
            f"status={self.status}>"
        )


class Page(Base):
    __tablename__ = "pages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


    image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("images.id"),
        nullable=False,
        index=True
    )

    annotated_image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("images.id"),
        nullable=True,
        index=True
    )

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )
    

    page_index = Column(Integer, nullable=False)
    
    document = relationship("Document")
    image = relationship(
        "Image",
        foreign_keys=[image_id]
    )
    annotated_image = relationship(
        "Image",
        foreign_keys=[annotated_image_id]
    )

class OCRResult(Base):
    __tablename__ = "ocrresults"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id"),
        nullable=True,
        index=True
    )

    # response = Column(JSON, nullable=False, default = dict)
    ocr_relative_path = Column(Text, nullable=False)
    ocr_count = Column(Integer, nullable=False, default=0)

    
    document = relationship("Document")
    page = relationship("Page")

class QualityCheck(Base):
    __tablename__ = "quality_check"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    ocr_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ocrresults.id"),
        nullable=False,
        index=True
    )

    page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id"),
        nullable=False,
        index=True
    )

    ocr_score = Column(Integer, nullable=False, default=0)
    original_orientation = Column(Integer, nullable=False, default=0)
    corrected_orientation = Column(Integer, nullable=False, default=0)
    needs_reocr = Column(Boolean, nullable=False, default=False)

    ocr = relationship("OCRResult")
    page = relationship("Page")

class LLMRequestImage(Base):
    __tablename__ = "llmrequest_images"

    llm_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("llmrequests.id", ondelete="CASCADE"),
        primary_key=True
    )

    image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="CASCADE"),
        primary_key=True
    )

    caption = Column(Text, nullable=False, default="")

    # relationships
    image = relationship("Image", lazy="joined")
    llm_request = relationship("LLMRequest", back_populates="image_links")


class LLMRequest(Base):
    __tablename__ = "llmrequests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id"),
        nullable=False,
        index=True,
        unique=True
    )

    stage_name = Column(Enum(Stages, name = "stages"), nullable=False, index=True)

    variables = Column(JSON, nullable=False, default=dict)
    page_index = Column(Integer, nullable=False)

    status = Column(Enum(LLMRequestStatus, name = "llm_task_status"), nullable=False, index=True)
    response = Column(JSON, nullable=False, default=dict)
    retry_count = Column(Integer, nullable=False, default=0)

    # relationships
    document = relationship("Document")
    task = relationship("Task")

    image_links = relationship(
        "LLMRequestImage",
        back_populates="llm_request",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # convenience accessor (read-only)
    @property
    def images(self):
        return [link.image for link in self.image_links]


    

class Batch(Base):
    __tablename__ = "batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_batch_id = Column(String(500), nullable=True, unique=True, index=True)
    model_name = Column(String(100), nullable=True, index=True)
    status = Column(Enum(BatchStatus, name = "batch_status"), nullable=False, index=True)
    input_file_uri = Column(String(500), nullable=True)
    output_file_uri = Column(String(500), nullable=True)
    requests_count = Column(Integer, default=0)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)

    input_text_tokens = Column(Integer, default=0)
    input_image_tokens = Column(Integer, default=0)
    total_input_tokens = Column(Integer, default=0)

    output_text_tokens = Column(Integer, default=0)
    output_thinking_tokens = Column(Integer, default=0)
    total_output_tokens = Column(Integer, default=0)

    total_tokens = Column(Integer, default=0)

    response = Column(JSON, nullable=True)
    input_file_size_bytes = Column(
        BigInteger, nullable=True
    )
    images_size_bytes = Column(BigInteger, nullable=False, default=0)

    created_time = Column(DateTime(timezone=True), server_default=func.now())
    updated_time = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self):
        return f"<Batch id={self.id} status={self.status}>"




class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("images.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Hash is indexed for cache checks, but not unique: identical bytes can appear
    # across different image rows when cross-image dedupe is disabled.
    file_hash = Column(String(64), nullable=False, index=True)
    mime_type = Column(String(100), nullable=False)
    google_file_uri = Column(String(500), nullable=False, unique=True)
    status = Column(String(20), nullable=True, default=None)
    file_size_bytes = Column(
        BigInteger, nullable=False
    )  # For storage tracking (20GB limit)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    created_time = Column(DateTime(timezone=True), server_default=func.now())
    updated_time = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    image = relationship("Image")


class BatchRequest(Base):
    __tablename__ = "batch_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    batch_id = Column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False, index=True)
    llm_request_id = Column(UUID(as_uuid=True), ForeignKey("llmrequests.id"), nullable=False, index=True)
    request_key = Column(String(255), nullable=False, index=True)

    status = Column(Enum(BatchRequestStatus, name = "batch_request_status"), nullable=False, index=True)

    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)

    batch = relationship("Batch")
    llm_request = relationship("LLMRequest")




class Status(Base):
    __tablename__ = "status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    # Mutable system state (input/output of stages)
    statedata = Column(JSON, nullable=False)

    document = relationship("Document")

    def __repr__(self):
        return f"<Status doc={self.document_id}>"



class Response(Base):
    __tablename__ = "responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    llm_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("llmrequests.id"),
        nullable=False,
        index=True,
        unique=True,
    )
    batch_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("batch_requests.id"),
        nullable=True,
        index=True,
    )

    # Token tracking fields
    input_text_tokens = Column(BigInteger, nullable=True)
    input_image_tokens = Column(BigInteger, nullable=True)
    total_input_tokens = Column(BigInteger, nullable=True)
    output_text_tokens = Column(BigInteger, nullable=True)
    output_thinking_tokens = Column(BigInteger, nullable=True)
    total_output_tokens = Column(BigInteger, nullable=True)
    total_tokens = Column(BigInteger, nullable=True)

    response_text = Column(Text, nullable=True)
    response_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    created_time = Column(DateTime(timezone=True), server_default=func.now())
    updated_time = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    llm_request = relationship("LLMRequest")
    batch_request = relationship("BatchRequest")
