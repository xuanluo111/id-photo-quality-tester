"""
基于 OpenCV QualityBRISQUE 的无参考图像质量评估。
在 L 通道上计算，输出 [0, 1] 分数（越大表示主观质量越好）。
"""
from __future__ import annotations

import os
from typing import Union

import cv2

# OpenCV 官方示例使用的 BRISQUE 模型文件名（需与 backend/models 中文件一致）
_BRISQUE_MODEL_FILENAME = "brisque_model_live.yml"
_BRISQUE_RANGE_FILENAME = "brisque_range_live.yml"


class BRISQUEQualityEvaluator:
    """封装 QualityBRISQUE：构造期校验路径并创建引擎；evaluate 内完成读图、预处理与归一化。"""

    def __init__(self, model_dir: Union[str, os.PathLike] = "models") -> None:
        resolved_dir = os.path.abspath(os.path.expanduser(os.fspath(model_dir)))
        model_path = os.path.join(resolved_dir, _BRISQUE_MODEL_FILENAME)
        range_path = os.path.join(resolved_dir, _BRISQUE_RANGE_FILENAME)

        if not os.path.isdir(resolved_dir):
            raise FileNotFoundError(f"模型目录不存在: {resolved_dir}")
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"BRISQUE 模型文件缺失: {model_path}")
        if not os.path.isfile(range_path):
            raise FileNotFoundError(f"BRISQUE range 文件缺失: {range_path}")

        try:
            self.brisque = cv2.quality.QualityBRISQUE.create(model_path, range_path)
        except cv2.error as exc:
            raise RuntimeError(
                "无法初始化 BRISQUE（请检查模型是否与当前 OpenCV 版本兼容）: "
                f"{model_path}"
            ) from exc

    def evaluate(self, image_path: Union[str, os.PathLike]) -> float:
        path = os.fspath(image_path)
        if not path or not path.strip():
            raise ValueError("图像路径为空")
        if not os.path.isfile(path):
            raise FileNotFoundError(f"图像文件不存在或不是文件: {path}")

        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"无法解码图像（格式损坏或不受支持）: {path}")
        if img.ndim != 3 or img.shape[2] != 3:
            raise ValueError(
                f"需要 BGR 三通道图像，当前 shape={img.shape}: {path}"
            )

        # LAB 的 L 通道近似亮度，再扩成伪 BGR 以满足 BRISQUE 三通道输入
        try:
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l_channel = lab[:, :, 0]
            gray3 = cv2.cvtColor(l_channel, cv2.COLOR_GRAY2BGR)
            raw_scalar = self.brisque.compute(gray3)
        except cv2.error as exc:
            raise RuntimeError(f"BRISQUE 预处理或计算失败: {path}") from exc

        raw_score = float(raw_scalar[0])
        # 原始分通常落在 [0,100] 附近；裁剪后映射为越大越好的 [0,1]
        clipped = max(0.0, min(100.0, raw_score))
        return 1.0 - clipped / 100.0
