#!/bin/bash

echo "🚀 Setting up Talk Vault backend..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r api/requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Create environment file
cp api/.env.example api/.env

# Create uploads directory
mkdir -p api/uploads

echo "✅ Backend setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Update api/.env with your configurations"
echo "3. Run the server: cd api && python -m uvicorn app.main:app --reload"
echo ""
echo "Backend will be available at: http://localhost:8000"
echo "API documentation: http://localhost:8000/docs"
