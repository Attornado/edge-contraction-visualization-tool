import os
from random import randint
import networkx as nx
import plotly.express as px
import pandas as pd
from components import upload_button, graph_plot, main_page, COLORS, paginated, edge_cut_tables
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import business.utils as utl
import business.graph_functions as gf

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
     Output(component_id='user-input-div', component_property='style'),
     Output(component_id='refresh-btn', component_property='style'),
     Output(component_id='cut-tables-container', component_property='children'),
     Output(component_id='cut-tables-container', component_property='style')],
    [Input(component_id='upload-btn', component_property='contents'),
     Input(component_id="random-graph-btn", component_property="n_clicks")],
    [State(component_id='upload-btn', component_property='filename'),
     State(component_id="radios", component_property="value"),
     State(component_id="n_iter_max", component_property="value"),
     State(component_id='nodes', component_property="value"),
     State(component_id="edge-prob", component_property="value")],
    prevent_initial_call=True
)
def update_output_div(contents, n_clicks_random_graph, filename, show_steps: int, n_iter_max: int,
                      n_nodes_random_graph: int, edge_probability_random_graph: float):
    """
    Callback handling the user input and the visualization of the graphs.
    """

    # If filename is given then generate the graph corresponding to the file
    if filename:
        df = utl.parse_csv(contents, filename)
        g = gf.graph_from_df(df)

    # Otherwise, generate random graph with the specified number of nodes
    else:
        g = nx.random_geometric_graph(n_nodes_random_graph, edge_probability_random_graph)

    show_steps = bool(show_steps)

    # Find the best cut executing edge-contraction n_iter_max times
    if n_iter_max is None:
        n_iter_max = 1
    output_cut, alg_steps = gf.edge_contraction(g=g, return_all_steps=show_steps, max_iter=n_iter_max)

    # Find the optimal cut according to the Edmonds-Karp/Ford-Fulkerson algorithm
    opt_cut = gf.optimal_cut(g)

    # Generate figures of starting graph, algorithm steps (if required), edge-contraction cut and optimal cut
    figures = []
    graph_figures = []

    # Starting graph figure
    fig = graph_plot(g, title="Input graph", text=f"|V| = {len(g.nodes)}, |E| = {len(g.edges)}.")
    figures.append(fig)

    if show_steps:
        # For each algorithm step
        for alg_step in alg_steps:

            # Create a figure with the corresponding graph alongside other information on the execution step
            fig = graph_plot(
                g=alg_step.graph,
                title=f"Edge-contraction graph step #{alg_step.iter_number}",
                text=f"Contracted edge: {alg_step.contracted_edge}."
            )
            figures.append(fig)

    # Edge-contraction cut figure
    fig = graph_plot(
        g=g,
        title=f"Edge-contraction cut",
        text="Input graph with edge-contraction cut edges highlighted.",
        special_edges=output_cut
    )
    figures.append(fig)

    # Optimal cut figure
    fig = graph_plot(
        g=g,
        title=f"Optimal cut",
        text="Input graph with optimal cut edges highlighted.",
        special_edges=opt_cut
    )
    figures.append(fig)

    # Generate figure DOM elements
    for i in range(0, len(figures)):
        fig = figures[i]
        fig.update_layout(
            plot_bgcolor=COLORS['background'],
            paper_bgcolor=COLORS['background'],
            font_color=COLORS['text']
        )
        graph_fig = dcc.Graph(
            id=f'graph{i}',
            figure=fig
        )
        graph_figures.append(graph_fig)

    # Paginate the content
    paginated_graphs = paginated(graph_figures)


    """
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

    edges = list(g.edges)
    edge_cut_opt = edge_cut_output = set([edges[randint(0, len(edges) - 1)] for _ in range(0, len(edges)//3)])
    
    return [paginated_graphs], \
        {"display": "block"}, \
        graph_figs, \
        {"display": "none"}, \
        {"display": "block", 'color': COLORS['text'], 'textAlign': 'center', 'marginTop': '5%'}, \
        [edge_cut_tables(edge_cut_opt, edge_cut_output)], \
        {"display": "block"}
    """
    return [paginated_graphs], \
        {"display": "block"}, \
        graph_figures, \
        {"display": "none"}, \
        {"display": "block", 'color': COLORS['text'], 'textAlign': 'center', 'marginTop': '5%'}, \
        [edge_cut_tables(opt_cut, output_cut)], \
        {"display": "block"}


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


@app.callback(
    Output("modal", "is_open"),
    [Input("open-modal", "n_clicks"), Input("close-modal", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(
        host=os.getenv("HOST", "127.0.0.1"),
        port=os.getenv("PORT", "8050"),
        debug=True
    )
