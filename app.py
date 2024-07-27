from flask import Flask, request, render_template, jsonify
from YoutubeTags import videotags
import random
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/youtubetagextract', methods=['GET', 'POST'])
def youtube_tag_extract():
    if request.method == 'POST':
        youtube_link = request.form['youtube_link']
        tags = videotags(youtube_link).split(',')
        tags = [tag.strip() for tag in tags]  # Remove extra whitespace
        return render_template('extractor.html', tags=tags)
    return render_template('extractor.html')

@app.route('/shuffle_tags', methods=['POST'])
def shuffle_tags():
    tags = request.json.get('tags')
    random.shuffle(tags)
    return jsonify(tags)

if __name__ == '__main__':
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(host='0.0.0.0', port=5000, debug=True)
