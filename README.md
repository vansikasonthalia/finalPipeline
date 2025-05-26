# 🧠 GraphQL Query Comparison & Schema Preprocessing Pipeline

[![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project provides an end-to-end pipeline to:

✅ Preprocess GraphQL schemas and queries  
✅ Generate ASTs and query graphs  
✅ Detect and remove cycles in GraphQL queries  
✅ Optimize queries using schema-aware logic  
✅ Compare two queries for logical equivalence  


---

## ⚙️ Installation

Install dependencies:

```bash
pip install pandas graphql-core networkx matplotlib

🏁 How to Run
Step 1: Preprocess Input CSV
python preProcessor.py
This updates raw_schema.csv with: 
a. Cleaned GraphQL queries
b. StepZen-compatible schemas

Step 2: Run the Full Pipeline
python main.py


📊 Output
Results in results/:

comparison_summary.csv

graph1_visualization.png, graph2_visualization.png

graph-1-cleaned.json, optimized_links2.json



