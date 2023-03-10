import random
from typing import Optional, final, Union
import dash.development.base_component
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import networkx as nx
from business.graph_functions import SuperNode
from business.utils import edge_cut_dataframe, EDGE_CUT_OUTPUT, EDGE_CUT_OPT, EDGE


_POSITION_ATTRIBUTE: final = "pos"
_X_MIN: final = 0
_X_MAX: final = 2
_Y_MIN: final = 0
_Y_MAX: final = 2

NORMAL_EDGE_COLOR: final = "#888"
SPECIAL_EDGE_COLOR: final = "#c71111"
COLOR_PLOT_PALETTE: final = "YlGnBu"
COLORS: final = {
    'background': '#111111',
    'text': '#7FDBFF'
}


def upload_button(text: str = "Upload CSV File", comp_id: str = "upload-btn") -> html.Div:
    return html.Div([
        dcc.Upload(html.Button(text), id=comp_id)
    ])


def content_modal(header_title: str, content: list[dash.development.base_component.Component]) -> (dbc.Button,
                                                                                                   dbc.Modal):
    btn = dbc.Button(children=["Cut comparison"], id="open-modal", n_clicks=0)
    modal = dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(header_title)),
            dbc.ModalBody(children=content),
            dbc.ModalFooter(
                dbc.Button(children=["Close"], id="close-modal", className="ms-auto btn-secondary", color="white", n_clicks=0)
            ),
        ],
        id="modal",
        is_open=False,
        size="xl"
    )
    return btn, modal


def edge_cut_tables(cut_edges_opt: set[tuple[int, int]], cut_edges_output: set[tuple[int, int]]) -> html.Div:

    df, jaccard_sim = edge_cut_dataframe(cut_edges_opt, cut_edges_output)

    if len(cut_edges_opt) == 0 and len(cut_edges_output) == 0:
        division = 1
    elif len(cut_edges_opt) == 0:
        division = 0
    else:
        division = len(cut_edges_output) / len(cut_edges_opt)

    df[EDGE] = df[EDGE].apply(lambda edge: str(edge))  # Convert tuples to string
    df[EDGE_CUT_OPT] = df[EDGE_CUT_OPT].apply(lambda x: "Yes" if x else "No")  # Convert bool to string
    df[EDGE_CUT_OUTPUT] = df[EDGE_CUT_OUTPUT].apply(lambda x: "Yes" if x else "No")  # Convert bool to string

    df.rename(
        columns={EDGE: "Edge", EDGE_CUT_OPT: 'Optimal Cut', EDGE_CUT_OUTPUT: 'Output Cut'}, inplace=True
    )  # Rename columns

    btn, modal = content_modal("Edge cut comparison table", content=[
        dbc.Table.from_dataframe(
            id="edge-cut-table",
            df=df,
            bordered=True,
            dark=True,
            hover=True,
            responsive=True,
            striped=True
        )
    ])

    return html.Div([
        btn,
        modal,
        dbc.Table(
            children=[
                html.Thead(html.Tr([html.Th("Jaccard similarity"), html.Th("|OUTPUT_CUT|/|OPT_CUT|")])),
                html.Tr([html.Td(str(round(jaccard_sim, 4))), html.Td(str(round(division, 4)))])
            ],
            id="metrics-table",
            bordered=True,
            dark=True,
            hover=True,
            responsive=True,
            striped=True
        )
    ])


def random_graph_options() -> html.Div:
    return html.Div([
        dbc.InputGroup([
            dbc.Input(type="number", min=1, max=1000, step=1, id="nodes", placeholder="Number of nodes"),
            dbc.Input(
                type="number",
                min=0,
                max=1,
                step=0.01,
                id="edge-prob",
                placeholder="Node proximity threshold for a edge to be added"
            ),
            dbc.Button("Generate random graph", id="random-graph-btn", n_clicks=0)
        ])
    ])


def algorithm_options() -> html.Div:
    return html.Div([
        dbc.InputGroup([
            html.Div([
                dbc.Label(children=[
                    html.Span("Show algorithm steps; recommended for small or sparse graphs only,"),
                    html.Br(),
                    html.Span([
                        "otherwise execution time will increase from:",
                        dcc.Markdown('$O\left(|V| + |E|\\right)$', mathjax=True),
                        "to",
                        dcc.Markdown('$O\left(|V| \\cdot \left(|V| + |E|\\right)\\right)$', mathjax=True)
                    ])
                ]),
                show_steps_radio()
            ], className="radio-container"),
            dbc.Input(type="number", min=1, max=100000, step=1, id="n_iter_max", placeholder="Max iterations"),
        ])
    ])


def show_steps_radio() -> html.Div:
    return html.Div(children=[dbc.RadioItems(
        id="radios",
        className="btn-group",
        inputClassName="btn-check",
        labelClassName="btn btn-outline-primary",
        labelCheckedClassName="active",
        options=[
            {"label": "Yes", "value": 1},
            {"label": "No", "value": 0}
        ],
        value=1,
    )])


def graph_plot(g: nx.Graph, title: str = "Your title", text: str = "Your text",  special_edges: Optional[set] = None,
               supernodes: Optional[dict[int, SuperNode]] = None):

    if special_edges is None:
        special_edges = set()

    # Set random node (x, y)-positions if not given
    if len(nx.get_node_attributes(g, "pos",)) == 0:
        pos = {i: (random.gauss(_X_MIN, _X_MAX), random.gauss(_Y_MIN, _Y_MAX)) for i in g.nodes}
        nx.set_node_attributes(g, pos, "pos")

    # Get edge coordinates
    edge_x = []
    edge_y = []
    edge_x_spec = []
    edge_y_spec = []
    for edge in g.edges():
        x0, y0 = g.nodes[edge[0]]['pos']
        x1, y1 = g.nodes[edge[1]]['pos']

        # Add to the normal edge to the corresponding list
        if edge not in special_edges and tuple(reversed(edge)) not in special_edges:
            edge_x.append(x0)
            edge_x.append(x1)
            edge_x.append(None)
            edge_y.append(y0)
            edge_y.append(y1)
            edge_y.append(None)

        # Add special edge to corresponding list
        else:
            edge_x_spec.append(x0)
            edge_x_spec.append(x1)
            edge_x_spec.append(None)
            edge_y_spec.append(y0)
            edge_y_spec.append(y1)
            edge_y_spec.append(None)

    # Plot edges
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color=NORMAL_EDGE_COLOR),
        hoverinfo='none',
        mode='lines'
    )

    # Plot special edges
    if len(edge_x_spec) > 0:
        edge_trace_spec = go.Scatter(
            x=edge_x_spec, y=edge_y_spec,
            line=dict(width=0.5, color=SPECIAL_EDGE_COLOR),
            hoverinfo='none',
            mode='lines'
        )
    else:
        edge_trace_spec = None

    # Get all node coordinates
    node_x = []
    node_y = []
    for node in g.nodes():
        x, y = g.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)

    # Plot nodes
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            # color-scale options
            # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            colorscale=COLOR_PLOT_PALETTE,
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    # Get node connections
    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(g.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        txt = f'Node: {adjacencies[0]}, # of connections: ' + str(len(adjacencies[1]))

        # Add super-node info if required
        if supernodes is not None:
            txt += f", Supernode info: {str(supernodes[adjacencies[0]])}"

        node_text.append(txt)

    # Add different colors based on the node degree
    node_trace.marker.color = node_adjacencies
    node_trace.text = node_text

    # Set plot data
    data = [edge_trace, node_trace]
    if edge_trace_spec is not None:
        data.append(edge_trace_spec)

    # Create the figure
    fig = go.Figure(
        data=data,
        layout=go.Layout(
            title=f'<br>{title}',
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text=f"{text}",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002)
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
    )
    return fig


def main_page() -> dbc.Container:
    return dbc.Container(style={'backgroundColor': COLORS['background']}, children=[
        html.H1(
            children=[html.A('ECVT: Edge Contraction Visualization Tool', href="/", style={
                "text-decoration": "none",
                "hoverable": False
            })],
            style={
                'textAlign': 'center',
                'color': COLORS['text'],
                "margin-top": "5%",
            }
        ),

        html.Div(children='Welcome to Edge Contraction algorithm Visualization Tool!', style={
            'textAlign': 'center',
            'color': COLORS['text']
        }),

        html.Div(
            className="graph-container",
            id="graph-container",
            children=[
                "To begin visualization, upload a csv containing graph edges or generate a random graph.",
                paginated([], display=False)
            ],
            style={
                'textAlign': 'center',
                'color': COLORS['text']
            }
        ),

        html.Div(
            id="user-input-div",
            children=[
                html.Div(
                    id="upload-btn-container",
                    children=[
                        upload_button(text="Upload CSV File", comp_id="upload-btn")
                    ],
                    style={
                        'color': COLORS['text'],
                        'textAlign': 'center',
                        'marginTop': '5%'
                    }
                ),
                html.P(["or"]),
                html.Div(
                    id="random-graph-options-container",
                    children=[
                        random_graph_options()
                    ]
                ),
                html.Div(
                    id="algorithm-options-container",
                    children=[
                        algorithm_options()
                    ]
                )
            ]
        ),
        html.Div(
            id="cut-tables-container",
            children=[
                edge_cut_tables(set([]), set([]))
            ]
        ),
        html.Div(
            id="refresh-btn",
            children=[dbc.Button(children=[html.A(children=["Restart"], href="/")])],
            style={
                'color': COLORS['text'],
                'textAlign': 'center',
                'marginTop': '5%'
            }
        ),
        html.Span(id="scrollUpBtn", children=[
            html.I(className="fa fa-chevron-up")
        ]),
    ])


def paginated(components: list[dash.development.base_component.Component], display: bool = True,
              contents_only: bool = False, index_to_display: int = 0) -> \
        Union[dash.development.base_component.Component, list[dash.development.base_component.Component]]:
    children = []

    for i in range(0, len(components)):

        # Select the index to display
        if i == index_to_display:
            class_name = "page toShow"
        else:
            class_name = "page"

        children.append(
            html.Div(className=class_name, id=f"page{i + 1}", children=[components[i]])
        )

    # If just contents are wanted, return them
    if contents_only:
        return children

    # Otherwise, create the entire page content and page numbers div
    storage = dcc.Store(id="current-contents")  # to store plots for pagination callbacks
    pages = html.Div(id="pagination-contents", children=children)
    if not display:
        pagination_container = html.Div(
            id="pagination-container",
            children=[storage, pages, dbc.Pagination(
                id="pagination",
                max_value=len(components),
                fully_expanded=False,
                first_last=True,
                previous_next=True
            )],
            style={"display": "none"}
        )
    else:
        pagination_container = html.Div(
            id="pagination-container",
            children=[storage, pages, dbc.Pagination(
                id="pagination",
                className="pagination-dark",
                max_value=len(components),
                fully_expanded=False,
                first_last=True,
                previous_next=True
            )]
        )
    return pagination_container
