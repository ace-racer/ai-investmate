import streamlit as st
from utils import get_chat_response, upload_file, format_dict_as_markdown, fetch_graph_data, draw_graph_plotly
import time
from models import ChatSession, ChatMessage

st.set_page_config(page_title="AIInvestmate")
st.title(f"AIInvestmate")

# Sidebar for inputs
with st.sidebar:
    uploaded_file = st.file_uploader("Choose a file", type=['pdf'])
    name = st.text_input("A friendly file name")
    description = st.text_input("File description")
    upload_button = st.button("Upload File")
    st.text("")
    st.text("")
    st.markdown("***")
    show_knowledge_graph = st.button("Show accumulated knowledge")

if show_knowledge_graph:
    print("Showing knowledge graph")
    with st.spinner("Displaying graph..."):
        graph_data = fetch_graph_data()
        print(f"Retrieved graph_data: {graph_data}")
        if graph_data:
                # Save the graph data to a session state
                st.session_state.graph_data = graph_data
                fig = draw_graph_plotly(st.session_state.graph_data)
                # https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart
                st.plotly_chart(fig)

        else:
            st.error("Failed to retrieve graph data")

# Check if the button is pressed and the file is uploaded
if upload_button and uploaded_file:
    file_bytes = uploaded_file.getvalue()
    response = upload_file(file_bytes, name, description)
    if response.status_code == 200:
        st.success(f"{response.json()['message']}")
    else:
        st.error("Failed to upload the file")

if "chat_session" not in st.session_state:
    st.session_state.chat_session = ChatSession(session_id=str(int(time.time())), conversation_history=[])

for message in st.session_state.chat_session.conversation_history:
    with st.chat_message(message.role):
        st.markdown(message.content)
        if message.meta and len(message.meta) > 0:
            meta_expander = st.expander(label="More details")
            with meta_expander:
                # Convert the dictionary to a Markdown formatted string
                formatted_data = format_dict_as_markdown(message.meta)
                st.markdown(formatted_data)

if prompt := st.chat_input("What is up?"):
    st.session_state.chat_session.conversation_history.append(ChatMessage(role="user", content=prompt, meta=None))
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Waiting..."):
            updated_chat_session = get_chat_response(st.session_state.chat_session)
            if isinstance(updated_chat_session, ChatSession):
                latest_message = updated_chat_session.conversation_history[-1]
                message_placeholder.markdown(latest_message.content)
                st.session_state.chat_session.conversation_history.append(ChatMessage(role="assistant", content=latest_message.content, meta=latest_message.meta))
                if latest_message.meta and len(latest_message.meta) > 0:
                    meta_expander = st.expander(label="More details")
                    with meta_expander:
                        # Convert the dictionary to a Markdown formatted string
                        formatted_data = format_dict_as_markdown(latest_message.meta)
                        st.markdown(formatted_data)
            else:
                st.error(f"An error occurred. Details: {updated_chat_session}. Please retry.")
