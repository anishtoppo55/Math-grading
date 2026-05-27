from flask import Flask, request, jsonify, send_from_directory, render_template
import os
import sys
import json
import logging
import uuid

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from run_all import run_all as run_full_pipeline

app = Flask(__name__, static_folder='static', template_folder='static')
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logger = logging.getLogger("FrontendApp")
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/process', methods=['POST'])
def process():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(filepath)
    
    try:
        logger.info(f"Running full pipeline on {filepath}")
        
        # Change current working directory to PROJECT_ROOT
        original_cwd = os.getcwd()
        os.chdir(PROJECT_ROOT)
        
        # run_all returns the combined dictionary
        combined_result = run_full_pipeline(filepath)
        
        # Restore cwd
        os.chdir(original_cwd)
        
        return jsonify({
            'success': True,
            'image_url': f'/uploads/{unique_filename}',
            'result': combined_result
        })
    except Exception as e:
        logger.error(f"Pipeline Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
