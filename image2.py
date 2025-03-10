import networkx as nx
import matplotlib.pyplot as plt

# Define the graph data from the given JSON structure
graph_data = {
    "nodes": [
        {"id": "query"}, {"id": "users"}, {"id": "argument:id(10)"},
        {"id": "username"}, {"id": "posts"}, {"id": "title"},
        {"id": "content"}, {"id": "id"}
    ],
    "links": [
        {"source": "query", "target": "users"},
        {"source": "users", "target": "argument:id(10)"},
        {"source": "users", "target": "username"},
        {"source": "users", "target": "posts"},
        {"source": "posts", "target": "title"},
        {"source": "posts", "target": "content"},
        {"source": "posts", "target": "id"},
        {"source": "query", "target": "users"},
        {"source": "users", "target": "argument:id(10)"},
        {"source": "users", "target": "username"}
    ]
}

# Create a directed graph
G = nx.DiGraph()

# Add nodes and edges
for node in graph_data["nodes"]:
    G.add_node(node["id"])
for link in graph_data["links"]:
    G.add_edge(link["source"], link["target"])

# Draw the graph
plt.figure(figsize=(12, 8))
pos = nx.planar_layout(G)  # Layout for visualization

nx.draw(
    G,
    pos,
    with_labels=True,
    node_size=2000,
    node_color="lightblue",
    font_size=18,
    font_weight="bold",
    edge_color="black",
    arrows=True,  # Comma added here
     # Increase edge thickness
    arrowsize=20  # Make arrows more visible
)

plt.title("Graph Representation of the Given JSON Structure")
plt.show()
