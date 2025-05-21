import json
import os
import logging
import networkx as nx
import matplotlib.pyplot as plt
# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler("graph_processing.log")  # Also output to a file
    ]
)

def load_json(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            logging.info(f" Successfully loaded {file_path}")
            return data
    except Exception as e:
        logging.error(f" Error reading file {file_path}: {e}")
        return None
    
def visualize_graph(G, output_image):
    """ Visualize the graph and save it to an image. """
    try:
        logging.debug(f"Visualizing graph and saving to {output_image}")
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(G, seed=42)  # Layout for node positioning
        nx.draw(G, pos, with_labels=True, node_size=3000, node_color="skyblue", font_size=12, font_weight="bold", width=2, edge_color="gray")
        plt.title("Graph Visualization of AST")
        plt.savefig(output_image, format="PNG", bbox_inches="tight")
        plt.close()
        logging.info(f"Graph saved to {output_image}")
    except Exception as e:
        logging.error(f"Error visualizing graph and saving to {output_image}: {e}")

def detect_cycles(graph):
    """Detect cycles in the directed graph using DFS."""
    edges = graph["links"]
    adjacency_list = {}

    # Build adjacency list
    for edge in edges:
        source, target = edge["source"], edge["target"]
        if source not in adjacency_list:
            adjacency_list[source] = []
        adjacency_list[source].append(target)

    visited = set()
    stack = set()
    cycles = []

    def dfs(node, path):
        """Depth-First Search to detect cycles."""
        if node in stack:  # Cycle detected
            cycle_index = path.index(node)
            cycles.append(path[cycle_index:])  # Store only the cycle part
            logging.debug(f" Detected cycle: {path[cycle_index:]}")
            return

        if node in visited:
            return

        visited.add(node)
        stack.add(node)

        for neighbor in adjacency_list.get(node, []):
            dfs(neighbor, path + [neighbor])

        stack.remove(node)

    for node in adjacency_list:
        if node not in visited:
            dfs(node, [node])

    logging.info(f" Detected cycles: {len(cycles)} cycle(s) found.")
    return cycles

def remove_schema_redundant_cycles(graph, schema_rules):
    """Remove cycles that are redundant based on the schema rules."""
    cycles = detect_cycles(graph)
    filtered_edges = []
    removed_edges = []

    # Convert edges to set for easy lookup
    edge_set = {(edge["source"], edge["target"]) for edge in graph["links"]}

    for edge in graph["links"]:
        source, target = edge["source"], edge["target"]

        # Remove only schema-defined redundant cycles
        if (source, target) in schema_rules["redundant_cycles"]:
            if any(target in cycle and source in cycle for cycle in cycles):
                removed_edges.append(edge)
                continue  # Skip adding this edge (remove cycle)

        filtered_edges.append(edge)

    # Return the updated graph with cycles removed
    graph["links"] = filtered_edges
    logging.info(f" Removed {len(removed_edges)} redundant cycles based on schema rules.")
    return graph, removed_edges

def build_hierarchical_structure(graph):
    """Convert graph into a nested GraphQL-style structure."""
    node_map = {node["id"]: {"name": node["id"], "fields": []} for node in graph["nodes"]}

    for edge in graph["links"]:
        source, target = edge["source"], edge["target"]
        if "fields" not in node_map[source]:
            node_map[source]["fields"] = []
        node_map[source]["fields"].append(node_map[target])

    # Find the root node(s) (nodes that are never targets)
    all_targets = {edge["target"] for edge in graph["links"]}
    root_nodes = [node_map[node["id"]] for node in graph["nodes"] if node["id"] not in all_targets]

    return {"name": "MyQuery", "fields": root_nodes}

def process_graphs(graph1_path, graph2_path, output_dir):
    """Process both graphs to remove schema-redundant cycles and save cleaned versions."""
    # Load graphs
    graph1 = load_json(graph1_path)
    graph2 = load_json(graph2_path)

    if graph1 is None or graph2 is None:
        logging.error(" Error: One of the graphs could not be loaded.")
        return

    # Define schema rules (hardcoded based on your schema)
    schema_rules = {
        "redundant_cycles": {("posts", "users")}  # Remove 'posts → users' since it always refers to the same user
    }

    # Process both graphs
    graph1_cleaned, removed_edges1 = remove_schema_redundant_cycles(graph1, schema_rules)
    graph2_cleaned, removed_edges2 = remove_schema_redundant_cycles(graph2, schema_rules)

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Define correct file paths in the row directory
    graph1_cleaned_path = os.path.join(output_dir, "graph-1-cleaned.json")
    graph2_cleaned_path = os.path.join(output_dir, "graph-2-cleaned.json")
    graph1_structured_path = os.path.join(output_dir, "graph-1-cleaned-structured.json")
    graph2_structured_path = os.path.join(output_dir, "graph-2-cleaned-structured.json")

    # Save the cleaned graphs (standard format)
    with open(graph1_cleaned_path, "w") as f:
        json.dump(graph1_cleaned, f, indent=2)
        logging.info(f" Saved cleaned graph 1 to {graph1_cleaned_path}")

    with open(graph2_cleaned_path, "w") as f:
        json.dump(graph2_cleaned, f, indent=2)
        logging.info(f" Saved cleaned graph 2 to {graph2_cleaned_path}")

    # Convert to hierarchical format
    graph1_structured = build_hierarchical_structure(graph1_cleaned)
    graph2_structured = build_hierarchical_structure(graph2_cleaned)

    # Save hierarchical JSON format
    with open(graph1_structured_path, "w") as f:
        json.dump(graph1_structured, f, indent=2)
        logging.info(f" Saved structured graph 1 to {graph1_structured_path}")

    with open(graph2_structured_path, "w") as f:
        json.dump(graph2_structured, f, indent=2)
        logging.info(f" Saved structured graph 2 to {graph2_structured_path}")

    logging.info(" Cycles removed and graphs saved:")
    logging.info(f"   - {graph1_cleaned_path}")
    logging.info(f"   - {graph2_cleaned_path}")
    logging.info(f"   - {graph1_structured_path}")
    logging.info(f"   - {graph2_structured_path}")
    logging.info(f" Removed edges (Graph 1): {removed_edges1}")
    logging.info(f" Removed edges (Graph 2): {removed_edges2}")

if __name__ == "__main__":
    process_graphs("graph-1.json", "graph-2.json", "results/")
