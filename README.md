# WNS Vox BOT - Enterprise Document Intelligence System

[![Production Ready](https://img.shields.io/badge/Production-Ready-green)](https://github.com) [![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue)](https://python.org) [![Streamlit](https://img.shields.io/badge/Streamlit-1.50+-red)](https://streamlit.io) [![Security](https://img.shields.io/badge/Security-Validated-orange)](https://github.com)

**WNS Vox BOT v2.0.0** is a production-ready, enterprise-grade document intelligence and conversational AI system designed for professional environments. Built with security, scalability, and reliability at its core.

## 🚀 Key Features

### 🔒 Enterprise Security
- **Input validation & sanitization** - Comprehensive validation for all user inputs
- **File type validation** - MIME type checking and file signature verification  
- **Rate limiting** - Configurable request throttling to prevent abuse
- **Security logging** - Detailed audit trail for all security events
- **Circuit breakers** - Fault tolerance for critical operations

### 📊 Production Monitoring
- **Structured logging** - JSON-formatted logs with detailed context
- **Performance metrics** - Search performance, file processing times
- **Health checks** - System status monitoring and alerting
- **Error tracking** - Comprehensive exception handling and reporting

### ⚡ High Performance
- **Intelligent caching** - Query result caching for improved response times
- **Optimized search** - Multi-backend search with TF-IDF and keyword fallbacks
- **Document chunking** - Smart text segmentation for better search accuracy
- **Resource management** - Memory-efficient processing with configurable limits

## 🛠️ Installation

### Quick Start

1. **Clone and setup:**
```bash
git clone <repository-url>
cd ChatBOT
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Run application:**
```bash
# Development
streamlit run app_production.py --server.port 8501

# Production  
python -m uvicorn app_production:app --host 0.0.0.0 --port 8501
```

3. **Access:** `http://localhost:8501`

## ⚙️ Configuration

Create `.env` file for configuration:

```bash
# Application
APP_NAME="WNS Vox BOT"
DEBUG_MODE=false

# Security
MAX_FILE_SIZE=52428800
RATE_LIMIT_PER_MINUTE=60
ENABLE_FILE_SCAN=true

# Performance
CACHE_TTL=3600
SEARCH_MAX_RESULTS=5
```

## 📚 Usage

1. **Upload documents** (PDF, DOCX, TXT)
2. **Ask questions** in natural language
3. **Get intelligent responses** with source attribution
4. **Monitor performance** with debug mode

## 🚀 Production Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app_production.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Direct Deployment
```bash
export ENVIRONMENT=production
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app_production:app --bind 0.0.0.0:8501
```

## 🛡️ Security Features

- **Input validation** for all user inputs
- **File type verification** with MIME checking
- **Rate limiting** to prevent abuse
- **Security audit logging**
- **Circuit breaker patterns** for fault tolerance

## 📊 Monitoring

- **Structured JSON logging** in `logs/`
- **Performance metrics** tracking
- **Health check endpoints**
- **Error rate monitoring**

## 🧪 Testing

```bash
pip install pytest pytest-cov
pytest --cov=. --cov-report=html
```

## 📝 Project Structure

```
ChatBOT/
├── app_production.py     # Production Streamlit application
├── config.py            # Configuration management
├── production_logger.py # Structured logging system
├── validation.py        # Input validation & security
├── exception_handler.py # Error handling & circuit breakers
├── search_prod.py       # Production search engine
├── ingestion_prod.py    # Production document processing
├── requirements.txt     # Production dependencies
├── .env.example         # Environment template
├── .gitignore          # Git ignore rules
├── data/               # Document storage
├── logs/               # Application logs
└── temp/               # Temporary files
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Run tests: `pytest`
4. Submit pull request

## 📄 License

Copyright (c) 2025 WNS Global Services. All rights reserved.

---

**Built with ❤️ for Agent Excellence at WNS Global Services**

## Requirements

- Python 3.7+
- Libraries: streamlit, scikit-learn, pandas, PyPDF2, python-docx, sentence-transformers, nltk

## Notes

- The app uses TF-IDF for search; sentence embeddings can be integrated by modifying `search.py`.
- For production, consider adding authentication, better error handling, and integration with actual SharePoint.
- Ensure documents are text-extractable; scanned PDFs may require OCR preprocessing.