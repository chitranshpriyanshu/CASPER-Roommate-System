import pandas as pd
import numpy as np
import os
import re
import logging

# ---------------- CONFIG ----------------
INPUT_PATH = '../data/raw_data.csv'
OUTPUT_PATH = '../data/processed/cleaned_data.csv'

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# ==========================================
# UTIL FUNCTIONS
# ==========================================

def validate_email(email):
    """Validate email format"""
    if pd.isna(email):
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, str(email)) is not None


def safe_normalize(series):
    """Robust normalization with edge case handling"""
    series = series.astype(float)

    if series.max() == series.min():
        return pd.Series([0.5] * len(series))

    return (series - series.min()) / (series.max() - series.min())


def clean_text(series):
    """Standard text cleaning"""
    return series.astype(str).str.strip().str.lower()


# ==========================================
# MAIN PIPELINE
# ==========================================

def run_cleaning_pipeline(input_file, output_file):

    logging.info("🚀 Starting data processing...")

    # ---------------- LOAD ----------------
    if not os.path.exists(input_file):
        logging.error(f"File not found: {input_file}")
        return None

    df = pd.read_csv(input_file)
    logging.info(f"Loaded {len(df)} rows")

    # ---------------- COLUMN CLEAN ----------------
    df.columns = df.columns.str.strip()

    column_mapping = {
        'Submission ID': 'sub_id',
        'Full Name': 'name',
        'Email Address': 'Email',
        'Gender': 'gender',
        'Branch': 'branch',
        'How would you describe your social personality?': 'social',
        'English Proficiency': 'english',
        'Cleaniliness': 'cleanliness',
        'Sleep Time': 'sleep_time',
        'Noise Tolerance': 'noise_tolerance',
        'How easily do you get irritated by others?': 'irritability',
        'How often do you bring your firends to room?': 'friends_freq',
        'How do you usually listen to music?': 'music_habit',
        'How often do you eat Non-Veg?': 'non_veg_freq',
        'How often do you snore?': 'snore_freq',
        'How sensitive are you to snoring?': 'snore_sensitivity',
        '🎯 What do you do in your spare time?': 'hobbies_raw',
        'How much are you satisfied with your current roommate?': 'current_sat'
    }

    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

    # ---------------- REQUIRED CHECK ----------------
    required_cols = ['name', 'Email', 'sleep_time', 'cleanliness', 'social']

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logging.error(f"Missing required columns: {missing}")
        return None

    # ---------------- BASIC CLEAN ----------------
    df['name'] = df['name'].astype(str).str.strip()
    df['Email'] = clean_text(df['Email'])

    before_email = len(df)
    df = df[df['Email'].apply(validate_email)]
    logging.info(f"Valid emails: {len(df)} (removed {before_email - len(df)})")

    # ---------------- NUMERIC PROCESSING ----------------
    numeric_cols = [
        'social', 'english', 'cleanliness', 'sleep_time',
        'noise_tolerance', 'irritability', 'friends_freq',
        'music_habit', 'non_veg_freq', 'snore_freq', 'snore_sensitivity'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

            # Fill missing
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)

            # Clip values (expected range 0–10)
            df[col] = df[col].clip(0, 10)

            # Normalize
            df[f'{col}_norm'] = safe_normalize(df[col])

    # ---------------- HOBBY FEATURE ENGINEERING ----------------
    hobby_list = ['coding', 'music', 'sports', 'gaming', 'studies', 'social']

    if 'hobbies_raw' in df.columns:
        df['hobbies_raw'] = clean_text(df['hobbies_raw'])

        for hobby in hobby_list:
            df[f'hobby_{hobby}'] = df['hobbies_raw'].str.contains(hobby, regex=False).astype(int)

        df['hobby_score'] = df[[f'hobby_{h}' for h in hobby_list]].sum(axis=1)

    # ---------------- GENDER CLEAN ----------------
    if 'gender' in df.columns:
        df['gender'] = df['gender'].fillna('Unknown').str.strip().str.capitalize()

    # ---------------- SATISFACTION ----------------
    if 'current_sat' in df.columns:
        df['current_sat'] = pd.to_numeric(df['current_sat'], errors='coerce').fillna(5.0)

    # ---------------- REMOVE DUPLICATES ----------------
    before_dup = len(df)
    df = df.drop_duplicates(subset=['Email'])
    logging.info(f"Duplicates removed: {before_dup - len(df)}")

    # ---------------- RESET INDEX ----------------
    df = df.reset_index(drop=True)

    # ---------------- FINAL VALIDATION ----------------
    key_cols = ['sleep_time_norm', 'cleanliness_norm', 'social_norm']
    if not all(col in df.columns for col in key_cols):
        logging.error("Normalization failed for key features")
        return None

    logging.info("Final dataset stats:")
    logging.info(df[key_cols].describe())

    # ---------------- SAVE ----------------
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)

    logging.info(f"✅ Saved cleaned data → {output_file}")

    return df


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    run_cleaning_pipeline(INPUT_PATH, OUTPUT_PATH)
