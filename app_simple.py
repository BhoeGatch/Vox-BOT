import streamlit as st
import os
from pathlib import Path

# Configure Streamlit page
st.set_page_config(
    page_title="WNS Vox BOT - Simple Version", 
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 WNS Vox BOT - Simple Version")
st.markdown("**Error-free version for developers and testing**")

# Sidebar for file upload
st.sidebar.header("📁 Document Upload")
st.sidebar.markdown("Upload your documents to get started")

uploaded_files = st.sidebar.file_uploader(
    "Choose files", 
    accept_multiple_files=True, 
    type=['pdf', 'docx', 'txt'],
    help="Supported formats: PDF, DOCX, TXT files"
)

# Handle file uploads
if uploaded_files:
    # Create data folder if it doesn't exist
    data_folder = Path("data")
    data_folder.mkdir(exist_ok=True)
    
    st.sidebar.markdown("### Upload Status")
    
    # Process each uploaded file
    for file in uploaded_files:
        file_path = data_folder / file.name
        try:
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
            st.sidebar.success(f"✅ {file.name} ({file.size} bytes)")
        except Exception as e:
            st.sidebar.error(f"❌ Failed: {file.name} - {str(e)}")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Ask Questions")
    
    # Query input
    query = st.text_input(
        "Enter your question:", 
        placeholder="e.g., How do I handle customer complaints?",
        help="Type your question about the uploaded documents"
    )
    
    # Process query
    if query:
        st.markdown("---")
        st.markdown("### 🔍 Your Query")
        st.info(f"**Question:** {query}")
        
        # Placeholder for search results
        st.markdown("### 📋 Search Results")
        with st.container():
            st.markdown("""
            **Note:** This is the simple version for testing file uploads and UI functionality.
            
            In the full version, this would show:
            - 🔍 Relevant document excerpts
            - 📄 Source document names
            - 📊 Similarity scores
            - 📝 Step-by-step instructions (if available)
            """)
            
        # Simulated response for testing
        with st.expander("🤖 Simulated Response", expanded=True):
            st.markdown(f"""
            **Based on your query: "{query}"**
            
            This is where the AI response would appear in the full version.
            The system would search through your uploaded documents and provide relevant answers.
            
            **Features that would be active:**
            - Document content analysis
            - TF-IDF based search
            - Step extraction from procedures
            - Source attribution
            """)

with col2:
    st.subheader("📂 Uploaded Files")
    
    # Show uploaded files
    data_folder = Path("data")
    if data_folder.exists():
        files = list(data_folder.glob("*"))
        if files:
            st.markdown("### 📄 Available Documents")
            for file in files:
                file_size = file.stat().st_size
                file_size_mb = file_size / (1024 * 1024)
                
                with st.container():
                    st.markdown(f"""
                    **{file.name}**  
                    📏 Size: {file_size_mb:.2f} MB  
                    📅 Type: {file.suffix.upper()}
                    """)
        else:
            st.info("No files uploaded yet")
    else:
        st.info("Upload files using the sidebar")

# Footer information
st.markdown("---")
st.markdown("### ℹ️ About This Version")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
    **🚀 Simple Version Features:**
    - ✅ File upload without logging conflicts
    - ✅ Clean UI for testing
    - ✅ Error-free operation
    - ✅ Perfect for development
    """)

with col_b:
    st.markdown("""
    **🔄 To Use Full Version:**
    1. Fix logging conflicts in production version
    2. Use `app_vox.py` for basic functionality  
    3. Use `app_production.py` for enterprise features
    4. Check logs folder for any error details
    """)

# Debug information (expandable)
with st.expander("🛠️ Developer Debug Info", expanded=False):
    st.json({
        "files_uploaded": len(uploaded_files) if uploaded_files else 0,
        "data_folder_exists": Path("data").exists(),
        "total_files_stored": len(list(Path("data").glob("*"))) if Path("data").exists() else 0,
        "current_query": query if query else "None",
        "streamlit_version": st.__version__
    })

# Instructions for developers
st.markdown("---")
st.markdown("### 👩‍💻 For Developers")
st.info("""
**To run this app:**
```bash
streamlit run app_simple.py --server.port 8503
```

**This version avoids:**
- Complex logging systems that cause conflicts
- Advanced validation that might have dependency issues  
- Production-level error handling that can be problematic in development

**Use this for:**
- Testing file uploads
- UI development
- Basic functionality verification
- Avoiding logging conflicts in VS Code
""")