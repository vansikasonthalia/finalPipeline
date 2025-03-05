import numpy as np
import json


def convert_to_adjacency_matrix(graph):
    """
    Converts a graph represented as a JSON object into an adjacency matrix.
    Handles nested fields correctly by flattening the graph structure.
    """
    # Collect all unique field names (including nested fields)
    field_names = []
    def collect_field_names(fields):
        for field in fields:
            field_names.append(field["name"])
            if "fields" in field and field["fields"]:
                collect_field_names(field["fields"])

    collect_field_names(graph["fields"])

    # Create a mapping from field names to indices
    field_index = {field_names[i]: i for i in range(len(field_names))}

    # Initialize an adjacency matrix with 0s
    adj_matrix = np.zeros((len(field_names), len(field_names)), dtype=int)

    # Populate the adjacency matrix based on field relationships (edges)
    def populate_adjacency_matrix(fields):
        for field in fields:
            field_id = field_index[field["name"]]
            if "fields" in field and field["fields"]:
                for nested_field in field["fields"]:
                    nested_id = field_index[nested_field["name"]]
                    adj_matrix[field_id][nested_id] = 1  # There is a directed edge from field to nested_field
                    populate_adjacency_matrix([nested_field])  # Recursively process nested fields

    populate_adjacency_matrix(graph["fields"])
    
    return adj_matrix, field_names

def are_adjacent_matrices_equivalent(graph1, graph2, overfetching_threshold=0):
    """
    Compares two graphs represented as adjacency matrices and allows extra nodes in graph 2 up to the overfetching threshold.
    """
    # Convert both graphs to adjacency matrices
    matrix1, field_names1 = convert_to_adjacency_matrix(graph1)
    matrix2, field_names2 = convert_to_adjacency_matrix(graph2)

    # If the graphs have different numbers of fields, check if the difference is within the threshold
    if len(field_names1) != len(field_names2):
        extra_nodes = abs(len(field_names2) - len(field_names1))
        if extra_nodes > overfetching_threshold:
            return False  # Too many extra nodes in graph2
        # Adjust matrices for extra nodes if threshold is met (extend matrices with zeroes)
        if len(field_names2) > len(field_names1):
            matrix1 = np.pad(matrix1, ((0, len(field_names2)-len(field_names1)), (0, 0)), 'constant')
            field_names1.extend(field_names2[len(field_names1):])
        else:
            matrix2 = np.pad(matrix2, ((0, len(field_names1)-len(field_names2)), (0, 0)), 'constant')
            field_names2.extend(field_names1[len(field_names2):])

    # Compare adjacency matrices
    return np.array_equal(matrix1, matrix2)

