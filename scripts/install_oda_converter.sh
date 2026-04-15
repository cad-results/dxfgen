#!/bin/bash
# Install ODA File Converter for DWG support
#
# The ODA File Converter is a free tool from Open Design Alliance
# that enables conversion between DXF and DWG formats.
#
# Download page: https://www.opendesign.com/guestfiles/oda_file_converter
#
# This script provides instructions for installing ODA File Converter.
# Due to licensing, automated download is not supported.

set -e

echo "============================================"
echo "ODA File Converter Installation Guide"
echo "============================================"
echo ""
echo "The ODA File Converter enables DXF to DWG conversion."
echo ""
echo "INSTALLATION STEPS:"
echo ""
echo "1. Visit: https://www.opendesign.com/guestfiles/oda_file_converter"
echo ""
echo "2. Register for a free account (if you haven't already)"
echo ""
echo "3. Download the appropriate package for your system:"
echo "   - Linux (Debian/Ubuntu): ODAFileConverter_QT6_lnxX64_*.deb"
echo "   - Linux (RPM-based): ODAFileConverter_QT6_lnxX64_*.rpm"
echo "   - Windows: ODAFileConverter_*.exe"
echo "   - macOS: ODAFileConverter_*.dmg"
echo ""
echo "4. Install the package:"
echo ""
echo "   For Debian/Ubuntu:"
echo "   sudo dpkg -i ODAFileConverter_QT6_lnxX64_*.deb"
echo "   sudo apt-get install -f  # Install dependencies if needed"
echo ""
echo "   For RPM-based (Fedora/RHEL):"
echo "   sudo rpm -i ODAFileConverter_QT6_lnxX64_*.rpm"
echo ""
echo "   For Windows:"
echo "   Run the installer and follow the prompts"
echo ""
echo "5. Verify installation:"
echo "   ODAFileConverter --help"
echo ""
echo "============================================"
echo "Expected Installation Paths:"
echo "============================================"
echo ""
echo "Linux:   /usr/bin/ODAFileConverter"
echo "         /usr/local/bin/ODAFileConverter"
echo "         /opt/ODAFileConverter/ODAFileConverter"
echo ""
echo "Windows: C:\\Program Files\\ODA\\ODAFileConverter\\ODAFileConverter.exe"
echo ""
echo "============================================"
echo ""

# Check if ODA is already installed
echo "Checking for existing installation..."
echo ""

FOUND=0

for path in "/usr/bin/ODAFileConverter" "/usr/local/bin/ODAFileConverter" "/opt/ODAFileConverter/ODAFileConverter"; do
    if [ -x "$path" ]; then
        echo "FOUND: $path"
        FOUND=1
    fi
done

# Check PATH
if command -v ODAFileConverter &> /dev/null; then
    echo "FOUND in PATH: $(which ODAFileConverter)"
    FOUND=1
fi

if [ $FOUND -eq 0 ]; then
    echo "ODA File Converter is NOT currently installed."
    echo ""
    echo "Please follow the installation steps above to enable DWG support."
else
    echo ""
    echo "ODA File Converter is already installed!"
    echo "DWG conversion should be available in the application."
fi

echo ""
echo "============================================"
