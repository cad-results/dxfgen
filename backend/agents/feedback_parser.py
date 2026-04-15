"""Feedback Parser Agent - Understands user corrections and applies targeted fixes."""

from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class FeedbackAction(BaseModel):
    """A specific action to take based on user feedback."""

    action_type: str = Field(description="Type of action: 'fix_dimension', 'change_property', 'add_entity', 'remove_entity', 'regenerate_all'")
    target_entity_type: Optional[str] = Field(default=None, description="Type of entity to modify: 'lines', 'circles', 'arcs', etc.")
    target_description_pattern: Optional[str] = Field(default=None, description="Pattern to match in entity descriptions (e.g., 'window', 'wall')")
    property_name: Optional[str] = Field(default=None, description="Property to modify (e.g., 'x2', 'y2', 'radius', 'layer')")
    new_value: Optional[str] = Field(default=None, description="New value to set (as string, will be converted to appropriate type)")
    reason: str = Field(description="Explanation of why this action is needed")


class ParsedFeedback(BaseModel):
    """Result of parsing user feedback."""

    feedback_type: str = Field(description="Type of feedback: 'fix_validation_issue', 'modify_design', 'clarify_requirement', 'accept_as_is'")
    user_intent: str = Field(description="What the user wants to achieve with this feedback")
    actions: List[FeedbackAction] = Field(default_factory=list, description="Specific actions to take")
    requires_regeneration: bool = Field(description="Whether entities need to be regenerated from scratch")
    context_update: str = Field(default="", description="Additional context to pass to entity extractor")
    summary: str = Field(description="Summary of the parsed feedback")


class FeedbackParserAgent:
    """
    Agent that parses user feedback and translates it into actionable fixes.

    This agent understands various types of user corrections:
    - Fixing validation issues (e.g., "make the window frames some length that fits")
    - Adjusting dimensions (e.g., "make walls thicker", "increase room size")
    - Changing properties (e.g., "move door to north wall", "change layer")
    - Clarifying requirements (e.g., "add a bathroom", "remove the garage")
    - Accepting current state (e.g., "wall thickness is ok", "looks good")
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at understanding user feedback and corrections for CAD drawings.

Your job is to parse user feedback and determine exactly what actions need to be taken to address their concerns.

**Types of Feedback:**

1. **fix_validation_issue**: User is responding to a validation error or question
   - Examples: "make the window frames some length that fits", "fix the wall thickness", "yes, adjust it"
   - Action: Apply targeted fixes to resolve validation issues
   - requires_regeneration: Usually False (can fix existing entities)

2. **modify_design**: User wants to change the design
   - Examples: "make the living room bigger", "move the door", "add a window on the east wall"
   - Action: Modify or add specific entities
   - requires_regeneration: Depends on scope (minor changes = False, major = True)

3. **clarify_requirement**: User is providing additional detail
   - Examples: "the house should have 4 bedrooms", "use metric units", "make it residential style"
   - Action: Update context and regenerate with new requirements
   - requires_regeneration: True

4. **accept_as_is**: User is accepting the current state
   - Examples: "the wall thickness is ok", "looks good", "that's fine", "no changes needed"
   - Action: Override validation warnings, mark as accepted
   - requires_regeneration: False

**Understanding Validation Issue Responses:**

When user responds to validation questions, determine what they want:

- "make X fit" / "make X standard" → Apply standard dimensions/values
- "fix X" / "correct X" → Apply automatic correction
- "X is ok" / "X is fine" → Accept current value, suppress future warnings
- "remove X" → Delete the problematic entities
- "make X [value]" → Set specific value

**Action Types:**

1. **fix_dimension**: Fix dimensional issues
   - For "make window frames some length": Set standard dimension (1200mm for windows)
   - For "make wall thickness standard": Set to 200mm for exterior, 150mm for interior

2. **change_property**: Change a specific property
   - target_entity_type: "lines", "circles", "arcs", "polylines", "hatches"
   - target_description_pattern: keyword to match (e.g., "window", "wall")
   - property_name: property to change (e.g., "layer", "radius")
   - new_value: new value to set

3. **add_entity**: Add new entity (triggers regeneration with context)

4. **remove_entity**: Remove entities matching pattern

5. **regenerate_all**: Regenerate everything with updated context

**Validation Issue Context:**

When parsing feedback, consider what validation issues were reported:
- Zero-length lines → User likely wants standard dimensions applied
- Wall thickness concerns → User likely wants standard architectural dimensions (150-200mm)
- Missing dimensions → User wants you to infer reasonable defaults

**Professional Standards to Apply:**

- Window frames: 1200mm × 1200mm (standard), can be horizontal or vertical
- Door frames: 900mm wide × 2100mm high (interior), 1000mm × 2100mm (exterior)
- Wall thickness: 150mm (interior), 200mm (exterior)
- Room dimensions: At least 2000mm × 2000mm (bathroom), 3000mm × 3000mm (bedroom)

**Output Guidelines:**

- feedback_type: Categorize the feedback
- user_intent: Clear statement of what user wants
- actions: List of specific, actionable steps
- requires_regeneration: True if need to regenerate entities from scratch
- context_update: Additional context to pass to entity extractor (if regenerating)
- summary: Brief explanation of what will be done

**Examples:**

Input: "make the window frames some length that fits"
Output:
- feedback_type: "fix_validation_issue"
- user_intent: "Apply standard dimensions to zero-length window frames"
- actions: [
    {{
      action_type: "fix_dimension",
      target_entity_type: "lines",
      target_description_pattern: "window",
      reason: "Zero-length window frames need standard 1200mm dimension"
    }}
  ]
- requires_regeneration: False (can fix in place)

Input: "the wall thickness is ok"
Output:
- feedback_type: "accept_as_is"
- user_intent: "Accept current wall thickness, suppress warnings"
- actions: []
- requires_regeneration: False

Input: "make it a 4 bedroom house instead"
Output:
- feedback_type: "clarify_requirement"
- user_intent: "Change design to have 4 bedrooms instead of current number"
- context_update: "Design should have 4 bedrooms"
- requires_regeneration: True

Be precise, actionable, and always consider the professional standards when interpreting vague requests."""),
            ("user", """User Feedback:
{feedback}

Previous Validation Issues:
{validation_issues}

Current Entities Summary:
{entities_summary}

Please parse this feedback and determine what actions to take.""")
        ])

    def parse(
        self,
        feedback: str,
        validation_issues: List[str] = None,
        entities_summary: str = ""
    ) -> ParsedFeedback:
        """
        Parse user feedback and determine actions.

        Args:
            feedback: User's feedback text
            validation_issues: List of validation issues that were reported
            entities_summary: Summary of current entities

        Returns:
            ParsedFeedback with actions to take
        """
        if validation_issues is None:
            validation_issues = []

        structured_llm = self.llm.with_structured_output(ParsedFeedback)
        chain = self.prompt | structured_llm

        result = chain.invoke({
            "feedback": feedback,
            "validation_issues": "\n".join(f"- {issue}" for issue in validation_issues) if validation_issues else "None",
            "entities_summary": entities_summary if entities_summary else "No entities yet"
        })

        return result
