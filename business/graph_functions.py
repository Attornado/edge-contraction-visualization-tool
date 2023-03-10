from __future__ import annotations  # enable type annotation with a certain class within the same class definition
from typing import Optional, Iterable, Union
import networkx as nx
import pandas as pd
from business.utils import ListDict, EDGE, parse_tuple


class EdgeContractionStep(object):
    def __init__(self, graph: nx.Graph, supernodes: dict[int, SuperNode], contracted_edge: tuple[int, int],
                 iter_number: int):
        """
        This class represent a step of the edge contraction algorithm, characterized by an iteration number, a dict of
        super-nodes, the graph at that given step and the edge that has been contracted to obtain that graph.

        :param graph: The graph at that given algorithm step
        :type graph: nx.Graph
        :param supernodes: The supernodes corresponding to the graph node at the given step.
        :type supernodes: dict[int, SuperNode]
        :param contracted_edge: The edge that has been contracted to obtain that graph
        :type contracted_edge: tuple[int, int]
        :param iter_number: The iteration number of the algorithm step
        :type iter_number: int
        """
        self.__graph = graph
        self.__supernodes = supernodes
        self.__contracted_edge = contracted_edge
        self.__iter_number = iter_number

    @property
    def graph(self) -> nx.Graph:
        """
        The graph at the given step of the edge-contraction algorithm.
        :return: The graph is being returned.
        """
        return self.__graph

    @property
    def contracted_edge(self) -> tuple[int, int]:
        """
        This function returns the edge that has been contracted to obtain the graph in this step of the algorithm.
        :return: The contracted edge.
        """
        return self.__contracted_edge

    @property
    def iter_number(self) -> int:
        """
        Returns the iteration number of the algorithm step.
        :return: The number of iterations.
        """
        return self.__iter_number

    @property
    def supernodes(self) -> dict[int, SuperNode]:
        """
        Returns a list of all the supernodes in the graph.
        :return: A list of SuperNode objects.
        """
        return self.__supernodes

    def get_super_node(self, node: int) -> SuperNode:
        """
        Returns the supernode corresponding to the given node.

        :param node: The node to get the supernode for
        :type node: int
        :return: The supernode corresponding to the node.
        """
        return self.__supernodes[node]

    def __str__(self):
        supernodes_str = ""
        for supernode in self.__supernodes:
            supernodes_str += str(supernode) + "\n"
        return str({
            "Super-Nodes": supernodes_str,
            "Edges": list(self.__graph.edges),
            "Contracted edge": self.__contracted_edge,
            "Iteration number": self.__iter_number
        })


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

    def clone(self) -> SuperNode:
        cloned = SuperNode(self.__node)
        cloned.add_nodes(self.contracted_nodes)
        return cloned

    def __str__(self):
        return str({self.__node: str(self.__contracted_nodes)})


def _copy_supernodes(supernodes: dict[int, SuperNode]) -> dict[int, SuperNode]:
    """
    Creates a new dictionary of supernodes, where each supernode is a clone of the corresponding supernode in the input
    dictionary.

    :param supernodes: dict[int, SuperNode]
    :type supernodes: dict[int, SuperNode]
    :return: A dictionary of SuperNodes
    """
    copied = {}
    for node in supernodes:
        copied[node] = supernodes[node].clone()
    return copied


def _replace_edges_incident_to_contracted_node(edges: ListDict, contracted_incident_edges: list[tuple[int, int]],
                                               contracted_node: int, contracting_node: int):
    """
    For each edge (v, w)/(w, v) edge incident to the contracted node v, remove it from the edge list-dict and replace it
    with the new edge (u, w)/(w, u) incident to the contracting node.

    :param edges: The list-dict of edges in the graph
    :type edges: ListDict
    :param contracted_incident_edges: a list of edges of the form (v, w) or (w, v), where v is the contracted node and w
        is the other node in the edge
    :type contracted_incident_edges: list[tuple[int, int]]
    :param contracted_node: the node that is being contracted
    :type contracted_node: int
    :param contracting_node: The node that in which the contracted_node is being contracted
    :type contracting_node: int
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


def _edge_contraction(g: nx.Graph, return_all_steps: bool = False, log: bool = False) -> \
        (set[tuple[int, int]], Optional[list[EdgeContractionStep]]):
    """
    Takes a graph, performs the edge-contraction algorithm on it, returning the found cut and (optionally) a list of
    objects describing the graphs obtained during the algorithm execution.

    :param g: The graph to find the cut of
    :type g: nx.Graph
    :param return_all_steps: If True, the algorithm will return a list of all the graphs it generated during the
        algorithm, defaults to False (optional)
    :type return_all_steps: bool
    :param log: If True, a log of every contraction will be generated.
    :type log: bool

    :return: The cut and the graphs obtained during the steps of the algorithm
    """

    g_copy = g.copy()
    supernodes = {node: SuperNode(node) for node in g_copy.nodes}
    alg_steps = None
    remaining_edges = ListDict(g_copy.edges)  # list-dict representing the remaining edges
    iter_number = 0

    if return_all_steps:
        alg_steps = []

    while len(g_copy.nodes) > 2:

        # Choose random edge to contract
        edge = remaining_edges.choose_random()

        # Remove contracted edge from remaining edges
        remaining_edges.remove(edge)

        # Replace (v, w) and (w, v) edges with (u, w) edges, if v is contracted into u
        incident = g_copy.edges(edge[1])
        _replace_edges_incident_to_contracted_node(
            edges=remaining_edges,
            contracted_incident_edges=incident,
            contracting_node=edge[0],
            contracted_node=edge[1]
        )

        # If edge is (u, v), add v and all the nodes contracted in it into the u super-node
        supernodes[edge[0]].contract(supernodes[edge[1]])

        # Generate contraction log if required
        if log:
            print(f"Contracting edge '{edge}', collapsing supernode '{edge[1]}' into '{edge[0]}' \n"
                  f"New supernode '{edge[0]}': {str(supernodes[edge[0]])}")

        # Contract edge
        g_copy = nx.algorithms.contracted_edge(g_copy, edge, self_loops=False)

        # Add algorithm step graph to output if required
        if return_all_steps:
            # Handle multiple copies of supernodes for each step of the algorithm
            # Though inefficient, it can be acceptable since we are doing this just on small graphs for visualization
            # purposes only, and this is not done in other cases
            edge_contraction_step = EdgeContractionStep(
                graph=g_copy,
                supernodes=_copy_supernodes(supernodes),  # inefficient, but necessary for visualization purposes
                contracted_edge=edge,
                iter_number=iter_number
            )
            alg_steps.append(edge_contraction_step)

        iter_number += 1

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


def edge_contraction(g: nx.Graph, return_all_steps: bool = False, log: bool = False, max_iter: int = 1) -> \
        (set[tuple[int, int]], Optional[list[EdgeContractionStep]]):
    """
    Takes a graph, repeats the execution of the edge-contraction algorithm on it for the given maximum number
    iterations, returning the found cut and (optionally) a list of objects describing the graphs obtained during the
    best execution. If the given graph is not connected, an empty cut is returned.

    :param g: The graph to find a cut of
    :type g: nx.Graph
    :param return_all_steps: If True, the algorithm will return a list of all the graphs it generated during the
        algorithm, defaults to False
    :param log: If True, a log of every contraction in each execution will be generated.
    :type log: bool
    :param max_iter: An integer representing the maximum number of executions of the edge contraction algorithm to
        perform, defaults to 1
    :type max_iter: int

    :return: The cut and the graphs obtained during the steps of the algorithm
    """
    # Initialize best cut size, best cut and best algorithm execution history
    best_cut_size = -1
    best_cut = set()
    best_alg_steps = None

    # If the given graph is not connected, return empty cut
    if not nx.is_connected(g):
        if return_all_steps:
            best_alg_steps = []
        return best_cut, best_alg_steps

    # Otherwise execute the algorithm max_iter times, choosing the best cut
    for i in range(0, max_iter):
        cut, alg_steps = _edge_contraction(g=g, return_all_steps=return_all_steps, log=log)

        if best_cut_size == -1 or len(cut) < best_cut_size:
            best_cut_size = len(cut)
            best_cut = cut
            best_alg_steps = alg_steps

    return best_cut, best_alg_steps


def graph_from_df(df: pd.DataFrame) -> nx.Graph:
    """
    Takes a dataframe with an edge column, and it returns a networkx graph containing the read edges.

    :param df: pd.DataFrame containing the edge information
    :type df: pd.DataFrame
    :return: A graph object with the read edges
    """

    # Convert read strings into tuples
    df[EDGE] = df[EDGE].apply(lambda edge: parse_tuple(edge) if type(edge) == str else edge)
    edges = df[EDGE].to_list()

    # Create graph
    g = nx.Graph()
    g.add_edges_from(edges)

    return g


def optimal_cut(g: nx.Graph) -> set[tuple[int, int]]:
    """
    Returns the minimum edge cut of the graph, applying the Edmonds-Karp or the Ford-Fulkerson algorithm.

    :param g: nx.Graph
    :type g: nx.Graph
    :return: A set of edges that, if removed, would disconnect G. If source and target nodes are provided, the set
        contains the edges that if removed, would destroy all paths between source and target.
    """
    if nx.is_connected(g):
        return nx.algorithms.minimum_edge_cut(g)
    else:
        return set()
