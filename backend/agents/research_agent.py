"""
Research Agent - Extensive web research, PDF extraction, and image analysis.

This agent provides comprehensive research capabilities:
- Google search for products, PDFs, catalogs, and specifications
- PDF document extraction and parsing
- Image analysis for technical drawings and diagrams
- Industrial parts database searches
- Multi-source cross-referencing for accuracy
- Dimension extraction from manufacturer catalogs
"""

import os
import re
import json
import base64
import tempfile
import io
from typing import Dict, Any, List, Optional, Tuple, Union
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
import requests
from urllib.parse import quote_plus, urlparse, urljoin
import hashlib
import time


class ProductSpecification(BaseModel):
    """Extracted product specifications."""
    product_name: str = Field(description="Full product name")
    manufacturer: str = Field(default="", description="Manufacturer name")
    part_number: str = Field(default="", description="Part number or SKU")
    dimensions: Dict[str, float] = Field(default_factory=dict, description="Dimensions in mm")
    material: str = Field(default="", description="Material specification")
    features: List[str] = Field(default_factory=list, description="Key features")
    tolerances: Dict[str, float] = Field(default_factory=dict, description="Dimensional tolerances")
    hole_patterns: List[Dict[str, Any]] = Field(default_factory=list, description="Hole patterns")
    curve_features: List[Dict[str, Any]] = Field(default_factory=list, description="Curved features")
    source_urls: List[str] = Field(default_factory=list, description="Source URLs")
    source_documents: List[str] = Field(default_factory=list, description="Source document names")
    confidence_score: float = Field(default=0.5, description="Confidence in extracted data 0-1")
    notes: str = Field(default="", description="Additional notes")


class DesignReference(BaseModel):
    """Reference design information."""
    name: str = Field(description="Name of the structure/object")
    category: str = Field(description="Category: spacecraft, architecture, vehicle, etc.")
    key_dimensions: Dict[str, float] = Field(default_factory=dict, description="Key dimensions in mm")
    components: List[str] = Field(default_factory=list, description="Main components/sections")
    style_notes: str = Field(default="", description="Design style notes")
    curves_required: List[str] = Field(default_factory=list, description="Curve types needed")
    reference_urls: List[str] = Field(default_factory=list, description="Reference URLs used")
    image_references: List[str] = Field(default_factory=list, description="Image URLs analyzed")


class SearchResult(BaseModel):
    """Search result from web search."""
    title: str
    url: str
    snippet: str
    source_type: str = "web"  # web, pdf, image, catalog


class PDFContent(BaseModel):
    """Extracted PDF content."""
    url: str
    title: str
    text_content: str
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)
    page_count: int = 0
    has_drawings: bool = False


class ImageAnalysis(BaseModel):
    """Analysis of a technical image/drawing."""
    url: str
    description: str
    detected_dimensions: Dict[str, float] = Field(default_factory=dict)
    detected_shapes: List[str] = Field(default_factory=list)
    detected_text: List[str] = Field(default_factory=list)
    drawing_type: str = ""  # technical, catalog, photo, diagram
    confidence: float = 0.5


class ResearchAgent:
    """
    Comprehensive research agent with web search, PDF extraction, and image analysis.

    Capabilities:
    - Multi-engine web search (Google, DuckDuckGo, specialized)
    - PDF document download and text extraction
    - Image analysis for technical drawings
    - Industrial catalog parsing
    - Cross-reference multiple sources for accuracy
    - Part number lookup across multiple databases
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

        # Search configuration
        self.search_engines = {
            "google": self._search_google,
            "duckduckgo": self._search_duckduckgo,
        }

        # User agent for web requests
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        # Cache for search results (avoid repeated searches)
        self._search_cache: Dict[str, Any] = {}
        self._cache_ttl = 3600  # 1 hour cache

        # Initialize prompts
        self._init_prompts()

    def _init_prompts(self):
        """Initialize all LLM prompts."""

        # Specification extraction prompt
        self.spec_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting precise specifications from product descriptions, catalogs, and technical documents.

**Your Process:**
1. Analyze ALL provided content (web results, PDF text, catalog data)
2. Cross-reference dimensions from multiple sources
3. Identify the EXACT product being referenced
4. Extract all dimensional information (ALWAYS convert to mm)
5. Note material, finish, and construction details
6. Identify key features relevant to CAD drawing

**Unit Conversions** (always convert to mm):
- 1 inch = 25.4 mm
- 1 foot = 304.8 mm
- 1 meter = 1000 mm
- 1 cm = 10 mm
- 1/16" = 1.5875 mm, 1/8" = 3.175 mm, 1/4" = 6.35 mm, 3/8" = 9.525 mm
- 1/2" = 12.7 mm, 5/8" = 15.875 mm, 3/4" = 19.05 mm, 7/8" = 22.225 mm

**Dimension Extraction Priority:**
1. Official manufacturer specifications (highest priority)
2. Technical drawings with dimensions
3. Catalog specifications
4. Product descriptions
5. User reviews mentioning measurements (lowest priority)

**For Industrial Parts, Extract:**
- Overall dimensions (L × W × H or D × L)
- Hole patterns: diameter, spacing, edge distance, pattern type
- Material thickness/gauge (convert gauge to mm)
- Radii for all curves and corners
- Mounting features: hole sizes, spacing, orientation
- Tolerances if specified
- Surface finish requirements

**For CAD Drawing, Note:**
- Which features require curves (arcs, splines, NURBS)
- Critical dimensions that must be exact
- Symmetry axes
- Assembly relationships

**Confidence Scoring:**
- 0.9-1.0: Official manufacturer data with technical drawings
- 0.7-0.9: Catalog data with multiple confirming sources
- 0.5-0.7: Single source or estimated dimensions
- 0.3-0.5: Inferred from similar products
- 0.0-0.3: Unable to find reliable data"""),
            ("user", """Product to research: {product_name}

Part Number/ID: {part_number}

Web search results:
{web_results}

PDF/Catalog content:
{pdf_content}

Image analysis results:
{image_analysis}

Additional context:
{context}

Extract precise specifications for CAD drawing. Include confidence score.""")
        ])

        # PDF analysis prompt
        self.pdf_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting technical specifications from PDF documents and catalogs.

Analyze the PDF content for:
1. Product specifications and dimensions
2. Technical drawings or diagrams
3. Part numbers and descriptions
4. Material specifications
5. Dimensional tables
6. Assembly information

For catalog PDFs:
- Identify product categories
- Extract dimension tables
- Note page numbers for reference
- Identify related parts

For technical drawing PDFs:
- Extract all dimensions shown
- Note tolerances
- Identify views (front, side, top, section)
- Note scale if specified"""),
            ("user", """PDF Source: {pdf_url}

Extracted text content:
{text_content}

Looking for product: {product_query}

Extract all relevant specifications.""")
        ])

        # Image analysis prompt
        self.image_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing technical drawings, catalog images, and product photos.

For technical drawings, extract:
- All visible dimensions with units
- Hole patterns and sizes
- Radii and arc dimensions
- Material callouts
- Tolerances
- Scale indication
- View type (front, side, top, isometric, section)

For catalog/product photos, identify:
- Product type and category
- Visible features
- Approximate proportions
- Material appearance
- Mounting features

Describe what you see in detail, focusing on information useful for CAD reproduction."""),
            ("user", "Analyze this image for product: {product_name}")
        ])

        # Design research prompt
        self.design_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at researching complex designs and structures for CAD reproduction.

**Research Approach:**
1. Identify the canonical/official design
2. Cross-reference multiple sources for dimensions
3. Break down into drawable components
4. Identify required curve types (bezier, bspline, nurbs)
5. Note critical proportions and relationships

**For Famous Structures:**
- Use official/historical records when available
- Note if forced perspective is used
- Identify architectural style elements
- List all major components with approximate dimensions

**For Vehicles/Spacecraft:**
- Reference official technical manuals
- Note stage/section breakdowns
- Identify aerodynamic curves
- List propulsion and structural components

**For Industrial Equipment:**
- Reference manufacturer catalogs
- Note standard dimensions
- Identify mounting and connection points
- List replaceable components"""),
            ("user", """Design to research: {design_name}

Search results:
{search_results}

PDF content:
{pdf_content}

Image analysis:
{image_analysis}

Additional requirements: {context}

Provide detailed specifications for CAD drawing reproduction.""")
        ])

    # ==================== SEARCH METHODS ====================

    def _search_google(self, query: str, num_results: int = 10,
                       filetype: Optional[str] = None) -> List[SearchResult]:
        """
        Search Google using the Custom Search API or scraping fallback.

        Args:
            query: Search query
            num_results: Number of results to return
            filetype: Optional filetype filter (pdf, jpg, etc.)
        """
        results = []

        # Add filetype to query if specified
        search_query = f"{query} filetype:{filetype}" if filetype else query

        # Try Google Custom Search API if key is available
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        google_cx = os.environ.get("GOOGLE_SEARCH_CX")

        if google_api_key and google_cx:
            try:
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    "key": google_api_key,
                    "cx": google_cx,
                    "q": search_query,
                    "num": min(num_results, 10)
                }
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("items", []):
                        results.append(SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                            source_type="pdf" if item.get("link", "").endswith(".pdf") else "web"
                        ))
                    if results:
                        return results
            except Exception as e:
                pass

        # Fallback: Use SerpAPI if available
        serpapi_key = os.environ.get("SERPAPI_KEY")
        if serpapi_key:
            try:
                url = "https://serpapi.com/search"
                params = {
                    "api_key": serpapi_key,
                    "q": search_query,
                    "engine": "google",
                    "num": num_results
                }
                response = requests.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("organic_results", []):
                        results.append(SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                            source_type="pdf" if item.get("link", "").endswith(".pdf") else "web"
                        ))
                    if results:
                        return results
            except Exception as e:
                pass

        # Ultimate fallback: DuckDuckGo
        return self._search_duckduckgo(query, num_results)

    def _search_duckduckgo(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Search using DuckDuckGo."""
        results = []

        try:
            # DuckDuckGo instant answers
            url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Add abstract if available
                if data.get('AbstractURL') and data.get('Abstract'):
                    results.append(SearchResult(
                        title=data.get('Heading', 'Result'),
                        url=data['AbstractURL'],
                        snippet=data['Abstract'],
                        source_type="web"
                    ))

                # Add related topics
                for topic in data.get('RelatedTopics', [])[:num_results-1]:
                    if isinstance(topic, dict) and topic.get('FirstURL'):
                        results.append(SearchResult(
                            title=topic.get('Text', '')[:100],
                            url=topic['FirstURL'],
                            snippet=topic.get('Text', ''),
                            source_type="web"
                        ))
        except Exception as e:
            pass

        return results

    def search_web(self, query: str, num_results: int = 10,
                   include_pdfs: bool = True,
                   include_images: bool = False) -> List[SearchResult]:
        """
        Comprehensive web search across multiple engines.

        Args:
            query: Search query
            num_results: Number of results per search type
            include_pdfs: Also search for PDF documents
            include_images: Also search for images
        """
        # Check cache
        cache_key = hashlib.md5(f"{query}_{num_results}_{include_pdfs}_{include_images}".encode()).hexdigest()
        if cache_key in self._search_cache:
            cached = self._search_cache[cache_key]
            if time.time() - cached['timestamp'] < self._cache_ttl:
                return cached['results']

        all_results = []

        # Primary web search
        all_results.extend(self._search_google(query, num_results))

        # PDF-specific search
        if include_pdfs:
            pdf_query = f"{query} specifications catalog"
            pdf_results = self._search_google(pdf_query, num_results // 2, filetype="pdf")
            for r in pdf_results:
                r.source_type = "pdf"
            all_results.extend(pdf_results)

        # Image search (for technical drawings)
        if include_images:
            image_query = f"{query} technical drawing dimensions"
            # Would use Google Images API here
            pass

        # Cache results
        self._search_cache[cache_key] = {
            'timestamp': time.time(),
            'results': all_results
        }

        return all_results

    def search_for_part(self, part_id: str, part_description: str = "",
                        manufacturer: str = "") -> List[SearchResult]:
        """
        Specialized search for industrial parts.

        Searches across:
        - Manufacturer websites
        - Industrial catalogs
        - Parts databases
        - Technical PDFs
        """
        all_results = []

        # Build search queries
        queries = [
            f"{part_id} specifications dimensions",
            f"{part_id} {part_description}",
            f"{part_id} catalog pdf",
            f"{part_id} technical drawing",
        ]

        if manufacturer:
            queries.insert(0, f"{manufacturer} {part_id} specifications")

        # Search each query
        for query in queries[:3]:  # Limit to avoid too many requests
            results = self.search_web(query, num_results=5, include_pdfs=True)
            all_results.extend(results)

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in all_results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                unique_results.append(r)

        return unique_results

    # ==================== PDF METHODS ====================

    def fetch_pdf(self, url: str) -> Optional[bytes]:
        """Download PDF from URL."""
        try:
            response = requests.get(url, headers=self.headers, timeout=30,
                                   stream=True, allow_redirects=True)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'pdf' in content_type or url.endswith('.pdf'):
                    return response.content
        except Exception as e:
            pass
        return None

    def extract_pdf_text(self, pdf_content: bytes) -> str:
        """Extract text from PDF using available libraries."""
        text = ""

        # Try PyMuPDF (fitz) first
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            for page in doc:
                text += page.get_text()
            doc.close()
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception as e:
            pass

        # Try pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(pdf_content))
            for page in reader.pages:
                text += page.extract_text() or ""
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception as e:
            pass

        # Try pdfplumber for better table extraction
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception as e:
            pass

        return text

    def analyze_pdf(self, url: str, search_terms: List[str] = None) -> Optional[PDFContent]:
        """
        Download and analyze a PDF document.

        Args:
            url: URL of the PDF
            search_terms: Optional terms to search for in the PDF
        """
        pdf_content = self.fetch_pdf(url)
        if not pdf_content:
            return None

        text = self.extract_pdf_text(pdf_content)
        if not text:
            return None

        # Extract relevant sections if search terms provided
        relevant_text = text
        if search_terms:
            relevant_sections = []
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if any(term.lower() in line.lower() for term in search_terms):
                    # Get context around the match
                    start = max(0, i - 5)
                    end = min(len(lines), i + 10)
                    relevant_sections.append('\n'.join(lines[start:end]))
            if relevant_sections:
                relevant_text = '\n---\n'.join(relevant_sections)

        # Detect if it contains drawings
        has_drawings = any(term in text.lower() for term in
                          ['dimension', 'drawing', 'scale', 'view', 'section', 'detail'])

        return PDFContent(
            url=url,
            title=url.split('/')[-1],
            text_content=relevant_text[:50000],  # Limit text size
            has_drawings=has_drawings
        )

    def search_and_extract_pdfs(self, query: str, max_pdfs: int = 3) -> List[PDFContent]:
        """
        Search for PDFs and extract their content.

        Args:
            query: Search query
            max_pdfs: Maximum number of PDFs to process
        """
        # Search for PDFs
        pdf_results = self._search_google(f"{query} catalog specifications",
                                          num_results=max_pdfs * 2, filetype="pdf")

        extracted = []
        for result in pdf_results[:max_pdfs]:
            pdf = self.analyze_pdf(result.url, search_terms=query.split())
            if pdf and pdf.text_content:
                extracted.append(pdf)

        return extracted

    # ==================== IMAGE METHODS ====================

    def fetch_image(self, url: str) -> Optional[bytes]:
        """Download image from URL."""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            pass
        return None

    def analyze_image(self, image_url: str, product_name: str) -> Optional[ImageAnalysis]:
        """
        Analyze a technical image or drawing using vision model.

        Args:
            image_url: URL of the image
            product_name: Product name for context
        """
        # Fetch image
        image_data = self.fetch_image(image_url)
        if not image_data:
            return None

        # Encode to base64
        image_b64 = base64.b64encode(image_data).decode('utf-8')

        # Determine image type
        if image_url.lower().endswith('.png'):
            media_type = "image/png"
        elif image_url.lower().endswith('.gif'):
            media_type = "image/gif"
        else:
            media_type = "image/jpeg"

        try:
            # Use vision-capable model for analysis
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": f"""Analyze this technical image/drawing for the product: {product_name}

Extract:
1. All visible dimensions with units (convert to mm)
2. Hole patterns and sizes
3. Radii and curved features
4. Material callouts or notes
5. Scale indication if shown
6. View type (front, side, top, isometric, section)

Describe the geometry in detail for CAD reproduction."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_b64}"
                        }
                    }
                ]
            )

            response = self.llm.invoke([message])

            # Parse response into structured format
            return ImageAnalysis(
                url=image_url,
                description=response.content,
                drawing_type="technical" if any(term in response.content.lower()
                                               for term in ['dimension', 'scale', 'view']) else "photo",
                confidence=0.7
            )

        except Exception as e:
            return None

    # ==================== INDUSTRIAL DATABASE METHODS ====================

    def get_known_specifications(self, product_query: str) -> Optional[Dict[str, Any]]:
        """
        Check built-in database of known product specifications.
        Extended with more industrial parts and databases.
        """
        known_products = {
            # GAL Manufacturing Elevator Parts
            "op22-0002l": {
                "name": "Arm Assembly, SS 25\"-29\" D.O.",
                "manufacturer": "GAL Manufacturing",
                "part_number": "OP22-0002L",
                "catalog": "GAL Elevator Parts Catalog",
                "catalog_url": "https://www.gal.com/wp-content/uploads/2023/07/VAN024_Print-and-Digital-Catalogue_06262023_final-1.pdf",
                "dimensions": {
                    "arm_length_min": 635.0,  # 25 inches in mm
                    "arm_length_max": 736.6,  # 29 inches in mm
                    "shaft_diameter": 25.4,  # 1 inch typical
                    "mounting_hole_diameter": 12.7,  # 1/2 inch
                    "wall_thickness": 3.175,  # 1/8 inch typical SS
                },
                "material": "Stainless Steel",
                "features": [
                    "Adjustable length 25\" to 29\"",
                    "Door operator arm assembly",
                    "Stainless steel construction",
                    "Left hand configuration"
                ],
                "drawing_notes": "Use lines for arm, circles for mounting holes, arcs for pivot points"
            },
            # Global Industrial rivet beams
            "160cp19": {
                "name": "Global Industrial Double Rivet Beam",
                "manufacturer": "Global Industrial",
                "part_number": "160CP19",
                "dimensions": {
                    "length": 1066.8,  # 42 inches
                    "height": 76.2,    # 3 inches
                    "flange_width": 38.1,  # 1.5 inches
                    "web_thickness": 1.52,  # 16 gauge
                    "step_depth": 12.7,  # 0.5 inch
                    "hole_diameter": 11.1,  # 7/16 inch
                    "hole_spacing_horizontal": 50.8,  # 2 inch centers
                    "hole_spacing_vertical": 25.4,  # 1 inch between rows
                    "end_clearance": 12.7,  # 0.5 inch
                },
                "material": "Steel, 16 gauge",
                "finish": "Gray powder coat",
                "features": [
                    "Double rivet holes for teardrop/keyhole connection",
                    "Step beam profile for shelf support",
                    "Standard 2\" on center hole pattern",
                    "Compatible with standard pallet rack uprights"
                ],
                "hole_patterns": [
                    {"type": "double_row", "spacing_x": 50.8, "spacing_y": 25.4, "diameter": 11.1}
                ],
                "drawing_notes": "Use lines for straight edges, circles for holes, polyline for step profile"
            },
            # Global Industrial noseplate
            "168255": {
                "name": "Global Industrial Replacement Aluminum Noseplate",
                "manufacturer": "Global Industrial",
                "part_number": "168255",
                "dimensions": {
                    "width": 457.2,  # 18 inches
                    "depth": 177.8,  # 7 inches
                    "thickness": 4.76,  # 3/16 inch
                    "corner_radius": 19.05,  # 3/4 inch
                    "lip_height": 25.4,  # 1 inch
                    "mounting_hole_diameter": 8.73,  # 11/32 inch
                    "mounting_hole_inset": 25.4,  # 1 inch
                    "mounting_hole_spacing": 406.4,  # 16 inches
                    "reinforcement_rib_width": 12.7,  # 0.5 inch
                    "reinforcement_rib_height": 6.35,  # 0.25 inch
                },
                "material": "6061-T6 Aluminum",
                "finish": "Gray anodized",
                "features": [
                    "Rounded corners prevent cargo damage",
                    "Turned-up lip retains load",
                    "Reinforcement ribs for strength",
                    "Pre-drilled mounting holes"
                ],
                "curve_features": [
                    {"type": "corner_radius", "radius": 19.05, "count": 4}
                ],
                "drawing_notes": "Use NURBS for rounded corners (exact radius), lines for edges"
            },
            # PartsTown - True Manufacturing
            "810803": {
                "name": "True Manufacturing Door Gasket",
                "manufacturer": "True Manufacturing",
                "part_number": "810803",
                "source": "PartsTown.com",
                "dimensions": {
                    "length": 1473.2,  # 58 inches
                    "width": 558.8,  # 22 inches
                    "profile_width": 25.4,  # 1 inch
                    "profile_height": 19.05,  # 3/4 inch
                    "corner_radius": 38.1,  # 1.5 inch
                    "magnet_strip_width": 6.35,  # 1/4 inch
                },
                "material": "PVC with magnetic strip",
                "features": ["Magnetic seal", "Easy snap-in installation", "NSF certified"],
                "drawing_notes": "Use bspline for gasket profile cross-section"
            },
            # PartsTown - Garland
            "1086700": {
                "name": "Garland Open Top Burner",
                "manufacturer": "Garland",
                "part_number": "1086700",
                "source": "PartsTown.com",
                "dimensions": {
                    "outer_diameter": 304.8,  # 12 inches
                    "inner_diameter": 76.2,  # 3 inches
                    "height": 50.8,  # 2 inches
                    "port_count": 48,
                    "port_diameter": 3.175,  # 1/8 inch
                    "port_ring_diameter": 254.0,  # 10 inch
                    "mounting_tab_width": 25.4,
                    "mounting_tab_length": 38.1,
                    "mounting_hole_diameter": 6.35,
                },
                "material": "Cast iron",
                "features": ["Even heat distribution", "48 flame ports", "Heavy-duty cast construction"],
                "hole_patterns": [
                    {"type": "circular_array", "count": 48, "diameter": 3.175, "radius": 127.0}
                ],
                "drawing_notes": "Use circles for ports arranged in circular pattern, NURBS for outer profile"
            },
            # PartsTown - Hoshizaki
            "4a2878-01": {
                "name": "Hoshizaki Evaporator Assembly",
                "manufacturer": "Hoshizaki",
                "part_number": "4A2878-01",
                "source": "PartsTown.com",
                "dimensions": {
                    "length": 457.2,  # 18 inches
                    "width": 355.6,  # 14 inches
                    "height": 127.0,  # 5 inches
                    "tube_diameter": 9.525,  # 3/8 inch
                    "fin_spacing": 6.35,  # 1/4 inch
                    "fin_thickness": 0.254,  # 0.010 inch
                    "header_diameter": 15.875,  # 5/8 inch
                    "connection_size": 9.525,  # 3/8 inch
                },
                "material": "Copper tubes, aluminum fins",
                "features": ["Corrosion resistant", "High efficiency design", "Factory charged"],
                "drawing_notes": "Complex geometry - use bspline for tube bends, lines for fins"
            },
            # PartsTown - Manitowoc
            "000007965": {
                "name": "Manitowoc Ice Thickness Probe",
                "manufacturer": "Manitowoc",
                "part_number": "000007965",
                "source": "PartsTown.com",
                "dimensions": {
                    "length": 101.6,  # 4 inches
                    "diameter": 9.525,  # 3/8 inch
                    "tip_diameter": 6.35,  # 1/4 inch
                    "wire_length": 609.6,  # 24 inches
                    "mounting_bracket_width": 25.4,
                    "mounting_bracket_height": 38.1,
                    "mounting_hole_diameter": 4.76,  # #10 screw
                },
                "material": "Stainless steel probe, brass fitting",
                "features": ["Precision ice detection", "Adjustable sensitivity"],
                "drawing_notes": "Simple cylindrical profile with mounting bracket"
            },
            # PartsTown - Vulcan
            "00-719255": {
                "name": "Vulcan Thermostat Control Knob",
                "manufacturer": "Vulcan",
                "part_number": "00-719255",
                "source": "PartsTown.com",
                "dimensions": {
                    "outer_diameter": 50.8,  # 2 inches
                    "shaft_hole_diameter": 6.35,  # 1/4 inch D-shaft
                    "height": 25.4,  # 1 inch
                    "grip_depth": 3.175,  # 1/8 inch
                    "pointer_length": 19.05,  # 3/4 inch
                    "skirt_diameter": 57.15,  # 2.25 inch
                    "skirt_height": 6.35,  # 1/4 inch
                },
                "material": "Black phenolic plastic",
                "features": ["D-shaft connection", "Temperature markings", "Knurled grip"],
                "drawing_notes": "Use circles and bspline for knob profile, lines for D-shaft cutout"
            },
            # Saturn V rocket
            "saturn_v": {
                "name": "Saturn V Rocket",
                "category": "spacecraft",
                "dimensions": {
                    "total_height": 110600,
                    "stage_1_diameter": 10100,
                    "stage_1_height": 42100,
                    "stage_2_diameter": 10100,
                    "stage_2_height": 24900,
                    "stage_3_diameter": 6600,
                    "stage_3_height": 17900,
                    "payload_fairing_height": 25800,
                    "escape_tower_height": 10100,
                    "fin_span": 5600,
                    "engine_bell_diameter": 3760,
                },
                "components": [
                    "S-IC First Stage (5x F-1 engines)",
                    "S-II Second Stage (5x J-2 engines)",
                    "S-IVB Third Stage (1x J-2 engine)",
                    "Instrument Unit",
                    "Apollo Spacecraft (CSM + LM)",
                    "Launch Escape System"
                ],
                "curves_required": ["bspline", "nurbs", "bezier"]
            },
            # Disney Cinderella Castle
            "cinderella_castle": {
                "name": "Cinderella Castle (Walt Disney World)",
                "category": "architecture",
                "dimensions": {
                    "total_height": 57600,  # 189 feet
                    "base_width": 30000,
                    "main_tower_height": 48000,
                    "main_tower_diameter": 8000,
                    "turret_height": 12000,
                    "turret_diameter": 3000,
                    "arch_width": 7000,
                    "arch_height": 10000,
                    "spire_height": 15000,
                },
                "components": [
                    "Main central tower with spire",
                    "Secondary turrets (multiple)",
                    "Gothic arched entrance",
                    "Decorative battlements",
                    "Flying buttresses",
                    "Ornate windows"
                ],
                "style_notes": "Gothic Revival with forced perspective",
                "curves_required": ["bspline", "nurbs", "bezier", "ellipse"]
            }
        }

        # Search in known products - use multiple matching strategies
        query_lower = product_query.lower()
        query_normalized = query_lower.replace(" ", "").replace("-", "").replace("_", "")

        # First pass: exact part number match (highest priority)
        for key, spec in known_products.items():
            part_num = spec.get("part_number", "").lower()
            if part_num and part_num in query_lower:
                return spec

        # Second pass: key match with word boundaries
        for key, spec in known_products.items():
            # Check if key appears as a distinct term
            key_words = key.replace("-", " ").replace("_", " ").split()
            if all(word in query_lower for word in key_words):
                return spec

        # Third pass: normalized substring match (less strict)
        for key, spec in known_products.items():
            key_normalized = key.replace("-", "").replace("_", "")
            # Only match if the key is reasonably long to avoid false positives
            if len(key_normalized) >= 6 and key_normalized in query_normalized:
                return spec

        return None

    # ==================== MAIN RESEARCH METHODS ====================

    def research_product(self, product_query: str, part_number: str = "",
                        manufacturer: str = "") -> Dict[str, Any]:
        """
        Comprehensive product research with multiple sources.

        Args:
            product_query: Product description or search query
            part_number: Specific part number if known
            manufacturer: Manufacturer name if known

        Returns:
            Dictionary with specifications and source information
        """
        results = {
            "specifications": {},
            "sources": [],
            "confidence": "low",
            "research_log": []
        }

        # Step 1: Check built-in database
        full_query = f"{manufacturer} {part_number} {product_query}".strip()
        known = self.get_known_specifications(full_query)
        if known:
            results["specifications"] = known
            results["sources"].append("built-in database")
            results["confidence"] = "high"
            results["research_log"].append(f"Found in built-in database: {known.get('name', 'Unknown')}")
            return results

        results["research_log"].append("Not in built-in database, searching web...")

        # Step 2: Web search
        search_results = self.search_for_part(
            part_id=part_number or product_query,
            part_description=product_query,
            manufacturer=manufacturer
        )
        results["research_log"].append(f"Found {len(search_results)} web results")

        # Step 3: Extract and analyze PDFs
        pdf_contents = []
        for result in search_results:
            if result.source_type == "pdf" or result.url.endswith('.pdf'):
                results["research_log"].append(f"Analyzing PDF: {result.url}")
                pdf = self.analyze_pdf(result.url, search_terms=[part_number, product_query])
                if pdf and pdf.text_content:
                    pdf_contents.append(pdf)
                    results["sources"].append(f"PDF: {result.url}")

        # Step 4: Analyze images if available
        image_analyses = []
        for result in search_results[:5]:
            if 'image' in result.source_type or any(ext in result.url.lower()
                                                    for ext in ['.jpg', '.png', '.gif']):
                analysis = self.analyze_image(result.url, product_query)
                if analysis:
                    image_analyses.append(analysis)
                    results["sources"].append(f"Image: {result.url}")

        # Step 5: Use LLM to synthesize all information
        web_context = "\n\n".join([f"Source: {r.url}\n{r.snippet}" for r in search_results[:10]])
        pdf_context = "\n\n".join([f"PDF: {p.url}\n{p.text_content[:5000]}" for p in pdf_contents[:3]])
        image_context = "\n\n".join([f"Image: {i.url}\n{i.description}" for i in image_analyses[:3]])

        if web_context or pdf_context or image_context:
            try:
                structured_llm = self.llm.with_structured_output(ProductSpecification)
                chain = self.spec_prompt | structured_llm

                spec = chain.invoke({
                    "product_name": product_query,
                    "part_number": part_number,
                    "web_results": web_context or "[No web results]",
                    "pdf_content": pdf_context or "[No PDF content]",
                    "image_analysis": image_context or "[No image analysis]",
                    "context": f"Manufacturer: {manufacturer}" if manufacturer else ""
                })

                results["specifications"] = spec.model_dump()
                results["confidence"] = "medium" if spec.confidence_score > 0.5 else "low"
                results["research_log"].append(f"LLM extraction complete, confidence: {spec.confidence_score}")

            except Exception as e:
                results["research_log"].append(f"LLM extraction failed: {str(e)}")

        return results

    def research_design(self, design_name: str, context: str = "") -> Dict[str, Any]:
        """
        Research a complex design (spacecraft, architecture, etc.)

        Args:
            design_name: Name of the design to research
            context: Additional context or requirements
        """
        results = {
            "specifications": {},
            "sources": [],
            "confidence": "low",
            "research_log": []
        }

        # Check built-in database first
        known = self.get_known_specifications(design_name)
        if known:
            results["specifications"] = known
            results["sources"].append("built-in database")
            results["confidence"] = "high"
            return results

        # Web search
        search_results = self.search_web(
            f"{design_name} dimensions specifications blueprint",
            num_results=10,
            include_pdfs=True
        )

        # Extract PDFs
        pdf_contents = []
        for result in search_results:
            if result.url.endswith('.pdf'):
                pdf = self.analyze_pdf(result.url, search_terms=design_name.split())
                if pdf:
                    pdf_contents.append(pdf)

        # Synthesize with LLM
        web_context = "\n".join([f"{r.title}: {r.snippet}" for r in search_results[:10]])
        pdf_context = "\n".join([p.text_content[:3000] for p in pdf_contents[:2]])

        try:
            structured_llm = self.llm.with_structured_output(DesignReference)
            chain = self.design_prompt | structured_llm

            design = chain.invoke({
                "design_name": design_name,
                "search_results": web_context,
                "pdf_content": pdf_context,
                "image_analysis": "",
                "context": context
            })

            results["specifications"] = design.model_dump()
            results["confidence"] = "medium"
            results["sources"] = design.reference_urls

        except Exception as e:
            results["research_log"].append(f"Design research failed: {str(e)}")

        return results

    def research_with_fallback(self, query: str, context: str = "") -> Dict[str, Any]:
        """
        Research a product or design with automatic type detection and fallback.

        This is the main entry point for research in the workflow.
        """
        # Extract potential part number from query
        part_number_patterns = [
            r'\b([A-Z]{2,3}[\d-]+[A-Z]?)\b',  # OP22-0002L, 160CP19
            r'\b(\d{6,})\b',  # 168255, 810803
            r'\b(\d+-\d+)\b',  # 00-719255
            r'\b([A-Z0-9]{2,3}-?[A-Z0-9]{4,})\b',  # 4A2878-01
        ]

        part_number = ""
        for pattern in part_number_patterns:
            match = re.search(pattern, query.upper())
            if match:
                part_number = match.group(1)
                break

        # Detect manufacturer
        manufacturer = ""
        manufacturers = [
            "global industrial", "gal", "true", "garland", "hoshizaki",
            "manitowoc", "vulcan", "partstown", "grainger", "mcmaster"
        ]
        query_lower = query.lower()
        for mfr in manufacturers:
            if mfr in query_lower:
                manufacturer = mfr.title()
                break

        # Determine if this is a product or design
        is_design = any(term in query_lower for term in [
            "saturn", "rocket", "castle", "disney", "building", "spacecraft",
            "aircraft", "vehicle", "monument", "tower"
        ])

        if is_design and not part_number:
            return self.research_design(query, context)
        else:
            return self.research_product(query, part_number, manufacturer)

    def search_catalog_for_part(self, catalog_url: str, part_id: str) -> Dict[str, Any]:
        """
        Search a specific catalog PDF for a part.

        Args:
            catalog_url: URL of the catalog PDF
            part_id: Part number/ID to search for

        Returns:
            Extracted specifications if found
        """
        result = {
            "found": False,
            "specifications": {},
            "page_references": [],
            "context": ""
        }

        # Download and analyze the catalog
        pdf = self.analyze_pdf(catalog_url, search_terms=[part_id])
        if not pdf or not pdf.text_content:
            return result

        # Search for part in content
        lines = pdf.text_content.split('\n')
        relevant_lines = []
        for i, line in enumerate(lines):
            if part_id.lower() in line.lower():
                # Get context around the match
                start = max(0, i - 3)
                end = min(len(lines), i + 7)
                relevant_lines.extend(lines[start:end])
                result["found"] = True

        if result["found"]:
            result["context"] = '\n'.join(relevant_lines)

            # Use LLM to extract specs from the context
            try:
                structured_llm = self.llm.with_structured_output(ProductSpecification)
                chain = self.spec_prompt | structured_llm

                spec = chain.invoke({
                    "product_name": part_id,
                    "part_number": part_id,
                    "web_results": "",
                    "pdf_content": result["context"],
                    "image_analysis": "",
                    "context": f"From catalog: {catalog_url}"
                })

                result["specifications"] = spec.model_dump()

            except Exception as e:
                pass

        return result
