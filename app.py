from flask import Flask, request, render_template, jsonify
from YoutubeTags import videotags
import random

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_tags', methods=['POST'])
def get_tags():
    youtube_link = request.form['youtube_link']
    tags = videotags(youtube_link).split(',')
    tags = [tag.strip() for tag in tags]  # Remove extra whitespace
    return render_template('index.html', tags=tags)

@app.route('/shuffle_tags', methods=['POST'])
def shuffle_tags():
    tags = request.json.get('tags')
    random.shuffle(tags)
    return jsonify(tags)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

