from typing import List, Literal, Annotated, Optional
from pydantic import BaseModel, Field
from LLMBatcher.common.myenums import FalseTableTypes

class TableClassification(BaseModel):
    is_heavily_redacted: bool = Field(
        description="True if more than 50% of the visible cell area is obscured by redaction marks"
    )
    is_true_table: bool = Field(
        description="True if a genuine 2-D matrix where columns have independent analytical meaning and cells depend on both row AND column"
    )
    is_complex_table: bool = Field(
        description="True if the table has merged/spanned cells, multi-level headers, row-group headers, or nested tables. Always false when is_true_table is false."
    )
    false_table_type: Optional[FalseTableTypes] = Field(
        default=None,
        description="'list' for wrapped/snaking lists; 'kvp' for label-value pair blocks; "
                    "'list_with_selection' for a list where each item also carries a checkbox/"
                    "radio/tick-box or other selection marker. Null when is_true_table is true."
    )


table_classification_schema = TableClassification.model_json_schema()