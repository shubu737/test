from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from PIL import Image
import os
import sqlite3

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])  # Restrict CORS for security

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Configure Tesseract path if needed
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Database Setup
def init_db():
    try:
        conn = sqlite3.connect("notes.db")
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS notes 
                          (id INTEGER PRIMARY KEY, filename TEXT, text TEXT, tags TEXT)''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

init_db()  # Initialize DB on startup

@app.route("/")
def home():
    return jsonify({"message": "Welcome to the OCR Notes API!"})

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    tags = request.form.get("tags", "")  # Get tags from the request

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    # OCR Processing
    text = pytesseract.image_to_string(Image.open(filepath))

    # Store in DB
    conn = sqlite3.connect("notes.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO notes (filename, text, tags) VALUES (?, ?, ?)", 
                   (file.filename, text, tags))
    conn.commit()
    conn.close()

    return jsonify({"message": "File uploaded", "text": text, "tags": tags})

@app.route("/search", methods=["GET"])
def search_notes():
    query = request.args.get("query", "")
    conn = sqlite3.connect("notes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT filename, text, tags FROM notes WHERE text LIKE ? OR tags LIKE ?", 
                   ('%' + query + '%', '%' + query + '%'))
                   
    results = cursor.fetchall()
    conn.close()

    return jsonify({"results": [{"filename": r[0], "text": r[1], "tags": r[2]} for r in results]})

if __name__ == "__main__":
    app.run(debug=True)
