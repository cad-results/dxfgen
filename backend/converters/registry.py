"""Unified converter registry for multi-format CAD conversion."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import converters
from ..mayo import MayoConverter, SUPPORTED_EXPORT_FORMATS as MAYO_EXPORT_FORMATS
from .ezdxf_exporter import EzdxfExporter
from .oda_converter import ODAConverter


# Format categories for UI organization
FORMAT_CATEGORIES = {
    'source': {
        'label': 'Source Format',
        'description': 'Original DXF format (always included)',
        'formats': [
            {'name': 'DXF', 'extension': '.dxf', 'description': 'AutoCAD Drawing Exchange Format', 'converter': 'source'}
        ]
    },
    '3d_cad': {
        'label': '3D CAD Formats',
        'description': 'Industry-standard 3D CAD exchange formats',
        'formats': [
            {'name': 'STEP', 'extension': '.step', 'description': 'Industry Standard CAD Exchange', 'converter': 'mayo'},
            {'name': 'IGES', 'extension': '.igs', 'description': 'Legacy CAD Exchange', 'converter': 'mayo'},
            {'name': 'STL', 'extension': '.stl', 'description': '3D Printing / Mesh', 'converter': 'mayo'},
            {'name': 'OBJ', 'extension': '.obj', 'description': '3D Modeling / Mesh', 'converter': 'mayo'},
            {'name': 'GLTF', 'extension': '.gltf', 'description': 'Web 3D / AR/VR', 'converter': 'mayo'},
            {'name': 'PLY', 'extension': '.ply', 'description': 'Point Cloud / Mesh', 'converter': 'mayo'},
            {'name': 'OFF', 'extension': '.off', 'description': 'Object File Format', 'converter': 'mayo'},
        ]
    },
    '2d_export': {
        'label': '2D Export Formats',
        'description': 'Documentation and preview formats',
        'formats': [
            {'name': 'PDF', 'extension': '.pdf', 'description': 'Documentation / Print', 'converter': 'ezdxf'},
            {'name': 'SVG', 'extension': '.svg', 'description': 'Web Graphics / Vector', 'converter': 'ezdxf'},
            {'name': 'PNG', 'extension': '.png', 'description': 'Preview Image / Raster', 'converter': 'ezdxf'},
        ]
    },
    'dwg': {
        'label': 'DWG Format',
        'description': 'AutoCAD native format',
        'formats': [
            {'name': 'DWG', 'extension': '.dwg', 'description': 'AutoCAD Native Format', 'converter': 'oda'}
        ]
    }
}


class ConverterRegistry:
    """Unified facade for all format converters.

    Provides a single interface for converting DXF files to multiple formats
    using the appropriate converter for each format.
    """

    def __init__(self, mayo_conv_path: Optional[str] = None, oda_path: Optional[str] = None):
        """Initialize the converter registry.

        Args:
            mayo_conv_path: Path to mayo-conv binary. If None, uses default location.
            oda_path: Path to ODA File Converter. If None, searches default paths.
        """
        # Initialize converters
        self._mayo_converter: Optional[MayoConverter] = None
        self._mayo_error: Optional[str] = None

        self._ezdxf_exporter: Optional[EzdxfExporter] = None
        self._ezdxf_error: Optional[str] = None

        self._oda_converter: Optional[ODAConverter] = None
        self._oda_error: Optional[str] = None

        # Initialize Mayo converter
        try:
            self._mayo_converter = MayoConverter(mayo_conv_path)
        except (FileNotFoundError, PermissionError) as e:
            self._mayo_error = str(e)

        # Initialize ezdxf exporter
        self._ezdxf_exporter = EzdxfExporter()
        if not self._ezdxf_exporter.is_available():
            self._ezdxf_error = self._ezdxf_exporter.get_unavailable_reason()

        # Initialize ODA converter
        self._oda_converter = ODAConverter(oda_path)
        if not self._oda_converter.is_available():
            self._oda_error = self._oda_converter.get_unavailable_reason()

        # Build format availability map
        self._format_availability = self._build_format_availability()

    def _build_format_availability(self) -> Dict[str, Dict[str, Any]]:
        """Build a map of format availability."""
        availability = {}

        for category, info in FORMAT_CATEGORIES.items():
            for fmt in info['formats']:
                name = fmt['name']
                converter = fmt['converter']

                if converter == 'source':
                    # DXF is always available (source format)
                    availability[name] = {
                        'available': True,
                        'reason': None,
                        'converter': 'source',
                        'category': category
                    }
                elif converter == 'mayo':
                    available = self._mayo_converter is not None
                    availability[name] = {
                        'available': available,
                        'reason': self._mayo_error if not available else None,
                        'converter': 'mayo',
                        'category': category
                    }
                elif converter == 'ezdxf':
                    available = self._ezdxf_exporter is not None and self._ezdxf_exporter.is_available()
                    availability[name] = {
                        'available': available,
                        'reason': self._ezdxf_error if not available else None,
                        'converter': 'ezdxf',
                        'category': category
                    }
                elif converter == 'oda':
                    available = self._oda_converter is not None and self._oda_converter.is_available()
                    availability[name] = {
                        'available': available,
                        'reason': self._oda_error if not available else None,
                        'converter': 'oda',
                        'category': category
                    }

        return availability

    def get_available_formats(self) -> Dict[str, Any]:
        """Get categorized format information with availability status.

        Returns dict with structure:
        {
            'categories': {
                'source': {...},
                '3d_cad': {...},
                '2d_export': {...},
                'dwg': {...}
            }
        }
        """
        result = {'categories': {}}

        for category, info in FORMAT_CATEGORIES.items():
            formats = []
            for fmt in info['formats']:
                name = fmt['name']
                availability = self._format_availability.get(name, {})
                formats.append({
                    'name': name,
                    'extension': fmt['extension'],
                    'description': fmt['description'],
                    'available': availability.get('available', False),
                    'reason': availability.get('reason')
                })

            result['categories'][category] = {
                'label': info['label'],
                'description': info['description'],
                'formats': formats
            }

        return result

    def is_format_available(self, format_name: str) -> bool:
        """Check if a specific format is available for conversion."""
        format_name = format_name.upper()
        return self._format_availability.get(format_name, {}).get('available', False)

    def get_format_unavailable_reason(self, format_name: str) -> Optional[str]:
        """Get the reason why a format is unavailable."""
        format_name = format_name.upper()
        return self._format_availability.get(format_name, {}).get('reason')

    def convert(self, dxf_file: str, output_format: str,
                output_dir: Optional[str] = None,
                **kwargs) -> Tuple[bool, str, str]:
        """Convert a DXF file to the specified format.

        Args:
            dxf_file: Path to input DXF file
            output_format: Target format (STEP, PDF, DWG, etc.)
            output_dir: Output directory. If None, uses same directory as input.
            **kwargs: Additional converter-specific options

        Returns:
            Tuple of (success, output_path, error_message)
        """
        output_format = output_format.upper()

        # Check if format is DXF (source - no conversion needed)
        if output_format == 'DXF':
            return True, dxf_file, ""

        # Check availability
        if not self.is_format_available(output_format):
            reason = self.get_format_unavailable_reason(output_format)
            return False, "", reason or f"Format {output_format} is not available"

        # Determine which converter to use
        availability = self._format_availability.get(output_format, {})
        converter_type = availability.get('converter')

        if converter_type == 'mayo':
            return self._mayo_converter.convert_dxf_to_format(dxf_file, output_format, output_dir)

        elif converter_type == 'ezdxf':
            dpi = kwargs.get('dpi', 300)
            background = kwargs.get('background_color', '#FFFFFF')
            return self._ezdxf_exporter.export(dxf_file, output_format, output_dir, dpi, background)

        elif converter_type == 'oda':
            dwg_version = kwargs.get('dwg_version', '2018')
            timeout = kwargs.get('timeout', 60)
            return self._oda_converter.convert(dxf_file, output_dir, dwg_version, timeout)

        else:
            return False, "", f"No converter available for format: {output_format}"

    def convert_multiple(self, dxf_file: str, formats: List[str],
                         output_dir: Optional[str] = None,
                         parallel: bool = True,
                         **kwargs) -> Dict[str, Dict[str, Any]]:
        """Convert a DXF file to multiple formats.

        Args:
            dxf_file: Path to input DXF file
            formats: List of target formats
            output_dir: Output directory. If None, uses same directory as input.
            parallel: If True, run conversions in parallel
            **kwargs: Additional converter-specific options

        Returns:
            Dict mapping format name to conversion result:
            {
                'STEP': {'success': True, 'filename': 'drawing.step', 'download_url': '...'},
                'PDF': {'success': True, 'filename': 'drawing.pdf', 'download_url': '...'},
                'DWG': {'success': False, 'error': 'ODA not installed'}
            }
        """
        results = {}
        dxf_path = Path(dxf_file)

        if output_dir is None:
            output_dir = str(dxf_path.parent)

        # Filter out DXF (handled separately) and unavailable formats
        conversion_formats = []
        for fmt in formats:
            # Skip None or empty format names
            if fmt is None or not isinstance(fmt, str) or not fmt.strip():
                continue

            fmt = fmt.upper().strip()

            if fmt == 'DXF':
                # DXF is the source - always successful
                results['DXF'] = {
                    'success': True,
                    'filename': dxf_path.name,
                    'output_path': str(dxf_path)
                }
            elif fmt not in self._format_availability:
                # Unknown format - report as unsupported
                results[fmt] = {
                    'success': False,
                    'error': f"Unsupported format: {fmt}. Available formats: {', '.join(self._format_availability.keys())}"
                }
            elif not self.is_format_available(fmt):
                results[fmt] = {
                    'success': False,
                    'error': self.get_format_unavailable_reason(fmt) or f"Format {fmt} not available"
                }
            else:
                conversion_formats.append(fmt)

        if not conversion_formats:
            return results

        def convert_single(fmt: str) -> Tuple[str, Dict[str, Any]]:
            success, output_path, error = self.convert(dxf_file, fmt, output_dir, **kwargs)
            if success:
                return fmt, {
                    'success': True,
                    'filename': Path(output_path).name,
                    'output_path': output_path
                }
            else:
                return fmt, {
                    'success': False,
                    'error': error
                }

        if parallel and len(conversion_formats) > 1:
            # Run conversions in parallel
            with ThreadPoolExecutor(max_workers=min(4, len(conversion_formats))) as executor:
                futures = {executor.submit(convert_single, fmt): fmt for fmt in conversion_formats}
                for future in as_completed(futures):
                    fmt, result = future.result()
                    results[fmt] = result
        else:
            # Run conversions sequentially
            for fmt in conversion_formats:
                _, result = convert_single(fmt)
                results[fmt] = result

        return results

    def get_converter_status(self) -> Dict[str, Any]:
        """Get status information about all converters."""
        return {
            'mayo': {
                'available': self._mayo_converter is not None,
                'error': self._mayo_error,
                'formats': MAYO_EXPORT_FORMATS if self._mayo_converter else []
            },
            'ezdxf': {
                'available': self._ezdxf_exporter is not None and self._ezdxf_exporter.is_available(),
                'error': self._ezdxf_error,
                'formats': EzdxfExporter.SUPPORTED_FORMATS if self._ezdxf_exporter and self._ezdxf_exporter.is_available() else []
            },
            'oda': {
                'available': self._oda_converter is not None and self._oda_converter.is_available(),
                'error': self._oda_error,
                'formats': ODAConverter.SUPPORTED_FORMATS if self._oda_converter and self._oda_converter.is_available() else []
            }
        }
