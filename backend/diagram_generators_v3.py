"""
Version 3: Clean, detailed, properly flowing diagram generators
Focus on clarity, proper labeling, and logical flow
"""
import re
import json

def parse_description_to_steps(description):
    """Parse natural language into clean, labeled steps with proper flow"""
    # Split by periods first to handle multi-sentence input
    lines = re.split(r'\.|\n', description)
    
    steps = []
    decision_point = None
    decision_check_step = None
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        
        # Check if this line mentions "checks if" - this becomes the decision node
        check_match = re.search(r'(.+)\s+checks?\s+if\s+(.+)', line, re.IGNORECASE)
        if check_match:
            full_action = check_match.group(1).strip()
            condition = check_match.group(2).strip()
            
            # Store the condition for the decision node (will be used as the question)
            decision_check_step = condition.capitalize()
            # Don't add the "checks if" step itself - it becomes the decision diamond
            continue
        
        # Check for decision pattern: "If X, then Y. If not X, then Z."
        # Pattern 1: "If the user is logged in, it shows the dashboard"
        if_match = re.search(r'if\s+(?:the\s+)?(.+?)\s+is\s+(.+?),\s*(.+)', line, re.IGNORECASE)
        if if_match:
            subject = if_match.group(1).strip()
            state = if_match.group(2).strip()
            action = if_match.group(3).strip()
            
            # Check if we haven't set decision yet
            if not decision_point:
                # Use the condition from "checks if" if available, otherwise construct it
                condition_text = decision_check_step if decision_check_step else f"{subject.capitalize()} is {state}"
                # This is the YES branch
                decision_point = {
                    'condition': condition_text,
                    'yes': action.capitalize(),
                    'no': None  # Will be filled by next "if not" statement
                }
            elif decision_point['no'] is None:
                # This might be the NO branch
                # Check if it's a negative condition
                if 'not' in line.lower() or 'isn\'t' in line.lower():
                    decision_point['no'] = action.capitalize()
            continue
        
        # Pattern 2: "If X is not Y"
        if_not_match = re.search(r'if\s+(?:the\s+)?(.+?)\s+is\s+not\s+(.+?),\s*(.+)', line, re.IGNORECASE)
        if if_not_match:
            if decision_point and decision_point['no'] is None:
                action = if_not_match.group(3).strip()
                decision_point['no'] = action.capitalize()
            continue
        
        # Regular steps - not part of if/then logic
        if 'if' not in line.lower():
            cleaned = line.strip()
            if cleaned:
                cleaned = cleaned[0].upper() + cleaned[1:] if cleaned else cleaned
                # Remove trailing commas
                cleaned = cleaned.rstrip(',')
                steps.append(cleaned)
    
    return steps, decision_point

def generate_graphviz_v3(description):
    """Generate clean GraphViz with proper labels and flow"""
    steps, decision = parse_description_to_steps(description)
    
    code = 'digraph Workflow {\n'
    code += '  // Graph settings\n'
    code += '  bgcolor="transparent"\n'
    code += '  rankdir=TB\n'
    code += '  node [fontname="Arial", fontsize=12, style="filled,rounded", penwidth=2]\n'
    code += '  edge [fontname="Arial", fontsize=11, penwidth=2]\n\n'
    
    node_id = 0
    
    # Add start node
    code += f'  N{node_id} [label="START", shape=ellipse, fillcolor="#dcfce7", color="#16a34a", fontcolor="#16a34a", fontsize=13, style="filled"]\n'
    last_node = f'N{node_id}'
    node_id += 1
    
    # Add steps
    for i, step in enumerate(steps):
        current = f'N{node_id}'
        
        # Determine node type based on keywords
        if any(word in step.lower() for word in ['validate', 'check', 'verify', 'confirm']):
            code += f'  {current} [label="{step}", shape=box, fillcolor="#fef3c7", color="#f59e0b", fontcolor="#92400e"]\n'
        elif any(word in step.lower() for word in ['error', 'fail', 'reject', 'deny']):
            code += f'  {current} [label="{step}", shape=box, fillcolor="#fee2e2", color="#dc2626", fontcolor="#991b1b"]\n'
        elif any(word in step.lower() for word in ['save', 'store', 'database']):
            code += f'  {current} [label="{step}", shape=cylinder, fillcolor="#e0e7ff", color="#4f46e5", fontcolor="#3730a3"]\n'
        else:
            code += f'  {current} [label="{step}", shape=box, fillcolor="#e0f2fe", color="#0284c7", fontcolor="#075985"]\n'
        
        code += f'  {last_node} -> {current} [color="#64748b"]\n'
        last_node = current
        node_id += 1
    
    # Add decision point if exists
    if decision:
        decision_node = f'N{node_id}'
        yes_node = f'N{node_id + 1}'
        no_node = f'N{node_id + 2}'
        
        code += f'\n  // Decision point\n'
        code += f'  {decision_node} [label="{decision["condition"]}?", shape=diamond, fillcolor="#fef3c7", color="#f59e0b", fontcolor="#92400e", fontsize=12]\n'
        code += f'  {yes_node} [label="{decision["yes"]}", shape=box, fillcolor="#dcfce7", color="#16a34a", fontcolor="#16a34a"]\n'
        code += f'  {no_node} [label="{decision["no"]}", shape=box, fillcolor="#fee2e2", color="#dc2626", fontcolor="#991b1b"]\n'
        
        code += f'  {last_node} -> {decision_node} [color="#64748b"]\n'
        code += f'  {decision_node} -> {yes_node} [label="YES", color="#16a34a", fontcolor="#16a34a"]\n'
        code += f'  {decision_node} -> {no_node} [label="NO", color="#dc2626", fontcolor="#dc2626"]\n'
        
        last_node = yes_node
        node_id += 3
    
    # Add end node
    code += f'\n  N{node_id} [label="END", shape=ellipse, fillcolor="#dcfce7", color="#16a34a", fontcolor="#16a34a", fontsize=13, style="filled"]\n'
    code += f'  {last_node} -> N{node_id} [color="#64748b"]\n'
    
    code += '}\n'
    return code

def generate_mermaid_v3(description):
    """Generate clean Mermaid with proper labels and flow"""
    steps, decision = parse_description_to_steps(description)
    
    code = 'flowchart TD\n'
    code += '  %% Styles\n'
    code += '  classDef startEnd fill:#dcfce7,stroke:#16a34a,stroke-width:3px,color:#16a34a\n'
    code += '  classDef process fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0c4a6e\n'
    code += '  classDef decision fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#92400e\n'
    code += '  classDef success fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#16a34a\n'
    code += '  classDef error fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#991b1b\n\n'
    
    node_id = 0
    
    # Start node
    code += f'  N{node_id}([START]):::startEnd\n'
    last_node = f'N{node_id}'
    node_id += 1
    
    # Steps
    for step in steps:
        current = f'N{node_id}'
        
        if any(word in step.lower() for word in ['error', 'fail', 'reject']):
            code += f'  {current}["{step}"]:::error\n'
        elif any(word in step.lower() for word in ['validate', 'check', 'verify']):
            code += f'  {current}["{step}"]:::decision\n'
        else:
            code += f'  {current}["{step}"]:::process\n'
        
        code += f'  {last_node} --> {current}\n'
        last_node = current
        node_id += 1
    
    # Decision point
    if decision:
        decision_node = f'N{node_id}'
        yes_node = f'N{node_id + 1}'
        no_node = f'N{node_id + 2}'
        
        code += f'\n  %% Decision\n'
        code += f'  {decision_node}{{{{{decision["condition"]}?}}}}:::decision\n'
        code += f'  {yes_node}["{decision["yes"]}"]:::success\n'
        code += f'  {no_node}["{decision["no"]}"]:::error\n'
        
        code += f'  {last_node} --> {decision_node}\n'
        code += f'  {decision_node} -->|YES| {yes_node}\n'
        code += f'  {decision_node} -->|NO| {no_node}\n'
        
        last_node = yes_node
        node_id += 3
    
    # End node
    code += f'\n  N{node_id}([END]):::startEnd\n'
    code += f'  {last_node} --> N{node_id}\n'
    
    return code

def generate_pikchr_v3(description):
    """Generate clean Pikchr diagram - using GraphViz instead since Pikchr is unreliable"""
    # Pikchr has too many syntax issues, just use GraphViz which is proven to work
    return generate_graphviz_v3(description)

def generate_plantuml_v3(description):
    """Generate clean PlantUML with proper labels and flow"""
    steps, decision = parse_description_to_steps(description)
    
    code = '@startuml\n'
    code += 'skinparam backgroundColor transparent\n'
    code += 'skinparam defaultFontSize 12\n'
    code += 'skinparam defaultFontName Arial\n'
    code += 'skinparam activityBackgroundColor #e0f2fe\n'
    code += 'skinparam activityBorderColor #0284c7\n'
    code += 'skinparam activityBorderThickness 2\n'
    code += 'skinparam activityFontColor #0c4a6e\n'
    code += 'skinparam activityDiamondBackgroundColor #fef3c7\n'
    code += 'skinparam activityDiamondBorderColor #f59e0b\n'
    code += 'skinparam ArrowColor #64748b\n'
    code += 'skinparam ArrowThickness 2\n\n'
    
    code += 'start\n\n'
    
    # Steps
    for step in steps:
        if any(word in step.lower() for word in ['error', 'fail', 'reject']):
            code += f'#dc2626:{step};\n'
        elif any(word in step.lower() for word in ['validate', 'check']):
            code += f'#f59e0b:{step};\n'
        else:
            code += f':{step};\n'
    
    # Decision
    if decision:
        code += f'\nif ({decision["condition"]}?) then (yes)\n'
        code += f'  #dcfce7:{decision["yes"]};\n'
        code += 'else (no)\n'
        code += f'  #fee2e2:{decision["no"]};\n'
        code += 'endif\n'
    
    code += '\nstop\n'
    code += '@enduml\n'
    
    return code

def generate_excalidraw_v3(description):
    """Generate clean Excalidraw with proper labels, spacing, and layout"""
    steps, decision = parse_description_to_steps(description)
    
    elements = []
    element_id = 1
    
    # Better layout constants for clean diagram
    center_x = 600  # Center of canvas
    start_y = 80
    vertical_spacing = 140  # Space between vertical elements
    horizontal_branch_offset = 350  # Distance from center for branches
    
    def make_element(elem_type, x, y, width, height, text, bg_color, stroke_color):
        nonlocal element_id
        elem_id = f"element-{element_id}"
        text_id = f"text-{element_id + 1}"
        element_id += 2
        
        # Create shape element with bound text element reference
        elem = {
            "id": elem_id,
            "type": elem_type,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "angle": 0,
            "strokeColor": stroke_color,
            "backgroundColor": bg_color,
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 1,
            "opacity": 100,
            "seed": 12345,
            "version": 1,
            "versionNonce": 1,
            "isDeleted": False,
            "boundElements": [{"type": "text", "id": text_id}],
            "updated": 1,
            "link": None,
            "locked": False
        }
        
        if elem_type == "ellipse":
            elem["roundness"] = None
        else:
            elem["roundness"] = {"type": 3, "value": 16}
        
        elements.append(elem)
        
        # Calculate text metrics
        # Excalidraw uses the container's center as reference
        text_width = len(text) * 8  # Approximate width
        text_height = 20
        
        # Position text at container center (text will be centered within container)
        text_x = x + (width - text_width) / 2
        text_y = y + (height - text_height) / 2
        
        # Add text element bound to container
        text_elem = {
            "id": text_id,
            "type": "text",
            "x": text_x,
            "y": text_y,
            "width": text_width,
            "height": text_height,
            "angle": 0,
            "strokeColor": stroke_color,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 1,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "seed": 12345,
            "version": 1,
            "versionNonce": 1,
            "isDeleted": False,
            "boundElements": None,
            "updated": 1,
            "link": None,
            "locked": False,
            "text": text,
            "fontSize": 16,
            "fontFamily": 1,
            "textAlign": "center",
            "verticalAlign": "middle",
            "baseline": 16,
            "containerId": elem_id,
            "originalText": text,
            "lineHeight": 1.25
        }
        
        elements.append(text_elem)
        return elem_id, x + width // 2, y + height
    
    def make_arrow(from_x, from_y, to_x, to_y, label=None, color="#64748b", from_elem_id=None, to_elem_id=None):
        nonlocal element_id
        arrow_id = f"arrow-{element_id}"
        element_id += 1
        
        # Calculate arrow path
        dx = to_x - from_x
        dy = to_y - from_y
        
        arrow = {
            "id": arrow_id,
            "type": "arrow",
            "x": from_x,
            "y": from_y,
            "width": dx,
            "height": dy,
            "angle": 0,
            "strokeColor": color,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 3,  # Thicker arrows
            "strokeStyle": "solid",
            "roughness": 1,
            "opacity": 100,
            "seed": 12345,
            "version": 1,
            "versionNonce": 1,
            "isDeleted": False,
            "boundElements": [],
            "updated": 1,
            "link": None,
            "locked": False,
            "points": [[0, 0], [dx, dy]],
            "lastCommittedPoint": None,
            "startBinding": {"elementId": from_elem_id, "focus": 0, "gap": 8} if from_elem_id else None,
            "endBinding": {"elementId": to_elem_id, "focus": 0, "gap": 8} if to_elem_id else None,
            "startArrowhead": None,
            "endArrowhead": "arrow"
        }
        
        elements.append(arrow)
        
        if label:
            text_id = f"label-{element_id}"
            element_id += 1
            
            # Position label near the start of the arrow for better visibility
            label_offset_x = 60
            label_offset_y = 30
            label_x = from_x + label_offset_x
            label_y = from_y + label_offset_y
            
            # Larger, more visible label
            label_width = 60
            label_height = 30
            
            label_elem = {
                "id": text_id,
                "type": "text",
                "x": label_x,
                "y": label_y,
                "width": label_width,
                "height": label_height,
                "text": label,
                "fontSize": 20,  # Bigger font
                "fontFamily": 1,
                "textAlign": "center",
                "verticalAlign": "middle",
                "strokeColor": color,
                "backgroundColor": "#ffffff",  # White background for visibility
                "fillStyle": "solid",
                "strokeWidth": 0,
                "strokeStyle": "solid",
                "roughness": 0,
                "opacity": 100,
                "angle": 0,
                "seed": 12345,
                "version": 1,
                "versionNonce": 1,
                "isDeleted": False,
                "boundElements": None,
                "updated": 1,
                "link": None,
                "locked": False,
                "lineHeight": 1.25,
                "baseline": 18
            }
            
            elements.append(label_elem)
    
    current_y = start_y
    
    # Start node - centered
    start_width, start_height = 220, 90
    start_x = center_x - start_width // 2
    last_id, last_x, last_y = make_element(
        "ellipse", 
        start_x, 
        current_y, 
        start_width, 
        start_height, 
        "START", 
        "#dcfce7", 
        "#16a34a"
    )
    # Set last position to center bottom of START for next arrow
    last_x = center_x
    last_y = current_y + start_height
    current_y += start_height + vertical_spacing
    
    # Steps - all centered vertically
    for step in steps:
        if any(word in step.lower() for word in ['error', 'fail']):
            bg, stroke = "#fee2e2", "#dc2626"
        else:
            bg, stroke = "#e0f2fe", "#0284c7"
        
        # Calculate width based on text length (min 240, max 360)
        step_width = max(240, min(360, len(step) * 7))
        step_height = 80
        
        curr_id, curr_x, curr_y = make_element(
            "rectangle", 
            center_x - step_width // 2, 
            current_y, 
            step_width, 
            step_height, 
            step[:50], 
            bg, 
            stroke
        )
        
        # Arrow from previous element with proper binding (to center top of current box)
        box_center_x = center_x
        box_top_y = current_y
        make_arrow(last_x, last_y, box_center_x, box_top_y, None, "#64748b", last_id, curr_id)
        
        # Update last position to center bottom of this box
        last_id = curr_id
        last_x = box_center_x
        last_y = current_y + step_height
        current_y += step_height + vertical_spacing
    
    # Decision point
    if decision:
        # Decision diamond - centered
        dec_width, dec_height = 240, 120
        dec_id, dec_x, dec_y = make_element(
            "diamond", 
            center_x - dec_width // 2, 
            current_y, 
            dec_width, 
            dec_height, 
            decision['condition'][:40] + "?", 
            "#fef3c7", 
            "#f59e0b"
        )
        
        # Arrow to decision with proper binding (to center top of diamond)
        dec_center_x = center_x
        dec_top_y = current_y
        make_arrow(last_x, last_y, dec_center_x, dec_top_y, None, "#64748b", last_id, dec_id)
        
        current_y += dec_height + vertical_spacing
        
        # YES branch (left side)
        yes_width = max(240, min(340, len(decision['yes']) * 7))
        yes_height = 80
        yes_x = center_x - horizontal_branch_offset - yes_width // 2
        
        yes_id, yes_cx, yes_cy = make_element(
            "rectangle", 
            yes_x, 
            current_y, 
            yes_width, 
            yes_height, 
            decision['yes'][:45], 
            "#dcfce7", 
            "#16a34a"
        )
        
        # Calculate proper connection points
        dec_left_x = dec_x + 30
        dec_left_y = dec_y + dec_height // 2
        yes_top_x = yes_cx
        yes_top_y = current_y
        
        # Arrow from decision to YES with proper binding
        make_arrow(dec_left_x, dec_left_y, yes_top_x, yes_top_y, "YES", "#16a34a", dec_id, yes_id)
        
        # NO branch (right side)
        no_width = max(240, min(340, len(decision['no']) * 7))
        no_height = 80
        no_x = center_x + horizontal_branch_offset - no_width // 2
        
        no_id, no_cx, no_cy = make_element(
            "rectangle", 
            no_x, 
            current_y, 
            no_width, 
            no_height, 
            decision['no'][:45], 
            "#fee2e2", 
            "#dc2626"
        )
        
        # Calculate proper connection points
        dec_right_x = dec_x + dec_width - 30
        dec_right_y = dec_y + dec_height // 2
        no_top_x = no_cx
        no_top_y = current_y
        
        # Arrow from decision to NO with proper binding
        make_arrow(dec_right_x, dec_right_y, no_top_x, no_top_y, "NO", "#dc2626", dec_id, no_id)
        
        current_y += yes_height + vertical_spacing
        
        # Both branches converge to center for END
        last_x, last_y = yes_cx, yes_cy
        merge_y = current_y - 40
    
    # End node - centered
    end_width, end_height = 220, 90
    end_id, end_x, end_y = make_element(
        "ellipse", 
        center_x - end_width // 2, 
        current_y, 
        end_width, 
        end_height, 
        "END", 
        "#dcfce7", 
        "#16a34a"
    )
    
    # Arrow from last element to END with proper binding
    if decision:
        # From YES branch to END (from bottom of YES box to top of END)
        yes_bottom_x = yes_cx
        yes_bottom_y = current_y - vertical_spacing + yes_height
        end_center_x = end_x + end_width // 2
        end_top_y = current_y
        
        make_arrow(yes_bottom_x, yes_bottom_y, end_center_x, end_top_y, None, "#64748b", yes_id, end_id)
        
        # From NO branch to END (from bottom of NO box to top of END)
        no_bottom_x = no_cx  
        no_bottom_y = current_y - vertical_spacing + no_height
        
        make_arrow(no_bottom_x, no_bottom_y, end_center_x, end_top_y, None, "#64748b", no_id, end_id)
    else:
        make_arrow(last_x, last_y, end_x + end_width // 2, current_y, None, "#64748b", last_id, end_id)
    
    result = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": "#ffffff"
        },
        "files": {}
    }
    
    return json.dumps(result)
