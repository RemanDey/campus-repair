from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Issue(db.Model):
    __tablename__ = "issues"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    urgency = db.Column(db.String(20), default="Normal")
    description = db.Column(db.Text, nullable=False)
    contact = db.Column(db.String(100), nullable=True)
    image_filename = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(50), default="Reported")  # Reported / In Progress / Resolved / Closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # simple history as JSON string or text (for extensibility you could add a separate History model)
    history = db.Column(db.Text, default="")  # we'll append simple lines: timestamp|user|action|note

    def add_history(self, actor, action, note=""):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        entry = f"{now} | {actor} | {action} | {note}"
        if self.history:
            self.history += "\n" + entry
        else:
            self.history = entry
        self.updated_at = datetime.utcnow()
