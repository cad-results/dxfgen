# Quick Start Guide

Get up and running with DXF Generator Chatbot in 5 minutes!

## Prerequisites

- Python 3.11+ with Conda installed
- OpenAI API key
- Git

## Setup (First Time)

### 1. Get Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (it starts with `sk-`)

### 2. Configure the Project

```bash
cd /home/adminho/dxfgen

# Copy environment template
cp .env.example .env

# Edit .env and paste your OpenAI API key
nano .env  # or use your preferred editor
```

Your `.env` file should look like:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
FLASK_PORT=5000
FLASK_DEBUG=True
```

### 3. Start the Server

```bash
./start.sh
```

The script will:
- Check/create the conda environment
- Verify text_to_dxf is cloned
- Start the Flask server

curl -X POST http://localhost:5000/api/chat -H "Content-Type: application/json" -d '{"message": "draw a 20 mm
   circle with a radial castle design surrounding it and draw a potato", "session_id": "test123"}'

### 4. Open the Interface

Open your browser and go to:
```
http://localhost:5000
```

## Using the Chatbot

### Example 1: Simple Shape

**Type in the chatbot:**
```
Draw a square 100mm on each side
```

The system will:
1. Parse your intent
2. Extract geometric entities
3. Format to CSV
4. Validate the result
5. Show a "Generate DXF File" button

Click the button to generate and download your DXF file!

### Example 2: Multiple Shapes

**Type:**
```
Create a rectangle 150mm x 80mm with a circle of radius 30mm in the center
```

The system will:
- Identify the rectangle (4 lines)
- Identify the circle with calculated center position
- Generate both shapes in one DXF file

### Example 3: Complex Drawing

**Type:**
```
Draw a mechanical flange:
- Outer circle 120mm diameter
- Inner circle 40mm diameter
- Four 8mm mounting holes, 80mm from center, equally spaced
```

The system will:
- Calculate all circle positions
- Validate geometry
- Generate a complete flange drawing

## Testing Without the Web Interface

### Option 1: Command-Line Test

```bash
conda activate dxfgen
python test_workflow.py
```

Follow the interactive menu to test different examples.

### Option 2: API Client

```bash
# In one terminal, start the server:
./start.sh

# In another terminal:
conda activate dxfgen
python api_example.py
```

## Common Issues

### "OPENAI_API_KEY not set"
- Make sure you created `.env` file
- Check that your API key is correct
- Verify the file is in the project root directory

### "conda: command not found"
Install Miniconda:
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

### "Port 5000 already in use"
Change the port in `.env`:
```
FLASK_PORT=5001
```

### "text_to_dxf not found"
The start.sh script should clone it automatically, but you can do it manually:
```bash
git clone https://github.com/GreatDevelopers/text_to_dxf.git backend/text_to_dxf
```

## Where Are My DXF Files?

Generated DXF files are saved in:
```
/home/adminho/dxfgen/output/
```

## Example Drawing Ideas

Try these descriptions in the chatbot:

### Beginner
- "Draw a circle radius 50mm"
- "Create a rectangle 100mm x 60mm"
- "Draw a square 75mm on each side"

### Intermediate
- "Three concentric circles with radii 20, 40, 60mm"
- "Rectangle 120mm x 80mm with 10mm radius circles at each corner"
- "Equilateral triangle with 80mm sides"

### Advanced
- "Floor plan of a 5m x 4m room with a 900mm door opening"
- "Gear with 8 teeth around a 60mm circle"
- "Bolt circle pattern: 100mm diameter with 6 equally spaced 10mm holes"

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [examples/example_inputs.txt](examples/example_inputs.txt) for more ideas
- Explore the API with [api_example.py](api_example.py)
- Modify agents in `backend/agents/` to customize behavior

## Support

For issues:
1. Check the [Troubleshooting](README.md#troubleshooting) section in README
2. Review the console output for error messages
3. Verify your OpenAI API key is valid and has credits
4. Check that all dependencies are installed

## Architecture Overview

```
You describe drawing → LLM Agents process → CSV metadata → text_to_dxf → DXF file
```

**The four agents:**
1. **Intent Parser**: Understands what you want
2. **Entity Extractor**: Identifies shapes and coordinates
3. **Metadata Formatter**: Converts to CSV format
4. **Validator**: Checks quality and accuracy

## Credits

- Built with LangGraph and OpenAI
- Uses [text_to_dxf](https://github.com/GreatDevelopers/text_to_dxf) for DXF generation
- Flask web framework

---

**Happy Drawing! 🎨📐**

For detailed documentation, see [README.md](README.md)
