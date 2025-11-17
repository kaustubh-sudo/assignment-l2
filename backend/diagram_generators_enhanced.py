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
            code += f"{indent}#{dc2626}:{text};\n"
        elif step['type'] == 'database':
            code += f"{indent}#{4f46e5}:{text};\n"
        elif step['type'] == 'process':
            code += f"{indent}#{7c3aed}:{text};\n"
        else:
            code += f"{indent}:{text};\n"
    
    if len(workflow['steps']) > 2:
        code += "}\n\n"
    
    # Add conditional logic
    for cond in workflow['conditions']:
        code += f"if ({cond['condition']}?) then (yes)\n"
        code += f"  #{dcfce7}:{cond['yes']};\n"
        code += "else (no)\n"
        code += f"  #{fee2e2}:{cond['no']};\n"
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
