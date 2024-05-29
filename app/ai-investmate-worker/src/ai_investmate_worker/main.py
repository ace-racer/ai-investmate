import modal
from modal import Image
from common.db import get_chat_sessions, add_kg
from common.ner_re import extract_entities_and_relations
from common.kg import create_knowledge_graph, serialize_knowledge_graph

app = modal.App(
    "aiinvestmate-chat-session-insights"
)

nlp_image = (
    Image.debian_slim()
        .pip_install("torch", "transformers", "faunadb==4.5.1", "sentence-transformers", "spacy==3.7.4", "matplotlib==3.9.0", "spacy-llm==0.7.2")
)


@app.function(image=nlp_image, secrets=[modal.Secret.from_name("ai-investmate-faunadb"), modal.Secret.from_name("ai-investmate-openai")], gpu="T4", schedule=modal.Cron("0 7 * * *"), timeout=3600)
def generate_knowledge_graph():
    current_chat_sessions = get_chat_sessions()
    all_chat_session_content = []
    chat_sessions_processed = 0
    for chat_session in current_chat_sessions:
        session_id = chat_session["session_id"]
        print(f"session_id: {session_id}")
        # Extract the content from the data
        history_contents = [entry['content'] for entry in chat_session['conversation_history']]
        meta_contents = []
        for message in chat_session['conversation_history']:
            if "meta" in message:
                for metakey in message["meta"]:
                    meta_contents.extend(message["meta"][metakey])

        # Combine the content into a single list of chat_session
        chat_session_content = history_contents + meta_contents
        # Check the resulting chat_session_content
        print(f"len(chat_session_content): {len(chat_session_content)}")
        all_chat_session_content.extend(chat_session_content)
        chat_sessions_processed += 1

    print(f"len(all_chat_session_content): {len(all_chat_session_content)}")
    # get_topics_from_chat_session(all_chat_session_content)
    entities, relations, entity_labels = extract_entities_and_relations(all_chat_session_content)
    G = create_knowledge_graph(entities, relations)
    G_dict = serialize_knowledge_graph(G)
    print(f"G_dict: {G_dict}")
    add_kg(G_dict, entity_labels)

    return chat_sessions_processed


@app.local_entrypoint()
def main():
    conversations_processed = generate_knowledge_graph.remote()
    print("total conversations sessions processed", conversations_processed)