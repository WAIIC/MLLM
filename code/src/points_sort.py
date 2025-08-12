#points_sort.py
import numpy as np

# 定义坐标点
points = [
    [31, 67], [14, 74], [12, 82], [33, 73], [52, 78], [70, 83], [89, 97], [114, 105],
    [137, 103], [152, 104], [176, 105], [216, 94], [230, 89], [245, 95], [256, 94],
    [244, 86], [226, 77], [209, 91], [192, 99], [181, 102], [146, 98], [130, 101],
    [112, 100], [93, 96], [69, 79], [45, 73]
]

points = np.array(points)

# 定义一个函数来计算两点之间的欧几里得距离
def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

current_point = points[0]
ordered_points = [current_point.tolist()]
remaining_points = points[1:]

while len(remaining_points) > 0:
    # 计算当前点到所有剩余点的距离
    distances = [distance(current_point, point) for point in remaining_points]
    # 找到最近的点
    nearest_index = np.argmin(distances)
    nearest_point = remaining_points[nearest_index]
    # 将最近的点添加到有序列表中
    ordered_points.append(nearest_point.tolist())
    # 更新当前点
    current_point = nearest_point
    # 从剩余点中移除已选择的点
    remaining_points = np.delete(remaining_points, nearest_index, axis=0)

print("排序后的坐标：")
print(ordered_points)