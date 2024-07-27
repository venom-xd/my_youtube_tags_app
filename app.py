from flask import Flask, request, render_template, jsonify, send_file, url_for
import random
import logging
from logging.handlers import RotatingFileHandler
import aspose.pdf as ap
import io
import tempfile
import os
import urllib.parse

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

def compress_pdf_bytes(pdf_bytes, compression_mode):
    """Compress PDF using Aspose.PDF based on compression mode"""
    try:
        pdf_document = ap.Document(io.BytesIO(pdf_bytes))

        # Create an object of OptimizationOptions class
        pdfoptimizeOptions = ap.optimization.OptimizationOptions()

        # Set image compression options based on the selected mode
        if compression_mode == 'low':
            pdfoptimizeOptions.image_compression_options.image_quality = 100
        elif compression_mode == 'medium':
            pdfoptimizeOptions.image_compression_options.image_quality = 50
        elif compression_mode == 'high':
            pdfoptimizeOptions.image_compression_options.image_quality = 20
        else:
            pdfoptimizeOptions.image_compression_options.image_quality = 50  # Default to medium

        # Enable image compression
        pdfoptimizeOptions.image_compression_options.compress_images = True

        # Compress PDF
        pdf_document.optimize_resources(pdfoptimizeOptions)

        # Save to a byte stream
        output_stream = io.BytesIO()
        pdf_document.save(output_stream)
        output_stream.seek(0)

        # Create output filename with prefix
        output_filename = f"{compression_mode}_compressed.pdf"

        return output_stream.getvalue(), output_filename
    except ap.exceptions.AsposeException as e:
        app.logger.error(f"Aspose error during PDF compression: {e}")
    except Exception as e:
        app.logger.error(f"Error compressing PDF bytes: {e}")
    return b"", "compressed.pdf"

if __name__ == '__main__':
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(host='0.0.0.0', port=5000, debug=True)
