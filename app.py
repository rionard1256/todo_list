from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, nulls_last
from datetime import datetime
import os

app = Flask(__name__)

db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

if not db_url:
    raise RuntimeError("❌ DATABASE_URL is not set. Aborting to avoid using SQLite.")

app.config['SQLALCHEMY_DATABASE_URI'] = db_url #Flaskに対して,使用するdbのurlを設定

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  #変更追跡機能をオフにして無駄なメモリ使用を防ぐ（推奨設定）
db = SQLAlchemy(app)  #SQLAlchemyにFlaskアプリを紐付ける

# モデル定義
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    subtasks = db.relationship('SubTask', backref='parent', cascade='all, delete', lazy=True)

class SubTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.Date, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)

# DB初期化
with app.app_context():
    db.create_all()

# ルート
@app.route('/')
def index():
    tasks = Task.query.order_by(nulls_last(asc(Task.deadline))).all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        content = request.form.get('task')
        deadline_str = request.form.get('deadline')
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None
        if content:
            db.session.add(Task(content=content, deadline=deadline))
            db.session.commit()
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/add_subtask/<int:task_id>', methods=['POST'])
def add_subtask(task_id):
    content = request.form.get('subtask')
    deadline_str = request.form.get('subtask_deadline')
    deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None
    if content:
        db.session.add(SubTask(content=content, deadline=deadline, parent_id=task_id))
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete(task_id):
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_subtask/<int:subtask_id>')
def delete_subtask(subtask_id):
    subtask = SubTask.query.get(subtask_id)
    if subtask:
        db.session.delete(subtask)
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
