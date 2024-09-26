这是一个主要由AI编程助理[Cursor](https://www.cursor.com/)完成的项目，包括这个README文件。我大概用了一天的时间，而且我没有使用flask的经验，还有很多时间是花在CSS。
AI辅助助理很快将成为程序员的标配，没有AI助理，就像使用汇编语言开发程序。

# 视频分享平台

这是一个基于Flask的视频分享平台，允许用户上传、观看和管理视频。

## 功能特点

- 用户注册和登录
- 视频上传和删除
- 视频播放
- 公开/私密视频设置
- 视频点赞功能
- 视频缩略图生成
- 响应式设计

## 技术栈

- Python 3.x
- Flask
- SQLAlchemy
- FFmpeg
- HTML/CSS/JavaScript

## 安装

1. 克隆仓库：
   ```
   git clone https://github.com/jinhuaxing/videoapp.git
   cd videoapp
   ```

2. 创建虚拟环境并激活：
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

4. 确保已安装FFmpeg并添加到系统PATH中。

## 配置

1. 在 `app.py` 中设置 `SECRET_KEY` 和其他配置选项。
2. 确保 `static/videos` 和 `static/thumbnails` 目录存在并可写。

## 运行
```
flask run
```

访问 `http://localhost:5000` 来使用应用。

## 项目结构

- `app.py`: 主应用文件
- `templates/`: HTML模板
- `static/`: 静态文件（CSS、JavaScript、上传的视频和缩略图）
- `requirements.txt`: 项目依赖



## 许可

[MIT License](https://opensource.org/licenses/MIT)
