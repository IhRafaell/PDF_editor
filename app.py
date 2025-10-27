import os
import uuid 
from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify
from pypdf import PdfWriter
from PIL import Image

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def merge_pdfs(file_paths, output_file_path):
    """Merge multiple PDF files."""
    merger = PdfWriter()
    for path in file_paths:
        merger.append(path)
    merger.write(output_file_path)
    merger.close()

def convert_images_to_pdf(image_paths, output_file_path):
    """Convert images to PDF."""
    pil_images = []
    for path in image_paths:
        try:
            pil_images.append(Image.open(path).convert('RGB'))
        except Exception as e:
            print(f"Error processing image {path}: {e}")
            
    if not pil_images:
        raise ValueError("No valid images found for conversion.")

    pil_images[0].save(
        output_file_path,
        save_all=True,
        append_images=pil_images[1:]
    )

@app.route('/')
def index():
    return render_template('index.html', pdf_url='')

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(filepath) and filename.endswith('.pdf'):
        return send_file(filepath, mimetype='application/pdf')
    
    return "File not found.", 404

@app.route('/process', methods=['POST'])
def process():
    """Receive files, process them, and return the name of the generated PDF."""
    
    action = request.form.get('action')
    uploaded_files = request.files.getlist('files')
    
    if not uploaded_files or not action:
        return jsonify({'error': 'No files or action selected.'}), 400

    upload_paths = []
    unique_output_name = f'{uuid.uuid4()}.pdf'
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_output_name)

    try:
        for f in uploaded_files:
            if f and f.filename:
                upload_name = f"{uuid.uuid4()}_{f.filename}"
                saved_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_name)
                f.save(saved_path)
                upload_paths.append(saved_path)
        
        if not upload_paths:
             return jsonify({'error': 'No valid files uploaded.'}), 400

        if action == 'merge_pdfs':
            merge_pdfs(upload_paths, output_path)
        elif action == 'convert_images':
            convert_images_to_pdf(upload_paths, output_path)
        else:
            return jsonify({'error': 'Invalid action.'}), 400
        
        return jsonify({'filename': unique_output_name})

    except Exception as e:
        return jsonify({'error': f'An error occurred during processing: {str(e)}'}), 500
    
    finally:
        # Clean up temporary files
        for path in upload_paths:
            if os.path.exists(path):
                os.remove(path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
