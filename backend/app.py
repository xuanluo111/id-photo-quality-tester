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
from ai_evaluator.evaluator import AIResponseEvaluator

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


@app.route("/api/evaluate-llm", methods=["POST"])
def evaluate_llm():
    """评估大模型回答质量的API"""
    try:
        data = request.get_json() or {}
        run_times = data.get('run_times', 1)

        evaluator = AIResponseEvaluator()
        report = evaluator.run_full_evaluation(run_times=run_times)

        # 检查 report 是否有效
        if report is None:
            return jsonify({
                "success": False,
                "error": "评估失败，返回结果为空"
            }), 500

        if "error" in report:
            return jsonify({
                "success": False,
                "error": report["error"]
            }), 500

        return jsonify({
            "success": True,
            "report": report,
            "message": f"评估完成。综合得分: {report['summary']['avg_final_score']}/10"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/evaluate-llm/single", methods=["POST"])
def evaluate_llm_single():
    """评估单个问题的API"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请求体不能为空"}), 400

        question = data.get('question')
        if not question:
            return jsonify({"success": False, "error": "缺少 question 参数"}), 400

        # 创建评估器
        evaluator = AIResponseEvaluator()

        # 直接调用模型获取回答
        answer = evaluator.call_target_model(question)

        return jsonify({
            "success": True,
            "question": question,
            "answer": answer,
            "model": "deepseek-chat",
            "note": "如需完整评估（与标准答案对比），请使用 /api/evaluate-llm 接口"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/evaluate-llm/compare", methods=["POST"])
def evaluate_llm_compare():
    """对比两个模型的回答质量"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请求体不能为空"}), 400

        question = data.get('question')
        if not question:
            return jsonify({"success": False, "error": "缺少 question 参数"}), 400

        # 评估 DeepSeek（注意：参数名是 target_model，不是 taget_model）
        evaluator = AIResponseEvaluator(target_model="deepseek-chat")
        deepseek_answer = evaluator.call_target_model(question)

        # 可以在这里添加其他模型的对比
        # 例如：通义千问、文心一言等

        return jsonify({
            "success": True,
            "question": question,
            "models": {
                "deepseek-chat": {
                    "answer": deepseek_answer,
                    "model_name": "DeepSeek Chat",
                    "note": "如需完整质量评分，请使用 /api/evaluate-llm 接口"
                }
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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
