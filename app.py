from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy(app)

# ===== モデル定義 =====
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    articles = db.relationship('Article', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='commenter', lazy=True)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    article = db.relationship('Article', backref='comments', lazy=True)

# ===== ログイン設定 =====
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===== ルーティング =====
@app.route('/')
def index():
    articles = Article.query.order_by(Article.date_posted.desc()).all()
    return render_template('index.html', articles=articles)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        user = User(username=request.form['username'], email=request.form['email'], password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('登録完了！ログインしてください。')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('ログイン失敗')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    if request.method == 'POST':
        article = Article(title=request.form['title'], body=request.form['body'], user_id=current_user.id)
        db.session.add(article)
        db.session.commit()
        flash('記事を投稿しました！')
        return redirect(url_for('index'))
    return render_template('edit.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    article = Article.query.get_or_404(id)
    if article.author != current_user:
        flash('自分の記事のみ編集可能です。')
        return redirect(url_for('index'))
    if request.method == 'POST':
        article.title = request.form['title']
        article.body = request.form['body']
        db.session.commit()
        flash('記事を更新しました！')
        return redirect(url_for('article', id=article.id))
    return render_template('edit.html', article=article)

@app.route('/article/<int:id>', methods=['GET', 'POST'])
def article(id):
    article = Article.query.get_or_404(id)
    comments = Comment.query.filter_by(article_id=id).order_by(Comment.date_posted.asc()).all()
    if request.method == 'POST' and current_user.is_authenticated:
        comment = Comment(body=request.form['body'], user_id=current_user.id, article_id=id)
        db.session.add(comment)
        db.session.commit()
        flash('コメントを投稿しました！')
        return redirect(url_for('article', id=id))
    return render_template('article.html', article=article, comments=comments)
@app.route('/comments')
def comments():
    all_comments = Comment.query.order_by(Comment.date_posted.desc()).all()
    return render_template('comments.html', comments=all_comments)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
