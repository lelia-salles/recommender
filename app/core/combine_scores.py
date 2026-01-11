def combine_scores(*score_dicts):
    combined = {}

    for scores in score_dicts:
        for item, score in scores.items():
            combined[item] = combined.get(item, 0) + score

    return combined
