from fastapi import FastAPI
import pandas as pd
from src.graph.graph_builder import build_edges
from src.graph.matcher import max_weight_matching

app = FastAPI()

@app.post("/run_matching/")
def run_matching(data: list):
    df = pd.DataFrame(data)

    edges = build_edges(df)
    matches = max_weight_matching(edges)

    return {"matches": list(matches)}