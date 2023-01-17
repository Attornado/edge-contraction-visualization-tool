import random
from typing import Optional, final, Union
import dash.development.base_component
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import networkx as nx


_POSITION_ATTRIBUTE: final = "pos"
_X_MIN: final = 0
_X_MAX: final = 2
_Y_MIN: final = 0
_Y_MAX: final = 2

NORMAL_EDGE_COLOR: final = "#888"
SPECIAL_EDGE_COLOR: final = "#c71111"
COLOR_PLOT_PALETTE: final = "YlGnBu"
COLORS = {
    'background': '#111111',
    'text': '#7FDBFF'
}


def upload_button(text: str = "Upload CSV File", comp_id: str = "upload-btn", edges: Optional[set] = None):
    return html.Div([
        dcc.Upload(html.Button(text), id=comp_id)
    ])


def graph_plot(g: nx.Graph, title: str = "Your title", text: str = "Your text",  special_edges: Optional[set] = None):

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
        if edge not in special_edges:
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
            # colorscale options
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
        node_text.append('# of connections: ' + str(len(adjacencies[1])))

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


def refresh_page_btn():
    return html.A(html.Button('Refresh Data'), href='/')


def main_page():
    return dbc.Container(style={'backgroundColor': COLORS['background']}, children=[
        html.H1(
            children='ECVT: Edge Contraction Visualization Tool',
            style={
                'textAlign': 'center',
                'color': COLORS['text']
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
                "To begin visualization, upload a csv containing graph edges.",
                paginated([], display=False)
            ],
            style={
                'textAlign': 'center',
                'color': COLORS['text']
            }
        ),

        html.Div(
            id="upload-btn-container",
            children=[upload_button(text="Upload CSV File", comp_id="upload-btn")],
            style={
                'color': COLORS['text'],
                'textAlign': 'center',
                'marginTop': '5%'
            }
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
            children=[storage, pages, dbc.Pagination(id="pagination", max_value=len(components), fully_expanded=False)],
            style={"display": "none"}
        )
    else:
        pagination_container = html.Div(
            id="pagination-container",
            children=[storage, pages, dbc.Pagination(id="pagination", max_value=len(components), fully_expanded=False)]
        )
    return pagination_container
