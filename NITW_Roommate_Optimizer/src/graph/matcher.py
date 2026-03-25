import networkx as nx

def max_weight_matching(edges):
    G = nx.Graph()

    for i, j, w in edges:
        G.add_edge(i, j, weight=w)

    matching = nx.algorithms.matching.max_weight_matching(G, maxcardinality=True)

    return list(matching)