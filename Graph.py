import json
import networkx as nx
import matplotlib.pyplot as plt
import os
import logging

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture more detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Logs to the console
    ]
)

def load_normalized_ast(input_file):
    """ Load a normalized AST from a JSON file. """
    try:
        logging.info(f"Loading normalized AST from file: {input_file}")
        with open(input_file, "r") as file:
            ast = json.load(file)
        logging.info(f"Successfully loaded normalized AST from file: {input_file}")
        return ast
    except Exception as e:
        logging.error(f"Error loading normalized AST from {input_file}: {e}")
        raise ValueError(f"Error loading normalized AST from {input_file}: {e}")

def ast_to_graph_json(ast):
    """ Convert the normalized AST into a graph structure with arguments as separate nodes. """
    def build_graph(node):
        logging.debug(f"Processing node: {node['name']}")  # Log each node being processed
        graph_node = {
            "name": node["name"]
        }

        # If arguments are present, treat them as separate nodes and add them to the graph
        if "arguments" in node:
            graph_node["arguments"] = {}
            for arg_name, arg_value in node["arguments"].items():
                logging.debug(f"Adding argument: {arg_name} = {arg_value} for node: {node['name']}")  # Log each argument
                # Create an argument node that is distinct and add it to the graph
                argument_node_name = f"argument:{arg_name}({arg_value})"
                graph_node["arguments"][arg_name] = {
                    "name": argument_node_name,
                    "value": arg_value
                }

        # Process child fields (recursive)
        if "fields" in node:
            graph_node["children"] = [build_graph(child) for child in node["fields"]]
        
        logging.debug(f"Finished processing node: {node['name']}")
        return graph_node

    logging.info(f"Starting AST to graph conversion for: {ast['name']}")  # Log the start of conversion
    graph = build_graph(ast)
    logging.info(f"AST to graph conversion completed for: {ast['name']}")  # Log the completion
    return graph


def save_graph_to_json(graph, output_file):
    """ Save the graph to a JSON file. """
    try:
        logging.info(f"Saving graph to file: {output_file}")
        with open(output_file, "w") as file:
            json.dump(graph, file, indent=2)
        logging.info(f"Graph saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving graph to {output_file}: {e}")
        raise  # Re-raise the exception after logging


def process_normalized_asts(n1_ast_file, n2_ast_file, output_dir):
    """Processes ASTs and converts them into graphs."""
    try:
        logging.info(f"Loading normalized AST from file: {n1_ast_file}")
        normalized_query1_ast = load_normalized_ast(n1_ast_file)
        logging.info(f"Loaded normalized AST from file: {n1_ast_file}")

        logging.info(f"Loading normalized AST from file: {n2_ast_file}")
        normalized_query2_ast = load_normalized_ast(n2_ast_file)
        logging.info(f"Loaded normalized AST from file: {n2_ast_file}")

        # Add the root query operation to the graphs for both ASTs
        logging.info("Converting first AST to graph")
        graph1 = ast_to_graph_json(normalized_query1_ast)
        logging.info("First AST converted to graph")

        logging.info("Converting second AST to graph")
        graph2 = ast_to_graph_json(normalized_query2_ast)
        logging.info("Second AST converted to graph")

        # Save the graphs to JSON
        graph1_path = os.path.join(output_dir, "graph1.json")
        graph2_path = os.path.join(output_dir, "graph2.json")

        logging.info(f"Saving graph 1 to file: {graph1_path}")
        save_graph_to_json(graph1, graph1_path)
        logging.info(f"Graph 1 saved to file: {graph1_path}")

        logging.info(f"Saving graph 2 to file: {graph2_path}")
        save_graph_to_json(graph2, graph2_path)
        logging.info(f"Graph 2 saved to file: {graph2_path}")

        return graph1_path, graph2_path

    except ValueError as e:
        logging.error(f"Error processing normalized ASTs: {e}")
        raise  # Re-raise the exception after logging


def visualize_graph(graph, output_image):
    """ Visualize the graph with improved clarity and structure. """
    def add_edges_to_graph(graph_obj, node, parent=None):
        if isinstance(node, str):
            graph_obj.add_edge(parent, node)
        elif isinstance(node, dict):
            if parent:
                graph_obj.add_edge(parent, node["name"])
            for child in node.get("children", []):
                add_edges_to_graph(graph_obj, child, node["name"])

            # Add edges for arguments (arguments as nodes)
            if "arguments" in node:
                for arg_name, arg in node["arguments"].items():
                    graph_obj.add_edge(node["name"], f"{arg['name']}")

    G = nx.DiGraph()
    add_edges_to_graph(G, graph)

    plt.figure(figsize=(20, 16))  # Increased figure size for better spacing
    pos = nx.spring_layout(G, seed=42, k=0.5)  # Adjust "k" to control node spacing

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=3500,  # Adjusted node size for better visibility
        node_color="lightblue",
        font_size=14,
        font_weight="bold",
        width=2,
        edge_color="gray",  # Lighter color for edges
        arrows=True,
        font_color="black",  # Text color
        alpha=0.7,  # Slight transparency for clarity
        style="solid",  # Solid edges for consistency
    )

    plt.title("Graph Visualization", fontsize=18)
    try:
        plt.savefig(output_image, format="PNG", bbox_inches="tight")
        plt.close()
        logging.info(f"Graph visualization saved to {output_image}")
    except Exception as e:
        logging.error(f"Error saving graph visualization to {output_image}: {e}")
