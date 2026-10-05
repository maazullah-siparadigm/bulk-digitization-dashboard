from LLMBatcher.executors.db.models import Task, Document, Page \
                                         , OCRResult, QualityCheck, Section \
                                         , SpanningSectionResponse, SemanticSectionGroup \
                                         , ExtractionSectionBlock, TextSection \
                                         , MarginaliaSection, TableSection, ImageSection \
                                         , TableClassification, TextClassification \
                                         , AttestationSection, PageLinkageResponse
from LLMBatcher.common.myenums import Stages, TaskStatus
from sqlalchemy.orm import Session

def populate_doc_tree(task_id, task_dict: dict):
    page_num = None
    
    if task_dict[task_id]["task"].page:
        page_num = f"Page {task_dict[task_id]['task'].page.page_index}"
    task_name = " ".join(task_dict[task_id]["task"].stage_name.split("_"))
    node_dict = {
        "id" : task_id,
        "type" : task_dict[task_id]["task"].task_type,
        "name" : task_name,
        "page_index" : page_num,
        "status" : task_dict[task_id]["task"].status,
        "children" : []
    }

    for child_id in task_dict[task_id]["children"]:
        node_dict["children"].append(populate_doc_tree(child_id, task_dict))

    return node_dict



def get_data_associated_with_task(task: Task, db: Session):
    try:
        data = {}
        if task.status == TaskStatus.failed:
            data["status"] = {
                "field" : "Status",
                "values" : "Failed"
            }

            data["error"] = {
                "field" : "Error",
                "values" : task.failure_message
            }
            
            return data
        
        if task.stage_name == Stages.load_pdf:
            num_pages = db.query(Page).filter(Page.document_id == task.document_id).count()
            data["Pages Extracted"] = num_pages
        
        elif task.stage_name == Stages.ocr:
            ocr_result = db.query(OCRResult).filter(OCRResult.page_id == task.page_id).one_or_none()
            data["OCR Path"] = ocr_result.ocr_relative_path
            data["OCR Count"] = ocr_result.ocr_count

        elif task.stage_name == Stages.qc:
            task_ocr_qc = db.query(QualityCheck).filter(QualityCheck.page_id == task.page_id).one_or_none()
            data["Original Orientation"] = task_ocr_qc.original_orientation
            data["Corrected Orientation"] = task_ocr_qc.corrected_orientation
            data["Needs ReOCR"] = task_ocr_qc.needs_reocr
        
        elif task.stage_name == Stages.bbox_agent:
            all_sections = db.query(Section).filter(Section.page_id == task.page_id).all()

            data["total-sections-extracted"] = {
                                        "field" : "Total Sections Extracted",
                                        "value" : len(all_sections)
                                        } 
            
            data["section-names"] = {
                "field" : "Section Names",
                "value" : [f"{sec.section_type} | {sec.section_id}" for sec in all_sections]
            }

        elif task.stage_name == Stages.bbox_correction:
            pass

        elif task.stage_name == Stages.annotate_image:
            pass
        
        elif task.stage_name == Stages.section_span_agent:
            spanning_section_response = db.query(SpanningSectionResponse).filter(SpanningSectionResponse.page_id == task.page_id).one_or_none()
            data["spanning-response"] = {
                "field" : "Spanning Response",
                "value" : spanning_section_response.response
            }
        
        elif task.stage_name == Stages.semantic_grouping_and_extraction_blocks:
            num_semantic_sections = db.query(SemanticSectionGroup).filter(SpanningSectionResponse.page_id == task.page_id).count()
            num_extraction_sections = db.query(ExtractionSectionBlock).join(
                                ExtractionSectionBlock.semantic_section_group
                            ).filter(SpanningSectionResponse.page_id == task.page_id).count()
            data["num-semantic-sections"] = {
                "field" : "Num. Semantic Sections",
                "value" : num_semantic_sections
            }
            data["num-extraction-block-sections"] = {
                "field" : "Num. Extraction Block Sections",
                "value" : num_extraction_sections
            }
        elif task.stage_name == Stages.section_cropping:
            all_extraction_sections = db.query(ExtractionSectionBlock).join(
                                ExtractionSectionBlock.semantic_section_group
                            ).filter(SemanticSectionGroup.page_id == task.page_id).all()
            
            total_num_extracted_sections = len(all_extraction_sections)

            extracted_sections_with_images = 0

            for extraction_section in all_extraction_sections:
                if extraction_section.image_id:
                    extracted_sections_with_images += 1

            data["num-extraction-block-sections"] = {
                "field" : "Num. Extraction Block Sections",
                "value" : total_num_extracted_sections
            }

            data["num-extraction-block-sections-with-images"] = {
                "field" : "Num. Extraction Block Sections With Images",
                "value" : extracted_sections_with_images
            }

        elif task.stage_name in (Stages.router, Stages.text_router, Stages.table_router):
            num_children = db.query(Task).filter(Task.page_id == task.page_id, Task.invalidate_chain == False, Task.parent_task_id == task.id).count()
            data["num-children"] = {
                "field" : "Num. Children Spawned",
                "value" : num_children
            }

        elif task.stage_name == Stages.build_page_pairs:
            # Document-level task (page_id is None); the output lives on Page.
            pages = db.query(Page).filter(Page.document_id == task.document_id).all()
            data["pages-with-prev-page"] = {
                "field" : "Pages Paired With An Earlier Page",
                "value" : sum(1 for pg in pages if pg.prev_page_id)
            }
            data["pages-with-candidates"] = {
                "field" : "Pairs Needing A Linkage Call",
                "value" : sum(1 for pg in pages if pg.candidate_ids)
            }

        elif task.stage_name == Stages.link_page_continuity_agent:
            linkage = db.query(PageLinkageResponse).filter(
                                    PageLinkageResponse.page_id == task.page_id
                                    ).one_or_none()
            if linkage:
                data["page-linkage"] = {
                    "field" : "Page Linkage Response",
                    "value" : linkage.response
                }

        elif task.stage_name == Stages.build_cross_page_hierarchy:
            # Document-level task; the output is the links written onto Section.
            sections = db.query(Section).filter(Section.document_id == task.document_id).all()
            data["total-sections"] = {
                "field" : "Total Sections",
                "value" : len(sections)
            }
            data["sections-with-parent"] = {
                "field" : "Sections Nested Under A Parent",
                "value" : sum(1 for sec in sections if sec.parent_section_id)
            }
            data["sections-continuing"] = {
                "field" : "Sections Continuing From A Previous Page",
                "value" : sum(1 for sec in sections if sec.continues_from_section_id)
            }

        elif task.stage_name == Stages.text_classification_agent:
            text_classification = db.query(TextClassification).filter(
                                    TextClassification.extraction_block_id == task.extraction_block_id
                                    ).one_or_none()
            if text_classification:
                data["has-structured-content"] = {
                    "field" : "Has Structured Content",
                    "value" : text_classification.has_structured_content
                }

        elif task.stage_name == Stages.table_classification_agent:
            table_classification = db.query(TableClassification).filter(
                                    TableClassification.extraction_block_id == task.extraction_block_id
                                    ).one_or_none()
            if table_classification:
                data["table-classification"] = {
                    "field" : "Table Classification",
                    "value" : {
                        "is_true_table" : table_classification.is_true_table,
                        "is_heavily_redacted" : table_classification.is_heavily_redacted,
                        "is_complex_table" : table_classification.is_complex_table,
                        "false_table_type" : table_classification.false_table_type,
                        "final_section_type" : table_classification.final_section_type,
                    }
                }

        elif task.stage_name == Stages.attestation_extraction_agent:
            attestation_section = db.query(AttestationSection).filter(
                                    AttestationSection.extraction_block_id == task.extraction_block_id
                                    ).one_or_none()
            if attestation_section:
                data["attestation-section"] = {
                    "field" : "Attestation Section",
                    "value" : attestation_section.response
                }

        elif task.stage_name == Stages.content_extraction_using_ocr:
            # Writes a MarginaliaSection for marginalia blocks, a TextSection otherwise.
            ocr_section = db.query(TextSection).filter(
                                    TextSection.extraction_block_id == task.extraction_block_id
                                    ).one_or_none()
            if ocr_section:
                data["ocr-text-section"] = {
                    "field" : "Text Section (from OCR)",
                    "value" : ocr_section.response
                }
            else:
                ocr_marginalia = db.query(MarginaliaSection).filter(
                                    MarginaliaSection.extraction_block_id == task.extraction_block_id
                                    ).one_or_none()
                if ocr_marginalia:
                    data["ocr-marginalia-section"] = {
                        "field" : "Marginalia Section (from OCR)",
                        "value" : ocr_marginalia.response
                    }

        elif task.stage_name == Stages.text_extraction_agent:
            text_section = db.query(TextSection
                                        ).filter(
                                            TextSection.extraction_block_id == task.extraction_block_id
                                            ).one_or_none()
            if text_section:
                data["text-section"] = {
                    "field" : "Text Section",
                    "value" : text_section.response
                }

        elif task.stage_name == Stages.image_extraction_agent:
            image_section = db.query(ImageSection
                                        ).filter(
                                            ImageSection.extraction_block_id == task.extraction_block_id
                                            ).one_or_none()
            if image_section:
                data["image-section"] = {
                    "field" : "Image Section",
                    "value" : image_section.response
                }

        elif task.stage_name == Stages.marginalia_extraction_agent:
            marginalia_section = db.query(MarginaliaSection
                                        ).filter(
                                            MarginaliaSection.extraction_block_id == task.extraction_block_id
                                            ).one_or_none()
            if marginalia_section:
                data["marginalia-section"] = {
                    "field" : "Marginalia Section",
                    "value" : marginalia_section.response
                }

        elif task.stage_name in (
            Stages.table_extraction_agent,
            Stages.table_extraction_simple_agent,
            Stages.table_extraction_multipage_agent,
            Stages.table_extraction_multipage_simple_agent,
        ):
            table_section = db.query(TableSection
                                        ).filter(
                                            TableSection.extraction_block_id == task.extraction_block_id
                                            ).one_or_none()
            if table_section:
                data["extracted-section"] = {
                    "field" : "Extracted Table Content",
                    "value" : table_section.table_html
                }
                data["skip-verification"] = {
                    "field" : "Skip Verification",
                    "value" : table_section.skip_verification
                }
                if table_section.lineage_extraction_block_ids:
                    data["lineage-extraction-blocks"] = {
                        "field" : "Merged From Extraction Blocks",
                        "value" : table_section.lineage_extraction_block_ids
                    }

        elif task.stage_name == Stages.table_verification_agent:
            table_section = db.query(TableSection
                                        ).filter(
                                            TableSection.extraction_block_id == task.extraction_block_id
                                            ).one_or_none()
            if table_section:
                data["extracted-table"] = {
                    "field" : "Extracted Table Content",
                    "value" : table_section.table_html
                }
                data["verified-table"] = {
                    "field" : "Verified Table Content",
                    "value" : table_section.verified_html
                }
                data["skip-verification"] = {
                    "field" : "Skip Verification",
                    "value" : table_section.skip_verification
                }
        
        return data
    
    except Exception as e:
        return {"error" : str(e)}