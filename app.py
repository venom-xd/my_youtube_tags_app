from flask import Flask, request, render_template, jsonify, send_file, url_for
import random
import logging
from logging.handlers import RotatingFileHandler
import io
import tempfile
import os
import urllib.parse
from pypdf import PdfReader, PdfWriter
from flask import Flask, request, render_template, jsonify, send_file, url_for
import random
import logging
from logging.handlers import RotatingFileHandler
import aspose.pdf as ap
import io
import tempfile
import os
from YoutubeTags import videotags
import base64 

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


@app.route('/compress', methods=['GET', 'POST'])
def compress_pdf():
    if request.method == 'POST':
        if 'pdf' not in request.files:
            return "No file part"

        file = request.files['pdf']

        if file.filename == '':
            return "No selected file"

        if file and file.filename.lower().endswith('.pdf'):
            input_pdf = file.read()
            compression_mode = request.form.get('compression', 'medium')

            # Get input PDF size
            input_size_kb = len(input_pdf) / 1024

            # Compress the PDF
            compressed_pdf, output_filename = compress_pdf_bytes(input_pdf, compression_mode)

            # Get output PDF size
            output_size_kb = len(compressed_pdf) / 1024
            compressed_kb = input_size_kb - output_size_kb

            # Create a temporary file for the compressed PDF
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file.write(compressed_pdf)
            temp_file.flush()  # Ensure all data is written to the file
            temp_file.close()

            # URL encode the filename to handle spaces
            file_url = url_for('download_file', filename=urllib.parse.quote(os.path.basename(temp_file.name)))

            return render_template(
                'result.html',
                file_url=file_url,
                input_size=f"{input_size_kb:.2f} KB",
                output_size=f"{output_size_kb:.2f} KB",
                compressed_size=f"{compressed_kb:.2f} KB"
            )

        return "Invalid file type"

    return render_template('pdfcompressor.html')

@app.route('/download/<filename>')
def download_file(filename):
    # Decode the filename from URL encoding
    filename = urllib.parse.unquote(filename)
    return send_file(os.path.join(tempfile.gettempdir(), filename), as_attachment=True, download_name=filename, mimetype='application/pdf')

@app.route('/merge', methods=['GET', 'POST'])
def merge_pdfs():
    if request.method == 'POST':
        files = request.files.getlist('pdf_files')

        if not files or len(files) < 2:
            return jsonify(success=False, message="Please upload at least two PDF files.")

        merger = PdfWriter()

        for file in files:
            pdf_reader = PdfReader(file)
            merger.append(pdf_reader)

        # Create a temporary file for the merged PDF
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        merger.write(temp_file)
        temp_file.flush()
        temp_file.close()

        file_url = url_for('download_file', filename=urllib.parse.quote(os.path.basename(temp_file.name)))

        return jsonify(success=True, file_url=file_url)

    return render_template('pdfmerger.html')

@app.route('/extract_images', methods=['GET', 'POST'])
def extract_images():
    if request.method == 'POST':
        if 'pdf' not in request.files:
            return "No file part"

        file = request.files['pdf']

        if file.filename == '':
            return "No selected file"

        if file and file.filename.lower().endswith('.pdf'):
            input_pdf = file.read()

            images = extract_images_from_pdf(input_pdf)

            return jsonify(images=images)

        return "Invalid file type"

    return render_template('pdfimageextractor.html')


    return render_template('pdfimageextractor.html')

def compress_pdf_bytes(pdf_bytes, compression_mode):
    """Compress PDF using PyPDF based on compression mode"""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()

        # Remove duplication
        for page in reader.pages:
            writer.add_page(page)

        # Apply image compression and content stream compression
        for page in writer.pages:
            # Image compression
            for img in page.images:
                if compression_mode == 'low':
                    img.replace(img.image, quality=30)
                elif compression_mode == 'medium':
                    img.replace(img.image, quality=5)
                elif compression_mode == 'high':
                    img.replace(img.image, quality=1)
                else:
                    img.replace(img.image, quality=50)  # Default to medium

            # Content stream compression
            if compression_mode == 'low':
                page.compress_content_streams(level=1)
            elif compression_mode == 'medium':
                page.compress_content_streams(level=6)
            elif compression_mode == 'high':
                page.compress_content_streams(level=9)
            else:
                page.compress_content_streams(level=6)  # Default to medium

        # Save to a byte stream
        output_stream = io.BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)

        # Create output filename with prefix
        output_filename = f"{compression_mode}_compressed.pdf"

        return output_stream.getvalue(), output_filename
    except Exception as e:
        app.logger.error(f"Error compressing PDF: {e}")
        return b"", "compressed.pdf"

def extract_images_from_pdf(pdf_bytes):
    """Extract images from a PDF using PyPDF"""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        images = []

        for page in reader.pages:
            for count, image_file_object in enumerate(page.images):
                image_data = image_file_object.data
                image_extension = image_file_object.name.split('.')[-1]

                encoded_image = base64.b64encode(image_data).decode('utf-8')
                images.append({
                    'data': encoded_image,
                    'extension': image_extension
                })

        return images
    except Exception as e:
        app.logger.error(f"Error extracting images from PDF: {e}")
        return []

if __name__ == '__main__':
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(host='0.0.0.0', port=5000, debug=True)
