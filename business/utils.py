import ast
import base64
import io
from typing import final, Iterable, Optional
import pandas as pd
from dash import html
import random


EDGE_CUT_OPT: final = "edge_cut_opt"
EDGE_CUT_OUTPUT: final = "edge_cut_output"
EDGE: final = "edge"


def parse_tuple(string: str):
    """
    Takes a string, evaluates it as a Python expression, and returns the result if it's a tuple.

    :param string: str
    :type string: str
    :return: A tuple of the form (x_1, x_2, ..., x_n)
    """
    s = ast.literal_eval(str(string))
    if type(s) == tuple:
        return s
    else:
        raise ValueError("Given string is not a tuple.")


def parse_csv(contents, filename):
    """
    It takes a file that's been uploaded by the user, and returns a pandas dataframe.

    :param contents: the contents of the uploaded file
    :param filename: The name of the uploaded file
    :return: A dataframe
    """
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    df = None
    try:
        if "csv" in filename:
            # Assume that the user uploaded a CSV or TXT file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif "xls" in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        elif "txt" or "tsv" in filename:
            # Assume that the user upl, delimiter = r'\s+'oaded an excel file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")), delimiter=r"\s+")
    except Exception as e:
        print(e)
        return html.Div(["There was an error processing this file."])

    return df


def edge_cut_dataframe(cut_edges_opt: set[tuple[int, int]], cut_edges_output: set[tuple[int, int]]) -> (pd.DataFrame,
                                                                                                        float):
    """
    It takes the optimal cut and the output cut and returns a dataframe
    with the following columns, as well as the Jaccard similarity between the output and optimal cut:

    - EDGE: the edge
    - EDGE_CUT_OPT: True if the edge is in the optimal cut, False otherwise
    - EDGE_CUT_OUTPUT: True if the edge is in the output cut, False otherwise

    :param cut_edges_opt: the set of edges in the optimal cut
    :type cut_edges_opt: set[tuple[int, int]]
    :param cut_edges_output: the edges of the cut found by the algorithm
    :type cut_edges_output: set[tuple[int, int]]
    :return: A float indicating the Jaccard similarity between the optimal cut and the output cut, and a dataframe with
    the following columns:

        - EDGE: the edge
        - EDGE_CUT_OPT: True if the edge is in the optimal cut, False otherwise
        - EDGE_CUT_OUTPUT: True if the edge is in the output cut, False otherwise

    """

    cut_edges_output = set(cut_edges_output)  # copy cut_edges_output to avoid side-effects
    df = pd.DataFrame(columns=[EDGE, EDGE_CUT_OUTPUT, EDGE_CUT_OPT])  # output dataframe
    count = 0  # index of the last element added to the dataframe
    count_intersection = 0

    # Add edges of the optimal cut to the dataframe
    for edge in cut_edges_opt:
        reverse_edge = (edge[1], edge[0])  # reverse edge check too because the graph is indirected
        if edge in cut_edges_output or reverse_edge in cut_edges_output:
            if reverse_edge in cut_edges_output:
                cut_edges_output.remove(reverse_edge)
            else:
                cut_edges_output.remove(edge)
            df.loc[count] = {EDGE: edge, EDGE_CUT_OUTPUT: True, EDGE_CUT_OPT: True}
            count_intersection += 1
        else:
            df.loc[count] = {EDGE: edge, EDGE_CUT_OUTPUT: False, EDGE_CUT_OPT: True}
        count += 1

    # Add edges of the output cut to the dataframe
    for edge in cut_edges_output:
        df.loc[count] = {EDGE: edge, EDGE_CUT_OUTPUT: True, EDGE_CUT_OPT: False}
        count += 1

    if count == 0:
        jaccard_sim = 0
    else:
        jaccard_sim = count_intersection / count

    return df, jaccard_sim


class ListDict(object):
    def __init__(self, initial_values: Optional[Iterable] = None):
        """
        This class represent a list of items paired with a dictionary, which maps each item (that must be hash-able) to
        the corresponding position, hallowing to do operations like delete, retrieve and insert in O(1) time, as well as
        random selection.
        """
        self.__item_to_position = {}
        self.__items = []

        if initial_values is not None:
            self.extend(initial_values)

    def extend(self, items: Iterable):
        """
        Add a list of items to the list-dict.

        :param items: Iterable containing items to add to the list-dict
        :type items: Iterable
        """
        for item in items:
            self.add(item)

    def add(self, item):
        """
        Adds an element to the list-dict in O(1) time.

        :param item: The item to add to the list
        :return: The position of the item in the list.
        """
        if item in self.__item_to_position:
            return
        self.__items.append(item)
        self.__item_to_position[item] = len(self.__items) - 1

    def remove(self, item):
        """
        Removes the item from the list in O(1) time.

        :param item: The item to remove from the set
        """
        position = self.__item_to_position.pop(item)
        last_item = self.__items.pop()
        if position != len(self.__items):
            self.__items[position] = last_item
            self.__item_to_position[last_item] = position

    def choose_random(self, sample_size: int = 1):
        """
        Returns a random item from the list-dict of items in O() time, where k is the required sample size.

        :param sample_size: sample size.

        :return: A list with sample_size random items from the list-dict if sample_size > 1, a single random item with
            if sample_size = 1.
        """
        random_items = []
        for _ in range(0, sample_size):
            random_items.append(random.choice(self.__items))
        if sample_size == 1:
            return random_items[0]
        else:
            return random_items

    def position(self, item) -> int:
        """
        It returns the position of the item in the list-dict.

        :param item: The item to find the position of
        :return: The position of the item in the list-dict.
        """
        return self.__item_to_position[item]

    def to_list(self) -> list:
        """
        Returns a list containing all the items in the list-dict.

        :return: the contents of the list-dict as a list.
        :rtype: list
        """
        return list(self.__items)

    def __getitem__(self, index):
        """
        Returns the item at the given index.

        :param index: The index of the item you want to retrieve
        :return: The item at the given index.
        """
        return self.__items[index]

    def __contains__(self, item):
        """
        If the item is in the dictionary, return True. Otherwise, return False. This runs in O(1) time.

        :param item: The item to check for membership
        :return: The position of the item in the list.
        """
        return item in self.__item_to_position

    def __iter__(self):
        """
        Returns an iterator object that can be used to iterate over the items in the list-dict.
        :return: The iter() function is being called on the list of items.
        """
        return iter(self.__items)

    def __len__(self):
        """
        The function returns the length of the list-dict of items.
        :return: The length of the list-dict.
        """
        return len(self.__items)

    def __str__(self):
        return str(self.__items) + "\n" + str(self.__item_to_position)
