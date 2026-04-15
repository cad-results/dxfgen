"""Mayo-conv wrapper for file format conversion."""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List

# Supported formats from mayo-conv --system-info
SUPPORTED_IMPORT_FORMATS = ['DXF', 'STEP', 'IGES', 'OCCBREP', 'STL', 'GLTF', 'OBJ', 'OFF', 'PLY']
SUPPORTED_EXPORT_FORMATS = ['STEP', 'IGES', 'OCCBREP', 'STL', 'VRML', 'GLTF', 'OBJ', 'OFF', 'PLY', 'Image']

# File extensions mapping
FORMAT_EXTENSIONS = {
    'STEP': ['.step', '.stp'],
    'IGES': ['.iges', '.igs'],
    'OCCBREP': ['.brep'],
    'STL': ['.stl'],
    'VRML': ['.vrml', '.wrl'],
    'GLTF': ['.gltf', '.glb'],
    'OBJ': ['.obj'],
    'OFF': ['.off'],
    'PLY': ['.ply'],
    'DXF': ['.dxf'],
    'Image': ['.png', '.jpg', '.jpeg']
}


class MayoConverter:
    """Wrapper class for mayo-conv CLI tool."""

    def __init__(self, mayo_conv_path: Optional[str] = None):
        """Initialize the converter.

        Args:
            mayo_conv_path: Path to mayo-conv binary. If None, uses default location.
        """
        if mayo_conv_path is None:
            self.mayo_conv_path = Path(__file__).parent.parent / "bin" / "mayo-conv"
        else:
            self.mayo_conv_path = Path(mayo_conv_path)

        if not self.mayo_conv_path.exists():
            raise FileNotFoundError(f"mayo-conv not found at {self.mayo_conv_path}")

        if not os.access(self.mayo_conv_path, os.X_OK):
            raise PermissionError(f"mayo-conv is not executable: {self.mayo_conv_path}")

    def convert(self, input_file: str, output_file: str,
                timeout: int = 60) -> Tuple[bool, str, str]:
        """Convert a file from one format to another.

        Args:
            input_file: Path to input file
            output_file: Path to output file (format determined by extension)
            timeout: Timeout in seconds for conversion

        Returns:
            Tuple of (success, output_path, error_message)
        """
        input_path = Path(input_file)
        output_path = Path(output_file)

        if not input_path.exists():
            return False, "", f"Input file not found: {input_file}"

        # Validate output format
        output_ext = output_path.suffix.lower()
        output_format = self._get_format_from_extension(output_ext)
        if output_format not in SUPPORTED_EXPORT_FORMATS:
            return False, "", f"Unsupported output format: {output_ext}"

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build command
        cmd = [
            str(self.mayo_conv_path),
            str(input_path),
            '-e', str(output_path),
            '--no-progress'
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0 and output_path.exists():
                return True, str(output_path), ""
            else:
                error_msg = result.stderr or result.stdout or "Unknown conversion error"
                return False, "", error_msg

        except subprocess.TimeoutExpired:
            return False, "", f"Conversion timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)

    def convert_dxf_to_format(self, dxf_file: str, output_format: str,
                              output_dir: Optional[str] = None) -> Tuple[bool, str, str]:
        """Convert a DXF file to specified format.

        Args:
            dxf_file: Path to DXF file
            output_format: Target format (e.g., 'STEP', 'OBJ', 'STL')
            output_dir: Output directory. If None, uses same directory as input.

        Returns:
            Tuple of (success, output_path, error_message)
        """
        dxf_path = Path(dxf_file)

        if output_dir is None:
            output_dir = dxf_path.parent
        else:
            output_dir = Path(output_dir)

        # Get appropriate extension
        ext = self._get_extension_for_format(output_format)
        if ext is None:
            return False, "", f"Unknown format: {output_format}"

        output_file = output_dir / f"{dxf_path.stem}{ext}"

        return self.convert(str(dxf_path), str(output_file))

    def batch_convert(self, input_files: List[str], output_format: str,
                      output_dir: str) -> List[Tuple[str, bool, str, str]]:
        """Convert multiple files to the same format.

        Args:
            input_files: List of input file paths
            output_format: Target format for all files
            output_dir: Output directory for all converted files

        Returns:
            List of (input_file, success, output_path, error) tuples
        """
        results = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for input_file in input_files:
            success, out_path, error = self.convert_dxf_to_format(
                input_file, output_format, str(output_path)
            )
            results.append((input_file, success, out_path, error))

        return results

    @staticmethod
    def _get_format_from_extension(ext: str) -> Optional[str]:
        """Get format name from file extension."""
        ext = ext.lower()
        for format_name, extensions in FORMAT_EXTENSIONS.items():
            if ext in extensions:
                return format_name
        return None

    @staticmethod
    def _get_extension_for_format(format_name: str) -> Optional[str]:
        """Get primary file extension for a format."""
        format_name = format_name.upper()
        if format_name in FORMAT_EXTENSIONS:
            return FORMAT_EXTENSIONS[format_name][0]
        return None

    @staticmethod
    def get_supported_export_formats() -> List[str]:
        """Get list of supported export formats."""
        return SUPPORTED_EXPORT_FORMATS.copy()

    @staticmethod
    def get_supported_import_formats() -> List[str]:
        """Get list of supported import formats."""
        return SUPPORTED_IMPORT_FORMATS.copy()
