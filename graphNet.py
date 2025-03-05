import json
import networkx as nx
import matplotlib.pyplot as plt
import logging
from utils import setup_logger

# Set up the logger
logger = setup_logger("graphNet_processing.log")

def load_normalized_ast(input_file):
    """ Load a normalized AST from a JSON file. """
    try:
        logger.debug(f"Loading AST from file: {input_file}")
        with open(input_file, "r") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading normalized AST from {input_file}: {e}")
        raise ValueError(f"Error loading normalized AST from {input_file}: {e}")

# The rest of the functions follow this pattern



def build_graph_from_ast(ast):
    """ Build a graph from a given AST where fields and arguments are separate nodes. """
    G = nx.DiGraph()

    def add_node_and_edges(parent_node, node):
        # Add the current node to the graph
        G.add_node(node['name'])
        if parent_node:
            G.add_edge(parent_node, node['name'])

        # If arguments exist, treat them as separate nodes
        if 'arguments' in node:
            for arg_name, arg_value in node['arguments'].items():
                arg_node_name = f"argument:{arg_name}({arg_value})"
                G.add_node(arg_node_name)
                G.add_edge(node['name'], arg_node_name)

        # Process child fields recursively
        if 'fields' in node:
            for field in node['fields']:
                add_node_and_edges(node['name'], field)

    # Start building from the root (the 'fields' of the query)
    for field in ast.get('fields', []):
        add_node_and_edges(None, field)

    logger.debug("Graph construction completed.")
    return G


def save_graph_to_json(G, output_file):
    """ Save the graph to a JSON file. """
    try:
        graph_data = nx.readwrite.json_graph.node_link_data(G)
        with open(output_file, "w") as file:
            json.dump(graph_data, file, indent=2)
        logger.info(f"Graph saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving graph to {output_file}: {e}")


def visualize_graph(G, output_image):
    """ Visualize the graph and save it to an image. """
    try:
        logger.debug(f"Visualizing graph and saving to {output_image}")
        plt.figure(figsize=(10, 8))
        pos = nx.spring_layout(G, seed=42)  # Layout for node positioning
        nx.draw(G, pos, with_labels=True, node_size=3000, node_color="skyblue", font_size=12, font_weight="bold", width=2, edge_color="gray")
        plt.title("Graph Visualization of AST")
        plt.savefig(output_image, format="PNG", bbox_inches="tight")
        plt.close()
        logger.info(f"Graph saved to {output_image}")
    except Exception as e:
        logger.error(f"Error visualizing graph and saving to {output_image}: {e}")


def process_and_visualize_ast(input_file, output_graph_file, output_image_file):
    """ Process AST from JSON, build graph, save the result, and visualize it. """
    try:
        logger.info(f"Processing AST from {input_file}")
        # Load AST from the input JSON
        ast = load_normalized_ast(input_file)

        # Build the graph
        graph = build_graph_from_ast(ast)

        # Save the graph to JSON
        save_graph_to_json(graph, output_graph_file)

        # Visualize the graph and save the output image
        visualize_graph(graph, output_image_file)

    except Exception as e:
        logger.error(f"Error processing AST: {e}")


if __name__ == "__main__":
    # Input files for ASTs
    n1_ast_path = "n1_ast.json"
    n2_ast_path = "n2_ast.json"

    # Process the first AST (n1_ast.json)
    process_and_visualize_ast(n1_ast_path, "graph-1.json", "graph1_visualization.png")

    # Process the second AST (n2_ast.json)
    process_and_visualize_ast(n2_ast_path, "graph-2.json", "graph2_visualization.png")
