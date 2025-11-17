"""
Enhanced diagram generators for various diagram types
Supports advanced features, conditionals, styling, and complex workflows
"""
import re

FILLER_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might',
    'can', 'must', 'shall', 'it', 'this', 'that', 'these', 'those'
}

def clean_text(text, max_words=None):
    """Clean text by removing filler words"""
    words = text.split()
    cleaned = [w for w in words if w.lower() not in FILLER_WORDS or len(w) > 4]
    if max_words:
        cleaned = cleaned[:max_words]
    return ' '.join(cleaned) if cleaned else text.split()[:max_words or 6]

def parse_workflow(description):
    """Parse natural language into workflow components"""
    desc_lower = description.lower()
    
    # Extract steps
    steps = []
    conditions = []
    
    # Split by common delimiters
    parts = re.split(r'[,;]|\bthen\b|\bnext\b|\bafter\b', description, flags=re.IGNORECASE)
    
    # Find conditionals (if/else, either/or)
    conditional_patterns = [
        r'if\s+([^,]+?)\s+(show|display|go to|then|:)\s+([^,]+?)(?:\s+else\s+([^,]+?))?(?:[,;.]|$)',
        r'(?:either|when)\s+([^,]+?)\s+(?:or|otherwise)\s+([^,]+?)(?:[,;.]|$)',
    ]
    
    for pattern in conditional_patterns:
        for match in re.finditer(pattern, description, re.IGNORECASE):
            groups = match.groups()
            condition = clean_text(groups[0], max_words=5)
            yes_action = clean_text(groups[2] if len(groups) > 2 else groups[1], max_words=5)
            no_action = clean_text(groups[3], max_words=5) if len(groups) > 3 and groups[3] else "Alternative path"
            
            conditions.append({
                'condition': condition,
                'yes': yes_action,
                'no': no_action
            })
    
    # Extract regular steps
    for part in parts:
        part = part.strip()
        if len(part) > 5 and not any(cond['condition'] in part for cond in conditions):
            cleaned = clean_text(part, max_words=6)
            if cleaned:
                steps.append(cleaned)
    
    # Identify step types
    typed_steps = []
    for step in steps:
        step_lower = step.lower()
        if any(word in step_lower for word in ['start', 'begin', 'login', 'submit']):
            typed_steps.append({'text': step, 'type': 'start'})
        elif any(word in step_lower for word in ['end', 'complete', 'finish', 'logout', 'exit']):
            typed_steps.append({'text': step, 'type': 'end'})
        elif any(word in step_lower for word in ['validate', 'check', 'verify', 'review']):
            typed_steps.append({'text': step, 'type': 'decision'})
        elif any(word in step_lower for word in ['error', 'fail', 'reject']):
            typed_steps.append({'text': step, 'type': 'error'})
        elif any(word in step_lower for word in ['database', 'store', 'save', 'archive']):
            typed_steps.append({'text': step, 'type': 'database'})
        elif any(word in step_lower for word in ['process', 'execute', 'run', 'perform']):
            typed_steps.append({'text': step, 'type': 'process'})
        else:
            typed_steps.append({'text': step, 'type': 'default'})
    
    return {
        'steps': typed_steps,
        'conditions': conditions,
        'has_conditionals': len(conditions) > 0
    }

def generate_d2_diagram(description):
    """Generate advanced D2 diagram with conditionals, shapes, and styling"""
    workflow = parse_workflow(description)
    
    code = "# D2 Diagram - Generated from natural language\n"
    code += "direction: down\n\n"
    
    # Define classes for different node types
    code += """# Style classes for different node types
classes: {
  start: {
    shape: oval
    style: {
      fill: "#dcfce7"
      stroke: "#16a34a"
      stroke-width: 3
    }
  }
  process: {
    shape: rectangle
    style: {
      fill: "#e0f2fe"
      stroke: "#0284c7"
      stroke-width: 2
      border-radius: 8
    }
  }
  decision: {
    shape: diamond
    style: {
      fill: "#fef3c7"
      stroke: "#f59e0b"
      stroke-width: 2
    }
  }
  error: {
    shape: rectangle
    style: {
      fill: "#fee2e2"
      stroke: "#dc2626"
      stroke-width: 2
      border-radius: 8
    }
  }
  database: {
    shape: cylinder
    style: {
      fill: "#e0e7ff"
      stroke: "#4f46e5"
      stroke-width: 2
    }
  }
  end: {
    shape: oval
    style: {
      fill: "#dcfce7"
      stroke: "#16a34a"
      stroke-width: 3
    }
  }
}

"""
    
    # Generate nodes
    node_id_map = {}
    for i, step in enumerate(workflow['steps']):
        node_id = f"step{i}"
        node_id_map[step['text']] = node_id
        
        # Map type to class
        class_name = step['type'] if step['type'] != 'default' else 'process'
        
        code += f"{node_id}: {step['text']} {{\n"
        code += f"  class: {class_name}\n"
        code += "}\n"
    
    # Add conditional nodes
    for i, cond in enumerate(workflow['conditions']):
        cond_id = f"cond{i}"
        yes_id = f"yes{i}"
        no_id = f"no{i}"
        
        code += f"\n{cond_id}: {cond['condition']}? {{\n"
        code += "  class: decision\n"
        code += "}\n"
        
        code += f"{yes_id}: {cond['yes']} {{\n"
        code += "  class: process\n"
        code += "}\n"
        
        code += f"{no_id}: {cond['no']} {{\n"
        code += "  class: error\n"
        code += "}\n"
    
    # Connect steps
    code += "\n# Connections\n"
    prev_id = None
    for i, step in enumerate(workflow['steps']):
        node_id = f"step{i}"
        if prev_id:
            code += f"{prev_id} -> {node_id}\n"
        prev_id = node_id
    
    # Connect conditionals
    for i, cond in enumerate(workflow['conditions']):
        cond_id = f"cond{i}"
        yes_id = f"yes{i}"
        no_id = f"no{i}"
        
        if prev_id:
            code += f"{prev_id} -> {cond_id}\n"
        
        code += f"{cond_id} -> {yes_id}: Yes {{\n"
        code += "  style.stroke: \"#16a34a\"\n"
        code += "  style.stroke-width: 2\n"
        code += "}\n"
        
        code += f"{cond_id} -> {no_id}: No {{\n"
        code += "  style.stroke: \"#dc2626\"\n"
        code += "  style.stroke-width: 2\n"
        code += "}\n"
        
        prev_id = cond_id
    
    return code

def generate_blockdiag_diagram(description):
    """Generate advanced BlockDiag diagram with groups, colors, and styling"""
    workflow = parse_workflow(description)
    
    code = "blockdiag {\n"
    
    # Set diagram attributes
    code += "  default_fontsize = 13;\n"
    code += "  node_width = 180;\n"
    code += "  node_height = 60;\n"
    code += "  default_shape = roundedbox;\n"
    code += "  orientation = portrait;\n\n"
    
    # Generate nodes with proper attributes
    node_ids = []
    for i, step in enumerate(workflow['steps']):
        node_id = f"N{i}"
        node_ids.append(node_id)
        label = step['text'][:30]  # Limit label length
        
        # Choose color based on type
        if step['type'] == 'start':
            color = "lightgreen"
            textcolor = "#16a34a"
        elif step['type'] == 'end':
            color = "lightgreen"
            textcolor = "#16a34a"
        elif step['type'] == 'decision':
            color = "#fef3c7"
            textcolor = "#92400e"
        elif step['type'] == 'error':
            color = "#fee2e2"
            textcolor = "#991b1b"
        elif step['type'] == 'database':
            color = "#e0e7ff"
            textcolor = "#3730a3"
        else:
            color = "#e0f2fe"
            textcolor = "#075985"
        
        code += f'  {node_id} [label = "{label}", color = "{color}", textcolor = "{textcolor}"];\n'
    
    # Add conditional nodes
    cond_node_ids = []
    for i, cond in enumerate(workflow['conditions']):
        cond_id = f"C{i}"
        yes_id = f"Y{i}"
        no_id = f"N_No{i}"
        
        code += f'  {cond_id} [label = "{cond["condition"]}?", shape = "diamond", color = "#fef3c7", textcolor = "#92400e"];\n'
        code += f'  {yes_id} [label = "{cond["yes"]}", color = "#dcfce7", textcolor = "#16a34a"];\n'
        code += f'  {no_id} [label = "{cond["no"]}", color = "#fee2e2", textcolor = "#991b1b"];\n'
        
        cond_node_ids.append((cond_id, yes_id, no_id))
    
    # Create connections
    code += "\n  // Workflow connections\n"
    for i in range(len(node_ids) - 1):
        code += f"  {node_ids[i]} -> {node_ids[i+1]};\n"
    
    # Connect conditionals
    if cond_node_ids:
        code += "\n  // Conditional branches\n"
        last_node = node_ids[-1] if node_ids else None
        for cond_id, yes_id, no_id in cond_node_ids:
            if last_node:
                code += f"  {last_node} -> {cond_id};\n"
            code += f'  {cond_id} -> {yes_id} [label = "Yes", color = "green"];\n'
            code += f'  {cond_id} -> {no_id} [label = "No", color = "red"];\n'
            last_node = cond_id
    
    code += "}\n"
    return code

def generate_graphviz_enhanced(description):
    """Generate enhanced GraphViz with better parsing and all workflow elements"""
    workflow = parse_workflow(description)
    
    # Build node list
    nodes = []
    edges = []
    node_id_counter = 0
    
    # Helper to create node
    def make_node(text, node_type):
        nonlocal node_id_counter
        node_id = f"N{node_id_counter}"
        node_id_counter += 1
        
        label = text[:50]
        
        # Style by type
        if node_type == 'start':
            shape = 'ellipse'
            fillcolor = '#dcfce7'
            color = '#16a34a'
        elif node_type == 'end':
            shape = 'ellipse'
            fillcolor = '#dcfce7'
            color = '#16a34a'
        elif node_type == 'decision':
            shape = 'diamond'
            fillcolor = '#fef3c7'
            color = '#f59e0b'
        elif node_type == 'error':
            shape = 'box'
            fillcolor = '#fee2e2'
            color = '#dc2626'
        elif node_type == 'database':
            shape = 'cylinder'
            fillcolor = '#e0e7ff'
            color = '#4f46e5'
        elif node_type == 'process':
            shape = 'box'
            fillcolor = '#ddd6fe'
            color = '#7c3aed'
        else:
            shape = 'box'
            fillcolor = '#e0f2fe'
            color = '#0284c7'
        
        nodes.append(f'{node_id} [label="{label}", shape={shape}, style="filled,rounded", fillcolor="{fillcolor}", color="{color}", fontname="Arial", fontsize=11]')
        return node_id
    
    # Create nodes for steps
    step_node_ids = []
    for step in workflow['steps']:
        node_id = make_node(step['text'], step['type'])
        step_node_ids.append(node_id)
    
    # Connect steps sequentially
    for i in range(len(step_node_ids) - 1):
        edges.append(f'{step_node_ids[i]} -> {step_node_ids[i+1]} [color="#64748b", penwidth=2]')
    
    # Add conditionals
    last_node = step_node_ids[-1] if step_node_ids else None
    for cond in workflow['conditions']:
        cond_node = make_node(cond['condition'] + "?", 'decision')
        yes_node = make_node(cond['yes'], 'process')
        no_node = make_node(cond['no'], 'error')
        
        if last_node:
            edges.append(f'{last_node} -> {cond_node} [color="#64748b", penwidth=2]')
        
        edges.append(f'{cond_node} -> {yes_node} [label="Yes", color="#16a34a", penwidth=2, fontcolor="#16a34a"]')
        edges.append(f'{cond_node} -> {no_node} [label="No", color="#dc2626", penwidth=2, fontcolor="#dc2626"]')
        
        last_node = cond_node
    
    # Build final code
    code = '''digraph Workflow {
  bgcolor="transparent"
  rankdir=TB
  node [fontname="Arial"]
  edge [fontname="Arial", fontsize=10]
  
'''
    
    code += '  ' + '\n  '.join(nodes) + '\n\n'
    code += '  ' + '\n  '.join(edges) + '\n'
    code += '}\n'
    
    return code

def generate_mermaid_diagram(description):
    """Generate advanced Mermaid flowchart with subgraphs, styling, and conditionals"""
    workflow = parse_workflow(description)
    
    code = "%%{init: {'theme':'base', 'themeVariables': {'primaryColor':'#e0f2fe','primaryTextColor':'#0c4a6e','primaryBorderColor':'#0284c7','lineColor':'#64748b','secondaryColor':'#dcfce7','tertiaryColor':'#fef3c7'}}}%%\n"
    code += "flowchart TD\n"
    
    # Style definitions
    code += "    classDef startStyle fill:#dcfce7,stroke:#16a34a,stroke-width:3px,color:#16a34a\n"
    code += "    classDef processStyle fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0c4a6e\n"
    code += "    classDef decisionStyle fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#92400e\n"
    code += "    classDef errorStyle fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#991b1b\n"
    code += "    classDef databaseStyle fill:#e0e7ff,stroke:#4f46e5,stroke-width:2px,color:#3730a3\n"
    code += "    classDef endStyle fill:#dcfce7,stroke:#16a34a,stroke-width:3px,color:#16a34a\n\n"
    
    # Generate nodes
    node_ids = []
    for i, step in enumerate(workflow['steps']):
        node_id = f"N{i}"
        node_ids.append((node_id, step['type']))
        text = step['text'][:40]
        
        # Choose shape based on type
        if step['type'] == 'start':
            code += f"    {node_id}([{text}]):::{step['type']}Style\n"
        elif step['type'] == 'end':
            code += f"    {node_id}([{text}]):::{step['type']}Style\n"
        elif step['type'] == 'decision':
            code += f"    {node_id}{{{text}?}}:::{step['type']}Style\n"
        elif step['type'] == 'database':
            code += f"    {node_id}[({text})]:::{step['type']}Style\n"
        elif step['type'] == 'error':
            code += f"    {node_id}[{text}]:::{step['type']}Style\n"
        else:
            code += f"    {node_id}[{text}]:::{step['type']}Style\n"
    
    # Add conditional nodes
    cond_nodes = []
    for i, cond in enumerate(workflow['conditions']):
        cond_id = f"C{i}"
        yes_id = f"Y{i}"
        no_id = f"No{i}"
        
        code += f"    {cond_id}{{{cond['condition']}?}}:::decisionStyle\n"
        code += f"    {yes_id}[{cond['yes']}]:::processStyle\n"
        code += f"    {no_id}[{cond['no']}]:::errorStyle\n"
        
        cond_nodes.append((cond_id, yes_id, no_id))
    
    code += "\n"
    
    # Connect steps
    for i in range(len(node_ids) - 1):
        code += f"    {node_ids[i][0]} --> {node_ids[i+1][0]}\n"
    
    # Connect conditionals
    last_node = node_ids[-1][0] if node_ids else None
    for cond_id, yes_id, no_id in cond_nodes:
        if last_node:
            code += f"    {last_node} --> {cond_id}\n"
        code += f"    {cond_id} -->|Yes| {yes_id}\n"
        code += f"    {cond_id} -->|No| {no_id}\n"
        last_node = cond_id
    
    return code

def generate_plantuml_diagram(description):
    """Generate advanced PlantUML activity diagram with partitions, colors, and conditionals"""
    workflow = parse_workflow(description)
    
    code = "@startuml\n"
    
    # Skinparam for beautiful styling
    code += "skinparam backgroundColor transparent\n"
    code += "skinparam activityShape octagon\n"
    code += "skinparam activityBackgroundColor #e0f2fe\n"
    code += "skinparam activityBorderColor #0284c7\n"
    code += "skinparam activityBorderThickness 2\n"
    code += "skinparam activityFontColor #0c4a6e\n"
    code += "skinparam activityFontSize 12\n"
    code += "skinparam activityDiamondBackgroundColor #fef3c7\n"
    code += "skinparam activityDiamondBorderColor #f59e0b\n"
    code += "skinparam partitionBackgroundColor #f0f9ff\n"
    code += "skinparam partitionBorderColor #0284c7\n"
    code += "skinparam ArrowColor #64748b\n"
    code += "skinparam ArrowThickness 2\n\n"
    
    code += "start\n\n"
    
    # Group steps into a partition if there are multiple
    if len(workflow['steps']) > 2:
        code += "partition \"Workflow Steps\" #e0f2fe {\n"
        indent = "  "
    else:
        indent = ""
    
    # Generate activities
    for i, step in enumerate(workflow['steps']):
        text = step['text'][:50]
        
        if step['type'] == 'decision':
            code += f"{indent}:{text};\n"
            code += f"{indent}note right\n"
            code += f"{indent}  Decision point\n"
            code += f"{indent}end note\n"
        elif step['type'] == 'error':
            code += f"{indent}#dc2626:{text};\n"
        elif step['type'] == 'database':
            code += f"{indent}#4f46e5:{text};\n"
        elif step['type'] == 'process':
            code += f"{indent}#7c3aed:{text};\n"
        else:
            code += f"{indent}:{text};\n"
    
    if len(workflow['steps']) > 2:
        code += "}\n\n"
    
    # Add conditional logic
    for cond in workflow['conditions']:
        code += f"if ({cond['condition']}?) then (yes)\n"
        code += f"  #dcfce7:{cond['yes']};\n"
        code += "else (no)\n"
        code += f"  #fee2e2:{cond['no']};\n"
        code += "endif\n\n"
    
    # Add note if there are complex workflows
    if workflow['has_conditionals']:
        code += "note right\n"
        code += "  Workflow includes\n"
        code += "  conditional branches\n"
        code += "end note\n\n"
    
    code += "stop\n"
    code += "@enduml\n"
    
    return code

def generate_excalidraw_diagram(description):
    """Generate enhanced Excalidraw JSON with better layout and styling"""
    import json
    import hashlib
    
    workflow = parse_workflow(description)
    
    elements = []
    element_id_counter = 1
    y_position = 100
    x_position = 200
    
    # Helper to generate unique IDs
    def make_id():
        nonlocal element_id_counter
        element_id = f"element-{element_id_counter}"
        element_id_counter += 1
        return element_id
    
    # Track node positions for connections
    node_positions = []
    
    # Generate nodes for steps
    for i, step in enumerate(workflow['steps']):
        text = step['text'][:40]
        element_id = make_id()
        
        # Determine size based on text length
        text_width = len(text) * 8
        width = max(180, min(text_width, 280))
        height = 70
        
        # Choose colors based on type
        if step['type'] == 'start':
            bg_color = "#dcfce7"
            stroke_color = "#16a34a"
        elif step['type'] == 'end':
            bg_color = "#dcfce7"
            stroke_color = "#16a34a"
        elif step['type'] == 'decision':
            bg_color = "#fef3c7"
            stroke_color = "#f59e0b"
        elif step['type'] == 'error':
            bg_color = "#fee2e2"
            stroke_color = "#dc2626"
        elif step['type'] == 'database':
            bg_color = "#e0e7ff"
            stroke_color = "#4f46e5"
        else:
            bg_color = "#e0f2fe"
            stroke_color = "#0284c7"
        
        # Add rectangle
        elements.append({
            "id": element_id,
            "type": "rectangle",
            "x": x_position,
            "y": y_position,
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
            "roundness": {"type": 3, "value": 16},
            "seed": abs(hash(text)) % 100000,
            "version": 1,
            "versionNonce": abs(hash(text + str(i))) % 100000,
            "isDeleted": False,
            "boundElements": [],
            "updated": 1,
            "link": None,
            "locked": False
        })
        
        # Add text
        text_id = make_id()
        elements.append({
            "id": text_id,
            "type": "text",
            "x": x_position + 10,
            "y": y_position + (height - 20) / 2,
            "width": width - 20,
            "height": 25,
            "angle": 0,
            "strokeColor": stroke_color,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "seed": abs(hash(text + "text")) % 100000,
            "version": 1,
            "versionNonce": abs(hash(text + "text" + str(i))) % 100000,
            "isDeleted": False,
            "boundElements": [],
            "updated": 1,
            "link": None,
            "locked": False,
            "text": text,
            "fontSize": 16,
            "fontFamily": 1,
            "textAlign": "center",
            "verticalAlign": "middle",
            "baseline": 18,
            "containerId": element_id,
            "originalText": text,
            "lineHeight": 1.25
        })
        
        # Store position for connections
        node_positions.append({
            'id': element_id,
            'x': x_position,
            'y': y_position,
            'width': width,
            'height': height
        })
        
        # Update position for next node
        y_position += height + 100
    
    # Add arrows between nodes
    for i in range(len(node_positions) - 1):
        from_node = node_positions[i]
        to_node = node_positions[i + 1]
        
        arrow_id = make_id()
        
        # Calculate connection points
        start_x = from_node['x'] + from_node['width'] / 2
        start_y = from_node['y'] + from_node['height']
        end_x = to_node['x'] + to_node['width'] / 2
        end_y = to_node['y']
        
        elements.append({
            "id": arrow_id,
            "type": "arrow",
            "x": start_x,
            "y": start_y,
            "width": end_x - start_x,
            "height": end_y - start_y,
            "angle": 0,
            "strokeColor": "#64748b",
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 1,
            "opacity": 100,
            "seed": abs(hash(f"arrow{i}")) % 100000,
            "version": 1,
            "versionNonce": abs(hash(f"arrow{i}v")) % 100000,
            "isDeleted": False,
            "boundElements": [],
            "updated": 1,
            "link": None,
            "locked": False,
            "points": [[0, 0], [end_x - start_x, end_y - start_y]],
            "lastCommittedPoint": None,
            "startBinding": None,
            "endBinding": None,
            "startArrowhead": None,
            "endArrowhead": "arrow"
        })
    
    # Add conditional branches if any
    for i, cond in enumerate(workflow['conditions']):
        cond_y = y_position
        
        # Decision diamond
        decision_id = make_id()
        elements.append({
            "id": decision_id,
            "type": "diamond",
            "x": x_position,
            "y": cond_y,
            "width": 200,
            "height": 100,
            "angle": 0,
            "strokeColor": "#f59e0b",
            "backgroundColor": "#fef3c7",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 1,
            "opacity": 100,
            "seed": abs(hash(cond['condition'])) % 100000,
            "version": 1,
            "versionNonce": abs(hash(cond['condition'] + "v")) % 100000,
            "isDeleted": False,
            "boundElements": [],
            "updated": 1,
            "link": None,
            "locked": False
        })
        
        # Decision text
        decision_text_id = make_id()
        elements.append({
            "id": decision_text_id,
            "type": "text",
            "x": x_position + 20,
            "y": cond_y + 40,
            "width": 160,
            "height": 20,
            "text": cond['condition'][:30] + "?",
            "fontSize": 14,
            "fontFamily": 1,
            "textAlign": "center",
            "verticalAlign": "middle",
            "containerId": decision_id,
            "originalText": cond['condition'][:30] + "?",
            "strokeColor": "#92400e",
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": abs(hash(cond['condition'] + "text")) % 100000,
            "version": 1,
            "versionNonce": 1,
            "isDeleted": False,
            "lineHeight": 1.25,
            "baseline": 14
        })
        
        # Yes branch (left)
        yes_id = make_id()
        yes_x = x_position - 250
        yes_y = cond_y + 120
        
        elements.append({
            "id": yes_id,
            "type": "rectangle",
            "x": yes_x,
            "y": yes_y,
            "width": 180,
            "height": 70,
            "strokeColor": "#16a34a",
            "backgroundColor": "#dcfce7",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 1,
            "opacity": 100,
            "roundness": {"type": 3, "value": 16},
            "angle": 0,
            "seed": abs(hash(cond['yes'])) % 100000,
            "version": 1,
            "versionNonce": 1,
            "isDeleted": False,
            "boundElements": [],
            "updated": 1,
            "link": None,
            "locked": False
        })
        
        # Yes text
        elements.append({
            "id": make_id(),
            "type": "text",
            "x": yes_x + 10,
            "y": yes_y + 25,
            "width": 160,
            "height": 20,
            "text": cond['yes'][:30],
            "fontSize": 14,
            "fontFamily": 1,
            "textAlign": "center",
            "verticalAlign": "middle",
            "containerId": yes_id,
            "originalText": cond['yes'][:30],
            "strokeColor": "#16a34a",
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": 1,
            "version": 1,
            "versionNonce": 1,
            "isDeleted": False,
            "lineHeight": 1.25,
            "baseline": 14
        })
        
        # No branch (right)
        no_id = make_id()
        no_x = x_position + 250
        no_y = cond_y + 120
        
        elements.append({
            "id": no_id,
            "type": "rectangle",
            "x": no_x,
            "y": no_y,
            "width": 180,
            "height": 70,
            "strokeColor": "#dc2626",
            "backgroundColor": "#fee2e2",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 1,
            "opacity": 100,
            "roundness": {"type": 3, "value": 16},
            "angle": 0,
            "seed": abs(hash(cond['no'])) % 100000,
            "version": 1,
            "versionNonce": 1,
            "isDeleted": False,
            "boundElements": [],
            "updated": 1,
            "link": None,
            "locked": False
        })
        
        # No text
        elements.append({
            "id": make_id(),
            "type": "text",
            "x": no_x + 10,
            "y": no_y + 25,
            "width": 160,
            "height": 20,
            "text": cond['no'][:30],
            "fontSize": 14,
            "fontFamily": 1,
            "textAlign": "center",
            "verticalAlign": "middle",
            "containerId": no_id,
            "originalText": cond['no'][:30],
            "strokeColor": "#dc2626",
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "roughness": 0,
            "opacity": 100,
            "angle": 0,
            "seed": 1,
            "version": 1,
            "versionNonce": 1,
            "isDeleted": False,
            "lineHeight": 1.25,
            "baseline": 14
        })
        
        # Arrows from decision to branches
        # Arrow to Yes
        elements.append({
            "id": make_id(),
            "type": "arrow",
            "x": x_position,
            "y": cond_y + 50,
            "width": yes_x + 180 - x_position,
            "height": 70,
            "strokeColor": "#16a34a",
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 1,
            "opacity": 100,
            "angle": 0,
            "seed": 1,
            "version": 1,
            "versionNonce": 1,
            "isDeleted": False,
            "points": [[0, 0], [yes_x + 180 - x_position, 70]],
            "endArrowhead": "arrow",
            "startArrowhead": None
        })
        
        # Arrow to No
        elements.append({
            "id": make_id(),
            "type": "arrow",
            "x": x_position + 200,
            "y": cond_y + 50,
            "width": no_x - (x_position + 200),
            "height": 70,
            "strokeColor": "#dc2626",
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 1,
            "opacity": 100,
            "angle": 0,
            "seed": 1,
            "version": 1,
            "versionNonce": 1,
            "isDeleted": False,
            "points": [[0, 0], [no_x - (x_position + 200), 70]],
            "endArrowhead": "arrow",
            "startArrowhead": None
        })
        
        y_position = cond_y + 220
    
    # Create Excalidraw JSON structure
    excalidraw_data = {
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
    
    return json.dumps(excalidraw_data)
