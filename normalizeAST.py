import json
import os
from typing import List, Dict, Set

class CircularFragmentError(ValueError):
    pass

def load_ast_from_file(input_file):
    """Load an AST from a JSON file."""
    try:
        with open(input_file, "r") as file:
            return json.load(file)
    except Exception as e:
        raise ValueError(f"Error loading AST from {input_file}: {e}")

def inline_fragments(ast: Dict, max_depth: int = 20) -> Dict:
    """Simplify fragments in queries by recursively inlining fragment spreads."""
    definitions = ast["definitions"]

    # Collect fragment definitions into a map
    fragment_map = {
        definition["name"]["value"]: definition["selection_set"]["selections"]
        for definition in definitions
        if definition["kind"] == "fragment_definition"
    }

    def process_selections(
        selections: List[Dict],
        current_fragments: Set[str] = None,
        depth: int = 0
    ) -> List[Dict]:
        """Recursively process selections and inline fragments."""
        current_fragments = current_fragments or set()
        processed = []

        if depth > max_depth:
            raise CircularFragmentError(f"Maximum expansion depth {max_depth} exceeded")

        for selection in selections:
            if selection["kind"] == "fragment_spread":
                fragment_name = selection["name"]["value"]

                if fragment_name in current_fragments:
                    raise CircularFragmentError(
                        f"Circular fragment reference detected: {fragment_name}"
                    )

                if fragment_name in fragment_map:
                    new_fragments = current_fragments | {fragment_name}
                    processed.extend(
                        process_selections(fragment_map[fragment_name], new_fragments, depth + 1)
                    )
                else:
                    print(f"Warning: Fragment definition for '{fragment_name}' not found!")
            elif "selection_set" in selection and selection["selection_set"]:
                selection["selection_set"]["selections"] = process_selections(
                    selection["selection_set"]["selections"], current_fragments, depth
                )
                processed.append(selection)
            else:
                processed.append(selection)

        return processed

    # Process all definitions and inline fragments
    new_definitions = []
    for definition in definitions:
        if definition["kind"] != "fragment_definition":
            if "selection_set" in definition and definition["selection_set"]:
                try:
                    definition["selection_set"]["selections"] = process_selections(
                        definition["selection_set"]["selections"]
                    )
                except CircularFragmentError as e:
                    raise ValueError(f"Error in operation {definition['name']['value']}: {str(e)}") from e
            new_definitions.append(definition)

    ast["definitions"] = new_definitions
    return ast

def further_normalize_ast(node):
    """Normalize AST structure with safe access patterns."""
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
    """Process ASTs, inline fragments, and normalize them."""
    try:
        # Load the provided AST files
        query1_ast = load_ast_from_file(query1_ast_file)
        query2_ast = load_ast_from_file(query2_ast_file)

        # Inline fragments in both query ASTs
        query1_ast = inline_fragments(query1_ast)
        query2_ast = inline_fragments(query2_ast)

        # Further normalize the ASTs (you can modify this normalization logic as per your need)
        normalized_query1_ast = further_normalize_ast(query1_ast["definitions"][0])
        normalized_query2_ast = further_normalize_ast(query2_ast["definitions"][0])

        # Define output paths for the normalized ASTs
        n1_ast_path = os.path.join(output_dir, "n1_ast.json")
        n2_ast_path = os.path.join(output_dir, "n2_ast.json")

        # Save the normalized ASTs to the output directory
        save_normalized_ast_to_file(normalized_query1_ast, n1_ast_path)
        save_normalized_ast_to_file(normalized_query2_ast, n2_ast_path)

        # Return the paths to the normalized AST files
        return n1_ast_path, n2_ast_path

    except ValueError as e:
        print(f"Error: {e}")

# Example usage
if __name__ == "__main__":
    sample_query_file_1 = "query1.json"
    sample_query_file_2 = "query2.json"
    output_directory = "./output"

    try:
        process_asts(sample_query_file_1, sample_query_file_2, output_directory)
    except Exception as e:
        print(f"Processing failed: {e}")
