# crack_detect_origin.py
import cv2
import numpy as np
import json

def extract_ordered_line_coordinates(image_path, output_json_path, num_points=50):
    # 读取带有透明通道的图像
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("请检查路径是否正确")

    # 分离透明通道
    alpha_channel = image[:, :, 3]
    _, binary = cv2.threshold(alpha_channel, 1, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    if len(contours) == 0:
        raise ValueError("未检测到任何轮廓")
    max_contour = max(contours, key=cv2.contourArea)

    # 提取轮廓上的点
    points = max_contour.reshape(-1, 2)

    # 沿轮廓等距采样
    def interpolate_points(points, num_points):
        distances = np.sqrt(np.sum(np.diff(points, axis=0)**2, axis=1))
        cumulative_distances = np.cumsum(distances)
        total_distance = cumulative_distances[-1]
        target_distances = np.linspace(0, total_distance, num_points)
        interpolated_points = []
        for target_distance in target_distances:
            if target_distance == 0:
                interpolated_points.append(points[0])
            else:
                idx = np.searchsorted(cumulative_distances, target_distance)
                if idx == 0:
                    interpolated_points.append(points[0])
                else:
                    prev_point = points[idx - 1]
                    next_point = points[idx]
                    prev_distance = cumulative_distances[idx - 1]
                    fraction = (target_distance - prev_distance) / distances[idx - 1]
                    interpolated_point = prev_point + fraction * (next_point - prev_point)
                    interpolated_points.append(interpolated_point)
        return np.array(interpolated_points)

    ordered_points = interpolate_points(points, num_points)

    # 获取图像尺寸
    height, width = binary.shape

    # 创建JSON输出
    output = {
        "seam_path": [{"x": int(point[0]), "y": int(point[1])} for point in ordered_points],
        "start_point": {"x": int(ordered_points[0][0]), "y": int(ordered_points[0][1])},
        "end_point": {"x": int(ordered_points[-1][0]), "y": int(ordered_points[-1][1])},
        "image_dimensions": {"width": width, "height": height},
        "points_count": num_points
    }

    # 保存为JSON文件
    with open(output_json_path, 'w') as f:
        json.dump(output, f, indent=4)


# 示例用法
image_path = "cracks/pic2.png"
output_json_path = "cracks/line_coordinates.json"  # 输出的JSON文件路径
extract_ordered_line_coordinates(image_path, output_json_path)