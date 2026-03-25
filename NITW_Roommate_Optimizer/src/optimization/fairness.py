import numpy as np

def compute_variance(scores):
    return np.var(scores)

def improve_matching(pairs, score_lookup):
    # simple swap-based optimization
    improved = True

    while improved:
        improved = False

        for i in range(len(pairs)):
            for j in range(i+1, len(pairs)):
                a, b = pairs[i]
                c, d = pairs[j]

                current = score_lookup(a,b) + score_lookup(c,d)
                swapped = score_lookup(a,c) + score_lookup(b,d)

                if swapped > current:
                    pairs[i] = (a,c)
                    pairs[j] = (b,d)
                    improved = True

    return pairs