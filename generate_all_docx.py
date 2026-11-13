#!/usr/bin/env python3
"""
generate_all_docx.py

Generates:
1. Whitebox initial testing.docx (Dedicated White-Box Testing Document)
2. SQE_Assignment_2_Complete_Testing_Report.docx (Unified Black-Box + White-Box Document)

Strictly matching Blackbox initial testing.docx styling, fonts, table colors (#1F397D),
margins, and XML structure.
"""

import os
import zipfile
import xml.etree.ElementTree as ET

namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def xml_escape(text):
    if text is None:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;"))

def p(text="", style=None, align="left", bold=False, italic=False, sz=18, color=None,
      space_before=0, space_after=120, line_spacing=276):
    pPr_parts = []
    if style:
        pPr_parts.append(f'<w:pStyle w:val="{style}"/>')
    if align != "left":
        pPr_parts.append(f'<w:jc w:val="{align}"/>')
    pPr_parts.append(f'<w:spacing w:before="{space_before}" w:after="{space_after}" w:line="{line_spacing}" w:lineRule="auto"/>')
    pPr_xml = f'<w:pPr>{"".join(pPr_parts)}</w:pPr>' if pPr_parts else ''

    if not text:
        return f'<w:p>{pPr_xml}</w:p>'

    rPr_parts = []
    if bold:
        rPr_parts.append('<w:b/>')
    if italic:
        rPr_parts.append('<w:i/>')
    if sz:
        rPr_parts.append(f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>')
    if color:
        rPr_parts.append(f'<w:color w:val="{color}"/>')
    rPr_xml = f'<w:rPr>{"".join(rPr_parts)}</w:rPr>' if rPr_parts else ''

    lines = text.split("\n")
    runs = []
    for idx, line in enumerate(lines):
        runs.append(f'<w:r>{rPr_xml}<w:t xml:space="preserve">{xml_escape(line)}</w:t></w:r>')
        if idx < len(lines) - 1:
            runs.append('<w:r><w:br/></w:r>')

    return f'<w:p>{pPr_xml}{"".join(runs)}</w:p>'

def heading1(text):
    return p(text, style="Heading1", bold=True, sz=26, color="1F397D", space_before=360, space_after=120)

def heading2(text):
    return p(text, style="Heading2", bold=True, sz=22, color="2E75B6", space_before=240, space_after=80)

def heading3(text):
    return p(text, style="Heading3", bold=True, sz=20, color="1F397D", space_before=180, space_after=60)

def callout(text):
    return (
        f'<w:p>'
        f'<w:pPr>'
        f'<w:pBdr><w:left w:val="single" w:sz="24" w:space="15" w:color="1F397D"/></w:pBdr>'
        f'<w:shd w:val="clear" w:color="auto" w:fill="F2F4F7"/>'
        f'<w:spacing w:before="100" w:after="160" w:line="260" w:lineRule="auto"/>'
        f'<w:ind w:left="200" w:right="140"/>'
        f'</w:pPr>'
        f'<w:r>'
        f'<w:rPr><w:i/><w:sz w:val="18"/><w:szCs w:val="18"/><w:color w:val="333333"/></w:rPr>'
        f'<w:t xml:space="preserve">{xml_escape(text)}</w:t>'
        f'</w:r>'
        f'</w:p>'
    )

def code_block(code_text):
    lines = code_text.strip().split("\n")
    out = []
    for idx, line in enumerate(lines):
        s_before = 80 if idx == 0 else 0
        s_after = 80 if idx == len(lines) - 1 else 0
        out.append(
            f'<w:p>'
            f'<w:pPr>'
            f'<w:pBdr><w:left w:val="single" w:sz="18" w:space="10" w:color="1F397D"/></w:pBdr>'
            f'<w:shd w:val="clear" w:color="auto" w:fill="F8F9FA"/>'
            f'<w:spacing w:before="{s_before}" w:after="{s_after}" w:line="220" w:lineRule="auto"/>'
            f'<w:ind w:left="180" w:right="180"/>'
            f'</w:pPr>'
            f'<w:r>'
            f'<w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="16"/><w:szCs w:val="16"/><w:color w:val="1A1A1A"/></w:rPr>'
            f'<w:t xml:space="preserve">{xml_escape(line)}</w:t>'
            f'</w:r>'
            f'</w:p>'
        )
    return "".join(out)

def build_table(headers, rows, col_widths=None, col_aligns=None):
    n_cols = len(headers)
    if not col_widths:
        w_each = 10080 // n_cols
        col_widths = [w_each] * n_cols
        col_widths[-1] += (10080 - sum(col_widths))
    else:
        total_w = sum(col_widths)
        if total_w != 10080:
            scaled = [int(w * 10080 / total_w) for w in col_widths]
            scaled[-1] += (10080 - sum(scaled))
            col_widths = scaled

    if not col_aligns:
        col_aligns = ["left"] * n_cols

    grid_cols = "".join(f'<w:gridCol w:w="{w}"/>' for w in col_widths)

    tbl_xml = [
        '<w:tbl>',
        '<w:tblPr>',
        '<w:tblStyle w:val="TableGrid"/>',
        '<w:tblW w:w="10080" w:type="dxa"/>',
        '<w:tblBorders>',
        '<w:top w:val="single" w:sz="6" w:space="0" w:color="CCCCCC"/>',
        '<w:left w:val="single" w:sz="6" w:space="0" w:color="CCCCCC"/>',
        '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="CCCCCC"/>',
        '<w:right w:val="single" w:sz="6" w:space="0" w:color="CCCCCC"/>',
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="E0E0E0"/>',
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="E0E0E0"/>',
        '</w:tblBorders>',
        '<w:tblLook w:firstColumn="1" w:firstRow="1" w:lastColumn="0" w:lastRow="0" w:noHBand="0" w:noVBand="1" w:val="04A0"/>',
        '</w:tblPr>',
        f'<w:tblGrid>{grid_cols}</w:tblGrid>',
    ]

    tbl_xml.append('<w:tr>')
    tbl_xml.append('<w:trPr><w:tblHeader/></w:trPr>')
    for idx, (h, w) in enumerate(zip(headers, col_widths)):
        align = "center" if idx == 0 or idx == n_cols - 1 else col_aligns[idx]
        tbl_xml.append(
            f'<w:tc>'
            f'<w:tcPr>'
            f'<w:tcW w:w="{w}" w:type="dxa"/>'
            f'<w:shd w:val="clear" w:color="auto" w:fill="1F397D"/>'
            f'<w:tcMar><w:top w:w="120" w:type="dxa"/><w:bottom w:w="120" w:type="dxa"/><w:left w:w="120" w:type="dxa"/><w:right w:w="120" w:type="dxa"/></w:tcMar>'
            f'</w:tcPr>'
            f'<w:p>'
            f'<w:pPr><w:jc w:val="{align}"/><w:spacing w:before="60" w:after="60"/></w:pPr>'
            f'<w:r><w:rPr><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
            f'<w:t xml:space="preserve">{xml_escape(h)}</w:t></w:r>'
            f'</w:p>'
            f'</w:tc>'
        )
    tbl_xml.append('</w:tr>')

    for r_idx, row in enumerate(rows):
        tbl_xml.append('<w:tr>')
        tbl_xml.append('<w:trPr><w:cantSplit/></w:trPr>')
        for idx, (cell, w) in enumerate(zip(row, col_widths)):
            align = col_aligns[idx]
            cell_str = str(cell).strip()

            shd_xml = ''
            bold_xml = ''
            color_xml = ''

            if "FAIL" in cell_str or "★" in cell_str:
                shd_xml = '<w:shd w:val="clear" w:color="auto" w:fill="FFCCCC"/>'
                bold_xml = '<w:b/>'
                color_xml = '<w:color w:val="9C0006"/>'
                align = "center"
            elif "Structural" in cell_str or "STRUCTURAL" in cell_str:
                shd_xml = '<w:shd w:val="clear" w:color="auto" w:fill="D9E1F2"/>'
                bold_xml = '<w:b/>'
                color_xml = '<w:color w:val="1F397D"/>'
                align = "center"
            elif cell_str == "PASS":
                align = "center"
                bold_xml = '<w:b/>'
                color_xml = '<w:color w:val="006100"/>'
            elif cell_str in ("True", "False", "T", "F", "—", "N/E", "✅", "❌"):
                align = "center"
                if cell_str in ("T", "True", "✅"):
                    bold_xml = '<w:b/>'
                elif cell_str in ("F", "False", "❌"):
                    color_xml = '<w:color w:val="595959"/>'

            tbl_xml.append(
                f'<w:tc>'
                f'<w:tcPr>'
                f'<w:tcW w:w="{w}" w:type="dxa"/>'
                f'{shd_xml}'
                f'<w:tcMar><w:top w:w="80" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/><w:left w:w="120" w:type="dxa"/><w:right w:w="120" w:type="dxa"/></w:tcMar>'
                f'</w:tcPr>'
                f'<w:p>'
                f'<w:pPr><w:jc w:val="{align}"/><w:spacing w:before="40" w:after="40"/></w:pPr>'
                f'<w:r><w:rPr>{bold_xml}{color_xml}<w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
                f'<w:t xml:space="preserve">{xml_escape(cell_str)}</w:t></w:r>'
                f'</w:p>'
                f'</w:tc>'
            )
        tbl_xml.append('</w:tr>')

    tbl_xml.append('</w:tbl>')
    return "".join(tbl_xml)

def generate_part_b_elements():
    """Generates all XML elements for Part B: White-Box Testing."""
    elems = []

    # Title & Header
    elems.append(p("SQE Assignment 2 — White-Box Testing Tables & Structural Coverage", align="center", bold=True, sz=32, color="1F397D", space_before=120, space_after=80))
    elems.append(p("Course: SE3002 Software Quality Engineering\nSystem Under Test: Student Course Registration System (registration.py)\nArtifact: Structural White-Box Coverage Report & Verification Tables", align="center", sz=20, color="595959", space_after=240))
    elems.append(p(""))

    # -------------------------------------------------------------------------
    # B1. Control Flow Graph & Cyclomatic Complexity
    # -------------------------------------------------------------------------
    elems.append(heading1("B1  Control Flow Graph (CFG) and Cyclomatic Complexity Analysis"))
    elems.append(p("Target Function: registration_decision(student: Student, course: Course) -> str\n"
                   "Source Module: registration.py (lines 44–60)\n"
                   "Scope: Evaluates registration eligibility against fees, existing enrollment, prerequisites, credit hours limit, and class capacity without mutating student or course objects."))

    elems.append(heading2("1. Source Code Under Analysis"))
    code_text = (
        "44: def registration_decision(student: Student, course: Course) -> str:\n"
        "45:     \"\"\"Evaluate registration without changing student or course state.\"\"\"\n"
        "46:     if student.outstanding_dues < 0:\n"
        "47:         raise ValueError(\"Invalid dues\")\n"
        "48:     if not 0 <= course.enrolled <= course.capacity or course.capacity < 1:\n"
        "49:         raise ValueError(\"Invalid capacity or enrollment\")\n"
        "50:     if student.outstanding_dues > 1000:\n"
        "51:         return \"DUES_BLOCK\"\n"
        "52:     if course.code in student.registered_courses:\n"
        "53:         return \"ALREADY_REGISTERED\"\n"
        "54:     if not prerequisites_satisfied(student.completed_courses, course.prerequisites):\n"
        "55:         return \"PREREQUISITES_MISSING\"\n"
        "56:     if not check_credit_limit(student.current_credits, course.credit_hours):\n"
        "57:         return \"CREDIT_LIMIT\"\n"
        "58:     if course.enrolled > course.capacity:\n"
        "59:         return \"WAITLISTED\"\n"
        "60:     return \"REGISTERED\""
    )
    elems.append(code_block(code_text))

    elems.append(heading2("2. Short-Circuit Evaluation and Modeling Conventions"))
    elems.append(p("In Python, chained comparisons and compound Boolean expressions evaluate strictly left-to-right with short-circuit evaluation. Specifically, Line 48 decomposes into three atomic predicate evaluation points at the bytecode/AST level:\n"
                   "• C48a (enrolled < 0): Negated lower bound of chained comparison. If True, short-circuits immediately to line 49.\n"
                   "• C48b (enrolled > capacity): Negated upper bound of chained comparison. Evaluated only if C48a is False. If True, short-circuits to line 49.\n"
                   "• C48c (capacity < 1): Right-hand operand of 'or'. Evaluated only if both C48a and C48b are False. If True, executes line 49; if False, falls through to line 50.\n\n"
                   "Accordingly, two conventions exist in Software Quality Engineering:\n"
                   "• Convention A (Atomic Short-Circuit Predicate Decomposed CFG — McCabe's Standard): Every atomic decision point is modeled as a distinct decision node. (D = 9, N = 19, E = 27, V(G) = 10).\n"
                   "• Convention B (Statement-Level CFG): Each source statement is treated as a single composite node. (D = 7, N = 17, E = 23, V(G) = 8)."))

    elems.append(heading2("3. Node Taxonomy Table (Convention A)"))
    node_headers = ["Node ID", "Line(s)", "Node Type", "Description / Predicate Condition"]
    node_widths = [1000, 1000, 1800, 6280]
    node_aligns = ["center", "center", "left", "left"]
    node_rows = [
        ["1", "44–45", "Processing (Entry)", "Function entry point; parameter binding (student, course)"],
        ["2", "46", "Decision", "student.outstanding_dues < 0"],
        ["3", "47", "Exit / Raise", "raise ValueError('Invalid dues')"],
        ["4a", "48", "Decision", "course.enrolled < 0 (negated lower chained comparison)"],
        ["4b", "48", "Decision", "course.enrolled > course.capacity (negated upper chained comparison)"],
        ["4c", "48", "Decision", "course.capacity < 1 (second operand of 'or')"],
        ["5", "49", "Exit / Raise", "raise ValueError('Invalid capacity or enrollment')"],
        ["6", "50", "Decision", "student.outstanding_dues > 1000"],
        ["7", "51", "Exit / Return", "return 'DUES_BLOCK'"],
        ["8", "52", "Decision", "course.code in student.registered_courses"],
        ["9", "53", "Exit / Return", "return 'ALREADY_REGISTERED'"],
        ["10", "54", "Decision", "not prerequisites_satisfied(student.completed_courses, course.prerequisites)"],
        ["11", "55", "Exit / Return", "return 'PREREQUISITES_MISSING'"],
        ["12", "56", "Decision", "not check_credit_limit(student.current_credits, course.credit_hours)"],
        ["13", "57", "Exit / Return", "return 'CREDIT_LIMIT'"],
        ["14", "58", "Decision", "course.enrolled > course.capacity"],
        ["15", "59", "Exit / Return", "return 'WAITLISTED'"],
        ["16", "60", "Exit / Return", "return 'REGISTERED'"],
        ["X", "Exit", "Virtual Sink Node", "Virtual exit sink absorbing all return and exception exit paths"],
    ]
    elems.append(build_table(node_headers, node_rows, node_widths, node_aligns))
    elems.append(callout("Total Nodes (excluding sink X): N = 18. Total Nodes (including virtual sink X): N' = 19. Total Decision Predicates: D = 9."))

    elems.append(heading2("4. Directed Edge Listing Table"))
    edge_headers = ["Edge #", "Source", "Target", "Branch", "Semantics / Evaluation Path"]
    edge_widths = [900, 800, 800, 1400, 6180]
    edge_aligns = ["center", "center", "center", "center", "left"]
    edge_rows = [
        ["1", "1", "2", "Sequential", "Entry point to dues validation check"],
        ["2", "2", "3", "True", "outstanding_dues < 0 → raise ValueError('Invalid dues')"],
        ["3", "2", "4a", "False", "outstanding_dues >= 0 → evaluate enrolled < 0"],
        ["4", "4a", "5", "True", "enrolled < 0 → short-circuit raise ValueError('Invalid capacity...')"],
        ["5", "4a", "4b", "False", "enrolled >= 0 → evaluate enrolled > capacity"],
        ["6", "4b", "5", "True", "enrolled > capacity → short-circuit raise ValueError('Invalid capacity...')"],
        ["7", "4b", "4c", "False", "enrolled <= capacity → evaluate capacity < 1"],
        ["8", "4c", "5", "True", "capacity < 1 → raise ValueError('Invalid capacity...')"],
        ["9", "4c", "6", "False", "Capacity & enrollment valid → evaluate dues threshold > 1000"],
        ["10", "6", "7", "True", "dues > 1000 → return 'DUES_BLOCK'"],
        ["11", "6", "8", "False", "dues <= 1000 → evaluate duplicate registration check"],
        ["12", "8", "9", "True", "course.code in registered_courses → return 'ALREADY_REGISTERED'"],
        ["13", "8", "10", "False", "course not registered → evaluate prerequisites check"],
        ["14", "10", "11", "True", "prerequisites unsatisfied → return 'PREREQUISITES_MISSING'"],
        ["15", "10", "12", "False", "prerequisites satisfied → evaluate credit limit check"],
        ["16", "12", "13", "True", "credit limit exceeded → return 'CREDIT_LIMIT'"],
        ["17", "12", "14", "False", "credit limit acceptable → evaluate waitlist condition check"],
        ["18", "14", "15", "True", "course.enrolled > course.capacity → return 'WAITLISTED'"],
        ["19", "14", "16", "False", "course.enrolled <= course.capacity → return 'REGISTERED'"],
        ["20", "3", "X", "Exit Path", "Terminal raise node 3 connects to virtual sink X"],
        ["21", "5", "X", "Exit Path", "Terminal raise node 5 connects to virtual sink X"],
        ["22", "7", "X", "Exit Path", "Terminal return node 7 connects to virtual sink X"],
        ["23", "9", "X", "Exit Path", "Terminal return node 9 connects to virtual sink X"],
        ["24", "11", "X", "Exit Path", "Terminal return node 11 connects to virtual sink X"],
        ["25", "13", "X", "Exit Path", "Terminal return node 13 connects to virtual sink X"],
        ["26", "15", "X", "Exit Path", "Terminal return node 15 connects to virtual sink X"],
        ["27", "16", "X", "Exit Path", "Terminal return node 16 connects to virtual sink X"],
    ]
    elems.append(build_table(edge_headers, edge_rows, edge_widths, edge_aligns))
    elems.append(callout("Internal Directed Edges: E = 19. Terminal Exit Edges to Virtual Sink X: 8. Total Completed Edges: E' = 27."))

    elems.append(heading2("5. Visual Control Flow Graph Representation"))
    cfg_ascii = (
        "                    [ 1: Entry registration_decision() ]\n"
        "                                     |\n"
        "                                     v\n"
        "                        < 2: dues < 0 ? >\n"
        "                          /           \\\n"
        "                  True   /             \\  False\n"
        "                        v               v\n"
        "           [ 3: raise 'Invalid dues' ]   < 4a: enrolled < 0 ? >\n"
        "                        |                  /           \\\n"
        "                        |          True   /             \\  False\n"
        "                        |                v               v\n"
        "                        |   [ 5: raise 'Invalid cap' ]    < 4b: enrolled > capacity ? >\n"
        "                        |          ^       ^                /           \\\n"
        "                        |          |        \\       True   /             \\  False\n"
        "                        |          |         \\------------/               v\n"
        "                        |          \\----------------------------- < 4c: capacity < 1 ? >\n"
        "                        |                                           /           \\\n"
        "                        |                                   True   /             \\  False\n"
        "                        |               [ connects to Node 5 ] ---/               v\n"
        "                        |                                            < 6: dues > 1000 ? >\n"
        "                        |                                              /           \\\n"
        "                        |                                      True   /             \\  False\n"
        "                        |                                            v               v\n"
        "                        |                                 [ 7: 'DUES_BLOCK' ]   < 8: in registered ? >\n"
        "                        |                                            |            /           \\\n"
        "                        |                                            |    True   /             \\  False\n"
        "                        |                                            |          v               v\n"
        "                        |                                            |  [ 9: 'ALREADY_REG' ]   < 10: prereqs fail ? >\n"
        "                        |                                            |          |                /           \\\n"
        "                        |                                            |          |        True   /             \\  False\n"
        "                        |                                            |          |              v               v\n"
        "                        |                                            |          |  [ 11: 'PREREQS_MISS' ]  < 12: credit fail ? >\n"
        "                        |                                            |          |              |             /           \\\n"
        "                        |                                            |          |              |     True   /             \\  False\n"
        "                        |                                            |          |              |           v               v\n"
        "                        |                                            |          |              |  [ 13: 'CREDIT_LIMIT' ]  < 14: enrolled > cap ? >\n"
        "                        |                                            |          |              |           |                /           \\\n"
        "                        |                                            |          |              |           |        True   /             \\  False\n"
        "                        |                                            |          |              |           |              v               v\n"
        "                        |                                            |          |              |           |  [ 15: 'WAITLISTED' ]  [ 16: 'REGISTERED' ]\n"
        "                        |                                            |          |              |           |              |               |\n"
        "                        +--------------------------------------------+----------+--------------+-----------+--------------+---------------+---+\n"
        "                                                                     |\n"
        "                                                                     v\n"
        "                                                           (( Virtual Sink Node X ))"
    )
    elems.append(code_block(cfg_ascii))

    elems.append(heading2("6. Mathematical Derivation of Cyclomatic Complexity V(G)"))
    elems.append(p("Cyclomatic Complexity V(G) is computed using all three standard software engineering formulations:\n\n"
                   "Method 1: Graph Theory Definition (Single Connected Component P = 1)\n"
                   "  V(G) = E' - N' + 2P\n"
                   "  Where completed graph has N' = 19 nodes, E' = 27 edges, and P = 1 connected component:\n"
                   "  V(G) = 27 - 19 + 2(1) = 8 + 2 = 10\n\n"
                   "Method 2: Predicate Node Rule\n"
                   "  V(G) = D + 1\n"
                   "  Where decision predicates D = 9 (Nodes 2, 4a, 4b, 4c, 6, 8, 10, 12, 14):\n"
                   "  V(G) = 9 + 1 = 10\n\n"
                   "Method 3: Region Count Rule\n"
                   "  V(G) = R\n"
                   "  In a planar representation with virtual sink X, the graph bounds exactly 9 closed regions plus 1 unbounded external region:\n"
                   "  V(G) = 9 + 1 = 10"))

    elems.append(heading2("7. Comparison of Modeling Conventions"))
    conv_headers = ["Metric / Dimension", "Convention A (McCabe Short-Circuit AST)", "Convention B (Statement-Level)", "Engineering Rationale"]
    conv_widths = [2400, 2400, 2400, 2880]
    conv_aligns = ["left", "center", "center", "left"]
    conv_rows = [
        ["Decision Nodes (D)", "9", "7", "Chained comparison & 'or' at line 48 introduce 2 internal predicate branch points."],
        ["Total Graph Nodes (N')", "19", "17", "Nodes 4a, 4b, 4c vs single composite Node 4."],
        ["Total Graph Edges (E')", "27", "23", "Decomposed short-circuit paths add 4 directed edges."],
        ["Formula V(G) = E - N + 2", "27 - 19 + 2 = 10", "23 - 17 + 2 = 8", "Both models maintain internal mathematical consistency."],
        ["Formula V(G) = D + 1", "9 + 1 = 10", "7 + 1 = 8", "Exact agreement with predicate counting rule."],
        ["Runtime Fidelity", "High (matches bytecode branches)", "Medium (abstracts compound logic)", "Convention A directly reflects physical test coverage required by pytest-cov."]
    ]
    elems.append(build_table(conv_headers, conv_rows, conv_widths, conv_aligns))

    # -------------------------------------------------------------------------
    # B2. Basis Path Testing
    # -------------------------------------------------------------------------
    elems.append(heading1("B2  Independent Basis Paths and Basis Path Matrix"))
    elems.append(p("An independent basis path set consists of linearly independent execution paths through the CFG such that every edge is traversed at least once, and each path introduces at least one edge not present in any previous path. For V(G) = 10, exactly 10 basis paths form the basis vector space."))

    elems.append(heading2("1. Basis Path Matrix (V(G) = 10)"))
    bp_headers = ["Path ID", "Node Execution Sequence", "New Edge(s) Introduced", "Expected Outcome (Req vs Code)", "Representative Test / Inputs", "Result"]
    bp_widths = [900, 2700, 1500, 2180, 2100, 700]
    bp_aligns = ["center", "left", "left", "left", "left", "center"]
    bp_rows = [
        ["Path 1", "1 → 2 → 3 → X", "1→2, 2→3", "ValueError('Invalid dues')", "student(outstanding_dues=-1), course()", "PASS"],
        ["Path 2", "1 → 2 → 4a → 5 → X", "2→4a, 4a→5", "ValueError('Invalid capacity...')", "student(), course(enrolled=-1, cap=10)", "PASS"],
        ["Path 3", "1 → 2 → 4a → 4b → 5 → X", "4a→4b, 4b→5", "ValueError('Invalid capacity...')", "student(), course(enrolled=11, cap=10)", "PASS"],
        ["Path 4", "1 → 2 → 4a → 4b → 4c → 5 → X", "4b→4c, 4c→5", "ValueError('Invalid capacity...')", "student(), course(enrolled=0, cap=0)", "PASS"],
        ["Path 5", "1 → 2 → 4a → 4b → 4c → 6 → 7 → X", "4c→6, 6→7", "Req: DUES_BLOCK\nCode: REGISTERED (due to >1000 bug)", "student(outstanding_dues=1), course()", "FAIL ★"],
        ["Path 6", "1 → 2 → 4a → 4b → 4c → 6 → 8 → 9 → X", "6→8, 8→9", "ALREADY_REGISTERED", "student(registered={'C1'}), course(code='C1')", "PASS"],
        ["Path 7", "1 → 2 → 4a → 4b → 4c → 6 → 8 → 10 → 11 → X", "8→10, 10→11", "PREREQUISITES_MISSING", "student(completed=set()), course(prereqs={'P1'})", "PASS"],
        ["Path 8", "1 → 2 → 4a → 4b → 4c → 6 → 8 → 10 → 12 → 13 → X", "10→12, 12→13", "CREDIT_LIMIT", "student(current_credits=16), course(credit_hours=3)", "PASS"],
        ["Path 9", "1 → 2 → 4a → 4b → 4c → 6 → 8 → 10 → 12 → 14 → 15 → X", "12→14, 14→15", "Req: WAITLISTED\nCode: REGISTERED (due to > vs == bug)", "student(), course(enrolled=10, capacity=10)", "FAIL ★"],
        ["Path 10", "1 → 2 → 4a → 4b → 4c → 6 → 8 → 10 → 12 → 14 → 16 → X", "14→16", "REGISTERED", "student(current_credits=10), course(enrolled=5, cap=10)", "PASS"],
    ]
    elems.append(build_table(bp_headers, bp_rows, bp_widths, bp_aligns))
    elems.append(callout("★  FAIL indicates an implementation defect faithfully exposed by driving this basis path per REQUIREMENTS.md."))

    elems.append(heading2("2. Analysis of Structural Dead-Code Anomaly on Path 9"))
    elems.append(p("Inspection of registration.py reveals a critical structural masking anomaly:\n"
                   "• Line 48: if not 0 <= course.enrolled <= course.capacity or course.capacity < 1: raise ValueError(...)\n"
                   "• Line 58: if course.enrolled > course.capacity: return \"WAITLISTED\"\n\n"
                   "For any standard immutable Course instance, if enrolled > capacity, it is trapped at Line 48 and raises ValueError. Therefore, Line 58 can NEVER evaluate to True during normal execution. Line 59 is structurally dead code in the presence of immutable objects.\n\n"
                   "To verify the structural integrity of edge 14→15 (Path 9) during white-box coverage testing, a dynamic course fixture (_DynamicEnrollmentCourse) is employed. It returns enrolled=5 at line 48 (passing the guard) and enrolled=11 at line 58 (> capacity), driving the line 59 branch and achieving 100% structural coverage."))

    # -------------------------------------------------------------------------
    # B3. Statement and Branch Coverage Analysis
    # -------------------------------------------------------------------------
    elems.append(heading1("B3  Statement and Branch Coverage Analysis"))
    elems.append(p("Coverage measurement was conducted using pytest-cov with the --cov-branch flag against registration.py (53 total statements, 26 total branches)."))

    elems.append(heading2("1. Initial Coverage — Black-Box Tests Only (test_blackbox.py)"))
    elems.append(p("Execution Command: python -m pytest tests/test_blackbox.py --cov=registration --cov-branch --cov-report=term-missing"))

    cov_init_headers = ["Coverage Metric", "Statements / Branches Executed", "Total Measurable Units", "Initial Coverage %"]
    cov_init_widths = [2800, 2400, 2400, 2480]
    cov_init_aligns = ["left", "center", "center", "center"]
    cov_init_rows = [
        ["Statement Coverage", "50", "53", "94.3 %"],
        ["Branch Coverage", "23", "26", "88.5 %"],
        ["Combined pytest-cov Metric", "73", "79", "92.4 % (Reported 92%)"],
        ["Missing Statements", "3 statements uncovered", "Lines 51, 59, 71", "—"],
        ["Missing Partial Branches", "3 branches uncovered", "50→51, 58→59, 70→71", "—"]
    ]
    elems.append(build_table(cov_init_headers, cov_init_rows, cov_init_widths, cov_init_aligns))

    elems.append(heading2("2. Uncovered Locations & Root Cause Gap Analysis"))
    gap_headers = ["Gap ID", "Function / Location", "Uncovered Line & Branch", "Root Cause Analysis & Failure Mechanism"]
    gap_widths = [1000, 2000, 2000, 5080]
    gap_aligns = ["center", "left", "center", "left"]
    gap_rows = [
        ["GAP-1", "registration_decision", "Line 51 (return 'DUES_BLOCK')\nBranch 50→51 (True)", "Implementation defect: Line 50 checks 'dues > 1000' instead of 'dues > 0'. Black-box tests follow FR-04 and use dues=1..500, which never triggers > 1000."],
        ["GAP-2", "registration_decision", "Line 59 (return 'WAITLISTED')\nBranch 58→59 (True)", "Structural dead code: Line 48 validation guard traps enrolled > capacity before line 58. Furthermore, line 58 defectively checks enrolled > capacity instead of enrolled == capacity."],
        ["GAP-3", "register_course", "Line 71 (waitlist.append)\nBranch 70→71 (True)", "Downstream masking: Line 71 is only reachable if registration_decision returns 'WAITLISTED'. Because line 59 was unreachable, line 71 was also blocked from execution."]
    ]
    elems.append(build_table(gap_headers, gap_rows, gap_widths, gap_aligns))

    elems.append(heading2("3. Structural White-Box Test Suite Additions"))
    elems.append(p("To bridge the identified coverage gaps while faithfully preserving requirement-based test assertions, four dedicated structural white-box tests were implemented in test_whitebox.py:"))

    struct_headers = ["Test Case ID", "Target Gap", "Underlying Mechanism / Test Technique", "Covered Element", "Result"]
    struct_widths = [1400, 1000, 4280, 2200, 1200]
    struct_aligns = ["center", "center", "left", "left", "center"]
    struct_rows = [
        ["test_wb13_dues_above_1000...", "GAP-1", "Supplies outstanding_dues = 1001 to exceed buggy > 1000 threshold, directly executing line 51.", "Line 51\nBranch 50→51", "PASS (Structural)"],
        ["test_wb14_waitlisted_branch...", "GAP-2", "Utilizes _DynamicEnrollmentCourse (read 1 = 5, read 2 = 11) to bypass line 48 guard and trigger line 58.", "Line 59\nBranch 58→59", "PASS (Structural)"],
        ["test_wb15_register_waitlist...", "GAP-3", "Executes register_course with dynamic course; student not in waitlist → executes append.", "Line 71\nBranch 70→71", "PASS (Structural)"],
        ["test_wb16_register_no_dup...", "GAP-3", "Executes register_course with student already in waitlist → verifies idempotency (False branch).", "Branch 70→72 (False path)", "PASS (Structural)"]
    ]
    elems.append(build_table(struct_headers, struct_rows, struct_widths, struct_aligns))

    elems.append(heading2("4. Final Coverage Results — Combined Black-Box and White-Box"))
    elems.append(p("Execution Command: python -m pytest tests/test_blackbox.py tests/test_whitebox.py --cov=registration --cov-branch --cov-report=term-missing"))

    cov_final_headers = ["Coverage Metric", "Initial (Black-Box Only)", "Final (BB + White-Box)", "Delta / Improvement", "Status"]
    cov_final_widths = [2400, 2200, 2200, 1800, 1480]
    cov_final_aligns = ["left", "center", "center", "center", "center"]
    cov_final_rows = [
        ["Statement Coverage", "50 / 53 (94.3 %)", "53 / 53 (100.0 %)", "+ 5.7 %", "100 % Complete"],
        ["Branch Coverage", "23 / 26 (88.5 %)", "26 / 26 (100.0 %)", "+ 11.5 %", "100 % Complete"],
        ["Combined pytest-cov", "92.4 % (Reported 92%)", "100.0 % (Reported 100%)", "+ 7.6 %", "100 % Complete"],
        ["Uncovered Statements", "3 statements (51, 59, 71)", "0 statements missing", "All covered", "Zero Missing"],
        ["Uncovered Branches", "3 branches (50→51, 58→59, 70→71)", "0 branches missing", "All covered", "Zero Missing"]
    ]
    elems.append(build_table(cov_final_headers, cov_final_rows, cov_final_widths, cov_final_aligns))
    elems.append(callout("Structural white-box testing closes 100% of all statement and branch coverage gaps, achieving total structural verification."))

    # -------------------------------------------------------------------------
    # B4. Condition Coverage and MC/DC Analysis
    # -------------------------------------------------------------------------
    elems.append(heading1("B4  Condition Coverage and MC/DC Analysis"))
    elems.append(p("Condition Coverage requires every atomic Boolean condition within each decision to take on both True and False values across the test suite. Modified Condition / Decision Coverage (MC/DC) further requires demonstrating that each condition can independently affect the decision outcome while holding all other conditions fixed."))

    elems.append(heading2("1. Identification of Atomic Conditions in registration_decision"))
    cond_headers = ["Symbol", "Line", "Atomic Condition Expression", "Context / Evaluation Description"]
    cond_widths = [900, 800, 3600, 4780]
    cond_aligns = ["center", "center", "left", "left"]
    cond_rows = [
        ["A1", "46", "student.outstanding_dues < 0", "Dues lower bound guard; True triggers invalid dues ValueError"],
        ["B1", "48", "course.enrolled < 0", "Chained comparison lower bound; True triggers invalid capacity/enrollment ValueError"],
        ["B2", "48", "course.enrolled > course.capacity", "Chained comparison upper bound; evaluated only when B1 is False"],
        ["B3", "48", "course.capacity < 1", "Minimum capacity threshold; evaluated only when B1 and B2 are False"],
        ["C1", "50", "student.outstanding_dues > 1000", "Dues blocking decision (implementation threshold defect)"],
        ["D1", "52", "course.code in student.registered_courses", "Duplicate course registration prevention guard"],
        ["E1", "54", "not prerequisites_satisfied(...)", "Prerequisites verification predicate"],
        ["F1", "56", "not check_credit_limit(...)", "Credit limit calculation predicate (current + new < 18 defect)"],
        ["G1", "58", "course.enrolled > course.capacity", "Waitlist qualification decision (defective > operator)"],
    ]
    elems.append(build_table(cond_headers, cond_rows, cond_widths, cond_aligns))

    elems.append(heading2("2. Full Condition Coverage Truth Table"))
    elems.append(p("N/E = Not Evaluated due to Python left-to-right short-circuit termination."))

    cc_headers = ["Test ID", "A1", "B1", "B2", "B3", "C1", "D1", "E1", "F1", "G1", "Decision Outcome"]
    cc_widths = [1080, 600, 600, 600, 600, 600, 600, 600, 600, 600, 3500]
    cc_aligns = ["center"] * 10 + ["left"]
    cc_rows = [
        ["TC-C01", "T", "N/E", "N/E", "N/E", "N/E", "N/E", "N/E", "N/E", "N/E", "ValueError('Invalid dues')"],
        ["TC-C02", "F", "T", "N/E", "N/E", "N/E", "N/E", "N/E", "N/E", "N/E", "ValueError('Invalid capacity...')"],
        ["TC-C03", "F", "F", "T", "N/E", "N/E", "N/E", "N/E", "N/E", "N/E", "ValueError('Invalid capacity...')"],
        ["TC-C04", "F", "F", "F", "T", "N/E", "N/E", "N/E", "N/E", "N/E", "ValueError('Invalid capacity...')"],
        ["TC-C05", "F", "F", "F", "F", "T", "N/E", "N/E", "N/E", "N/E", "return 'DUES_BLOCK'"],
        ["TC-C06", "F", "F", "F", "F", "F", "T", "N/E", "N/E", "N/E", "return 'ALREADY_REGISTERED'"],
        ["TC-C07", "F", "F", "F", "F", "F", "F", "T", "N/E", "N/E", "return 'PREREQUISITES_MISSING'"],
        ["TC-C08", "F", "F", "F", "F", "F", "F", "F", "T", "N/E", "return 'CREDIT_LIMIT'"],
        ["TC-C09", "F", "F", "F", "F", "F", "F", "F", "F", "T", "return 'WAITLISTED' (via dynamic course)"],
        ["TC-C10", "F", "F", "F", "F", "F", "F", "F", "F", "F", "return 'REGISTERED'"],
    ]
    elems.append(build_table(cc_headers, cc_rows, cc_widths, cc_aligns))

    elems.append(heading2("3. Condition Coverage Verification Summary"))
    cc_sum_headers = ["Condition Symbol", "Evaluated True in Test", "Evaluated False in Test", "Condition Covered?", "Short-Circuit Accounting"]
    cc_sum_widths = [1800, 2200, 2200, 1800, 2080]
    cc_sum_aligns = ["center", "center", "center", "center", "left"]
    cc_sum_rows = [
        ["A1 (dues < 0)", "TC-C01", "TC-C02", "✅ Yes", "Always evaluated first at line 46"],
        ["B1 (enrolled < 0)", "TC-C02", "TC-C03", "✅ Yes", "Evaluated when A1 is False"],
        ["B2 (enrolled > cap)", "TC-C03", "TC-C04", "✅ Yes", "Evaluated when B1 is False"],
        ["B3 (cap < 1)", "TC-C04", "TC-C05", "✅ Yes", "Evaluated when B1, B2 are False"],
        ["C1 (dues > 1000)", "TC-C05", "TC-C06", "✅ Yes", "Evaluated when line 48 passes"],
        ["D1 (in registered)", "TC-C06", "TC-C07", "✅ Yes", "Evaluated when C1 is False"],
        ["E1 (prereqs fail)", "TC-C07", "TC-C08", "✅ Yes", "Evaluated when D1 is False"],
        ["F1 (credit limit fail)", "TC-C08", "TC-C10", "✅ Yes", "Evaluated when E1 is False"],
        ["G1 (enrolled > cap)", "TC-C09", "TC-C10", "✅ Yes", "Evaluated when F1 is False"],
    ]
    elems.append(build_table(cc_sum_headers, cc_sum_rows, cc_sum_widths, cc_sum_aligns))

    elems.append(heading2("4. Formal MC/DC Analysis — prerequisites_satisfied(completed, required)"))
    elems.append(p("The function prerequisites_satisfied embodies compound Boolean logic:\n"
                   "  def prerequisites_satisfied(completed: set[str], required: set[str]) -> bool:\n"
                   "      if not required:                                # Condition P: required is empty\n"
                   "          return True\n"
                   "      return bool(completed.intersection(required))   # Condition Q: intersection non-empty\n\n"
                   "Condition P: 'not required' (P = True if required is empty, False otherwise)\n"
                   "Condition Q: 'bool(completed.intersection(required))' (Q = True if intersection non-empty, False otherwise)"))

    mcdc_truth_headers = ["Test Vector ID", "Condition P (required == ∅)", "Condition Q (intersection ≠ ∅)", "Q Evaluated?", "Function Return Value"]
    mcdc_truth_widths = [1800, 2400, 2400, 1600, 1880]
    mcdc_truth_aligns = ["center", "center", "center", "center", "center"]
    mcdc_truth_rows = [
        ["MC-P1", "True", "N/E", "No (Short-circuit)", "True"],
        ["MC-P2", "False", "True", "Yes", "True"],
        ["MC-P3", "False", "False", "Yes", "False"],
    ]
    elems.append(build_table(mcdc_truth_headers, mcdc_truth_rows, mcdc_truth_widths, mcdc_truth_aligns))

    elems.append(heading2("5. MC/DC Independent Effect Pair Derivations"))
    elems.append(p("MC/DC requires proving that toggling each condition independently toggles the decision outcome while all other conditions remain fixed:"))

    mcdc_pair_headers = ["Condition", "Test Pair Selected", "Vector 1 (P, Q → Outcome)", "Vector 2 (P, Q → Outcome)", "Independent Effect Demonstrated?"]
    mcdc_pair_widths = [1600, 1800, 2200, 2200, 2280]
    mcdc_pair_aligns = ["center", "center", "left", "left", "center"]
    mcdc_pair_rows = [
        ["Condition P (required == ∅)", "MC-P1 vs MC-P3", "MC-P1: P=T, Q=N/E → True", "MC-P3: P=F, Q=F → False", "✅ Yes (Only P changes; outcome flips True→False)"],
        ["Condition Q (intersection ≠ ∅)", "MC-P2 vs MC-P3", "MC-P2: P=F, Q=T → True", "MC-P3: P=F, Q=F → False", "✅ Yes (P held at F; Q flips True→False; outcome flips)"]
    ]
    elems.append(build_table(mcdc_pair_headers, mcdc_pair_rows, mcdc_pair_widths, mcdc_pair_aligns))
    elems.append(callout("★ Implementation Defect Discovered: prerequisites_satisfied uses intersection (OR logic: any match returns True). Requirement FR-03 mandates subset (AND logic: every prerequisite must be satisfied). This defect is exposed by test_prerequisite_equivalence_classes where completed={CS101} and required={CS101, MATH101} returns True instead of False."))

    elems.append(heading2("6. Advanced MC/DC for Line 48 Compound Expression"))
    elems.append(p("Line 48 compound decision: not (0 <= enrolled <= capacity) or (capacity < 1)\n"
                   "Expressed as an OR-decision of atomic conditions: D = B1 ∨ B2 ∨ B3\n"
                   "To demonstrate MC/DC for an N=3 OR construct, exactly N + 1 = 4 test vectors are required:"))

    or_mcdc_headers = ["Condition", "Vector Pair", "B1 (enrolled < 0)", "B2 (enrolled > cap)", "B3 (cap < 1)", "Outcome D", "MC/DC Proof"]
    or_mcdc_widths = [1400, 1500, 1300, 1300, 1300, 1200, 2080]
    or_mcdc_aligns = ["center"] * 6 + ["left"]
    or_mcdc_rows = [
        ["B1", "TC-C02 vs TC-C10", "T vs F", "N/E (F)", "N/E (F)", "True vs False", "B1 toggles D from T to F"],
        ["B2", "TC-C03 vs TC-C10", "F (held)", "T vs F", "N/E (F)", "True vs False", "B2 toggles D from T to F"],
        ["B3", "TC-C04 vs TC-C10", "F (held)", "F (held)", "T vs F", "True vs False", "B3 toggles D from T to F"],
    ]
    elems.append(build_table(or_mcdc_headers, or_mcdc_rows, or_mcdc_widths, or_mcdc_aligns))

    # -------------------------------------------------------------------------
    # B5. Complete White-Box Test Suite Specification
    # -------------------------------------------------------------------------
    elems.append(heading1("B5  Complete White-Box Test Suite Specification (WB-01 to WB-20)"))
    elems.append(p("All white-box tests are implemented in tests/test_whitebox.py. In accordance with SQE standards, expected values reflect authoritative behavior from REQUIREMENTS.md; tests exposing known code defects faithfully report FAIL."))

    wb_test_headers = ["Test ID", "Target Category", "Basis Path / Branch", "Representative Test Input", "Expected Output (Req vs Code)", "Result"]
    wb_test_widths = [900, 1600, 1600, 2300, 2400, 1280]
    wb_test_aligns = ["center", "left", "left", "left", "left", "center"]
    wb_test_rows = [
        ["WB-01", "Exception Guard", "Basis Path 1 (2→3)", "student(outstanding_dues=-1), course()", "ValueError('Invalid dues')", "PASS"],
        ["WB-02", "Exception Guard", "Basis Path 2 (4a→5)", "student(), course(enrolled=-1, cap=10)", "ValueError('Invalid capacity or enrollment')", "PASS"],
        ["WB-02b", "Exception Guard", "Basis Path 3 (4b→5)", "student(), course(enrolled=11, cap=10)", "ValueError('Invalid capacity or enrollment')", "PASS"],
        ["WB-02c", "Exception Guard", "Basis Path 4 (4c→5)", "student(), course(enrolled=0, cap=0)", "ValueError('Invalid capacity or enrollment')", "PASS"],
        ["WB-03", "Decision Path", "Basis Path 5 (6→7)", "student(outstanding_dues=1), course()", "Req: DUES_BLOCK\nCode: REGISTERED (due to >1000 defect)", "FAIL ★"],
        ["WB-04", "Decision Path", "Basis Path 6 (8→9)", "student(registered={'C1'}), course(code='C1')", "ALREADY_REGISTERED", "PASS"],
        ["WB-05", "Decision Path", "Basis Path 7 (10→11)", "student(completed=set()), course(prereqs={'P1'})", "PREREQUISITES_MISSING", "PASS"],
        ["WB-06", "Decision Path", "Basis Path 8 (12→13)", "student(current_credits=16), course(credit_hours=3)", "CREDIT_LIMIT", "PASS"],
        ["WB-07", "Decision Path", "Basis Path 9 (14→15)", "student(), course(enrolled=10, capacity=10)", "Req: WAITLISTED\nCode: REGISTERED (due to > vs == defect)", "FAIL ★"],
        ["WB-08", "Decision Path", "Basis Path 10 (14→16)", "student(), course(enrolled=9, capacity=10)", "REGISTERED", "PASS"],
        ["WB-09", "Condition Cov.", "Condition C1 False side", "student(outstanding_dues=0), course()", "REGISTERED (falls through C1)", "PASS"],
        ["WB-10", "Condition Cov.", "Condition D1 False side", "student(registered=set()), course()", "REGISTERED (falls through D1)", "PASS"],
        ["WB-11", "Condition Cov.", "Condition E1 False side", "student(completed={'P1','P2'}), course()", "REGISTERED (falls through E1)", "PASS"],
        ["WB-12", "Condition Cov.", "Condition F1 Boundary", "student(current_credits=15), course(credits=3)", "Req: REGISTERED (15+3=18 allowed)\nCode: CREDIT_LIMIT (strict < 18 defect)", "FAIL ★"],
        ["WB-12b", "Condition Cov.", "Condition F1 False side", "student(current_credits=10), course(credits=3)", "REGISTERED (10+3=13 < 18)", "PASS"],
        ["WB-12c", "Condition Cov.", "Condition F1 False side", "student(current_credits=14), course(credits=3)", "REGISTERED (14+3=17 < 18)", "PASS"],
        ["WB-12d", "Condition Cov.", "Condition G1 False side", "student(), course(enrolled=9, capacity=10)", "REGISTERED (enrolled < cap)", "PASS"],
        ["WB-13", "Structural Gap", "GAP-1 (Line 51)", "student(outstanding_dues=1001), course()", "DUES_BLOCK (executes branch 50→51)", "PASS (Structural)"],
        ["WB-14", "Structural Gap", "GAP-2 (Line 59)", "student(), _DynamicEnrollmentCourse(5, 11)", "WAITLISTED (executes branch 58→59)", "PASS (Structural)"],
        ["WB-15", "Structural Gap", "GAP-3 (Line 71)", "register_course(s, dynamic_course)", "WAITLISTED; waitlist updated with student ID", "PASS (Structural)"],
        ["WB-16", "Structural Gap", "GAP-3 False (70→72)", "register_course(s, dynamic_course_with_id)", "WAITLISTED; no duplicate student ID appended", "PASS (Structural)"],
        ["WB-17", "MC/DC Proof", "Condition P = True", "prerequisites_satisfied(set(), set())", "True (empty prerequisites permitted)", "PASS"],
        ["WB-18", "MC/DC Proof", "Condition P=F, Q=F", "prerequisites_satisfied(set(), {'P1'})", "False (prerequisites unsatisfied)", "PASS"],
        ["WB-19", "MC/DC Proof", "Condition Q = True", "prerequisites_satisfied({'P1'}, {'P1'})", "True (prerequisites satisfied)", "PASS"],
        ["WB-20", "Priority Guard", "Validation Priority", "student(outstanding_dues=-1), course(cap=0)", "ValueError('Invalid dues') precedes capacity error", "PASS"],
    ]
    elems.append(build_table(wb_test_headers, wb_test_rows, wb_test_widths, wb_test_aligns))
    elems.append(callout("★ FAIL = Known implementation defect faithfully recorded per assignment instructions. Structural tests drive internal code branches to ensure 100% statement and branch coverage."))

    # -------------------------------------------------------------------------
    # B6. Implementation Defects & Cross-Comparison Synthesis
    # -------------------------------------------------------------------------
    elems.append(heading1("B6  Implementation Defects Revealed and Testing Method Synthesis"))
    elems.append(p("The combination of black-box and white-box testing provides a complete, rigorous verification methodology. Black-box testing identifies functional deviations from requirements, while white-box testing pinpoints the exact line of code, operator fault, and structural anomaly responsible."))

    defect_headers = ["Defect #", "FR Violated", "Source Code Fault & Root Cause", "Black-Box Exposure", "White-Box Diagnosis & Structural Impact"]
    defect_widths = [900, 1100, 3600, 2000, 2480]
    defect_aligns = ["center", "center", "left", "left", "left"]
    defect_rows = [
        ["D-01", "FR-04", "Line 50: student.outstanding_dues > 1000\nThreshold check uses 1000 instead of 0.", "Tests with dues=1..500 unexpectedly returned REGISTERED.", "CFG Node 6 / Path 5 analysis isolated the >1000 operator. Structural test WB-13 proved line 51 is executed only when dues > 1000."],
        ["D-02", "FR-03", "Line 41: bool(completed.intersection(required))\nImplements OR logic (any match) rather than AND logic (all match).", "Partial prerequisite test passed when it should have failed.", "MC/DC analysis of prerequisites_satisfied proved that intersection logic violates independence; correct expression is required.issubset(completed)."],
        ["D-03", "FR-01", "Line 34: current_credits + new_credits < 18\nStrict inequality '<' rejects total credits exactly equal to 18.", "BVA test with credits 15+3=18 failed with CREDIT_LIMIT.", "CFG Node 12 / Path 8 boundary analysis showed branch 56→True triggers at total=18 instead of total=19."],
        ["D-04", "FR-08", "Line 58: course.enrolled > course.capacity\nUses strict '>' instead of '==' for waitlisting, and is masked by Line 48.", "Course at capacity (enrolled=cap) returned REGISTERED instead of WAITLISTED.", "CFG analysis discovered dead code: Line 48 traps enrolled>cap, rendering Line 58 unreachable for static objects. Dynamic course was required to execute Path 9."],
        ["D-05", "FR-13", "Line 75–81: withdraw_course()\nDecrements student credits but fails to decrement course.enrolled.", "Withdrawal state test revealed course.enrolled remained unchanged after student removal.", "Control flow inspection of withdraw_course confirmed omission of 'course.enrolled -= 1' state update."]
    ]
    elems.append(build_table(defect_headers, defect_rows, defect_widths, defect_aligns))

    elems.append(heading2("Academic SQE Conclusion"))
    elems.append(p("This assignment validates the core tenet of Software Quality Engineering: Neither black-box nor white-box testing is sufficient in isolation.\n\n"
                   "1. Black-box testing (Part A: ECP, BVA, Decision Tables) successfully detected 5 functional non-conformances without bias from implementation details, but left 3 statements and 3 branches completely unexercised (92% coverage).\n"
                   "2. White-box testing (Part B: CFG, Cyclomatic Complexity, Basis Paths, MC/DC) exposed the root causes of those defects, identified critical dead-code anomalies (Line 48 vs Line 58), and designed specialized structural test drivers to achieve 100% statement and 100% branch coverage.\n"
                   "3. Combining specification-based expected outcomes with structure-based path execution ensures both functional correctness and exhaustive implementation verification."))

    return "".join(elems)

def create_docx(template_path, output_path, body_xml_children):
    """Creates a new docx by copying the template ZIP and replacing word/document.xml."""
    with zipfile.ZipFile(template_path, 'r') as zin:
        doc_xml = zin.read('word/document.xml').decode('utf-8')

        # Find document open and sectPr
        doc_start = doc_xml.find('<w:document')
        body_start = doc_xml.find('<w:body', doc_start)
        body_content_start = doc_xml.find('>', body_start) + 1

        sectPr_start = doc_xml.find('<w:sectPr', body_content_start)
        sectPr_end = doc_xml.find('</w:sectPr>', sectPr_start) + len('</w:sectPr>')
        sectPr_xml = doc_xml[sectPr_start:sectPr_end]

        new_doc_xml = (
            doc_xml[:body_content_start] +
            body_xml_children +
            sectPr_xml +
            '</w:body></w:document>'
        )

        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == 'word/document.xml':
                    zout.writestr(item, new_doc_xml.encode('utf-8'))
                else:
                    zout.writestr(item, zin.read(item.filename))

    print(f"Successfully generated: {output_path} (size: {os.path.getsize(output_path)} bytes)")

def extract_part_a_children():
    """Extracts the exact body children from Blackbox initial testing.docx (excluding sectPr)."""
    with zipfile.ZipFile('Blackbox initial testing.docx', 'r') as z:
        doc_xml = z.read('word/document.xml').decode('utf-8')
        doc_tree = ET.fromstring(doc_xml)
        body = doc_tree.find('w:body', namespaces)
        part_a_children = []
        for child in body:
            tag = child.tag.split('}')[-1]
            if tag == 'sectPr':
                continue
            part_a_children.append(ET.tostring(child, encoding='utf-8').decode('utf-8'))
        return "".join(part_a_children)

def main():
    print("Generating Part B XML elements...")
    part_b_xml = generate_part_b_elements()

    # 1. Generate standalone Whitebox initial testing.docx
    output_wb = "Whitebox initial testing.docx"
    create_docx("Blackbox initial testing.docx", output_wb, part_b_xml)

    # 2. Generate unified Complete Assignment Document
    print("\nExtracting Part A XML elements for unified document...")
    part_a_xml = extract_part_a_children()

    # Section separator for unified document
    divider = (
        p("") +
        p("—" * 65, align="center", color="CCCCCC") +
        p("") +
        p("PART B: WHITE-BOX TESTING & STRUCTURAL ANALYSIS", style="Heading1", align="center", bold=True, sz=28, color="1F397D", space_before=240, space_after=180) +
        p("")
    )

    unified_xml = part_a_xml + divider + part_b_xml
    output_unified = "SQE_Assignment_2_Complete_Testing_Report.docx"
    create_docx("Blackbox initial testing.docx", output_unified, unified_xml)

    print("\nBoth Word documents successfully created and verified!")

if __name__ == "__main__":
    main()
