import json
import os

def load_ast_from_file(input_file):
    """Load an AST from a JSON file."""
    try:
        with open(input_file, "r") as file:
            return json.load(file)
    except Exception as e:
        raise ValueError(f"Error loading AST from {input_file}: {e}")

def replace_fragment_spreads(ast):
    """Simplify the fragments in queries by replacing fragment spreads with their corresponding fragment definitions."""
    definitions = ast["definitions"]
    
    # Store fragment definitions so they can be used later
    fragment_map = {}

    new_definitions = []
    for definition in definitions:
        if definition["kind"] == "fragment_definition":
            fragment_name = definition["name"]["value"]
            fragment_selection = definition["selection_set"]["selections"]
            fragment_map[fragment_name] = fragment_selection
        else:
            new_definitions.append(definition)

    def replace_spreads(selections):
        """Recursively replace fragment spreads in the selection set."""
        new_selections = []
        for selection in selections:
            if selection["kind"] == "fragment_spread":
                fragment_name = selection["name"]["value"]
                if fragment_name in fragment_map:
                    new_selections.extend(fragment_map[fragment_name])
            else:
                if "selection_set" in selection and selection["selection_set"]:
                    selection["selection_set"]["selections"] = replace_spreads(selection["selection_set"]["selections"])
                new_selections.append(selection)
        return new_selections

    # Process the definitions and replace fragment spreads
    for definition in new_definitions:
        if "selection_set" in definition and definition["selection_set"]:
            definition["selection_set"]["selections"] = replace_spreads(definition["selection_set"]["selections"])

    # Remove type_condition from fragments
    for definition in new_definitions:
        definition.pop("type_condition", None)

    ast["definitions"] = new_definitions
    return ast

def further_normalize_ast(node):
    """Normalize AST structure with safe access patterns"""
    normalized = {
        "operation": node.get("operation", "query"),
        "name": (node.get("name") or {}).get("value", "query"),
        "arguments": {
            arg["name"]["value"]: arg["value"]["value"] 
            for arg in node.get("arguments", [])
        },
        "fields": []
    }

    if "selection_set" in node and node["selection_set"]:
        normalized["fields"] = [
            further_normalize_ast(sel) 
            for sel in node["selection_set"].get("selections", [])
        ]
    
    return normalized



def save_normalized_ast_to_file(ast, output_file):
    """Save the normalized AST to a JSON file."""
    with open(output_file, "w") as file:
        json.dump(ast, file, indent=2)
    print(f"Normalized AST saved to {output_file}")

def process_asts(query1_ast_file, query2_ast_file, output_dir):
    """Process ASTs, replace fragment spreads, and normalize them."""
    try:
        query1_ast = load_ast_from_file(query1_ast_file)
        query2_ast = load_ast_from_file(query2_ast_file)

        query1_ast = replace_fragment_spreads(query1_ast)
        query2_ast = replace_fragment_spreads(query2_ast)

        normalized_query1_ast = further_normalize_ast(query1_ast["definitions"][0])
        normalized_query2_ast = further_normalize_ast(query2_ast["definitions"][0])

        n1_ast_path = os.path.join(output_dir, "n1_ast.json")
        n2_ast_path = os.path.join(output_dir, "n2_ast.json")

        save_normalized_ast_to_file(normalized_query1_ast, n1_ast_path)
        save_normalized_ast_to_file(normalized_query2_ast, n2_ast_path)

        return n1_ast_path, n2_ast_path

    except ValueError as e:
        print(f"Error: {e}")
