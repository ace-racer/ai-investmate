import requests
from typing import Union
from configs import BACKEND_URL
from models import ChatSession
import networkx as nx
from networkx.readwrite import node_link_graph
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np

def get_chat_response(chat_session: ChatSession) -> Union[ChatSession, str]:
    # Endpoint URL
    url = f"{BACKEND_URL}/chat"
    print(f"chat_session: {chat_session}")

    # Send POST request with chat history
    response = requests.post(url, json=chat_session.model_dump())

    # Check response
    if response.status_code == 200:
        print("Chat history sent successfully.")
        # Parse JSON response
        data = response.json()
        print("data:", data)
        return ChatSession.model_validate(data)
    else:
        print("Failed to send chat history. Status code:", response.status_code)
        print("Response body:", response.text)
        return response.text
    

def upload_file(file, file_name: str, description: str):
    url = f"{BACKEND_URL}/upload/"
    files = {'file': file}
    data = {'description': description, 'name': file_name}
    response = requests.post(url, files=files, data=data)
    return response


def format_dict_as_markdown(data):
    markdown_str = ""
    fe_mapping = {
        "search_queries": "Search queries",
        "raw_document_results": "Results from your documents",
        "raw_websearch_results": "Results from the web"
    }
    for key, values in data.items():
        markdown_str += f"### {fe_mapping[key]}\n"
        for value in values:
            markdown_str += f"- {value}\n"
        markdown_str += "\n"  # Add a new line for spacing
    return markdown_str


def fetch_graph_data():
    try:
        response = requests.get(f"{BACKEND_URL}/kg")
        response.raise_for_status()
        graph_data = response.json()
        return graph_data
    except Exception as e:
        print(f"An error occurred while trying to get the knowledge graph: {e}")
        return f"An error occurred while trying to get the knowledge graph: {e}"


# https://plotly.com/python/network-graphs/
def draw_graph_plotly(graph_response):
    graph_data = graph_response["graph"]
    entity_labels = graph_response.get("entity_labels", {})
    print(f"total labels: {len(entity_labels)}")
    # Create directed graph
    G = nx.DiGraph()
    # Add nodes
    for node in graph_data["nodes"]:
        G.add_node(node["id"])

    # Add edges
    for link in graph_data["links"]:
        G.add_edge(link["source"], link["target"], relation=link["relation"])

    # Position nodes in a spring layout
    pos = nx.spring_layout(G)

    # Calculate node sizes based on the number of incoming edges
    node_sizes = [G.in_degree[node] * 5 + 10 for node in G.nodes]

    # Generate node colors using a Plotly colormap
    node_colors = []
    colors = ['blue', 'green', 'red', 'purple', 'orange', 'violet', 'purple', 'pink', 'yellow', 'brown']  # List of colors
    if not entity_labels:
        for i, node in enumerate(G.nodes):
            node_colors.append(colors[i % len(colors)])  # Cycle through colors
    else:
        unique_labels = set(entity_labels[k] for k in entity_labels)
        label_color_mapping = {}
        for itr, label in enumerate(unique_labels):
            label_color_mapping[label] = colors[itr % len(colors)]
        for i, node in enumerate(G.nodes):
            node_colors.append(label_color_mapping[entity_labels[node]])

    # Create edge traces with hover text
    # https://plotly.com/python-api-reference/generated/plotly.graph_objects.Scatter.html
    edge_trace = []
    for edge in G.edges:
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        x_center = (x0 + x1) / 2
        y_center = (y0 + y1) / 2
        edge_trace.append(
            go.Scatter(
                x=[x0, x_center, x1, None],
                y=[y0, y_center, y1, None],
                line=dict(width=1, color='black'),
                hoverinfo='text',
                mode='lines+markers+text',
                hovertext=f"{edge[0]}->{edge[1]}[{G.edges[edge[0], edge[1]]['relation']}]",
                # text=f"{edge[0]}->{edge[1]}[{G.edges[edge[0], edge[1]]['relation']}]",
                textposition="middle center",
                marker=dict(
                size=[1, 6, 1],  # Different sizes for end points and the center marker
                color=['red', 'black', 'red'],  # Different colors for end points and the center marker
                symbol=['circle', 'square', 'circle']  # Different symbols for end points and the center marker
            )
                
            )
        )

    # Create node traces
    node_trace = go.Scatter(
        x=[pos[node][0] for node in G.nodes],
        y=[pos[node][1] for node in G.nodes],
        text=[node for node in G.nodes],
        mode='markers+text',
        textposition="bottom center",
        hoverinfo='text',
        marker=dict(
            size = node_sizes,
            color=node_colors
        )
    )

    # Add to the figure
    fig = go.Figure(data=edge_trace + [node_trace])

    # Update layout to remove axes and increase figure size
    fig.update_layout(
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        autosize=False,
        width=1000,
        height=800
    )

    return fig