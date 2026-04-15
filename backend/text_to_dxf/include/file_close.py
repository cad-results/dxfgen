#########################################################################
# This file contains code to close various opened files used in the     #
# script.                                                               #
#                                                                       #
# This program is free software; you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation; either version 2 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program; if not, write to the Free Software           #
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.             #
#########################################################################

from include.file_open import *

# Closes opened files
in_file.close()

# Validate that entities were created
entity_count = len(list(msp))
if entity_count == 0:
    print("Warning: No entities were created in the DXF file. The output may be empty.")

# Calculate drawing extents BEFORE saving
# Store extent values for post-processing
calculated_extents = None
try:
    from ezdxf.bbox import extents

    # Calculate bounding box of all entities in modelspace
    bbox = extents(msp)

    if bbox.has_data:
        # Store calculated extents for post-processing
        calculated_extents = {
            'extmin': bbox.extmin,
            'extmax': bbox.extmax
        }

        # Calculate viewport settings
        center_x = (bbox.extmin[0] + bbox.extmax[0]) / 2
        center_y = (bbox.extmin[1] + bbox.extmax[1]) / 2
        width = bbox.extmax[0] - bbox.extmin[0]
        height = bbox.extmax[1] - bbox.extmin[1]
        viewport_height = max(width, height) * 1.2

        # Ensure minimum viewport height
        if viewport_height < 1.0:
            viewport_height = 100.0

        # Set viewport to show entire drawing with padding
        dwg.set_modelspace_vport(height=viewport_height, center=(center_x, center_y))
    else:
        # Set default extents for empty drawings
        print("Warning: No geometry bounds found. Setting default extents.")
        dwg.set_modelspace_vport(height=100.0, center=(0, 0))

except Exception as e:
    print(f"Warning: Could not calculate extents: {e}")

# Saves the output file
dwg.saveas(output_file)

# Post-process the DXF file to fix extents (workaround for ezdxf limitation)
# ezdxf resets EXTMIN/EXTMAX during save, so we need to fix them afterwards
if calculated_extents is not None:
    try:
        # Read the saved file
        with open(output_file, 'r') as f:
            content = f.read()

        # Replace EXTMIN and EXTMAX values
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            # Fix $EXTMIN (exact match, not $PEXTMIN)
            if stripped == '$EXTMIN':
                # Skip to the coordinate values
                if i + 1 < len(lines) and lines[i + 1].strip() == '10':
                    lines[i + 2] = str(calculated_extents['extmin'][0])  # X
                if i + 3 < len(lines) and lines[i + 3].strip() == '20':
                    lines[i + 4] = str(calculated_extents['extmin'][1])  # Y
                if i + 5 < len(lines) and lines[i + 5].strip() == '30':
                    lines[i + 6] = str(calculated_extents['extmin'][2])  # Z

            # Fix $EXTMAX (exact match, not $PEXTMAX)
            elif stripped == '$EXTMAX':
                # Skip to the coordinate values
                if i + 1 < len(lines) and lines[i + 1].strip() == '10':
                    lines[i + 2] = str(calculated_extents['extmax'][0])  # X
                if i + 3 < len(lines) and lines[i + 3].strip() == '20':
                    lines[i + 4] = str(calculated_extents['extmax'][1])  # Y
                if i + 5 < len(lines) and lines[i + 5].strip() == '30':
                    lines[i + 6] = str(calculated_extents['extmax'][2])  # Z

            i += 1

        # Write the fixed content back
        with open(output_file, 'w') as f:
            f.write('\n'.join(lines))

    except Exception as e:
        print(f"Warning: Could not fix extents in saved file: {e}")