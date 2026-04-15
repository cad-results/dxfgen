"""Flask API server for DXF chatbot with settings and augmentation support."""

import os
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import traceback

from .graph import DXFWorkflow
from .dxf_generator import DXFGenerator
from .settings import settings_manager, UserSettings
from .mayo import MayoConverter, ViewerLauncher, SUPPORTED_EXPORT_FORMATS
from .converters import ConverterRegistry, FORMAT_CATEGORIES
from .viewer_2d import DXF2DViewer

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')
CORS(app)

# Global workflow instance (will be initialized on first request)
workflow = None
dxf_generator = None
mayo_converter = None
viewer_launcher = None
converter_registry = None
viewer_2d = None

# Session storage (in production, use Redis or similar)
sessions = {}


def get_workflow():
    """Get or create workflow instance."""
    global workflow
    if workflow is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")
        model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
        workflow = DXFWorkflow(api_key, model)
    return workflow


def get_dxf_generator():
    """Get or create DXF generator instance."""
    global dxf_generator
    if dxf_generator is None:
        dxf_generator = DXFGenerator()
    return dxf_generator


def get_mayo_converter():
    """Get or create MayoConverter instance."""
    global mayo_converter
    if mayo_converter is None:
        try:
            mayo_converter = MayoConverter()
        except FileNotFoundError:
            return None
    return mayo_converter


def get_viewer_launcher():
    """Get or create ViewerLauncher instance."""
    global viewer_launcher
    if viewer_launcher is None:
        viewer_launcher = ViewerLauncher()
    return viewer_launcher


def get_converter_registry():
    """Get or create ConverterRegistry instance."""
    global converter_registry
    if converter_registry is None:
        converter_registry = ConverterRegistry()
    return converter_registry


def get_viewer_2d():
    """Get or create DXF2DViewer instance."""
    global viewer_2d
    if viewer_2d is None:
        viewer_2d = DXF2DViewer()
    return viewer_2d


@app.route('/')
def index():
    """Serve the chatbot interface."""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages and process through workflow with settings support."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        # Safely get message, handling None values
        raw_message = data.get('message')
        user_message = str(raw_message).strip() if raw_message is not None else ''

        session_id = data.get('session_id', 'default')
        is_refinement = data.get('is_refinement', False)
        refinement_context = data.get('refinement_context', None)
        user_settings_data = data.get('settings') or {}

        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400

        # Get or update user settings
        if user_settings_data:
            user_settings = settings_manager.update_settings(session_id, user_settings_data)
        else:
            user_settings = settings_manager.get_settings(session_id)

        # Get workflow
        wf = get_workflow()

        # Handle refinement requests
        if is_refinement and refinement_context:
            # This is a refinement request with context
            result = wf.run_refinement(
                original_input=refinement_context.get('original_input', ''),
                previous_metadata=refinement_context.get('previous_metadata', ''),
                refinement_request=user_message,
                refinement_history=refinement_context.get('refinement_history', [])
            )
        elif session_id in sessions and sessions[session_id].get('requires_user_feedback'):
            # Continue with feedback
            previous_state = sessions[session_id]['state']
            result = wf.continue_with_feedback(previous_state, user_message)
        else:
            # New conversation with settings
            result = wf.run(user_message, max_iterations=3, settings=user_settings)

        # Store session
        sessions[session_id] = {
            'state': result,
            'requires_user_feedback': result.get('requires_user_feedback', False)
        }

        # Extract messages for response
        messages = []
        for msg in result.get('messages', []):
            messages.append({
                'role': 'user' if msg.type == 'human' else 'assistant',
                'content': msg.content
            })

        # Build response
        response = {
            'messages': messages,
            'requires_feedback': result.get('requires_user_feedback', False),
            'is_complete': not result.get('requires_user_feedback', False),
            'metadata': {
                'intent': result.get('intent'),
                'entities': result.get('entities'),
                'validation': result.get('validation')
            }
        }

        # If complete and valid, include CSV and generation option
        if response['is_complete'] and result.get('formatted_csv'):
            response['csv_metadata'] = result['formatted_csv']
            response['can_generate'] = True

        return jsonify(response)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def generate_dxf():
    """Generate DXF file from metadata.

    Supports:
    1. Direct entity generation (preferred) - bypasses CSV parsing
    2. CSV-based generation (fallback) - uses text_to_dxf

    Uses minimal DXF format by default for clean, non-bloated output.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        session_id = data.get('session_id', 'default')
        csv_metadata = data.get('csv_metadata') or ''
        filename = data.get('filename')
        entities_dict = data.get('entities')
        use_minimal = data.get('use_minimal_format', True)  # Default to minimal format

        # Try to get entities from session if not provided directly
        if not entities_dict and session_id in sessions:
            state = sessions[session_id]['state']
            entities_dict = state.get('entities', {})
            if not csv_metadata:
                csv_metadata = state.get('formatted_csv', '')

        generator = get_dxf_generator()

        # Check if we have any entities to generate
        has_entities = entities_dict and any(
            key in entities_dict and entities_dict[key]
            for key in ['lines', 'circles', 'arcs', 'polylines', 'hatches',
                       'splines', 'nurbs_curves', 'bezier_curves', 'ellipses',
                       'polylines_with_curves']
        )

        # Check if we have advanced curve entities
        has_advanced_curves = entities_dict and any(
            key in entities_dict and entities_dict[key]
            for key in ['splines', 'nurbs_curves', 'bezier_curves', 'ellipses']
        )

        if has_entities:
            # PREFERRED: Direct entity generation (bypasses CSV parsing)
            success, output_path, error_msg = generator.generate_from_entities(
                entities_dict, filename, use_minimal_format=use_minimal
            )
            generation_method = 'direct_entity'
        elif csv_metadata:
            # FALLBACK: CSV-based generation
            success, output_path, error_msg = generator.generate(csv_metadata, filename)
            generation_method = 'csv_based'
        else:
            return jsonify({'error': 'No entities or metadata provided'}), 400

        if success:
            output_filename = Path(output_path).name

            return jsonify({
                'success': True,
                'filename': output_filename,
                'download_url': f'/api/download/{output_filename}',
                'generation_method': generation_method,
                'used_minimal_format': use_minimal and not has_advanced_curves
            })
        else:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download generated DXF file."""
    try:
        output_dir = Path(__file__).parent.parent / "output"
        file_path = output_dir / filename

        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/dxf'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/preview', methods=['POST'])
def preview_metadata():
    """Preview formatted metadata before generation."""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')

        if session_id not in sessions:
            return jsonify({'error': 'Session not found'}), 404

        state = sessions[session_id]['state']

        return jsonify({
            'csv_metadata': state.get('formatted_csv', ''),
            'entities': state.get('entities', {}),
            'validation': state.get('validation', {})
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'openai_configured': bool(os.getenv('OPENAI_API_KEY'))
    })


@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    """Get or update user settings."""
    try:
        if request.method == 'GET':
            session_id = request.args.get('session_id', 'default')
            # Get current settings
            settings = settings_manager.get_settings(session_id)
            return jsonify(settings.model_dump())

        elif request.method == 'POST':
            data = request.json
            if not data:
                return jsonify({'error': 'Request body is required'}), 400

            session_id = data.get('session_id', 'default')
            # Update settings - handle None gracefully
            settings_data = data.get('settings') or {}
            updated_settings = settings_manager.update_settings(session_id, settings_data)
            return jsonify({
                'success': True,
                'settings': updated_settings.model_dump()
            })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/reset', methods=['POST'])
def reset_settings():
    """Reset settings to default."""
    try:
        data = request.json
        session_id = data.get('session_id', 'default') if data else 'default'
        reset_result = settings_manager.reset_settings(session_id)
        return jsonify({
            'success': True,
            'settings': reset_result.model_dump()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/augment', methods=['POST'])
def augment_metadata():
    """Augment existing metadata with user modifications."""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        session_id = data.get('session_id', 'default')
        raw_request = data.get('augmentation_request')
        augmentation_request = str(raw_request).strip() if raw_request is not None else ''

        if not augmentation_request:
            return jsonify({'error': 'Augmentation request cannot be empty'}), 400

        if session_id not in sessions:
            return jsonify({'error': 'Session not found'}), 404

        state = sessions[session_id]['state']
        current_entities_dict = state.get('entities', {})

        if not current_entities_dict:
            return jsonify({'error': 'No entities to augment'}), 400

        # Get workflow and augmentation agent
        wf = get_workflow()
        from .agents.entity_extractor import ExtractedEntities
        from .agents import AugmentationAgent

        current_entities = ExtractedEntities(**current_entities_dict)
        augmentation_agent = AugmentationAgent(wf.llm)

        # Apply augmentation
        augmentation_result = augmentation_agent.augment(
            augmentation_request=augmentation_request,
            current_entities=current_entities,
            original_description=state.get('original_user_input', '')
        )

        if augmentation_result.success:
            # Update state with modified entities
            state['entities'] = augmentation_result.modified_entities.model_dump()

            # Reformat metadata
            formatted_csv = wf.metadata_formatter.format(augmentation_result.modified_entities)
            state['formatted_csv'] = formatted_csv

            # Update session
            sessions[session_id]['state'] = state

            return jsonify({
                'success': True,
                'changes_made': augmentation_result.changes_made,
                'warnings': augmentation_result.warnings,
                'summary': augmentation_result.summary,
                'csv_metadata': formatted_csv
            })
        else:
            return jsonify({
                'success': False,
                'error': augmentation_result.summary,
                'warnings': augmentation_result.warnings
            }), 400

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Mayo Integration Endpoints
# ============================================================================

@app.route('/api/formats', methods=['GET'])
def get_formats():
    """Get available export formats with categories and availability status."""
    registry = get_converter_registry()
    formats_data = registry.get_available_formats()

    # Also include legacy flat format list for backwards compatibility
    formats_data['export_formats'] = SUPPORTED_EXPORT_FORMATS
    formats_data['default_format'] = 'DXF'

    return jsonify(formats_data)


@app.route('/api/convert', methods=['POST'])
def convert_file():
    """Convert a generated file to another format."""
    try:
        data = request.json
        source_filename = data.get('filename')
        target_format = data.get('format', 'STEP')

        if not source_filename:
            return jsonify({'error': 'No filename provided'}), 400

        converter = get_mayo_converter()
        if converter is None:
            return jsonify({'error': 'Converter not available'}), 503

        # Find source file
        output_dir = Path(__file__).parent.parent / "output"
        source_path = output_dir / source_filename

        if not source_path.exists():
            return jsonify({'error': f'Source file not found: {source_filename}'}), 404

        # Convert
        success, output_path, error = converter.convert_dxf_to_format(
            str(source_path), target_format, str(output_dir)
        )

        if success:
            output_filename = Path(output_path).name
            return jsonify({
                'success': True,
                'filename': output_filename,
                'download_url': f'/api/download/{output_filename}'
            })
        else:
            return jsonify({
                'success': False,
                'error': error
            }), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-and-convert', methods=['POST'])
def generate_and_convert():
    """Generate DXF and optionally convert to another format."""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        csv_metadata = data.get('csv_metadata', '')
        target_format = data.get('format', 'DXF')  # Default to DXF
        filename = data.get('filename', None)
        entities_dict = data.get('entities')

        # Get from session if not provided
        if not entities_dict and session_id in sessions:
            state = sessions[session_id]['state']
            entities_dict = state.get('entities', {})
            if not csv_metadata:
                csv_metadata = state.get('formatted_csv', '')

        generator = get_dxf_generator()

        # Check if we have entities for direct generation
        has_entities = entities_dict and any(
            key in entities_dict and entities_dict[key]
            for key in ['lines', 'circles', 'arcs', 'polylines', 'hatches',
                       'splines', 'nurbs_curves', 'bezier_curves', 'ellipses',
                       'polylines_with_curves']
        )

        # Generate DXF - prefer direct entity generation
        if has_entities:
            success, dxf_path, error_msg = generator.generate_from_entities(
                entities_dict, filename, use_minimal_format=True
            )
        elif csv_metadata:
            success, dxf_path, error_msg = generator.generate(csv_metadata, filename)
        else:
            return jsonify({'error': 'No entities or metadata provided'}), 400

        if not success:
            return jsonify({
                'success': False,
                'error': f'DXF generation failed: {error_msg}'
            }), 500

        dxf_filename = Path(dxf_path).name

        # If target is DXF, we're done
        if target_format.upper() == 'DXF':
            return jsonify({
                'success': True,
                'filename': dxf_filename,
                'format': 'DXF',
                'download_url': f'/api/download/{dxf_filename}'
            })

        # Convert to target format
        converter = get_mayo_converter()
        if converter is None:
            return jsonify({
                'success': True,
                'filename': dxf_filename,
                'format': 'DXF',
                'download_url': f'/api/download/{dxf_filename}',
                'warning': 'Converter not available, returning DXF'
            })

        success, output_path, error = converter.convert_dxf_to_format(
            dxf_path, target_format
        )

        if success:
            output_filename = Path(output_path).name
            return jsonify({
                'success': True,
                'filename': output_filename,
                'format': target_format,
                'download_url': f'/api/download/{output_filename}',
                'dxf_filename': dxf_filename,
                'dxf_download_url': f'/api/download/{dxf_filename}'
            })
        else:
            return jsonify({
                'success': True,
                'filename': dxf_filename,
                'format': 'DXF',
                'download_url': f'/api/download/{dxf_filename}',
                'warning': f'Conversion to {target_format} failed: {error}'
            })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-multi', methods=['POST'])
def generate_multi():
    """Generate DXF and convert to multiple formats simultaneously.

    Request body:
    {
        "session_id": "...",
        "csv_metadata": "...",
        "formats": ["DXF", "STEP", "PDF", "STL"],
        "filename": "optional_base_name"
    }

    Response:
    {
        "success": true,
        "dxf": {"filename": "drawing.dxf", "download_url": "/api/download/drawing.dxf"},
        "conversions": {
            "STEP": {"success": true, "filename": "drawing.step", "download_url": "..."},
            "PDF": {"success": true, "filename": "drawing.pdf", "download_url": "..."},
            "STL": {"success": false, "error": "Conversion failed"}
        }
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        session_id = data.get('session_id', 'default')
        csv_metadata = data.get('csv_metadata') or ''
        formats = data.get('formats', ['DXF'])
        filename = data.get('filename')

        # Ensure formats is a list
        if formats is None:
            formats = ['DXF']
        elif isinstance(formats, str):
            formats = [formats]
        elif not isinstance(formats, list):
            formats = ['DXF']

        # Handle empty list
        if not formats:
            formats = ['DXF']

        # Filter out None and non-string values, normalize to uppercase
        formats = [str(f).upper() for f in formats if f is not None and isinstance(f, (str, int, float))]

        # If all formats were invalid, default to DXF
        if not formats:
            formats = ['DXF']

        # Ensure DXF is always included
        if 'DXF' not in formats:
            formats.insert(0, 'DXF')

        # Get entities and metadata from session if not provided
        entities_dict = data.get('entities')
        if not entities_dict and session_id in sessions:
            state = sessions[session_id]['state']
            entities_dict = state.get('entities', {})
            if not csv_metadata:
                csv_metadata = state.get('formatted_csv', '')

        generator = get_dxf_generator()

        # Check if we have entities for direct generation
        has_entities = entities_dict and any(
            key in entities_dict and entities_dict[key]
            for key in ['lines', 'circles', 'arcs', 'polylines', 'hatches',
                       'splines', 'nurbs_curves', 'bezier_curves', 'ellipses',
                       'polylines_with_curves']
        )

        # Generate DXF - prefer direct entity generation
        if has_entities:
            success, dxf_path, error_msg = generator.generate_from_entities(
                entities_dict, filename, use_minimal_format=True
            )
        elif csv_metadata:
            success, dxf_path, error_msg = generator.generate(csv_metadata, filename)
        else:
            return jsonify({'error': 'No entities or metadata provided'}), 400

        if not success:
            return jsonify({
                'success': False,
                'error': f'DXF generation failed: {error_msg}'
            }), 500

        dxf_filename = Path(dxf_path).name
        output_dir = Path(dxf_path).parent

        # Build response for DXF
        response = {
            'success': True,
            'dxf': {
                'filename': dxf_filename,
                'download_url': f'/api/download/{dxf_filename}'
            },
            'conversions': {}
        }

        # If only DXF requested, return now
        if formats == ['DXF']:
            return jsonify(response)

        # Get converter registry and convert to other formats
        registry = get_converter_registry()

        # Remove DXF from conversion list (already have it)
        conversion_formats = [f for f in formats if f != 'DXF']

        # Convert to multiple formats
        conversion_results = registry.convert_multiple(
            dxf_path,
            conversion_formats,
            str(output_dir),
            parallel=True
        )

        # Build conversions response
        for fmt, result in conversion_results.items():
            if result.get('success'):
                response['conversions'][fmt] = {
                    'success': True,
                    'filename': result['filename'],
                    'download_url': f'/api/download/{result["filename"]}'
                }
            else:
                response['conversions'][fmt] = {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }

        return jsonify(response)

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/converters/status', methods=['GET'])
def converter_status():
    """Get status of all converters."""
    registry = get_converter_registry()
    return jsonify(registry.get_converter_status())


@app.route('/api/view', methods=['POST'])
def launch_viewer():
    """Launch the 3D viewer for a file."""
    try:
        data = request.json
        filename = data.get('filename')
        use_fallback = data.get('use_fallback', False)

        if not filename:
            return jsonify({'error': 'No filename provided'}), 400

        # Find file
        output_dir = Path(__file__).parent.parent / "output"
        file_path = output_dir / filename

        if not file_path.exists():
            return jsonify({'error': f'File not found: {filename}'}), 404

        launcher = get_viewer_launcher()

        # Check if format is viewable
        if not launcher.can_view(str(file_path)):
            return jsonify({
                'error': f'File format not supported for viewing. Supported: GLB, GLTF, OBJ, PLY, STL, OFF'
            }), 400

        # Check if viewer is available
        if not launcher.is_available() or use_fallback:
            # Try fallback viewer
            success, error = launcher.launch_fallback_viewer(str(file_path))
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Fallback viewer launched for {filename}',
                    'fallback': True
                })
            else:
                display_error = launcher.get_display_error()
                return jsonify({
                    'success': False,
                    'error': display_error or error or 'Viewer not available',
                    'details': launcher.get_viewer_status_details()
                }), 503

        # Launch main viewer
        try:
            process = launcher.launch(str(file_path))
            return jsonify({
                'success': True,
                'message': f'Viewer launched for {filename}',
                'pid': process.pid
            })
        except Exception as e:
            # Try fallback on failure
            success, error = launcher.launch_fallback_viewer(str(file_path))
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Fallback viewer launched for {filename}',
                    'fallback': True
                })
            return jsonify({
                'success': False,
                'error': f'Main viewer failed: {str(e)}. Fallback also failed: {error}'
            }), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/viewer/status', methods=['GET'])
def viewer_status():
    """Check if viewer is available."""
    launcher = get_viewer_launcher()
    status_details = launcher.get_viewer_status_details()

    return jsonify({
        'available': launcher.is_available(),
        'supported_formats': launcher.get_supported_formats(),
        'details': status_details,
        'fallback_available': len(status_details.get('fallback_viewers', [])) > 0
    })


# ============================================================================
# 2D Viewer Endpoints
# ============================================================================

@app.route('/api/view-2d', methods=['POST'])
def view_2d():
    """Generate SVG for 2D viewing or launch external viewer.

    Request body:
    {
        "filename": "drawing.dxf",
        "open_external": false  // Optional: launch external viewer instead
    }

    Response:
    {
        "success": true,
        "svg": "<svg>...</svg>",  // Only if open_external is false
        "message": "..."  // Only if open_external is true
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        filename = data.get('filename')
        open_external = data.get('open_external', False)

        if not filename:
            return jsonify({'error': 'No filename provided'}), 400

        # Find file
        output_dir = Path(__file__).parent.parent / "output"
        file_path = output_dir / filename

        if not file_path.exists():
            return jsonify({'error': f'File not found: {filename}'}), 404

        viewer = get_viewer_2d()

        if open_external:
            # Launch external viewer
            success, error = viewer.launch_external_viewer(str(file_path))
            if success:
                return jsonify({
                    'success': True,
                    'message': f'External viewer launched for {filename}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': error
                }), 500
        else:
            # Generate SVG for in-page display
            ext = file_path.suffix.lower()

            if ext == '.dxf':
                success, svg, error = viewer.from_dxf(str(file_path))
            elif ext == '.svg':
                # Already SVG, just return content
                svg = file_path.read_text()
                success, error = True, ""
            else:
                return jsonify({
                    'error': f'Unsupported format for 2D viewing: {ext}'
                }), 400

            if success:
                return jsonify({
                    'success': True,
                    'svg': svg,
                    'filename': filename
                })
            else:
                return jsonify({
                    'success': False,
                    'error': error
                }), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/preview-2d', methods=['POST'])
def preview_2d():
    """Generate SVG preview from metadata directly (no file needed).

    Request body:
    {
        "session_id": "...",
        "csv_metadata": "LINE, 0, 0, 100, 100\nCIRCLE, 50, 50, 25",
        "entities": {...}  // Alternative: direct entities dict
    }

    Response:
    {
        "success": true,
        "svg": "<svg>...</svg>"
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        session_id = data.get('session_id', 'default')
        csv_metadata = data.get('csv_metadata', '')
        entities = data.get('entities')

        # Try to get from session if not provided
        if not csv_metadata and not entities and session_id in sessions:
            state = sessions[session_id]['state']
            csv_metadata = state.get('formatted_csv', '')
            entities = state.get('entities')

        viewer = get_viewer_2d()

        if entities:
            # Generate from entities dict directly
            success, svg, error = viewer.from_entities(entities)
        elif csv_metadata:
            # Generate from CSV metadata
            success, svg, error = viewer.from_metadata(csv_metadata)
        else:
            return jsonify({'error': 'No metadata or entities provided'}), 400

        if success:
            return jsonify({
                'success': True,
                'svg': svg
            })
        else:
            return jsonify({
                'success': False,
                'error': error
            }), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/viewer/2d-status', methods=['GET'])
def viewer_2d_status():
    """Check 2D viewer availability and capabilities."""
    viewer = get_viewer_2d()
    return jsonify({
        'available': True,  # SVG generation always available
        'supported_formats': ['.dxf', '.svg'],
        'external_viewers_available': True,  # Could check actual availability
        'features': {
            'svg_generation': True,
            'metadata_preview': True,
            'external_launch': True
        }
    })


def main():
    """Run the Flask server."""
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    print(f"Starting DXF Generator Chatbot on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    main()
