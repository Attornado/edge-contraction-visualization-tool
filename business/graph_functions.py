from typing import Optional, Iterable
import networkx as nx
from random import randint


class SuperNode(object):
    def __init__(self, node: int):
        """
        This function initializes the supernode and the set of contracted nodes.

        :param node: The supernode.
        :type node: int
        """
        self.__node = node
        self.__contracted_nodes = set()

    @property
    def node(self) -> int:
        """
        It returns the index of the super-node of the graph.
        :return: The node is being returned.
        """
        return self.__node

    @property
    def contracted_nodes(self) -> set[int]:
        """
        It returns the set of contracted nodes.
        :return: A set of integers
        """
        return self.__contracted_nodes

    def contains(self, node: int) -> bool:
        """
        It checks if the node is in the contracted nodes.

        :param node: The node to check if it's contracted
        :type node: int
        :return: A boolean value.
        """
        return node in self.__contracted_nodes

    def add_node(self, node: int):
        """
        It adds a node to the set of contracted nodes

        :param node: the node to be added to the set of contracted nodes
        :type node: int
        """
        self.__contracted_nodes.add(node)

    def add_nodes(self, nodes: Iterable[int]):
        """
        This function adds a list of nodes to the set of contracted nodes

        :param nodes: list[int]
        :type nodes: list[int]
        """
        self.__contracted_nodes.update(nodes)


def edge_contraction(g: nx.Graph, return_all_steps=False) -> (Optional[list[nx.Graph]], set[tuple[int, int]]):
    """
    Takes a graph, performs the edge-contraction algorithm on it, returning the found cut and (optionally) a list of all
    the graphs obtained during the algorithm execution.

    :param g: The graph to find the cut of
    :type g: nx.Graph
    :param return_all_steps: If True, the algorithm will return a list of all the graphs it generated during the
        algorithm, defaults to False (optional)
    :return: The cut and the graphs obtained during the steps of the algorithm
    """
    g_copy = g.copy()
    supernodes = {node: SuperNode(node) for node in g_copy.nodes}
    alg_steps = None

    if return_all_steps:
        alg_steps = []

    while len(g_copy.nodes) > 2:

        # Choose random edge to contract
        edge = g.edges[randint(0, len(g.edges) - 1)]

        # If edge is (u, v), add v and all the nodes contracted in it into the u super-node
        supernodes[edge[0]].add_nodes(supernodes[edge[1]].contracted_nodes)

        # Contract edge
        g_copy = nx.algorithms.contracted_edge(g_copy, edge, self_loops=False)

        # Add algorithm step to output of required
        if return_all_steps:
            alg_steps.append(g_copy)

    # Get the two last super-nodes
    last_two_nodes = list(g_copy.nodes)
    u = supernodes[last_two_nodes[0]]
    v = supernodes[last_two_nodes[1]]

    cut = set([])
    # Get the edges between the two super-nodes, which represent the cut
    for edge in g.edges:
        x = edge[0]
        y = edge[1]
        if (u.contains(x) and v.contains(y)) or (u.contains(y) and v.contains(x)):
            cut.add(edge)

    return cut, alg_steps
