# Talk Vault - AI-Powered Meeting Summarization System

Talk Vault is a secure, AI-powered web application that transforms raw meeting audio and text into structured, actionable summaries with privacy-first redaction capabilities.

## 🌟 Features

- **Intelligent Summarization**: Automatically generates concise summaries from meeting transcripts
- **Action Item Extraction**: Identifies tasks, owners, and deadlines from discussions
- **PII Redaction**: Automatically detects and masks personally identifiable information
- **Secure Authentication**: JWT-based user authentication and authorization
- **RESTful API**: Well-documented API endpoints with OpenAPI/Swagger docs
- **File Upload Support**: Handles both audio files and text transcripts
- **Export Options**: Export summaries in various formats (PDF, JSON, ICS)

## 🏗️ Architecture

```
Talk Vault/
├── api/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py        # FastAPI application entry point
│   │   ├── core/          # Configuration and security
│   │   ├── db/            # Database models and connection
│   │   ├── api/v1/        # API endpoints
│   │   ├── services/      # Business logic services
│   │   └── schemas/       # Pydantic schemas
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile        # Docker configuration
├── nlp/                   # NLP processing modules
│   └── src/talkvault_nlp/
│       ├── summarizer.py     # Text summarization
│       ├── action_extractor.py # Action item extraction
│       └── pii_redactor.py    # PII detection and redaction
├── src/                   # React frontend (existing)
├── docker-compose.yml     # Multi-service Docker setup
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Docker (optional)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/RaghavAgarwal-01/TalkVault.git
   cd TalkVault
   ```

2. **Set up the backend**
   ```bash
   # Linux/Mac
   chmod +x setup_backend.sh
   ./setup_backend.sh
   
   # Windows
   setup_backend.bat
   ```

3. **Activate virtual environment and run**
   ```bash
   # Linux/Mac
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate.bat
   
   # Run the API server
   cd api
   python -m uvicorn app.main:app --reload
   ```

### Frontend Setup

Your existing React frontend should work with the new backend. Update your API endpoint configuration to point to `http://localhost:8000`.

### Using Docker

```bash
# Build and run all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Configuration

### Environment Variables

Copy `api/.env.example` to `api/.env` and update:

```env
# Database
DATABASE_URL=sqlite:///./talkvault.db

# JWT Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# File Upload
MAX_FILE_SIZE=52428800

# CORS
ALLOWED_HOSTS=["http://localhost:3000", "http://localhost:5173"]
```

### Database Migration

The application uses SQLite by default. For PostgreSQL:

1. Update `DATABASE_URL` in `.env`
2. Uncomment `psycopg2-binary` in `requirements.txt`
3. Install dependencies: `pip install -r requirements.txt`

## 🧪 API Usage Examples

### Authentication

```bash
# Sign up
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "testuser", "password": "password123"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### File Upload

```bash
# Upload text
curl -X POST "http://localhost:8000/api/v1/upload/text" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=Team Meeting" \
  -F "content=Meeting transcript content here..."

# Upload file
curl -X POST "http://localhost:8000/api/v1/upload/file" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=Team Meeting" \
  -F "file=@meeting.txt"
```

### Get Meetings

```bash
curl -X GET "http://localhost:8000/api/v1/meetings/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔒 Security Features

- **Password Hashing**: Using bcrypt for secure password storage
- **JWT Tokens**: Secure authentication with configurable expiration
- **PII Redaction**: Automatic detection and masking of sensitive information
- **CORS Protection**: Configurable allowed origins
- **Input Validation**: Pydantic schemas for request/response validation

## 🧠 NLP Pipeline

1. **Text Processing**: Clean and preprocess input text
2. **Summarization**: Extract key sentences using TextRank algorithm
3. **Action Extraction**: Rule-based and NER approach for task identification
4. **PII Redaction**: Pattern matching and named entity recognition for privacy
5. **Storage**: Secure storage with both original and redacted versions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, email [your-email@example.com] or create an issue on GitHub.

## 🚧 Development Status

- ✅ Backend API (FastAPI)
- ✅ Authentication system
- ✅ File upload handling
- ✅ NLP processing pipeline
- ✅ Database models
- ✅ Docker configuration
- 🔄 Frontend integration (in progress)
- 🔄 Audio transcription service
- 📋 Export functionality
- 📋 Advanced PII detection
- 📋 Real-time processing updates

---

Built with ❤️ by the Talk Vault Team
