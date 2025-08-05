#!/bin/bash

# Setup environment variables for the PDF Chatbot with RAG

echo "🚀 Setting up environment variables for PDF Chatbot with RAG"
echo "=========================================================="

# Check if .env already exists
if [ -f "backend/.env" ]; then
    echo "⚠️  backend/.env already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled. Your existing .env file was preserved."
        exit 1
    fi
fi

# Copy the example file
cp backend/env.example backend/.env

echo "✅ Created backend/.env from template"

# Prompt for OpenAI API key
echo ""
echo "🔑 Please enter your OpenAI API key:"
echo "   (You can get one from https://platform.openai.com/api-keys)"
read -p "OpenAI API Key: " openai_key

# Update the .env file with the API key
if [ -n "$openai_key" ]; then
    # Use sed to replace the placeholder with the actual API key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your_openai_api_key_here/$openai_key/g" backend/.env
    else
        # Linux
        sed -i "s/your_openai_api_key_here/$openai_key/g" backend/.env
    fi
    echo "✅ OpenAI API key configured"
else
    echo "⚠️  No API key provided. Please edit backend/.env manually."
fi

echo ""
echo "🎉 Environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Review backend/.env and adjust settings if needed"
echo "   2. Run: docker-compose up -d weaviate"
echo "   3. Run: ./start.sh"
echo ""
echo "🔧 Configuration files:"
echo "   - backend/.env (environment variables)"
echo "   - docker-compose.yml (Weaviate configuration)"
echo "   - backend/app/utils/config.py (application settings)" 