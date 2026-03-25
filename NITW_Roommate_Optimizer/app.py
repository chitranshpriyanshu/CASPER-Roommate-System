import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import smtplib
from email.mime.text import MIMEText
import networkx as nx
import seaborn as sns
import matplotlib.pyplot as plt

from src.graph.graph_builder import build_edges
from src.graph.matcher import max_weight_matching

# ---------------- LOGIN ----------------
USERNAME = os.environ.get("APP_USER", "admin")
PASSWORD = os.environ.get("APP_PASS", "casper123")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 CASPER Login")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == USERNAME and pwd == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# ---------------- PAGE ----------------
st.set_page_config(page_title="CASPER Dashboard", layout="wide")

col_title, col_logout = st.columns([8,1])
with col_title:
    st.title("🏠 CASPER Roommate Matching System")
with col_logout:
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()

# ---------------- DATA (FINAL FIX) ----------------
POSSIBLE_PATHS = [
    "data/processed/cleaned_data.csv",
    "NITW_Roommate_Optimizer/data/processed/cleaned_data.csv"
]

DATA_PATH = None
for path in POSSIBLE_PATHS:
    if os.path.exists(path):
        DATA_PATH = path
        break

if DATA_PATH is None:
    st.error("❌ Dataset not found!")
    st.write("Current dir:", os.getcwd())
    st.write("Files:", os.listdir())
    st.stop()

df = pd.read_csv(DATA_PATH)

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ Parameters")
lambda_ = st.sidebar.slider("Lambda", 0.1, 2.0, 1.2)
threshold = st.sidebar.slider("Threshold", 0.1, 1.0, 0.4)

# ---------------- EMAIL ----------------
def send_email(to_email, subject, body):
    sender = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")

    if not sender or not password:
        return "Email credentials not set"

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()

        return True
    except Exception as e:
        return str(e)

# ---------------- LOGIC ----------------
def compatibility_score(a, b):
    sleep = 1 - abs(df.loc[a,'sleep_time_norm'] - df.loc[b,'sleep_time_norm'])
    clean = 1 - abs(df.loc[a,'cleanliness_norm'] - df.loc[b,'cleanliness_norm'])
    social = 1 - abs(df.loc[a,'social_norm'] - df.loc[b,'social_norm'])
    score = (sleep + clean + social) / 3
    return round(score, 2)

def smart_fallback(unmatched):
    pairs = []
    used = set()

    for i in unmatched:
        if i in used:
            continue

        best_j = None
        best_score = -1

        for j in unmatched:
            if j != i and j not in used:
                score = compatibility_score(i, j)
                if score > best_score:
                    best_score = score
                    best_j = j

        if best_j is not None:
            pairs.append((i, best_j))
            used.add(i)
            used.add(best_j)

    return pairs

# ---------------- RUN ----------------
if "pairs" not in st.session_state:
    st.session_state.pairs = None

if st.button("🚀 Run Matching"):
    edges = build_edges(df, lambda_=lambda_, threshold=threshold)
    matches = max_weight_matching(edges)

    matched = set()
    for a, b in matches:
        matched.add(a)
        matched.add(b)

    unmatched = list(set(df.index) - matched)
    fallback = smart_fallback(unmatched)

    st.session_state.pairs = list(matches) + fallback

if st.session_state.pairs is None:
    st.warning("Run matching first")
    st.stop()

pairs = st.session_state.pairs

# ---------------- METRICS ----------------
st.subheader("📊 Overview")
col1, col2 = st.columns(2)
col1.metric("Students", len(df))
col2.metric("Pairs", len(pairs))

# ---------------- DISTRIBUTION ----------------
scores = [compatibility_score(a,b) for a,b in pairs]
fig = px.histogram(x=scores)
st.plotly_chart(fig, use_container_width=True)

# ---------------- MATCHES ----------------
st.subheader("👥 Matches")

for a,b in pairs:
    name_a = df.loc[a,'name']
    name_b = df.loc[b,'name']
    score = compatibility_score(a,b)

    st.write(f"**{name_a} ↔ {name_b} | Score: {score}**")

# ---------------- GRAPH ----------------
st.subheader("🧠 Graph")

G = nx.Graph()
for i in df.index:
    G.add_node(i)

pos = nx.spring_layout(G)

edges_plot = []
for a,b in pairs:
    x0,y0 = pos[a]
    x1,y1 = pos[b]
    edges_plot.append(go.Scatter(x=[x0,x1], y=[y0,y1], mode='lines'))

nodes_plot = go.Scatter(
    x=[pos[i][0] for i in df.index],
    y=[pos[i][1] for i in df.index],
    mode='markers'
)

fig = go.Figure(data=edges_plot + [nodes_plot])
st.plotly_chart(fig)
