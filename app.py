import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from config import Config
from models import db, Issue
from datetime import datetime

def allowed_file(filename, allowed):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    @app.before_request
    def create_tables():
        db.create_all()

    @app.route("/")
    def index():
        categories = ["Electrical", "Plumbing", "Carpentry", "Cleaning", "IT", "Other"]
        urgencies = ["Low", "Normal", "High", "Critical"]
        return render_template("index.html", categories=categories, urgencies=urgencies)

    @app.route("/submit", methods=["POST"])
    def submit_issue():
        title = request.form.get("title", "").strip()
        location = request.form.get("location", "").strip()
        category = request.form.get("category", "Other")
        urgency = request.form.get("urgency", "Normal")
        description = request.form.get("description", "").strip()
        contact = request.form.get("contact", "").strip()

        if not title or not location or not description:
            flash("Please fill title, location and description.", "danger")
            return redirect(url_for("index"))

        image_filename = None
        if "image" in request.files:
            f = request.files["image"]
            if f and f.filename and allowed_file(f.filename, app.config["ALLOWED_EXTENSIONS"]):
                filename = secure_filename(f.filename)
                # make filename unique
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
                filename = f"{timestamp}_{filename}"
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                f.save(save_path)
                image_filename = filename

        issue = Issue(
            title=title,
            location=location,
            category=category,
            urgency=urgency,
            description=description,
            contact=contact,
            image_filename=image_filename,
            status="Reported"
        )
        issue.add_history("Reporter", "Reported", f"Urgency:{urgency}")
        db.session.add(issue)
        db.session.commit()
        flash("Issue reported successfully. Thank you!", "success")
        return redirect(url_for("index"))

    @app.route("/issues")
    def issues_list():
        # filter params
        status = request.args.get("status")
        category = request.args.get("category")
        q = request.args.get("q")
        issues = Issue.query.order_by(Issue.created_at.desc())
        if status:
            issues = issues.filter_by(status=status)
        if category:
            issues = issues.filter_by(category=category)
        if q:
            q_like = f"%{q}%"
            issues = issues.filter((Issue.title.ilike(q_like)) | (Issue.description.ilike(q_like)) | (Issue.location.ilike(q_like)))
        issues = issues.all()
        categories = sorted(list({i.category for i in Issue.query.all()})) or ["Electrical","Plumbing","Carpentry","Cleaning","IT","Other"]
        return render_template("issues.html", issues=issues, categories=categories)

    @app.route("/issue/<int:issue_id>")
    def issue_detail(issue_id):
        issue = Issue.query.get_or_404(issue_id)
        history_lines = issue.history.splitlines() if issue.history else []
        return render_template("issue_detail.html", issue=issue, history_lines=history_lines)

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Admin endpoints (very simple auth could be added later)
    @app.route("/admin")
    def admin():
        issues = Issue.query.order_by(Issue.updated_at.desc()).all()
        stats = {
            "total": Issue.query.count(),
            "reported": Issue.query.filter_by(status="Reported").count(),
            "in_progress": Issue.query.filter_by(status="In Progress").count(),
            "resolved": Issue.query.filter_by(status="Resolved").count(),
        }
        return render_template("admin.html", issues=issues, stats=stats)

    @app.route("/admin/update_status", methods=["POST"])
    def admin_update_status():
        data = request.json
        issue_id = data.get("id")
        new_status = data.get("status")
        actor = data.get("actor", "Admin")
        note = data.get("note", "")

        issue = Issue.query.get(issue_id)
        if not issue:
            return jsonify({"ok": False, "error": "Issue not found"}), 404

        old = issue.status
        issue.status = new_status
        issue.add_history(actor, f"Status changed {old} -> {new_status}", note)
        db.session.commit()
        return jsonify({"ok": True, "new_status": new_status, "updated_at": issue.updated_at.isoformat()})

    @app.route("/admin/comment", methods=["POST"])
    def admin_comment():
        issue_id = request.form.get("id")
        actor = request.form.get("actor", "Admin")
        comment = request.form.get("comment", "")
        issue = Issue.query.get(issue_id)
        if not issue:
            flash("Issue not found", "danger")
            return redirect(url_for("admin"))
        issue.add_history(actor, "Comment", comment)
        db.session.commit()
        flash("Comment added", "success")
        return redirect(url_for("issue_detail", issue_id=issue.id))

    # Simple API to fetch issue status (used by JS)
    @app.route("/api/issue_status/<int:issue_id>")
    def api_issue_status(issue_id):
        issue = Issue.query.get_or_404(issue_id)
        return jsonify({"id": issue.id, "status": issue.status, "updated_at": issue.updated_at.isoformat()})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
