"""
Advanced diagram code generator for complex workflows
"""
import re

FILLER_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might',
    'can', 'must', 'shall', 'it', 'this', 'that', 'these', 'those'
}

def clean_text(text):
    """Clean text by removing filler words and extra spaces"""
    words = text.split()
    cleaned = [w for w in words if w.lower() not in FILLER_WORDS or len(w) > 4]
    return ' '.join(cleaned[:6])  # Limit to 6 words max

def make_safe_id(text):
    """Create safe GraphViz node ID"""
    words = text.split()[:2]
    base = ''.join(w.capitalize() for w in words if w.lower() not in FILLER_WORDS)
    # Remove invalid characters
    base = re.sub(r'[^a-zA-Z0-9]', '', base)
    return base if base else 'Node'

def generate_graphviz_advanced(description):
    """
    Generate sophisticated GraphViz code from natural language
    Handles: routing, branching, parallel, errors, retries
    """
    nodes = []
    edges = []
    node_map = {}
    node_counter = 0
    
    def add_node(text, shape='box', fillcolor='#e0f2fe', color='#0284c7'):
        nonlocal node_counter
        node_id = f"{make_safe_id(text)}{node_counter}"
        node_counter += 1
        label = clean_text(text)[:40]
        nodes.append(f'{node_id} [label="{label}", shape={shape}, style="filled", fillcolor="{fillcolor}", color="{color}"]')
        node_map[text] = node_id
        return node_id
    
    def add_edge(from_id, to_id, label='', color='#64748b', style=''):
        style_attr = f', style={style}' if style else ''
        label_attr = f', label="{label}"' if label else ''
        edges.append(f'{from_id} -> {to_id} [{label_attr} color="{color}"{style_attr}]')
    
    # Parse description into logical components
    desc_lower = description.lower()
    
    # 1. Extract main steps (split by periods, commas)
    sentences = re.split(r'[.]', description)
    main_steps = []
    
    for sentence in sentences:
        parts = re.split(r',|;', sentence)
        for part in parts:
            part = part.strip()
            if len(part) > 10:
                main_steps.append(part)
    
    # 2. Detect routing (fast-path/slow-path, either/or)
    routing_match = re.search(r'(?:routed?\s+to|choose)\s+(?:either\s+)?(?:a\s+)?(\w+[- ]?\w+)\s+(?:or|\/)\s+(?:a\s+)?(\w+[- ]?\w+)', description, re.IGNORECASE)
    
    # 3. Detect error handling
    error_patterns = {
        'transient': re.search(r'(?:retry|transient\s+errors?)\s*[:]?\s*([^,.]{10,40})', description, re.IGNORECASE),
        'fatal': re.search(r'(?:fatal\s+errors?|dead[- ]?letter)\s*[:]?\s*([^,.]{10,40})', description, re.IGNORECASE),
        'timeout': re.search(r'(?:timeout)\s*[:]?\s*([^,.]{10,40})', description, re.IGNORECASE),
    }
    
    # 4. Detect conditionals
    conditional_match = re.search(r'if\s+([^:,]{5,30})\s*[:]?\s*([^,.]{5,40})', description, re.IGNORECASE)
    
    # 5. Detect success/failure paths
    success_match = re.search(r'(?:on\s+)?success\s*[:]?\s*([^,.]{10,40})', description, re.IGNORECASE)
    
    # Build diagram structure
    prev_id = None
    
    # Add start node if description starts with user/submit
    if re.search(r'^(?:a\s+)?user\s+submits?', desc_lower):
        start_id = add_node("User Submits Request", shape='ellipse', fillcolor='#dcfce7', color='#16a34a')
        prev_id = start_id
    
    # Add validation/enrichment steps
    if 'validat' in desc_lower:
        validate_id = add_node("Validate Request", shape='diamond', fillcolor='#fef3c7', color='#f59e0b')
        if prev_id:
            add_edge(prev_id, validate_id)
        prev_id = validate_id
    
    if 'enrich' in desc_lower:
        enrich_id = add_node("Enrich Data", shape='box', fillcolor='#e0f2fe', color='#0284c7')
        if prev_id:
            add_edge(prev_id, enrich_id)
        prev_id = enrich_id
    
    # Add routing node if detected
    if routing_match:
        path1, path2 = routing_match.groups()
        route_id = add_node("Route Request", shape='diamond', fillcolor='#fef3c7', color='#f59e0b')
        if prev_id:
            add_edge(prev_id, route_id)
        
        # Add path 1 (usually fast-path)
        path1_id = add_node(f"{path1} Processing", shape='box', fillcolor='#e0f2fe', color='#0284c7')
        add_edge(route_id, path1_id, label=path1, color='#16a34a')
        
        # Add path 2 (usually slow-path)
        path2_id = add_node(f"{path2} Queue", shape='cylinder', fillcolor='#fce7f3', color='#db2777')
        add_edge(route_id, path2_id, label=path2, color='#ea580c')
        
        # Continue from slow path
        if 'worker' in desc_lower or 'parallel' in desc_lower:
            worker_id = add_node("Parallel Workers", shape='folder', fillcolor='#ddd6fe', color='#7c3aed')
            add_edge(path2_id, worker_id)
            prev_id = worker_id
        else:
            prev_id = path2_id
    
    # Add conditional if detected
    if conditional_match:
        condition, action = conditional_match.groups()
        cond_id = add_node(condition, shape='diamond', fillcolor='#fef3c7', color='#f59e0b')
        if prev_id:
            add_edge(prev_id, cond_id)
        
        action_id = add_node(action, shape='box', fillcolor='#e0f2fe', color='#0284c7')
        add_edge(cond_id, action_id, label="Yes", color='#16a34a')
        prev_id = action_id
    
    # Add success path
    if success_match:
        success_action = success_match.group(1)
        success_id = add_node(success_action, shape='box3d', fillcolor='#e0e7ff', color='#4f46e5')
        if prev_id:
            add_edge(prev_id, success_id, label="Success", color='#16a34a')
    
    # Add error handling paths
    if error_patterns['transient'] and error_patterns['transient'].group(1):
        retry_id = add_node("Retry with Backoff", shape='box', fillcolor='#fff7ed', color='#ea580c')
        if prev_id:
            add_edge(prev_id, retry_id, label="Transient Error", color='#ea580c', style='dashed')
            add_edge(retry_id, prev_id, label="Retry", color='#ea580c', style='dashed')
    
    if error_patterns['fatal'] and error_patterns['fatal'].group(1):
        dlq_id = add_node("Dead Letter Queue", shape='box', fillcolor='#fee2e2', color='#dc2626')
        alert_id = add_node("Raise Alert", shape='box', fillcolor='#fff7ed', color='#ea580c')
        if prev_id:
            add_edge(prev_id, dlq_id, label="Fatal Error", color='#dc2626')
            add_edge(dlq_id, alert_id, color='#dc2626')
    
    # Generate code
    code = f'''digraph ComplexFlow {{
  bgcolor="transparent"
  rankdir=TB
  node [fontname="Arial", fontsize=11]
  edge [fontname="Arial", fontsize=9]
  
  {chr(10).join('  ' + node for node in nodes)}
  
  {chr(10).join('  ' + edge for edge in edges)}
}}'''
    
    return code
