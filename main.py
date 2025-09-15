from flask import Flask, request, render_template_string, send_from_directory, redirect, url_for
import os
import re

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

KEYWORDS = ["resume", "job", "experience", "education", "python", "project"]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Text File Analyzer</title>
    <style>
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; flex-direction: column; margin: 0; background: #f9f9f9; padding: 20px;}
        .container { max-width: 900px; width: 100%; padding: 20px; }
        h1, h2 { text-align: center; color: #333; }
        form { margin-bottom: 20px; padding: 15px; background: #fff; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; }
        input[type="file"], input[type="text"], select { padding: 8px; margin: 10px 0; }
        input[type="submit"] { padding: 8px 15px; border: none; background: #007BFF; color: white; border-radius: 5px; cursor: pointer; }
        input[type="submit"]:hover { background: #0056b3; }
        .result, .search-results, .uploaded-files { padding: 15px; background: #fff; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-top: 20px; }
        ul { list-style-type: none; padding: 0; display: flex; flex-wrap: wrap; gap: 15px; }
        li { display: flex; flex-direction: column; align-items: center; width: 120px; word-break: break-word; }
        .file-icon { font-size: 50px; color: #007BFF; }
        a, button { margin-top: 5px; text-decoration: none; color: white; background: #28a745; border: none; padding: 5px 10px; border-radius: 5px; cursor: pointer; }
        a:hover, button:hover { opacity: 0.8; }
        .delete-btn { background: #dc3545; }
        .highlight { background-color: yellow; font-weight: bold; }
        .file-preview { white-space: pre-wrap; background: #f1f1f1; padding: 10px; border-radius: 5px; margin-top: 10px; max-height: 200px; overflow-y: hidden; }
        .expanded { max-height: 600px !important; overflow-y: auto; }
        .toggle-btn { display: inline-block; margin-top: 8px; cursor: pointer; color: #007BFF; font-size: 14px; }
        select { width: 200px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📂 Text File Analyzer</h1>

        <!-- Upload Section -->
        <h2>Upload .txt files</h2>
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="files" accept=".txt" multiple required>
            <input type="submit" value="Analyze">
        </form>

        <!-- Uploaded Files Section -->
        <div class="uploaded-files">
            <h2>Uploaded Files</h2>
            {% if uploaded_files %}
            <ul>
                {% for f in uploaded_files %}
                <li>
                    <div class="file-icon">📄</div>
                    <div>{{ f }}</div>
                    <a href="/download/{{ f }}" target="_blank">Download</a>
                    <form method="POST" action="/delete/{{ f }}" style="margin-top: 5px;">
                        <button type="submit" class="delete-btn">Delete</button>
                    </form>
                </li>
                {% endfor %}
            </ul>
            {% else %}
            <p>No files uploaded yet.</p>
            {% endif %}
        </div>

        {% if results and not search_word %}
            {% for res in results %}
            <div class="result">
                <h3>Result for {{ res.filename }}</h3>
                <p><b>Word Count:</b> {{ res.word_count }}</p>
                <p><b>Found Keywords:</b> {{ res.found_keywords if res.found_keywords else 'None' }}</p>
                <p><a href="/download/{{ res.filename }}" target="_blank">📥 Open File</a></p>
            </div>
            {% endfor %}
        {% endif %}

        <!-- Search Section -->
        <h2>Search Keywords</h2>
        <form method="GET">
            <input type="text" name="search" placeholder="Enter word to search">
            <br><b>or</b><br>
            <select name="keyword">
                <option value="">-- Select Keyword --</option>
                {% for kw in keywords %}
                <option value="{{ kw }}" {% if search_word == kw %}selected{% endif %}>{{ kw }}</option>
                {% endfor %}
            </select>
            <br>
            <input type="submit" value="Search">
        </form>

        {% if search_word %}
            <div class="search-results">
                <h3>Search Results for '{{ search_word }}'</h3>
                {% if search_results %}
                    <ul>
                        {% for f, highlighted_text in search_results.items() %}
                            <li>
                                <b>{{ f }}</b> — <a href="/download/{{ f }}" target="_blank">📥 Open</a>
                                <div class="file-preview" id="preview-{{ loop.index }}">{{ highlighted_text|safe }}</div>
                                <span class="toggle-btn" onclick="togglePreview({{ loop.index }})">Show More</span>
                            </li>
                        {% endfor %}
                    </ul>
                {% else %}
                    <p>No files contain this word.</p>
                {% endif %}
            </div>
        {% endif %}
    </div>

    <script>
        function togglePreview(index) {
            const preview = document.getElementById("preview-" + index);
            const btn = preview.nextElementSibling;
            preview.classList.toggle("expanded");
            btn.textContent = preview.classList.contains("expanded") ? "Show Less" : "Show More";
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        uploaded_files = request.files.getlist("files")
        for uploaded_file in uploaded_files:
            if uploaded_file.filename.endswith(".txt"):
                filepath = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
                uploaded_file.save(filepath)

                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()

                word_count = len(text.split())
                found_keywords = [kw for kw in KEYWORDS if kw.lower() in text.lower()]
                results.append({"filename": uploaded_file.filename, "word_count": word_count, "found_keywords": found_keywords})

    # Handle search (manual input or dropdown keyword)
    search_word = request.args.get("search") or request.args.get("keyword")
    search_results = {}
    if search_word:
        for fname in os.listdir(UPLOAD_FOLDER):
            if fname.endswith(".txt"):
                filepath = os.path.join(UPLOAD_FOLDER, fname)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                if re.search(re.escape(search_word), text, re.IGNORECASE):
                    highlighted_text = re.sub(
                        f"({re.escape(search_word)})",
                        r'<span class="highlight">\1</span>',
                        text,
                        flags=re.IGNORECASE
                    )
                    search_results[fname] = highlighted_text

    uploaded_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".txt")]

    return render_template_string(
        HTML_TEMPLATE,
        results=results,
        search_word=search_word,
        search_results=search_results,
        keywords=KEYWORDS,
        uploaded_files=uploaded_files
    )

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
