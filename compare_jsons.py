import json

def load_json(file_path):
    """Load the JSON data from a file."""
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return None

def create_adjacency_matrix(graph):
    """Create an adjacency matrix from a graph JSON, ensuring consistent node order."""
    nodes = graph.get('nodes', [])
    links = graph.get('links', [])

    # Sort nodes by their id to ensure consistent node order
    nodes.sort(key=lambda x: x['id'])

    # Create a mapping from node id to index
    node_to_index = {node['id']: idx for idx, node in enumerate(nodes)}
    
    # Initialize adjacency matrix with all 0s
    adj_matrix = [[0 for _ in range(len(nodes))] for _ in range(len(nodes))]

    # Fill the adjacency matrix based on links
    for link in links:
        source_idx = node_to_index.get(link['source'])
        target_idx = node_to_index.get(link['target'])
        
        if source_idx is not None and target_idx is not None:
            adj_matrix[source_idx][target_idx] = 1

    return adj_matrix

def transitive_closure_from_node(adj_matrix, start_node_idx):
    """Compute the transitive closure from a given start node using Floyd-Warshall algorithm."""
    n = len(adj_matrix)
    # Create a copy of the adjacency matrix to store the transitive closure
    transitive_closure = [row[:] for row in adj_matrix]

    # Apply the Floyd-Warshall algorithm to compute transitive closure
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if transitive_closure[i][k] and transitive_closure[k][j]:
                    transitive_closure[i][j] = 1

    # Ensure only the paths from the 'start_node_idx' are considered
    for i in range(n):
        if not transitive_closure[start_node_idx][i]:
            transitive_closure[i] = [0] * n  # No path from start_node to i

    return transitive_closure

def compare_transitive_closures(graph1, graph2, start_node="query"):
    """Compare the transitive closures of two graphs starting from the 'start_node'."""
    # Create adjacency matrices for both graphs
    matrix1 = create_adjacency_matrix(graph1)
    matrix2 = create_adjacency_matrix(graph2)

    # Get the index of the 'start_node'
    node_list1 = [node['id'] for node in graph1['nodes']]
    node_list2 = [node['id'] for node in graph2['nodes']]

    if start_node not in node_list1 or start_node not in node_list2:
        print(f"Error: '{start_node}' node not found in one or both graphs.")
        return False

    start_node_idx1 = node_list1.index(start_node)
    start_node_idx2 = node_list2.index(start_node)

    # Compute the transitive closure starting from the 'start_node'
    tc1 = transitive_closure_from_node(matrix1, start_node_idx1)
    tc2 = transitive_closure_from_node(matrix2, start_node_idx2)

    # Compare the two transitive closures
    return tc1 == tc2
