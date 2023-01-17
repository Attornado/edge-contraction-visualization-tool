import base64
import io
import pandas as pd
import plotly.graph_objs as go
from dash import html


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
