# API Setup Guide

This project requires API keys from three providers to function correctly (Gemini, Pinecone, and Cohere).

## 1. Google Gemini (LLM & Embeddings)
*   **Purpose:** Handles text embeddings and final answer generation.
*   **Provider:** Google AI Studio
*   **Cost:** Free (within rate limits).
*   **Steps:**
    1. Go to [Google AI Studio](https://aistudio.google.com/).
    2. Sign in with your Google account.
    3. Click on "Get API key".
    4. Copy the key string.

## 2. Pinecone (Vector Database)
*   **Purpose:** Stores the document embeddings for fast semantic retrieval.
*   **Provider:** Pinecone
*   **Cost:** Free (Starter tier, 1 index).
*   **Steps:**
    1. Go to [Pinecone Login](https://app.pinecone.io/) and sign up.
    2. Go to "API Keys" in the sidebar and copy your key.
    3. **(Optional):** Create an index named `minirag-index` (Dimensions: 768, Metric: Cosine).

## 3. Cohere (Reranking)
*   **Purpose:** Re-orders the retrieved documents to ensure the most relevant ones are passed to the LLM (specialized rerank model).
*   **Provider:** Cohere
*   **Cost:** Free (Trial keys available).
*   **Steps:**
    1. Go to [Cohere Dashboard](https://dashboard.cohere.com/welcome/register).
    2. Sign up/Login.
    3. Go to "API Keys".
    4. Create a "Trial Key" (or use the default one).
    5. Copy the key.

## Final Configuration
Once you have the keys, update your `.env` file:

```ini
GOOGLE_API_KEY=AIzaSy...
PINECONE_API_KEY=pcsk_...
COHERE_API_KEY=vwn...
```

**Note:** Never commit this `.env` file to public repositories.
