import os
import csv
import logging
from readcsv import processed_files  # Import processed file paths
from AST import process_queries
from normalizeAST import process_asts
from Graph import process_normalized_asts
from graphNet import process_and_visualize_ast
from cycles import process_graphs
import newRed  # Import newRed module
from compare_jsons import are_adjacent_matrices_equivalent
import json

# Setup logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

summary_csv = os.path.join("results", "comparison_summary.csv")

def read_file_content(file_path):
    """Read and return file content as string with error handling."""
    try:
        with open(file_path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return "CONTENT_UNAVAILABLE"

def load_json(file_path):
    """ Load the JSON data from a file. """
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading file {file_path}: {e}")
        return None

def main():
    os.makedirs("results", exist_ok=True)
    
    with open(summary_csv, "w", newline="") as summary_file:
        writer = csv.writer(summary_file)
        writer.writerow(["Schema Content", "Query1 Content", "Query2 Content", "Equal", "Extra Fields"])

        for row_dir, schema_file, query1_file, query2_file in processed_files:
            logger.info(f"\n Processing {row_dir}...")
            
            try:
                # Get actual content for CSV
                schema_content = read_file_content(schema_file)
                query1_content = read_file_content(query1_file)
                query2_content = read_file_content(query2_file)
                
                # Step 1: Processing and Normalizing ASTs
                query1_ast_path, query2_ast_path = process_queries(schema_file, query1_file, query2_file, row_dir)
                
                if query1_ast_path is None or query2_ast_path is None:
                    logger.error(f"Skipping processing for {row_dir} due to validation errors in queries.")
                    continue

                # Step 2: Further Normalizing ASTs
                n1_ast_path, n2_ast_path = process_asts(query1_ast_path, query2_ast_path, row_dir)

                # Step 3: Convert ASTs to Graphs
                graph1_path, graph2_path = process_normalized_asts(n1_ast_path, n2_ast_path, row_dir)

                # Step 4: Build and Visualize Graphs
                process_and_visualize_ast(n1_ast_path, graph1_path, os.path.join(row_dir, "graph1_visualization.png"))
                process_and_visualize_ast(n2_ast_path, graph2_path, os.path.join(row_dir, "graph2_visualization.png"))

                # Step 5: Detect and Remove Cycles in Graphs
                process_graphs(graph1_path, graph2_path, row_dir)

                # Step 6: Optimizing Query 2 Based on Schema Validation
                schema_path = os.path.join(row_dir, "schema.graphql")
                if os.path.exists(schema_path):
                    newRed.optimize_queries(schema_path, row_dir)

                # Step 7: Compare Query 1 and Optimized Query 2
                query1_data = os.path.join(row_dir, "graph-1-cleaned-structured.json")
                query2_data = os.path.join(row_dir, "optimized_query2.json")
                
                graph1 = load_json(query1_data)
                graph2 = load_json(query2_data)
                
                is_equal = are_adjacent_matrices_equivalent(graph1, graph2, overfetching_threshold=2)

                # Write content to CSV
                writer.writerow([
                    schema_content,
                    query1_content,
                    query2_content,
                    "Equal" if is_equal else "Unequal",
                    "N/A"
                ])

            except Exception as e:
                logger.error(f"Error processing {row_dir}: {e}")
                continue

    logger.info(f"\n Comparison summary saved to: {summary_csv}")
    logger.info("\n All query sets processed successfully!")

if __name__ == "__main__":
    main()
