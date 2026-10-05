from LLMBatcher.configs.schemas import TaskConfig, AgentConfig, ComputeConfig
from LLMBatcher.common.myenums import Stages, TaskTypes, ThinkingLevels

from LLMBatcher.configs.agent_schemas.bbox_agent import  bbox_agent_schema
from LLMBatcher.configs.agent_schemas.spanning_agent import section_span_agent_schema 
from LLMBatcher.configs.agent_schemas.image_extraction_agent import  image_extraction_agent_schema 
from LLMBatcher.configs.agent_schemas.marginalia_extraction_agent import marginalia_extraction_schema
from LLMBatcher.configs.agent_schemas.table_agent import table_extraction_schema 
from LLMBatcher.configs.agent_schemas.table_classification import table_classification_schema
from LLMBatcher.configs.agent_schemas.text_extraction_agent import text_extraction_schema
from LLMBatcher.configs.agent_schemas.text_classification_agent import text_classification_schema
from LLMBatcher.configs.agent_schemas.attestation_agent import attestation_extraction_schema
from LLMBatcher.configs.agent_schemas.page_linkage_agent import page_linkage_schema

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
 You are a precise document layout analyzer. Given a single document page image, detect every semantic section on the page and output each section's bounding box, type, parent/child relationship, and reading-order position, in the JSON format specified at the end of this prompt.

      A "section" is a coherent block of content with a unified purpose — e.g. "Introduction", "Figure 3", "Contact Information", a page header, a page footer.

      ===========================================================
      CRITICAL CONSTRAINTS — read this before anything else.
      These are the rules most likely to be violated. Carry them through the rest of the prompt, and check your output against all four in the self-verification step before you emit anything.
      ===========================================================

      1. TABLE PRECEDENCE. A repeating row/column structure — header row through the last data row present on the page — is ONE section, type="table". This holds even when individual cells contain bold text, ALL-CAPS labels, or text that looks like a heading (a bold drug name, a bold "Patient Name:" label). If a bold or label-like string repeats in the same relative position across multiple rows, it is a table cell, not a title. Never split a table row into a title box + body box.

      2. NO OVERLAPPING BOXES. Two boxes may never overlap, with the sole exception of a scan_code or attestation genuinely stamped on top of other content. Check every pair of boxes before finalizing output.

      3. TIGHT TITLE/BODY SPLIT. Where a heading introduces a section, and that section is not part of a table, the heading gets its own tight box (type="title") and nothing else; the body gets a separate box below it, with parent_id pointing back to the title. Never use one box for both.

      4. COLUMN-GROUPED READING ORDER. On a multi-column page, read every section in the left-most column band, top to bottom, before any section in the next column band. Never interleave sections from different columns by y-coordinate.

      ===========================================================
      TYPE TAXONOMY — single source of truth. Use only these eight types.
      ===========================================================

      - "title": a heading/short block that introduces the content below it — numbered headings, named headings, ALL-CAPS form labels, bold/underlined standalone headings, form-section dividers. Tight box around the heading line only.
        - Does NOT apply to a label inside a repeating table row (see constraint 1) — that stays inside the table's box.
        - Does NOT apply to table/figure captions (e.g. "Table 1:", "Figure 3:"). A caption labels a figure/table rather than introducing a body section beneath it — classify captions as type="text" instead, in their own box (see "text" and "image" below).

      - "text": any textual content that is not part of a repeating table structure — paragraphs (single- or multi-column), lists, standalone key-value pairs, flowing or multi-line text, checkboxes, form fields, and table/figure captions. Also covers any header/footer/margin region that contains a checkbox, radio button, signature field, or key-value pair (contrast with "marginalia" below, which is the plain-text case of the same region).

      - "marginalia": plain, non-interactive text outside the main body — headers, footers, page numbers, side-margin notes, footnotes, watermarks. If the region has any fillable field (a checkbox, a signature line, a "Page __ of __" blank, a "Reviewed by: ___" line), classify it as "text" instead, even though it sits in the header/footer/margin. Never includes barcodes or QR codes (always "scan_code") or logos/purely graphical marks (always "image"), even when they sit in a header, footer, or margin.

      - "table": a repeating row/column structure. One box for the entire structure — header through the last row present on the page. See constraint 1.

      - "image": visual content only — figures, photos, logos, diagrams, charts, drawings, icons, illustrations. A caption is a separate type="text" box (per the "title" and "text" entries above) — do not merge caption text into the image's own bounding box; keep the image box tight to the visual content only.

      - "attestation": hand-written signatures, e-signatures, stamps, seals.

      - "scan_code": barcodes and QR codes, even when physically overlapping other content.

      - "card": identification cards, driver's licenses.

      heading_level: set only when type="title" (1 = top-level, 2 = sub-heading, 3 = sub-sub-heading). Leave null for every other type.

      ===========================================================
      BOUNDING BOXES
      ===========================================================

      - Normalize coordinates to a 0-1000 scale on both axes: box_2d = [ymin, xmin, ymax, xmax].
      - If a section has its own heading and is not part of a table, the heading gets its own tight box; the body beneath it gets a separate box.
      - If a section has no heading, start the box at the top-left of its first content line (text or image) and end at the bottom-right of its last content element.
      - A table's box encloses every row and column present on the page in a single box. Never split one table across multiple boxes; never leave a row outside the box.

      ===========================================================
      PARENT-CHILD RELATIONSHIPS (parent_id)
      ===========================================================

      - text/table/image directly under a title -> parent_id = that title's section_id.
      - A sub-heading under a higher-level title -> parent_id = the higher-level title's ID (not further up the chain).
      - Content directly under a sub-heading -> parent_id = that sub-heading's ID.
      - marginalia -> parent_id = "" always.
      - Top-level titles, or the document title -> parent_id = "".
      - A table is one atomic section: its internal rows/cells never get their own parent_id; only the table's own parent_id (its section title, if it has one) is set.
      - In multi-column layouts, a section's parent is always the title in its own column, never a title in a different column, even if they sit at the same height.

      ===========================================================
      READING ORDER
      ===========================================================

      Work this out in two passes. Do this BEFORE assigning final section IDs (see "Assigning IDs" below).

      Pass 1 - find column bands: Look at the x-ranges of every text/title/table/image section, excluding marginalia. If several sections share a consistent, non-overlapping x-range (e.g. one group spans roughly x=20-280, another spans roughly x=300-560), those are separate column bands. Judge this by geometry alone - not by topic, section count, or how many columns a page like this "usually" has.

      Pass 2 - sequence:
      a. Header marginalia first (top of page).
      b. Any section whose x-range spans, or nearly spans, the full content width, sitting above a column split, is read at that point - before the columns beneath it.
      c. Column bands are read strictly left-to-right (right-to-left for RTL documents). Every section in one band, top-to-bottom, before any section in the next band. Never alternate bands by y-coordinate, even if a right-column section starts higher on the page than a left-column section ends.
      d. A full-width section appearing below a set of columns (a footer note, a full-width table) is read after all column bands above it.
      e. A sidebar/inset is read immediately after the column band it visually interrupts or sits beside.
      f. A caption follows its figure/table immediately; footnotes follow all body content in their zone, before the footer.
      g. Footer marginalia last.

      Self-check before finalizing: list your section IDs in chosen order alongside which column band each belongs to. If the sequence alternates (A, B, A, B, A, B), that is almost always wrong - go back and group all of A together, then all of B. The only case where alternation is correct is when a genuine full-width section separates two independent column groups (see rule b).

      ===========================================================
      ASSIGNING IDS
      ===========================================================

      Only after reading order (above) is settled: assign S1, S2, S3... to every section in that final order. Do this last, not while you are still detecting sections. The array you output should already be in this order, and the ID numbers must match it - S1 first, S2 second, and so on.

      ===========================================================
      EXAMPLES (illustrative only - do not output these)
      ===========================================================

      Example A - standard single-column page:
      {
        "sections": [
          {"section_id": "S1", "box_2d": [10, 15, 60, 585], "type": "marginalia", "heading_level": null, "parent_id": ""},
          {"section_id": "S2", "box_2d": [70, 40, 90, 300], "type": "title", "heading_level": 1, "parent_id": ""},
          {"section_id": "S3", "box_2d": [95, 40, 180, 560], "type": "text", "heading_level": null, "parent_id": "S2"},
          {"section_id": "S4", "box_2d": [200, 120, 350, 480], "type": "image", "heading_level": null, "parent_id": "S2"},
          {"section_id": "S5", "box_2d": [800, 200, 830, 400], "type": "marginalia", "heading_level": null, "parent_id": ""}
        ]
      }

      Example B - table with bold cell labels. The page has a heading "Current Medications" followed by a table where each row has a bold drug name, dose, and refill count. The bold drug names are NOT extracted as separate title sections - the whole table is one box (constraint 1):
      {
        "sections": [
          {"section_id": "S1", "box_2d": [12, 20, 40, 550], "type": "marginalia", "heading_level": null, "parent_id": ""},
          {"section_id": "S2", "box_2d": [60, 40, 82, 320], "type": "title", "heading_level": 1, "parent_id": ""},
          {"section_id": "S3", "box_2d": [90, 40, 420, 560], "type": "table", "heading_level": null, "parent_id": "S2"}
        ]
      }

      Example C - two-column page (reading order). A full-width title (S1) sits above two columns: the left column has a sub-heading and two paragraphs (S2, S3, S4); the right column has a figure and its caption (S5, S6).
      CORRECT order: S1, S2, S3, S4, S5, S6 - every left-column section is read before any right-column section.
      WRONG order: S1, S2, S5, S3, S6, S4 - this interleaves columns by y-coordinate instead of finishing the left column first. This is exactly the alternating pattern the self-check above is designed to catch.
      {
        "sections": [
          {"section_id": "S1", "box_2d": [20, 30, 60, 970], "type": "title", "heading_level": 1, "parent_id": ""},
          {"section_id": "S2", "box_2d": [80, 30, 100, 480], "type": "title", "heading_level": 2, "parent_id": "S1"},
          {"section_id": "S3", "box_2d": [110, 30, 300, 480], "type": "text", "heading_level": null, "parent_id": "S2"},
          {"section_id": "S4", "box_2d": [310, 30, 480, 480], "type": "text", "heading_level": null, "parent_id": "S2"},
          {"section_id": "S5", "box_2d": [80, 520, 350, 970], "type": "image", "heading_level": null, "parent_id": "S1"},
          {"section_id": "S6", "box_2d": [355, 520, 380, 970], "type": "text", "heading_level": null, "parent_id": "S1"}
        ]
      }

      ===========================================================
      SELF-VERIFICATION - run this before you output anything
      ===========================================================

      - Every pair of boxes: do any overlap? If so, resize/clip or merge them.
      - Does any table look like it has been split into multiple table sections, or a table row split into a title + text pair? If so, merge it back into one table box.
      - Does any bold/label-like string you classified as "title" repeat in the same relative position across multiple rows elsewhere on the page? If so, it is a table cell - fold it back into the table box.
      - In the final array, do the column-band labels for your section order read A, B, A, B (alternating)? If so, re-group by column band per the reading-order self-check.
      - Do the boxes collectively cover all major content, with nothing significant omitted and no box sitting over pure whitespace?
      - Enclose the sybmols, icon, checkbox or radio button at the start or end of phrase with in the box, rather than leaving it outside the box? If not, resize the box to include it.
      - IMPORTANT INSTRUCTION (TITLE RE-VERIFICATION): If you identify a box as a title, and it consists of a selected, unselected, filled, unfilled, marked or unmarked checkbox or radio button (square/rectangle/circle shape at the beginning or end of the phrase in the layout), classify it as type="text" instead, in its own box (see "text" below). 

      ===========================================================
      OUTPUT FORMAT
      ===========================================================

      Return only valid JSON - no explanation, no markdown fences. Top-level key "sections" -> array of objects:

      {"section_id": "string", "box_2d": [ymin, xmin, ymax, xmax], "type": "string", "heading_level": null_or_int, "parent_id": "string"}

      Sort the array in the final reading order determined above.

      Follow the four CRITICAL CONSTRAINTS strictly:
      1. Never split a table row into a title box and a body box, even when a cell contains bold or label-like text that repeats across rows.
      2. No two boxes may overlap.
      3. Every non-tabular heading gets its own tight box, separate from its body.
      4. Reading order must group all sections in one column band before moving to the next - never alternate columns by y-coordinate.

      Run the full self-verification checklist before producing output, and correct any overlapping boxes, incorrectly split table rows, or alternating-column reading order you find.

      Provide the output in the defined JSON format strictly and do not miss any sections.""",
        thinking_level=ThinkingLevels.LOW,
        response_json_schema=bbox_agent_schema,
        max_output_tokens=7000,
        seed=42
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

# One per-document compute task, spawned once every page of the document has settled
# (annotated, or terminated at end, or failed). It resolves which pages pair with which
# - donut's _prev_nonempty_page, core.py:1386 - and builds everything the linking agent
# needs to judge each pair: the indented section tree and candidate ids printed into the
# prompt (_find_continuation_candidates, core.py:1240) and the two-page stitched image
# (_stitch_pages_top_to_bottom, core.py:1113). All of it is written onto Page.
#
# ngl_donut_ai does this inline inside link_all_pages (core.py:1383), where the values
# live in locals for the length of one await. Here the payload is built by this worker
# and read back by the orchestrator when it builds the agent request - different
# processes - so it has to persist.
stage_configs[Stages.build_page_pairs] = TaskConfig(
    name=Stages.build_page_pairs,
    task_type=TaskTypes.compute,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue="build_page_pairs"
    )
)

# The <reading_order> half of the link_page_continuity prompt. It is spliced into the
# {reading_order_block} hole below, but only for pairs where BOTH sides have candidates -
# otherwise the hole is filled with "". That conditional is why this text is a separate
# constant instead of part of human_prompt: orchestrator.py picks between this and ""
# when it builds LLMRequest.variables.
#
# ngl_donut_ai keeps this text in core.py:1405 rather than in its prompt YAML, because
# YAML cannot express the condition. Our prompts are Python, so it lives with the prompt
# it belongs to - one file holds both halves.
#
# Extracted byte-for-byte from ngl_donut_ai core.py:1405, indentation included. The
# {prev_last_id} and {current_first_id} braces are LITERAL and deliberate: donut's string
# has no f-prefix and its variable dict (core.py:1295) passes only prev_tree_str,
# tree_str and reading_order_block - so those two braces reach the model unsubstituted.
# We reproduce that. fill_prompt_variables replaces per-key, so it leaves them alone too.
READING_ORDER_BLOCK = r"""
                        <reading_order>
                        A page's reading order moves through its columns in sequence, finishing one column entirely before starting the next — so the section that comes last in a page's own reading order is often its rightmost column, not its leftmost, and that is the one most likely to continue onto the next page. In the stacked image, that means the true continuation candidate is usually diagonal across the page break (previous page's last column connecting to the current page's first column), not the section directly above it at the same horizontal position.

                        In this pair of pages: {prev_last_id} is last in the previous page's own reading order. {current_first_id} is first in the current page's own reading order. If the previous page's content was cut off, {prev_last_id} continuing into {current_first_id} is the pairing to check first — confirm it by reading whether {prev_last_id}'s content is genuinely incomplete and {current_first_id} genuinely completes it, the same way you would confirm any other candidate.
                        </reading_order>
                    """

stage_configs[Stages.link_page_continuity_agent] = TaskConfig(
    name=Stages.link_page_continuity_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        temperature=0.1,
        model_name="gemini-3-flash-preview",
        system_prompt="",
        # Ported verbatim from ngl_donut_ai configs/AgentConfigs/link_page_continuity.yaml.
        # {prev_tree_str}, {tree_str} and {reading_order_block} are template holes filled at
        # request-build time (request_payload.build_request_parts) from LLMRequest.variables -
        # they are NOT part of the prompt text this pipeline sends verbatim.
        human_prompt=r"""<role>
You are a document-continuity analyst. You are shown one tall image: the PREVIOUS page stacked above a thick yellow "PAGE BREAK" bar, the CURRENT page stacked below it — one image, not two. Section boxes have IDs printed directly on them (e.g. "Page1_S5", "Page2_S1"). The pages were rescaled to a common width to stack them, so identify sections by their printed IDs and by reading their actual content, not by their horizontal position in the stacked image — two boxes lining up at the same x-position across the page break is a coincidence of the layout, not evidence of a connection between them.
</role>

<previous_page_sections>
{prev_tree_str}
</previous_page_sections>

<current_page_candidates>
{tree_str}
</current_page_candidates>
{reading_order_block}
<guidance>
New document: look specifically at two concrete things, then weigh them with the rest.
- Marginalia (page numbers, footers, headers): read the actual printed page number and footer/header text on both pages. A number that continues the same sequence (e.g. 6 → 7) supports the same document; a reset or an unrelated footer (e.g. 6 → 1, or different footer wording, date, or reference) supports a new one — on its own this is still weak evidence, since numbering can legitimately restart for an appendix.
- Visual style (layout template, typography, color scheme, borders or frames, logo or letterhead): a document keeps this consistent across its own pages, so an abrupt change to a genuinely different template — not just a photo sitting next to a form, but a different overall page design — supports a new document.

Combine these with content type and any persisting identifiers (case/order/invoice numbers); no single signal decides this alone. Text that picks up mid-thought from the previous page is always the same document, regardless of anything else.

Continuations (only relevant when it is the same document): a section only needs a match if it has nowhere left to go on its own page — multi-column pages routinely flow bottom-of-one-column into top-of-next-column within the same page, which is normal and not a cross-page continuation. A page can carry several independent content streams in parallel — separate columns, separate lists, separate note sections — and each one is its own complete, self-contained check: confirm every stream on its own merits, the same way you would if it were the only one on the page, regardless of how many others you've already confirmed or ruled out. "Genuinely incomplete" covers more than an unfinished sentence: an enumerated or bulleted list that simply stops with no closing line, summary, or new heading after it is just as much a cutoff as a sentence trailing off mid-word — confirm a match by reading the actual words, sentences, list items, or data sequences on both sides of the break. When in doubt, don't match — a missed continuation costs far less than a false one.

Example: page 2's right column ends mid-sentence with no further column below it on page 2; page 3's left column opens by finishing that exact sentence — that is a real match, even though the right column of page 2 and the left column of page 3 sit at different horizontal positions.

Example: page 1's left column ends with one entry of a bulleted problem list, with no closing line after it and no further column below it on page 1; page 2's left column opens with the next entry of that same kind of list, with no new heading introducing it — that is also a real match, even though neither side has an unfinished sentence. A sentence continuation and a list continuation like this one can both be genuine at once on the same two pages, in different columns — each is checked independently, and finding one does not mean the search is done.

Example: page 5 has a different letterhead and organization name than page 4, its page numbering restarts at 1, and it opens with its own title rather than continuing anything from page 4 — that is a new document, and continuations must be empty.
</guidance>

<task>
Decide is_new_document for the current page. If true, continuations must be empty. If false, decide which current-page candidates continue a specific previous-page section.
</task>
""",
        thinking_level=ThinkingLevels.LOW,
        response_json_schema=page_linkage_schema,
        max_output_tokens=10000,
        seed=42
    )
)

# build_cross_page_hierarchy is a single per-document compute task with no LLM call -
# it folds the per-page-pair linkage verdicts into Section.continues_from_section_id
# and the document splits (ngl_donut_ai core.py:1476).
stage_configs[Stages.build_cross_page_hierarchy] = TaskConfig(
    name=Stages.build_cross_page_hierarchy,
    task_type=TaskTypes.compute,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue="build_cross_page_hierarchy"
    )
)

stage_configs[Stages.semantic_grouping_and_extraction_blocks] = TaskConfig(
    name=Stages.semantic_grouping_and_extraction_blocks,
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
        model_name="gemini-3.5-flash-lite",
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
        model_name="gemini-3.1-flash-lite",
        system_prompt="",
        human_prompt=r"""
## **ROLE & COMPETENCY**
You are an **expert document analyst with 20 years of experience** in large-scale and fine-grained document content extraction.

You are given a **cropped image** of a document region. Your job is to extract everything visible in this crop into **precise, non-hallucinated, structured JSON** with **semantic hierarchy relationships**.

---

## **TXT_BLOCK — DEFINITIONS & SUBSECTIONS**
Everything in this crop falls under one or more of the following categories:
- paragraphs, sentences, phrases, words
- unordered lists
- ordered lists
- key-value pairs
- checkboxes
- radio buttons
- signatures

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
* **Never Invent a Key:** The key must be the exact label text actually printed/visible next to the value. Do NOT invent, infer, or paraphrase a key from context when no label is shown — if a value has no visible label, it is not a `key_values` element; extract it as plain `text` instead.
* **Multiple Values:** A `value` can be either a **single string** or a **list of strings**. Use a single string when the key maps to exactly one value. Use a list of strings when the key maps to multiple distinct values (e.g., several selected options, multiple line items, or multiple entries listed under one label).

#### **4. Choices (Checkboxes & Radio Buttons)**
Detect checkboxes (□/☑/☒/■) and radio buttons (○/●) positioned immediately before or after a text phrase, even from a small cropped fragment.
Classify using visible evidence:
- Only straight horizontal/vertical edges forming a box corner, no diagonal stroke → Unselected (0)
- Only a curved arc forming part of a circle, no line/fill inside → Unselected (0)
- Any diagonal stroke, X, check-like stroke, or solid fill present, even partial → Selected (1)
- A stroke that is NOT purely horizontal/vertical (i.e., angled or irregular) adjacent to a phrase should be treated as a checkmark/strike-through fragment → Selected (1)
- If truly no stroke or fill is visible at all, only a clean outline → Unselected (0)
Output per element: phrase text, type (checkbox/radio), state (1/0).

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

**Formatting rules for text content:**
- Mathematical formulas, equations, and expressions must be transcribed in **LaTeX** notation (e.g., `$x^2 + y^2 = z^2$`, `$\frac{a}{b}$`).
- Special characters and symbols (e.g., °, ±, µ, ×, ÷, ™, ©, é, ñ) must be transcribed as their actual **Unicode** characters, not escaped sequences or spelled-out names.

#### **7. Generate Summary**
Create a highly concise summary (maximum 50 words) based on what you observe that captures essential textual content without information loss.

---

## STRICT Guardrails (Must Follow)
### Extraction Rules
- Extract content AS-IS, exactly as visible.
- You MUST NOT hallucinate any text.
- You MUST NOT infer missing text or meaning.
- You MUST NOT create keys or values that are not present in the image.
- If OCR misses text visible in the image → add it manually.
- Never add punctuation or formatting that is not present.
- Never merge or split lines that appear separately unless it clearly forms a single coherent semantic unit.

### Subsection Rules
- If no subsection applies → return an empty list.
- Do NOT include bounding boxes or coordinates.

## 🟦 JSON Output Structure

1. **Key-Value Pairs**
```json
{"id":"e001","type":"key_values","key":"<exact key as seen>","value":"<exact value as seen or empty string if empty>"}
```
Or, when the key maps to multiple values:
```json
{"id":"e001","type":"key_values","key":"<exact key as seen>","value":["<value1>","<value2>"]}
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
- Level 0 = topmost heading/subsection visible in this crop.
- Level increases as structure descends.

---
## Relationships Section
Relationships describe the **visual, structural, and/or semantic hierarchy** inside the crop.
You must determine which subsections belong under which parent, and connect them via their id keys:

```json
{"id":"r001","parent":"e001","child":"e004"}
```

---

## FINAL OUTPUT FORMAT
Return ONLY a valid JSON object with this structure:

```json
{"summary":"Concise summary under 50 words capturing essential textual content without information loss","elements":[{"id":"e001","type":"text","content":"Patient Information","level":0},{"id":"e002","type":"key_values","key":"Name","value":"John Doe"}],"relationships":[{"id":"r001","parent":"e001","child":"e002"}]}
```

**CRITICAL:**
- Return ONLY valid JSON, no explanations or markdown
- If no text is visible, return: {"summary":"No visible text content","elements":[],"relationships":[]}

NOW ANALYZE THE PROVIDED IMAGE AND RETURN STRUCTURED JSON
""",
        response_json_schema=text_extraction_schema,
        thinking_level=ThinkingLevels.MINIMAL,
        max_output_tokens=15000,
        seed=42
    )
)

stage_configs[Stages.marginalia_extraction_agent] = TaskConfig(
    name=Stages.marginalia_extraction_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        model_name="gemini-3.5-flash-lite",
        system_prompt="",
        human_prompt=r"""
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

**Parent ID (Hierarchy):**
Every element may declare a `parent_id` pointing at the id of the element it is nested under (e.g. a label element that is the parent of an image/value beside it).
- A top-level element (no parent in this crop) omits `parent_id` or sets it to `null`.
- `parent_id` must reference an id that exists in `elements`; never invent an id, and never set `parent_id` equal to the element's own `id`.

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
- **Mathematical formulas/equations:** transcribe using LaTeX (e.g. `$E = mc^2$`, `$\frac{a}{b}$`). Wrap inline formulas in single `$...$` and standalone/display formulas in `$$...$$`.
- **Special characters/symbols** (e.g. °, ±, ≤, ≥, ≠, µ, ½, ™, ®, ©, α, β, →): transcribe as the literal Unicode character, exactly as printed — do not spell them out or approximate with ASCII (e.g. use `≤`, not `<=`).
- Return only valid COMPACT JSON

ANALYZE THE MARGINALIA IMAGE NOW:
""",
        response_json_schema=marginalia_extraction_schema,
        max_output_tokens=10000,
        seed=42
    )
)

stage_configs[Stages.image_extraction_agent] = TaskConfig(
    name=Stages.image_extraction_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        model_name="gemini-3.5-flash-lite",
        system_prompt="",
        human_prompt=r"""
**TASK: Image Analysis**

You are an expert visual content analyst. Analyze the provided image and return ONLY image type and detailed description.

**REQUIREMENTS:**

1. **Identify Image Type:** Classify the image into one of these categories:
  - "chart" - Bar charts, line graphs, pie charts, scatter plots, histograms, data visualizations
  - "figure" - Photographs, realistic images, medical/scientific figures
  - "logo" - Company logos, brand marks, symbols, emblems
  - "infographic" - Process flows, diagrams, illustrations, flowcharts, instructional graphics
  - "map" - Geographical maps, floor plans, location diagrams
  - "barcode" - 1D barcodes
  - "qr_code" - QR codes or other 2D matrix codes
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

  **For Barcode/QR Code:**
  - Code type (1D barcode vs QR code / other 2D matrix code)
  - Any human-readable text/digits printed alongside the code (do NOT attempt to decode the code's pattern itself)
  - Surrounding label or context (e.g. "product barcode", "tracking sticker")

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
  "image_type": "chart|figure|logo|infographic|map|barcode|qr_code|other",
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
        max_output_tokens=7000,
        seed=42
    )
)

# Text Classification - cheap gate in front of text_extraction_agent.
stage_configs[Stages.text_classification_agent] = TaskConfig(
    name=Stages.text_classification_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        temperature=0,
        model_name="gemini-3.5-flash-lite",
        system_prompt="",
        human_prompt="""
You are an expert document-analysis assistant that classifies text-block
images. Follow the field description exactly.

Analyse the text-block image and decide whether
it contains any STRUCTURED content, or is PURE PROSE.

════════════════════════════════════════════════════════════════════════════
DEFINITIONS
════════════════════════════════════════════════════════════════════════════

has_structured_content = TRUE when the crop contains one or more of:
  • Key-value pairs - a label paired with a field/value (e.g. "Name: John Doe",
    a label next to a box/line/dropdown/chip).
  • Checkboxes or radio buttons before or after a phrase - any selectable indicator, such as a box, or circle 
    that may be checked, filled, marked, selected, or not. IMPORTANT NOTE: Due to cropping, these indicators may 
    appear incomplete or partially visible, but if any part of a checkbox/radio button is present, 
    it counts as structured content. 
  • Signature fields - a signature line or box, signed or blank.
  • Ordered lists - items preceded by incrementing numeric/alphanumeric
    markers (1., 2., i., ii., A., B., ...).
  • Unordered lists - items preceded by bullet markers (•, -, *, ...).
  • Image, Symbol, Icon - If the crop contains any non-text visual element (image fragment, icon, decorative graphic, Rectangle or Marker), it counts as structured content. Ignore the content of the image; just note its presence.

has_structured_content = FALSE when the crop is PURE PROSE:
  • Only paragraphs, sentences, phrases, or standalone headings/subheadings.
  • No labeled fields, no boxes/lines to fill in, no checkboxes/radios, no
    signature areas, no bulleted/numbered list markers.

When in doubt, favour TRUE (safer to run full extraction than to lose structured data).
""",
        thinking_level=ThinkingLevels.LOW,
        response_json_schema=text_classification_schema,
        max_output_tokens=7000,
        seed=42
    )
)

stage_configs[Stages.text_router] = TaskConfig(
    name=Stages.text_router,
    task_type=TaskTypes.router,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue=""
    )
)


# Attestation Extraction - hand-written signatures, e-signatures, stamps and seals.
stage_configs[Stages.attestation_extraction_agent] = TaskConfig(
    name=Stages.attestation_extraction_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        model_name="gemini-3.5-flash-lite",
        system_prompt="",
        human_prompt="""
**TASK: Attestation Mark Analysis**

You are an expert document analyst. Analyze the provided image, which may contain one or more attestation marks (signatures, stamps, or other marks), and return a list of elements describing each mark found.

**REQUIREMENTS:**

1. **Identify every distinct attestation mark in the image** and classify each into one of:
  - "hand_written_signature" - pen/ink signature written by hand
  - "e_signature" - digitally typed, drawn, or inserted signature (e.g. DocuSign-style signature block, typed name in a signature/cursive font, image-pasted signature)
  - "stamp" - notary/company stamps AND official seals of authenticity
  - "other" - any other attestation mark

2. **Per-type fields:**
  - "hand_written_signature": set `is_signed` to `true` if the signature area actually contains a handwritten signature, `false` if it is blank/unsigned.
  - "e_signature": set `signed_by` to the signer's name if legible, otherwise `null`.
  - "stamp": set `stamp_text` to the legible text within the stamp/seal (issuer, organization, registration number, date, etc.), otherwise `null`.
  - "other": set `content` to a free-form description of the mark.

3. **Generate Summary:** Create a highly concise summary (maximum 50 words) capturing the essential attestation content across all marks, without information loss.

**OUTPUT FORMAT:**
Return ONLY valid JSON with exactly this structure:

```json
{
  "summary": "Concise summary under 50 words capturing essential attestation content without information loss",
  "elements": [
    {"type": "hand_written_signature", "is_signed": true},
    {"type": "e_signature", "signed_by": "Jane Doe"},
    {"type": "stamp", "stamp_text": "Notary Public - State of NY"},
    {"type": "other", "content": "Description of the mark"}
  ]
}
```

**CRITICAL RULES:**
- NO hallucination - describe only what you actually see
- Extract exact text as it appears
- If no attestation mark is visible, return an empty `elements` list
- Do not use markdown or backticks in response
- Output must be valid JSON only

ANALYZE THE IMAGE NOW:
""",
        thinking_level=ThinkingLevels.LOW,
        response_json_schema=attestation_extraction_schema,
        max_output_tokens=7000,
        seed=42
    )
)


# Table Classification
stage_configs[Stages.table_classification_agent] = TaskConfig(
    name=Stages.table_classification_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        temperature=0.0,
        model_name="gemini-3.5-flash-lite",
        system_prompt="",
        human_prompt="""
You are an expert document-analysis assistant that classifies table 
images. Follow the field descriptions exactly and populate every field.

Analyse the table image and classify it according
to the schema. Apply the definitions below rigorously.

════════════════════════════════════════════════════════════════════════════
DEFINITIONS
════════════════════════════════════════════════════════════════════════════

is_heavily_redacted
  • true  → more than 50 % of the visible cell area is obscured by redaction
            marks (solid black bars, white-out blocks, pixelation, or any
            deliberate concealment of text/numbers).
  • false → redaction covers 50 % or less, OR none is present.

is_true_table
  The key test is SEMANTIC, not visual. Ask: "Do the columns carry
  independent analytical meaning, or are they just a layout device?"

  • true  → genuine 2-D matrix where:
              1. Columns have named or implied dimensions each carrying
                distinct meaning (e.g. "Q1 Sales", "Q2 Sales", "Q3 Sales").
              2. Rows represent separate entities measured across those
                dimensions.
              3. A cell's meaning depends on BOTH its row AND its column.
              Minimum: 2 meaningful columns × 2 data rows (header excluded).

            SPECIAL RULE — Lab / clinical result displays are ALWAYS true
            tables, even if they visually resemble KVP:
            Any image that shows laboratory, pathology, hematology, or
            clinical test results (CBC, CMP, LFT, BMP, urinalysis, lipid
            panel, coagulation, microbiology, culture, toxicology, genetic,
            radiology findings, or ANY numeric/textual test outcome) must be
            classified as is_true_table = True. This applies even when:
              – Only two columns are visible (e.g. Test Name | Result).
              – There is no explicit column header row.
              – It superficially looks like a list of "name: value" pairs.
            The presence of measured or reported clinical values is sufficient
            to treat the structure as a true table. Do not classify lab result
            displays as false tables under any circumstance.

  • false → grid appearance is a layout convenience, not a data model.
            Classify false in ALL of these cases, even when physically
            arranged in multiple columns:

              – Wrapped / snaking lists: a single list overflowing into
                multiple columns to save space (gene-test menus, drug
                formularies, multi-column checklists). Tell-tale sign:
                reading L→R then T→B, or T→B then L→R, yields one flat list.

              – Multi-column KVP blocks: independent label–value pairs
                arranged side-by-side purely to save space (e.g. patient
                demographics: "Name: John Doe  Age: 33  DOB: 01/01/90").
                Columns share no semantic header.

              – Repeated KVP groups: the same label-value template repeats
                across columns (e.g. "Item | Qty | Price" repeated twice).

              – Form fields: blank lines, checkboxes, or input boxes next to
                labels, even if arranged in a grid.

              – Single-column or single-row layouts, even with decorative
                borders (a true table requires both dimensions to be plural).

              – Directory / index blocks: entries arranged in a grid for
                space efficiency with no analytically meaningful column
                headers.

            When in doubt, favour false.

is_complex_table  (evaluate only when is_true_table is true)
  • true  → one or more of:
              a) Merged / spanned cells (colspan or rowspan).
              b) Multi-level / hierarchical headers.
              c) Row-group headers (leftmost cell spans several data rows).
              d) Nested inner tables inside a cell.
              e) Irregular column counts implying intentional spanning.
  • false → flat grid: every cell occupies exactly one row × one column,
            single-tier header, no spanning whatsoever.
            Always false when is_true_table is false.
            Simple tabular structure with no merged cells.

false_table_type  (evaluate only when is_true_table is false)
  Classify the non-table structure into one of three types:

  • "list" → the content is a single flat sequence that has been wrapped
            or split across columns purely for space efficiency. Reading
            top-to-bottom then left-to-right (or left-to-right then
            top-to-bottom) yields one continuous list with no independent
            column semantics. Includes:
              – Wrapped / snaking lists 
              – Directory / index blocks
              – Single-column or single-row layouts
            Use "list" only when NO item carries its own selection
            marker - if it does, classify as "list_with_selection" instead.

  • "list_with_selection" → same structure as "list" (a single flat
            sequence, not a true table), but any item ALSO carries its
            own checkbox, radio button, tick-box, or other
            selection/marking indicator (e.g. a test-name menu where
            every line has an empty or checked box, a symptom checklist
            with tick marks). Whether any item is checked/selected is
            itself meaningful data that plain OCR text can lose or
            garble, so this type is routed differently from a plain
            "list" even though the underlying layout is the same.

  • "kvp"  → a list of independent field–value attributes where:
              1. Each row is a self-contained key–value pair (field name +
                  its value). The key can be understood without any column
                  header or neighboring row.
              2. There is no shared schema — no column or row headers that
                  provide context across multiple rows.
              3. The document is essentially a list of attributes.

            Do NOT classify as "kvp" — these are true tables (is_true_table
            should be True, not false_table_type = "kvp"):
              – Lab / test result panels where column headers (Test, Result,
                Unit, Reference Range) define a shared schema across all rows.
                Example: "Hemoglobin | 12.5 | g/dL" — the column "Result"
                gives the value meaning; removing it makes the row ambiguous.
              – Any structure where a column header is required to interpret
                the values in a row — that is a true table.

  • null   → leave null when is_true_table is true.
════════════════════════════════════════════════════════════════════════════
""",
        thinking_level=ThinkingLevels.LOW,
        response_json_schema=table_classification_schema,
        max_output_tokens=7000,
        seed=42
    )
)

stage_configs[Stages.table_router] = TaskConfig(
    name=Stages.table_router,
    task_type=TaskTypes.router,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue=""
    )
)

stage_configs[Stages.content_extraction_using_ocr] = TaskConfig(
    name=Stages.content_extraction_using_ocr,
    task_type=TaskTypes.compute,
    task_config=ComputeConfig(
        task_type=TaskTypes.compute,
        queue="ocr_content_extraction"
    )
)


# Complex Table Extraction
stage_configs[Stages.table_extraction_agent] = TaskConfig(
    name=Stages.table_extraction_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        temperature=1,
        model_name="gemini-3.5-flash",
        system_prompt="",
        human_prompt="""
        Convert the image to an HTML table. The output should begin with <table> and end with </table>. Specify rowspan and colspan attributes when they are greater than 1. Do not specify any other attributes. Only use table related HTML tags, no additional formatting is required.
        """,
        thinking_level=ThinkingLevels.LOW,
        max_output_tokens=15000,
        seed=42
    )

)

# Simple Table Extraction
stage_configs[Stages.table_extraction_simple_agent] = TaskConfig(
    name=Stages.table_extraction_simple_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        temperature=0.1,
        model_name="gemini-3.1-flash-lite",
        system_prompt="",
        human_prompt="""
        Convert the image to an HTML table. The output should begin with <table> and end with </table>. Specify rowspan and colspan attributes when they are greater than 1. Do not specify any other attributes. Only use table related HTML tags, no additional formatting is required.
        """,
        thinking_level=ThinkingLevels.MEDIUM,
        max_output_tokens=15000
    )
)


# ---------------------------------------------------------------------------
# Cross-page table merge. One call over every page-crop in a continues_from lineage,
# instead of one call per page each returning a fragment of the same table.
#
# Ported from ngl_donut_ai configs/AgentConfigs/multipage_table_extraction.yaml, used at
# core.py:334. Donut keeps ONE config and assigns the model at runtime
# (core.py:346: "gemini-3.5-flash" if is_complex else "gemini-3.5-flash-lite"). Our configs
# are static, so that becomes two stages - the same translation already applied to donut's
# identical swap for single-page tables at core.py:249.
#
# The prompt below is donut's user_prompt byte-for-byte, INCLUDING the literal "\n"
# sequences. Donut writes them inside a YAML `|` block scalar, where escape sequences are
# NOT interpreted - so the model really does receive the two characters backslash-n as
# text, on top of the real newlines the block scalar already preserves. Replicated rather
# than cleaned up, per the port rule.
# TODO: strip the literal \n sequences once donut does; they are noise in the prompt.
#
# {length_of_crop_images} is filled from LLMRequest.variables. fill_prompt_variables
# (request_payload.py:9) does a plain str.replace of "{key}", not str.format, so the
# literal braces elsewhere in a prompt need no escaping.
#
# max_output_tokens is donut's 40000, well above the single-page agent's 15000: the output
# is one table spanning N pages, so the HTML is roughly N times longer.
# thinking_level LOW and temperature 1 are donut's too. The single-page agents use
# MEDIUM/0.1, but those values belong to a different prompt and a different job.
# ---------------------------------------------------------------------------

MULTIPAGE_TABLE_PROMPT = r"""
        You are given {length_of_crop_images} images, in page order, each a crop of the SAME
        table as it appears across consecutive pages of a PDF (image 1 = earliest page).
        Convert them into ONE continuous HTML table.\n\n
        Rules:\n
        1. Keep the header row(s) from IMAGE 1 only. If a later image repeats the same
        column headers, do not include that repeated header row again in the output.\n
        2. If the LAST row visible in one image and the FIRST row visible in the next image
        are two halves of one row split by the page break, fuse them into a single row,
        matching cells by column position.\n
        3. Otherwise, include all data rows in the given order — do not reorder, drop, or
        invent rows.\n
        4. Specify rowspan/colspan attributes when they are greater than 1. Only use
        table-related HTML tags, no additional formatting.\n\n
        Return ONLY the merged HTML table, starting with <table> and ending with </table>.
        """

stage_configs[Stages.table_extraction_multipage_agent] = TaskConfig(
    name=Stages.table_extraction_multipage_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        temperature=1,
        # donut: "gemini-3.5-flash" when is_complex_table (core.py:346). Kept on the same
        # model family as our single-page complex agent so the pair stays comparable.
        model_name="gemini-3.1-flash",
        system_prompt="",
        human_prompt=MULTIPAGE_TABLE_PROMPT,
        thinking_level=ThinkingLevels.LOW,
        max_output_tokens=40000,
        seed=42,
    )
)

stage_configs[Stages.table_extraction_multipage_simple_agent] = TaskConfig(
    name=Stages.table_extraction_multipage_simple_agent,
    task_type=TaskTypes.agent,
    task_config=AgentConfig(
        task_type=TaskTypes.agent,
        temperature=1,
        # donut: "gemini-3.5-flash-lite" when not is_complex_table (core.py:346).
        model_name="gemini-3.1-flash-lite",
        system_prompt="",
        human_prompt=MULTIPAGE_TABLE_PROMPT,
        thinking_level=ThinkingLevels.LOW,
        max_output_tokens=40000,
        seed=42,
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


######################## OBSOLETE
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
        model_name="gemini-3.5-flash-lite",
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
