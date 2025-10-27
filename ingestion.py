import os
import re
import PyPDF2
from docx import Document

def extract_text_from_pdf(file_path):
    """Enhanced PDF text extraction with better handling"""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            
            for page_num, page in enumerate(reader.pages):
                try:
                    # Extract text from page
                    page_text = page.extract_text()
                    
                    # Clean up common PDF extraction issues
                    if page_text:
                        # Fix spacing issues common in PDFs
                        page_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', page_text)  # Add space between camelCase
                        page_text = re.sub(r'(\w)(\d)', r'\1 \2', page_text)  # Add space between word and number
                        page_text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', page_text)  # Add space between number and word
                        page_text = re.sub(r'\s+', ' ', page_text)  # Normalize whitespace
                        
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                        
                except Exception as page_error:
                    print(f"Error extracting page {page_num + 1} from {file_path}: {page_error}")
                    continue
            
            return text.strip()
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = ''
    for para in doc.paragraphs:
        text += para.text + '\n'
    return text

def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def chunk_text(text, chunk_size=1500, overlap=200):
    """Split text into overlapping chunks for better search accuracy"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings near the chunk boundary
            for i in range(end, max(start + chunk_size - 200, start + 1), -1):
                if text[i-1:i+1] in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                    end = i
                    break
        
        chunk = text[start:end].strip()
        if chunk and len(chunk) > 50:  # Only add substantial chunks
            chunks.append(chunk)
        
        start = end - overlap if end < len(text) else len(text)
        
        if start >= len(text):
            break
    
    return chunks

def load_documents(folder_path):
    """Enhanced document loading with chunking for better search results"""
    documents = []
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif filename.lower().endswith('.docx'):
            text = extract_text_from_docx(file_path)
        elif filename.lower().endswith('.txt'):
            text = extract_text_from_txt(file_path)
        else:
            continue
            
        text = (text or "").strip()
        
        # Only process if there's meaningful content
        if text and re.search(r"[A-Za-z]", text) and len(text) > 100:
            
            # For large documents, create chunks for better search
            if len(text) > 2000:
                chunks = chunk_text(text, chunk_size=1500, overlap=200)
                
                for i, chunk in enumerate(chunks):
                    chunk_name = f"{filename} (Part {i+1}/{len(chunks)})" if len(chunks) > 1 else filename
                    documents.append({
                        'filename': chunk_name,
                        'content': chunk,
                        'original_filename': filename
                    })
            else:
                # Keep smaller documents as single units
                documents.append({
                    'filename': filename, 
                    'content': text,
                    'original_filename': filename
                })
    
    return documents