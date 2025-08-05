"""
Enhanced chat service for handling AI interactions using OpenAI with RAG capabilities.
"""

import logging
from typing import List, Optional, Dict, Any
from openai import OpenAI
import tiktoken

from ..models import ChatMessage
from .rag_service import RAGService

logger = logging.getLogger(__name__)

class ChatService:
    """Enhanced service for handling chat interactions with AI using OpenAI and RAG."""
    
    def __init__(self, api_key: str, weaviate_url: str, weaviate_api_key: str = "", 
                 weaviate_class_name: str = "PDFChunks", model: str = "gpt-3.5-turbo", 
                 max_tokens: int = 1000, temperature: float = 0.7):
        """Initialize chat service with OpenAI and Weaviate configuration."""
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        
        # Initialize RAG service with Weaviate
        self.rag_service = RAGService(
            api_key=api_key,
            weaviate_url=weaviate_url,
            weaviate_api_key=weaviate_api_key,
            class_name=weaviate_class_name
        )
        
        # Store PDF context
        self.pdf_context: Optional[str] = None
        self.use_rag: bool = False
        self.current_filename: str = None
    
    def set_pdf_context(self, pdf_text: str, chunks=None, filename: str = "unknown.pdf"):
        """Set the PDF context for the chat service."""
        self.pdf_context = pdf_text
        self.current_filename = filename
        
        # If chunks are provided, use RAG
        if chunks and len(chunks) > 5:  # Use RAG for PDFs with more than 5 chunks
            logger.info(f"Setting up RAG for {len(chunks)} chunks from {filename}")
            success = self.rag_service.create_embeddings(chunks, filename)
            if success:
                self.use_rag = True
                logger.info("RAG system activated with Weaviate")
            else:
                logger.warning("Failed to create embeddings, falling back to simple context")
                self.use_rag = False
        else:
            self.use_rag = False
            logger.info("Using simple context mode")
    
    def create_system_prompt(self, relevant_context: str = "") -> str:
        """Create system prompt for the AI."""
        base_prompt = """You are a helpful AI assistant that can answer questions about PDF documents. 
        You should provide accurate, helpful, and concise responses based on the information available in the PDF.
        
        Guidelines:
        - Only answer questions based on the information provided in the PDF
        - If the information is not available in the PDF, clearly state that
        - Be helpful and conversational in your responses
        - Provide specific references when possible (mention page numbers if available)
        - Keep responses concise but informative
        - If you're referencing specific content, cite the page number
        """
        
        if relevant_context:
            base_prompt += f"\n\nRelevant PDF Content:\n{relevant_context}"
        elif self.pdf_context and not self.use_rag:
            # Fallback to simple context for short PDFs
            context_preview = self.pdf_context[:4000]
            base_prompt += f"\n\nPDF Content:\n{context_preview}"
            
            if len(self.pdf_context) > 4000:
                base_prompt += "\n\n[Note: This is a preview of the PDF content. The full document contains more information.]"
        
        return base_prompt
    
    def chat(self, message: str, conversation_history: Optional[List[ChatMessage]] = None) -> Dict[str, Any]:
        """
        Process a chat message and return AI response using RAG when available.
        
        Args:
            message: User message
            conversation_history: Previous conversation messages
            
        Returns:
            Dictionary containing response and updated conversation history
        """
        try:
            # Get relevant context using RAG or fallback
            relevant_context = ""
            if self.use_rag:
                relevant_context = self.rag_service.get_relevant_context(
                    message, 
                    max_tokens=5000, 
                    filename=self.current_filename
                )
                logger.info(f"RAG retrieved {len(relevant_context)} characters of relevant context")
            elif self.pdf_context:
                # Simple fallback for short PDFs
                relevant_context = self.pdf_context[:5000]
            
            # Create system prompt
            system_prompt = self.create_system_prompt(relevant_context)
            
            # Prepare messages for OpenAI API
            messages = []
            
            # Add system message
            messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history (keep last 8 messages to save tokens for context)
            if conversation_history:
                for msg in conversation_history[-8:]:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Add current user message
            messages.append({"role": "user", "content": message})
            
            # Get AI response from OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            ai_response = response.choices[0].message.content
            
            # Count tokens
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # Update conversation history
            updated_history = conversation_history or []
            updated_history.extend([
                ChatMessage(role="user", content=message),
                ChatMessage(role="assistant", content=ai_response)
            ])
            
            return {
                "response": ai_response,
                "conversation_history": updated_history,
                "tokens_used": tokens_used,
                "rag_used": self.use_rag
            }
            
        except Exception as e:
            logger.error(f"Error in chat service: {str(e)}")
            raise ValueError(f"Failed to process chat message: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model configuration."""
        rag_stats = self.rag_service.get_stats()
        
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "has_pdf_context": bool(self.pdf_context),
            "rag_enabled": self.use_rag,
            "current_filename": self.current_filename,
            "rag_stats": rag_stats
        } 