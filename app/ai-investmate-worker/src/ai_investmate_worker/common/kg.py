import networkx as nx
import matplotlib.pyplot as plt
from networkx.readwrite import json_graph

def create_knowledge_graph(entities, relations):
    G = nx.DiGraph()

    for ent in entities:
        G.add_node(ent)

    for subj, rel, obj in relations:
        G.add_edge(subj, obj, relation=rel)

    return G

def serialize_knowledge_graph(G) -> dict:
    # Draw and display the graph
    pos = nx.spring_layout(G)
    plt.figure(figsize=(12, 12))
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=2500, font_size=10, font_weight='bold', edge_color='gray')
    nx.draw_networkx_edge_labels(G, pos, edge_labels={(u, v): d['relation'] for u, v, d in G.edges(data=True)}, font_color='red')
    data = json_graph.node_link_data(G)

    return data