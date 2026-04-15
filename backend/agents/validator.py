"""Validator Agent - Reviews and validates DXF metadata."""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Result of validation check."""

    is_valid: bool = Field(description="Whether the metadata is valid and ready for DXF generation")
    confidence_score: float = Field(description="Confidence score from 0.0 to 1.0")
    issues: List[str] = Field(default_factory=list, description="List of issues found")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    questions_for_user: List[str] = Field(default_factory=list, description="Questions to ask the user for clarification")
    summary: str = Field(description="Summary of the validation")


class ValidatorAgent:
    """Agent that validates extracted entities and formatted metadata."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert CAD quality assurance specialist. Your job is to validate DXF metadata.

Review the extracted entities and formatted metadata for:

1. **Completeness**: Are all entities properly defined with required parameters?
2. **Correctness**: Do coordinates and measurements make sense?
3. **Consistency**: Do entities relate to each other logically?
4. **Quality**: Is the description clear? Are layers properly assigned?
5. **Format compliance**: Does it match text_to_dxf requirements?

Check for common issues:
- Missing or invalid coordinates
- Impossible geometry (e.g., negative radius, invalid angles)
- Overlapping entities that shouldn't overlap
- Scale issues (values too large/small for typical use)
- Missing descriptions or layer assignments

Provide:
- A validation status (valid/invalid)
- Confidence score (0.0 to 1.0)
- List of specific issues found
- Actionable suggestions for improvement
- Questions to ask the user if clarification is needed
- A summary of the validation

Be thorough but constructive. If minor issues exist but the metadata is usable, mark as valid but note improvements."""),
            ("user", """Original User Input:
{user_input}

Extracted Entities:
{entities}

Formatted CSV Metadata:
{formatted_csv}

Please validate this metadata.""")
        ])

    def validate(self, user_input: str, entities: Dict[str, Any], formatted_csv: str) -> ValidationResult:
        """Validate the extracted entities and formatted metadata."""
        structured_llm = self.llm.with_structured_output(ValidationResult)
        chain = self.prompt | structured_llm
        result = chain.invoke({
            "user_input": user_input,
            "entities": str(entities),
            "formatted_csv": formatted_csv
        })
        return result

    def quick_validate(self, formatted_csv: str) -> bool:
        """Perform a quick syntax validation without LLM."""
        if not formatted_csv or formatted_csv.strip() == "":
            return False

        lines = formatted_csv.strip().split('\n')
        if len(lines) < 2:  # Need at least header and data
            return False

        # Basic format checking
        for i in range(0, len(lines), 3):  # Each entity is 3 lines (header, data, empty)
            if i >= len(lines):
                break
            header = lines[i].strip()
            if not (header.startswith('[') and header.endswith(']')):
                continue  # Skip if not a header
            if i + 1 < len(lines):
                data = lines[i + 1].strip()
                if not data:
                    return False

        return True
