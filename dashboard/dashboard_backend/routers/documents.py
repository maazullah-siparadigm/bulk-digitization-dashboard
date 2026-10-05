# routers/documents.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List

from dashboard_db import get_db
from operations import list_all_documents, create_document_tree, get_document_stats, change_task_status_in_db, get_stage_data_db, get_task_status_counts, get_batch_counts_by_model, get_requests_count_per_batch, get_document_counts, get_failed_tasks_by_document, get_token_aggregates, get_token_histograms, get_token_aggregates_by_agent_model, get_completed_pages_over_time, get_stage_models
from schemas import TaskStatusUpdate

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/document_counts")
def document_counts(db: Session = Depends(get_db)):
    try:
        document_stats = get_document_counts(db)
        print("Document stats...")
        print(document_stats)
        return document_stats
    except Exception as e:
        print("Exception in fetching data.")
        return {"error": f"Error {e}"}


@router.get("/failed_tasks_by_document")
def failed_tasks_by_document(db: Session = Depends(get_db)):
    try:
        return get_failed_tasks_by_document(db)
    except Exception as e:
        return {"error": f"Error {e}"}


@router.get("/all_documents")
def get_all_documents(page: int = 1, page_size: int = 50, db: Session = Depends(get_db)):
    try:
        return list_all_documents(db, page=page, page_size=page_size)
    except Exception as e:
        return {"error": f"Error {e}"}
    

@router.get("/document_info/{doc_id}")
def get_document_info(doc_id, db: Session = Depends(get_db)):
    if doc_id:
        try:
            doc_tree = create_document_tree(db, doc_id)
            doc_stats = get_document_stats(db, doc_id)
            return {"docTree" : doc_tree, "docStats" : doc_stats}
        except Exception as e:
            return HTTPException(status_code=401, detail=f"Error {e}")
    else:
        return HTTPException(status_code=401, detail=f"Document tree cannot be null.")


@router.post("/task_status_change")
def change_task_status(data: TaskStatusUpdate, db: Session = Depends(get_db)):
    try:
        resp = change_task_status_in_db(db, task_id=data.taskId, task_status=data.status)
        return resp

    except Exception as e:
        return HTTPException(status_code=401, detail=f"Error {e}")
    

@router.get("/task_status_counts")
def task_status_counts(db: Session = Depends(get_db)):
    try:
        return get_task_status_counts(db)
    except Exception as e:
        return {"error": f"Error {e}"}


@router.get("/stage_models")
def stage_models():
    try:
        return get_stage_models()
    except Exception as e:
        return {"error": f"Error {e}"}


@router.get("/batch_counts_by_model")
def batch_counts_by_model(db: Session = Depends(get_db)):
    try:
        return get_batch_counts_by_model(db)
    except Exception as e:
        return {"error": f"Error {e}"}


@router.get("/requests_count_per_batch")
def requests_count_per_batch(db: Session = Depends(get_db)):
    try:
        return get_requests_count_per_batch(db)
    except Exception as e:
        return {"error": f"Error {e}"}


@router.get("/token_aggregates")
def token_aggregates(db: Session = Depends(get_db)):
    try:
        return get_token_aggregates(db)
    except Exception as e:
        return {"error": f"Error {e}"}


@router.get("/token_histograms")
def token_histograms(group_by: str = None, db: Session = Depends(get_db)):
    if group_by not in ("model", "agent"):
        raise HTTPException(status_code=400, detail="group_by must be 'model' or 'agent'")
    try:
        return get_token_histograms(db, group_by)
    except Exception as e:
        return {"error": f"Error {e}"}


@router.get("/token_aggregates_by_agent_model")
def token_aggregates_by_agent_model(db: Session = Depends(get_db)):
    try:
        return get_token_aggregates_by_agent_model(db)
    except Exception as e:
        return {"error": f"Error {e}"}


@router.get("/completed_pages_over_time")
def completed_pages_over_time(window_days: int = None, granularity: str = None, db: Session = Depends(get_db)):
    if window_days not in (1, 2, 3, 5, 7):
        raise HTTPException(status_code=400, detail="window_days must be one of 1, 2, 3, 5, 7")
    if granularity not in ("hour", "day"):
        raise HTTPException(status_code=400, detail="granularity must be 'hour' or 'day'")
    try:
        return get_completed_pages_over_time(db, window_days, granularity)
    except Exception as e:
        return {"error": f"Error {e}"}


@router.get("/get_stage_data/{task_id}")
def get_stage_data(task_id, db: Session = Depends(get_db)):
    try:
        resp = get_stage_data_db(db, task_id)
        return resp

    except Exception as e:
        return HTTPException(status_code=401, detail=f"Error {e}")

# @router.get("/{doc_id}", response_model=DocumentResponse)
# def get_document(doc_id: int, db: Session = Depends(get_db)):
#     document = db.query(Document).filter(Document.id == doc_id).first()

#     if not document:
#         raise HTTPException(status_code=404, detail="Document not found")

#     return document