"""
Enhanced PDF processing service for extracting and chunking text from PDF documents.
"""

import os
import PyPDF2
from typing import Tuple, Optional, List, Dict, Any
import logging
from pathlib import Path
import re
import tiktoken

logger = logging.getLogger(__name__)

class PDFChunk:
    """Represents a chunk of text from a PDF with metadata."""
    
    def __init__(self, content: str, page_number: int, chunk_index: int, metadata: Dict[str, Any] = None):
        self.content = content
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.metadata = metadata or {}
    
    def __str__(self):
        return f"Page {self.page_number}, Chunk {self.chunk_index}: {self.content[:100]}..."

class PDFService:
    """Enhanced service for processing PDF documents with chunking and metadata."""
    
    def __init__(self, upload_dir: str = "uploads"):
        """Initialize PDF service with upload directory."""
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self._current_pdf_text: Optional[str] = None
        self._current_pdf_path: Optional[str] = None
        self._current_chunks: List[PDFChunk] = []
        
        # Initialize tokenizer for chunking
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        except:
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, int, List[PDFChunk]]:
        """
        Extract text from a PDF file with enhanced processing.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (extracted_text, number_of_pages, chunks)
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                all_text = []
                all_chunks = []
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text.strip():  # Only process non-empty pages
                        # Clean up the text
                        cleaned_text = self._clean_text(page_text)
                        all_text.append(cleaned_text)
                        
                        # Create chunks for this page
                        page_chunks = self._create_chunks(cleaned_text, page_num)
                        all_chunks.extend(page_chunks)
                
                extracted_text = '\n\n'.join(all_text)
                logger.info(f"Successfully extracted text from {pdf_path} ({num_pages} pages, {len(all_chunks)} chunks)")
                
                return extracted_text, num_pages, all_chunks
                
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers/footers (common patterns)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)  # Standalone page numbers
        
        # Fix common OCR issues
        text = text.replace('|', 'I')  # Common OCR mistake
        text = text.replace('0', 'O')  # In certain contexts
        
        # Remove excessive line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()
    
    def _create_chunks(self, text: str, page_number: int, max_tokens: int = 1000) -> List[PDFChunk]:
        """Create chunks from text with overlap for better context."""
        if not text.strip():
            return []
        
        chunks = []
        sentences = self._split_into_sentences(text)
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)
            
            # If adding this sentence would exceed the limit
            if current_tokens + sentence_tokens > max_tokens and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunk = PDFChunk(
                    content=chunk_text,
                    page_number=page_number,
                    chunk_index=chunk_index,
                    metadata={
                        'tokens': current_tokens,
                        'start_sentence': 0,
                        'end_sentence': len(current_chunk)
                    }
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap (keep last 2 sentences)
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_tokens = sum(self.count_tokens(s) for s in current_chunk)
                chunk_index += 1
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add the last chunk if it has content
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk = PDFChunk(
                content=chunk_text,
                page_number=page_number,
                chunk_index=chunk_index,
                metadata={
                    'tokens': current_tokens,
                    'start_sentence': 0,
                    'end_sentence': len(current_chunk)
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while preserving structure."""
        # Split on sentence endings, but be careful with abbreviations
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter out empty sentences and clean up
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def save_pdf(self, file_content: bytes, filename: str) -> str:
        """
        Save uploaded PDF file to disk.
        
        Args:
            file_content: PDF file content as bytes
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        try:
            # Ensure filename is safe
            safe_filename = self._sanitize_filename(filename)
            file_path = self.upload_dir / safe_filename
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"PDF saved to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving PDF {filename}: {str(e)}")
            raise ValueError(f"Failed to save PDF: {str(e)}")
    
    def process_pdf(self, file_content: bytes, filename: str) -> Tuple[str, int, int, List[PDFChunk]]:
        """
        Process uploaded PDF: save, extract text, and create chunks.
        
        Args:
            file_content: PDF file content as bytes
            filename: Original filename
            
        Returns:
            Tuple of (extracted_text, number_of_pages, text_length, chunks)
        """
        # Save the PDF
        pdf_path = self.save_pdf(file_content, filename)
        
        # Extract text and create chunks
        extracted_text, num_pages, chunks = self.extract_text_from_pdf(pdf_path)
        
        # Store current PDF info
        self._current_pdf_text = extracted_text
        self._current_pdf_path = pdf_path
        self._current_chunks = chunks
        
        return extracted_text, num_pages, len(extracted_text), chunks
    
    def get_current_pdf_text(self) -> Optional[str]:
        """Get text from the currently loaded PDF."""
        return self._current_pdf_text
    
    def get_current_pdf_path(self) -> Optional[str]:
        """Get path of the currently loaded PDF."""
        return self._current_pdf_path
    
    def get_current_chunks(self) -> List[PDFChunk]:
        """Get chunks from the currently loaded PDF."""
        return self._current_chunks
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent security issues."""
        # Remove path traversal attempts
        filename = os.path.basename(filename)
        
        # Remove or replace dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
        
        # Ensure it ends with .pdf
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        
        return filename
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old PDF files to save disk space."""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for file_path in self.upload_dir.glob("*.pdf"):
                if current_time - file_path.stat().st_mtime > max_age_seconds:
                    file_path.unlink()
                    logger.info(f"Cleaned up old file: {file_path}")
                    
        except Exception as e:
            logger.warning(f"Error during cleanup: {str(e)}") 