from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os, uuid
from brisque_evaluator import BRISQUEQualityEvaluator

app = Flask(__name__)

# 作用：启用跨域资源共享（Cross-Origin Resource Sharing）
CORS(app)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'models')

evaluator = BRISQUEQualityEvaluator(model_dir=MODEL_DIR)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # 获取文件扩展名
    ext = file.filename.split('.', 1)[-1].lower() if '.' in file.filename else ''
    filename = secure_filename(file.filename)
    # 如果 safe_name 为空，可以自己生成一个
    if not filename or filename.split('.')[0] == '':
        filename = f"file_{uuid.uuid4().hex}.{ext}" if ext else f"file_{uuid.uuid4().hex}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        score = evaluator.evaluate(filepath)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # 评估完成后删除临时文件
        if os.path.exists(filepath):
            os.remove(filepath)

    # 简单规则：分数 >0.7为高质量，<=0.7为低质量
    quality = "good" if score > 0.7 else "bad"
    return jsonify({
        'filename': filename,
        'brisque_score': round(score, 2),
        'quality': quality
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)