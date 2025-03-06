import json
import re
import os
import yaml
import logging
from graphql import build_schema

# Initialize logging
logging.basicConfig(
    level=logging.INFO,  # Set logging level to INFO for general log messages
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format with timestamp
    handlers=[logging.StreamHandler()]  # Output log to console
)

def load_json(file_path):
    """ Load JSON data from a file. """
    try:
        with open(file_path, "r") as file:
            logging.info(f" Successfully loaded JSON file: {file_path}")
            return json.load(file)
    except Exception as e:
        logging.error(f" Error reading file {file_path}: {e}")
        return None

def load_schema(schema_path):
    """ Load and parse the GraphQL schema from the specified path. """
    if not os.path.exists(schema_path):
        logging.error(f" Error: Schema file {schema_path} not found! Skipping schema validation.")
        return None
    try:
        with open(schema_path, "r") as file:
            logging.info(f" Successfully loaded schema from {schema_path}")
            return build_schema(file.read())
    except Exception as e:
        logging.error(f" Error loading schema from {schema_path}: {e}")
        return None

def load_config(config_path="config.yaml"):
    """ Load configuration from YAML file. """
    if not os.path.exists(config_path):
        logging.warning(f"Configuration file {config_path} not found. Using default settings.")
        return {}
    try:
        with open(config_path, "r") as file:
            logging.info(f"Successfully loaded configuration from {config_path}")
            return yaml.safe_load(file)
    except Exception as e:
        logging.error(f" Error loading config file {config_path}: {e}")
        return {}

def extract_query_types(schema):
    """ Extract all query field names and their return types from the schema. """
    query_type = schema.get_type("Query")
    query_fields = query_type.fields
    return {normalize_field_name(field_name): str(query_fields[field_name].type) for field_name in query_fields}

def normalize_field_name(field_name):
    """ Remove arguments from field names for comparison. """
    return re.sub(r"\(.*?\)", "", field_name)

def extract_all_field_names(graph):
    """ Recursively extract all field names from a query JSON structure. """
    field_names = set()

    def traverse(node):
        normalized_name = normalize_field_name(node["name"])
        field_names.add(normalized_name)
        if "fields" in node and node["fields"]:
            for child in node["fields"]:
                traverse(child)

    for entry in graph.get("fields", []):
        traverse(entry)

    return field_names

def find_equivalent_endpoints(schema, query1_fields, query2_fields):
    """ Find redundant endpoints in query2 that reference the same type as an endpoint in query1. """
    query_types = extract_query_types(schema)
    replacements = {}

    for q2_endpoint in query2_fields:
        q2_type = query_types.get(q2_endpoint)

        for q1_endpoint in query1_fields:
            q1_type = query_types.get(q1_endpoint)

            if q1_type and q2_type and q1_type == q2_type:
                replacements[q2_endpoint] = q1_endpoint
                logging.info(f" Found equivalent endpoints: {q2_endpoint} → {q1_endpoint}")

    return replacements

def replace_redundant_endpoints(graph, replacements):
    """ Replace redundant fields in query2 based on schema-verified equivalence. """
    def traverse(node):
        normalized_name = normalize_field_name(node["name"])
        if normalized_name in replacements:
            logging.info(f" Replacing {node['name']} → {replacements[normalized_name]}")
            node["name"] = replacements[normalized_name]
        if "fields" in node and node["fields"]:
            for child in node["fields"]:
                traverse(child)

    for entry in graph.get("fields", []):
        traverse(entry)

    return graph

def save_json(data, file_path):
    """ Save the optimized query graph as JSON. """
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=2)
        logging.info(f" Optimized query saved as {file_path}")
    except Exception as e:
        logging.error(f" Error saving file {file_path}: {e}")
    

def optimize_queries(schema_path, row_dir):
    """ Optimize Query 2 using schema validation and save the result in the respective row directory. """
    
    schema = load_schema(schema_path)
    if schema is None:
        logging.error(f" Skipping query optimization for {row_dir} due to missing schema.")
        return

    # Dynamically set query file paths
    query1_path = os.path.join(row_dir, "graph-1-cleaned-structured.json")
    query2_path = os.path.join(row_dir, "graph-2-cleaned-structured.json")
    optimized_query_path = os.path.join(row_dir, "optimized_query2.json")

    query1_graph = load_json(query1_path)
    query2_graph = load_json(query2_path)

    if query1_graph is None or query2_graph is None:
        logging.error(f" Skipping query optimization for {row_dir} due to missing query JSON.")
        return

    query1_fields = extract_all_field_names(query1_graph)
    query2_fields = extract_all_field_names(query2_graph)

    logging.info(f" Query1 Fields: {query1_fields}")
    logging.info(f" Query2 Fields: {query2_fields}")

    replacements = find_equivalent_endpoints(schema, query1_fields, query2_fields)

    if not replacements:
        logging.info(" No redundant endpoints found. Saving unmodified Query 2.")

    optimized_query2 = replace_redundant_endpoints(query2_graph, replacements) if replacements else query2_graph

    save_json(optimized_query2, optimized_query_path)
    # Convert and save graph structure
    optimized_graph = convert_to_graph_structure(optimized_query2)
    graph_output_path = os.path.join(row_dir, "optimized_links2.json")
    save_json(optimized_graph, graph_output_path)

def convert_to_graph_structure(optimized_query):
    nodes = []
    links = []
    node_ids = set()

    def add_node(node_id):
        if node_id not in node_ids:
            nodes.append({"id": node_id})
            node_ids.add(node_id)

    def traverse_fields(parent, fields):
        for field in fields:
            # Preserve full argument syntax with parentheses
            if field["name"].startswith("argument:"):
                clean_name = field["name"].replace("argument:", "argument_")  # Convert colon to underscore
                clean_name = re.sub(r'_([a-zA-Z]+)\(', r':\1(', clean_name)  # Restore colon after argument prefix
            else:
                # Clean non-argument fields normally
                clean_name = re.sub(r'\(.*?\)', '', field["name"])
            
            add_node(clean_name)
            links.append({"source": parent, "target": clean_name})
            
            if field.get("fields"):
                traverse_fields(clean_name, field["fields"])

    add_node("query")
    if "fields" in optimized_query:
        for top_field in optimized_query["fields"]:
            if top_field["name"] == "query":
                traverse_fields("query", top_field.get("fields", []))
    
    return {"nodes": nodes, "links": links}
