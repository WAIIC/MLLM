#utils_crack_move.py
import cv2
import numpy as np
import json
import os
import time
import math
from utils_robot import *  # 导入机械臂控制函数
from utils_crack_upload import *


def extract_ordered_line_coordinates(image_path, output_json_path, num_points=50, visualize=True):
    """从分割图像中提取有序的裂纹点坐标，并可选进行可视化"""
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

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)


    # 保存为JSON文件
    with open(output_json_path, 'w') as f:
        json.dump(output, f, indent=4)

    print(f"裂纹坐标已成功保存到 {output_json_path}")
    print(f"起点: ({start_point[0]}, {start_point[1]}), 终点: ({end_point[0]}, {end_point[1]})")
    print(f"共 {num_points} 个有序点")

    # 可视化处理 - 将点坐标标注在图像上
    if visualize:
        # 创建可视化图像
        # 使用原始分割图像作为背景
        visual_image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        # 绘制裂纹轮廓
        contour_points = np.array([(point[0], point[1]) for point in sorted_points], dtype=np.int32)
        cv2.polylines(visual_image, [contour_points], isClosed=False, color=(0, 255, 0), thickness=2)

        # 绘制起点和终点
        cv2.circle(visual_image, (start_point[0], start_point[1]), 8, (0, 0, 255), -1)  # 红色起点
        cv2.circle(visual_image, (end_point[0], end_point[1]), 8, (255, 0, 0), -1)  # 蓝色终点

        # 绘制所有点
        for i, point in enumerate(sorted_points):

            x, y = int(point[0]), int(point[1])
            # 绘制点
            cv2.circle(visual_image, (x, y), 3, (255, 0, 255), -1)  # 紫色点

            # 标注点序号
            cv2.putText(visual_image, str(i + 1), (x + 5, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # 添加图例
        cv2.putText(visual_image, "Start", (start_point[0] + 10, start_point[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(visual_image, "End", (end_point[0] + 10, end_point[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        cv2.putText(visual_image, f"Points: {num_points}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # 保存可视化图像

        visual_path = output_json_path.replace(".json", "_visual.png")
        cv2.imwrite(visual_path, visual_image)
        print(f"可视化图像已保存至: {visual_path}")

        # 显示可视化图像（可选）
        cv2.imshow("Crack Visualization", visual_image)
        cv2.waitKey(5000)  # 显示1秒
        cv2.destroyAllWindows()

    return output


def move_along_crack(json_path, safe_height=230, speed=20, delay=1.0):
    """
    控制机械臂沿着裂纹点坐标顺序移动（从第二个点开始）


    参数:
    json_path: 包含裂纹点坐标的JSON文件路径
    safe_height: 机械臂移动的安全高度

    speed: 机械臂移动速度
    delay: 每个点之间的延迟时间（秒）

    """
    # 读取裂纹点坐标
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON文件 {json_path} 不存在！")

    with open(json_path, 'r') as f:
        crack_data = json.load(f)

    print(f"读取裂纹点坐标成功，共 {crack_data['points_count']} 个点")

    # 获取点列表
    points = crack_data["seam_path"]

    # 移动到安全高度
    print("移动机械臂到安全高度...")
    mc.send_coords([0, 0, safe_height, 0, 180, 90], speed, 0)
    time.sleep(3)

    # 移动到起点上方
    start_point = crack_data["start_point"]
    start_x, start_y = eye2hand(start_point["x"], start_point["y"])
   # print(f"移动到起点上方: ({start_x}, {start_y})")
    #mc.send_coords([start_x, start_y, safe_height, 0, 180, 90], speed, 0)
    #time.sleep(3)

    # 移动到起点位置（降低高度）
    #print(f"移动到起点位置: ({start_x}, {start_y})")
    #mc.send_coords([start_x, start_y, safe_height - 50, 0, 180, 90], speed, 0)
    #time.sleep(2)

    # 沿着裂纹点移动（从第二个点开始）

    print("开始沿着裂纹移动")

    # 跳过第一个点（起点），从第二个点开始
    for i, point in enumerate(points[1:], start=1):  # 从索引1开始
        # 手眼标定转换
        x_robot, y_robot = eye2hand(point["x"], point["y"])

        # 移动到当前点（保持安全高度）
        print(f"移动至点 {i + 1}/{len(points)}: ({x_robot}, {y_robot})")
        mc.send_coords([x_robot, y_robot, safe_height - 50, 0, 180, 90], speed, 0)
        time.sleep(delay)

    # 移动到终点上方
    end_point = crack_data["end_point"]
    end_x, end_y = eye2hand(end_point["x"], end_point["y"])
    print(f"移动到终点上方: ({end_x}, {end_y})")
    mc.send_coords([end_x, end_y, safe_height, 0, 180, 90], speed, 0)
    time.sleep(2)

    # 返回安全位置
    print("返回安全位置...")
    mc.send_coords([0, 0, safe_height, 0, 180, 90], speed, 0)
    time.sleep(3)

    print("裂纹跟踪完成！")


# 主程序
def crack_move(PROMPT='焊接裂缝', input_way='keyboard'):

    try:
        # 1. 连接机械臂并初始化
        # 机械臂已在utils_robot中连接，这里只需确认连接
        '''

            拍摄一张图片并保存
            check：是否需要人工看屏幕确认拍照成功，再在键盘上按q键确认继续
        '''
        print('    移动至俯视姿态')
        move_to_top_view()
        time.sleep(1)

        # 获取摄像头，传入0表示获取系统默认摄像头
        cap = cv2.VideoCapture(20)
        # 打开cap
        cap.open(20)
        time.sleep(2)
        success, img_bgr = cap.read()

        # 保存图像
        print('    保存至同目录下的crack.png')
        cv2.imwrite('crack.png', img_bgr)

        # 屏幕上展示图像
        cv2.destroyAllWindows()  # 关闭所有opencv窗口
        cv2.imshow('waiic_crack', img_bgr)
        cv2.waitKey(1000)  # 显示1秒
        cv2.destroyAllWindows()

        # 关闭摄像头
        cap.release()

        # 2. 调用分割API
        print("调用分割API处理图像...")
        success, result = start_segmented_image_upload()
        if not success:
            raise RuntimeError(f"图像分割失败: {result}")

        image_path = "segmented_image.png"  # 分割后的图像路径
        json_path = "cracks/line_coordinates.json"  # 输出的JSON文件路径

        print("提取裂纹点坐标...")
        crack_data = extract_ordered_line_coordinates(image_path, json_path, num_points=30, visualize=True)

        # 3. 沿着裂纹点移动机械臂
        print("开始控制机械臂沿着裂纹移动...")
        move_along_crack(json_path, safe_height=100, speed=10, delay=2)

        # 4. 完成后放松机械臂
        print("任务完成，复位")

        back_zero()

    except Exception as e:
        print(f"发生错误: {str(e)}")
        back_zero()
