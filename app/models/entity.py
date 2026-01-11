class Entity:
    def __init__(self, entity_id: str, entity_type: str):
        self.id = entity_id
        self.type = entity_type  # user, product, course, concert, teacher
