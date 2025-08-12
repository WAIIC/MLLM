import cv2
import numpy as np
import json
import time
from pymycobot import MyCobot280
from pymycobot import PI_PORT, PI_BAUD

mc = MyCobot280(PI_PORT, PI_BAUD)

class camera_detect:
    def __init__(self, camera_id, marker_size, mtx, dist):
        self.camera_id = camera_id
        self.mtx = mtx
        self.dist = dist
        self.marker_size = marker_size
        self.camera = cv2.VideoCapture(camera_id)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.origin_mycbot_horizontal = [39.19, -4.39, -69.43, -10.63, 1.75, 80.77]
        self.origin_mycbot_level = [39.19, -4.39, -69.43, -10.63, 1.75, 80.77]
        self.IDENTIFY_LEN = 300  # to keep identify length
        self.EyesInHand_matrix = None
        self.load_matrix()

    def save_matrix(self, filename="EyesInHand_matrix.json"):
        if self.EyesInHand_matrix is not None:
            with open(filename, 'w') as f:
                json.dump(self.EyesInHand_matrix.tolist(), f)

    def load_matrix(self, filename="EyesInHand_matrix.json"):
        try:
            with open(filename, 'r') as f:
                self.EyesInHand_matrix = np.array(json.load(f))
        except FileNotFoundError:
            print(f"Matrix file {filename} not found. EyesInHand_matrix will be initialized later.")

    def wait(self):
        time.sleep(0.5)
        while mc.is_moving():
            time.sleep(0.2)

    def coord_limit(self, coords):
        min_coord = [-350, -350, 300]
        max_coord = [350, 350, 500]
        for i in range(3):
            if coords[i] < min_coord[i]:
                coords[i] = min_coord[i]
            if coords[i] > max_coord[i]:
                coords[i] = max_coord[i]

    def camera_open(self):
        self.camera.open(self.camera_id)

    def get_frame(self):
        ret, frame = self.camera.read()
        if not ret:
            print("Failed to grab frame")
            return None
        return frame

    def detect_aruco(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        parameters = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
        corners, ids, rejectedImgPoints = detector.detectMarkers(gray)
        if len(corners) > 0:
            return corners, ids
        return None, None

    def calc_markers_base_position(self, corners, ids):
        """
        输入：
            corners : list[np.ndarray]  每个元素的 shape=(1,4,2)
            ids     : list[int]
        返回：
            np.ndarray  [x,y,z,rx,ry,rz] 在相机坐标系下的位姿
        """
        if len(corners) == 0:
            return None

        # ArUco 的 4 个角点（单位：米）
        object_points = np.array([
            [-self.marker_size / 2, -self.marker_size / 2, 0],
            [self.marker_size / 2, -self.marker_size / 2, 0],
            [self.marker_size / 2, self.marker_size / 2, 0],
            [-self.marker_size / 2, self.marker_size / 2, 0]
        ], dtype=np.float32)

        # 遍历所有检测到的 marker
        for corner in corners:
            image_points = corner[0]  # shape=(4,2)
            success, rvec, tvec = cv2.solvePnP(
                object_points,
                image_points,
                self.mtx,
                self.dist
            )
            if success:
                # 旋转向量 → 旋转矩阵 → 欧拉角
                R, _ = cv2.Rodrigues(rvec)
                Euler = self.CvtRotationMatrixToEulerAngle(R)
                return np.array([tvec[0, 0], tvec[1, 0], tvec[2, 0],
                                 Euler[0], Euler[1], Euler[2]])
        return None

    def CvtRotationMatrixToEulerAngle(self, pdtRotationMatrix):
        pdtEulerAngle = np.zeros(3)
        pdtEulerAngle[2] = np.arctan2(pdtRotationMatrix[1, 0], pdtRotationMatrix[0, 0])
        fCosRoll = np.cos(pdtEulerAngle[2])
        fSinRoll = np.sin(pdtEulerAngle[2])
        pdtEulerAngle[1] = np.arctan2(-pdtRotationMatrix[2, 0],
                                      (fCosRoll * pdtRotationMatrix[0, 0]) + (fSinRoll * pdtRotationMatrix[1, 0]))
        pdtEulerAngle[0] = np.arctan2((fSinRoll * pdtRotationMatrix[0, 2]) - (fCosRoll * pdtRotationMatrix[1, 2]),
                                      (-fSinRoll * pdtRotationMatrix[0, 1]) + (fCosRoll * pdtRotationMatrix[1, 1]))
        return pdtEulerAngle

    def Eyes_in_hand(self, coord, camera, Matrix_TC):
        Position_Camera = np.transpose(camera[:3])  # 相机坐标
        Matrix_BT = self.Transformation_matrix(coord)  # 机械臂坐标矩阵

        Position_Camera = np.append(Position_Camera, 1)  # 物体坐标（相机系）
        Position_B = Matrix_BT @ Matrix_TC @ Position_Camera  # 物体坐标（基坐标系）
        return Position_B

    def Transformation_matrix(self, coord):
        position_robot = coord[:3]
        pose_robot = coord[3:]
        RBT = self.CvtEulerAngleToRotationMatrix(pose_robot)  # 将欧拉角转为旋转矩阵
        PBT = np.array([[position_robot[0]],
                        [position_robot[1]],
                        [position_robot[2]]])
        temp = np.concatenate((RBT, PBT), axis=1)
        array_1x4 = np.array([[0, 0, 0, 1]])
        matrix = np.concatenate((temp, array_1x4), axis=0)  # 将两个数组按行拼接起来
        return matrix

    def CvtEulerAngleToRotationMatrix(self, ptrEulerAngle):
        ptrSinAngle = np.sin(ptrEulerAngle)
        ptrCosAngle = np.cos(ptrEulerAngle)
        ptrRotationMatrix = np.zeros((3, 3))
        ptrRotationMatrix[0, 0] = ptrCosAngle[2] * ptrCosAngle[1]
        ptrRotationMatrix[0, 1] = ptrCosAngle[2] * ptrSinAngle[1] * ptrSinAngle[0] - ptrSinAngle[2] * ptrCosAngle[0]
        ptrRotationMatrix[0, 2] = ptrCosAngle[2] * ptrSinAngle[1] * ptrCosAngle[0] + ptrSinAngle[2] * ptrSinAngle[0]
        ptrRotationMatrix[1, 0] = ptrSinAngle[2] * ptrCosAngle[1]
        ptrRotationMatrix[1, 1] = ptrSinAngle[2] * ptrSinAngle[1] * ptrSinAngle[0] + ptrCosAngle[2] * ptrCosAngle[0]
        ptrRotationMatrix[1, 2] = ptrSinAngle[2] * ptrSinAngle[1] * ptrCosAngle[0] - ptrCosAngle[2] * ptrSinAngle[0]
        ptrRotationMatrix[2, 0] = -ptrSinAngle[1]
        ptrRotationMatrix[2, 1] = ptrCosAngle[1] * ptrSinAngle[0]
        ptrRotationMatrix[2, 2] = ptrCosAngle[1] * ptrCosAngle[0]
        return ptrRotationMatrix

    def detect_and_calculate(self, mc):
        frame = self.get_frame()
        if frame is None:
            return None
        corners, ids = self.detect_aruco(frame)
        if ids is None:
            return None
        target_coords = self.calc_markers_base_position(corners, ids)
        if target_coords is None:
            return None
        current_coords = mc.get_coords()
        while current_coords is None:
            current_coords = mc.get_coords()
        cur_coords = np.array(current_coords.copy())
        cur_coords[-3:] *= np.pi / 180  # 转为弧度
        fact_bcl = self.Eyes_in_hand(cur_coords, target_coords, self.EyesInHand_matrix)
        return fact_bcl

    def vision_trace_loop(self, mc):
        while True:
            result = self.detect_and_calculate(mc)
            if result is not None:
                print("Detected coordinates:", result)
            time.sleep(0.1)
    # -------- 手眼标定接口（ArUco 版） --------
    def Matrix_identify(self, ml):
        """
        让机械臂移动 5 个位姿，记录 (机械臂坐标, ArUco相机坐标)
        返回 pose, tbe, Mc, state
        """
        ml.send_angles(self.origin_mycbot_level, 50)
        self.wait()
        input("确保相机能看到 ArUco，按回车继续...")

        pose = ml.get_coords()[3:6]
        Mc_all, tbe_all = [], []
        for i in range(5):
            print(f"第 {i+1}/5 次采集...")
            corners, ids = self.detect_aruco(self.get_frame())
            if ids is None:
                print("❌ 未检测到 ArUco，重试")
                continue
            target = self.calc_markers_base_position(corners, ids)
            if target is None:
                continue
            Mc_all.append(target[:3])
            tbe_all.append(ml.get_coords()[:3])
            # 简单扰动
            ml.send_coord(1, ml.get_coords()[0] + (i+1)*20, 30)
            self.wait()

        Mc = np.array(Mc_all)
        tbe = np.array(tbe_all)
        return pose, tbe, Mc, None

    def eyes_in_hand_calculate(self, pose, tbe, Mc, Mr):
        """
        计算手眼矩阵（eye-in-hand）
        """
        pose, Mr = np.array(pose), np.array(Mr)
        euler = pose * np.pi / 180
        Rbe = self.CvtEulerAngleToRotationMatrix(euler)
        Reb = Rbe.T

        A = np.empty((3, 0))
        b_comb = np.empty((3, 0))
        r = tbe.shape[0]
        for i in range(1, r):
            A = np.hstack((A, (Mc[i] - Mc[0]).reshape(3, 1)))
            b_comb = np.hstack((b_comb, (tbe[0] - tbe[i]).reshape(3, 1)))

        b = Reb @ b_comb
        U, _, Vt = np.linalg.svd(A @ b.T)
        Rce = Vt.T @ U.T

        tbe_sum = np.sum(tbe, axis=0)
        Mc_sum = np.sum(Mc, axis=0)
        tce = Reb @ (Mr.reshape(3, 1) - tbe_sum.reshape(3, 1)/r - (Rbe @ Rce @ Mc_sum.reshape(3, 1))/r)
        tce[2] -= self.IDENTIFY_LEN  # 保持识别距离

        EyesInHand_matrix = np.vstack((np.hstack((Rce, tce)), [0, 0, 0, 1]))
        print("EyesInHand_matrix = \n", EyesInHand_matrix)
        return EyesInHand_matrix

    def Eyes_in_hand_calibration(self, ml):
        """
        完整标定流程
        """
        pose, tbe, Mc, _ = self.Matrix_identify(ml)
        input("将机械臂末端贴到 ArUco 中心，按回车继续...")
        mc.release_all_servos()
        input("贴紧后按回车锁定伺服")
        ml.power_on()
        Mr = np.array(ml.get_coords()[:3])
        self.EyesInHand_matrix = self.eyes_in_hand_calculate(pose, tbe, Mc, Mr)
        self.save_matrix()
        print("✅ 手眼矩阵已保存到 EyesInHand_matrix.json")
if __name__ == "__main__":
    camera_params = np.load("camera_params.npz")
    mtx, dist = camera_params["mtx"], camera_params["dist"]
    mc = MyCobot280(PI_PORT, PI_BAUD)
    cd = camera_detect(20, 100, mtx, dist)
    cd.vision_trace_loop(mc)