from LLMBatcher.configs.schemas import TaskConfig, AgentConfig, ComputeConfig
from LLMBatcher.common.myenums import Stages, TaskTypes, ThinkingLevels

from LLMBatcher.configs.agent_schemas.bbox_agent import  bbox_agent_schema
from LLMBatcher.configs.agent_schemas.spanning_agent import section_span_agent_schema 
from LLMBatcher.configs.agent_schemas.image_extraction_agent import  image_extraction_agent_schema 
from LLMBatcher.configs.agent_schemas.marginalia_extraction_agent import marginalia_extraction_schema
from LLMBatcher.configs.agent_schemas.table_agent import table_extraction_schema 
from LLMBatcher.configs.agent_schemas.text_extraction_agent import text_extraction_schema

from typing import List, Optional
#TODO: This could be changed later on so that this data is loaded from either a DB or from a config file.

stage_configs = {}
stage_configs[Stages.load_pdf] = TaskConfig(
    name=Stages.load_pdf,
    task_type=TaskTypes.compute,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue="pdf_to_image"
    )
)

stage_configs[Stages.ocr] = TaskConfig(
    name=Stages.ocr,
    task_type=TaskTypes.compute,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue=""
    )
)

stage_configs[Stages.qc] = TaskConfig(
    name=Stages.qc,
    task_type=TaskTypes.compute,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue="quality_check"
    )
)

stage_configs[Stages.bbox_agent] = TaskConfig(
    name=Stages.bbox_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        temperature=0.1,
        model_name="gemini-3-flash-preview",
        system_prompt="",
        human_prompt="""
You are a precise document layout analyzer. Your task is to detect all **semantic sections** on the given document page image straightforward correctly without thinking.

**Instructions**:
1. **Identify every distinct semantic section**, where a *section* is a coherent block of content with a unified purpose (e.g., "Introduction", "Figure 3", "Contact Information", "Header", "Footer").
2. **CRITICAL: Apply strict table classification** - Only classify as "table" if the content has genuine 2D matrix structure with multiple rows AND columns. Key-value pairs, lists, forms, and checkbox grids must be classified as "text".
3. **For each section**:
   - **Include**:
     - Figures, tables, equations, and standalone images — *each as its own section*.
     - Page header (top margin area with repeated info like title/page number) — *if present*.
     - Page footer (bottom margin area with page numbers, dates, etc.) — *if present*.
   - **Bounding box (`box_2d`)** must be tightly cropped:
     - Start at the **top-left of the section's heading/title** (if a heading exists).
     - If **no heading**, start at the top-left of the first content line (text or image).
     - End at the **bottom-right of the last content element** in that section (e.g., last text line, bottom of image).
     - Coordinates must be in **pixel units** relative to the full page image: `[ymin, xmin, ymax, xmax]`.
     - **IMPORTANT**: Use [ymin, xmin, ymax, xmax] format (top, left, bottom, right).
   - **Label must be a concise, descriptive name:
     - Prefer explicit headings (e.g., "Methods", "Appendix A").
     - For figures/tables: use "Figure [number]" or "Table [number]" if captioned; otherwise "Figure" or "Table".
     - For header/footer: use "Header" or "Footer".
     - For uncaptioned images: use "Image".
     - For unheaded blocks (e.g., signature block): infer meaning (e.g., "Signature", "Address Block").
   - **Type (`type`)** must be one of: "marginalia" (headers/footers/page numbers), "text" (paragraphs/titles/lists/key-value pairs/forms), "table" (genuine 2D data matrices only), "image" (figures/photos/diagrams).

**Type Definitions**:
- **"marginalia"**: Content outside the main textual body - headers, footers, page numbers, side-margin notes, footnotes, watermarks, any text/graphical element clearly belonging to margins
- **"text"**: Any textual content - paragraphs (single/multi-column), titles, section headers, ordered/unordered lists, key-value pairs, checkboxes/radio buttons, flowing or multi-line text
- **"image"**: Visual content only - figures, photos, logos, diagrams, charts/graphs, drawings, illustrations, icons, stickers, attached visual elements. Include captions directly associated with an image inside the same block
- **"table"**: ONLY genuine 2-dimensional tabular data with BOTH multiple rows AND multiple columns containing actual data values that form a matrix structure. Must have clear intersecting row/column relationships where each cell represents data at the intersection of a specific row and column. **CRITICAL REQUIREMENT**: Information must be inherently 2D - cannot be meaningfully represented as simple key-value pairs or single-column lists.

3. **Output Requirements**:
   - Return **only valid JSON** — no explanations, no markdown.
   - Top-level key: `"sections"` → list of objects.
   - Each object: `{"box_2d": [ymin, xmin, ymax, xmax], "label": "string", "type": "string"}`.
   - Boxes must be non-overlapping and collectively cover all major content (excluding pure whitespace).
   - Sort sections in **top-to-bottom, left-to-right reading order** (e.g., header first, then main sections, then footer).

**Example Output** (do NOT output this—illustrative only):
{
  "sections": [
    {"box_2d": [10, 15, 60, 585], "label": "Header", "type": "marginalia"},
    {"box_2d": [80, 40, 180, 560], "label": "Abstract", "type": "text"},
    {"box_2d": [200, 120, 350, 480], "label": "Figure 1", "type": "image"},
    {"box_2d": [370, 40, 500, 560], "label": "Introduction", "type": "text"},
    {"box_2d": [800, 200, 830, 400], "label": "Footer", "type": "marginalia"}
  ]
}

Now analyze the provided page image and output the in the above JSON format strictly.

You must follow all rules strictly and respond using **only** the schema format provided above.
You must provide the output in defined json format strictly and should not miss any sections.

**CRITICAL REMINDER**: Only classify content as "table" if it has genuine 2D matrix structure with multiple data rows AND columns.
If content can be expressed as key-value pairs, lists, forms, or checkboxes - classify as "text" instead.
""",
        thinking_level=ThinkingLevels.LOW,
        response_json_schema=bbox_agent_schema,
        max_output_tokens=7000
    )
)

stage_configs[Stages.bbox_correction] = TaskConfig(
    name=Stages.bbox_correction,
    task_type=TaskTypes.compute,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue="bbox_correction"
    )
)

stage_configs[Stages.annotate_image] = TaskConfig(
    name=Stages.annotate_image,
    task_type=TaskTypes.compute,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue="image_annotator"
    )
)

stage_configs[Stages.semantic_grouping_and_extraction_blocks] = TaskConfig(
    name=Stages.annotate_image,
    task_type=TaskTypes.compute,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue="semantic_grouping_and_extraction_blocks"
    )
)

stage_configs[Stages.section_span_agent] = TaskConfig(
    name=Stages.section_span_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        temperature=0.5,
        model_name="gemini-2.5-flash",
        system_prompt="",
        human_prompt="""
**Role:**
You are an advanced vision-language reasoning system specialized in document structure analysis, visual comparison, contextual clustering, and semantic segmentation of scanned or photographed pages.

**Task:**
You are given:

1. **A full-page image** of a document page.
2. **A set of crop images**, each representing a smaller region extracted from that same page (e.g., headings, paragraphs, tables, diagrams, footnotes).

Your job is to visually and contextually determine **which crops belong together** as a coherent semantic section of the document.

A semantic section is defined as a group of crops that form a logical unit of meaning, typically grouped under a common heading or subheading.

---

## **You Must Perform the Following Steps**

### **1. Analyze Visual Structure**

For each crop and for the full page:

* Compare font style, size, weight, typography, line spacing.
* Identify headings, subheadings, paragraphs, lists, tables, figures.
* Look at spatial alignment and indentation patterns.

### **2. Analyze Contextual Meaning**

* Read all visible text inside each bounding box.
* Use context to determine whether bounding boxes share a topic or belong under the same heading.
* Match crops to the section headers visible in the full page or in the crops.

### **3. Determine Section Groupings**

For each distinct semantic section:

* Identify the **main heading text** exactly as it appears in the image.
* Group all crop IDs (bbox_ids) that belong under that heading.

### **4. Output Requirements**

Your final answer **must be a COMPACT JSON object** with this exact structure:

```json
{"sections":[{"section_header":"Exact text of the Main Heading","bbox_ids":["Page1_S1 | Label","Page1_S2 | Label"]}]}
```

**Rules:**

* `"section_header"` must contain the **exact text** of the heading as seen in the image.
* `"bbox_ids"` must list all bounding‐box IDs that belong to that section.
* Do **not** hallucinate content—only include text visible in the images.
* If no explicit heading exists, infer a descriptive label in this format: `"No Heading: Inferred Topic"`.

### **5. Additional Instructions**

* Keep ordering logical and left-to-right / top-to-bottom where applicable.
* Do not add extra fields or commentary inside the COMPACT JSON.

---
Now analyze the page and individual crops below:
                    """,
        thinking_budget=0,
        response_json_schema=section_span_agent_schema,
        max_output_tokens=7000
    )
)

stage_configs[Stages.section_cropping] = TaskConfig(
    name=Stages.section_cropping,
    task_type=TaskTypes.compute,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue="section_cropper"
    )
)

stage_configs[Stages.router] = TaskConfig(
    name=Stages.router,
    task_type=TaskTypes.router,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue=""
    )
)

stage_configs[Stages.text_extraction_agent] = TaskConfig(
    name=Stages.text_extraction_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        # temperature=0,
        model_name="gemini-2.5-flash",
        system_prompt="",
        human_prompt="""
# **TXT_BLOCK Content Extraction Prompt (Expert-Level, 20-Year Analyst)**

## **ROLE & COMPETENCY**
You are an **expert document analyst with 20 years of experience** in large-scale and fine-grained document content extraction.

You specialize **exclusively in analyzing TXT_BLOCKS** — blocks composed purely of textual information.
Your job is to read a cropped image and output **precise, non-hallucinated, structured COMPACT JSON** containing structured elements and **semantic hierarchy relationships**.

---

## **TXT_BLOCK — DEFINITIONS & SUBSECTIONS**
A **TXT_BLOCK** includes only textual representation of information such as:
- paragraphs, sentences, phrases, words
- unordered lists
- ordered lists
- key-value pairs
- checkboxes
- radio buttons

**If the block consists of a picture or any image content, IGNORE it — treat it as non-text.**

### **Subsections to Identify**

#### **1. Ordered List**
A list where each item is preceded by **incrementing numeric or alphanumeric markers**, such as:
- `1.`, `2.`, `3.`
- `i.`, `ii.`, `iii.`
- `A.`, `B.`, `C.`

#### **2. Unordered List**
A list with **bullet markers** such as:
- `•`, `-`, `–`, `*`


#### **3. Key-Value Pairs**

Key-value pairs **are NOT tables**.
A key-value pair consists of a **Label (Key)** and its associated **Field Content (Value)**.
* **Mapping:** If a label is positioned immediately above or to the left of a text box, dropdown, or chip, merge them into a single `key_values` element.
* The **Label** becomes the **Key**.
* The **Content inside the box/field** becomes the **Value**.
* **Structure:** A key-value pair has:
* a **key**, followed by a **colon**, **space**, **line**, or **border/box**, e.g.:
* `Name: ________`
* `[ Content inside a box ]`
* **Web & UI Elements:**
* **Selection Fields:** If a label is followed by a bounded box containing text (like a diagnosis), the text inside the box is the **Value**, NOT a new Key.
* **Dropdowns/Chips:** Use the currently selected/visible option as the value.
* **Empty States:** If a key has no corresponding value, return an empty string `""`.


#### **4. Choices (Checkboxes & Radio Buttons)**
Interactive selection elements such as:
- checkboxes , ,
- radio buttons ◯, ⬤

Detect selection state (selected = 1, unselected = 0).

#### **5. Signatures**
Signature fields or signature areas such as:
- Signature lines with labels like "Patient Signature:", "Doctor Signature:", "Authorized Signature:"
- Signature boxes or areas designated for signing

**For signatures, determine if signed or unsigned:**
- **flag: 1** if the signature field contains actual signature content (handwritten signature, electronic signature, or any mark indicating it has been signed)
- **flag: 0** if the signature field is blank, empty, or unsigned
- **Do NOT interpret the signature content itself** - only determine if something is present (signed) or absent (unsigned)

#### **6. Text (Free-Form Content)**
All textual content that is **not** an Ordered List, Unordered List, Key-Value Pairs, Choices, or Signatures.
Includes:
- paragraphs
- sentences
- phrases
- standalone words
- headings/subheadings

#### **7. Generate Summary**
Create a highly concise summary (maximum 50 words) based on what you observe that captures essential textual content without information loss.

---

## STRICT Guardrails (Must Follow)
### Extraction Rules
- Extract content AS-IS, exactly as visible.
- You MUST NOT hallucinate any text.
- You MUST NOT infer missing text or meaning.
- If OCR misses text visible in the image → add it manually.
- Never add punctuation or formatting that is not present.
- Never merge or split lines that appear separately unless it clearly forms a single coherent semantic unit.

### Subsection Rules
- If no subsection applies → return an empty list.
- Do NOT include bounding boxes or coordinates.


## Output Format (COMPACT JSON)
Each extracted element must produce a COMPACT JSON object with:
- ID format: e001, e002, e003, … (increment sequentially)
- IDs must be unique, never reused.

## 🟦 JSON Output Structure

1. **Key-Value Pairs**
```json
{"id":"e001","type":"key_values","key":"<exact key as seen>","value":"<exact value as seen or empty string if empty>"}
```

2. **Choices (Checkboxes / Radio Buttons)**
```json
{"id":"e002","type":"checkbox","key":"<label or text>","flag":1}
```

3. **Signatures**
```json
{"id":"e003","type":"signature","key":"<signature label>","flag":1}
```

4. **Lists (Ordered / Unordered)**
```json
{"id":"e004","type":"ordered","items":["<item1 as-is>","<item2 as-is>","<item3 as-is>"]}
```

5. **Free-Form Text**
```json
{"id":"e005","type":"text","content":"<text exactly as seen>","level":0}
```

**Level rules:**
- Use visual hierarchy (font size, boldness, capitalization, indentation).
- Level 0 = topmost heading/subsection for this crop.
- Level increases as structure descends.

---
## Relationships Section
Relationships describe the **visual, structural, and/or semantic hierarchy** inside the TXT_BLOCK.
You must determine which TXT_BLOCK subsections belong under which parent, and connect them via their id keys:

```json
{"id":"r001","parent":"e001","child":"e004"}
```

---

## FINAL OUTPUT FORMAT
Return ONLY a valid COMPACT JSON object with this structure:

```json
{"summary":"Concise summary under 50 words capturing essential textual content without information loss","elements":[{"id":"e001","type":"text","content":"Patient Information","level":0},{"id":"e002","type":"key_values","key":"Name","value":"John Doe"}],"relationships":[{"id":"r001","parent":"e001","child":"e002"}]}
```

**CRITICAL:**
- Return ONLY valid COMPACT JSON, no explanations or markdown
- If no text is visible, return: {"summary":"No visible text content","elements":[],"relationships":[]}
- Never include non-text content (images, charts, etc.)

NOW ANALYZE THE PROVIDED IMAGE AND RETURN STRUCTURED COMPACT JSON:
""",
        response_json_schema=text_extraction_schema,
        max_output_tokens=15000
    )
)

stage_configs[Stages.marginalia_extraction_agent] = TaskConfig(
    name=Stages.marginalia_extraction_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        model_name="gemini-2.5-flash",
        system_prompt="",
        human_prompt="""
**TASK: Marginalia Content Analysis**

You are an expert document analyst analyzing **marginalia content** - headers, footers, page numbers, logos, and other peripheral document elements.

**STEP 1: Identify Marginalia Type**
Classify as one of:
- "header" - Content at the top of the page
- "footer" - Content at the bottom of the page

**STEP 2: Identify and Extract Elements**
Analyze all visible content and extract as separate elements:

**STEP 3: Generate Summary**
Create a highly concise summary (maximum 50 words) based on what you observe that captures essential marginalia content without information loss.

**For TEXT Elements:**
Extract exactly like the text agent:
- Key-value pairs: {id, type: "key_values", key, value}
- Lists: {id, type: "ordered"/"unordered", items}
- Checkboxes: {id, type: "checkbox", key, flag}
- Free text: {id, type: "text", content, level}

**For IMAGE Elements:**
Extract exactly like the image agent:
- {id, type: "image", content: "chart|figure|logo|infographic|map|other","description":"detailed comprehensive description"}

**OUTPUT FORMAT:**
Return ONLY valid COMPACT JSON:

```json
{"summary":"Concise summary under 50 words capturing essential marginalia content without information loss","marginalia_type":"header","elements":[{"id":"e001","type":"image","content":"logo","description":"Logo"},{"id":"e003","type":"text","content":"Patient Laboratory Report","level":0}],"relationships":[]}
```

**Footer with page number:**
```json
{"summary":"Footer containing page navigation and copyright information","marginalia_type":"footer","elements":[{"id":"e001","type":"text","content":"Page 1 of 3","level":0},{"id":"e002","type":"text","content":" 2023 Medical Laboratory Inc.","level":0}],"relationships":[]}
```

**CRITICAL RULES:**
- For text: extract as text, key_values, lists, checkboxes with same COMPACT JSON structure
- For images: extract as image with same COMPACT JSON structure
- Extract ALL visible content exactly as shown
- Return only valid COMPACT JSON

ANALYZE THE MARGINALIA IMAGE NOW:
        """,
        response_json_schema=marginalia_extraction_schema,
        max_output_tokens=10000
    )
)

stage_configs[Stages.table_extraction_agent] = TaskConfig(
    name=Stages.table_extraction_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        temperature=0.1,
        model_name="gemini-3.5-flash",
        system_prompt="",
        human_prompt="""
        Convert the image to an HTML table. The output should begin with <table> and end with </table>. Specify rowspan and colspan attributes when they are greater than 1. Do not specify any other attributes. Only use table related HTML tags, no additional formatting is required.
        """,
        thinking_level=ThinkingLevels.MEDIUM,
        max_output_tokens=15000
    )
)

stage_configs[Stages.table_renderer] = TaskConfig(
    name=Stages.table_renderer,
    task_type=TaskTypes.compute,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue="render_table"
    )
)

stage_configs[Stages.table_verification_agent] = TaskConfig(
    name=Stages.table_verification_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        temperature=0.5,
        model_name="gemini-2.5-flash",
        system_prompt="",
        human_prompt="""
**Role:** You are a table quality assurance expert.

**Task:** Compare the original table image with the rendered HTML table and fix any structural or content issues.

**Instructions:**
1. **Compare Images:** Look at the original table crop and the rendered HTML version
2. **Identify Issues:** Check for:
   - Missing or incorrect cell content
   - Wrong cell positioning or alignment
   - Incorrect colspan/rowspan values
   - Missing rows or columns
   - Structural inconsistencies
3. **Fix HTML:** Provide the corrected HTML table that better matches the original
4. **Generate Summary:** Create a highly concise summary (maximum 50 words) based on what you observe that captures essential table content without information loss

**Requirements:**
- Use ONLY `<table>`, `<tr>`, and `<td>` tags
- Maintain semantic relationships between data
- Use appropriate class attributes (header, data, footer, section-header)
- Include the `<style>` block for formatting
- Ensure mathematical consistency (row cell counts must match table structure)

**Output:** Provide structured JSON output with exactly this format:
```json
{
  "summary": "Concise summary under 50 words capturing essential table content without information loss",
  "corrected_html": "Complete corrected HTML table code with <style> block"
}
```
                    """,
        thinking_budget=800,
        response_json_schema=table_extraction_schema,
        max_output_tokens=15000

    )
)

stage_configs[Stages.image_extraction_agent] = TaskConfig(
    name=Stages.image_extraction_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        model_name="gemini-2.5-flash",
        system_prompt="",
        human_prompt="""
**TASK: Image Analysis**

You are an expert visual content analyst. Analyze the provided image and return ONLY image type and detailed description.

**REQUIREMENTS:**

1. **Identify Image Type:** Classify the image into one of these categories:
   - "chart" - Bar charts, line graphs, pie charts, scatter plots, histograms, data visualizations
   - "figure" - Photographs, realistic images, medical/scientific figures
   - "logo" - Company logos, brand marks, symbols, emblems
   - "infographic" - Process flows, diagrams, illustrations, flowcharts, instructional graphics
   - "map" - Geographical maps, floor plans, location diagrams
   - "other" - Any other visual content not fitting above categories

2. **Write Detailed Description:** Provide comprehensive description covering ALL aspects visible in the image:

3. **Generate Summary:** Create a highly concise summary (maximum 50 words) based on what you observe that captures essential visual content without information loss.

   **For Charts/Graphs:**
   - Chart type (bar, line, pie, etc.)
   - Title and axis labels if visible
   - Data trends, patterns, key values
   - Legend information
   - All visible text and numbers
   - Key insights from the data

   **For Figures/Photos:**
   - Main subjects and objects
   - Setting/environment/background
   - Colors, lighting, composition
   - Any text, captions, or labels
   - Relevant details and context

   **For Logos:**
   - Design elements (shapes, colors, fonts)
   - Company/brand name if visible
   - Symbol or icon description
   - Text elements and styling

   **For Infographics/Diagrams:**
   - Overall structure and layout
   - Process flow or relationships shown
   - All text labels and annotations
   - Visual elements and connections
   - Purpose and information conveyed

   **For Maps:**
   - Geographic area or location
   - Landmarks, roads, boundaries shown
   - Scale, legend, or directional indicators
   - Any text labels or place names

   **For Other:**
   - Describe all visible elements
   - Purpose or function if apparent
   - Any text or identifying information

**INSTRUCTIONS:**
- Include a highly concise summary (maximum 50 words) that captures the essential content without information loss
- The summary should be based on what you actually observe in the image

**OUTPUT FORMAT:**
Return ONLY valid JSON with exactly this structure:

```json
{
  "summary": "Concise summary under 50 words capturing essential visual content without information loss",
  "image_type": "chart|figure|logo|infographic|map|other",
  "description": "Comprehensive detailed description covering all visual aspects without leaving any detail"
}
```

**CRITICAL RULES:**
- NO hallucination - describe only what you actually see
- Include ALL visible text, numbers, labels, captions
- Be thorough and detailed in description
- Extract exact text as it appears
- For charts, include actual data values and trends
- Do not use markdown or backticks in response
- Output must be valid JSON only

ANALYZE THE IMAGE NOW:
                            """,
        response_json_schema=image_extraction_agent_schema,
        max_output_tokens=7000
    )
)

stage_configs[Stages.end] = TaskConfig(
    name=Stages.end,
    task_type=TaskTypes.end,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue=""
    )
)


def get_agent_config(agent_name: str) -> Optional[AgentConfig]:
    if agent_name not in stage_configs.keys(): return None
    if not isinstance(stage_configs[agent_name].task_config, AgentConfig): return None
    return stage_configs[agent_name].task_config


def get_models_used_by_stages() -> List[str]:
    seen = set()

    for stage_config in stage_configs.values():
        if not isinstance(stage_config.task_config, AgentConfig):
            continue

        model_name = stage_config.task_config.model_name
        if model_name in seen:
            continue

        seen.add(model_name)

    models = list(seen)
    return models
