from pydantic import BaseModel

class TaskStatusUpdate(BaseModel):
    taskId: str
    status: str