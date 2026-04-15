#!/usr/bin/env python3
"""
DXF Viewer - Interactive 2D visualization for DXF CAD drawings.

Supports viewing DXF files with interactive pan/zoom capabilities.
Works in WSL2 environments with X11 forwarding.

Keyboard Controls:
    S       - Save screenshot
    A/LEFT  - Previous file (browse mode)
    D/RIGHT - Next file (browse mode)
    G       - Toggle grid
    I       - Show file info
    R       - Reset view
    Q/ESC   - Quit viewer

Mouse Controls (matplotlib toolbar):
    Pan     - Click and drag with pan tool
    Zoom    - Scroll wheel or zoom rectangle tool
    Home    - Reset view to fit all
"""

# Configure environment for WSL2 BEFORE importing matplotlib
import os
os.environ.setdefault('MPLBACKEND', 'TkAgg')

import argparse
import glob
import sys
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

try:
    import ezdxf
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing import matplotlib as mpl_backend
    from ezdxf.addons.drawing.config import Configuration
except ImportError:
    print("Error: ezdxf is required. Install with: pip install ezdxf[draw]")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backend_bases import KeyEvent
except ImportError:
    print("Error: matplotlib is required. Install with: pip install matplotlib")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("Error: numpy is required. Install with: pip install numpy")
    sys.exit(1)


class DXFLoader:
    """Handles loading and parsing of DXF files."""

    SUPPORTED_FORMATS = {'.dxf'}

    def __init__(self):
        pass

    def load(self, filepath: str) -> Optional[Any]:
        """Load a DXF file.

        Args:
            filepath: Path to the DXF file

        Returns:
            ezdxf Drawing object or None if loading fails
        """
        path = Path(filepath)
        if not path.exists():
            print(f"Error: File not found: {filepath}")
            return None

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            print(f"Error: Unsupported format: {path.suffix}")
            return None

        try:
            doc = ezdxf.readfile(str(path))
            return doc
        except Exception as e:
            print(f"Error loading DXF file {filepath}: {e}")
            return None

    def get_entity_stats(self, doc: Any) -> Dict[str, int]:
        """Count entities by type in the modelspace.

        Args:
            doc: ezdxf Drawing object

        Returns:
            Dictionary mapping entity type to count
        """
        stats = {}
        msp = doc.modelspace()

        for entity in msp:
            entity_type = entity.dxftype()
            stats[entity_type] = stats.get(entity_type, 0) + 1

        return stats

    def get_extents(self, doc: Any) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Calculate drawing extents (bounding box).

        Args:
            doc: ezdxf Drawing object

        Returns:
            Tuple of ((min_x, min_y), (max_x, max_y))
        """
        msp = doc.modelspace()

        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for entity in msp:
            try:
                bbox = ezdxf.bbox.extents([entity])
                if bbox.has_data:
                    min_x = min(min_x, bbox.extmin.x)
                    min_y = min(min_y, bbox.extmin.y)
                    max_x = max(max_x, bbox.extmax.x)
                    max_y = max(max_y, bbox.extmax.y)
            except Exception:
                pass

        if min_x == float('inf'):
            return ((0, 0), (100, 100))

        return ((min_x, min_y), (max_x, max_y))

    def get_layers(self, doc: Any) -> List[str]:
        """Get list of layers in the document.

        Args:
            doc: ezdxf Drawing object

        Returns:
            List of layer names
        """
        return [layer.dxf.name for layer in doc.layers]

    def get_files_in_directory(self, directory: str) -> List[str]:
        """Get all DXF files in a directory.

        Args:
            directory: Path to directory

        Returns:
            Sorted list of DXF file paths
        """
        directory = Path(directory)
        files = []

        for ext in self.SUPPORTED_FORMATS:
            files.extend(glob.glob(str(directory / f"*{ext}")))
            files.extend(glob.glob(str(directory / f"*{ext.upper()}")))

        return sorted(set(files))


class DXFViewer:
    """Interactive 2D DXF viewer using matplotlib."""

    # Dark theme colors
    BG_COLOR = '#1a1a1a'
    GRID_COLOR = '#333333'
    TEXT_COLOR = '#ffffff'

    def __init__(self):
        self.loader = DXFLoader()

        # Current state
        self.current_doc: Optional[Any] = None
        self.current_file: str = ""
        self.file_list: List[str] = []
        self.file_index: int = 0
        self.browse_mode: bool = False

        # Display state
        self.fig: Optional[plt.Figure] = None
        self.ax: Optional[plt.Axes] = None
        self.show_grid: bool = False
        self.should_exit: bool = False

    def load_file(self, filepath: str) -> bool:
        """Load a DXF file.

        Args:
            filepath: Path to DXF file

        Returns:
            True if loaded successfully
        """
        self.current_file = filepath
        self.current_doc = self.loader.load(filepath)

        if self.current_doc is None:
            return False

        return True

    def _entity_filter(self, entity) -> bool:
        """Filter function to skip problematic entities.

        Args:
            entity: DXF entity

        Returns:
            True if entity should be rendered
        """
        dxf_type = entity.dxftype()

        # Skip TEXT and MTEXT entities - they often cause rendering issues
        # with missing style definitions
        if dxf_type in ('TEXT', 'MTEXT'):
            return False

        return True

    def render(self):
        """Render the current DXF document to the figure."""
        if self.current_doc is None or self.ax is None:
            return

        # Clear axes
        self.ax.clear()

        # Get modelspace
        msp = self.current_doc.modelspace()

        # Count entities (use len() directly, don't consume iterator)
        entity_count = len(msp)
        if entity_count == 0:
            self.ax.text(0.5, 0.5, "Empty drawing (no entities)",
                        transform=self.ax.transAxes,
                        ha='center', va='center',
                        fontsize=14, color=self.TEXT_COLOR)
            self._apply_style()
            return

        try:
            # Create rendering context
            ctx = RenderContext(self.current_doc)

            # Create backend
            backend = mpl_backend.MatplotlibBackend(self.ax)

            # Create configuration
            config = Configuration()

            # Create frontend and draw
            frontend = Frontend(ctx, backend, config)
            frontend.draw_layout(msp, filter_func=self._entity_filter)

        except Exception as e:
            print(f"Warning: Render error: {e}")
            self.ax.text(0.5, 0.5, f"Render error: {e}",
                        transform=self.ax.transAxes,
                        ha='center', va='center',
                        fontsize=10, color='#ff6666')

        # Apply styling
        self._apply_style()

        # Auto-fit view
        self.ax.autoscale(enable=True)
        self.ax.set_aspect('equal')

        # Handle degenerate axis limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        if xlim[0] == xlim[1]:
            self.ax.set_xlim(xlim[0] - 10, xlim[0] + 10)
        if ylim[0] == ylim[1]:
            self.ax.set_ylim(ylim[0] - 10, ylim[0] + 10)

    def _apply_style(self):
        """Apply dark theme styling to the axes."""
        if self.ax is None:
            return

        # Background
        self.ax.set_facecolor(self.BG_COLOR)

        # Grid
        if self.show_grid:
            self.ax.grid(True, color=self.GRID_COLOR, linestyle='-', linewidth=0.5, alpha=0.5)
        else:
            self.ax.grid(False)

        # Axis styling
        self.ax.tick_params(colors=self.TEXT_COLOR)
        for spine in self.ax.spines.values():
            spine.set_color(self.GRID_COLOR)

    def _setup_figure(self):
        """Setup matplotlib figure with dark theme."""
        # Create figure
        self.fig = plt.figure(figsize=(12, 9), facecolor=self.BG_COLOR)
        self.ax = self.fig.add_subplot(111)

        # Set tight layout
        self.fig.tight_layout(pad=1.0)

        # Connect event handlers
        self.fig.canvas.mpl_connect('key_press_event', self._on_key_press)
        self.fig.canvas.mpl_connect('close_event', self._on_close)

        # Update window title
        self._update_title()

    def _update_title(self):
        """Update the window title."""
        if self.fig is None:
            return

        filename = Path(self.current_file).name
        parts = [f"DXF Viewer - {filename}"]

        if self.browse_mode and self.file_list:
            parts.append(f"[{self.file_index + 1}/{len(self.file_list)}]")

        title = " ".join(parts)
        self.fig.canvas.manager.set_window_title(title)

    def _on_key_press(self, event: KeyEvent):
        """Handle keyboard events.

        Args:
            event: matplotlib KeyEvent
        """
        key = event.key.lower() if event.key else ""

        if key in ('q', 'escape'):
            self._exit_viewer()
        elif key == 's':
            self._save_screenshot()
        elif key == 'g':
            self._toggle_grid()
        elif key == 'i':
            self._show_info()
        elif key == 'r':
            self._reset_view()
        elif key in ('a', 'left'):
            self._prev_file()
        elif key in ('d', 'right'):
            self._next_file()
        elif key == 'h':
            self._show_help()

    def _on_close(self, event):
        """Handle window close event."""
        self.should_exit = True

    def _exit_viewer(self):
        """Exit the viewer."""
        self.should_exit = True
        plt.close(self.fig)

    def _save_screenshot(self):
        """Save current view as screenshot."""
        filename = f"screenshot_{Path(self.current_file).stem}.png"
        try:
            self.fig.savefig(filename, dpi=150, facecolor=self.BG_COLOR,
                           edgecolor='none', bbox_inches='tight')
            print(f"\nScreenshot saved: {filename}")
        except Exception as e:
            print(f"\nError saving screenshot: {e}")

    def _toggle_grid(self):
        """Toggle grid visibility."""
        self.show_grid = not self.show_grid
        self._apply_style()
        self.fig.canvas.draw_idle()
        print(f"\nGrid: {'ON' if self.show_grid else 'OFF'}")

    def _show_info(self):
        """Show file information."""
        if self.current_doc is None:
            return

        stats = self.loader.get_entity_stats(self.current_doc)
        layers = self.loader.get_layers(self.current_doc)

        print("\n" + "=" * 50)
        print(f"File: {self.current_file}")
        print("=" * 50)
        print(f"DXF Version: {self.current_doc.dxfversion}")
        print(f"Layers: {len(layers)}")
        print(f"  {', '.join(layers[:5])}" + ("..." if len(layers) > 5 else ""))
        print(f"Entities:")
        for entity_type, count in sorted(stats.items()):
            print(f"  {entity_type}: {count}")
        print(f"Total: {sum(stats.values())} entities")
        print("=" * 50)

    def _reset_view(self):
        """Reset view to fit all entities."""
        if self.ax is None:
            return
        self.ax.autoscale(enable=True)
        self.ax.set_aspect('equal')
        self.fig.canvas.draw_idle()
        print("\nView reset")

    def _prev_file(self):
        """Switch to previous file in browse mode."""
        if not self.browse_mode or len(self.file_list) <= 1:
            return

        self.file_index = (self.file_index - 1) % len(self.file_list)
        self._load_and_render_current()

    def _next_file(self):
        """Switch to next file in browse mode."""
        if not self.browse_mode or len(self.file_list) <= 1:
            return

        self.file_index = (self.file_index + 1) % len(self.file_list)
        self._load_and_render_current()

    def _load_and_render_current(self):
        """Load and render the current file in the list."""
        if self.load_file(self.file_list[self.file_index]):
            self.render()
            self._update_title()
            self._print_status()
            self.fig.canvas.draw_idle()

    def _show_help(self):
        """Show help information."""
        print("\n" + "=" * 50)
        print("DXF VIEWER - KEYBOARD SHORTCUTS")
        print("=" * 50)
        print("  S         Save screenshot")
        print("  G         Toggle grid")
        print("  I         Show file info")
        print("  R         Reset view")
        print("  A/LEFT    Previous file (browse mode)")
        print("  D/RIGHT   Next file (browse mode)")
        print("  H         Show this help")
        print("  Q/ESC     Quit viewer")
        print("-" * 50)
        print("MOUSE CONTROLS (use toolbar)")
        print("  Pan tool  Click and drag to pan")
        print("  Zoom tool Click and drag to zoom")
        print("  Home      Reset view to fit all")
        print("  Save      Save figure")
        print("=" * 50)

    def _print_status(self):
        """Print current file status to console."""
        if self.current_doc is None:
            return

        filename = Path(self.current_file).name
        stats = self.loader.get_entity_stats(self.current_doc)
        total = sum(stats.values())

        status = f"{filename} | {total} entities"
        if self.browse_mode:
            status += f" | File {self.file_index + 1}/{len(self.file_list)}"

        print(f"\r{status}", end="", flush=True)

    def run(self, file_path: str = None, browse_dir: str = None):
        """Run the interactive viewer.

        Args:
            file_path: Path to a single DXF file
            browse_dir: Directory to browse for DXF files
        """
        # Setup browse mode if directory specified
        if browse_dir:
            self.browse_mode = True
            self.file_list = self.loader.get_files_in_directory(browse_dir)
            if not self.file_list:
                print(f"No DXF files found in {browse_dir}")
                return
            print(f"Browse mode: Found {len(self.file_list)} DXF files")
            file_path = self.file_list[0]
        elif file_path:
            self.file_list = [file_path]
        else:
            print("Error: No file or directory specified")
            return

        # Load initial file
        if not self.load_file(file_path):
            print("Failed to load file")
            return

        # Setup figure
        self._setup_figure()

        # Print header
        print("\n" + "=" * 55)
        print(" " * 18 + "DXF VIEWER")
        print("=" * 55)
        print(f"  File: {Path(file_path).name}")

        stats = self.loader.get_entity_stats(self.current_doc)
        print(f"  Entities: {sum(stats.values())}")
        for entity_type, count in sorted(stats.items()):
            print(f"    {entity_type}: {count}")

        if self.browse_mode:
            print(f"  Browse mode: {len(self.file_list)} files")

        print("-" * 55)
        print("  Press H for help | Q to quit")
        print("=" * 55)

        # Render
        self.render()

        # Show
        plt.show()

        print("\nViewer closed.")


def main():
    parser = argparse.ArgumentParser(
        description="DXF Viewer - Interactive 2D CAD drawing viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View a specific DXF file
  python dxf_viewer.py output/square.dxf

  # Browse all DXF files in a directory
  python dxf_viewer.py --browse output/

  # View a sample file
  python dxf_viewer.py ../backend/text_to_dxf/samples/circle.dxf

Keyboard Controls:
  S       - Save screenshot
  A/LEFT  - Previous file (browse mode)
  D/RIGHT - Next file (browse mode)
  G       - Toggle grid
  I       - Show file info
  R       - Reset view
  H       - Show help
  Q/ESC   - Quit viewer

Mouse Controls (matplotlib toolbar):
  Pan     - Click and drag with pan tool
  Zoom    - Scroll wheel or zoom rectangle tool
  Home    - Reset view to fit all
        """
    )

    parser.add_argument(
        "file",
        nargs="?",
        help="Path to DXF file to view"
    )
    parser.add_argument(
        "--browse", "-b",
        metavar="DIR",
        help="Browse mode: view all DXF files in directory"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.file and not args.browse:
        parser.print_help()
        print("\nError: Please specify a file or use --browse for directory browsing")
        return

    # Create and run viewer
    viewer = DXFViewer()
    viewer.run(
        file_path=args.file,
        browse_dir=args.browse
    )


if __name__ == "__main__":
    main()
