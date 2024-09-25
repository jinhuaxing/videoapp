from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import ffmpeg
import subprocess
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'
app.config['UPLOAD_FOLDER'] = 'static/videos'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov'}
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 添加点赞关联表
likes = db.Table('likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('video_id', db.Integer, db.ForeignKey('video.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    videos = db.relationship('Video', backref='user', lazy=True)
    liked_videos = db.relationship('Video', secondary=likes, backref=db.backref('liked_by', lazy='dynamic'))

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creation_time = db.Column(db.String(120), nullable=True)
    is_public = db.Column(db.Boolean, default=True)

with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # 清除闪现消息
        session.pop('_flashes', None)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('video_list'))
        else:
            flash('登录失败。请检查您的用户名和密码,或者注册一个新账号。')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        # 清除闪现消息
        session.pop('_flashes', None)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在,请选择其他用户名。')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功!请登录。')
            return redirect(url_for('login'))
    return render_template('register.html')

def get_video_duration(video_path):
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['streams'][0]['duration'])
        return f"{int(duration // 60)}:{int(duration % 60):02d}"
    except Exception as e:
        print(f"Error getting duration for {video_path}: {str(e)}")
        return "未知"

def generate_thumbnail(video_path, output_path):
    try:
        subprocess.run(['ffmpeg', '-i', video_path, '-ss', '00:00:01', '-vframes', '1', output_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating thumbnail for {video_path}: {str(e)}")
        return False

@app.route('/video_list')
@login_required
def video_list():
    user_id = session['user_id']
    user = User.query.get(user_id)
    video_folder = 'static/videos'
    thumbnail_folder = 'static/thumbnails'
    if not os.path.exists(thumbnail_folder):
        os.makedirs(thumbnail_folder)
    
    user_videos = []
    public_videos = []
    
    for video in Video.query.all():
        video_path = os.path.join(video_folder, video.filename)
        thumbnail_path = os.path.join(thumbnail_folder, f"{os.path.splitext(video.filename)[0]}.jpg")
        
        if not os.path.exists(thumbnail_path):
            generate_thumbnail(video_path, thumbnail_path)
        
        duration = get_video_duration(video_path)
        video_info = {
            'id': video.id,
            'name': video.filename,
            'duration': duration,
            'thumbnail': os.path.relpath(thumbnail_path, 'static'),
            'creation_time': video.creation_time,
            'is_public': video.is_public,
            'user': video.user.username,
            'likes_count': video.liked_by.count(),
            'is_liked': user in video.liked_by
        }
        
        if video.user_id == user_id:
            user_videos.append(video_info)
        elif video.is_public:
            public_videos.append(video_info)
    
    return render_template('video_list.html', user_videos=user_videos, public_videos=public_videos)

@app.route('/play_video/<video_name>')
@login_required
def play_video(video_name):
    video = Video.query.filter_by(filename=video_name).first()
    user = User.query.get(session['user_id'])
    if video and (video.user_id == session['user_id'] or video.is_public):
        return render_template('play_video.html', video=video, is_liked=user in video.liked_by)
    else:
        flash('您没有权限播放此视频')
        return redirect(url_for('video_list'))

@app.route('/like_video/<int:video_id>', methods=['POST'])
@login_required
def like_video(video_id):
    video = Video.query.get(video_id)
    user = User.query.get(session['user_id'])
    if video and (video.is_public or video.user_id == user.id):
        if user in video.liked_by:
            video.liked_by.remove(user)
            db.session.commit()
            return jsonify({'status': 'success', 'action': 'unliked', 'likes_count': video.liked_by.count()})
        else:
            video.liked_by.append(user)
            db.session.commit()
            return jsonify({'status': 'success', 'action': 'liked', 'likes_count': video.liked_by.count()})
    return jsonify({'status': 'error', 'message': '无法点赞此视频'})

@app.route('/upload_video', methods=['GET', 'POST'])
@login_required
def upload_video():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有文件部分')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            user_id = session['user_id']
            
            # 读取视频的拍摄时间
            try:
                probe = ffmpeg.probe(file_path)
                creation_time = probe['format']['tags'].get('creation_time', '未知')
            except Exception as e:
                print(f"Error getting creation time for {file_path}: {str(e)}")
                creation_time = '未知'
            
            is_public = request.form.get('is_public') == 'on'
            new_video = Video(filename=filename, user_id=user_id, creation_time=creation_time, is_public=is_public)
            db.session.add(new_video)
            db.session.commit()
            flash('文件上传成功')
    return render_template('upload_video.html')

@app.route('/delete_video/<int:video_id>', methods=['POST'])
@login_required
def delete_video(video_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    video = Video.query.get(video_id)
    if video and video.user_id == session['user_id']:
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
        thumbnail_path = os.path.join('static/thumbnails', f"{os.path.splitext(video.filename)[0]}.jpg")
        
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
        
        db.session.delete(video)
        db.session.commit()
        flash('视频删除成功')
    else:
        flash('无法删除视频')
    
    return redirect(url_for('video_list'))

@app.route('/debug/users')
def debug_users():
    users = User.query.all()
    return render_template('debug_users.html', users=users)

@app.route('/debug/videos')
def debug_videos():
    videos = Video.query.all()
    return render_template('debug_videos.html', videos=videos)

@app.route('/toggle_visibility/<int:video_id>', methods=['POST'])
@login_required
def toggle_visibility(video_id):
    video = Video.query.get(video_id)
    if video and video.user_id == session['user_id']:
        video.is_public = not video.is_public
        db.session.commit()
        return jsonify({
            'status': 'success',
            'is_public': video.is_public
        })
    else:
        return jsonify({
            'status': 'error',
            'message': '您没有权限更改此视频的可见性'
        })

if __name__ == '__main__':
    app.run(debug=True)