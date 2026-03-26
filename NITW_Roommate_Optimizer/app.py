import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
import os
import smtplib
from email.mime.text import MIMEText
import networkx as nx
import seaborn as sns
import matplotlib.pyplot as plt
from src.graph.graph_builder import build_edges
from src.graph.matcher import max_weight_matching

# ---------------- LOGIN CONFIG ----------------
USERNAME = os.environ.get("APP_USER", "admin")
PASSWORD = os.environ.get("APP_PASS", "casper123")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------------- LOGIN PAGE ----------------
if not st.session_state.logged_in:
    st.title("🔐 CASPER Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.logged_in = True
            st.success("Login successful!")
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

# ---------------- DATA ----------------
try:
    df = pd.read_csv("NITW_Roommate_Optimizer/data/processed/cleaned_data.csv")
except:
    st.error("Dataset not found!")
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ Parameters")
lambda_ = st.sidebar.slider("Lambda", 0.1, 2.0, 1.2)
threshold = st.sidebar.slider("Threshold", 0.1, 1.0, 0.4)

# ---------------- EMAIL FUNCTION ----------------
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

# ---------------- FUNCTIONS ----------------
def explain_pair(a, b):
    reasons = []

    if abs(df.loc[a,'sleep_time_norm'] - df.loc[b,'sleep_time_norm']) < 0.2:
        reasons.append("Similar sleep schedule")

    if abs(df.loc[a,'cleanliness_norm'] - df.loc[b,'cleanliness_norm']) < 0.2:
        reasons.append("Similar cleanliness")

    if abs(df.loc[a,'social_norm'] - df.loc[b,'social_norm']) < 0.2:
        reasons.append("Similar social behavior")

    return reasons


def compatibility_score(a, b):
    sleep = 1 - abs(df.loc[a,'sleep_time_norm'] - df.loc[b,'sleep_time_norm'])
    clean = 1 - abs(df.loc[a,'cleanliness_norm'] - df.loc[b,'cleanliness_norm'])
    social = 1 - abs(df.loc[a,'social_norm'] - df.loc[b,'social_norm'])

    score = (sleep + clean + social) / 3
    return round(score, 2), sleep, clean, social


def average_score(pairs):
    if len(pairs) == 0:
        return 0
    return round(sum(compatibility_score(a,b)[0] for a,b in pairs)/len(pairs),2)


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
                score = compatibility_score(i, j)[0]
                if score > best_score:
                    best_score = score
                    best_j = j

        if best_j is not None:
            pairs.append((i, best_j))
            used.add(i)
            used.add(best_j)

    return pairs

# ---------------- SESSION ----------------
if "final_pairs" not in st.session_state:
    st.session_state.final_pairs = None

# ---------------- RUN ----------------
if st.button("🚀 Run CASPER Matching"):
    edges = build_edges(df, lambda_=lambda_, threshold=threshold)
    matches = max_weight_matching(edges)

    matched_nodes = set()
    for a, b in matches:
        matched_nodes.add(a)
        matched_nodes.add(b)

    unmatched = list(set(df.index) - matched_nodes)
    fallback_pairs = smart_fallback(unmatched)

    st.session_state.final_pairs = list(matches) + fallback_pairs

# ---------------- STOP ----------------
if st.session_state.final_pairs is None:
    st.warning("Click 'Run CASPER Matching' first")
    st.stop()

final_pairs = st.session_state.final_pairs

# ---------------- METRICS ----------------
col1, col2, col3 = st.columns(3)
col1.metric("👥 Students", len(df))
col2.metric("🟢 CASPER Matches", len(final_pairs))
col3.metric("📊 Avg Score", average_score(final_pairs))
# ---------------- ALGORITHM COMPARISON ----------------
st.subheader("⚖️ Algorithm Comparison")

# Greedy matching (baseline)
greedy_pairs = smart_fallback(list(df.index))
greedy_score = average_score(greedy_pairs)

# CASPER (Blossom)
blossom_score = average_score(final_pairs)

colA, colB = st.columns(2)
colA.metric("🟡 Greedy Matching Score", greedy_score)
colB.metric("🟢 Max Weight (Blossom) Score", blossom_score)

# Improvement display
if greedy_score > 0:
    improvement = round(((blossom_score - greedy_score) / greedy_score) * 100, 2)
    st.success(f"🚀 Improvement: {improvement}% better than Greedy")
# ---------------- EMAIL ALL + DOWNLOAD ----------------
st.subheader("📤 Actions")

colA, colB = st.columns(2)

with colA:
    if st.button("📨 Send Email to All"):
        success = True
        for a, b in final_pairs:
            name_a = df.loc[a, 'name']
            name_b = df.loc[b, 'name']
            email_a = df.loc[a, 'Email']
            email_b = df.loc[b, 'Email']

            res1 = send_email(email_a, "Roommate Assigned",
                              f"You are paired with {name_b}")
            res2 = send_email(email_b, "Roommate Assigned",
                              f"You are paired with {name_a}")

            if res1 != True or res2 != True:
                success = False

        if success:
            st.success("All emails sent successfully!")
        else:
            st.error("Some emails failed")

with colB:
    csv_data = []
    for a, b in final_pairs:
        csv_data.append({
            "Student 1": df.loc[a, 'name'],
            "Email 1": df.loc[a, 'Email'],
            "Student 2": df.loc[b, 'name'],
            "Email 2": df.loc[b, 'Email'],
            "Score": compatibility_score(a,b)[0]
        })

    csv_df = pd.DataFrame(csv_data)

    st.download_button(
        "⬇ Download Pairings CSV",
        csv_df.to_csv(index=False),
        "roommate_pairs.csv",
        "text/csv"
    )

# ---------------- HEATMAP ----------------
st.subheader("🔥 Compatibility Heatmap")

matrix = [[compatibility_score(i,j)[0] for j in df.index] for i in df.index]

fig, ax = plt.subplots()
sns.heatmap(matrix, ax=ax, cmap="coolwarm")
st.pyplot(fig)

# ---------------- DISTRIBUTION ----------------
st.subheader("📊 Match Score Distribution")

scores = [compatibility_score(a,b)[0] for a,b in final_pairs]
fig = px.histogram(x=scores, nbins=10)
st.plotly_chart(fig, use_container_width=True)

# ---------------- MATCHES ----------------
st.subheader("👥 Roommate Pairs")

for a, b in final_pairs:

    name_a = df.loc[a, 'name']
    name_b = df.loc[b, 'name']
    email_a = df.loc[a, 'Email']
    email_b = df.loc[b, 'Email']

    score, sleep, clean, social = compatibility_score(a, b)

    color = "#00C853" if score > 0.7 else "#FFC107" if score > 0.5 else "#FF5252"

    st.markdown(f"""
    <div style="padding:15px;margin-bottom:12px;border-radius:12px;
    background-color:#1e1e1e;border-left:6px solid {color};">
        <b>{name_a} ↔ {name_b}</b><br>
        <span style="color:{color};">Score: {score}</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3,1])

    with col1:
        with st.expander("🔍 View Details"):
            st.write(f"**{name_a} Email:** {email_a}")
            st.write(f"**{name_b} Email:** {email_b}")

            st.write("### 📊 Score Breakdown")
            st.write(f"Sleep: {round(sleep,2)}")
            st.write(f"Cleanliness: {round(clean,2)}")
            st.write(f"Social: {round(social,2)}")

            reasons = explain_pair(a, b)
            st.write("### ✅ Reasons")
            if reasons:
                for r in reasons:
                    st.write(f"✔ {r}")
            else:
                st.write("⚠ No strong similarity")

    with col2:
        if st.button("📧 Email", key=f"email_{a}_{b}"):
            res1 = send_email(email_a, "Roommate Assigned",
                              f"You are paired with {name_b}")
            res2 = send_email(email_b, "Roommate Assigned",
                              f"You are paired with {name_a}")

            if res1 == True and res2 == True:
                st.success("Emails sent!")
            else:
                st.error(f"Error: {res1} | {res2}")

# ---------------- GRAPH ----------------
st.subheader("🧠 Smart Matching Graph")

G = nx.Graph()

for i in df.index:
    G.add_node(i)

pos = nx.spring_layout(G, seed=42, k=1.2)

edge_traces = []

for a, b in final_pairs:
    score = compatibility_score(a, b)[0]
    x0, y0 = pos[a]
    x1, y1 = pos[b]

    color = 'green' if score > 0.7 else 'orange' if score > 0.5 else 'red'
    width = 2 + 4 * score

    edge_traces.append(go.Scatter(
        x=[x0, x1],
        y=[y0, y1],
        mode='lines',
        line=dict(width=width, color=color),
        hoverinfo='text',
        text=f"Score: {score}"
    ))

node_x, node_y, text = [], [], []

for node in df.index:
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    text.append(df.loc[node,'name'])

node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode='markers+text',
    text=text,
    textposition="top center",
    marker=dict(size=10, color='lightblue')
)

fig = go.Figure(data=edge_traces + [node_trace])
st.plotly_chart(fig, use_container_width=True)
