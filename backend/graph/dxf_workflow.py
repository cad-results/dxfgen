"""LangGraph workflow for DXF metadata generation with feedback loops and specialist agents."""

from typing import TypedDict, Annotated, Literal, Optional
from typing_extensions import NotRequired
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import os

from ..agents import (
    IntentParserAgent,
    EntityExtractorAgent,
    MetadataFormatterAgent,
    ValidatorAgent,
    DetailRefinementAgent,
    FloorPlanSpecialistAgent,
    MechanicalSpecialistAgent,
    AutoValidatorAgent,
    FeedbackParserAgent
)
from ..agents.curve_specialist import CurveSpecialistAgent
from ..agents.advanced_curve_specialist import AdvancedCurveSpecialistAgent
from ..agents.research_agent import ResearchAgent
from ..settings import UserSettings


class WorkflowState(TypedDict):
    """State for the DXF generation workflow."""

    # Messages history
    messages: Annotated[list, add_messages]

    # User input
    user_input: str
    original_user_input: NotRequired[str]  # Store original before refinement

    # User settings
    settings: NotRequired[dict]  # UserSettings as dict
    auto_accept_mode: NotRequired[bool]

    # Agent outputs
    intent: NotRequired[dict]
    refinement_result: NotRequired[dict]  # From DetailRefinementAgent
    refined_description: NotRequired[str]  # Final refined description
    entities: NotRequired[dict]
    formatted_csv: NotRequired[str]
    validation: NotRequired[dict]
    auto_fixes_log: NotRequired[list]  # Log of auto-fixes applied

    # Research data
    research_data: NotRequired[dict]  # From ResearchAgent
    requires_research: NotRequired[bool]

    # Workflow control
    iteration_count: NotRequired[int]
    max_iterations: NotRequired[int]
    requires_user_feedback: NotRequired[bool]
    is_complete: NotRequired[bool]

    # Routing control
    specialist_domain: NotRequired[str]  # 'floorplan', 'mechanical', 'general'
    needs_refinement: NotRequired[bool]

    # Validation memory
    validation_history: NotRequired[list]  # List of all validation issues encountered
    accepted_warnings: NotRequired[list]  # List of warnings user has accepted
    feedback_history: NotRequired[list]  # List of user feedback and actions taken


class DXFWorkflow:
    """LangGraph workflow for conversational DXF generation."""

    def __init__(self, openai_api_key: str, model: str = "gpt-4-turbo-preview"):
        self.api_key = openai_api_key
        self.model = model

        # Initialize LLM
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model=model,
            temperature=0.7
        )

        # Initialize original agents
        self.intent_parser = IntentParserAgent(self.llm)
        self.entity_extractor = EntityExtractorAgent(self.llm)
        self.metadata_formatter = MetadataFormatterAgent(self.llm)
        self.validator = ValidatorAgent(self.llm)

        # Initialize new agents
        self.detail_refinement = DetailRefinementAgent(self.llm)
        self.floorplan_specialist = FloorPlanSpecialistAgent(self.llm)
        self.mechanical_specialist = MechanicalSpecialistAgent(self.llm)
        self.curve_specialist = CurveSpecialistAgent(self.llm)
        self.advanced_curve_specialist = AdvancedCurveSpecialistAgent(self.llm)
        self.research_agent = ResearchAgent(self.llm)
        self.auto_validator = AutoValidatorAgent(self.llm)
        self.feedback_parser = FeedbackParserAgent(self.llm)

        # Build graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the enhanced LangGraph workflow with refinement and specialists."""

        # Define the graph
        workflow = StateGraph(WorkflowState)

        # Add nodes
        workflow.add_node("parse_intent", self._parse_intent_node)
        workflow.add_node("research", self._research_node)
        workflow.add_node("refine_details", self._refine_details_node)
        workflow.add_node("extract_entities_general", self._extract_entities_general_node)
        workflow.add_node("extract_entities_floorplan", self._extract_entities_floorplan_node)
        workflow.add_node("extract_entities_mechanical", self._extract_entities_mechanical_node)
        workflow.add_node("extract_entities_curves", self._extract_entities_curves_node)
        workflow.add_node("extract_entities_advanced_curves", self._extract_entities_advanced_curves_node)
        workflow.add_node("format_metadata", self._format_metadata_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("ask_feedback", self._ask_feedback_node)

        # Set entry point
        workflow.set_entry_point("parse_intent")

        # Conditional edge from parse_intent: research, refinement, or extraction?
        workflow.add_conditional_edges(
            "parse_intent",
            self._route_after_intent,
            {
                "research": "research",
                "refine": "refine_details",
                "extract_entities_general": "extract_entities_general",
                "extract_entities_floorplan": "extract_entities_floorplan",
                "extract_entities_mechanical": "extract_entities_mechanical",
                "extract_entities_curves": "extract_entities_curves",
                "extract_entities_advanced_curves": "extract_entities_advanced_curves"
            }
        )

        # After research, route to appropriate specialist
        workflow.add_conditional_edges(
            "research",
            self._route_after_research,
            {
                "refine": "refine_details",
                "extract_entities_general": "extract_entities_general",
                "extract_entities_floorplan": "extract_entities_floorplan",
                "extract_entities_mechanical": "extract_entities_mechanical",
                "extract_entities_curves": "extract_entities_curves",
                "extract_entities_advanced_curves": "extract_entities_advanced_curves"
            }
        )

        # After refinement, route to appropriate specialist
        workflow.add_conditional_edges(
            "refine_details",
            self._route_to_specialist,
            {
                "floorplan": "extract_entities_floorplan",
                "mechanical": "extract_entities_mechanical",
                "curves": "extract_entities_curves",
                "advanced_curves": "extract_entities_advanced_curves",
                "general": "extract_entities_general"
            }
        )

        # All extraction paths lead to format_metadata
        workflow.add_edge("extract_entities_general", "format_metadata")
        workflow.add_edge("extract_entities_floorplan", "format_metadata")
        workflow.add_edge("extract_entities_mechanical", "format_metadata")
        workflow.add_edge("extract_entities_curves", "format_metadata")
        workflow.add_edge("extract_entities_advanced_curves", "format_metadata")

        workflow.add_edge("format_metadata", "validate")

        # Conditional edge from validate
        workflow.add_conditional_edges(
            "validate",
            self._should_continue,
            {
                "complete": END,
                "feedback": "ask_feedback",
                "retry": "extract_entities_general"
            }
        )

        workflow.add_edge("ask_feedback", END)

        return workflow.compile()

    def _parse_intent_node(self, state: WorkflowState) -> WorkflowState:
        """Parse user intent and determine if refinement or specialist is needed."""
        intent = self.intent_parser.parse(state["user_input"])
        state["intent"] = intent.model_dump()
        state["needs_refinement"] = intent.needs_refinement
        state["specialist_domain"] = intent.specialist_domain
        state["requires_research"] = intent.requires_research
        state["original_user_input"] = state.get("original_user_input", state["user_input"])

        # Build status message
        status_parts = [f"I understand you want to create: {intent.description}"]
        status_parts.append(f"Main entities: {', '.join(intent.main_entities)}")

        if intent.requires_curves:
            status_parts.append(f"Curve types needed: {intent.curve_type_hint or 'bspline'}")

        if intent.requires_research:
            status_parts.append(f"Research required: {intent.research_query}")

        if intent.needs_refinement and not state.get("auto_accept_mode", False):
            status_parts.append(f"Refinement needed: {intent.refinement_reason}")

        state["messages"].append(AIMessage(content="\n".join(status_parts)))
        return state

    def _research_node(self, state: WorkflowState) -> WorkflowState:
        """Perform comprehensive web research for specifications and details.

        This node performs:
        1. Built-in database lookup
        2. Google/web search for specifications
        3. PDF catalog download and extraction
        4. Image analysis for technical drawings
        5. Cross-reference multiple sources
        """
        intent = state.get("intent", {})
        user_input = state["user_input"]
        research_query = intent.get("research_query", user_input)

        state["messages"].append(
            AIMessage(content=f"Researching: {research_query}...")
        )

        # Extract part number if present
        import re
        part_number = ""
        part_patterns = [
            r'\b([A-Z]{2,3}[\d-]+[A-Z]?)\b',  # OP22-0002L
            r'\b(\d{6,})\b',  # 168255
            r'\b(\d+-\d+)\b',  # 00-719255
        ]
        for pattern in part_patterns:
            match = re.search(pattern, user_input.upper())
            if match:
                part_number = match.group(1)
                state["messages"].append(
                    AIMessage(content=f"Detected part number: {part_number}")
                )
                break

        # Perform comprehensive research
        research_result = self.research_agent.research_with_fallback(
            research_query,
            str(intent)
        )

        # Log research process
        research_log = research_result.get("research_log", [])
        if research_log:
            log_summary = "\n".join([f"  - {log}" for log in research_log[:5]])
            state["messages"].append(
                AIMessage(content=f"Research steps:\n{log_summary}")
            )

        # If we found a catalog URL and part number, do targeted search
        specs = research_result.get("specifications", {})
        catalog_url = specs.get("catalog_url")
        if catalog_url and part_number:
            state["messages"].append(
                AIMessage(content=f"Searching catalog: {catalog_url}")
            )
            catalog_result = self.research_agent.search_catalog_for_part(
                catalog_url, part_number
            )
            if catalog_result.get("found"):
                # Merge catalog specs with existing
                catalog_specs = catalog_result.get("specifications", {})
                if catalog_specs:
                    specs.update(catalog_specs)
                    research_result["specifications"] = specs
                    research_result["sources"].append(f"Catalog: {catalog_url}")

        state["research_data"] = research_result

        # Report findings
        if specs:
            sources = research_result.get("sources", ["unknown"])
            confidence = research_result.get("confidence", "medium")

            msg_parts = [f"Research complete (confidence: {confidence})"]

            # List sources
            if sources:
                msg_parts.append(f"Sources: {', '.join(sources[:3])}")

            # Product info
            if specs.get("name"):
                msg_parts.append(f"Product: {specs['name']}")
            if specs.get("manufacturer"):
                msg_parts.append(f"Manufacturer: {specs['manufacturer']}")
            if specs.get("material"):
                msg_parts.append(f"Material: {specs['material']}")

            # Extract key dimensions
            dims = specs.get("dimensions", {})
            if dims:
                msg_parts.append("Key dimensions:")
                dim_strs = [f"  - {k}: {v}mm" for k, v in list(dims.items())[:8]]
                msg_parts.extend(dim_strs)

            # Features
            features = specs.get("features", [])
            if features:
                msg_parts.append(f"Features: {', '.join(features[:4])}")

            # Drawing notes
            drawing_notes = specs.get("drawing_notes")
            if drawing_notes:
                msg_parts.append(f"CAD notes: {drawing_notes}")

            state["messages"].append(AIMessage(content="\n".join(msg_parts)))
        else:
            state["messages"].append(
                AIMessage(content="Research completed with limited results. Using built-in knowledge.")
            )

        return state

    def _route_after_intent(self, state: WorkflowState) -> str:
        """Determine routing after intent parsing."""
        intent = state.get("intent", {})

        # Check if research is needed first
        if intent.get("requires_research", False):
            return "research"

        # Check if refinement is needed
        if state.get("needs_refinement", False):
            return "refine"

        # Route to specialist
        return self._get_extraction_route(intent)

    def _route_after_research(self, state: WorkflowState) -> str:
        """Determine routing after research."""
        intent = state.get("intent", {})

        # Check if refinement is still needed
        if state.get("needs_refinement", False):
            return "refine"

        # Route to specialist
        return self._get_extraction_route(intent)

    def _get_extraction_route(self, intent: dict) -> str:
        """Get the appropriate extraction route based on intent."""
        domain = intent.get("specialist_domain", "general")
        complexity = intent.get("complexity_level", "standard")
        requires_curves = intent.get("requires_curves", False)

        # Use advanced curve specialist for complex designs
        if complexity in ["complex", "highly_complex"] and requires_curves:
            return "extract_entities_advanced_curves"

        # Use curve specialist for simpler curve designs
        if requires_curves or domain == "curves":
            return "extract_entities_curves"

        # Standard specialists
        if domain == "floorplan":
            return "extract_entities_floorplan"
        elif domain == "mechanical":
            return "extract_entities_mechanical"
        elif domain == "industrial":
            return "extract_entities_advanced_curves"  # Industrial uses advanced for precision
        else:
            return "extract_entities_general"

    def _route_to_specialist(self, state: WorkflowState) -> str:
        """Route to appropriate specialist based on domain."""
        intent = state.get("intent", {})
        return self._get_extraction_route(intent).replace("extract_entities_", "")

    def _refine_details_node(self, state: WorkflowState) -> WorkflowState:
        """Recursively refine vague descriptions into detailed specifications."""
        auto_accept = state.get("auto_accept_mode", False)
        settings = state.get("settings", {})
        max_passes = settings.get("refinement_passes", 3)

        # Perform recursive refinement
        refinement_result = self.detail_refinement.refine_recursively(
            user_input=state["user_input"],
            max_passes=max_passes,
            auto_accept=auto_accept
        )

        state["refinement_result"] = refinement_result.model_dump()
        state["refined_description"] = refinement_result.refined_description
        state["user_input"] = refinement_result.refined_description  # Use refined for extraction

        # Only show refinement details if not in auto-accept mode
        if not auto_accept:
            state["messages"].append(
                AIMessage(content=f"Refined specification (confidence: {refinement_result.confidence_score:.1%}):\n"
                                  f"{refinement_result.refined_description}\n\n"
                                  f"Key specifications:\n" +
                                  "\n".join(f"- {spec}" for spec in refinement_result.key_specifications))
            )
        elif auto_accept:
            state["messages"].append(
                AIMessage(content=f"Specification refined automatically (confidence: {refinement_result.confidence_score:.1%})")
            )

        return state

    def _extract_entities_general_node(self, state: WorkflowState) -> WorkflowState:
        """Extract geometric entities using general extractor."""
        description = state.get("refined_description", state["user_input"])
        entities = self.entity_extractor.extract(
            description,
            state.get("intent", {})
        )
        return self._process_extracted_entities(state, entities, "general")

    def _extract_entities_floorplan_node(self, state: WorkflowState) -> WorkflowState:
        """Extract entities using floor plan specialist."""
        description = state.get("refined_description", state["user_input"])
        settings = state.get("settings", {})

        entities = self.floorplan_specialist.generate_floorplan(
            refined_specification=description,
            include_furniture=settings.get("include_furniture", False),
            include_annotations=settings.get("include_annotations", True),
            quality_level=settings.get("quality_level", "professional")
        )
        return self._process_extracted_entities(state, entities, "floorplan specialist")

    def _extract_entities_mechanical_node(self, state: WorkflowState) -> WorkflowState:
        """Extract entities using mechanical parts specialist."""
        description = state.get("refined_description", state["user_input"])
        settings = state.get("settings", {})

        entities = self.mechanical_specialist.generate_mechanical_part(
            refined_specification=description,
            include_annotations=settings.get("include_annotations", True),
            quality_level=settings.get("quality_level", "professional")
        )
        return self._process_extracted_entities(state, entities, "mechanical specialist")

    def _extract_entities_curves_node(self, state: WorkflowState) -> WorkflowState:
        """Extract entities using curve specialist for splines, NURBS, Bezier, etc."""
        description = state.get("refined_description", state["user_input"])
        intent = state.get("intent", {})

        entities = self.curve_specialist.extract(
            user_input=description,
            intent=intent
        )
        return self._process_extracted_entities(state, entities, "curve specialist")

    def _extract_entities_advanced_curves_node(self, state: WorkflowState) -> WorkflowState:
        """Extract entities using advanced curve specialist for complex designs.

        Handles:
        - Saturn V rockets, spacecraft, aircraft
        - Disney Cinderella Castle, princess dresses
        - Industrial products with precise specifications (Global Industrial parts)
        - PartsTown commercial kitchen equipment
        - Any design requiring research + complex curves
        """
        description = state.get("refined_description", state["user_input"])
        intent = state.get("intent", {})
        research_data = state.get("research_data", {})

        # Determine design type from intent and description
        complexity = intent.get("complexity_level", "standard")
        drawing_type = intent.get("drawing_type", "")
        description_lower = description.lower()

        # Choose the appropriate design generator
        if "saturn" in description_lower and ("v" in description_lower or "5" in description_lower or "rocket" in description_lower):
            # Saturn V rocket
            state["messages"].append(
                AIMessage(content="Generating Saturn V rocket profile with multi-stage design...")
            )
            entities = self.advanced_curve_specialist.create_saturn_v(
                scale=1.0,
                detail_level="high" if complexity == "highly_complex" else "medium"
            )

        elif "castle" in description_lower or "cinderella" in description_lower:
            # Disney Cinderella Castle
            state["messages"].append(
                AIMessage(content="Generating Cinderella Castle silhouette with Gothic spires and turrets...")
            )
            entities = self.advanced_curve_specialist.create_castle_silhouette(
                scale=1.0,
                detail_level="high" if complexity == "highly_complex" else "medium"
            )

        elif "dress" in description_lower or "gown" in description_lower or "princess" in description_lower:
            # Princess ball gown
            state["messages"].append(
                AIMessage(content="Generating princess ball gown silhouette with flowing curves...")
            )
            entities = self.advanced_curve_specialist.create_princess_dress(
                scale=1.0,
                style="cinderella" if "cinderella" in description_lower else "belle" if "belle" in description_lower else "generic"
            )

        elif any(part_id in description for part_id in ["160CP19", "168255", "810803", "1086700"]):
            # Industrial product with part number
            state["messages"].append(
                AIMessage(content="Generating industrial product from specifications...")
            )

            # Extract part number
            part_number = None
            for pid in ["160CP19", "168255", "810803", "1086700"]:
                if pid in description:
                    part_number = pid
                    break

            # Use research data if available
            specs = research_data.get("specifications", {})

            if part_number == "160CP19":
                # Double rivet beam
                entities = self.advanced_curve_specialist.create_industrial_beam(
                    length_mm=specs.get("dimensions", {}).get("length", 1066.8),
                    height_mm=specs.get("dimensions", {}).get("height", 76.2),
                    specifications=specs
                )
            elif part_number == "168255":
                # Aluminum noseplate
                entities = self.advanced_curve_specialist.create_noseplate(
                    width_mm=specs.get("dimensions", {}).get("width", 457.2),
                    height_mm=specs.get("dimensions", {}).get("height", 355.6),
                    specifications=specs
                )
            else:
                # Generic industrial part from specs
                entities = self.advanced_curve_specialist.create_from_specifications(
                    description=description,
                    specifications=specs
                )

        elif "partstown" in description_lower or any(term in description_lower for term in ["gasket", "burner", "evaporator", "thermostat"]):
            # PartsTown commercial kitchen equipment
            state["messages"].append(
                AIMessage(content="Generating commercial kitchen equipment part...")
            )
            specs = research_data.get("specifications", {})
            entities = self.advanced_curve_specialist.create_from_specifications(
                description=description,
                specifications=specs
            )

        else:
            # Complex curve design using LLM extraction
            state["messages"].append(
                AIMessage(content="Generating complex curve design using advanced specialist...")
            )
            entities = self.advanced_curve_specialist.extract_advanced(
                user_input=description,
                intent=intent,
                research_data=research_data
            )

        return self._process_extracted_entities(state, entities, "advanced curve specialist")

    def _process_extracted_entities(self, state: WorkflowState, entities, agent_name: str) -> WorkflowState:
        """Common processing for extracted entities."""
        state["entities"] = entities.model_dump()

        # Count basic entities
        total = (len(entities.lines) + len(entities.circles) +
                 len(entities.arcs) + len(entities.polylines) + len(entities.hatches))

        entity_counts = [
            f"- Lines: {len(entities.lines)}",
            f"- Circles: {len(entities.circles)}",
            f"- Arcs: {len(entities.arcs)}",
            f"- Polylines: {len(entities.polylines)}",
            f"- Hatches: {len(entities.hatches)}"
        ]

        # Count curve entities if present (ExtendedEntities)
        if hasattr(entities, 'splines') and entities.splines:
            total += len(entities.splines)
            entity_counts.append(f"- B-Splines: {len(entities.splines)}")
        if hasattr(entities, 'nurbs_curves') and entities.nurbs_curves:
            total += len(entities.nurbs_curves)
            entity_counts.append(f"- NURBS curves: {len(entities.nurbs_curves)}")
        if hasattr(entities, 'bezier_curves') and entities.bezier_curves:
            total += len(entities.bezier_curves)
            entity_counts.append(f"- Bezier curves: {len(entities.bezier_curves)}")
        if hasattr(entities, 'ellipses') and entities.ellipses:
            total += len(entities.ellipses)
            entity_counts.append(f"- Ellipses: {len(entities.ellipses)}")
        if hasattr(entities, 'polylines_with_curves') and entities.polylines_with_curves:
            total += len(entities.polylines_with_curves)
            entity_counts.append(f"- Curved polylines: {len(entities.polylines_with_curves)}")

        state["messages"].append(
            AIMessage(content=f"Extracted {total} geometric entities using {agent_name}:\n" +
                              "\n".join(entity_counts))
        )

        if entities.notes:
            state["messages"].append(
                AIMessage(content=f"Notes: {entities.notes}")
            )

        return state


    def _format_metadata_node(self, state: WorkflowState) -> WorkflowState:
        """Format entities to text_to_dxf CSV format."""
        from ..agents.entity_extractor import ExtractedEntities
        from ..agents.curve_entities import ExtendedEntities

        # Reconstruct entities object
        entities_dict = state.get("entities", {})

        # Determine if we have curve entities
        has_curves = any(key in entities_dict for key in
                        ['splines', 'nurbs_curves', 'bezier_curves', 'ellipses', 'polylines_with_curves'])

        if has_curves:
            # Use ExtendedEntities which includes curve support
            entities = ExtendedEntities(**entities_dict)
        else:
            entities = ExtractedEntities(**entities_dict)

        # Format to CSV
        formatted_csv = self.metadata_formatter.format(entities)
        state["formatted_csv"] = formatted_csv

        curve_note = " (including curve entities)" if has_curves else ""
        state["messages"].append(
            AIMessage(content=f"Formatted metadata to text_to_dxf CSV format{curve_note}.")
        )

        return state

    def _validate_node(self, state: WorkflowState) -> WorkflowState:
        """Validate the generated metadata using AutoValidator."""
        auto_accept = state.get("auto_accept_mode", False)

        # Use AutoValidatorAgent which can apply automatic fixes
        validation_result, fixed_entities = self.auto_validator.validate(
            user_input=state.get("original_user_input", state["user_input"]),
            entities=state.get("entities", {}),
            formatted_csv=state.get("formatted_csv", ""),
            auto_accept=auto_accept
        )

        # If entities were fixed, update them and reformat
        if auto_accept and validation_result.auto_fixes_applied:
            state["entities"] = fixed_entities.model_dump()
            state["auto_fixes_log"] = [fix.model_dump() for fix in validation_result.auto_fixes_applied]

            # Reformat with fixed entities
            formatted_csv = self.metadata_formatter.format(fixed_entities)
            state["formatted_csv"] = formatted_csv

        state["validation"] = validation_result.model_dump()
        state["iteration_count"] = state.get("iteration_count", 0) + 1

        # Track validation history
        validation_history = state.get("validation_history", [])
        accepted_warnings = state.get("accepted_warnings", [])

        # Filter out issues that were previously accepted
        new_issues = [
            issue for issue in validation_result.issues
            if not any(issue.lower() in accepted.lower() for accepted in accepted_warnings)
        ]

        # Check for recurring issues (same issue appearing multiple times)
        recurring_issues = []
        for issue in new_issues:
            issue_count = sum(1 for hist in validation_history if issue.lower() in hist.get("issue", "").lower())
            if issue_count >= 2:  # Issue has appeared 2+ times
                recurring_issues.append(issue)

        # Add current issues to history
        for issue in validation_result.issues:
            validation_history.append({
                "iteration": state.get("iteration_count", 0),
                "issue": issue,
                "auto_fixed": any(fix.description for fix in validation_result.auto_fixes_applied if issue in fix.description)
            })

        state["validation_history"] = validation_history

        # Filter questions to avoid asking about accepted warnings
        new_questions = [
            q for q in validation_result.questions_for_user
            if not any(q.lower() in accepted.lower() for accepted in accepted_warnings)
        ]

        # Update validation result with filtered issues and questions
        validation_result.issues = new_issues
        validation_result.questions_for_user = new_questions

        # Add validation message
        if validation_result.is_valid:
            message = f"✓ Validation passed (confidence: {validation_result.confidence_score:.1%})\n{validation_result.summary}"

            # Show auto-fixes if any were applied
            if auto_accept and validation_result.auto_fixes_applied:
                message += f"\n\nAuto-fixes applied ({len(validation_result.auto_fixes_applied)}):\n"
                message += "\n".join(f"- {fix.description}" for fix in validation_result.auto_fixes_applied)

            state["messages"].append(AIMessage(content=message))

            if validation_result.suggestions:
                state["messages"].append(
                    AIMessage(content="Suggestions:\n" + "\n".join(f"- {s}" for s in validation_result.suggestions))
                )
        else:
            # Warn about recurring issues
            if recurring_issues:
                state["messages"].append(
                    AIMessage(content=f"⚠ Recurring validation issues detected (attempting auto-fix):\n" +
                                      "\n".join(f"- {issue}" for issue in recurring_issues))
                )

            if new_issues:
                state["messages"].append(
                    AIMessage(content=f"⚠ Validation issues found:\n" +
                                      "\n".join(f"- {issue}" for issue in new_issues))
                )

        return state

    def _ask_feedback_node(self, state: WorkflowState) -> WorkflowState:
        """Ask user for feedback."""
        validation = state.get("validation", {})
        questions = validation.get("questions_for_user", [])

        if questions:
            state["messages"].append(
                AIMessage(content="I have some questions:\n" +
                                  "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions)))
            )

        state["requires_user_feedback"] = True
        return state

    def _should_continue(self, state: WorkflowState) -> Literal["complete", "feedback", "retry"]:
        """Decide whether to continue, ask for feedback, or complete."""
        validation = state.get("validation", {})
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 3)

        # Check if valid and confident
        if validation.get("is_valid") and validation.get("confidence_score", 0) > 0.7:
            return "complete"

        # Check if we need user feedback
        if validation.get("questions_for_user"):
            return "feedback"

        # Retry if under iteration limit
        if iteration_count < max_iterations:
            return "retry"

        # Otherwise complete (even if not perfect)
        return "complete"

    def run(self, user_input: str, max_iterations: int = 3, settings: Optional[UserSettings] = None) -> dict:
        """Run the workflow with user settings."""
        if settings is None:
            settings = UserSettings()

        initial_state: WorkflowState = {
            "messages": [HumanMessage(content=user_input)],
            "user_input": user_input,
            "original_user_input": user_input,
            "settings": settings.model_dump(),
            "auto_accept_mode": settings.auto_accept_mode,
            "iteration_count": 0,
            "max_iterations": max_iterations,
            "requires_user_feedback": False,
            "is_complete": False,
            "validation_history": [],
            "accepted_warnings": [],
            "feedback_history": []
        }

        final_state = self.graph.invoke(initial_state)
        return final_state

    def continue_with_feedback(self, previous_state: WorkflowState, feedback: str) -> dict:
        """Continue workflow with user feedback using intelligent parsing."""
        # Add user feedback to messages
        previous_state["messages"].append(HumanMessage(content=feedback))

        # Parse the feedback to understand what the user wants
        validation_issues = previous_state.get("validation", {}).get("issues", [])
        entities_dict = previous_state.get("entities", {})

        # Create a summary of current entities
        entities_summary = f"Lines: {len(entities_dict.get('lines', []))}, " \
                          f"Circles: {len(entities_dict.get('circles', []))}, " \
                          f"Arcs: {len(entities_dict.get('arcs', []))}, " \
                          f"Polylines: {len(entities_dict.get('polylines', []))}, " \
                          f"Hatches: {len(entities_dict.get('hatches', []))}"

        parsed_feedback = self.feedback_parser.parse(
            feedback=feedback,
            validation_issues=validation_issues,
            entities_summary=entities_summary
        )

        # Add parsed feedback to history
        feedback_history = previous_state.get("feedback_history", [])
        feedback_history.append({
            "feedback": feedback,
            "parsed": parsed_feedback.model_dump(),
            "iteration": previous_state.get("iteration_count", 0)
        })
        previous_state["feedback_history"] = feedback_history

        # Handle different feedback types
        if parsed_feedback.feedback_type == "accept_as_is":
            # User is accepting current state, add to accepted warnings
            accepted_warnings = previous_state.get("accepted_warnings", [])
            for issue in validation_issues:
                if not issue in accepted_warnings:
                    accepted_warnings.append(issue)
            previous_state["accepted_warnings"] = accepted_warnings

            # Mark as complete
            previous_state["requires_user_feedback"] = False
            previous_state["is_complete"] = True

            previous_state["messages"].append(
                AIMessage(content=f"Understood. {parsed_feedback.summary}")
            )

            return previous_state

        elif parsed_feedback.requires_regeneration:
            # Need to regenerate with updated context
            updated_input = previous_state.get("original_user_input", previous_state["user_input"])
            if parsed_feedback.context_update:
                updated_input = f"{updated_input}\n\nAdditional requirements: {parsed_feedback.context_update}"

            previous_state["user_input"] = updated_input
            previous_state["requires_user_feedback"] = False

            # Re-run from parse_intent
            final_state = self.graph.invoke(previous_state)
            return final_state

        else:
            # Apply targeted actions to existing entities
            from ..agents.entity_extractor import ExtractedEntities
            entities = ExtractedEntities(**entities_dict)

            # Apply each action
            for action in parsed_feedback.actions:
                if action.action_type == "fix_dimension":
                    # Apply standard dimensions based on target
                    self._apply_dimension_fix(entities, action)

            # Update state with modified entities
            previous_state["entities"] = entities.model_dump()

            # Reformat metadata
            formatted_csv = self.metadata_formatter.format(entities)
            previous_state["formatted_csv"] = formatted_csv

            previous_state["requires_user_feedback"] = False

            previous_state["messages"].append(
                AIMessage(content=f"Applied corrections: {parsed_feedback.summary}")
            )

            # Re-validate
            final_state = self.graph.invoke(previous_state)
            return final_state

    def _apply_dimension_fix(self, entities: 'ExtractedEntities', action: 'FeedbackAction') -> None:
        """Apply a dimension fix to entities based on parsed feedback action."""
        if action.target_entity_type == "lines":
            for line in entities.lines:
                if action.target_description_pattern and \
                   action.target_description_pattern.lower() in line.description.lower():
                    # Apply standard window dimension (1200mm)
                    if "window" in action.target_description_pattern.lower():
                        # Check if line is zero-length
                        import math
                        distance = math.sqrt((line.x2 - line.x1)**2 + (line.y2 - line.y1)**2)
                        if distance < 0.01:
                            # Determine orientation and set standard dimension
                            if "vertical" in line.description.lower():
                                line.y2 = line.y1 + 1200.0
                            else:
                                line.x2 = line.x1 + 1200.0

    def run_refinement(self, original_input: str, previous_metadata: str,
                      refinement_request: str, refinement_history: list = None) -> dict:
        """Run workflow with refinement context to improve metadata."""
        if refinement_history is None:
            refinement_history = []

        # Build context-aware input that includes all refinement information
        refinement_context = f"""Original request: {original_input}

Previous metadata generated:
```
{previous_metadata}
```

Refinement history:
{chr(10).join(f"{i+1}. {req}" for i, req in enumerate(refinement_history)) if refinement_history else "None"}

New refinement request: {refinement_request}

Please analyze the refinement request and improve the metadata accordingly. Focus on:
1. Understanding what specific changes or additions are requested
2. Maintaining consistency with the original intent
3. Preserving existing correct elements while making targeted improvements
4. Ensuring the refined metadata is more accurate and complete
"""

        # Create initial state with refinement context
        initial_state: WorkflowState = {
            "messages": [
                SystemMessage(content="You are refining previously generated DXF metadata. "
                                    "Use the context provided to make targeted improvements."),
                HumanMessage(content=refinement_context)
            ],
            "user_input": refinement_context,
            "iteration_count": 0,
            "max_iterations": 3,
            "requires_user_feedback": False,
            "is_complete": False
        }

        # Run the workflow
        final_state = self.graph.invoke(initial_state)

        # Add a message indicating this was a refinement
        final_state["messages"].append(
            AIMessage(content="Metadata has been refined based on your feedback.")
        )

        return final_state
