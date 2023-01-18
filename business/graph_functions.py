from __future__ import annotations  # enable type annotation
from typing import Optional, Iterable, Union
import networkx as nx
from business.utils import ListDict


class SuperNode(object):
    def __init__(self, node: int):
        """
        This class represents a super-node in the edge contraction algorithm, and it is characterized by a node
        identifier and a set of contracted nodes.

        :param node: The supernode.
        :type node: int
        """
        self.__node = node
        self.__contracted_nodes = {node}  # init with the node itself

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

    def contract(self, supernode: Union[SuperNode, int]):
        """
        Takes a supernode as an argument and adds the supernode's contracted nodes to the graph.

        :param supernode: the supernode that is being contracted
        """
        if type(supernode) == SuperNode:
            self.add_nodes(supernode.contracted_nodes)
        elif type(supernode) == int:
            self.add_node(supernode)


def replace_edges_incident_to_contracted_node(edges: ListDict, contracted_incident_edges: list[tuple[int, int]],
                                              contracting_node: int, contracted_node: int):
    """
    For each edge incident to the contracted node, remove it from the edge list-dict and replace it with the new edge
    incident to the contracting node

    :param edges: The list-dict of edges in the graph
    :type edges: ListDict
    :param contracted_incident_edges: a list of tuples of the form (v, w) or (w, v) where v is the contracted node and w
        is the other node in the edge
    :type contracted_incident_edges: list[tuple[int, int]]
    :param contracting_node: The node that is being contracted
    :type contracting_node: int
    :param contracted_node: the node that is being contracted
    :type contracted_node: int
    """

    # For each (v, w) or (w, v) edge incident to the contracted node
    for incident_edge in contracted_incident_edges:

        # If the edge is not the contracted one (u, v) or (v, u)
        if incident_edge[0] != contracting_node and incident_edge[1] != contracting_node:

            # Remove the edge (v, w) or (v, w) from the edge list-dict
            if incident_edge in edges:
                edges.remove(incident_edge)
            else:
                edges.remove(tuple(reversed(incident_edge)))

            # Replace the removed edge with the new edge (u, w) or (w, u)
            if incident_edge[0] == contracted_node:
                new_edge = (contracting_node, incident_edge[1])
            else:
                new_edge = (contracting_node, incident_edge[0])

            if tuple(reversed(new_edge)) not in edges:
                edges.add(new_edge)


def edge_contraction(g: nx.Graph, return_all_steps: bool = False) -> (Optional[list[nx.Graph]], set[tuple[int, int]]):
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
    remaining_edges = ListDict(g_copy.edges)  # list-dict representing the remaining edges

    if return_all_steps:
        alg_steps = []

    while len(g_copy.nodes) > 2:

        # Choose random edge to contract
        edge = remaining_edges.choose_random()

        # Remove contracted edge from remaining edges
        remaining_edges.remove(edge)

        # Replace (v, w) and (w, v) edges with (u, w) edges, if v is contracted into u
        incident = g_copy.edges(edge[1])
        replace_edges_incident_to_contracted_node(
            edges=remaining_edges,
            contracted_incident_edges=incident,
            contracting_node=edge[0],
            contracted_node=edge[1]
        )

        # If edge is (u, v), add v and all the nodes contracted in it into the u super-node
        supernodes[edge[0]].contract(supernodes[edge[1]])

        # Contract edge
        g_copy = nx.algorithms.contracted_edge(g_copy, edge, self_loops=False)

        # Add algorithm step graph to output if required
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
        if (u.contains(x) and v.contains(y)) or (u.contains(y) and v.contains(x)) and tuple(reversed(edge)) not in cut:
            cut.add(edge)

    return cut, alg_steps
