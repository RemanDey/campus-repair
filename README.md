# 🏫 Campus Repair Management System

A simple **Flask + HTML + CSS + JavaScript** web application for managing and tracking repair issues in a campus environment.  
Students, staff, or residents can report problems (like electrical, plumbing, cleaning, IT issues, etc.), and administrators can view, update, and resolve them through an admin dashboard.

---

## 🚀 Features

- 📝 **Report an Issue**
  - Title, location, category, urgency, description
  - Optional contact info and image upload

- 📋 **View All Issues**
  - Public list of all reported issues
  - Filter by category, status, or search text

- 🛠️ **Admin Dashboard**
  - View all issues with quick status updates
  - Add comments or notes to issues
  - Automatically logs history of status changes

- 🖼️ **Attachments**
  - Optional photo uploads stored in `static/uploads/`

- ⚡ **Lightweight & Self-contained**
  - Uses SQLite database
  - No external dependencies or setup needed

---

## 🧩 Tech Stack

| Layer | Technology |
|-------|-------------|
| Backend | Flask (Python) |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite via Flask-SQLAlchemy |
| Styling | Vanilla CSS (responsive) |
| File Uploads | Werkzeug secure upload |
| Templates | Jinja2 templating engine |

---

## 📂 Project Structure

campus-repair/
├── app.py
├── config.py
├── models.py
├── requirements.txt
├── README.md
├── templates/
│ ├── base.html
│ ├── index.html
│ ├── issues.html
│ ├── issue_detail.html
│ └── admin.html
└── static/
├── css/
│ └── style.css
├── js/
│ └── main.js
└── uploads/


---

## ⚙️ Installation & Setup

### 1. Run all these:
```bash
git clone https://github.com/RemanDey/campus-repair.git
cd campus-repair
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
python app.py
