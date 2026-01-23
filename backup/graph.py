from collections import defaultdict, deque

class Graph:
    def __init__(self):
        self.adjacency = defaultdict(list)

    def add_edge(self, source, target, weight=1.0):
        self.adjacency[source].append((target, weight))
        self.adjacency[target].append((source, weight))

    def bfs(self, start, max_depth=2):
        visited = set()
        queue = deque([(start, 0)])
        scores = {}

        while queue:
            node, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for neighbor, weight in self.adjacency.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    scores[neighbor] = scores.get(neighbor, 0) + weight / (depth + 1)
                    queue.append((neighbor, depth + 1))

        return scores

    def dfs(self, start, max_depth=2):
        scores = {}

        def _dfs(node, depth):
            if depth > max_depth:
                return

            for neighbor, weight in self.adjacency.get(node, []):
                scores[neighbor] = scores.get(neighbor, 0) + weight / (depth + 1)
                _dfs(neighbor, depth + 1)

        _dfs(start, 1)
        return scores
