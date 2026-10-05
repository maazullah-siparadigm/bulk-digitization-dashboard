from LLMBatcher.executors.db.models import Task, Document, Batch, \
                                           LLMRequest, Response, BatchRequest, \
                                           Page
from LLMBatcher.common.myenums import TaskStatus, TaskTypes, Stages, BatchStatus
from LLMBatcher.configs.stage_configs import get_agent_config
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, distinct, and_, or_
from utilities import populate_doc_tree, get_data_associated_with_task
from histogram import build_group_histograms, TOKEN_TYPES
from datetime import datetime, timedelta, timezone



def list_all_documents(db: Session, page: int = 1, page_size: int = 50):
    total = db.query(func.count(Document.id)).scalar()

    offset = (page - 1) * page_size
    documents = db.query(Document).offset(offset).limit(page_size).all()

    # Only fetch failed-task counts for the documents on this page, scoped by the
    # indexed document_id, instead of scanning every failed task in the table.
    doc_ids = [document.id for document in documents]
    failed_counts = {}
    if doc_ids:
        failed_counts = dict(
            db.query(Task.document_id, func.count(Task.id))
            .filter(Task.document_id.in_(doc_ids), Task.status == TaskStatus.failed)
            .group_by(Task.document_id)
            .all()
        )

    documents_list = [
        {
            "id": document.id,
            "title": document.document_name,
            "farthestStage": "",
            "lowestStage": "",
            "digitized": "Yes" if document.digitization_completed else "No",
            "failed_tasks": failed_counts.get(document.id, 0),
        }
        for document in documents
    ]

    documents_list = sorted(documents_list, key=lambda x: x["failed_tasks"], reverse=True)

    return {"documents": documents_list, "total": total, "page": page, "page_size": page_size}

def create_document_tree(db: Session, doc_id):
    # Eager-load each task's page so populate_doc_tree's `task.page.page_index`
    # access does not trigger a separate lazy query per task (N+1).
    all_document_tasks = (
        db.query(Task)
        .options(joinedload(Task.page))
        .filter(Task.document_id == doc_id, Task.invalidate_chain == False)
        .all()
    )

    tasks_dict = {}

    start_task = None
    for doc_task in all_document_tasks:
        tasks_dict[doc_task.id] = {"task" : doc_task, "parents" : [], "children" : []}
        if not doc_task.parent_task_id:
            start_task = doc_task 

    for idx, doc_task in enumerate(all_document_tasks):
        if doc_task.parent_task_id:
            tasks_dict[doc_task.parent_task_id]["children"].append(doc_task.id)
            tasks_dict[doc_task.id]["parents"].append(doc_task.parent_task_id)
    #     print(f"{idx + 1} / {len(all_document_tasks)}")
    # print("HERE")

    # build_page_pairs and build_cross_page_hierarchy are document-level (they belong to
    # no single page) but are parented under one arbitrary task of the previous stage -
    # page_barrier_worker so the lineage walk can see them, the orchestrator's generic
    # spawn for the hierarchy. Drawn as-is they land inside one page's lane. Display
    # only: hoist them to the root and flag them so the viewer lays each out in its own
    # column after the page lanes, fed by every task of the stage that precedes it.
    # Listed in pipeline order - the viewer places them left to right in this order.
    document_level_stages = (
        (Stages.build_page_pairs, Stages.annotate_image),
        (Stages.build_cross_page_hierarchy, Stages.link_page_continuity_agent),
    )
    sources_by_task = {}
    for stage, source_stage in document_level_stages:
        source_ids = [t.id for t in all_document_tasks if t.stage_name == source_stage]
        for doc_task in all_document_tasks:
            if doc_task.stage_name == stage and doc_task.parent_task_id in tasks_dict:
                tasks_dict[doc_task.parent_task_id]["children"].remove(doc_task.id)
                tasks_dict[start_task.id]["children"].append(doc_task.id)
                sources_by_task[doc_task.id] = source_ids

    doc_tree = populate_doc_tree(start_task.id, tasks_dict)
    for child in doc_tree["children"]:
        if child["id"] in sources_by_task:
            child["document_level"] = True
            child["source_ids"] = sources_by_task[child["id"]]

    return doc_tree

def get_document_stats(db: Session, doc_id):
    total_tasks = db.query(Task).filter(Task.document_id == doc_id, Task.invalidate_chain == False).count()
    num_pending = db.query(Task).filter(Task.document_id == doc_id, Task.status == TaskStatus.pending, Task.invalidate_chain == False).count()
    num_failed = db.query(Task).filter(Task.document_id == doc_id, Task.status == TaskStatus.failed, Task.invalidate_chain == False).count()
    num_completed = db.query(Task).filter(Task.document_id == doc_id, Task.status == TaskStatus.completed, Task.invalidate_chain == False).count()
    
    num_agentic_calls = db.query(Task).filter(Task.document_id == doc_id, Task.task_type == TaskTypes.agent, Task.invalidate_chain == False).count()
    
    doc = db.query(Document).filter(Document.id == doc_id).one_or_none()

    num_pages = 0
    if doc:
        num_pages = doc.num_pages


    return {
        "numPages" : num_pages,
        "totalTasks" : total_tasks,
        "numPending" : num_pending,
        "numFailed" : num_failed,
        "numCompleted" : num_completed,
        "numAgenticCalls" : num_agentic_calls,
    }


def change_task_status_in_db(db: Session, task_id, task_status: TaskStatus):
    try:
        task = db.query(Task).filter(Task.id == task_id).one_or_none()
        task.status = task_status
        db.commit()

        return {"success" : True, "status" : task.status}

    except Exception as e:
        raise Exception(f"Could not find the selected task - {e}")
    

def get_task_status_counts(db: Session):
    rows = (
        db.query(Task.stage_name, Task.status, func.count(Task.id))
        .filter(Task.invalidate_chain == False)
        .group_by(Task.stage_name, Task.status)
        .all()
    )

    all_statuses = [s.value for s in TaskStatus]
    result = {stage.value: {s: 0 for s in all_statuses} for stage in Stages}

    for stage_name, status, count in rows:
        result[stage_name.value][status.value] = count

    return result


def get_failed_tasks_by_document(db: Session):
    rows = (
        db.query(Task.id, Task.document_id, Document.document_name, Task.stage_name, Task.task_type, Task.failure_message)
        .join(Document, Task.document_id == Document.id)
        .filter(Task.status == TaskStatus.failed, Task.invalidate_chain == False)
        .all()
    )

    # Collect agent task IDs that have no failure_message so we can batch-fetch their Response error
    agent_task_ids = [
        task_id for task_id, _, _, _, task_type, failure_message in rows
        if task_type == TaskTypes.agent and failure_message is None
    ]

    # Single query: Task -> LLMRequest -> Response
    response_errors = {}
    if agent_task_ids:
        error_rows = (
            db.query(LLMRequest.task_id, Response.error_message)
            .join(Response, Response.llm_request_id == LLMRequest.id)
            .filter(LLMRequest.task_id.in_(agent_task_ids))
            .all()
        )
        response_errors = {str(task_id): error_message for task_id, error_message in error_rows}

    result = {}
    for task_id, document_id, document_name, stage_name, task_type, failure_message in rows:
        key = str(document_id)
        if key not in result:
            result[key] = {"name": document_name, "failed_tasks": []}

        if task_type == TaskTypes.agent and failure_message is None:
            failure_message = response_errors.get(str(task_id))

        result[key]["failed_tasks"].append({
            "stage_name": stage_name.value,
            "failure_message": failure_message,
        })

    return result


def get_document_counts(db: Session):
    print("finding document stats...")
    total = db.query(func.count(Document.id)).scalar()
    completed = db.query(func.count(Document.id)).filter(Document.digitization_completed == True).scalar()
    # Count distinct documents that have a failed (non-invalidated) task directly,
    # instead of building the full per-document failure structure just to len() it.
    digitization_failed = (
        db.query(func.count(distinct(Task.document_id)))
        .filter(Task.status == TaskStatus.failed, Task.invalidate_chain == False)
        .scalar()
    )

    total_pages = db.query(func.count(Page.id)).scalar()

    completed_pages = 0

    
    failed_page_ids = (
            db.query(Task.page_id)
            .filter(Task.status == TaskStatus.failed, Task.invalidate_chain == False, Task.page_id.isnot(None))
        )
    # Compute "completed" pages with one grouped query instead of a per-page loop.
    # Grouping each page's tasks, it's completed when it has no failed (non-invalidated)
    # task AND either the router spawned nothing but an END/COMPLETED task exists, or the
    # router-spawned count equals the END/COMPLETED count.
    originated = func.count(Task.id).filter(Task.prev_stage_name == Stages.router)
    end_completed = func.count(Task.id).filter(
        and_(Task.stage_name == Stages.end, Task.status == TaskStatus.completed)
    )
    failed_in_page = func.count(Task.id).filter(
        and_(Task.status == TaskStatus.failed, Task.invalidate_chain == False)
    )

    # The predicate only depends on these three kinds of tasks, so scan just those
    # rows before grouping. Pages with none of them can't be "completed" anyway.
    relevant_task = or_(
        Task.prev_stage_name == Stages.router,
        and_(Task.stage_name == Stages.end, Task.status == TaskStatus.completed),
        and_(Task.status == TaskStatus.failed, Task.invalidate_chain == False),
    )

    completed_page_groups = (
        db.query(Task.page_id)
        .filter(Task.page_id.isnot(None), relevant_task)
        .group_by(Task.page_id)
        .having(and_(
            failed_in_page == 0,
            or_(
                and_(originated == 0, end_completed > 0),
                and_(originated > 0, originated == end_completed),
            ),
        ))
        .subquery()
    )
    completed_pages = db.query(func.count()).select_from(completed_page_groups).scalar()

    failed_pages = failed_page_ids.count()

    return {"total": total, 
            "completed": completed, 
            "digitization_failed": digitization_failed,
            "total_pages" : total_pages,
            "completed_pages" : completed_pages,
            "failed_pages" : failed_pages
            }


def get_batch_counts_by_model(db: Session):
    rows = (
        db.query(Batch.model_name, Batch.status, func.count(Batch.id))
        .group_by(Batch.model_name, Batch.status)
        .all()
    )

    all_statuses = [s.value for s in BatchStatus]

    result = {}
    for model_name, status, count in rows:
        key = model_name or "unknown"
        if key not in result:
            result[key] = {s: 0 for s in all_statuses}
        result[key][status.value] = count

    return result


def get_requests_count_per_batch(db: Session):
    batches = (
        db.query(Batch.id, Batch.model_name, Batch.status, Batch.requests_count)
        .order_by(Batch.created_time.desc())
        .all()
    )

    return [
        {
            "batch_id": str(batch_id),
            "model_name": model_name or "unknown",
            "status": status.value,
            "requests_count": requests_count,
        }
        for batch_id, model_name, status, requests_count in batches
    ]


def get_stage_data_db(db: Session, task_id):
    try:
        task = db.query(Task).filter(Task.id == task_id).one_or_none()
        if task:
            return get_data_associated_with_task(task, db)
        else:
            return {"error" : "Task does not exist"}

    except Exception as e:
        raise Exception(f"Could not find the task data - {e}")


def get_token_aggregates(db: Session) -> dict[str, dict[str, int]]:
    # Aggregated from the small `batches` table (hundreds of rows), which already
    # stores per-batch token sums. This avoids scanning the multi-GB `responses`
    # table and is ~170x faster. Counts tokens that went through batches.
    rows = (
        db.query(
            Batch.model_name,
            func.coalesce(func.sum(Batch.total_input_tokens), 0),
            func.coalesce(func.sum(Batch.output_text_tokens), 0),
            func.coalesce(func.sum(Batch.output_thinking_tokens), 0),
        )
        .group_by(Batch.model_name)
        .all()
    )

    result = {}
    for model_name, input_tokens, output_tokens, thinking_tokens in rows:
        result[model_name or "unknown"] = {
            "input_tokens": int(input_tokens or 0),
            "output_tokens": int(output_tokens or 0),
            "thinking_tokens": int(thinking_tokens or 0),
        }

    return result


def get_token_histograms(db: Session, group_by: str) -> dict[str, dict[str, list[dict]]]:
    if group_by not in ("model", "agent"):
        raise ValueError("group_by must be 'model' or 'agent'")

    token_columns = (
        Response.total_input_tokens,
        Response.output_text_tokens,
        Response.output_thinking_tokens,
    )

    if group_by == "model":
        query = (
            db.query(Batch.model_name, *token_columns)
            .select_from(Response)
            .outerjoin(BatchRequest, Response.batch_request_id == BatchRequest.id)
            .outerjoin(Batch, BatchRequest.batch_id == Batch.id)
            .filter(Response.total_tokens.isnot(None))
        )
    else:  # "agent"
        query = (
            db.query(LLMRequest.stage_name, *token_columns)
            .select_from(Response)
            .join(LLMRequest, Response.llm_request_id == LLMRequest.id)
            .filter(Response.total_tokens.isnot(None))
        )

    grouped = {}
    for group_value, input_tokens, output_tokens, thinking_tokens in query.all():
        if group_by == "model":
            key = group_value or "unknown"
        else:
            key = group_value.value  # Stages enum -> "OCR", "TABLE_EXTRACTION_AGENT", ...

        bucket = grouped.setdefault(key, {tt: [] for tt in TOKEN_TYPES})
        bucket["input_tokens"].append(int(input_tokens or 0))
        bucket["output_tokens"].append(int(output_tokens or 0))
        bucket["thinking_tokens"].append(int(thinking_tokens or 0))

    return {key: build_group_histograms(values) for key, values in grouped.items()}


def get_token_aggregates_by_agent_model(db: Session) -> dict[str, dict[str, dict[str, int]]]:
    rows = (
        db.query(
            LLMRequest.stage_name,
            func.coalesce(func.sum(Response.total_input_tokens), 0),
            func.coalesce(func.sum(Response.output_text_tokens), 0),
            func.coalesce(func.sum(Response.output_thinking_tokens), 0),
        )
        .select_from(Response)
        .join(LLMRequest, Response.llm_request_id == LLMRequest.id)
        .filter(Response.total_tokens.isnot(None))
        .group_by(LLMRequest.stage_name)
        .all()
    )

    result = {}
    for stage_name, input_tokens, output_tokens, thinking_tokens in rows:
        # Model name comes from the stage config (the model that agent is configured to use),
        # not from Batch.model_name. Compute/non-agent stages have no model -> "unknown".
        agent_config = get_agent_config(stage_name)
        model_name = agent_config.model_name if agent_config else "unknown"

        result[stage_name.value] = {
            model_name: {
                "input_tokens": int(input_tokens or 0),
                "output_tokens": int(output_tokens or 0),
                "thinking_tokens": int(thinking_tokens or 0),
            }
        }

    return result


def get_completed_pages_over_time(db: Session, window_days: int, granularity: str) -> dict:
    # A page is "completed" (matching the manual per-page method) when it has no
    # failed task AND either:
    #   - the router spawned no tasks for it AND it has an END/COMPLETED task, or
    #   - the router-spawned task count equals its END/COMPLETED task count.
    # The page's completion time is the latest END/COMPLETED task's updated_time.
    # The whole thing is done as one grouped aggregate instead of a per-page loop.
    step = timedelta(hours=1) if granularity == "hour" else timedelta(days=1)

    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc - timedelta(days=window_days)

    now_naive = now_utc.replace(tzinfo=None)
    if granularity == "hour":
        truncate = lambda d: d.replace(minute=0, second=0, microsecond=0)
    else:
        truncate = lambda d: d.replace(hour=0, minute=0, second=0, microsecond=0)
    last_bucket = truncate(now_naive)
    first_bucket = truncate(cutoff.replace(tzinfo=None))

    end_completed = and_(Task.stage_name == Stages.end, Task.status == TaskStatus.completed)
    latest_end = func.max(Task.updated_time).filter(end_completed)

    # Per-page aggregates over all of the page's tasks. HAVING keeps only pages
    # whose latest completion falls inside the requested window.
    rows = (
        db.query(
            func.count(Task.id).filter(Task.prev_stage_name == Stages.router).label("originated"),
            func.count(Task.id).filter(end_completed).label("end_completed"),
            func.count(Task.id).filter(and_(Task.status == TaskStatus.failed, Task.invalidate_chain == False)).label("failed_count"),
            latest_end.label("latest_end"),
        )
        .filter(Task.page_id.isnot(None))
        .group_by(Task.page_id)
        .having(latest_end >= cutoff)
        .all()
    )

    counts = {}
    for originated, end_completed_count, failed_count, latest in rows:
        if failed_count > 0:
            continue
        is_completed = (
            (originated == 0 and end_completed_count > 0)
            or (originated > 0 and originated == end_completed_count)
        )
        if not is_completed:
            continue

        # latest is the page's newest END/COMPLETED task time; normalize to naive UTC.
        latest_naive = latest.astimezone(timezone.utc).replace(tzinfo=None) if latest.tzinfo else latest
        bucket = truncate(latest_naive)
        counts[bucket] = counts.get(bucket, 0) + 1

    data = []
    current = first_bucket
    while current <= last_bucket:
        data.append({"timestamp": current.isoformat(), "count": int(counts.get(current, 0))})
        current += step

    return {"granularity": granularity, "data": data}



def get_stage_models() -> dict:
    # Stage name -> the model its agent is configured with. Compute stages have no
    # model and are left out, so callers can treat a missing key as "other".
    result = {}
    for stage in Stages:
        agent_config = get_agent_config(stage)
        if agent_config:
            result[stage.value] = agent_config.model_name
    return result
