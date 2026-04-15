"""DWG conversion using ODA File Converter."""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Tuple, Optional, List


class ODAConverter:
    """Convert DXF files to DWG format using ODA File Converter.

    The ODA File Converter is a free tool from Open Design Alliance that can
    convert between DXF and DWG formats. It must be installed separately.

    Download from: https://www.opendesign.com/guestfiles/oda_file_converter
    """

    SUPPORTED_FORMATS = ['DWG']

    # Common installation paths for ODA File Converter
    DEFAULT_PATHS = [
        '/usr/bin/ODAFileConverter',
        '/usr/local/bin/ODAFileConverter',
        '/opt/ODAFileConverter/ODAFileConverter',
        os.path.expanduser('~/ODAFileConverter/ODAFileConverter'),
        # Windows paths (for WSL compatibility)
        '/mnt/c/Program Files/ODA/ODAFileConverter/ODAFileConverter.exe',
        '/mnt/c/Program Files (x86)/ODA/ODAFileConverter/ODAFileConverter.exe',
    ]

    # DWG version options
    DWG_VERSIONS = {
        '2018': 'ACAD2018',
        '2013': 'ACAD2013',
        '2010': 'ACAD2010',
        '2007': 'ACAD2007',
        '2004': 'ACAD2004',
        '2000': 'ACAD2000',
    }

    def __init__(self, converter_path: Optional[str] = None):
        """Initialize the ODA converter.

        Args:
            converter_path: Path to ODAFileConverter binary. If None, searches default paths.
        """
        self._converter_path = None
        self._available = False
        self._error = None

        if converter_path:
            if os.path.exists(converter_path) and os.access(converter_path, os.X_OK):
                self._converter_path = converter_path
                self._available = True
            else:
                self._error = f"ODA File Converter not found at: {converter_path}"
        else:
            # Search default paths
            for path in self.DEFAULT_PATHS:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    self._converter_path = path
                    self._available = True
                    break

            if not self._available:
                # Try to find it in PATH
                found = shutil.which('ODAFileConverter')
                if found:
                    self._converter_path = found
                    self._available = True
                else:
                    self._error = "ODA File Converter not installed. Download from: https://www.opendesign.com/guestfiles/oda_file_converter"

    def is_available(self) -> bool:
        """Check if the converter is available."""
        return self._available

    def get_unavailable_reason(self) -> Optional[str]:
        """Get the reason why the converter is unavailable."""
        return self._error

    def supports_format(self, format_name: str) -> bool:
        """Check if a format is supported."""
        return format_name.upper() in self.SUPPORTED_FORMATS

    def convert(self, dxf_file: str, output_dir: Optional[str] = None,
                dwg_version: str = '2018', timeout: int = 60) -> Tuple[bool, str, str]:
        """Convert DXF file to DWG format.

        Args:
            dxf_file: Path to input DXF file
            output_dir: Output directory. If None, uses same directory as input.
            dwg_version: Target DWG version (2018, 2013, 2010, 2007, 2004, 2000)
            timeout: Timeout in seconds for conversion

        Returns:
            Tuple of (success, output_path, error_message)
        """
        if not self._available:
            return False, "", self._error

        dxf_path = Path(dxf_file)
        if not dxf_path.exists():
            return False, "", f"Input file not found: {dxf_file}"

        if dxf_path.suffix.lower() != '.dxf':
            return False, "", f"Input file must be a DXF file: {dxf_file}"

        if output_dir is None:
            output_dir = dxf_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        # Get DWG version string
        version_str = self.DWG_VERSIONS.get(dwg_version, 'ACAD2018')

        output_path = output_dir / f"{dxf_path.stem}.dwg"

        try:
            # ODA File Converter command line syntax:
            # ODAFileConverter "Input Folder" "Output Folder" version type recurse audit [filter]
            # type: DXF = 0, DWG = 1
            # recurse: 0 = no, 1 = yes
            # audit: 0 = no, 1 = yes

            # Create a temporary directory for the single file conversion
            import tempfile
            with tempfile.TemporaryDirectory() as temp_input_dir:
                # Copy the DXF file to temp directory
                temp_input = Path(temp_input_dir) / dxf_path.name
                shutil.copy2(dxf_path, temp_input)

                cmd = [
                    self._converter_path,
                    temp_input_dir,      # Input folder
                    str(output_dir),     # Output folder
                    version_str,         # Output version
                    'DWG',               # Output type
                    '0',                 # Don't recurse
                    '1'                  # Audit input files
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                if output_path.exists():
                    return True, str(output_path), ""
                else:
                    error_msg = result.stderr or result.stdout or "Conversion completed but output file not found"
                    return False, "", error_msg

        except subprocess.TimeoutExpired:
            return False, "", f"Conversion timed out after {timeout} seconds"
        except Exception as e:
            return False, "", f"Conversion failed: {str(e)}"

    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """Get list of supported export formats."""
        return cls.SUPPORTED_FORMATS.copy()

    @classmethod
    def get_supported_versions(cls) -> List[str]:
        """Get list of supported DWG versions."""
        return list(cls.DWG_VERSIONS.keys())
