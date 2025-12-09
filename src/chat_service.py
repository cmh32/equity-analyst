"""
RAG Chat Service - Enables Q&A on completed analysis reports.
Uses ChromaDB for vector storage and OpenAI for embeddings/chat.
"""
import os
from typing import Optional
import chromadb
import chromadb.errors
from chromadb.utils import embedding_functions
from openai import OpenAI

from .config import get_api_key, MODEL_NAME


class AnalysisChatService:
    """
    RAG-based chat service for equity analysis reports.
    Stores analysis sections as embeddings for semantic retrieval.
    """

    def __init__(self):
        self.client = OpenAI(api_key=get_api_key("OPENAI_API_KEY"))
        self.chroma_client = chromadb.Client()  # In-memory for simplicity
        self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=get_api_key("OPENAI_API_KEY"),
            model_name="text-embedding-3-small"
        )
        # Store collections per ticker
        self.collections = {}

    def index_analysis(self, ticker: str, analysis_data: dict) -> None:
        """
        Index the analysis results into a vector store for RAG retrieval.

        Args:
            ticker: Stock ticker symbol
            analysis_data: Dict with 'final_report' and 'details' from analysis
        """
        # Create or get collection for this ticker
        collection_name = f"analysis_{ticker.lower()}"

        # Delete existing collection if it exists (fresh index each time)
        try:
            self.chroma_client.delete_collection(collection_name)
        except (ValueError, chromadb.errors.NotFoundError):
            pass

        collection = self.chroma_client.create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )
        self.collections[ticker.upper()] = collection

        # Prepare documents from analysis
        documents = []
        metadatas = []
        ids = []

        # Add the final CIO report (chunked by sections)
        final_report = analysis_data.get("final_report", "")
        cio_sections = self._split_into_sections(final_report, "CIO Memo")
        for i, (section_title, section_content) in enumerate(cio_sections):
            documents.append(section_content)
            metadatas.append({"source": "CIO Memo", "section": section_title})
            ids.append(f"cio_{i}")

        # Add individual agent outputs from details
        details = analysis_data.get("details", {})
        for agent_name, output in details.items():
            if output and isinstance(output, str):
                # Chunk large outputs
                chunks = self._chunk_text(output, max_chars=1500)
                for j, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({"source": agent_name, "section": f"chunk_{j}"})
                    ids.append(f"{agent_name.lower().replace(' ', '_')}_{j}")

        # Filter out empty documents
        valid_docs = []
        valid_metas = []
        valid_ids = []

        for doc, meta, doc_id in zip(documents, metadatas, ids):
            if doc and doc.strip():
                valid_docs.append(doc)
                valid_metas.append(meta)
                valid_ids.append(doc_id)
        
        documents = valid_docs
        metadatas = valid_metas
        ids = valid_ids

        # Add to collection
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"   📚 Indexed {len(documents)} chunks for {ticker}")
        else:
            print("Debug: No documents to add.")


    def chat(self, ticker: str, question: str, history: list = None) -> str:
        """
        Answer a question about the analysis using RAG.

        Args:
            ticker: Stock ticker symbol
            question: User's question
            history: List of previous messages [{"role": "user/assistant", "content": "..."}]

        Returns:
            Assistant's response
        """
        ticker = ticker.upper()

        if ticker not in self.collections:
            return f"No analysis found for {ticker}. Please run an analysis first."

        collection = self.collections[ticker]

        # Retrieve relevant chunks
        results = collection.query(
            query_texts=[question],
            n_results=5
        )

        # Build context from retrieved chunks
        context_parts = []
        if results["documents"] and results["documents"][0]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                source = meta.get("source", "Unknown")
                context_parts.append(f"[Source: {source}]\n{doc}")

        context = "\n\n---\n\n".join(context_parts)

        # Build messages for chat
        messages = [
            {
                "role": "system",
                "content": f"""You are an AI assistant helping users understand an equity analysis report for {ticker}.

Use the following context from the analysis to answer questions. If the context doesn't contain the answer, say so clearly.

Be specific and cite which analyst (Macro, Quant, Technical, Fundamental, or CIO) the information comes from when relevant.

CONTEXT:
{context}"""
            }
        ]

        # Add conversation history
        if history:
            for msg in history[-6:]:  # Keep last 6 messages to manage context
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current question
        messages.append({"role": "user", "content": question})

        # Get response from LLM
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_completion_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"DEBUG ERROR: {type(e).__name__}: {e}")
            return f"Error getting response: {e}"

    def _split_into_sections(self, text: str, source: str) -> list:
        """Split CIO memo into sections based on headers."""
        sections = []

        # Common section headers
        headers = [
            "Recommendation", "Executive Summary", "Macro & Sentiment",
            "Quantitative Snapshot", "Fundamental Analysis", "Technical Analysis",
            "Scenario Analysis", "Actionable Takeaways", "Data Caveats"
        ]

        lines = text.split('\n')
        current_section = "Introduction"
        current_content = []

        for line in lines:
            # Check if line is a section header
            is_header = False
            for header in headers:
                if line.strip().lower().startswith(header.lower()):
                    # Save previous section
                    if current_content:
                        sections.append((current_section, '\n'.join(current_content)))
                    current_section = header
                    current_content = [line]
                    is_header = True
                    break

            if not is_header:
                current_content.append(line)

        # Add final section
        if current_content:
            sections.append((current_section, '\n'.join(current_content)))

        return sections

    def _chunk_text(self, text: str, max_chars: int = 1500) -> list:
        """Split text into chunks, trying to break at paragraph boundaries."""
        if len(text) <= max_chars:
            return [text]

        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # If single paragraph is too long, split by sentences
                if len(para) > max_chars:
                    sentences = para.replace('. ', '.\n').split('\n')
                    current_chunk = ""
                    for sent in sentences:
                        if len(current_chunk) + len(sent) + 1 <= max_chars:
                            current_chunk += sent + " "
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sent + " "
                else:
                    current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def has_analysis(self, ticker: str) -> bool:
        """Check if an analysis exists for the given ticker."""
        return ticker.upper() in self.collections


# Global instance for the API
chat_service = AnalysisChatService()
