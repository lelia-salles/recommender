def combine_scores(bfs_scores, dfs_scores):
    combined = {}

    for k, v in bfs_scores.items():
        combined[k] = combined.get(k, 0) + v

    for k, v in dfs_scores.items():
        combined[k] = combined.get(k, 0) + v

    return combined
