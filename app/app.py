import os
import networkx as nx
import plotly.express as px
import pandas as pd
from components import upload_button, graph_plot, main_page, COLORS, paginated
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import business.utils as utl

external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css",
    dbc.themes.BOOTSTRAP
]

external_scripts = [
    "https://ajax.googleapis.com/ajax/libs/jquery/3.6.1/jquery.min.js"
]

app = Dash(__name__, external_stylesheets=external_stylesheets, external_scripts=external_scripts)

# Build the app page
app.layout = main_page()


# Callbacks, eventually move these to another file
@app.callback(
    [Output(component_id='graph-container', component_property='children'),
     Output(component_id='pagination-container', component_property='style'),
     Output(component_id='current-contents', component_property="data"),
     Output(component_id='upload-btn', component_property='style'),
     Output(component_id='refresh-btn', component_property='style')],
    Input(component_id='upload-btn', component_property='contents'),
    State(component_id='upload-btn', component_property='filename'),
    prevent_initial_call=True
)
def update_output_div(contents, filename):
    g = nx.random_geometric_graph(50, 0.1)

    g = nx.Graph()

    g.add_edges_from([(1, i) for i in range(2, 200)])

    special_edges = set([(1, i) for i in range(2, 50)])

    fig = graph_plot(g, "ciao grafo", text="descrizione", special_edges=special_edges)

    fig.update_layout(
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['background'],
        font_color=COLORS['text']
    )

    graph_fig = dcc.Graph(
        id='graph',
        figure=fig
    )

    fig = graph_plot(g, "ciao grafo2", text="descrizione", special_edges=special_edges)

    fig.update_layout(
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['background'],
        font_color=COLORS['text']
    )

    graph_fig2 = dcc.Graph(
        id='graph2',
        figure=fig
    )

    fig = graph_plot(g, "ciao grafo3", text="descrizione", special_edges=special_edges)

    fig.update_layout(
        plot_bgcolor=COLORS['background'],
        paper_bgcolor=COLORS['background'],
        font_color=COLORS['text']
    )

    graph_fig3 = dcc.Graph(
        id='graph3',
        figure=fig
    )

    graph_figs = [graph_fig, graph_fig2, graph_fig3]

    paginated_graphs = paginated(graph_figs)

    return [paginated_graphs], \
        {"display": "block"}, \
        graph_figs, \
        {"display": "none"}, \
        {"display": "block", 'color': COLORS['text'], 'textAlign': 'center', 'marginTop': '5%'}


# Pagination callback
@app.callback(
    Output("pagination-contents", "children"),
    Input("pagination", "active_page"),
    State(component_id="current-contents", component_property="data"),
    prevent_initial_call=True
)
def change_page(page, page_contents):
    new_pages = paginated(page_contents, contents_only=True, index_to_display=page - 1)

    return new_pages


if __name__ == '__main__':
    app.run_server(
        host=os.getenv("HOST", "127.0.0.1"),
        port=os.getenv("PORT", "8050"),
        debug=True
    )
