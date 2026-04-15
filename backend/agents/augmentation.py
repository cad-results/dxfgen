"""Augmentation Agent - Modifies and enhances existing DXF metadata."""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from .entity_extractor import ExtractedEntities


class AugmentationRequest(BaseModel):
    """Structured augmentation request."""

    operation: str = Field(
        description="Type of operation: 'add', 'remove', 'modify', 'relocate', 'scale'"
    )
    target: str = Field(
        description="What to operate on (e.g., 'window', 'door', 'wall', 'furniture')"
    )
    details: str = Field(
        description="Specific details of the operation"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Operation parameters (dimensions, position, quantity, etc.)"
    )


class AugmentationResult(BaseModel):
    """Result of augmentation operation."""

    success: bool = Field(description="Whether augmentation was successful")
    modified_entities: ExtractedEntities = Field(description="Modified entities")
    changes_made: List[str] = Field(description="List of changes made")
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings or considerations"
    )
    summary: str = Field(description="Summary of augmentation")


class AugmentationAgent:
    """
    Agent that modifies existing DXF metadata based on user requests.

    Supports operations like:
    - Add: "add a window to the north wall"
    - Remove: "remove the small table"
    - Modify: "make the door wider"
    - Relocate: "move the bed to the opposite wall"
    - Scale: "make the room 20% larger"
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert CAD modification specialist. Your job is to intelligently modify existing DXF metadata based on user augmentation requests.

**Your Capabilities:**

1. **Add Operations**:
   - "add a window to the north wall" → Insert window entity with opening and frame
   - "add a table in the center" → Insert table polyline at calculated center
   - "add 2 more gears" → Duplicate and position gear entities

2. **Remove Operations**:
   - "remove the small table" → Identify and delete table entities
   - "remove all furniture" → Delete entities on Furniture layer
   - "remove the window from east wall" → Delete specific window entities

3. **Modify Operations**:
   - "make the door wider" → Adjust door width and opening size
   - "increase gear radius by 10mm" → Modify gear circle radii
   - "change wall thickness to 200mm" → Adjust wall line positions

4. **Relocate Operations**:
   - "move the bed to the opposite wall" → Calculate new position and update coordinates
   - "center the table" → Calculate center and reposition
   - "swap bedroom 1 and bedroom 2" → Exchange room positions

5. **Scale Operations**:
   - "make the room 20% larger" → Scale all entities by 1.2
   - "double the gear size" → Scale gear by 2.0
   - "shrink furniture by 10%" → Scale furniture entities by 0.9

**Process:**

1. **Parse Augmentation Request**:
   - Understand the operation type
   - Identify target entities (by description, layer, type)
   - Extract parameters (dimensions, positions, quantities)

2. **Analyze Existing Entities**:
   - Find affected entities
   - Understand spatial relationships
   - Check for dependencies (e.g., door in wall)

3. **Plan Modifications**:
   - Calculate new coordinates/dimensions
   - Ensure consistency (e.g., doors still in walls, furniture doesn't overlap walls)
   - Maintain professional standards

4. **Apply Changes**:
   - Modify entity parameters
   - Add new entities as needed
   - Remove entities as requested
   - Update descriptions and layers

5. **Validate Result**:
   - Ensure modifications are valid
   - Check for unintended side effects
   - Verify professional standards maintained

**Intelligence Guidelines:**

- **Contextual Understanding**: "north wall" means wall facing north, calculate which entities
- **Spatial Reasoning**: "opposite wall" means calculate opposite side of room
- **Standard Compliance**: New windows/doors follow professional dimensions
- **Consistency**: Modified elements maintain relationships (door swing with new width)
- **Smart Defaults**: "add a window" uses standard 1200×1200mm if not specified

**Example Augmentation:**

Request: "add a window to the north wall of the bedroom"

Analysis:
- Find bedroom entities (look for polylines or lines with "bedroom" in description)
- Identify north wall (top wall, highest Y coordinate)
- Calculate window position (center of wall)
- Use standard window size (1200mm wide)

Modifications:
- Add window opening (gap in wall lines)
- Add window frame marks (perpendicular lines at gap)
- Assign to "Windows" layer
- Update descriptions

Changes Made:
- "Added window opening (1200mm wide) to north wall of bedroom at X=2400, Y=4000"
- "Added window frame marks on Windows layer"

**Output Requirements:**

- Return complete modified ExtractedEntities (all entities, not just changed ones)
- List all specific changes made
- Provide warnings for potential issues
- Give clear summary

Be intelligent, maintain consistency, and follow professional CAD standards."""),
            ("user", """Augmentation Request:
{augmentation_request}

Current Entities:
{current_entities}

Original Design Context:
{original_description}

Please analyze and apply the requested augmentation.""")
        ])

    def augment(
        self,
        augmentation_request: str,
        current_entities: ExtractedEntities,
        original_description: str = ""
    ) -> AugmentationResult:
        """
        Apply augmentation to existing entities.

        Args:
            augmentation_request: Natural language augmentation request
            current_entities: Current entity set
            original_description: Original design description for context

        Returns:
            AugmentationResult with modified entities and change log
        """
        structured_llm = self.llm.with_structured_output(AugmentationResult)
        chain = self.prompt | structured_llm

        result = chain.invoke({
            "augmentation_request": augmentation_request,
            "current_entities": current_entities.model_dump(),
            "original_description": original_description
        })

        return result

    def parse_request(self, augmentation_request: str) -> AugmentationRequest:
        """Parse natural language augmentation request into structured format."""
        parse_prompt = ChatPromptTemplate.from_messages([
            ("system", """Parse the augmentation request into structured format.

Operations: 'add', 'remove', 'modify', 'relocate', 'scale'

Extract:
- operation type
- target entity
- details
- parameters (dimensions, position, etc.)"""),
            ("user", "{request}")
        ])

        structured_llm = self.llm.with_structured_output(AugmentationRequest)
        chain = parse_prompt | structured_llm

        result = chain.invoke({"request": augmentation_request})
        return result
