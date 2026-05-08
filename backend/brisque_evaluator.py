import os
import cv2

class BRISQUEQualityEvaluator:
    def __init__(self, model_dir="models"):
        # 加载 BRISQUE 所需的模型文件
        model_path = os.path.join(model_dir, "brisque_model_live.yml")
        range_path = os.path.join(model_dir, "brisque_range_live.yml")

        # 检查文件是否存在
        if not os.path.exists(model_path) or not os.path.exists(range_path):
            raise FileNotFoundError(f"模型文件不存在，请确认路径：{model_path}, {range_path}")

        # 创建 BRISQUE 对象
        self.brisque = cv2.quality.QualityBRISQUE.create(model_path, range_path)

    def evaluate(self, image_path):
        # 读取图像（OpenCV 默认是 BGR 格式）
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图像: {image_path}")

        # 将 BRISQUE 分数归一化到 [0, 1] 范围，值越大表示图像质量越好
        raw_score = self.brisque.compute(img)[0]
        normalized_score = 1 - min(max(raw_score, 0), 100) / 100.0
        return normalized_score
