import os
import io
from flask import Flask, render_template, request, jsonify
from rag_engine import RagEngine
from dotenv import load_dotenv
from pypdf import PdfReader

# Load env before imports typically, but here we do it for the app config
load_dotenv()

app = Flask(__name__)

# Initialize RAG Engine
# We instantiate it once. 
rag_engine = RagEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ingest', methods=['POST'])
def ingest():
    data = request.json
    text_content = data.get('text')
    
    if not text_content:
        return jsonify({"status": "error", "message": "No text provided"}), 400
    
    try:
        num_chunks = rag_engine.ingest_text(text_content)
        return jsonify({
            "status": "success", 
            "message": f"Successfully processed and indexed {num_chunks} chunks."
        })
    except Exception as e:
        # Log the error properly in a real app
        print(f"Ingest Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
        
    if file and file.filename.lower().endswith('.pdf'):
        try:
            # Read PDF from memory
            pdf_stream = io.BytesIO(file.read())
            reader = PdfReader(pdf_stream)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            if not text.strip():
                 return jsonify({"status": "error", "message": "Could not extract text from PDF (scanned?)"}), 400

            # Reuse existing ingest logic
            num_chunks = rag_engine.ingest_text(text)
            return jsonify({
                "status": "success", 
                "message": f"Successfully processed PDF '{file.filename}' and indexed {num_chunks} chunks."
            })
        except Exception as e:
            print(f"Upload Error: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "error", "message": "Only PDF files are supported currently"}), 400

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({"status": "error", "message": "No question provided"}), 400
    
    try:
        result = rag_engine.search(question)
        return jsonify({
            "status": "success", 
            "answer": result['answer'],
            "citations": result['citations'],
            "timings": result['timings']
        })
    except Exception as e:
        print(f"Query Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
