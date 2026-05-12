import os  # 标准库：路径解析与文件是否存在判断
from typing import Union  # 类型注解：构造函数接受 str 或 os.PathLike

import cv2  # OpenCV：读图、色彩空间转换、QualityBRISQUE 无参考质量评估

# BRISQUE 官方配套模型文件名（需与 OpenCV 文档中的命名一致）
_BRISQUE_MODEL_FILENAME = "brisque_model_live.yml"
_BRISQUE_RANGE_FILENAME = "brisque_range_live.yml"


class BRISQUEQualityEvaluator:
    """封装 OpenCV QualityBRISQUE：在 L 通道上评估，输出归一化到 [0,1] 的分数（越大越好）。"""

    def __init__(self, model_dir: Union[str, os.PathLike] = "models") -> None:
        # 将模型目录解析为绝对路径，避免工作目录变化导致找不到文件
        resolved_dir = os.path.abspath(os.path.expanduser(os.fspath(model_dir)))
        # 拼接 BRISQUE 主模型文件的完整路径
        model_path = os.path.join(resolved_dir, _BRISQUE_MODEL_FILENAME)
        # 拼接 BRISQUE 动态范围配置文件的完整路径
        range_path = os.path.join(resolved_dir, _BRISQUE_RANGE_FILENAME)

        # 目录必须存在，否则后续读文件无意义
        if not os.path.isdir(resolved_dir):
            raise FileNotFoundError(f"模型目录不存在: {resolved_dir}")
        # 主模型与 range 文件都必须为普通文件（排除目录同名等情况）
        if not os.path.isfile(model_path):
            raise FileNotFoundError(f"BRISQUE 模型文件缺失: {model_path}")
        if not os.path.isfile(range_path):
            raise FileNotFoundError(f"BRISQUE range 文件缺失: {range_path}")

        # 创建 BRISQUE 评估器；捕获 OpenCV 底层异常并附上可读说明
        try:
            self.brisque = cv2.quality.QualityBRISQUE.create(model_path, range_path)
        except cv2.error as exc:
            raise RuntimeError(
                f"无法初始化 BRISQUE（请检查模型是否与当前 OpenCV 版本兼容）: {model_path}"
            ) from exc

    def evaluate(self, image_path: Union[str, os.PathLike]) -> float:
        # 统一为字符串路径，便于报错信息与 OpenCV API 使用
        path = os.fspath(image_path)
        # 空路径直接拒绝，避免 imread 行为不明确
        if not path or not path.strip():
            raise ValueError("图像路径为空")
        # 路径必须对应已存在的普通文件
        if not os.path.isfile(path):
            raise FileNotFoundError(f"图像文件不存在或不是文件: {path}")

        # 按默认 BGR 三通道读取图像
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        # imread 失败时返回 None，需显式判断
        if img is None:
            raise ValueError(f"无法解码图像（格式损坏或不受支持）: {path}")
        # 必须是彩色三通道，否则 LAB 转换与后续假设不成立
        if img.ndim != 3 or img.shape[2] != 3:
            raise ValueError(f"需要 BGR 三通道图像，当前 shape={img.shape}: {path}")

        # BGR → LAB，便于仅用亮度 L 做质量评估，减弱色彩偏差影响
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        # 取 L 通道（单通道 uint8）
        l_channel = lab[:, :, 0]
        # 将灰度扩展为伪 BGR 三通道，满足 BRISQUE 对三通道输入的要求
        img_preprocessed = cv2.cvtColor(l_channel, cv2.COLOR_GRAY2BGR)

        # compute 返回 Scalar，取第一个分量作为原始 BRISQUE 分数
        try:
            raw_scalar = self.brisque.compute(img_preprocessed)
        except cv2.error as exc:
            raise RuntimeError(f"BRISQUE 计算失败: {path}") from exc

        raw_score = float(raw_scalar[0])
        # 将原始分数裁剪到 [0, 100] 再线性映射到 [0, 1]，1 表示质量更好
        clipped = 0.0 if raw_score < 0 else 100.0 if raw_score > 100 else raw_score
        normalized_score = 1.0 - clipped / 100.0
        return normalized_score
