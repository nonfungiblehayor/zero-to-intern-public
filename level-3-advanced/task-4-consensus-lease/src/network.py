from typing import Set, Tuple


class SimulatedNetwork:
    def __init__(self):
        # Set of frozenset of frozenset representing isolated partition sets
        self.partitions: Set[frozenset] = set()
        self.dropped_nodes: Set[str] = set()

    def partition(self, group_a: Set[str], group_b: Set[str]):
        """Isolates nodes in group_a from nodes in group_b."""
        self.partitions.add(frozenset((frozenset(group_a), frozenset(group_b))))

    def heal(self):
        """Heals all partitions and drops."""
        self.partitions.clear()
        self.dropped_nodes.clear()

    def drop_node(self, node_id: str):
        self.dropped_nodes.add(node_id)

    def recover_node(self, node_id: str):
        self.dropped_nodes.discard(node_id)

    def can_communicate(self, src: str, dst: str) -> bool:
        if src in self.dropped_nodes or dst in self.dropped_nodes:
            return False
        for part in self.partitions:
            groups = list(part)
            if len(groups) == 2:
                g1, g2 = groups[0], groups[1]
                if (src in g1 and dst in g2) or (src in g2 and dst in g1):
                    return False
        return True
