import yaml
import pandas as pd
import os
from datetime import datetime
import logging
from utils import setup_logger
import csv


# Set up the logger
logger = setup_logger("readcsv_processing.log")

# Load configuration
yaml_file = "config.yaml"
try:
    with open(yaml_file, "r") as file:
        config = yaml.safe_load(file)
    logger.info(f"Configuration loaded successfully from {yaml_file}")
except Exception as e:
    logger.error(f"Error loading configuration file {yaml_file}: {e}")
    config = {}

csv_file = config.get("csv_location", "")
output_dir = config.get("output_dir", "")

if not csv_file:
    logger.error("CSV location not found in config.")
    raise ValueError("CSV location not found in config.")

if not output_dir:
    logger.error("Output directory not found in config.")
    raise ValueError("Output directory not found in config.")

logger.info(f"📂 Looking for CSV at: {csv_file}")

# Read CSV file
try:
    df = pd.read_csv(csv_file)
    logger.info(f"CSV file {csv_file} read successfully.")
except Exception as e:
    logger.error(f"Error reading CSV file {csv_file}: {e}")
    raise

# Create output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    logger.info(f"Output directory {output_dir} created.")

# The rest of the code follows this pattern
# In readcsv.py - Add threshold column
def process_csv(input_csv):
    processed = []
    with open(input_csv, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        for idx, row in enumerate(reader):
            if len(row) != 4:
                raise ValueError(f"Invalid row {idx+1}: Expected 4 columns (schema, query1, query2, threshold), got {len(row)}")
            
            schema_file, query1_file, query2_file, threshold = row
            row_dir = os.path.join("results", f"row_{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            processed.append((row_dir, schema_file, query1_file, query2_file, int(threshold)))
    return processed

def clean_string(value):
    """Remove leading and trailing quotes from strings."""
    if isinstance(value, str):
        return value.strip('"')
    return str(value)

# Store processed file paths
processed_files = []

for index, row in df.iterrows():
    # Generate timestamped unique directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    row_dir = os.path.join(output_dir, f"row_{index + 1}_{timestamp}")
    os.makedirs(row_dir, exist_ok=True)

    # Extract and clean data
    schema_str = clean_string(row["schema"])
    query1_str = clean_string(row["query1"])
    query2_str = clean_string(row["query2"])

    # Save files
    schema_file = os.path.join(row_dir, "schema.graphql")
    query1_file = os.path.join(row_dir, "query1.graphql")
    query2_file = os.path.join(row_dir, "query2.graphql")

    try:
        with open(schema_file, "w") as f:
            f.write(schema_str)
        with open(query1_file, "w") as f:
            f.write(query1_str)
        with open(query2_file, "w") as f:
            f.write(query2_str)
        logging.info(f"Processed files for row {index + 1} saved successfully.")
    except Exception as e:
        logging.error(f"Error saving files for row {index + 1}: {e}")

    # Store file paths
    processed_files.append((row_dir, schema_file, query1_file, query2_file))

logging.info(f"✅ Processed {len(processed_files)} rows from CSV.")
