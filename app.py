from datetime import timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    'sqlite:///blog.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = (
    'super-maxfiy-kalit-soz'
)
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db = SQLAlchemy(app)
jwt = JWTManager(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False
    )
    comments = db.relationship(
        'Comment', backref='post', lazy=True, cascade='all, delete-orphan'
    )


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False
    )





@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username va parol kiritilishi shart'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Bu foydalanuvchi allaqachon mavjud'}), 400

    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': "Muvaffaqiyatli ro'yxatdan o'tdingiz!"}), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(
        username=data.get('username'), password=data.get('password')
    ).first()
    if not user:
        return jsonify({'error': 'Login yoki parol xato'}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({'access_token': access_token}), 200


@app.route('/api/posts', methods=['GET'])
def get_posts():
    posts = Post.query.all()
    result = []
    for post in posts:
        result.append({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author_id': post.author_id,
        })
    return jsonify(result), 200


@app.route('/api/posts', methods=['POST'])
@jwt_required()
def create_post():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Sarlavha va matn kiritilishi shart'}), 400

    new_post = Post(
        title=data['title'],
        content=data['content'],
        author_id=int(current_user_id),
    )
    db.session.add(new_post)
    db.session.commit()

    return jsonify({'message': "Post muvaffaqiyatli qo'shildi", 'id': new_post.id}), 201


@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    comments = [
        {'id': c.id, 'content': c.content, 'author_id': c.author_id}
        for c in post.comments
    ]
    return (
        jsonify({
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author_id': post.author_id,
            'comments': comments,
        }),
        200,
    )


@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('content'):
        return jsonify({'error': 'Izoh matni bo\'sh bo\'lishi mumkin emas'}), 400

    new_comment = Comment(
        content=data['content'],
        post_id=post.id,
        author_id=int(current_user_id),
    )
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({'message': "Izoh muvaffaqiyatli qo'shildi"}), 201


if __name__ == '__main__':
    app.run(debug=True)
