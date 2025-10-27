# -*- coding: utf-8 -*-
import streamlit as st
from ingestion import load_documents
from search_fast import FastSearchEngine
from logger import log_interaction
import os
import re

# Page config with custom theme
st.set_page_config(
    page_title="WNS Vox BOT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme with blue/white bot icon - Enhanced UX
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    
    * {
        transition: all 0.2s ease-in-out;
    }
    
    .main {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1a2e 50%, #16213e 100%);
        font-family: 'Inter', sans-serif;
        color: #e6e6e6;
    }
    
    .block-container {
        background: linear-gradient(135deg, rgba(10, 14, 39, 0.98) 0%, rgba(22, 33, 62, 0.98) 100%);
        border-radius: 24px;
        padding: 2.5rem 3.5rem !important;
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6), 0 0 1px rgba(102, 126, 234, 0.3);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(102, 126, 234, 0.25);
        max-width: 1400px;
        margin: 0 auto;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px) scale(1); }
        50% { transform: translateY(-18px) scale(1.02); }
    }
    
    @keyframes glow {
        0%, 100% { 
            filter: drop-shadow(0 0 25px rgba(0, 212, 255, 0.7)) 
                    drop-shadow(0 0 50px rgba(102, 126, 234, 0.4)); 
        }
        50% { 
            filter: drop-shadow(0 0 40px rgba(0, 212, 255, 1)) 
                    drop-shadow(0 0 70px rgba(102, 126, 234, 0.6)); 
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInFromLeft {
        from {
            opacity: 0;
            transform: translateX(-40px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .logo-container {
        text-align: center;
        padding: 1.5rem 0 2.5rem 0;
        animation: fadeInUp 0.8s ease-out;
    }
    
    .vox-bot {
        display: inline-block;
        position: relative;
        width: 150px;
        height: 150px;
        animation: float 3.5s ease-in-out infinite, glow 2.5s ease-in-out infinite;
        cursor: default;
    }
    
    .bot-head {
        width: 95px;
        height: 95px;
        background: linear-gradient(135deg, #00d4ff 0%, #667eea 50%, #5a67d8 100%);
        border-radius: 24px;
        position: absolute;
        top: 32px;
        left: 27px;
        box-shadow: 
            0 12px 35px rgba(0, 212, 255, 0.6),
            inset 0 -2px 8px rgba(0, 0, 0, 0.3),
            inset 0 2px 8px rgba(255, 255, 255, 0.2);
    }
    
    .bot-eyes {
        position: absolute;
        top: 30px;
        left: 20px;
        display: flex;
        gap: 28px;
    }
    
    .bot-eye {
        width: 20px;
        height: 20px;
        background: white;
        border-radius: 50%;
        box-shadow: 
            0 0 15px rgba(255, 255, 255, 1),
            inset 0 2px 4px rgba(0, 0, 0, 0.1);
        animation: blink 5s infinite;
        position: relative;
    }
    
    .bot-eye::after {
        content: '';
        position: absolute;
        width: 8px;
        height: 8px;
        background: #00d4ff;
        border-radius: 50%;
        top: 6px;
        left: 6px;
        box-shadow: 0 0 8px rgba(0, 212, 255, 0.8);
    }
    
    @keyframes blink {
        0%, 48%, 52%, 100% { transform: scaleY(1); opacity: 1; }
        50% { transform: scaleY(0.1); opacity: 0.8; }
    }
    
    .bot-mouth {
        position: absolute;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        width: 48px;
        height: 24px;
        border: 3px solid white;
        border-top: none;
        border-radius: 0 0 24px 24px;
        box-shadow: 
            0 0 12px rgba(255, 255, 255, 0.8),
            inset 0 -2px 6px rgba(0, 0, 0, 0.2);
    }
    
    .einstein-cloud {
        position: absolute;
        top: -5px;
        left: -12px;
        font-size: 3.8rem;
        animation: wiggle 2.5s ease-in-out infinite;
        filter: brightness(1.3) drop-shadow(0 0 12px rgba(255, 255, 255, 0.6));
    }
    
    @keyframes wiggle {
        0%, 100% { transform: rotate(-4deg) scale(1); }
        50% { transform: rotate(4deg) scale(1.05); }
    }
    
    .bot-antenna {
        position: absolute;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        width: 3px;
        height: 25px;
        background: linear-gradient(180deg, #00d4ff 0%, transparent 100%);
    }
    
    .bot-antenna::before {
        content: '';
        position: absolute;
        top: -6px;
        left: 50%;
        transform: translateX(-50%);
        width: 10px;
        height: 10px;
        background: #00d4ff;
        border-radius: 50%;
        animation: antennaBlink 1.5s infinite;
        box-shadow: 0 0 15px #00d4ff;
    }
    
    @keyframes antennaBlink {
        0%, 49%, 100% { opacity: 1; }
        50%, 99% { opacity: 0.3; }
    }
    
    .main-title {
        font-family: 'Poppins', sans-serif;
        font-size: 3.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #00d4ff 40%, #a78bfa 70%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
        animation: fadeInUp 0.8s ease-out 0.2s backwards;
    }
    
    .subtitle {
        text-align: center;
        color: #00d4ff;
        font-size: 1.25rem;
        font-weight: 400;
        margin-bottom: 2.5rem;
        text-shadow: 0 0 15px rgba(0, 212, 255, 0.4);
        animation: fadeInUp 0.8s ease-out 0.4s backwards;
        opacity: 0.95;
    }
    
    .stChatMessage {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.12) 0%, rgba(118, 75, 162, 0.12) 100%) !important;
        border-radius: 16px !important;
        padding: 1.25rem 1.5rem !important;
        margin: 0.75rem 0 !important;
        box-shadow: 
            0 2px 8px rgba(0, 0, 0, 0.2),
            0 8px 24px rgba(0, 0, 0, 0.15) !important;
        border: 1px solid rgba(102, 126, 234, 0.25);
        color: #e6e6e6 !important;
        animation: slideInFromLeft 0.4s ease-out;
        backdrop-filter: blur(8px);
    }
    
    .stChatMessage:hover {
        transform: translateY(-2px);
        box-shadow: 
            0 4px 12px rgba(0, 0, 0, 0.25),
            0 12px 32px rgba(0, 212, 255, 0.15) !important;
        border-color: rgba(0, 212, 255, 0.4);
    }
    
    .stChatMessage p, .stChatMessage div {
        color: #e6e6e6 !important;
        line-height: 1.7;
        font-size: 1.02rem;
    }
    
    /* User messages with distinct styling */
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(102, 126, 234, 0.15) 100%) !important;
        border-color: rgba(0, 212, 255, 0.35);
    }
    
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e27 0%, #16213e 100%);
        padding: 2rem 1.25rem;
        border-right: 1px solid rgba(0, 212, 255, 0.2);
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
    }
    
    section[data-testid="stSidebar"] * {
        color: #e6e6e6 !important;
    }
    
    section[data-testid="stSidebar"] h3 {
        color: #00d4ff !important;
        text-shadow: 0 0 15px rgba(0, 212, 255, 0.6);
        font-weight: 600;
        font-size: 1.15rem;
        letter-spacing: 0.3px;
    }
    
    section[data-testid="stSidebar"] .markdown-text-container {
        font-size: 0.95rem;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #00d4ff 100%);
        color: white !important;
        border: none;
        border-radius: 28px;
        padding: 0.65rem 2.2rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 
            0 4px 16px rgba(102, 126, 234, 0.45),
            0 2px 8px rgba(0, 212, 255, 0.3);
        cursor: pointer;
        letter-spacing: 0.3px;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 
            0 8px 24px rgba(0, 212, 255, 0.6),
            0 4px 12px rgba(102, 126, 234, 0.5);
        background: linear-gradient(135deg, #00d4ff 0%, #667eea 100%);
    }
    
    .stButton > button:active {
        transform: translateY(-1px) scale(0.98);
    }
    
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        box-shadow: 
            0 4px 16px rgba(255, 107, 107, 0.4),
            0 2px 8px rgba(238, 90, 111, 0.3);
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #ee5a6f 0%, #c44569 100%);
        box-shadow: 
            0 8px 24px rgba(255, 107, 107, 0.5),
            0 4px 12px rgba(238, 90, 111, 0.4);
    }
    
    .stChatInput > div > div > input {
        border-radius: 28px;
        border: 2px solid rgba(102, 126, 234, 0.4);
        padding: 1rem 1.75rem;
        font-size: 1.02rem;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        background: rgba(10, 14, 39, 0.9);
        color: #e6e6e6;
        box-shadow: 
            0 2px 8px rgba(0, 0, 0, 0.2),
            inset 0 1px 2px rgba(255, 255, 255, 0.05);
    }
    
    .stChatInput > div > div > input::placeholder {
        color: rgba(230, 230, 230, 0.5);
        font-weight: 400;
    }
    
    .stChatInput > div > div > input:focus {
        border-color: #00d4ff;
        box-shadow: 
            0 0 0 3px rgba(0, 212, 255, 0.15),
            0 0 28px rgba(0, 212, 255, 0.4),
            0 4px 16px rgba(0, 0, 0, 0.3);
        background: rgba(10, 14, 39, 1);
        outline: none;
    }
    
    .stChatInput > div > div > input:hover {
        border-color: rgba(0, 212, 255, 0.5);
    }
    
    .stSuccess, .stInfo {
        background: linear-gradient(135deg, rgba(132, 250, 176, 0.15) 0%, rgba(143, 211, 244, 0.15) 100%);
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        border: 1px solid rgba(132, 250, 176, 0.35);
        color: #84fab0;
        font-weight: 500;
        box-shadow: 0 2px 12px rgba(132, 250, 176, 0.15);
        animation: fadeInUp 0.4s ease-out;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(250, 112, 154, 0.15) 0%, rgba(254, 225, 64, 0.15) 100%);
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        border: 1px solid rgba(254, 225, 64, 0.35);
        color: #fee140;
        font-weight: 500;
        box-shadow: 0 2px 12px rgba(254, 225, 64, 0.15);
        animation: fadeInUp 0.4s ease-out;
    }
    
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.18) 0%, rgba(118, 75, 162, 0.18) 100%);
        border-radius: 12px;
        font-weight: 600;
        color: #00d4ff !important;
        border: 1px solid rgba(102, 126, 234, 0.3);
        padding: 0.9rem 1.2rem;
        transition: all 0.25s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.25) 0%, rgba(118, 75, 162, 0.25) 100%);
        border-color: rgba(0, 212, 255, 0.4);
        transform: translateX(4px);
    }
    
    .streamlit-expanderContent {
        background: rgba(10, 14, 39, 0.6);
        border-radius: 0 0 12px 12px;
        border: 1px solid rgba(102, 126, 234, 0.25);
        border-top: none;
        padding: 1rem;
        backdrop-filter: blur(8px);
    }
    
    hr {
        margin: 2.5rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.4), rgba(0, 212, 255, 0.6), rgba(102, 126, 234, 0.4), transparent);
        opacity: 0.6;
    }
    
    .doc-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.12) 0%, rgba(118, 75, 162, 0.12) 100%);
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin: 0.6rem 0;
        box-shadow: 
            0 2px 8px rgba(0, 0, 0, 0.2),
            0 4px 16px rgba(0, 0, 0, 0.15);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        border-left: 3px solid #00d4ff;
        color: #e6e6e6;
        cursor: default;
    }
    
    .doc-card:hover {
        transform: translateX(6px) translateY(-2px);
        box-shadow: 
            0 4px 12px rgba(0, 0, 0, 0.25),
            0 8px 24px rgba(0, 212, 255, 0.25);
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.18) 0%, rgba(118, 75, 162, 0.18) 100%);
        border-left-width: 4px;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.4rem 1.2rem;
        border-radius: 22px;
        background: linear-gradient(135deg, rgba(132, 250, 176, 0.25) 0%, rgba(0, 212, 255, 0.25) 100%);
        color: #00d4ff;
        font-weight: 600;
        font-size: 0.92rem;
        animation: fadeInUp 0.6s ease-out;
        border: 1px solid rgba(0, 212, 255, 0.4);
        box-shadow: 0 2px 12px rgba(0, 212, 255, 0.2);
        letter-spacing: 0.3px;
    }
    
    section[data-testid="stFileUploadDropzone"] {
        background: rgba(102, 126, 234, 0.08);
        border: 2px dashed rgba(0, 212, 255, 0.4);
        border-radius: 16px;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        padding: 2rem;
    }
    
    section[data-testid="stFileUploadDropzone"]:hover {
        border-color: #00d4ff;
        background: rgba(102, 126, 234, 0.15);
        box-shadow: 
            0 0 24px rgba(0, 212, 255, 0.25),
            0 4px 16px rgba(0, 0, 0, 0.2);
        transform: scale(1.01);
    }
    
    ::-webkit-scrollbar {
        width: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(10, 14, 39, 0.9);
        border-radius: 12px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #00d4ff 100%);
        border-radius: 12px;
        border: 2px solid rgba(10, 14, 39, 0.9);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #00d4ff 0%, #667eea 100%);
        box-shadow: 0 0 12px rgba(0, 212, 255, 0.5);
    }
    
    .footer {
        text-align: center;
        padding: 2.5rem 0 1.5rem 0;
        color: rgba(102, 126, 234, 0.8);
        font-size: 0.92rem;
        border-top: 1px solid rgba(102, 126, 234, 0.2);
        margin-top: 3.5rem;
        font-weight: 500;
        letter-spacing: 0.3px;
    }
    
    .footer p {
        margin: 0;
        opacity: 0.9;
    }
    
    /* Loading spinner */
    .stSpinner > div {
        border-top-color: #00d4ff !important;
        border-right-color: rgba(0, 212, 255, 0.3) !important;
    }
    
    /* Tooltips */
    [data-baseweb="tooltip"] {
        background: linear-gradient(135deg, #667eea 0%, #00d4ff 100%);
        border-radius: 8px;
        padding: 0.5rem 0.75rem;
        font-size: 0.9rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    }
    
    /* Focus visible for accessibility */
    *:focus-visible {
        outline: 2px solid #00d4ff;
        outline-offset: 2px;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# Animated Einstein-style Bot Logo
bot_logo_html = """
<div class="logo-container">
    <div class="vox-bot">
        <div class="einstein-cloud">☁️</div>
        <div class="bot-antenna"></div>
        <div class="bot-head">
            <div class="bot-eyes">
                <div class="bot-eye"></div>
                <div class="bot-eye"></div>
            </div>
            <div class="bot-mouth"></div>
        </div>
    </div>
</div>
<h1 class="main-title">WNS Vox BOT</h1>
<p class="subtitle">🎓 Your Intelligent Knowledge Base Assistant</p>
"""

st.markdown(bot_logo_html, unsafe_allow_html=True)

def generate_comprehensive_answer(user_query, results):
    """Generate coherent, contextual answers from search results"""
    
    if not results:
        return "No relevant information found in the documents."
    
    # Find the most relevant content blocks
    relevant_blocks = []
    query_words = set(word.lower() for word in user_query.split() if len(word) > 2)
    
    for result in results:
        sim = result.get('similarity', 0)
        if sim > 0.005:  # Lower threshold for better coverage
            content = result['content']
            filename = result.get('original_filename', result['filename'])
            
            # Split into paragraphs and find relevant ones
            paragraphs = content.split('\n\n')
            
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if len(paragraph) > 50:  # Substantial content
                    paragraph_lower = paragraph.lower()
                    
                    # Check relevance - at least one query word should appear
                    relevance_score = sum(1 for word in query_words if word in paragraph_lower)
                    
                    if relevance_score > 0:
                        # Clean the text
                        clean_text = re.sub(r'[•*▪▫◦‣⁃]', '', paragraph)
                        clean_text = re.sub(r'\s+', ' ', clean_text)
                        clean_text = clean_text.strip()
                        
                        if len(clean_text) > 30:
                            relevant_blocks.append({
                                'text': clean_text,
                                'source': filename,
                                'relevance': relevance_score,
                                'similarity': sim
                            })
            
            # If no paragraphs found, try sentence-level extraction
            if not relevant_blocks:
                sentences = content.replace('\n', ' ').split('. ')
                current_chunk = []
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 20:
                        sentence_lower = sentence.lower()
                        
                        if any(word in sentence_lower for word in query_words):
                            current_chunk.append(sentence)
                            
                            if len(current_chunk) >= 2:
                                chunk_text = '. '.join(current_chunk)
                                if not chunk_text.endswith('.'):
                                    chunk_text += '.'
                                
                                relevant_blocks.append({
                                    'text': chunk_text,
                                    'source': filename,
                                    'relevance': sum(1 for word in query_words if word in chunk_text.lower()),
                                    'similarity': sim
                                })
                                current_chunk = []
    
    # Sort by relevance and similarity
    relevant_blocks.sort(key=lambda x: (x['relevance'], x['similarity']), reverse=True)
    
    if not relevant_blocks:
        return f"I found documents that may be related to '{user_query}', but couldn't locate specific information that directly addresses your question. Try using more specific keywords or rephrasing your query."
    
    # Create a coherent response
    response = f"**{user_query}**\n\n"
    
    # Use the most relevant blocks (limit to 3-4 for coherence)
    top_blocks = relevant_blocks[:min(3, len(relevant_blocks))]
    sources = set()
    
    for i, block in enumerate(top_blocks):
        text = block['text']
        sources.add(block['source'])
        
        # Clean and format the text
        text = text.strip()
        if not text.endswith(('.', '!', '?')):
            text += '.'
        
        # Add the content naturally
        response += f"{text}\n\n"
    
    # Add sources
    if sources:
        source_list = list(sources)
        response += f"---\n**📚 Source{'s' if len(source_list) > 1 else ''}:** {', '.join(source_list)}"
    
    return response

# Optimized document loading with better memory management
@st.cache_resource
def load_and_index_documents(data_folder, _force_reload=False):
    """Load documents once and cache the search engine with optimization"""
    if not os.path.exists(data_folder):
        os.makedirs(data_folder, exist_ok=True)
        return [], None
    
    documents = load_documents(data_folder)
    if documents:
        # Use TF-IDF method for better accuracy and relevance
        search_engine = FastSearchEngine(documents, method='tfidf')
        return documents, search_engine
    return documents, None

# Initialize session state for efficiency
def initialize_session_state():
    """Initialize session state variables to avoid repeated checks"""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "show_details" not in st.session_state:
        st.session_state.show_details = False

# Sidebar with improved UX
with st.sidebar:
    st.markdown("### 📁 Document Management")
    st.markdown('<p style="font-size: 0.9rem; opacity: 0.8; margin-top: -0.5rem;">Upload and manage your knowledge base</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    uploaded_files = st.file_uploader(
        "📤 Upload Documents", 
        accept_multiple_files=True, 
        type=['pdf', 'docx', 'txt'],
        help="Supported formats: PDF, DOCX, TXT • Drag and drop or click to browse"
    )
    
    if uploaded_files:
        data_folder = 'data'
        os.makedirs(data_folder, exist_ok=True)
        for uploaded_file in uploaded_files:
            file_path = os.path.join(data_folder, uploaded_file.name)
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
        st.success(f"✨ {len(uploaded_files)} file(s) uploaded!")
        load_and_index_documents.clear()
        st.rerun()
    
    st.markdown("---")
    
    if os.path.exists('data'):
        existing_files = [f for f in os.listdir('data') if f.endswith(('.pdf', '.docx', '.txt'))]
        if existing_files:
            st.markdown("### 📚 Knowledge Base")
            for filename in existing_files:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"📄 {filename}")
                with col2:
                    if st.button("🗑️", key=f"del_{filename}"):
                        os.remove(os.path.join('data', filename))
                        st.success("Deleted!")
                        load_and_index_documents.clear()
                        st.rerun()
            
            st.markdown("---")
            if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
                for filename in existing_files:
                    os.remove(os.path.join('data', filename))
                st.success("All cleared!")
                load_and_index_documents.clear()
                st.rerun()
        else:
            st.info("📭 No documents uploaded yet. Add some to get started!")
    
    st.markdown("---")
    st.markdown('<p style="font-size: 0.85rem; opacity: 0.7;">⚙️ Settings</p>', unsafe_allow_html=True)
    show_debug = st.checkbox("🐛 Debug Mode", help="Show detailed search results and system information")

# Initialize session state for better performance
initialize_session_state()

# Load documents with optimized caching
data_folder = 'data'
documents, search_engine = load_and_index_documents(data_folder)

# Status display with better UX
if documents:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f'<span class="status-badge">✅ {len(documents)} document(s) ready</span>', unsafe_allow_html=True)
    with col2:
        show_details_btn = st.button("ℹ️ Details", key="show_details_btn")
    
    # Toggle on button click (session state already initialized)
    if show_details_btn:
        st.session_state.show_details = not st.session_state.show_details
    
    if st.session_state.show_details:
        with st.expander("📊 Knowledge Base Summary", expanded=True):
            total_chars = sum(len(doc["content"]) for doc in documents)
            st.markdown(f"""
            <div style="background: rgba(102, 126, 234, 0.1); padding: 1rem; border-radius: 12px; margin: 0.5rem 0;">
                <p style="margin: 0; opacity: 0.9;">📚 Total Documents: <strong>{len(documents)}</strong></p>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">📝 Total Content: <strong>{total_chars:,} characters</strong></p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            for doc in documents:
                st.markdown(f'<div class="doc-card">📄 <strong>{doc["filename"]}</strong><br/><span style="opacity: 0.7; font-size: 0.9rem;">{len(doc["content"]):,} characters</span></div>', unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align: center; padding: 3rem 2rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%); border-radius: 16px; border: 2px dashed rgba(102, 126, 234, 0.3);">
        <p style="font-size: 3rem; margin: 0;">📚</p>
        <h3 style="color: #00d4ff; margin: 1rem 0 0.5rem 0;">No Knowledge Base Yet</h3>
        <p style="opacity: 0.8; margin: 0;">Upload documents using the sidebar to get started</p>
        <p style="opacity: 0.6; font-size: 0.9rem; margin: 1rem 0 0 0;">Supported formats: PDF, DOCX, TXT</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Display chat history (session state already initialized)
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_query = st.chat_input("💬 Ask me anything about your documents...")

if user_query:
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    if not search_engine:
        assistant_msg = "❌ **No documents indexed yet.** Please upload DOCX, TXT, or text-based PDF files using the sidebar."
        results = []
    else:
        try:
            with st.spinner("🔍 Searching knowledge base..."):
                results = search_engine.search(user_query, top_k=10)  # Get more results for comprehensive answers
            
            if results and results[0].get('similarity', 0) > 0.02:  # Balanced threshold for relevant matches
                # Generate coherent, contextual response
                assistant_msg = generate_comprehensive_answer(user_query, results)
            else:
                # More helpful fallback when no strong matches found
                if results and len(results) > 0:
                    top_sources = [r['filename'] for r in results[:3]]
                    assistant_msg = f"I found some documents that might contain related information ({', '.join(top_sources)}), but couldn't locate content that directly addresses **'{user_query}'**.\n\n💡 **Try:**\n• Using more specific keywords\n• Breaking down complex questions into simpler parts\n• Checking if the information exists in your uploaded documents"
                else:
                    assistant_msg = f"No documents found matching **'{user_query}'**. Please make sure you have uploaded relevant documents and try using different search terms."
        except Exception as e:
            assistant_msg = f"❌ **Search error:** {str(e)}"
            results = []
    
    with st.chat_message("assistant"):
        st.markdown(assistant_msg)
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_msg})
    
    try:
        log_interaction(user_query, assistant_msg)
    except Exception as e:
        if show_debug:
            st.caption(f"Note: Logging failed ({e})")
    
    if results and show_debug:
        with st.expander("🔍 Debug: Match details"):
            for r in results[:5]:
                st.json({
                    "source": r.get("filename"),
                    "similarity": round(r.get("similarity", 0), 4),
                    "content_preview": r.get("content", "")[:200] + "..."
                })

if show_debug:
    st.markdown("---")
    st.subheader("🐛 Debug Information")
    st.json({
        "docs_indexed": len(documents),
        "search_engine_ready": bool(search_engine),
        "chat_history_length": len(st.session_state.chat_history),
        "data_folder_exists": os.path.exists(data_folder)
    })

st.markdown("""
<div class="footer">
    <p>✨ Powered by WNS Vox BOT • Built with ❤️ for Agent Excellence</p>
</div>
""", unsafe_allow_html=True)
