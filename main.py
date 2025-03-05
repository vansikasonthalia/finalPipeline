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
        writer.writerow(["Schema", "Query1", "Query2", "Equal", "Extra Fields"])

        for row_dir, schema_file, query1_file, query2_file in processed_files:
            logger.info(f"\n Processing {row_dir}...")

            # Step 1: Processing and Normalizing ASTs
            try:
                query1_ast_path, query2_ast_path = process_queries(schema_file, query1_file, query2_file, row_dir)

                # Skip if either AST path is None (indicating validation errors)
                if query1_ast_path is None or query2_ast_path is None:
                    logger.error(f"Skipping processing for {row_dir} due to validation errors in queries.")
                    continue  # Skip to next set of queries

                logger.debug(f"Generated ASTs: {query1_ast_path}, {query2_ast_path}")
            except Exception as e:
                logger.error(f"Error in Step 1 for {row_dir}: {e}")
                continue  # Skip to next set of queries

            # Step 2: Further Normalizing ASTs
            try:
                n1_ast_path, n2_ast_path = process_asts(query1_ast_path, query2_ast_path, row_dir)
                logger.debug(f"Normalized ASTs: {n1_ast_path}, {n2_ast_path}")
            except Exception as e:
                logger.error(f"Error in Step 2 for {row_dir}: {e}")
                continue  # Skip to next set of queries

            # Step 3: Convert ASTs to Graphs
            try:
                graph1_path, graph2_path = process_normalized_asts(n1_ast_path, n2_ast_path, row_dir)
                logger.debug(f"Generated Graphs: {graph1_path}, {graph2_path}")
            except Exception as e:
                logger.error(f"Error in Step 3 for {row_dir}: {e}")
                continue  # Skip to next set of queries

            # Step 4: Build and Visualize Graphs
            try:
                process_and_visualize_ast(n1_ast_path, graph1_path, os.path.join(row_dir, "graph1_visualization.png"))
                process_and_visualize_ast(n2_ast_path, graph2_path, os.path.join(row_dir, "graph2_visualization.png"))
            except Exception as e:
                logger.error(f"Error in Step 4 for {row_dir}: {e}")
                continue  # Skip to next set of queries

            # Step 5: Detect and Remove Cycles in Graphs
            logger.info("\n Step 5: Detecting and Removing Cycles in Graphs...")
            try:
                process_graphs(graph1_path, graph2_path, row_dir)
            except Exception as e:
                logger.error(f"Error in Step 5 for {row_dir}: {e}")
                continue  # Skip to next set of queries

            # Step 6: Optimizing Query 2 Based on Schema Validation
            schema_path = os.path.join(row_dir, "schema.graphql")  # Load per-row schema
            logger.info("\n Step 6: Optimizing Query 2 Based on Schema Validation...")

            if os.path.exists(schema_path):
                try:
                    newRed.optimize_queries(schema_path, row_dir)  # Ensure function uses correct schema
                    logger.debug(f"Optimized query 2 using schema: {schema_path}")
                except Exception as e:
                    logger.error(f"Error optimizing query for {row_dir}: {e}")
                    continue  # Skip to next set of queries
            else:
                logger.error(f" Error: Schema file {schema_path} not found! Skipping query optimization.")

            # Step 7: Compare Query 1 and Optimized Query 2
            query1_data = os.path.join(row_dir, "graph-1-cleaned-structured.json")  # Path for graph 1
            query2_data = os.path.join(row_dir, "optimized_query2.json")  # Path for graph 2

            try:
                # Load the graph data from the files
                graph1 = load_json(query1_data)
                graph2 = load_json(query2_data)

                if not graph1 or not graph2:
                    logger.error(f"Error loading graphs for row {row_dir}. Skipping comparison.")
                    continue

                # Use the paths of the processed graphs for comparison
                threshold = 2  # Allow up to 2 extra nodes in graph 2
                is_equal = are_adjacent_matrices_equivalent(graph1, graph2, overfetching_threshold=threshold)
                logger.debug(f"Comparison result: Equal={is_equal}")

                # Store comparison result in summary CSV
                writer.writerow([schema_file, query1_file, query2_file, "Equal" if is_equal else "Unequal", "N/A"])
            except Exception as e:
                logger.error(f"Error in Step 7 for {row_dir}: {e}")
                continue  # Skip to next set of queries

            logger.info(f"Completed processing {row_dir}")

    logger.info("\n Comparison summary saved to: %s", summary_csv)
    logger.info("\n All query sets processed successfully!")

if __name__ == "__main__":
    main()
