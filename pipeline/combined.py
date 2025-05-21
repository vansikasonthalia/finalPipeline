
import re
from graphql import build_schema, print_schema

def read_schema_from_file(file_path: str) -> str:
 
    with open(file_path, 'r') as file:
        return file.read()

def preprocess_stepzen_schema(schema: str) -> str:
   
    # StepZen's known custom scalars (from documentation)
    stepzen_scalars = {
        'Date': 'scalar Date',
        'DateTime': 'scalar DateTime',
        'JSON': 'scalar JSON',
        'Secret': 'scalar Secret'
    }

    # 1. Find used scalars in the schema
    scalar_pattern = r'\b(Date|DateTime|JSON|Secret)\b'
    used_scalars = set(re.findall(scalar_pattern, schema))

    # 2. Check existing scalar definitions
    existing_scalars = set(re.findall(r'^scalar\s+(\w+)', schema, re.MULTILINE))

    # 3. Add missing scalar definitions
    missing_definitions = [
        stepzen_scalars[s] for s in used_scalars 
        if s in stepzen_scalars and s not in existing_scalars
    ]

    # 4. Clean up schema artifacts (remove directives like @rest, if any)
    cleaned_schema = re.sub(r'@\w+\(.*?\)', '', schema)  # Remove directives
    cleaned_schema = re.sub(r'\n{3,}', '\n\n', cleaned_schema).strip()  # Normalize spacing

    # 5. Combine final schema (add missing scalars at the top)
    if missing_definitions:
        return '\n'.join(missing_definitions) + '\n\n' + cleaned_schema
    return cleaned_schema

def update_schema(schema_str: str) -> str:

    schema = build_schema(schema_str)
    
    for type_name, type_def in schema.type_map.items():
        if hasattr(type_def, 'interfaces'):
            for interface in type_def.interfaces:
                for field_name, field_def in interface.fields.items():
                    if field_name not in type_def.fields:
                        type_def.fields[field_name] = field_def

    return print_schema(schema)

def write_schema_to_file(schema: str, file_path: str):
   
    with open(file_path, 'w') as output_file:
        output_file.write(schema)

def process_schema(input_file_path: str, output_file_path: str):

    input_schema = read_schema_from_file(input_file_path)
    
    processed_schema = preprocess_stepzen_schema(input_schema)
    
    final_schema = update_schema(processed_schema)
    
    write_schema_to_file(final_schema, output_file_path)
    print(f"Final processed schema has been written to '{output_file_path}'")

if __name__ == "__main__":
    process_schema('schema.graphql', 'schema_final.graphql')
