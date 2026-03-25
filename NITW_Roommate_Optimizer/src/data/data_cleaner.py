import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

INPUT_PATH = os.path.join(BASE_DIR, 'data', 'raw', 'raw_data.csv')
OUTPUT_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'cleaned_data.csv')
# ==========================================

def run_cleaning_pipeline(input_file, output_file):
  
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found. Make sure the 'data' folder exists.")
        return None
        
    df = pd.read_csv(input_file)
    
    # 2. Standardize Column Names (Mapping raw text to code-friendly keys)
    column_mapping = {
        'Submission ID': 'sub_id',
        'Full Name': 'name',
        'Gender': 'gender',
        
        'Branch': 'branch',
        ' How would you describe your social personality?': 'social',
        'English Proficiency': 'english',
        'Cleaniliness': 'cleanliness',
        'Sleep Time': 'sleep_time',
        'Noise Tolerance': 'noise_tolerance',
        'How easily do you get irritated by others?': 'irritability',
        'How often do you bring your firends to room?': 'friends_freq',
        ' How do you usually listen to music?': 'music_habit',
        'How often do you eat Non-Veg?': 'non_veg_freq',
        ' How often do you snore?': 'snore_freq',
        'How sensitive are you to snoring?': 'snore_sensitivity',
        '🎯 What do you do in your spare time?': 'hobbies_raw',
        'How much are you satisfied with your current roommate?': 'current_sat'
    }
    df = df.rename(columns=column_mapping)

    # 3. Clean Numeric Features & Normalize (0.0 to 1.0)
    numeric_cols = [
        'social', 'english', 'cleanliness', 'sleep_time', 'noise_tolerance',
        'irritability', 'friends_freq', 'music_habit', 'non_veg_freq',
        'snore_freq', 'snore_sensitivity'
    ]

    for col in numeric_cols:
        # Convert to numeric, fill missing with median
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col].median())
        # Scaling 0-10 to 0.0-1.0
        df[f'{col}_norm'] = df[col] / 10.0

    # 4. Hobby Vectorization (One-Hot Encoding)
    # This turns text like "Gaming, Coding" into binary 1s and 0s
    hobby_list = [
        'Coding / Tech', 'Music / Arts', 'Sports / Fitness', 
        'Gaming', 'Studies / Academic focus', 'Social / Hanging out'
    ]
    
    for hobby in hobby_list:
        # Create a clean column name like 'hobby_coding'
        clean_hobby_name = f"hobby_{hobby.split(' / ')[0].lower().replace(' ', '_')}"
        df[clean_hobby_name] = df['hobbies_raw'].apply(
            lambda x: 1 if str(hobby) in str(x) else 0
        )

    # 5. Final Sanitization
    df['gender'] = df['gender'].str.strip().str.capitalize()
    df['current_sat'] = pd.to_numeric(df['current_sat'], errors='coerce').fillna(5.0)
    
    # 6. Save the cleaned result
    df.to_csv(output_file, index=False)
    print(f"✅ SUCCESS: Cleaned {len(df)} records.")
    print(f"📂 Saved to: {output_file}")
    
    return df

if __name__ == "__main__":
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    # Run using the variables defined at the top
    run_cleaning_pipeline(INPUT_PATH, OUTPUT_PATH)