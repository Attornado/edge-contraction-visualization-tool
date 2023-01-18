import base64
import io
from typing import final
import pandas as pd
from dash import html


EDGE_CUT_OPT: final = "edge_cut_opt"
EDGE_CUT_OUTPUT: final = "edge_cut_output"
EDGE: final = "edge"


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
