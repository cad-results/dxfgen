"""User settings and preferences for DXF generation."""

from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator


# Valid quality levels
VALID_QUALITY_LEVELS = {"draft", "standard", "professional"}
VALID_UNITS = {"mm", "cm", "m", "inches", "feet"}


class UserSettings(BaseModel):
    """User preferences for DXF generation workflow."""

    auto_accept_mode: bool = Field(
        default=False,
        description="When enabled, automatically fix validation issues without user confirmation"
    )

    refinement_passes: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of recursive refinement passes for vague queries"
    )

    default_units: str = Field(
        default="mm",
        description="Default measurement units (mm, cm, m, inches, feet)"
    )

    include_annotations: bool = Field(
        default=True,
        description="Include annotations (labels, dimensions) in generated DXF"
    )

    include_furniture: bool = Field(
        default=False,
        description="Include furniture and fixtures in floor plans by default"
    )

    quality_level: str = Field(
        default="professional",
        description="Output quality level: 'draft', 'standard', 'professional'"
    )

    enable_templates: bool = Field(
        default=True,
        description="Enable template system for quick starts"
    )

    @field_validator('quality_level')
    @classmethod
    def validate_quality_level(cls, v: str) -> str:
        """Validate and normalize quality level."""
        if v is None:
            return "professional"
        v_lower = str(v).lower().strip()
        if v_lower not in VALID_QUALITY_LEVELS:
            return "professional"  # Default to professional for invalid values
        return v_lower

    @field_validator('default_units')
    @classmethod
    def validate_units(cls, v: str) -> str:
        """Validate and normalize units."""
        if v is None:
            return "mm"
        v_lower = str(v).lower().strip()
        if v_lower not in VALID_UNITS:
            return "mm"  # Default to mm for invalid values
        return v_lower

    @field_validator('refinement_passes', mode='before')
    @classmethod
    def validate_refinement_passes(cls, v) -> int:
        """Validate refinement passes is within valid range."""
        try:
            val = int(v)
            if val < 1:
                return 1
            if val > 10:
                return 10
            return val
        except (TypeError, ValueError):
            return 3  # Default value

    @field_validator('auto_accept_mode', 'include_annotations', 'include_furniture', 'enable_templates', mode='before')
    @classmethod
    def validate_bool_fields(cls, v) -> bool:
        """Convert various truthy/falsy values to boolean."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', 'yes', '1', 'on')
        if isinstance(v, (int, float)):
            return bool(v)
        return False


class SettingsManager:
    """Manages user settings with session-based storage."""

    def __init__(self):
        self.sessions: Dict[str, UserSettings] = {}
        self.default_settings = UserSettings()

    def get_settings(self, session_id: str = "default") -> UserSettings:
        """Get settings for a session, or return default."""
        if session_id not in self.sessions:
            self.sessions[session_id] = UserSettings()
        return self.sessions[session_id]

    def update_settings(self, session_id: str, settings: Dict[str, Any]) -> UserSettings:
        """Update settings for a session with proper validation."""
        current = self.get_settings(session_id)

        # Build a dict of current values and update with new values
        current_dict = current.model_dump()

        # Only update fields that exist in the model
        for key, value in settings.items():
            if key in current_dict:
                current_dict[key] = value

        # Create new UserSettings with validation
        try:
            updated = UserSettings(**current_dict)
        except Exception:
            # If validation fails, return current settings unchanged
            return current

        self.sessions[session_id] = updated
        return updated

    def reset_settings(self, session_id: str) -> UserSettings:
        """Reset settings to default for a session."""
        self.sessions[session_id] = UserSettings()
        return self.sessions[session_id]

    def clear_session(self, session_id: str):
        """Clear settings for a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]


# Global settings manager instance
settings_manager = SettingsManager()
