#utils_test_script2.py
import cv2, json
from utils_robot import mc, top_view_shot

points = []
def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        coords = mc.get_coords()[:2]
        points.append((x, y, *coords))
        print(f"记录 -> 像素:({x},{y}) 机械臂:{coords}")

top_view_shot(check=True)
cv2.namedWindow("click")
cv2.setMouseCallback("click", on_mouse)
cv2.imshow("click", cv2.imread("temp/vl_now.jpg"))
cv2.waitKey(0)
cv2.destroyAllWindows()

json.dump(points, open("temp/points.json","w"), indent=2)
print("已保存到 temp/points.json")