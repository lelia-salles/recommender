import numpy as np
import hashlib
from collections import defaultdict


class MinHashLSH:
    def __init__(self, num_perm=128, threshold=0.5):
        """
        :param num_perm: Número de funções de hash (tamanho da assinatura).
                         Mais alto = mais preciso, porém mais lento. 128 é um bom padrão.
        :param threshold: Similaridade mínima (0 a 1) para considerar "vizinho".
        """
        self.num_perm = num_perm
        self.threshold = threshold
        self.users_signatures = {}  # Armazena {user_id: assinatura_numpy}

        # Gera coeficientes aleatórios para simular N funções de hash diferentes
        # h(x) = (a*x + b) % c
        # Usamos um primo grande de Mersenne para evitar colisões
        self.prime = (1 << 61) - 1
        self.max_val = (1 << 32) - 1

        # Fixamos a semente para garantir consistência entre reinícios do servidor
        rs = np.random.RandomState(42)
        self.a = rs.randint(1, self.max_val, size=num_perm, dtype=np.uint64)
        self.b = rs.randint(0, self.max_val, size=num_perm, dtype=np.uint64)

    def _hash_item(self, item_str):
        """Transforma string do item em um inteiro determinístico."""
        # Usamos SHA256 para garantir que o mesmo item sempre dê o mesmo ID numérico
        hex_digest = hashlib.sha256(item_str.encode('utf-8')).hexdigest()
        return int(hex_digest, 16)

    def compute_signature(self, item_set):
        """
        Gera a assinatura MinHash para um conjunto de itens.
        """
        if not item_set:
            return None

        # 1. Converte itens para inteiros
        item_ids = np.array([self._hash_item(item) for item in item_set], dtype=np.uint64)

        # 2. Aplica as N funções de hash em todos os itens
        # Resultado shape: (num_items, num_perm)
        # h = (a * x + b) % prime
        # Broadcasting do numpy faz isso super rápido
        hashes = (np.outer(item_ids, self.a) + self.b) % self.prime

        # 3. Pega o valor MÍNIMO de cada coluna (hash function)
        # É isso que define o MinHash
        signature = np.min(hashes, axis=0)

        return signature

    def add_user(self, user_id, item_set):
        """Calcula e salva a assinatura de um usuário."""
        sig = self.compute_signature(item_set)
        if sig is not None:
            self.users_signatures[user_id] = sig

    def find_similar_users(self, target_user_id):
        """
        Encontra usuários com assinaturas similares.
        Em produção real usaríamos "Bucketing/Banding" para não comparar 1-pra-1.
        Aqui compararemos 1-pra-todos (rápido para até ~10k usuários).
        """
        target_sig = self.users_signatures.get(target_user_id)
        if target_sig is None:
            return []

        similar_users = []

        for user_id, sig in self.users_signatures.items():
            if user_id == target_user_id:
                continue

            # Cálculo da Similaridade de Jaccard estimada
            # Fração de posições onde os valores de hash são iguais
            matching_hashes = np.sum(target_sig == sig)
            estimated_jaccard = matching_hashes / self.num_perm

            if estimated_jaccard >= self.threshold:
                similar_users.append((user_id, estimated_jaccard))

        # Ordena pelos mais similares
        return sorted(similar_users, key=lambda x: x[1], reverse=True)