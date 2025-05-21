import os
import csv
import logging
from pipeline.readcsv import processed_files  # Import processed file paths
from pipeline.AST import process_queries
from pipeline.normalizeAST import process_asts
from pipeline.Graph import process_normalized_asts
from pipeline.graphNet import process_and_visualize_ast
from pipeline.cycles import process_graphs
import pipeline.newRed as newRed  # Import newRed module
from pipeline.compare_jsons import compare_transitive_closures
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
        # Add a "Comments" column to specify errors for each row
        writer.writerow(["Schema Content", "Query1 Content", "Query2 Content", "Equal", "Extra Fields", "Comments"])

        for row_dir, schema_file, query1_file, query2_file in processed_files:
            logger.info(f"\n Processing {row_dir}...")
            
            try:
                # Initialize comments for this row
                comments = ""

                # Get actual content for CSV
                schema_content = read_file_content(schema_file)
                query1_content = read_file_content(query1_file)
                query2_content = read_file_content(query2_file)
                
                # Step 1: Processing and Normalizing ASTs
                query1_ast_path, query2_ast_path = process_queries(schema_file, query1_file, query2_file, row_dir)
                
                if query1_ast_path is None or query2_ast_path is None:
                    comments = f"Validation errors in queries for {row_dir}."
                    raise ValueError(comments)

                # Step 2: Further Normalizing ASTs
                n1_ast_path, n2_ast_path = process_asts(query1_ast_path, query2_ast_path, row_dir)

                # Step 3: Convert ASTs to Graphs
                graph1_path, graph2_path = process_normalized_asts(n1_ast_path, n2_ast_path, row_dir)

                # Step 4: Build and Visualize Graphs
                process_and_visualize_ast(n1_ast_path, os.path.join(row_dir, "graph-1.json"), os.path.join(row_dir, "graph1_visualization.png"))
                process_and_visualize_ast(n2_ast_path, os.path.join(row_dir, "graph-2.json"), os.path.join(row_dir, "graph2_visualization.png"))

                # Step 5: Detect and Remove Cycles in Graphs
                process_graphs(os.path.join(row_dir, "graph-1.json"), os.path.join(row_dir, "graph-2.json"), row_dir)

                # Step 6: Optimizing Query 2 Based on Schema Validation
                schema_path = os.path.join(row_dir, "schema.graphql")
                if os.path.exists(schema_path):
                    newRed.optimize_queries(schema_path, row_dir)

                # Step 7: Compare Query 1 and Optimized Query 2
                query1_data = os.path.join(row_dir, "graph-1-cleaned.json")
                query2_data = os.path.join(row_dir, "optimized_links2.json")

                graph1 = load_json(query1_data)
                graph2 = load_json(query2_data)

                if graph1 is None or graph2 is None:
                    comments = f"Error loading JSON data for {row_dir}."
                    raise ValueError(comments)

                is_equal = compare_transitive_closures(graph1, graph2, start_node="query")

                # Write content to CSV
                writer.writerow([
                    schema_content,
                    query1_content,
                    query2_content,
                    "Equal" if is_equal else "Unequal",
                    "N/A",
                    comments or "No Errors"
                ])

            except Exception as e:
                logger.error(f"Error processing {row_dir}: {e}")
                
                # Write error details to the CSV's Comments column for this row
                writer.writerow([
                    schema_content if 'schema_content' in locals() else "N/A",
                    query1_content if 'query1_content' in locals() else "N/A",
                    query2_content if 'query2_content' in locals() else "N/A",
                    "N/A",
                    "N/A",
                    str(e)
                ])

    logger.info(f"\n Comparison summary saved to: {summary_csv}")
    logger.info("\n All query sets processed successfully!")

if __name__ == "__main__":
    main()
