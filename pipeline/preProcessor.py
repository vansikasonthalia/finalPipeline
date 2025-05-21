from collections import defaultdict, deque
import re
from graphql import build_schema, print_schema
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Extract GraphQL query from a text blob
def extract_graphql_query(text):
    query_pattern = r"""(?:fragment\s+\w+\s+on\s+\w+\s*\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}\s*)*
    (query|mutation|subscription)\s*\w*\s*\{
    (?:[^{}]|\.\.\.\w+|\{(?:[^{}]|\{[^{}]*\})*\})*
    \}"""
    match = re.search(query_pattern, text, re.DOTALL | re.VERBOSE)
    if match:
        return match.group(0)
    return None

# Remove operation names (e.g. `query myQuery {` -> `query {`)
def strip_operation_name(query):
    if pd.isnull(query):
        return query
    return re.sub(
        r'\b(query|mutation|subscription)\b(?:\s+\w+(?:\s*\([^)]*\))?)\s*{',
        r'\1 {',
        query
    )

# Read input CSV
file_path = 'raw_schema.csv'
df = pd.read_csv(file_path)

# Extract query text
df['extracted_graphql'] = df['Generated_GraphQL'].apply(extract_graphql_query)

# Reorder schema types based on dependencies
def reorder_schema(schema: str) -> str:
    blocks = []
    current_block = []
    for line in schema.split('\n'):
        stripped = line.strip()
        if not stripped:
            if current_block:
                blocks.append('\n'.join(current_block))
            current_block = []
            continue
        if stripped.startswith(('type ', 'interface ', 'input ', 'extend type ')):
            if current_block:
                blocks.append('\n'.join(current_block))
            current_block = [line]
        else:
            current_block.append(line)
    if current_block:
        blocks.append('\n'.join(current_block))

    scalar_types = {'String', 'Int', 'Float', 'Boolean', 'ID'}
    type_info = {}
    base_blocks = {}
    for block in blocks:
        if not block.startswith(('type ', 'interface ', 'input ')):
            continue
        lines = block.split('\n')
        first_line = lines[0].strip()
        type_kw = first_line.split()[0]
        name = first_line.split('{', 1)[0].split()[-1]
        dependencies = []
        if type_kw == 'type' and 'implements' in first_line:
            implements_part = first_line.split('implements', 1)[1].split('{', 1)[0]
            dependencies.extend([i.strip() for i in implements_part.split('&')])
        for line in lines[1:]:
            line = line.strip().rstrip('}')
            if not line or ':' not in line:
                continue
            field_type = line.split(':', 1)[1].strip()
            field_type = field_type.split('!')[0].split('[')[0].split(']')[-1]
            if field_type not in scalar_types:
                dependencies.append(field_type)
        type_info[name] = list(set(dependencies))
        base_blocks[name] = block

    adj = defaultdict(list)
    in_degree = defaultdict(int)
    all_types = set(type_info.keys())
    for name, deps in type_info.items():
        for dep in deps:
            if dep in all_types:
                adj[dep].append(name)
                in_degree[name] += 1
    queue = deque([t for t in all_types if in_degree[t] == 0])
    sorted_types = []
    while queue:
        node = queue.popleft()
        sorted_types.append(node)
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    sorted_types += [t for t in all_types if t not in sorted_types]

    extensions = defaultdict(list)
    other_blocks = []
    for block in blocks:
        if block.startswith('extend type '):
            type_name = block.split('{', 1)[0].split()[-1]
            extensions[type_name].append(block)
        elif block not in base_blocks.values():
            other_blocks.append(block)

    ordered_schema = []
    seen_types = set()
    for t in sorted_types:
        if t in base_blocks:
            ordered_schema.append(base_blocks[t])
            seen_types.add(t)
        if t in extensions:
            ordered_schema.extend(extensions[t])
    for block in other_blocks:
        if block not in ordered_schema:
            ordered_schema.append(block)
    return '\n\n'.join(ordered_schema)

# Add scalar definitions if used in StepZen
def preprocess_stepzen_schema(schema: str) -> str:
    stepzen_scalars = {
        'Date': 'scalar Date',
        'DateTime': 'scalar DateTime',
        'JSON': 'scalar JSON',
        'Secret': 'scalar Secret'
    }
    scalar_pattern = r'\b(Date|DateTime|JSON|Secret)\b'
    used_scalars = set(re.findall(scalar_pattern, schema))
    existing_scalars = set(re.findall(r'^scalar\s+(\w+)', schema, re.MULTILINE))
    missing_definitions = [
        stepzen_scalars[s] for s in used_scalars
        if s in stepzen_scalars and s not in existing_scalars
    ]
    cleaned_schema = re.sub(r'@\w+\(.*?\)', '', schema)
    cleaned_schema = re.sub(r'\n{3,}', '\n\n', cleaned_schema).strip()
    if missing_definitions:
        return '\n'.join(missing_definitions) + '\n\n' + cleaned_schema
    return cleaned_schema

# Merge interface fields into implementing types
def update_schema(schema_str: str) -> str:
    schema = build_schema(schema_str)
    for type_name, type_def in schema.type_map.items():
        if hasattr(type_def, 'interfaces'):
            for interface in type_def.interfaces:
                for field_name, field_def in interface.fields.items():
                    if field_name not in type_def.fields:
                        type_def.fields[field_name] = field_def
    return print_schema(schema)

# Pipeline for schema preprocessing
def preProcess(schema):
    try:
        logger.info("Starting schema processing...")
        schema2 = reorder_schema(schema)
        logger.info("Schema reordered..")
        schema3 = preprocess_stepzen_schema(schema2)
        logger.info("scalar preprocessing done")
        schema4 = update_schema(schema3)
        logger.info("interface merging done")
        return schema4
    except Exception as e:
        logger.warning(f"Error processing schema: {e}")
        return schema

# Apply schema processing
df['final_Schema'] = df['Refined_Schema'].apply(preProcess)

# Apply query cleaning (strip named ops)
df['GT_GQL'] = df['GT_GQL'].apply(strip_operation_name)
df['extracted_graphql'] = df['extracted_graphql'].apply(strip_operation_name)

# Write output
output_file_path = 'raw_schema.csv'
df.to_csv(output_file_path, index=False)
