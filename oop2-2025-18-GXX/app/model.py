import numpy as np
import cv2
from typing import Optional

class ImageProcessingModel:
    """
    アプリケーションのデータ（画像）とビジネスロジックを担当するクラス。
    カメラフレームの取得、画像合成ロジック、画像データの保持を行う。
    Interface から設定されたカメラオブジェクトとロゴ画像を使用する。
    """
    
    # フレームごとの表示間隔（GUI側でQTimerに使用）
    DELAY: int = 33 # 1000ms / 30fps

    # ----------------------------------------------------
    # コンストラクタ: Modelはデータとロジックの提供に専念するため引数なし
    # ----------------------------------------------------
    def __init__(self):
        # ライブフィード中に最後に取得した生フレーム（ターゲットマークなし）
        self.current_live_frame: Optional[np.ndarray] = None
        # ユーザーがフリーズ/撮影した画像（合成後の保存対象）
        self.captured_composite_image: Optional[np.ndarray] = None 
        # OpenCVのビデオキャプチャオブジェクト（Interfaceから設定される）
        self.cap: Optional[cv2.VideoCapture] = None
        
        # 課題に必要なGoogleロゴ画像（背景画像）
        self.google_img: Optional[np.ndarray] = None

    # ----------------------------------------------------
    # Interfaceから呼ばれる設定ロジック
    # ----------------------------------------------------
    def set_google_image(self, img_data: np.ndarray):
        """InterfaceからGoogleロゴの画像データを受け取り、内部に保持する"""
        self.google_img = img_data

    def set_camera_object(self, cap_object: cv2.VideoCapture):
        """Interfaceから初期化済みのカメラオブジェクトを受け取る"""
        self.cap = cap_object

    # ----------------------------------------------------
    # カメラフレーム取得 ロジック
    # ----------------------------------------------------
    def is_camera_open(self) -> bool:
        """カメラがオープン状態かどうかを返す"""
        return self.cap is not None and self.cap.isOpened()
    
    def stop_capture(self):
        """カメラキャプチャを停止し、リソースを解放する"""
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
            self.cap = None
            
    def get_frame_for_display(self) -> Optional[np.ndarray]:
        """
        カメラから最新のフレームを取得し、ターゲットマークを付加して返す。
        生フレームは self.current_live_frame に保存される。
        """
        if not self.is_camera_open():
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        # 生フレームを内部状態として保存
        self.current_live_frame = frame
        
        # ----------------------------------------------------
        # ライブフィード用：ターゲットマーク描画ロジック
        # ----------------------------------------------------
        img = frame.copy()
        h, w, _ = img.shape
        center = (w // 2, h // 2)

        # 赤いターゲットマークを描画
        img = cv2.line(img, (center[0], center[1] - 80), (center[0], center[1] + 80), (0, 0, 255), 3)
        img = cv2.line(img, (center[0] - 80, center[1]), (center[0] + 80, center[1]), (0, 0, 255), 3)

        # 左右反転
        img = cv2.flip(img, flipCode=1)
        
        return img # ターゲットマーク付きのフレームを返す

    # ----------------------------------------------------
    # 画像合成/保存 ロジック
    # ----------------------------------------------------
    
    def process_and_capture_composite_image(self) -> Optional[np.ndarray]:
        """
        現在のライブフレームを取得し、Googleロゴの白色部分を置き換える画像合成処理を実行する。
        """
        capture_img = self.current_live_frame # 現在のカメラフレーム
        
        if capture_img is None or self.google_img is None:
            raise ValueError("Google画像またはカメラフレームがロードされていません。")

        composite_img = self.google_img.copy() 
        
        g_hight, g_width, _ = composite_img.shape
        c_hight, c_width, _ = capture_img.shape
        
        # 課題の画像合成ロジック（白色置き換え）
        for x in range(g_width):
            for y in range(g_hight):
                b, g, r = composite_img[y, x] 
                
                if (b, g, r) == (255, 255, 255):
                    # カメラフレームをタイリングして使用（元のコードのロジックを再現）
                    composite_img[y, x] = capture_img[y % c_hight, x % c_width]
                    
        self.captured_composite_image = composite_img
        
        return composite_img

    def get_captured_image(self) -> Optional[np.ndarray]:
        """最後にキャプチャ/合成された画像を取得する"""
        return self.captured_composite_image

    def save_image(self, file_path: str) -> bool:
        """最後にキャプチャ/合成された画像（self.captured_composite_image）をファイルに保存する"""
        if self.captured_composite_image is None:
            raise ValueError("保存する画像がありません。")

        return cv2.imwrite(file_path, self.captured_composite_image)