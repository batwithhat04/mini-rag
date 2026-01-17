import os
import time
import logging
import uuid
from typing import List, Dict, Any

import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
import cohere
import tiktoken
from dotenv import load_dotenv

load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RagEngine:
    def __init__(self):
        # 1. Initialize Clients
        self._init_google()
        self._init_pinecone()
        self._init_cohere()
        
        # 2. Configs for functionality
        self.chunk_size = 1000 # tokens (approx)
        self.chunk_overlap = 150 # tokens
        self.top_k_retrieval = 10
        self.top_n_rerank = 5
        
        # Tokenizer for estimation
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
             # Fallback if tiktoken fails (unlikely)
            self.tokenizer = None

    def _init_google(self):
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        if self.google_api_key:
            genai.configure(api_key=self.google_api_key)
            self.embed_model = "models/text-embedding-004"
            self.llm_model = genai.GenerativeModel("gemini-2.5-flash")
            logger.info("Google Gemini initialized.")
        else:
            logger.warning("GOOGLE_API_KEY not found. LLM features will fail.")

    def _init_pinecone(self):
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "minirag-index")
        
        if self.pinecone_api_key:
            self.pc = Pinecone(api_key=self.pinecone_api_key)
            
            # Check if index exists, else create (Serverless spec)
            existing_indexes = [i.name for i in self.pc.list_indexes()]
            if self.index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                try:
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=768, # Dimension for text-embedding-004
                        metric="cosine",
                        spec=ServerlessSpec(cloud="aws", region="us-east-1")
                    )
                except Exception as e:
                    logger.error(f"Failed to create index: {e}")
            
            self.index = self.pc.Index(self.index_name)
            logger.info("Pinecone initialized.")
        else:
            self.pc = None
            self.index = None
            logger.warning("PINECONE_API_KEY not found. Retrieval will fail.")

    def _init_cohere(self):
        self.cohere_key = os.getenv("COHERE_API_KEY")
        if self.cohere_key:
            self.co = cohere.Client(self.cohere_key)
            logger.info("Cohere initialized.")
        else:
            self.co = None
            logger.warning("COHERE_API_KEY not found. Reranking will fail.")

    def count_tokens(self, text: str) -> int:
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return len(text) // 4 # Rough estimate

    def chunk_text(self, text: str) -> List[str]:
        """
        Splits text into chunks of roughly `chunk_size` tokens with `chunk_overlap`.
        """
        tokens = self.tokenizer.encode(text) if self.tokenizer else list(text) # Fallback is bad but functional
        
        chunks = []
        for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
            chunk_tokens = tokens[i : i + self.chunk_size]
            if self.tokenizer:
                chunk_text = self.tokenizer.decode(chunk_tokens)
            else:
                chunk_text = "".join(chunk_tokens)
            chunks.append(chunk_text)
        
        return chunks

    def ingest_text(self, text: str):
        """
        Chunks text, creates embeddings, and upserts to Pinecone.
        """
        if not self.index or not self.google_api_key:
            raise ValueError("Services not configured. check .env")

        # 1. Chunk
        chunks = self.chunk_text(text)
        logger.info(f"Created {len(chunks)} chunks.")

        # 2. Embed
        # Gemini batch embedding
        # Prepare content for embedding
        points_to_upsert = []
        
        # Batching for API limits (Gemini has limits on list size)
        batch_size = 50 
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            
            # Get embeddings
            result = genai.embed_content(
                model=self.embed_model,
                content=batch_chunks,
                task_type="retrieval_document"
            )
            embeddings = result['embedding']

            for j, emb in enumerate(embeddings):
                chunk_id = str(uuid.uuid4())
                chunk_content = batch_chunks[j]
                
                metadata = {
                    "text": chunk_content,
                    "position": i + j,
                    "source": "user_upload" # Placeholder for now
                }
                
                points_to_upsert.append((chunk_id, emb, metadata))

        # 3. Upsert to Pinecone (batches of 100 recommended)
        upsert_batch_size = 100
        for i in range(0, len(points_to_upsert), upsert_batch_size):
            batch = points_to_upsert[i : i + upsert_batch_size]
            self.index.upsert(vectors=batch)
            
        return len(chunks)

    def search(self, query: str) -> Dict[str, Any]:
        """
        Full RAG pipeline: Query -> Embed -> Retrieve -> Rerank -> LLM
        Returns: {
            "answer": str,
            "citations": List[Dict],
            "timings": Dict,
            "usage": Dict
        }
        """
        start_time = time.time()
        timings = {}

        if not self.index or not self.google_api_key:
             # Graceful fallback for mock/demo if keys missing
             if not self.google_api_key: return {"answer": "Error: Missing Google API Key.", "citations": [], "timings": {}}
        
        # 1. Embed Query
        t0 = time.time()
        query_embedding_res = genai.embed_content(
            model=self.embed_model,
            content=query,
            task_type="retrieval_query"
        )
        query_vec = query_embedding_res['embedding']
        timings['embedding'] = round(time.time() - t0, 3)

        # 2. Retrieve (Vector Search)
        t0 = time.time()
        retrieval_res = self.index.query(
            vector=query_vec,
            top_k=self.top_k_retrieval,
            include_metadata=True
        )
        
        retrieved_docs = [] # List of {"text": ..., "id": ...}
        for match in retrieval_res['matches']:
            if match.metadata and 'text' in match.metadata:
                retrieved_docs.append({
                    "text": match.metadata['text'],
                    "id": match.id,
                    "score": match.score # similarity score
                })
        timings['retrieval'] = round(time.time() - t0, 3)

        if not retrieved_docs:
            return {
                "answer": "I couldn't find any relevant information in the uploaded documents.",
                "citations": [],
                "timings": timings
            }

        # 3. Rerank (Cohere)
        t0 = time.time()
        documents_text = [d['text'] for d in retrieved_docs]
        top_docs = []
        
        if self.co:
            try:
                rerank_res = self.co.rerank(
                    model="rerank-english-v3.0",
                    query=query,
                    documents=documents_text,
                    top_n=self.top_n_rerank
                )
                for result in rerank_res.results:
                    # result.index corresponds to the index in 'documents_text'
                    original_doc = retrieved_docs[result.index]
                    top_docs.append(original_doc)
            except Exception as e:
                logger.error(f"Cohere Rerank failed: {e}. Falling back to top vector matches.")
                top_docs = retrieved_docs[:self.top_n_rerank]
        else:
            # Fallback if no Cohere key
            logger.info("No Cohere key found, skipping reranker.")
            top_docs = retrieved_docs[:self.top_n_rerank]
            
        timings['reranking'] = round(time.time() - t0, 3)

        # 4. Generate Answer (LLM)
        t0 = time.time()
        
        # Construct Context with [Citation] indices
        context_str = ""
        citations_list = []
        
        for idx, doc in enumerate(top_docs):
            citation_num = idx + 1
            context_str += f"Source [{citation_num}]:\n{doc['text']}\n\n"
            citations_list.append({
                "id": citation_num,
                "text": doc.get('text', '')[:200] + "...", # Snippet for UI
                "full_text": doc.get('text', '')
            })

        system_prompt = (
            "You are an intelligent AI assistant capable of synthesizing information. "
            "Answer the user's question by *synthesizing* and *summarizing* the relevant information from the provided context below. "
            "Do not just copy-paste text (extractive); instead, provide a well-written, abstractive summary that directly answers the question. "
            "However, you MUST still ground your answer in the provided context and include citations [x] where appropriate. "
            "If the answer is not in the context, say 'I cannot answer this based on the provided documents.'"
        )
        
        full_prompt = f"{system_prompt}\n\nExisting Knowledge:\n{context_str}\n\nUser Question: {query}"
        
        # Use the requested stable model
        response = self.llm_model.generate_content(full_prompt)
        answer_text = response.text
        
        timings['generation'] = round(time.time() - t0, 3)
        timings['total'] = round(time.time() - start_time, 3)

        return {
            "answer": answer_text,
            "citations": citations_list,
            "timings": timings,
            "cost_estimate": "Free (Gemini 2.5 Flash)"
        }
