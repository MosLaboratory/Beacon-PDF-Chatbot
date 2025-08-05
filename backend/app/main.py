"""
Main FastAPI application for the PDF Chatbot with RAG capabilities.
"""

import logging
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .models import (
    ChatRequest, ChatResponse, UploadResponse, 
    HealthResponse, ErrorResponse, ChatMessage
)
from .services.pdf_service import PDFService
from .services.chat_service import ChatService
from .utils.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
pdf_service: PDFService = None
chat_service: ChatService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global pdf_service, chat_service
    
    # Startup
    logger.info("Starting PDF Chatbot application with RAG capabilities...")
    
    # Validate settings
    try:
        settings.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    # Initialize services
    pdf_service = PDFService(upload_dir=settings.UPLOAD_DIR)
    chat_service = ChatService(
        api_key=settings.OPENAI_API_KEY,
        weaviate_url=settings.WEAVIATE_URL,
        weaviate_api_key=settings.WEAVIATE_API_KEY,
        weaviate_class_name=settings.WEAVIATE_CLASS_NAME,
        model=settings.DEFAULT_MODEL,
        max_tokens=settings.MAX_TOKENS,
        temperature=settings.TEMPERATURE
    )
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PDF Chatbot application...")
    if pdf_service:
        pdf_service.cleanup_old_files()

# Create FastAPI app
app = FastAPI(
    title="PDF Chatbot API with RAG",
    description="A conversational chatbot that can interact with PDF documents using RAG",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with health information."""
    return HealthResponse(
        status="healthy",
        version="2.0.0"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="2.0.0"
    )

@app.post("/upload-pdf", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF file with enhanced chunking and RAG preparation.
    
    Args:
        file: PDF file to upload
        
    Returns:
        Upload response with file information
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Process PDF with enhanced chunking
        extracted_text, num_pages, text_length, chunks = pdf_service.process_pdf(content, file.filename)
        
        # Set PDF context for chat service (including chunks for RAG)
        chat_service.set_pdf_context(extracted_text, chunks, file.filename)
        
        logger.info(f"PDF uploaded successfully: {file.filename} ({num_pages} pages, {len(chunks)} chunks)")
        
        return UploadResponse(
            filename=file.filename,
            pages=num_pages,
            text_length=text_length,
            message=f"PDF uploaded and processed successfully. Created {len(chunks)} chunks for RAG."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload PDF: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the chatbot using RAG when available.
    
    Args:
        request: Chat request with message and conversation history
        
    Returns:
        Chat response with AI reply and updated conversation history
    """
    try:
        # Check if PDF is loaded
        if not pdf_service.get_current_pdf_text():
            raise HTTPException(
                status_code=400, 
                detail="No PDF loaded. Please upload a PDF first."
            )
        
        # Process chat message with RAG
        result = chat_service.chat(request.message, request.conversation_history)
        
        return ChatResponse(
            response=result["response"],
            conversation_history=result["conversation_history"],
            tokens_used=result["tokens_used"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")

@app.get("/model-info")
async def get_model_info():
    """Get information about the current model configuration and RAG status."""
    try:
        return chat_service.get_model_info()
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@app.get("/pdf-info")
async def get_pdf_info():
    """Get information about the currently loaded PDF."""
    try:
        pdf_text = pdf_service.get_current_pdf_text()
        pdf_path = pdf_service.get_current_pdf_path()
        chunks = pdf_service.get_current_chunks()
        
        if not pdf_text:
            return {"message": "No PDF currently loaded"}
        
        return {
            "filename": os.path.basename(pdf_path) if pdf_path else "Unknown",
            "text_length": len(pdf_text),
            "has_content": bool(pdf_text.strip()),
            "chunks_count": len(chunks),
            "rag_ready": len(chunks) > 5
        }
        
    except Exception as e:
        logger.error(f"Error getting PDF info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get PDF info: {str(e)}")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 