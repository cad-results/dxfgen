#!/bin/bash
# Wrapper script for DXF Viewer with WSL2 support
# Configures display environment for matplotlib TkAgg backend

# Function to check if we're running in WSL
is_wsl() {
    [ -f /proc/version ] && grep -qi microsoft /proc/version
}

# Function to check if X server is running
check_x_server() {
    xset -q &>/dev/null
    return $?
}

# Function to test display connection
test_display() {
    local display=$1
    DISPLAY=$display timeout 1 xset -q &>/dev/null
    return $?
}

# Function to find working display
find_working_display() {
    # Common display values for WSL2
    local displays=(":0" ":0.0" "localhost:0" "localhost:0.0")

    # Try host IP for WSLg
    if command -v ip &>/dev/null; then
        local host_ip=$(ip route show | grep -i default | awk '{ print $3 }')
        if [ -n "$host_ip" ]; then
            displays+=("${host_ip}:0" "${host_ip}:0.0")
        fi
    fi

    # Try nameserver from resolv.conf (common for WSL2)
    if [ -f /etc/resolv.conf ]; then
        local nameserver=$(grep nameserver /etc/resolv.conf | awk '{print $2}' | head -1)
        if [ -n "$nameserver" ]; then
            displays+=("${nameserver}:0" "${nameserver}:0.0")
        fi
    fi

    for display in "${displays[@]}"; do
        if test_display "$display"; then
            echo "$display"
            return 0
        fi
    done

    return 1
}

echo "DXF Viewer - Initializing display environment..."

# Detect WSL
if is_wsl; then
    echo "Running in WSL2 environment"

    # Check for WSLg (built-in GUI support in Windows 11)
    if [ -d "/mnt/wslg" ]; then
        echo "WSLg detected - using native WSL GUI support"

        # Force X11 mode for matplotlib/Tk compatibility
        echo "Forcing X11 mode for matplotlib/Tk"
        export DISPLAY=:0

        # Disable Wayland
        unset WAYLAND_DISPLAY
        export WAYLAND_DISPLAY=

        # Force X11 for various toolkits
        export GDK_BACKEND=x11
        export QT_QPA_PLATFORM=xcb
        export SDL_VIDEODRIVER=x11

    else
        # Try to find a working X server
        if [ -z "$DISPLAY" ]; then
            echo "DISPLAY not set, searching for X server..."
            working_display=$(find_working_display)
            if [ -n "$working_display" ]; then
                export DISPLAY="$working_display"
                echo "Found working display: $DISPLAY"
            else
                echo ""
                echo "ERROR: No X server detected!"
                echo ""
                echo "To run GUI applications in WSL2, you need one of these options:"
                echo ""
                echo "Option 1: Windows 11 with WSLg (Recommended)"
                echo "  - Update to Windows 11 (build 22000 or later)"
                echo "  - Update WSL: wsl --update"
                echo "  - Restart WSL: wsl --shutdown"
                echo ""
                echo "Option 2: Install VcXsrv on Windows"
                echo "  1. Download VcXsrv from: https://sourceforge.net/projects/vcxsrv/"
                echo "  2. Install and run XLaunch"
                echo "  3. Select 'Multiple windows' and 'Start no client'"
                echo "  4. Check 'Disable access control'"
                echo "  5. In WSL2, run: export DISPLAY=\$(cat /etc/resolv.conf | grep nameserver | awk '{print \$2}'):0"
                echo ""
                exit 1
            fi
        else
            echo "Using DISPLAY=$DISPLAY"
            if ! check_x_server; then
                echo "WARNING: Cannot connect to display $DISPLAY"
            fi
        fi
    fi
else
    # Native Linux
    if [ -z "$DISPLAY" ]; then
        if [ -n "$WAYLAND_DISPLAY" ]; then
            echo "Wayland session detected"
            export DISPLAY=:0
        else
            echo "No display server detected"
            export DISPLAY=:0
        fi
    fi
fi

# Force matplotlib to use TkAgg backend
export MPLBACKEND=TkAgg

# Additional WSL2 settings
if is_wsl; then
    export LIBGL_ALWAYS_SOFTWARE=1
    export MESA_GL_VERSION_OVERRIDE=3.3
fi

# Verify Python dependencies
echo "Checking Python dependencies..."
if ! python3 -c "import ezdxf" 2>/dev/null; then
    echo "ERROR: ezdxf is not installed"
    echo "Install with: pip install ezdxf[draw]"
    exit 1
fi

if ! python3 -c "import matplotlib" 2>/dev/null; then
    echo "ERROR: matplotlib is not installed"
    echo "Install with: pip install matplotlib"
    exit 1
fi

# Test TkAgg backend
if ! python3 -c "import matplotlib; matplotlib.use('TkAgg')" 2>/dev/null; then
    echo "WARNING: TkAgg backend may not work"
    echo "Install tk with: sudo apt install python3-tk"
fi

# Print configuration
echo ""
echo "Display Configuration:"
echo "  DISPLAY=$DISPLAY"
echo "  MPLBACKEND=$MPLBACKEND"
echo ""

# Test X server connection
if command -v xset &>/dev/null; then
    if xset -q &>/dev/null; then
        echo "X server connection: OK"
    else
        echo "WARNING: Cannot connect to X server at $DISPLAY"
    fi
fi

echo ""
echo "Starting DXF Viewer..."
echo "----------------------------------------"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the DXF viewer with all arguments passed through
exec python3 "$SCRIPT_DIR/dxf_viewer.py" "$@"
