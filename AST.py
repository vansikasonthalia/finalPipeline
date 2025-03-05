import logging
from graphql import parse, build_schema, validate 
import json
import sys
import os

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Log format
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to console
        logging.FileHandler("process_queries.log")  # Log to a file
    ]
)

def load_file(file_path):
    """Loads a file and returns its content."""
    try:
        logging.info(f"Attempting to load file: {file_path}")
        with open(file_path, "r") as file:
            content = file.read().strip()
        logging.info(f"Successfully loaded file: {file_path}")
        return content
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        raise ValueError(f"Error reading file {file_path}: {e}")

def validate_and_parse_query(schema_content, query_content):
    """Validate and parse a GraphQL query."""
    logging.info("Validating and parsing query...")
    schema = build_schema(schema_content)
    query_ast = parse(query_content)

    # Validate the query
    validation_errors = validate(schema, query_ast)
    if validation_errors:
        logging.error(" Validation errors detected:")
        for error in validation_errors:
            logging.error(f"   - {error.message}")
            logging.error("Continuing to next set of queries despite validation errors.")

        return None  # Exit the script with an error status

    logging.info("Query successfully validated and parsed.")
    return query_ast.to_dict()

def normalize_aliases(node):
    """Normalize aliases in the query AST."""
    if node["kind"] == "field" and node.get("alias"):
        node["alias"] = None
    if "selection_set" in node and node["selection_set"]:
        for selection in node["selection_set"]["selections"]:
            normalize_aliases(selection)

def resolve_fragments(node, fragments):
    """Resolve fragments in the query AST."""
    if node["kind"] == "fragment_spread":
        fragment_name = node["name"]["value"]
        if fragment_name in fragments:
            return fragments[fragment_name]["selection_set"]
        else:
            raise ValueError(f"Fragment {fragment_name} not found.")
    elif "selection_set" in node and node["selection_set"]:
        resolved_selections = []
        for selection in node["selection_set"]["selections"]:
            if selection["kind"] == "fragment_spread":
                fragment_selections = resolve_fragments(selection, fragments)
                resolved_selections.extend(fragment_selections["selections"])
            else:
                resolved_selections.append(selection)
        node["selection_set"]["selections"] = resolved_selections
    return node

def normalize_query_ast(query_ast):
    """Normalize the query AST by handling aliases and fragments."""
    fragments = {
        definition["name"]["value"]: definition
        for definition in query_ast["definitions"]
        if definition["kind"] == "fragment_definition"
    }

    for definition in query_ast["definitions"]:
        if definition["kind"] == "operation_definition":
            normalize_aliases(definition)
            resolve_fragments(definition, fragments)

def save_ast_to_file(ast, output_file):
    """Save the AST to a file."""
    try:
        logging.info(f"Saving AST to {output_file}...")
        with open(output_file, "w") as file:
            json.dump(ast, file, indent=2)
        logging.info(f"AST successfully saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving AST to {output_file}: {e}")

def process_queries(schema_file, query1_file, query2_file, output_dir):
    """Process queries, validate ASTs, and save them in the correct directory."""
    try:
        logging.info("Processing queries...")

        schema_content = load_file(schema_file)
        query1_content = load_file(query1_file)
        query2_content = load_file(query2_file)

        logging.info("Validating and parsing Query 1...")
        query1_ast = validate_and_parse_query(schema_content, query1_content)
        if query1_ast is None:
            logging.error(f"Skipping Query 1 due to validation errors.")
            return None, None  # Return None to indicate failur
        normalize_query_ast(query1_ast)

        logging.info("Validating and parsing Query 2...")
        query2_ast = validate_and_parse_query(schema_content, query2_content)
        if query2_ast is None:
            logging.error(f"Skipping Query 2 due to validation errors.")
            return None, None  # Return None to indicate failure
        
        normalize_query_ast(query2_ast)

        query1_ast_path = os.path.join(output_dir, "query1_ast.json")
        query2_ast_path = os.path.join(output_dir, "query2_ast.json")

        save_ast_to_file(query1_ast, query1_ast_path)
        save_ast_to_file(query2_ast, query2_ast_path)

        return query1_ast_path, query2_ast_path

    except ValueError as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    schema_path = "schema.graphql"
    query1_path = "query1.graphql"
    query2_path = "query2.graphql"

    process_queries(schema_path, query1_path, query2_path)
