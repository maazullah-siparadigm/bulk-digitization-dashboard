from LLMBatcher.executors.db.models import Task, Document, Page \
                                         , OCRResult, QualityCheck, Section \
                                         , SpanningSectionResponse, SemanticSectionGroup \
                                         , ExtractionSectionBlock, TextSection \
                                         , MarginaliaSection, TableSection, ImageSection
from LLMBatcher.common.myenums import Stages, TaskStatus
from sqlalchemy.orm import Session

def populate_doc_tree(task_id, task_dict: dict):
    page_num = None
    
    if task_dict[task_id]["task"].page:
        page_num = f" Page {task_dict[task_id]['task'].page.page_index}"
    task_name = " ".join(task_dict[task_id]["task"].stage_name.split("_"))
    node_dict = {
        "id" : task_id,
        "type" : task_dict[task_id]["task"].task_type,
        "name" : task_name,
        "pade_index" : page_num,
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
                "value" : [f"{sec.label} | {sec.section_type} | {sec.section_id}" for sec in all_sections]
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

        elif task.stage_name == Stages.router:
            num_children = db.query(Task).filter(Task.page_id == task.page_id, Task.invalidate_chain == False, Task.parent_task_id == task.id).count()
            data["num-children"] = {
                "field" : "Num. Children Spawned",
                "value" : num_children
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

        elif task.stage_name == Stages.table_extraction_agent:
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