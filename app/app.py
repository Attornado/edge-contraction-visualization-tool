import os
from typing import final
import networkx as nx
from components import graph_plot, main_page, COLORS, paginated, edge_cut_tables
from dash import Dash, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import business.utils as utl
import business.graph_functions as gf


EXTERNAL_STYLESHEETS: final = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css',
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css",
    dbc.themes.BOOTSTRAP
]
EXTERNAL_SCRIPTS: final = [
    "https://ajax.googleapis.com/ajax/libs/jquery/3.6.1/jquery.min.js"
]
LOG_CONTRACTION: final = False

app = Dash(__name__, external_stylesheets=EXTERNAL_STYLESHEETS, external_scripts=EXTERNAL_SCRIPTS)

# Build the app page
app.layout = main_page()


# Callbacks
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
def update_output_div(contents, _, filename, show_steps: int, n_iter_max: int,
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
    output_cut, alg_steps = gf.edge_contraction(
        g=g,
        return_all_steps=show_steps,
        max_iter=n_iter_max,
        log=LOG_CONTRACTION
    )

    # Find the optimal cut according to the Edmonds-Karp/Ford-Fulkerson algorithm
    opt_cut = gf.optimal_cut(g)

    # Generate figures of starting graph, algorithm steps (if required), edge-contraction cut and optimal cut
    figures = []
    graph_figures = []

    # Starting graph figure
    if show_steps and len(alg_steps) > 0:
        first_edge = alg_steps[0].contracted_edge  # show info on the first contracted edge if required
        fig = graph_plot(
            g=g,
            title="Input graph",
            text=f"|V| = {len(g.nodes)}, |E| = {len(g.edges)}, selected edge: {first_edge}.",
            special_edges={first_edge}
        )
    else:
        fig = graph_plot(g, title="Input graph", text=f"|V| = {len(g.nodes)}, |E| = {len(g.edges)}.")
    figures.append(fig)

    if show_steps:
        # For each algorithm step
        for i in range(0, len(alg_steps)):

            alg_step = alg_steps[i]  # current algorithm step info

            # If current step isn't the last one
            if alg_step.iter_number < len(alg_steps) - 1:

                alg_step_next = alg_steps[i + 1]  # next algorithm step info
                # Create a figure with the corresponding graph alongside other information on the execution step
                fig = graph_plot(
                    g=alg_step.graph,
                    title=f"Edge-contraction graph step #{alg_step.iter_number + 1}",
                    text=f"Contracted edge: {alg_step.contracted_edge}, "
                         f"selected edge: {alg_step_next.contracted_edge}.",
                    supernodes=alg_step.supernodes,
                    special_edges={alg_step_next.contracted_edge}  # highlight the next edge to contract
                )
                figures.append(fig)

            else:
                # Create a figure with the corresponding graph alongside other information on the execution step
                fig = graph_plot(
                    g=alg_step.graph,
                    title=f"Edge-contraction graph step #{alg_step.iter_number + 1}.",
                    text=f"Contracted edge: {alg_step.contracted_edge}.",
                    supernodes=alg_step.supernodes
                )
                figures.append(fig)

    # Edge-contraction cut figure
    fig = graph_plot(
        g=g,
        title=f"Edge-contraction cut",
        text=f"Input graph with edge-contraction cut edges highlighted. |OUTPUT_CUT| = {len(output_cut)}.",
        special_edges=output_cut
    )
    figures.append(fig)

    # Optimal cut figure
    fig = graph_plot(
        g=g,
        title=f"Optimal cut",
        text=f"Input graph with optimal cut edges highlighted. |OPT_CUT| = {len(opt_cut)}.",
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
            figure=fig,
            className="interactive-plot"
        )
        graph_figures.append(graph_fig)

    # Paginate the content
    paginated_graphs = paginated(graph_figures)

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
    """
    It takes a page number and a list of page contents, and returns the contents of the page number that was passed in.

    :param page: the page number to display
    :param page_contents: the contents of the page
    :return: A list of strings.
    """
    new_pages = paginated(page_contents, contents_only=True, index_to_display=page - 1)

    return new_pages


@app.callback(
    Output("modal", "is_open"),
    [Input("open-modal", "n_clicks"), Input("close-modal", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    """
    If either n1 or n2 is true, return the opposite of is_open, otherwise return is_open

    :param n1: The first number to be compared
    :param n2: The number of times the button has been clicked
    :param is_open: This is the boolean value that determines whether the modal is open or not
    :return: the opposite of the is_open argument.
    """
    if n1 or n2:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(
        host=os.getenv("HOST", "127.0.0.1"),
        port=os.getenv("PORT", "8050"),
        debug=True
    )
