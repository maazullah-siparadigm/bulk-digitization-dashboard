from pydantic import BaseModel, Field
from typing import List, Literal, Union, Any, Optional

from LLMBatcher.common.myenums import NodeTypes, TaskTypes,ThinkingLevels

class IOSchema(BaseModel):
    name: str
    type: str
    crumb : str = ""
    value: Union[List["IOSchema"], str, int, float, bool, None] = None

class LLMConfig(BaseModel):
    node_type: Literal[NodeTypes.llm] = NodeTypes.llm

    system_prompt: str
    human_prompt: str
    model_name: str
    temperature: float
    multi_instance: bool = Field(default=False)

class CodeConfig(BaseModel):
    node_type: Literal[NodeTypes.code] = NodeTypes.code

class ComputeConfig(BaseModel):
    node_type: Literal[NodeTypes.compute] = NodeTypes.compute
    queue: str
    
class NodeConfig(BaseModel):
    name: str
    node_type: NodeTypes
    children_nodes: List[str]
    inputs: List[IOSchema] = Field(default_factory=list)
    outputs: List[IOSchema] = Field(default_factory=list)

    node_config: Union[LLMConfig, CodeConfig, ComputeConfig] = Field(discriminator = "node_type")

class AgentConfig(BaseModel):
    task_type: Literal[TaskTypes.agent] = TaskTypes.agent

    system_prompt: str
    human_prompt: str
    model_name: str
    temperature: Optional[float] = None
    thinking_budget: Optional[int]=None
    thinking_level: Optional[ThinkingLevels] = None  # default OFF
    response_json_schema : Optional[dict] = None
    max_output_tokens: Optional[int] = None

class ComputeConfig(BaseModel):
    task_type: Literal[TaskTypes.compute] = TaskTypes.compute
    queue: str

class TaskConfig(BaseModel):
    name: str
    task_type: TaskTypes

    task_config: Union[AgentConfig, ComputeConfig] = Field(discriminator = "task_type")