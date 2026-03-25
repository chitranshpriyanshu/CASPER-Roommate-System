# ---------------- DATA (FINAL FIX) ----------------
import os

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
    st.error("❌ Dataset not found in any expected location!")
    
    # DEBUG INFO (very useful)
    st.write("Current directory:", os.getcwd())
    st.write("Files here:", os.listdir())
    
    st.stop()

df = pd.read_csv(DATA_PATH)
st.success(f"✅ Loaded dataset from: {DATA_PATH}")
