#!/usr/bin/env python3
"""
Unit tests to verify the fixes for edge cases.
Tests the settings validation and format handling without API calls.
"""

import sys
sys.path.insert(0, '/home/user/dxfgen')

from backend.settings import UserSettings, SettingsManager, VALID_QUALITY_LEVELS


def test_settings_validation():
    """Test UserSettings validation."""
    print("Testing UserSettings validation...")

    # Test 1: Boolean field with string "yes"
    settings = UserSettings(auto_accept_mode="yes")
    assert settings.auto_accept_mode == True, "String 'yes' should convert to True"
    print("  String 'yes' -> True: PASS")

    # Test 2: Boolean field with string "no"
    settings = UserSettings(auto_accept_mode="no")
    assert settings.auto_accept_mode == False, "String 'no' should convert to False"
    print("  String 'no' -> False: PASS")

    # Test 3: Boolean field with integer 1
    settings = UserSettings(auto_accept_mode=1)
    assert settings.auto_accept_mode == True, "Integer 1 should convert to True"
    print("  Integer 1 -> True: PASS")

    # Test 4: Boolean field with integer 0
    settings = UserSettings(auto_accept_mode=0)
    assert settings.auto_accept_mode == False, "Integer 0 should convert to False"
    print("  Integer 0 -> False: PASS")

    # Test 5: Invalid quality level
    settings = UserSettings(quality_level="INVALID")
    assert settings.quality_level == "professional", "Invalid quality should default to 'professional'"
    print("  Invalid quality_level -> 'professional': PASS")

    # Test 6: Valid quality levels
    for level in ["draft", "standard", "professional"]:
        settings = UserSettings(quality_level=level)
        assert settings.quality_level == level, f"Quality level '{level}' should be preserved"
    print("  Valid quality levels: PASS")

    # Test 7: Case insensitive quality level
    settings = UserSettings(quality_level="DRAFT")
    assert settings.quality_level == "draft", "Quality level should be case insensitive"
    print("  Case insensitive quality: PASS")

    # Test 8: Negative refinement passes
    settings = UserSettings(refinement_passes=-5)
    assert settings.refinement_passes == 1, "Negative refinement should become 1"
    print("  Negative refinement -> 1: PASS")

    # Test 9: Zero refinement passes
    settings = UserSettings(refinement_passes=0)
    assert settings.refinement_passes == 1, "Zero refinement should become 1"
    print("  Zero refinement -> 1: PASS")

    # Test 10: Refinement passes > 10
    settings = UserSettings(refinement_passes=100)
    assert settings.refinement_passes == 10, "Refinement > 10 should become 10"
    print("  Refinement > 10 -> 10: PASS")

    # Test 11: Non-numeric refinement passes
    settings = UserSettings(refinement_passes="abc")
    assert settings.refinement_passes == 3, "Non-numeric refinement should default to 3"
    print("  Non-numeric refinement -> 3: PASS")

    # Test 12: Invalid units
    settings = UserSettings(default_units="INVALID")
    assert settings.default_units == "mm", "Invalid units should default to 'mm'"
    print("  Invalid units -> 'mm': PASS")

    # Test 13: Valid units case insensitive
    settings = UserSettings(default_units="INCHES")
    assert settings.default_units == "inches", "Units should be case insensitive"
    print("  Units case insensitive: PASS")

    print("\nAll UserSettings validation tests PASSED!")


def test_settings_manager():
    """Test SettingsManager with various inputs."""
    print("\nTesting SettingsManager...")

    manager = SettingsManager()

    # Test 1: Update with string boolean
    session_id = "test_session_1"
    result = manager.update_settings(session_id, {"auto_accept_mode": "yes"})
    assert result.auto_accept_mode == True, "Manager should convert 'yes' to True"
    print("  Manager update with 'yes': PASS")

    # Test 2: Update with invalid quality
    result = manager.update_settings(session_id, {"quality_level": "BADVALUE"})
    assert result.quality_level == "professional", "Manager should default invalid quality"
    print("  Manager update with invalid quality: PASS")

    # Test 3: Update with negative refinement
    result = manager.update_settings(session_id, {"refinement_passes": -10})
    assert result.refinement_passes == 1, "Manager should clamp negative refinement"
    print("  Manager update with negative refinement: PASS")

    # Test 4: Update with unknown field (should be ignored)
    result = manager.update_settings(session_id, {"unknown_field": "value"})
    assert not hasattr(result, "unknown_field") or result.model_dump().get("unknown_field") is None
    print("  Manager ignores unknown fields: PASS")

    # Test 5: Reset settings
    manager.update_settings(session_id, {"auto_accept_mode": True, "quality_level": "draft"})
    reset_result = manager.reset_settings(session_id)
    assert reset_result.auto_accept_mode == False, "Reset should restore defaults"
    assert reset_result.quality_level == "professional", "Reset should restore quality default"
    print("  Manager reset: PASS")

    print("\nAll SettingsManager tests PASSED!")


def test_converter_registry_format_handling():
    """Test converter registry format handling."""
    print("\nTesting ConverterRegistry format handling...")

    from backend.converters.registry import ConverterRegistry

    registry = ConverterRegistry()

    # Test 1: Check unknown format returns proper error
    available = registry.is_format_available("INVALID_FORMAT")
    assert available == False, "Invalid format should not be available"
    print("  Invalid format not available: PASS")

    # Test 2: Check DXF is always available
    available = registry.is_format_available("DXF")
    assert available == True, "DXF should always be available"
    print("  DXF always available: PASS")

    # Test 3: Get available formats returns proper structure
    formats = registry.get_available_formats()
    assert "categories" in formats, "Should have categories"
    assert "source" in formats["categories"], "Should have source category"
    print("  Format structure correct: PASS")

    # Test 4: Convert with invalid format
    success, path, error = registry.convert("/tmp/test.dxf", "INVALID_FORMAT")
    assert success == False, "Invalid format should fail"
    assert "not available" in error.lower() or "format" in error.lower(), "Should have format error message"
    print("  Invalid format conversion fails: PASS")

    print("\nAll ConverterRegistry tests PASSED!")


def test_empty_and_edge_inputs():
    """Test edge case inputs."""
    print("\nTesting edge case inputs...")

    # Test None values
    try:
        settings = UserSettings(auto_accept_mode=None)
        # If it doesn't error, check the value is reasonable
        assert settings.auto_accept_mode in [False, True]
        print("  None for boolean handled: PASS")
    except Exception as e:
        print(f"  None for boolean: Expected - {type(e).__name__}")

    # Test empty dict for settings manager
    manager = SettingsManager()
    result = manager.update_settings("empty_test", {})
    assert result is not None
    print("  Empty dict update: PASS")

    # Test model_dump works
    settings = UserSettings()
    dump = settings.model_dump()
    assert "auto_accept_mode" in dump
    assert "quality_level" in dump
    print("  model_dump works: PASS")

    print("\nAll edge case tests PASSED!")


if __name__ == "__main__":
    try:
        test_settings_validation()
        test_settings_manager()
        test_converter_registry_format_handling()
        test_empty_and_edge_inputs()
        print("\n" + "=" * 50)
        print("ALL UNIT TESTS PASSED!")
        print("=" * 50)
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
