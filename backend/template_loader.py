"""Template Loader System - Load and parse DXF generation templates."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import re


class Template:
    """Represents a DXF generation template."""

    def __init__(
        self,
        name: str,
        category: str,
        description: str,
        parameters: Dict[str, Any],
        prompt: str,
        metadata: Optional[str] = None
    ):
        self.name = name
        self.category = category
        self.description = description
        self.parameters = parameters
        self.prompt = prompt
        self.metadata = metadata

    def apply_parameters(self, user_params: Dict[str, Any]) -> str:
        """Apply user-provided parameters to the template prompt."""
        prompt = self.prompt
        params = {**self.parameters, **user_params}

        # Replace placeholders like {param_name}
        for key, value in params.items():
            placeholder = "{" + key + "}"
            prompt = prompt.replace(placeholder, str(value))

        return prompt


class TemplateLoader:
    """Loads and manages DXF generation templates from markdown files."""

    def __init__(self, templates_dir: Optional[Path] = None):
        if templates_dir is None:
            # Default to templates/ directory in project root
            templates_dir = Path(__file__).parent.parent / "templates"

        self.templates_dir = Path(templates_dir)
        self.templates: Dict[str, Template] = {}
        self._load_all_templates()

    def _load_all_templates(self):
        """Load all template files from templates directory."""
        if not self.templates_dir.exists():
            print(f"Templates directory not found: {self.templates_dir}")
            return

        # Load all .md files
        for template_file in self.templates_dir.glob("*.md"):
            try:
                templates = self._parse_template_file(template_file)
                for template in templates:
                    self.templates[template.name] = template
            except Exception as e:
                print(f"Error loading template file {template_file}: {e}")

    def _parse_template_file(self, file_path: Path) -> List[Template]:
        """
        Parse a markdown template file.

        Expected format:
        # Template Name
        **Category**: category_name
        **Description**: Template description

        ## Parameters
        - param1: default_value (description)
        - param2: default_value (description)

        ## Prompt
        Template prompt with {param1} and {param2} placeholders

        ## Metadata (optional)
        Pre-generated CSV metadata
        """
        templates = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by top-level headings (# Template Name)
        template_sections = re.split(r'\n# ', content)

        for section in template_sections:
            if not section.strip():
                continue

            # Add back the # if it was split
            if not section.startswith('#'):
                section = '# ' + section

            template = self._parse_template_section(section)
            if template:
                templates.append(template)

        return templates

    def _parse_template_section(self, section: str) -> Optional[Template]:
        """Parse a single template section."""
        lines = section.split('\n')

        # Extract name (first line, remove #)
        name = lines[0].strip('# ').strip()
        if not name:
            return None

        # Initialize fields
        category = "general"
        description = ""
        parameters = {}
        prompt = ""
        metadata = None

        # Parse sections
        current_section = None
        section_content = []

        for line in lines[1:]:
            # Check for section headers
            if line.startswith('## Parameters'):
                if current_section and section_content:
                    self._process_section(current_section, section_content, locals())
                current_section = 'parameters'
                section_content = []
            elif line.startswith('## Prompt'):
                if current_section and section_content:
                    self._process_section(current_section, section_content, locals())
                current_section = 'prompt'
                section_content = []
            elif line.startswith('## Metadata'):
                if current_section and section_content:
                    self._process_section(current_section, section_content, locals())
                current_section = 'metadata'
                section_content = []
            # Check for inline fields
            elif line.startswith('**Category**:'):
                category = line.split(':', 1)[1].strip()
            elif line.startswith('**Description**:'):
                description = line.split(':', 1)[1].strip()
            # Add to current section content
            elif current_section:
                section_content.append(line)

        # Process last section
        if current_section and section_content:
            if current_section == 'parameters':
                parameters = self._parse_parameters(section_content)
            elif current_section == 'prompt':
                prompt = '\n'.join(section_content).strip()
            elif current_section == 'metadata':
                metadata = '\n'.join(section_content).strip()

        return Template(
            name=name,
            category=category,
            description=description,
            parameters=parameters,
            prompt=prompt,
            metadata=metadata
        )

    def _process_section(self, section_name: str, content: List[str], context: Dict):
        """Process a section and update the context."""
        if section_name == 'parameters':
            context['parameters'] = self._parse_parameters(content)
        elif section_name == 'prompt':
            context['prompt'] = '\n'.join(content).strip()
        elif section_name == 'metadata':
            context['metadata'] = '\n'.join(content).strip()

    def _parse_parameters(self, lines: List[str]) -> Dict[str, Any]:
        """Parse parameter lines like: - param_name: default_value (description)"""
        parameters = {}

        for line in lines:
            line = line.strip()
            if not line or not line.startswith('-'):
                continue

            # Remove leading dash
            line = line[1:].strip()

            # Split on first colon
            if ':' not in line:
                continue

            param_name, rest = line.split(':', 1)
            param_name = param_name.strip()

            # Extract default value (before parenthesis if present)
            if '(' in rest:
                default_value = rest.split('(')[0].strip()
            else:
                default_value = rest.strip()

            # Try to parse as number if possible
            try:
                if '.' in default_value:
                    default_value = float(default_value)
                else:
                    default_value = int(default_value)
            except (ValueError, AttributeError):
                # Keep as string
                pass

            parameters[param_name] = default_value

        return parameters

    def get_template(self, name: str) -> Optional[Template]:
        """Get a template by name."""
        return self.templates.get(name)

    def get_templates_by_category(self, category: str) -> List[Template]:
        """Get all templates in a category."""
        return [t for t in self.templates.values() if t.category == category]

    def list_templates(self) -> List[Dict[str, str]]:
        """List all available templates."""
        return [
            {
                'name': t.name,
                'category': t.category,
                'description': t.description
            }
            for t in self.templates.values()
        ]

    def list_categories(self) -> List[str]:
        """List all template categories."""
        categories = set(t.category for t in self.templates.values())
        return sorted(categories)

    def apply_template(self, name: str, user_params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Apply a template with user parameters and return the prompt."""
        template = self.get_template(name)
        if not template:
            return None

        if user_params is None:
            user_params = {}

        return template.apply_parameters(user_params)


# Global template loader instance
template_loader = TemplateLoader()
