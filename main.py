from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from PIL import Image
from moviepy.editor import VideoFileClip

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
LETTERS_DIR = 'letters'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp3', 'mp4', 'avi'}

os.makedirs(LETTERS_DIR, exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file, filepath):
    image = Image.open(file)
    image.thumbnail((800, 800))  # Resize image to max 800x800
    image.save(filepath, optimize=True, quality=85)

def compress_video(file, filepath):
    clip = VideoFileClip(file)
    clip_resized = clip.resize(newsize=(640, 360))  # Resize video to 640x360
    clip_resized.write_videofile(filepath, bitrate="500k")  # Compress to 500k bitrate

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/write', methods=['GET', 'POST'])
def write_letter():
    if request.method == 'POST':
        sender = request.form['sender']
        content = request.form['content']
        filename = os.path.join(LETTERS_DIR, f'{sender}.txt')
        with open(filename, 'w') as f:
            f.write(content)

        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'{sender}_{file.filename}')
                if file.filename.split('.')[-1] in ['png', 'jpg', 'jpeg', 'gif']:
                    save_image(file, filepath)
                elif file.filename.split('.')[-1] in ['mp4', 'avi']:
                    compress_video(file, filepath)
                else:
                    file.save(filepath)  # Save audio files directly

        return redirect(url_for('index'))
    return render_template('letter.html')

@app.route('/read', methods=['POST'])
def read_letter():
    sender = request.form['sender']
    return redirect(url_for('display_letter', sender=sender))

@app.route('/letter/<sender>')
def display_letter(sender):
    filename = os.path.join(LETTERS_DIR, f'{sender}.txt')
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            content = f.read()
        files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(sender)]
        return render_template('letter.html', content=content, sender=sender, files=files)
    return "No letter found."

@app.route('/download_letter/<sender>')
def download_letter(sender):
    filename = f'{sender}.txt'
    return send_from_directory(LETTERS_DIR, filename, as_attachment=True)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/delete/<sender>')
def delete_letter(sender):
    filename = os.path.join(LETTERS_DIR, f'{sender}.txt')
    if os.path.exists(filename):
        os.remove(filename)

    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(sender)]
    for file in files:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81)
