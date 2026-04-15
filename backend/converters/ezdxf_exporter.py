"""Export DXF files to 2D formats (PDF, SVG, PNG) using ezdxf drawing addon."""

import os
from pathlib import Path
from typing import Tuple, Optional

# Check if ezdxf drawing addon is available
_DRAWING_AVAILABLE = False
_DRAWING_ERROR = None

try:
    import ezdxf
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.config import Configuration
    from ezdxf.addons.drawing import matplotlib as mpl_backend
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    _DRAWING_AVAILABLE = True
except ImportError as e:
    _DRAWING_ERROR = str(e)


class EzdxfExporter:
    """Export DXF files to 2D formats using ezdxf drawing addon."""

    SUPPORTED_FORMATS = ['PDF', 'SVG', 'PNG']

    FORMAT_EXTENSIONS = {
        'PDF': '.pdf',
        'SVG': '.svg',
        'PNG': '.png',
    }

    def __init__(self):
        """Initialize the exporter."""
        self._available = _DRAWING_AVAILABLE
        self._error = _DRAWING_ERROR

    def is_available(self) -> bool:
        """Check if the exporter is available."""
        return self._available

    def get_unavailable_reason(self) -> Optional[str]:
        """Get the reason why the exporter is unavailable."""
        if self._available:
            return None
        return f"ezdxf drawing addon not available: {self._error}. Install with: pip install ezdxf[draw] matplotlib"

    def supports_format(self, format_name: str) -> bool:
        """Check if a format is supported."""
        return format_name.upper() in self.SUPPORTED_FORMATS

    def export(self, dxf_file: str, output_format: str,
               output_dir: Optional[str] = None,
               dpi: int = 300,
               background_color: str = '#FFFFFF') -> Tuple[bool, str, str]:
        """Export DXF file to 2D format.

        Args:
            dxf_file: Path to input DXF file
            output_format: Target format (PDF, SVG, PNG)
            output_dir: Output directory. If None, uses same directory as input.
            dpi: Resolution for raster formats (PNG)
            background_color: Background color for the export

        Returns:
            Tuple of (success, output_path, error_message)
        """
        if not self._available:
            return False, "", self.get_unavailable_reason()

        output_format = output_format.upper()
        if output_format not in self.SUPPORTED_FORMATS:
            return False, "", f"Unsupported format: {output_format}"

        dxf_path = Path(dxf_file)
        if not dxf_path.exists():
            return False, "", f"Input file not found: {dxf_file}"

        if output_dir is None:
            output_dir = dxf_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        ext = self.FORMAT_EXTENSIONS[output_format]
        output_path = output_dir / f"{dxf_path.stem}{ext}"

        try:
            # Load the DXF document
            doc = ezdxf.readfile(str(dxf_path))

            # Get the modelspace
            msp = doc.modelspace()

            # Count entities to validate DXF has content
            entity_count = len(list(msp))
            if entity_count == 0:
                return False, "", f"DXF file has no entities in modelspace: {dxf_file}"

            # Create rendering context
            ctx = RenderContext(doc)

            # Create a figure with automatic sizing
            fig = plt.figure()
            ax = fig.add_axes([0, 0, 1, 1])
            ax.set_aspect('equal')

            # Create the backend with the axes
            backend = mpl_backend.MatplotlibBackend(ax)

            # Create configuration for the frontend
            config = Configuration()

            # Filter function to skip problematic text entities
            def entity_filter(entity):
                dxf_type = entity.dxftype()
                # Skip text entities with invalid attributes
                if dxf_type == 'TEXT':
                    try:
                        insert = entity.dxf.get('insert')
                        if insert is None:
                            return False
                        # Check style attribute - set default if None
                        style = entity.dxf.get('style')
                        if style is None:
                            entity.dxf.style = 'Standard'
                    except Exception:
                        return False
                # Handle MTEXT entities similarly
                elif dxf_type == 'MTEXT':
                    try:
                        insert = entity.dxf.get('insert')
                        if insert is None:
                            return False
                        style = entity.dxf.get('style')
                        if style is None:
                            entity.dxf.style = 'Standard'
                    except Exception:
                        return False
                return True

            # Create frontend and draw the entities
            frontend = Frontend(ctx, backend, config)
            frontend.draw_layout(msp, filter_func=entity_filter)

            # Remove axis
            ax.set_axis_off()

            # Set background color
            fig.patch.set_facecolor(background_color)
            ax.set_facecolor(background_color)

            # Auto-fit the view
            ax.autoscale(enable=True)

            # Handle degenerate axis limits (empty or minimal drawings)
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            if xlim[0] == xlim[1] or ylim[0] == ylim[1]:
                # Set default viewport for degenerate cases
                ax.set_xlim(-10, 10)
                ax.set_ylim(-10, 10)

            # Save based on format
            if output_format == 'PNG':
                fig.savefig(str(output_path), dpi=dpi, bbox_inches='tight',
                           facecolor=background_color, edgecolor='none')
            elif output_format == 'PDF':
                fig.savefig(str(output_path), format='pdf', bbox_inches='tight',
                           facecolor=background_color, edgecolor='none')
            elif output_format == 'SVG':
                fig.savefig(str(output_path), format='svg', bbox_inches='tight',
                           facecolor=background_color, edgecolor='none')

            plt.close(fig)

            if output_path.exists():
                return True, str(output_path), ""
            else:
                return False, "", "Export completed but output file not found"

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return False, "", f"Export failed for {dxf_file}: {str(e)}\nDetails:\n{error_details}"

    @classmethod
    def get_supported_formats(cls) -> list:
        """Get list of supported export formats."""
        return cls.SUPPORTED_FORMATS.copy()
