# Deployment Guide (GitHub & Render)

This guide walks you through pushing your code to GitHub and hosting it live on Render.

## Part 1: Push to GitHub

1.  **Initialize Git**:
    Open your terminal in the `miniRag` folder and run:
    ```bash
    git init
    # (Checking your .gitignore includes .env is CRITICAL so you don't leak keys!)
    ```

2.  **Commit Code**:
    ```bash
    git add .
    git commit -m "Initial commit of MiniRAG"
    ```

3.  **Create Repo**:
    *   Go to [GitHub.com](https://github.com/new).
    *   Create a new repository named `miniRag` (Public or Private).
    *   **Do not** add a README or .gitignore (we already have them).

4.  **Push**:
    *   Copy the commands under "…or push an existing repository from the command line". It looks like:
    ```bash
    git remote add origin https://github.com/YOUR_USERNAME/miniRag.git
    git branch -M main
    git push -u origin main
    ```

## Part 2: Deploy to Render

1.  **Account**:
    *   Go to [Render.com](https://render.com/) and sign up/login (you can use your GitHub account).

2.  **New Web Service**:
    *   Click the "New +" button → "Web Service".
    *   Select "Build and deploy from a Git repository".
    *   Connect your GitHub account if asked, and select the `miniRag` repo you just pushed.

3.  **Configuration**:
    *   **Name**: `minirag-app` (or similar)
    *   **Region**: Closest to you (e.g., Singapore, Frankfurt, US East).
    *   **Branch**: `main`
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt` (Default is usually fine)
    *   **Start Command**: `gunicorn app:app` (This is defined in the `Procfile` I created, but good to double-check).
    *   **Instance Type**: Free

4.  **Environment Variables (CRITICAL)**:
    *   Scroll down to "Environment Variables".
    *   Click "Add Environment Variable" for each key you have in your local `.env` file:
        *   `GOOGLE_API_KEY`: (Paste your key)
        *   `PINECONE_API_KEY`: (Paste your key)
        *   `PINECONE_INDEX_NAME`: `minirag-index`
        *   `COHERE_API_KEY`: (Paste your key)
        *   `PYTHON_VERSION`: `3.11.0` (Optional, helps sometimes)

5.  **Deploy**:
    *   Click "Create Web Service".
    *   Render will start building. Watch the logs. It takes about 2-5 minutes.
    *   Once done, you will see a green "Live" badge and a URL (e.g., `https://minirag-app.onrender.com`).

## Troubleshooting
*   **Context/Version Errors**: If `pypdf` or imports fail, ensure `requirements.txt` is in the root.
*   **500 Errors**: Check the "Logs" tab in Render. It usually means an API key is missing or invalid.
