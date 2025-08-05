"""
RAG (Retrieval-Augmented Generation) service for handling embeddings and vector search using Weaviate.
"""

import logging
from typing import List, Dict, Any, Optional
from weaviate import WeaviateClient
from weaviate.classes.config import Property, DataType, Configure
from weaviate.classes.query import Filter, MetadataQuery
import weaviate
from urllib.parse import urlparse
import uuid
from datetime import datetime

from .pdf_service import PDFChunk

logger = logging.getLogger(__name__)

class RAGService:
    """Service for handling embeddings, vector storage, and semantic search using Weaviate."""
    
    def __init__(self, api_key: str, weaviate_url: str, weaviate_api_key: str = "", 
                 class_name: str = "PDFChunks", embedding_model: str = "text-embedding-3-large"):
        """Initialize RAG service with OpenAI and Weaviate configuration."""
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.embedding_model = embedding_model
        self.class_name = class_name
        
        # Initialize Weaviate client v4 for local instance without auth
        parsed = urlparse(weaviate_url)
        self.weaviate_client = weaviate.connect_to_local(
            skip_init_checks=True
        )
        
        # Ensure the class exists
        self._ensure_class_exists()
    
    def _ensure_class_exists(self):
        """Ensure the Weaviate class exists with proper schema."""
        try:
            # Check if class exists
            if not self.weaviate_client.collections.exists(self.class_name):
                logger.info(f"Creating Weaviate class: {self.class_name}")
                
                # Define the class schema using v4 syntax
                self.weaviate_client.collections.create(
                    name=self.class_name,
                    description="PDF document chunks with embeddings for semantic search",
                    vectorizer_config=Configure.Vectorizer.text2vec_openai(
                        model=self.embedding_model
                    ),
                    properties=[
                        Property(
                            name="content",
                            data_type=DataType.TEXT,
                            description="The text content of the PDF chunk"
                        ),
                        Property(
                            name="page_number",
                            data_type=DataType.INT,
                            description="The page number where this chunk was found"
                        ),
                        Property(
                            name="chunk_index",
                            data_type=DataType.INT,
                            description="The index of this chunk within the page"
                        ),
                        Property(
                            name="filename",
                            data_type=DataType.TEXT,
                            description="The source PDF filename"
                        ),
                        Property(
                            name="uploaded_at",
                            data_type=DataType.DATE,
                            description="When this chunk was uploaded"
                        ),
                        Property(
                            name="tokens",
                            data_type=DataType.INT,
                            description="Estimated token count for this chunk"
                        )
                    ]
                )
                logger.info(f"Successfully created Weaviate class: {self.class_name}")
            else:
                logger.info(f"Weaviate class {self.class_name} already exists")
                
        except Exception as e:
            logger.error(f"Error ensuring Weaviate class exists: {str(e)}")
            raise
    
    def create_embeddings(self, chunks: List[PDFChunk], filename: str = "unknown.pdf") -> bool:
        """
        Create embeddings for PDF chunks and store them in Weaviate.
        
        Args:
            chunks: List of PDF chunks to embed
            filename: Source PDF filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not chunks:
                logger.warning("No chunks provided for embedding")
                return False
            
            logger.info(f"Creating embeddings for {len(chunks)} chunks in Weaviate...")
            
            # Clear existing data for this filename (optional - for updates)
            self._clear_existing_data(filename)
            
            # Get the collection
            collection = self.weaviate_client.collections.get(self.class_name)
            
            # Process chunks in batches
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                
                # Prepare batch data
                batch_data = []
                for chunk in batch_chunks:
                    data_object = {
                        "content": chunk.content,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                        "filename": filename,
                        "uploaded_at": datetime.now().isoformat(),
                        "tokens": chunk.metadata.get('tokens', 0)
                    }
                    batch_data.append(data_object)
                
                # Add batch to Weaviate using v4 API
                collection.data.insert_many(batch_data)
                
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
            
            logger.info(f"Successfully created embeddings for {len(chunks)} chunks in Weaviate")
            return True
            
        except Exception as e:
            logger.error(f"Error creating embeddings in Weaviate: {str(e)}")
            return False
    
    def _clear_existing_data(self, filename: str):
        """Clear existing data for a specific filename."""
        try:
            # Get the collection
            collection = self.weaviate_client.collections.get(self.class_name)
            
            # Delete objects with matching filename using v4 API
            result = collection.data.delete_many(
                where=Filter.by_property("filename").equal(filename)
            )
            
            if result:
                logger.info(f"Cleared {result} existing objects for filename: {filename}")
                
        except Exception as e:
            logger.warning(f"Error clearing existing data: {str(e)}")
    
    def search(self, query: str, top_k: int = 5, filename: str = None) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks using semantic similarity in Weaviate.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            filename: Optional filter by filename
            
        Returns:
            List of relevant chunks with scores
        """
        try:
            # Get the collection
            collection = self.weaviate_client.collections.get(self.class_name)
            
            # Always use semantic search for better matching
            response = collection.query.near_text(
                query=query,
                limit=top_k * 3,  # Get more results to filter from
                return_properties=["content", "page_number", "chunk_index", "filename", "tokens"],
                return_metadata=MetadataQuery(distance=True)
            )
            
            # Process results
            all_results = []
            for result in response.objects:
                all_results.append({
                    'content': result.properties['content'],
                    'page_number': result.properties['page_number'],
                    'chunk_index': result.properties['chunk_index'],
                    'filename': result.properties['filename'],
                    'score': 1 - result.metadata.distance,  # Convert distance to similarity
                    'tokens': result.properties['tokens']
                })
            
            # Filter by filename if specified
            if filename:
                filtered_results = [r for r in all_results if r['filename'] == filename]
                # Return top_k results from filtered results
                results = filtered_results[:top_k]
            else:
                # Return top_k results from all results
                results = all_results[:top_k]
            
            logger.info(f"Found {len(results)} relevant chunks for query: {query[:50]}...")
            
            # Log the retrieved chunks for debugging
            for i, result in enumerate(results):
                logger.info(f"Chunk {i+1}: Page {result['page_number']}, Score: {result['score']:.3f}")
                logger.info(f"Content: {result['content'][:200]}...")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during Weaviate search: {str(e)}")
            return []
    
    def get_relevant_context(self, query: str, max_tokens: int = 5000, filename: str = None) -> str:
        """
        Get relevant context from PDF based on user query using Weaviate.
        
        Args:
            query: User query
            max_tokens: Maximum tokens to include in context
            filename: Optional filter by filename
            
        Returns:
            Relevant context as string
        """
        try:
            # Search for relevant chunks - increased from 10 to 20 for better coverage
            results = self.search(query, top_k=20, filename=filename)
            
            if not results:
                return ""
            
            # Build context from top results
            context_parts = []
            current_tokens = 0
            
            for result in results:
                # Use actual token count if available, otherwise estimate
                chunk_tokens = result.get('tokens', len(result['content'].split()) * 1.3)
                
                if current_tokens + chunk_tokens > max_tokens:
                    break
                
                context_parts.append(
                    f"[Page {result['page_number']}] {result['content']}"
                )
                current_tokens += chunk_tokens
            
            context = "\n\n".join(context_parts)
            
            if context:
                logger.info(f"Retrieved {len(context_parts)} chunks ({current_tokens:.0f} estimated tokens) for query")
                logger.info(f"Context preview: {context[:500]}...")
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {str(e)}")
            return ""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        try:
            # Get the collection
            collection = self.weaviate_client.collections.get(self.class_name)
            
            # Get total count using v4 API
            response = collection.aggregate.over_all(total_count=True)
            total_count = response.total_count
            
            return {
                "status": "ready",
                "total_chunks": total_count,
                "class_name": self.class_name,
                "embedding_model": self.embedding_model,
                "weaviate_url": self.weaviate_client.url
            }
            
        except Exception as e:
            logger.error(f"Error getting Weaviate stats: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def delete_all_data(self) -> bool:
        """Delete all data from the vector store."""
        try:
            # Get the collection
            collection = self.weaviate_client.collections.get(self.class_name)
            
            # Delete all objects using v4 API
            result = collection.data.delete_many()
            logger.info(f"Deleted {result} objects from Weaviate")
            return True
        except Exception as e:
            logger.error(f"Error deleting data: {str(e)}")
            return False 