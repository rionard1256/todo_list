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

app.config['SQLALCHEMY_DATABASE_URI'] = db_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  #変更追跡機能をオフにして無駄なメモリ使用を防ぐ（推奨設定）
db = SQLAlchemy(app)  #SQLAlchemyにFlaskアプリを紐付ける

# データベースモデル
class Task(db.Model):  #Task テーブルを定義（1つのタスクを表す）
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.Date, nullable=True)

# 初期化（最初の実行時だけ）


with app.app_context(): #Flaskアプリの実行コンテキストを一時的に有効化（データベース操作のために必要）
    db.create_all()  #モデルに基づいて tasks.db を初期化（テーブルを作成）

@app.route('/')
def index():
    tasks = Task.query.order_by(nulls_last(asc(Task.deadline))).all()
    return render_template('index.html', tasks=tasks) #index.html を表示し、タスク一覧をテンプレートに渡す

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        task_content = request.form.get('task')  #フォームから送信されたタスクの内容を取得（name="task" の入力欄）
        deadline_str = request.form.get('deadline')
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date() if deadline_str else None
        if task_content:
            new_task = Task(content=task_content, deadline=deadline)  #新しいタスクインスタンスを作成
            db.session.add(new_task)  #データベースに追加を予約（まだ反映されない）
            db.session.commit()  #変更を確定して保存（コミット）
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/delete/<int:task_id>')  #タスク削除用のルート。タスクのIDをURLから受け取る。
def delete(task_id):
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
