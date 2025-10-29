from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from datetime import datetime, timedelta
import sqlite3
import os
import json

try:
    import openai
except Exception:
    openai = None

DB_PATH = 'issues.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
llm=not True
# --- Database helpers ---

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            location TEXT,
            severity TEXT,
            media_path TEXT,
            created_at TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()


def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv


# --- Helpers ---

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_media(file):
    if file and allowed_file(file.filename):
        filename = f"{datetime.utcnow().timestamp()}_{file.filename}"
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        return path
    return None

# --- Routes ---

@app.route('/')
def index():
    issues = query_db('SELECT * FROM issues ORDER BY created_at DESC')
    return render_template('index.html', issues=issues)


@app.route('/issue/<int:issue_id>')
def issue_detail(issue_id):
    issue = query_db('SELECT * FROM issues WHERE id = ?', (issue_id,), one=True)
    if not issue:
        return "Issue not found", 404
    return render_template('issue.html', issue=issue)


@app.route('/new', methods=['GET', 'POST'])
def new_issue():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        location = request.form['location']
        severity = request.form['severity']
        media_file = request.files.get('media')
        media_path = save_media(media_file) if media_file else None
        created_at = datetime.utcnow().isoformat()

        query_db('''INSERT INTO issues (title, description, location, severity, media_path, created_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (title, description, location, severity, media_path, created_at, 'open'))

        return redirect(url_for('index'))
    return render_template('new_issue.html')


@app.route('/resolve/<int:issue_id>', methods=['POST'])
def resolve_issue(issue_id):
    query_db('UPDATE issues SET status = ? WHERE id = ?', ('resolved', issue_id))
    return redirect(url_for('issue_detail', issue_id=issue_id))


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    title = data.get('title', '')
    description = data.get('description', '')
    location = data.get('location', '')
    severity = data.get('severity', 'medium')

    prompt = build_prompt(title, description, location, severity)
    openai_key ="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"

    if openai and openai_key and llm:
        
        client = openai.OpenAI(api_key=openai_key)
        try:
            resp = client.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an assistant that estimates repair fix times for campus maintenance issues. Provide a JSON response only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=300,
            )
            text = resp['choices'][0]['message']['content'].strip()
            print(text)
            parsed = try_extract_json(text)
            if parsed:
                return jsonify(parsed)
            else:
                return jsonify({"raw": text})
        except Exception as e:
            return jsonify({"error": "LLM call failed", "exception": str(e)}), 500
    else:
        estimated_days, confidence = heuristic_estimate(severity)
        estimated_fix_iso = (datetime.utcnow() + timedelta(days=estimated_days)).isoformat()
        rationale = f"Fallback heuristic: severity='{severity}' => {estimated_days} days"
        return jsonify({
            "estimated_days": estimated_days,
            "estimated_fix_iso": estimated_fix_iso,
            "confidence": confidence,
            "rationale": rationale
        })


# --- Helper functions ---

def build_prompt(title, description, location, severity):
    now_iso = datetime.utcnow().isoformat()
    prompt = (
        f"Issue title: {title}\nDescription: {description}\nLocation: {location}\nSeverity: {severity}\nCurrent UTC: {now_iso}\n\n"
        "Estimate how many days it will take to fix this problem and probable date/time (ISO 8601). Return JSON: {estimated_days, estimated_fix_iso, confidence, rationale}."
    )
    return prompt


def try_extract_json(text):
    try:
        if text.strip().startswith('{'):
            return json.loads(text)
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
    except Exception:
        return None


def heuristic_estimate(sev):
    sev = sev.lower()
    if sev in ('critical', 'high'): return 1, 0.7
    if sev in ('medium', 'normal'): return 3, 0.6
    if sev in ('low', 'minor'): return 7, 0.5
    return 4, 0.5

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
