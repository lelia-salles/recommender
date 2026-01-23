class Entity:
    def __init__(self, entity_id: str, entity_type: str):
        self.id = entity_id
        self.type = entity_type  # user, product, course, concert, teacher
def combine_scores(*score_dicts):
    combined = {}

    for scores in score_dicts:
        for item, score in scores.items():
            combined[item] = combined.get(item, 0) + score

    return combined


class Interaction:
      def __init__(
        self,
        source_id: str,
        target_id: str,
        weight: float = 1.0,
        interaction_type: str = "view"
    ):
        self.source_id = source_id   # user
        self.target_id = target_id   # item
        self.weight = weight
        self.type = interaction_type
