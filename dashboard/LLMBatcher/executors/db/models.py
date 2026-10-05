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
    UniqueConstraint,
    CheckConstraint,
    Index

)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func, text


import uuid

from LLMBatcher.common.myenums import SectionTypes, Stages, TaskTypes \
                                    , TaskStatus, LLMRequestStatus \
                                    , BatchRequestStatus, BatchStatus \
                                    , SectionGroupTypes, TableTypes \
                                    , FalseTableTypes


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

    # Storage only - deliberately NOT yet used as a sort key. The scheduling-fairness
    # fix is ordering by Task.created_time alone, so that it can be confirmed on its
    # own; wiring priority in at the same time would make it unclear which change
    # resolved the stall. Ordering becomes `priority DESC, created_time ASC` when it
    # is actually needed.
    priority = Column(Integer, nullable=False, server_default=text("0"), index=True)

    file_size_bytes = Column(BigInteger, nullable=True)
    created_date = Column(DateTime(timezone=True), nullable=True)
    modified_date = Column(DateTime(timezone=True), nullable=True)

    # clock_timestamp() is per-row; now() would tie every row in a batch insert
    ingested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("clock_timestamp()"),
    )

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
    # Cross-page rework, Stage 4 (multi-page table merge). list[str(UUID)] of every
    # ExtractionSectionBlock a merged table's content came from. extraction_block_id
    # above stays single-valued and points at the primary/first block, so nothing
    # that reads it today changes; this records the rest of the lineage.
    lineage_extraction_block_ids = Column(JSON, nullable=True)

    extraction_block = relationship("ExtractionSectionBlock")
    table_rendered_image = relationship("Image")

class TableClassification(Base):
    __tablename__ = "tableclassifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    is_true_table = Column(Boolean, nullable=False, default=False)
    is_heavily_redacted = Column(Boolean, nullable=False, default=False)
    is_complex_table = Column(Boolean, nullable=False, default=False)
    false_table_type = Column(Enum(FalseTableTypes, name = "false_table_types"), nullable=True, index=False)
    
    final_section_type = Column(Enum(SectionTypes, name = "section_types"), nullable=True, index=False)


    extraction_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("extractionsectionblocks.id"),
        nullable=False,
        index=True
    )
    extraction_block = relationship("ExtractionSectionBlock")


class AttestationSection(Base):
    """Result of attestation_extraction_agent - signatures, e-signatures, stamps, seals.

    Same shape as the other per-type result tables: the agent's JSON response is stored
    whole in `response` (summary + discriminated-union elements), one row per
    ExtractionSectionBlock.
    """

    __tablename__ = "attestationsections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    response = Column(JSON, nullable=False)

    extraction_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("extractionsectionblocks.id"),
        nullable=False,
        index=True
    )
    extraction_block = relationship("ExtractionSectionBlock")


class TextClassification(Base):
    """Verdict of text_classification_agent, read by Stages.text_router.

    Mirrors TableClassification: ngl_donut_ai decides inline whether a text crop needs
    the extraction agent at all (core.py:519-523), but this pipeline routes from DB
    state, so the verdict is persisted here and branched on in text_router. False means
    the crop is pure prose and the OCR text is used instead of calling the text agent.
    """

    __tablename__ = "textclassifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    has_structured_content = Column(Boolean, nullable=False, default=False)

    extraction_block_id = Column(
        UUID(as_uuid=True),
        ForeignKey("extractionsectionblocks.id"),
        nullable=False,
        index=True
    )
    extraction_block = relationship("ExtractionSectionBlock")


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

    # __table_args__ = (
    #     # DB-level guard against the simplest case (a section pointing at itself).
    #     # This does NOT catch longer loops (A -> B -> A) - that has to be checked
    #     # by whatever code writes these links (bbox_correction_worker.py for
    #     # parent_section_id, link_page_continuity_agent's resolution code for
    #     # continues_from_section_id) before it saves the row.
    #     CheckConstraint("id != parent_section_id", name="ck_section_parent_not_self"),
    #     CheckConstraint("id != continues_from_section_id", name="ck_section_continues_from_not_self"),
    # )

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

    # Same-page nesting, written by bbox_agent/bbox_correction_worker.py.
    # SET NULL is defensive here rather than strictly required: this link only ever
    # points within one page, and bbox_agent's retry path deletes that whole page's
    # sections in a single statement, so the referencing rows go with the referenced
    # ones. It matters for any future code that deletes one section on its own.
    # (continues_from_section_id below is the one where it is load-bearing.)
    parent_section_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Cross-page continuation, written by the future link_page_continuity_agent.
    # ondelete="SET NULL" is REQUIRED here, not a nicety: bbox_agent's retry path
    # (TaskInvalidator, Stages.bbox_agent branch, orchestrator.py ~524) hard-deletes
    # every Section on the retried page with a raw bulk DELETE that bypasses ORM
    # cascades. A section on the NEXT page pointing back at a deleted one is not
    # covered by that DELETE, so without SET NULL Postgres raises ForeignKeyViolation
    # and the retry itself breaks.
    continues_from_section_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    heading_level = Column(Integer, nullable=True)


    document = relationship("Document")
    extraction_block = relationship("ExtractionSectionBlock")
    page = relationship("Page")
    parent_section = relationship("Section", remote_side=[id], foreign_keys=[parent_section_id])
    continues_from_section = relationship("Section", remote_side=[id], foreign_keys=[continues_from_section_id])


    section_type = Column(Enum(SectionTypes, name = "section_types"), nullable=False, index=True)

    section_id = Column(String(100), nullable=False)
    page_index = Column(Integer, nullable=False)

    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)


class Task(Base):
    __tablename__ = "tasks"

    # __table_args__ = (
    #     # Activation concurrency guard. activate_documents decides a document is in
    #     # the pool by "has no Task row", so two simultaneous callers can both pass
    #     # that check and double-create the start task. Listed as a known gap in
    #     # docs/document_intake.md; harmless with one CLI user, not with a web layer.
    #     Index(
    #         "uq_task_one_start_per_document",
    #         "document_id",
    #         unique=True,
    #         postgresql_where=text("stage_name = 'START'"),
    #     ),
    #     # (A "one link task per page-pair" index used to be sketched here, keyed on
    #     # page_id + prev_page_id. It is no longer needed: a page-pair is identified by
    #     # its LATER page, so Task.page_id already names it, and the linking payload
    #     # lives on Page - see Page.prev_page_id below. Writing it twice is idempotent
    #     # rather than duplicative.)
    # )

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
    # clock_timestamp(), not now(): now() returns the TRANSACTION start time, so every
    # Task inserted in one transaction (all start tasks from one activation run, all
    # block tasks from one orchestrator pass) would get a byte-identical value and be
    # unorderable among themselves. Same reason Document.ingested_at uses it.
    # The order_by clauses that consume this are not written yet - see the deferred
    # scheduling-fairness work in docs/digitization_rework_roadmap.md.
    created_time = Column(
        DateTime(timezone=True),
        server_default=text("clock_timestamp()"),
        index=True,
    )
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

    # ---- cross-page linking, written by the link_page_continuity prep worker ----
    #
    # ngl_donut_ai keeps all of this in locals and page-indexed lists inside
    # link_all_pages (core.py:1383) - the stitched image, the section trees and the
    # candidate lists live for the length of one await and die with the call. Here the
    # payload is built by a compute worker and consumed by the orchestrator when it
    # builds the agent request: different processes, different transactions. So it has
    # to persist, and it persists on Page because every one of these values describes a
    # single page. A "pair" is just a page plus a pointer backwards.
    #
    # This is the same kind of column as annotated_image_id above: derived output of a
    # stage, nullable until that stage runs, reset by TaskInvalidator on a retry.

    # The page this one is compared against: donut's _prev_nonempty_page (core.py:1386),
    # the nearest EARLIER page that actually HAS an annotated image. That is not
    # page_index - 1: a page scoring below OCR_SCORE_THRESHOLD is routed straight to
    # Stages.end and never annotates, so page 5 pointing back at page 3 is normal.
    # NULL on the first page, and on any page that is itself blank.
    prev_page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id"),
        nullable=True,
        index=True
    )

    # This page's own sections as the indented tree printed into the linking prompt
    # (_find_continuation_candidates, core.py:1240). Read twice: as {tree_str} for this
    # page's own call, and as {prev_tree_str} for the next page's. Donut rebuilds it
    # for each of those; storing it means it is computed once per page instead.
    tree_str = Column(Text, nullable=True)

    # The printed ids on this page that could continue something from the previous page
    # - every non-marginalia section. An empty list is donut's `if not candidate_ids:
    # continue` (core.py:1396): a page of nothing but headers and footers has nothing
    # that could continue, and no LLM call is made for it at all.
    #
    # Not just a skip flag - donut passes these into the call (core.py:1414) to validate
    # the ids that come back, so a hallucinated "Page5_S9" is rejected rather than
    # resolved against the wrong row.
    candidate_ids = Column(JSON, nullable=True)

    # This page stacked BELOW prev_page with the thick yellow "PAGE BREAK" divider
    # between them (_stitch_pages_top_to_bottom, core.py:1113). The agent's only image:
    # its prompt is written against one tall image, not two. NULL when there is no pair
    # or no candidates - the prep worker skips the stitch rather than rendering a file
    # nothing will reference.
    stitched_image_id = Column(
        UUID(as_uuid=True),
        ForeignKey("images.id"),
        nullable=True,
        index=True
    )

    document = relationship("Document")
    # foreign_keys must be explicit: three FKs into images.id now, so SQLAlchemy cannot
    # infer which one each relationship means.
    image = relationship(
        "Image",
        foreign_keys=[image_id]
    )
    annotated_image = relationship(
        "Image",
        foreign_keys=[annotated_image_id]
    )
    stitched_image = relationship(
        "Image",
        foreign_keys=[stitched_image_id]
    )
    # Self-referential: remote_side marks the "one" end, so page.prev_page is the
    # earlier Page rather than a collection.
    prev_page = relationship("Page", remote_side=[id])

class PageLinkageResponse(Base):
    """The validated PageLinkage answer for one page-pair, keyed by the LATER page.

    Mirrors SpanningSectionResponse exactly: the whole model_dump() of an agent's
    response, stored as JSON against the page it describes. Kept out of Page itself
    because every agent response in this schema lives in its own table - TextSection,
    TableSection, ImageSection, MarginaliaSection, AttestationSection,
    TableClassification and TextClassification all hang off ExtractionSectionBlock,
    and SpanningSectionResponse hangs off Page rather than sitting on it.

    The split also means a retried agent call deletes this row and leaves Page alone,
    so the re-ask reuses the stitched image and the section trees instead of
    re-rendering them.

    Only half of what is in here is resolved into the schema. `continuations` is
    applied to Section.continues_from_section_id, which is what
    build_cross_page_hierarchy reads - that worker never looks at this table.
    `is_new_document` and `new_document_reason` stay here and are read much later by
    the serializer, which uses them to split one uploaded PDF into several documents
    (ngl_donut_ai digitization_serializer/converter.py:395).
    """

    __tablename__ = "pagelinkageresponses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    response = Column(JSON, nullable=False)

    # The LATER page of the pair. Its Page.prev_page_id names the other half, so the
    # pair is fully identified by this one column.
    page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id"),
        nullable=False,
        index=True
    )

    page = relationship("Page")


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
