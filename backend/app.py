"""
证件照上传与 BRISQUE 质量评估 API。
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Optional, Tuple

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from brisque_evaluator import BRISQUEQualityEvaluator

logger = logging.getLogger(__name__)

app = Flask(__name__)

# 跨域：前端与后端不同端口/域名时浏览器会拦截，需开启 CORS
CORS(app)

# 上传落盘目录；MAX_CONTENT_LENGTH 在解析请求体时生效，超限抛 RequestEntityTooLarge
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
MAX_UPLOAD_BYTES = 16 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
os.makedirs(UPLOAD_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")

# 白名单后缀：先拒绝再解码，减少 OpenCV 无效工作与异常
ALLOWED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png"})
# 业务阈值：与前端「高质量 / 低质量」展示一致
GOOD_QUALITY_THRESHOLD = 0.7


def _init_evaluator() -> Tuple[Optional[BRISQUEQualityEvaluator], Optional[str]]:
    """启动时加载模型；失败返回 (None, 原因)，避免 import 即崩溃。"""
    try:
        return BRISQUEQualityEvaluator(model_dir=MODEL_DIR), None
    except Exception as exc:
        logger.exception("BRISQUE evaluator init failed")
        return None, str(exc)


evaluator, evaluator_init_error = _init_evaluator()


def _cleanup_temp(path: str) -> None:
    """评估结束后删除临时文件；失败仅记录日志。"""
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError as exc:
        logger.warning("Failed to remove temp upload %s: %s", path, exc)


@app.route("/upload", methods=["POST"])
def upload_file():
    if evaluator is None:
        return (
            jsonify(
                {
                    "error": "Evaluator not ready",
                    "detail": evaluator_init_error,
                }
            ),
            500,
        )

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    upload = request.files["file"]
    if not upload.filename:
        return jsonify({"error": "No selected file"}), 400

    _, ext = os.path.splitext(upload.filename)
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return (
            jsonify(
                {
                    "error": "Unsupported file type",
                    "allowed": sorted(ALLOWED_EXTENSIONS),
                }
            ),
            400,
        )

    safe_name = secure_filename(upload.filename) or f"upload{ext}"
    stored_name = f"upload_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)

    try:
        upload.save(filepath)
    except OSError as exc:
        logger.exception("Failed to save upload to %s", filepath)
        return jsonify({"error": "Failed to save file", "detail": str(exc)}), 500

    try:
        score = evaluator.evaluate(filepath)
    except Exception as exc:
        logger.exception("BRISQUE evaluation failed for %s", filepath)
        return jsonify({"error": "Evaluation failed", "detail": str(exc)}), 500
    finally:
        _cleanup_temp(filepath)

    quality = "good" if score > GOOD_QUALITY_THRESHOLD else "bad"
    return jsonify(
        {
            "filename": safe_name,
            "stored_filename": stored_name,
            "brisque_score": round(float(score), 2),
            "quality": quality,
        }
    )


@app.errorhandler(RequestEntityTooLarge)
@app.errorhandler(413)
def _payload_too_large(_e):
    return (
        jsonify(
            {
                "error": "Payload too large",
                "max_bytes": MAX_UPLOAD_BYTES,
            }
        ),
        413,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
