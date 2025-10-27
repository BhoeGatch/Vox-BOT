import streamlit as st
from ingestion import load_documents
from search import SearchEngine
from logger import log_interaction
import os

st.title("WNS Vox BOT – Agent Assist")
st.sidebar.checkbox("Show debug", key="__debug__")

# Sidebar for document management
st.sidebar.header("Document Management")
uploaded_files = st.sidebar.file_uploader("Upload documents", accept_multiple_files=True, type=['pdf', 'docx', 'txt'])
if uploaded_files:
    data_folder = 'data'
    os.makedirs(data_folder, exist_ok=True)
    for uploaded_file in uploaded_files:
        file_path = os.path.join(data_folder, uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
    st.sidebar.success("Documents uploaded successfully!")
    st.rerun()  # Reload to update documents

# Load documents and initialize search
data_folder = 'data'
documents = []
search_engine = None
if os.path.exists(data_folder):
    documents = load_documents(data_folder)
    if documents:
        search_engine = SearchEngine(documents)
        st.caption(f"Indexed {len(documents)} document(s). Start asking questions below.")
    else:
        st.info("No readable text found in uploaded files. Try a DOCX or TXT file, or a text-based PDF.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input (always render chat box)
prompt = st.chat_input("Enter your agent query")

# Also render a fallback input in case chat_input doesn't trigger on some browsers
with st.form("fallback_query_form", clear_on_submit=True):
    fb_query = st.text_input("Or type your question here and press Submit")
    submitted = st.form_submit_button("Submit")

active_query = None
if prompt:
    active_query = prompt
elif submitted and fb_query:
    active_query = fb_query

if active_query:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": active_query})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(active_query)

    # Get response
    did_search = False
    results = []
    if not search_engine:
        response = "No knowledge base indexed yet. Upload DOCX/TXT or text-based PDF via the sidebar, then ask again."
    else:
        try:
            with st.spinner("Searching knowledge base..."):
                results = search_engine.search(active_query)
                did_search = True
        except Exception as e:
            response = f"Search error: {e}"

    if did_search:
        if results:
            response = ""
            for i, result in enumerate(results, 1):
                response += f"**Source: {result['filename']}**\n"
                content = result['content']
                # Attempt to split into steps if numbered
                lines = content.split('\n')
                steps = [line for line in lines if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('Step'))]
                if steps:
                    response += "Steps:\n"
                    for step in steps:
                        response += f"- {step}\n"
                else:
                    response += content[:1000] + "\n"
                response += "---\n"
        else:
            response = "No relevant information found from the indexed documents. Try rephrasing or uploading more specific SOP/KB files."

    print(f"Response: {response}")  # Debug print
    st.session_state["last_response"] = response
    st.session_state["last_results"] = results

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
    # Also show a compact result panel for visibility
    with st.expander("View latest match summary", expanded=False):
        if results:
            for r in results:
                st.write({"source": r.get("filename"), "similarity": round(r.get("similarity", 0.0), 3)})
        else:
            st.write("No matches.")

    # Log the interaction (do not block UI on logging errors)
    try:
        log_interaction(active_query, response)
    except Exception:
        st.caption("Note: Logging failed, but the response was generated.")

if not search_engine:
    st.write("No documents available. Please upload documents in the sidebar.")

# Always show the latest response panel for visibility
st.divider()
st.subheader("Latest Response")
if "last_response" in st.session_state:
    st.markdown(st.session_state["last_response"] or "(empty)")
    with st.expander("Match summary", expanded=False):
        for r in (st.session_state.get("last_results") or []):
            st.write({"source": r.get("filename"), "similarity": round(r.get("similarity", 0.0), 3)})
else:
    st.caption("Ask a question to see results here.")

# Optional debug info
if st.session_state.get("__debug__"):
    st.divider()
    st.subheader("Debug Info")
    st.write({
        "docs_indexed": len(documents) if documents else 0,
        "search_engine_ready": bool(search_engine),
        "messages_count": len(st.session_state.get("messages", [])),
    })