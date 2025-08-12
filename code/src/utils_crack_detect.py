#utils_crack_detect.py
import cv2
import numpy as np
import json
import os
import math


def extract_ordered_line_coordinates(image_path, output_json_path, num_points=50):
    # 直接从本地读取图片文件
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件 {image_path} 不存在！")

    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"无法读取图片文件 {image_path}，请检查格式是否正确！")

    # 分离透明通道
    if image.shape[2] != 4:
        raise ValueError("图像不包含透明通道！")
    alpha_channel = image[:, :, 3]

    # 将透明通道转换为二值图像
    _, binary = cv2.threshold(alpha_channel, 1, 255, cv2.THRESH_BINARY)

    # 查找轮廓
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # 假设最长的轮廓是目标线条
    if len(contours) == 0:
        raise ValueError("未检测到任何轮廓！")
    max_contour = max(contours, key=cv2.contourArea)

    # 提取轮廓上的点
    points = max_contour.reshape(-1, 2)

    # 找到起点和终点（在图像边界上的点）
    def is_on_edge(point, width, height):
        return point[0] == 0 or point[0] == width - 1 or point[1] == 0 or point[1] == height - 1

    height, width = binary.shape

    # 找到所有在边界上的点
    edge_points = [point for point in points if is_on_edge(point, width, height)]

    if len(edge_points) < 2:
        raise ValueError("未找到足够的边界点！")

    start_point = edge_points[0]
    end_point = edge_points[-1]

    # 沿轮廓等距采样
    def interpolate_points(points, num_points):
        distances = np.sqrt(np.sum(np.diff(points, axis=0) ** 2, axis=1))
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

    # 点坐标排序算法 - 确保点按顺序连接形成连续线条
    def sort_points(points, start, end):
        """对点进行排序，从起点开始，沿着线条到终点"""
        # 计算每个点到起点的距离
        distances = np.linalg.norm(points - start, axis=1)

        # 按距离排序
        sorted_indices = np.argsort(distances)
        sorted_points = points[sorted_indices]

        # 确保起点是第一个点
        start_idx = np.argmin(np.linalg.norm(sorted_points - start, axis=1))
        if start_idx > 0:
            sorted_points = np.roll(sorted_points, -start_idx, axis=0)

        # 确保终点是最后一个点
        end_idx = np.argmin(np.linalg.norm(sorted_points - end, axis=1))
        if end_idx < len(sorted_points) - 1:
            # 如果终点不在最后，反转后半部分点
            sorted_points = np.concatenate([
                sorted_points[:end_idx + 1],
                np.flip(sorted_points[end_idx + 1:], axis=0)
            ])

        return sorted_points

    # 应用排序算法
    sorted_points = sort_points(ordered_points, start_point, end_point)

    # 创建JSON输出
    output = {
        "seam_path": [{"x": int(point[0]), "y": int(point[1])} for point in sorted_points],
        "start_point": {"x": int(start_point[0]), "y": int(start_point[1])},
        "end_point": {"x": int(end_point[0]), "y": int(end_point[1])},
        "image_dimensions": {"width": width, "height": height},
        "points_count": num_points
    }

    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)

    # 保存为JSON文件
    with open(output_json_path, 'w') as f:
        json.dump(output, f, indent=4)

    print(f"起点: ({start_point[0]}, {start_point[1]}), 终点: ({end_point[0]}, {end_point[1]})")
    print(f"共 {num_points} 个有序点")


image_path = "segmented_image.png"  # 本地图片路径
output_json_path = "cracks/line_coordinates.json"  # 输出的JSON文件路径
extract_ordered_line_coordinates(image_path, output_json_path)