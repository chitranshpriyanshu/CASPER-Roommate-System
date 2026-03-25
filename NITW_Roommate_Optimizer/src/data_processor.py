import pandas as pd
import numpy as np
import os
import re

INPUT_PATH = '../data/raw_data.csv'
OUTPUT_PATH = '../data/processed/cleaned_data.csv'

# ==========================================

def validate_email(email):
    """Basic email validation"""
    if pd.isna(email):
        return False
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, str(email)) is not None


def safe_normalize(series):
    """Robust normalization (handles edge cases)"""
    if series.max() == series.min():
        return pd.Series([0.5] * len(series))
    return (series - series.min()) / (series.max() - series.min())


# ==========================================

def run_cleaning_pipeline(input_file, output_file):

    print("🚀 Starting data processing...")

    # 1. Check file
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found.")
        return None

    df = pd.read_csv(input_file)
    print(f"📥 Loaded {len(df)} rows")

    # 2. Clean column names
    df.columns = df.columns.str.strip()

    # 3. Rename columns (SAFE)
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

    # 4. Ensure required columns exist
    required_cols = ['name', 'Email', 'sleep_time', 'cleanliness', 'social']
    for col in required_cols:
        if col not in df.columns:
            print(f"❌ Missing required column: {col}")
            return None

    # 5. Clean basic fields
    df['name'] = df['name'].astype(str).str.strip()
    df['Email'] = df['Email'].astype(str).str.strip().str.lower()

    # Remove invalid emails
    df = df[df['Email'].apply(validate_email)]
    print(f"📧 Valid emails: {len(df)}")

    # 6. Numeric Columns
    numeric_cols = [
        'social', 'english', 'cleanliness', 'sleep_time',
        'noise_tolerance', 'irritability', 'friends_freq',
        'music_habit', 'non_veg_freq', 'snore_freq', 'snore_sensitivity'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

            # Fill missing with median
            df[col] = df[col].fillna(df[col].median())

            # Clip outliers (0–10 expected)
            df[col] = df[col].clip(0, 10)

            # Normalize (robust)
            df[f'{col}_norm'] = safe_normalize(df[col])

    # 7. Hobby Processing (UPGRADED)
    hobby_list = ['coding', 'music', 'sports', 'gaming', 'studies', 'social']

    if 'hobbies_raw' in df.columns:
        df['hobbies_raw'] = df['hobbies_raw'].fillna('').str.lower()

        for hobby in hobby_list:
            df[f'hobby_{hobby}'] = df['hobbies_raw'].str.contains(hobby).astype(int)

        # Hobby score (optional future use)
        df['hobby_score'] = df[[f'hobby_{h}' for h in hobby_list]].sum(axis=1)

    # 8. Gender clean
    if 'gender' in df.columns:
        df['gender'] = df['gender'].fillna('Unknown').str.strip().str.capitalize()

    # 9. Satisfaction cleanup
    if 'current_sat' in df.columns:
        df['current_sat'] = pd.to_numeric(df['current_sat'], errors='coerce').fillna(5.0)

    # 10. Remove duplicates
    before = len(df)
    df = df.drop_duplicates(subset=['Email'])
    print(f"🧹 Removed {before - len(df)} duplicates")

    # 11. Reset index (VERY IMPORTANT for graph matching)
    df = df.reset_index(drop=True)

    # 12. Final sanity check
    print("📊 Final dataset summary:")
    print(df[['sleep_time_norm', 'cleanliness_norm', 'social_norm']].describe())

    # 13. Save
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)

    print(f"\n✅ SUCCESS: Cleaned {len(df)} records")
    print(f"📂 Saved to: {output_file}")

    return df


# ==========================================

if __name__ == "__main__":
    run_cleaning_pipeline(INPUT_PATH, OUTPUT_PATH)
