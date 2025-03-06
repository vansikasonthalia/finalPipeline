import pandas as pd
import re

# Define a function to extract GraphQL queries
def extract_graphql_query(text):
    # Look for a query or mutation in the format 'query { ... }' or 'mutation { ... }'
    query_pattern = r'(query)\s+(\w+)?\s*{.*?}'
    match = re.search(query_pattern, text, re.DOTALL)
    if match:
        return match.group(0)  # Return the whole GraphQL query
    return None  # No query found

# Load the CSV file
file_path = 'ZeroShot_ibm_granite-20b-code-instruct-op_1164 (1).csv'
df = pd.read_csv(file_path)

# Apply the extraction function to the 'Generated_GraphQL' column
df['extracted_graphql'] = df['Generated_GraphQL'].apply(extract_graphql_query)

# Save the DataFrame with the new column to a new CSV file
output_file_path = 'processed_data_with_queries.csv'
df.to_csv(output_file_path, index=False)

# Provide the output file path for download
output_file_path
