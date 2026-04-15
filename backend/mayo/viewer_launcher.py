"""Launcher for the Mayo/PartField viewer."""

import os
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Optional, Tuple


class ViewerLauncher:
    """Launches the 3D viewer for mesh visualization."""

    SUPPORTED_FORMATS = {'.glb', '.gltf', '.obj', '.ply', '.stl', '.off'}

    def __init__(self, viewer_script_path: Optional[str] = None,
                 run_script_path: Optional[str] = None):
        """Initialize the viewer launcher.

        Args:
            viewer_script_path: Path to viewer.py
            run_script_path: Path to run_viewer.sh wrapper script
        """
        if viewer_script_path is None:
            self.viewer_script = Path(__file__).parent / "viewer.py"
        else:
            self.viewer_script = Path(viewer_script_path)

        if run_script_path is None:
            self.run_script = Path(__file__).parent.parent / "scripts" / "run_viewer.sh"
        else:
            self.run_script = Path(run_script_path)

        self._display_error = None

    def launch(self, file_path: str, use_wrapper: bool = True,
               browse_mode: bool = False) -> subprocess.Popen:
        """Launch the viewer for a file.

        Args:
            file_path: Path to the mesh file to view
            use_wrapper: Use run_viewer.sh wrapper (handles WSL2/display setup)
            browse_mode: Enable browse mode for directory

        Returns:
            Popen process object
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if use_wrapper and self.run_script.exists():
            cmd = [str(self.run_script)]
            if browse_mode and file_path.is_dir():
                cmd.extend(['--browse', str(file_path)])
            else:
                cmd.append(str(file_path))
        else:
            cmd = [sys.executable, str(self.viewer_script)]
            if browse_mode and file_path.is_dir():
                cmd.extend(['--browse', str(file_path)])
            else:
                cmd.append(str(file_path))

        # Launch in background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True  # Detach from parent
        )

        return process

    def can_view(self, file_path: str) -> bool:
        """Check if a file can be viewed.

        Args:
            file_path: Path to check

        Returns:
            True if file format is supported
        """
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_FORMATS

    def is_available(self) -> bool:
        """Check if viewer dependencies are available."""
        try:
            import open3d
            import trimesh
            # Also check for display capability
            return self._check_display_capability()
        except ImportError:
            return False

    def _check_display_capability(self) -> bool:
        """Check if display/OpenGL is available for rendering."""
        try:
            # Set software rendering environment vars
            os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
            os.environ['MESA_GL_VERSION_OVERRIDE'] = '3.3'
            os.environ['MESA_GLSL_VERSION_OVERRIDE'] = '330'
            os.environ['GALLIUM_DRIVER'] = 'llvmpipe'

            import open3d as o3d
            vis = o3d.visualization.Visualizer()
            # Try creating a hidden test window
            result = vis.create_window(window_name='Test', visible=False, width=1, height=1)
            vis.destroy_window()

            if not result:
                self._display_error = "Cannot create OpenGL window. This may be a WSL2 or headless environment."
                return False

            return True
        except Exception as e:
            self._display_error = f"Display check failed: {str(e)}"
            return False

    def get_display_error(self) -> Optional[str]:
        """Get the last display error message, if any."""
        return self._display_error

    def get_supported_formats(self) -> list:
        """Get list of supported file extensions."""
        return list(self.SUPPORTED_FORMATS)

    def launch_fallback_viewer(self, file_path: str) -> Tuple[bool, str]:
        """Try to launch a fallback viewer using system tools.

        Args:
            file_path: Path to the 3D file

        Returns:
            Tuple of (success, error_message)
        """
        path = Path(file_path)
        if not path.exists():
            return False, f"File not found: {file_path}"

        ext = path.suffix.lower()

        # For GLTF/GLB files, try to use web-based viewers or other tools
        viewers_to_try = []

        if ext in {'.glb', '.gltf'}:
            # Web browsers can view GLTF files with model-viewer or three.js
            viewers_to_try = ['xdg-open', 'firefox', 'chromium', 'google-chrome']
        elif ext == '.stl':
            # STL viewers
            viewers_to_try = ['meshlab', 'f3d', 'xdg-open']
        elif ext == '.obj':
            viewers_to_try = ['meshlab', 'f3d', 'blender', 'xdg-open']
        elif ext == '.ply':
            viewers_to_try = ['meshlab', 'f3d', 'xdg-open']
        else:
            viewers_to_try = ['xdg-open', 'meshlab', 'f3d']

        for viewer in viewers_to_try:
            if shutil.which(viewer):
                try:
                    subprocess.Popen(
                        [viewer, str(path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return True, ""
                except Exception:
                    continue

        return False, "No suitable 3D viewer found. Install meshlab or f3d for 3D viewing."

    def get_viewer_status_details(self) -> dict:
        """Get detailed status about viewer availability."""
        status = {
            'open3d_installed': False,
            'trimesh_installed': False,
            'display_available': False,
            'fallback_viewers': [],
            'error': None
        }

        try:
            import open3d
            status['open3d_installed'] = True
        except ImportError:
            pass

        try:
            import trimesh
            status['trimesh_installed'] = True
        except ImportError:
            pass

        status['display_available'] = self._check_display_capability()
        if not status['display_available']:
            status['error'] = self._display_error

        # Check for fallback viewers
        fallback_viewers = ['meshlab', 'f3d', 'blender']
        for viewer in fallback_viewers:
            if shutil.which(viewer):
                status['fallback_viewers'].append(viewer)

        return status
