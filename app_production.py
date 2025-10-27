# -*- coding: utf-8 -*-
"""
WNS Vox BOT - Production Ready Application
Version: 2.0.0
"""

import streamlit as st
import os
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List

# Production imports
from config import config
from production_logger import log_interaction, log_file_upload, log_search_query, get_logger
from validation import validate_query, validate_filename, validate_file_content, check_rate_limit
from exception_handler import handle_exceptions, safe_execute, FileProcessingError, SearchError

# Core functionality imports
from ingestion_prod import load_documents
from search_prod import FastSearchEngine

# Initialize logger
logger = get_logger('main_app')

# Page config with enhanced security headers
st.set_page_config(
    page_title=config.APP_NAME,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Security headers (would be better handled at server level)
st.markdown("""
<script>
// Basic client-side security measures
if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
    console.warn('Application should be served over HTTPS in production');
}
</script>
""", unsafe_allow_html=True)

# Enhanced CSS with better security considerations
def load_custom_css():
    """Load custom CSS with security considerations"""
    css_file = Path(__file__).parent / "static" / "custom.css"
    
    if css_file.exists():
        with open(css_file, 'r', encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Inline CSS as fallback
        st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
            
            .main {
                background: linear-gradient(135deg, #0a0e27 0%, #1a1a2e 50%, #16213e 100%);
                font-family: 'Inter', sans-serif;
                color: #e6e6e6;
            }
            
            .block-container {
                background: linear-gradient(135deg, rgba(10, 14, 39, 0.98) 0%, rgba(22, 33, 62, 0.98) 100%);
                border-radius: 24px;
                padding: 2.5rem 3.5rem !important;
                box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(102, 126, 234, 0.25);
                max-width: 1400px;
                margin: 0 auto;
            }
            
            .status-badge {
                background: linear-gradient(135deg, #667eea 0%, #00d4ff 100%);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 20px;
                font-weight: 600;
                font-size: 0.9rem;
                box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
            }
            
            .error-message {
                background: linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%);
                color: white;
                padding: 1rem;
                border-radius: 12px;
                margin: 1rem 0;
                font-weight: 500;
                box-shadow: 0 4px 16px rgba(255, 107, 107, 0.3);
            }
            
            .success-message {
                background: linear-gradient(135deg, #51cf66 0%, #69db7c 100%);
                color: white;
                padding: 1rem;
                border-radius: 12px;
                margin: 1rem 0;
                font-weight: 500;
                box-shadow: 0 4px 16px rgba(81, 207, 102, 0.3);
            }
            
            .warning-message {
                background: linear-gradient(135deg, #ffd43b 0%, #ffe066 100%);
                color: #333;
                padding: 1rem;
                border-radius: 12px;
                margin: 1rem 0;
                font-weight: 500;
                box-shadow: 0 4px 16px rgba(255, 212, 59, 0.3);
            }
            
            .security-notice {
                background: rgba(255, 193, 7, 0.1);
                border: 1px solid rgba(255, 193, 7, 0.3);
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
                font-size: 0.9rem;
            }
        </style>
        """, unsafe_allow_html=True)

@handle_exceptions("initialize_session_state", default_return=None)
def initialize_session_state():
    """Initialize session state with production defaults"""
    defaults = {
        'chat_history': [],
        'show_details': False,
        'session_id': None,
        'user_id': None,
        'last_activity': time.time(),
        'request_count': 0,
        'uploaded_files': [],
        'error_count': 0
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # Generate session ID if not exists
    if not st.session_state.session_id:
        st.session_state.session_id = hashlib.sha256(
            f"{time.time()}_{st.session_state.user_id or 'anonymous'}".encode()
        ).hexdigest()[:16]
    
    # Update last activity
    st.session_state.last_activity = time.time()

@handle_exceptions("get_session_identifier", default_return="unknown")
def get_session_identifier() -> str:
    """Get session identifier for rate limiting"""
    return st.session_state.get('session_id', 'unknown')

@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
@handle_exceptions("load_and_index_documents", default_return=([], None))
def load_and_index_documents(data_folder: str) -> tuple[List[Dict], Optional[FastSearchEngine]]:
    """Load and index documents with production caching"""
    logger.info("Loading documents", extra={'data_folder': data_folder})
    
    if not os.path.exists(data_folder):
        config.DATA_DIR.mkdir(exist_ok=True)
        return [], None
    
    try:
        documents = load_documents(data_folder)
        
        if not documents:
            logger.info("No documents found")
            return [], None
        
        search_engine = FastSearchEngine(documents, method='tfidf')
        
        logger.info("Documents loaded successfully", extra={
            'document_count': len(documents),
            'has_search_engine': bool(search_engine)
        })
        
        return documents, search_engine
        
    except Exception as e:
        logger.error(f"Failed to load documents: {e}")
        raise FileProcessingError(f"Failed to load documents: {e}")

@handle_exceptions("generate_comprehensive_answer", default_return="I apologize, but I encountered an error processing your request.")
def generate_comprehensive_answer(user_query: str, results: List[Dict], documents: List[Dict]) -> str:
    """Generate comprehensive answer with enhanced error handling"""
    if not results:
        return "I couldn't find relevant information for your query. Please try rephrasing or check if relevant documents are uploaded."
    
    try:
        query_words = set(user_query.lower().split())
        relevant_blocks = []
        
        for result in results[:config.SEARCH_MAX_RESULTS]:
            content = result.get('content', '')
            filename = result.get('filename', 'Unknown')
            sim = result.get('similarity', 0)
            
            # Enhanced content processing with security considerations
            sentences = [s.strip() for s in content.split('.') if s.strip()]
            current_chunk = []
            
            for sentence in sentences[:50]:  # Limit processing for performance
                if len(sentence) > 20 and len(sentence) < 1000:  # Security: reasonable length
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
        
        if not relevant_blocks:
            return f"I found documents that may be related to '{user_query}', but couldn't locate specific information that directly addresses your question."
        
        # Sort by relevance and similarity
        relevant_blocks.sort(key=lambda x: (x['relevance'], x['similarity']), reverse=True)
        
        # Create response with length limits for security
        response = f"**{user_query[:200]}**\n\n"  # Limit query display length
        
        top_blocks = relevant_blocks[:min(3, len(relevant_blocks))]
        sources = set()
        
        for block in top_blocks:
            text = block['text'][:2000]  # Limit response length
            sources.add(block['source'])
            
            text = text.strip()
            if not text.endswith(('.', '!', '?')):
                text += '.'
            
            response += f"{text}\n\n"
        
        # Add sources with limit
        if sources:
            source_list = list(sources)[:5]  # Limit source count
            response += f"---\n**📚 Source{'s' if len(source_list) > 1 else ''}:** {', '.join(source_list)}"
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return "I encountered an error while processing the search results. Please try again."

def display_error_message(message: str, error_type: str = "error"):
    """Display formatted error message"""
    css_class = f"{error_type}-message"
    st.markdown(f'<div class="{css_class}">⚠️ {message}</div>', unsafe_allow_html=True)

def display_success_message(message: str):
    """Display formatted success message"""
    st.markdown(f'<div class="success-message">✅ {message}</div>', unsafe_allow_html=True)

def main():
    """Main application function"""
    try:
        # Load CSS and initialize
        load_custom_css()
        initialize_session_state()
        
        # Configuration display in debug mode
        if config.DEBUG_MODE:
            st.markdown('<div class="security-notice">🔧 Debug Mode Active - Not for production use</div>', 
                       unsafe_allow_html=True)
        
        # Header with version info
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title(f"🤖 {config.APP_NAME}")
            st.markdown(f"*Version {config.APP_VERSION} - Enterprise Ready*")
        
        with col2:
            if config.DEBUG_MODE:
                st.markdown(f"**Session:** `{st.session_state.session_id}`")
        
        # Sidebar for file management
        with st.sidebar:
            st.markdown("### 📁 Document Management")
            
            # File upload with validation
            uploaded_files = st.file_uploader(
                "Upload documents",
                type=['pdf', 'docx', 'txt'],
                accept_multiple_files=True,
                help=f"Max file size: {config.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
            
            if uploaded_files:
                session_id = get_session_identifier()
                
                # Rate limiting check
                if not check_rate_limit(session_id):
                    display_error_message("Rate limit exceeded. Please wait before uploading more files.")
                    st.stop()
                
                for uploaded_file in uploaded_files:
                    try:
                        # Validate filename
                        filename = validate_filename(uploaded_file.name)
                        
                        # Check file count limit
                        if len(st.session_state.uploaded_files) >= config.MAX_FILES_PER_SESSION:
                            display_error_message(f"Maximum {config.MAX_FILES_PER_SESSION} files per session allowed.")
                            break
                        
                        # Save file with validation
                        config.ensure_directories()
                        file_path = config.DATA_DIR / filename
                        
                        with open(file_path, 'wb') as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Validate file content
                        file_info = validate_file_content(file_path)
                        
                        # Log successful upload
                        log_file_upload(
                            filename=filename,
                            file_size=file_info['size'],
                            session_id=session_id
                        )
                        
                        st.session_state.uploaded_files.append(filename)
                        display_success_message(f"✅ {filename} uploaded successfully!")
                        
                        # Clear cache to reload documents
                        load_and_index_documents.clear()
                        
                    except Exception as e:
                        logger.error(f"File upload failed: {e}")
                        display_error_message(f"Failed to upload {uploaded_file.name}: {str(e)}")
                        
                        # Clean up failed file
                        file_path = config.DATA_DIR / uploaded_file.name
                        if file_path.exists():
                            file_path.unlink()
            
            # Display existing files
            if config.DATA_DIR.exists():
                existing_files = [f.name for f in config.DATA_DIR.iterdir() 
                                if f.suffix.lower() in config.ALLOWED_EXTENSIONS]
                
                if existing_files:
                    st.markdown("### 📚 Knowledge Base")
                    for filename in existing_files:
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"📄 {filename}")
                        with col2:
                            if st.button("🗑️", key=f"del_{filename}"):
                                try:
                                    (config.DATA_DIR / filename).unlink()
                                    display_success_message("File deleted!")
                                    load_and_index_documents.clear()
                                    st.rerun()
                                except Exception as e:
                                    display_error_message(f"Failed to delete file: {e}")
                    
                    st.markdown("---")
                    if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
                        try:
                            for filename in existing_files:
                                (config.DATA_DIR / filename).unlink()
                            display_success_message("All files cleared!")
                            st.session_state.uploaded_files.clear()
                            load_and_index_documents.clear()
                            st.rerun()
                        except Exception as e:
                            display_error_message(f"Failed to clear files: {e}")
                else:
                    st.info("📭 No documents uploaded yet.")
            
            # Settings
            st.markdown("---")
            st.markdown("### ⚙️ Settings")
            show_debug = st.checkbox("🐛 Debug Mode", value=config.DEBUG_MODE)
        
        # Main chat interface
        st.markdown("### 💬 Chat Interface")
        
        # Load documents
        documents, search_engine = load_and_index_documents(str(config.DATA_DIR))
        
        # Status display
        if documents:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f'<span class="status-badge">✅ {len(documents)} document(s) ready</span>', 
                           unsafe_allow_html=True)
            with col2:
                if st.button("ℹ️ Details"):
                    st.session_state.show_details = not st.session_state.show_details
            
            if st.session_state.show_details:
                with st.expander("📊 Knowledge Base Summary", expanded=True):
                    total_chars = sum(len(doc["content"]) for doc in documents)
                    st.write(f"**Total Content:** {total_chars:,} characters")
                    st.write(f"**Search Engine:** {'Ready' if search_engine else 'Not initialized'}")
        else:
            st.info("📝 Please upload documents to start chatting!")
        
        # Chat history display
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # User input with validation
        if user_query := st.chat_input("Ask about your documents..."):
            session_id = get_session_identifier()
            
            # Rate limiting
            if not check_rate_limit(session_id):
                display_error_message("Too many requests. Please wait a moment.")
                st.stop()
            
            try:
                # Validate query
                validated_query = validate_query(user_query)
                
                # Display user message
                with st.chat_message("user"):
                    st.markdown(validated_query)
                st.session_state.chat_history.append({"role": "user", "content": validated_query})
                
                # Process query
                if documents and search_engine:
                    start_time = time.time()
                    
                    try:
                        results = search_engine.search(validated_query, top_k=config.SEARCH_MAX_RESULTS)
                        search_time = time.time() - start_time
                        
                        # Log search
                        log_search_query(
                            query=validated_query,
                            results_count=len(results),
                            search_time=search_time,
                            session_id=session_id
                        )
                        
                        if results:
                            assistant_msg = generate_comprehensive_answer(validated_query, results, documents)
                        else:
                            assistant_msg = "I couldn't find relevant information for your query. Please try rephrasing or uploading relevant documents."
                        
                    except Exception as e:
                        logger.error(f"Search failed: {e}")
                        assistant_msg = "I encountered an error while searching. Please try again."
                        results = []
                else:
                    assistant_msg = "Please upload documents first to enable search functionality."
                    results = []
                
                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(assistant_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": assistant_msg})
                
                # Log interaction
                try:
                    log_interaction(
                        query=validated_query,
                        response=assistant_msg,
                        session_id=session_id,
                        processing_time=time.time() - start_time if 'start_time' in locals() else None
                    )
                except Exception as e:
                    if show_debug:
                        st.caption(f"Logging failed: {e}")
                
                # Debug information
                if show_debug and 'results' in locals():
                    with st.expander("🔍 Debug Information"):
                        st.json({
                            "query_length": len(validated_query),
                            "results_count": len(results),
                            "search_time": f"{search_time:.3f}s" if 'search_time' in locals() else "N/A",
                            "session_id": session_id,
                            "documents_loaded": len(documents),
                            "search_engine_ready": bool(search_engine)
                        })
                        
                        if results:
                            st.subheader("Search Results")
                            for i, result in enumerate(results[:3]):
                                st.json({
                                    "rank": i + 1,
                                    "source": result.get("filename", "Unknown"),
                                    "similarity": round(result.get("similarity", 0), 4),
                                    "content_preview": result.get("content", "")[:200] + "..."
                                })
                
            except Exception as e:
                logger.error(f"Query processing failed: {e}")
                display_error_message(f"Failed to process query: {str(e)}")
                st.session_state.error_count += 1
        
        # Footer with system info
        st.markdown("---")
        footer_cols = st.columns([2, 1, 1])
        
        with footer_cols[0]:
            st.markdown(f"✨ **{config.APP_NAME}** v{config.APP_VERSION}")
        
        with footer_cols[1]:
            if show_debug:
                st.markdown(f"**Session:** {st.session_state.session_id}")
        
        with footer_cols[2]:
            if show_debug:
                st.markdown(f"**Requests:** {st.session_state.request_count}")
        
        # Update request count
        st.session_state.request_count += 1
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error("⚠️ Application encountered an unexpected error. Please refresh the page.")
        
        if config.DEBUG_MODE:
            st.exception(e)

if __name__ == "__main__":
    main()