# 🧠 RGEval

[![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/)
---

## ⚙️ Installation

Install dependencies:

```bash
Dependencies:
pip install pandas graphql-core networkx matplotlib pyyaml

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
comparison_summary.csv and detailed breakdown




