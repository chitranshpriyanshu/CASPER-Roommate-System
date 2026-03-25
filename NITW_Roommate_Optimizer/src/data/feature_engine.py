import numpy as np

NUMERIC_COLS = [
    'social_norm', 'english_norm', 'cleanliness_norm',
    'sleep_time_norm', 'noise_tolerance_norm',
    'irritability_norm', 'friends_freq_norm',
    'music_habit_norm', 'non_veg_freq_norm',
    'snore_freq_norm', 'snore_sensitivity_norm'
]

HOBBY_COLS = [col for col in [
    'hobby_coding', 'hobby_music', 'hobby_sports',
    'hobby_gaming', 'hobby_studies', 'hobby_social'
]]

def compute_cs(a, b, alpha=0.6):
    # numeric similarity
    diff = np.abs(a[NUMERIC_COLS] - b[NUMERIC_COLS])
    cs_num = 1 - diff.mean()

    # hobby similarity (Jaccard)
    h1 = a[HOBBY_COLS].values
    h2 = b[HOBBY_COLS].values

    intersection = np.sum((h1 & h2))
    union = np.sum((h1 | h2)) + 1e-6

    cs_hobby = intersection / union

    return alpha * cs_num + (1 - alpha) * cs_hobby


def compute_cf(a, b):
    snore = abs(a['snore_freq_norm'] - b['snore_sensitivity_norm'])
    noise = abs(a['noise_tolerance_norm'] - b['friends_freq_norm'])
    sleep = abs(a['sleep_time_norm'] - b['sleep_time_norm'])
    irrit = (a['irritability_norm'] + b['irritability_norm']) / 2

    return 0.3*snore + 0.3*noise + 0.2*sleep + 0.2*irrit