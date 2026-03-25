from itertools import combinations
from src.data.feature_engine import compute_cs, compute_cf
def build_edges(df, lambda_=1.2, threshold=0.4):
    edges = []

    for i, j in combinations(df.index, 2):
        if df.loc[i, 'gender'] != df.loc[j, 'gender']:
            continue

        cs = compute_cs(df.loc[i], df.loc[j])
        cf = compute_cf(df.loc[i], df.loc[j])

        if cf > threshold:
            continue

        score = cs - lambda_ * (cf ** 2)
        edges.append((i, j, score))

    return edges