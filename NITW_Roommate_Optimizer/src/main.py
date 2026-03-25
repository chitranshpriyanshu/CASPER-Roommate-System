import pandas as pd
import random
from src.graph.graph_builder import build_edges
from src.graph.matcher import max_weight_matching

# Load data
df = pd.read_csv("data/processed/cleaned_data.csv")

# Step 1: Build graph
edges = build_edges(df)

print(f"Total Nodes: {len(df)}")
print(f"Total Edges: {len(edges)}")

# Step 2: Matching (CASPER)
matches = max_weight_matching(edges)

print(f"Total Matches (CASPER): {len(matches)}")

# -------------------------------
# Score helper
# -------------------------------
def score_lookup(i, j):
    for a, b, w in edges:
        if (a == i and b == j) or (a == j and b == i):
            return w
    return 0

def avg_score(pairs):
    return sum(score_lookup(a,b) for a,b in pairs) / len(pairs)

# -------------------------------
# Step 3: Find unmatched
# -------------------------------
matched_nodes = set()
for a, b in matches:
    matched_nodes.add(a)
    matched_nodes.add(b)

unmatched = list(set(df.index) - matched_nodes)

print(f"\nUnmatched count: {len(unmatched)}")

# -------------------------------
# Step 4: Fallback pairing
# -------------------------------
random.shuffle(unmatched)

fallback_pairs = []
for i in range(0, len(unmatched)-1, 2):
    fallback_pairs.append((unmatched[i], unmatched[i+1]))

# -------------------------------
# Step 5: Final pairs
# -------------------------------
final_pairs = list(matches) + fallback_pairs

# -------------------------------
# Step 6: Print final result
# -------------------------------

def explain_pair(i, j):
    reasons = []

    a = df.loc[i]
    b = df.loc[j]

    # ------------------------
    # Similarity reasons
    # ------------------------
    if abs(a['sleep_time_norm'] - b['sleep_time_norm']) < 0.2:
        reasons.append("Similar sleep schedule")

    if abs(a['cleanliness_norm'] - b['cleanliness_norm']) < 0.2:
        reasons.append("Similar cleanliness level")

    if abs(a['social_norm'] - b['social_norm']) < 0.2:
        reasons.append("Similar social behavior")

    # ------------------------
    # Hobby overlap
    # ------------------------
    hobbies = [
        'hobby_coding', 'hobby_music', 'hobby_sports',
        'hobby_gaming', 'hobby_studies', 'hobby_social'
    ]

    common_hobbies = []
    for h in hobbies:
        if a[h] == 1 and b[h] == 1:
            common_hobbies.append(h.replace("hobby_", ""))

    if common_hobbies:
        reasons.append(f"Common hobbies: {', '.join(common_hobbies)}")

    # ------------------------
    # Conflict avoidance
    # ------------------------
    if abs(a['snore_freq_norm'] - b['snore_sensitivity_norm']) < 0.3:
        reasons.append("Snoring compatibility")

    if abs(a['noise_tolerance_norm'] - b['friends_freq_norm']) < 0.3:
        reasons.append("Noise tolerance compatibility")

    return reasons
print("\n=== FINAL ROOMMATE ASSIGNMENT (WITH REASONS) ===\n")

for a, b in final_pairs:
    name_a = df.loc[a, 'name']
    name_b = df.loc[b, 'name']

    if (a, b) in matches or (b, a) in matches:
        tag = "CASPER"
    else:
        tag = "FALLBACK"

    score = score_lookup(a, b)

    print(f"{name_a}  ↔  {name_b}   | {tag} | Score: {score:.3f}")

    reasons = explain_pair(a, b)

    if reasons:
        for r in reasons:
            print(f"   ✔ {r}")
    else:
        print("   ⚠ No strong similarity (fallback pairing)")

    print()