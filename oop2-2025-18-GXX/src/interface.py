import cv2
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QFileDialog
from app.view import MainWindow
from app.model import ImageProcessingModel
import numpy as np
import os
from typing import Optional

class Interface:
    """
    Model (画像管理) と View (GUI) の間の仲介役（Controller/Presenter）。
    カメラの初期化、QTimerによるライブフィード制御、ViewとModelの接続を担う。
    """
    def __init__(self, view: MainWindow, model: ImageProcessingModel):
        # ModelとViewのインスタンスを参照として保持
        self.view = view
        self.model = model
        
        self.timer = QTimer()
        self.is_live_feed: bool = False # ライブフィードがアクティブかどうか
        
        self._load_initial_images()
        self._setup_timer()
        self._connect_signals()
        
    def _load_initial_images(self):
        """
        初期ロード時にGoogleロゴ画像 (images/google.png) を読み込み、Modelに設定する。
        """
        # プロジェクトルートからの相対パス ('images/google.png') を想定
        image_path = 'images/google.png' 
        google_img = cv2.imread(image_path)
        
        if google_img is None:
            self.view.show_error_message(
                "画像ロードエラー", 
                f"Googleロゴ画像 '{image_path}' が見つかりません。プロジェクトルートの 'images/google.png' を確認してください。"
            )
        else:
            self.model.set_google_image(google_img)
        
    def _setup_timer(self):
        """カメラフレーム取得のためのQTimerを設定する"""
        self.timer.timeout.connect(self.update_frame)
        # Modelで定義されたフレーム間隔を使用
        self.timer.setInterval(self.model.DELAY) 
        
    def _connect_signals(self):
        """Viewで定義されたシグナルを、Interfaceの処理メソッドに接続する。"""
        
        self.view.capture_toggle_requested.connect(self.handle_capture_toggle)
        self.view.composite_requested.connect(self.handle_capture_and_composite)
        self.view.save_requested.connect(self.handle_save_image)

    # ----------------------------------------------------
    # カメラライブフィード関連
    # ----------------------------------------------------

    def handle_capture_toggle(self):
        """
        Viewからの「撮影開始/停止」リクエストを処理する。（トグル）
        """
        if self.model.google_img is None:
            self.view.show_error_message("処理未完了", "初期画像が読み込めていないため処理できません。")
            return
            
        if self.timer.isActive():
            # 既にライブフィード中の場合、停止する
            self._stop_live_feed()
            self.view.show_status_message("カメラ停止しました。")
        elif self.model.is_camera_open():
             # フリーズ中からの再開
             self._start_live_feed()
             self.view.show_status_message("ライブフィード再開。")
        else:
            # カメラ起動（Interfaceがcv2.VideoCaptureを初期化し、Modelに渡す）
            cap_object = cv2.VideoCapture(0) # カメラID 0 を使用
            
            # カメラ設定（Modelのロジックを使用せず、Interface側で設定する例）
            cap_object.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap_object.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            if cap_object.isOpened():
                self.model.set_camera_object(cap_object)
                self._start_live_feed()
                self.view.show_status_message("ライブフィード開始。画像合成を実行ボタンでキャプチャ")
            else:
                cap_object.release() # 失敗時は解放
                self.view.show_error_message("カメラエラー", "カメラの起動に失敗しました。カメラIDを確認してください。")
                self.view.set_toggle_button_text("撮影開始")

    def _start_live_feed(self):
        """ライブフィードを開始する"""
        self.is_live_feed = True
        self.timer.start()
        self.view.set_toggle_button_text("撮影停止")

    def _stop_live_feed(self):
        """ライブフィードを停止する（カメラリソースは解放しない）"""
        self.timer.stop()
        self.is_live_feed = False
        self.view.set_toggle_button_text("再開") # フリーズ状態に移行
        
    def update_frame(self):
        """
        QTimerのタイムアウト時に呼ばれ、カメラからフレームを取得してViewに表示する。
        """
        frame = self.model.get_frame_for_display() 
        
        if frame is None:
            if self.is_live_feed:
                self._stop_live_feed()
                self.model.stop_capture()
                self.view.display_frame(None)
                self.view.show_status_message("フレーム取得失敗。カメラを停止しました。")
            return

        # BGR (OpenCV) -> RGB に変換
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # QImage -> QPixmapに変換し、Viewに表示を指示
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        self.view.display_frame(pixmap)
        
    # ----------------------------------------------------
    # 画像合成・保存関連
    # ----------------------------------------------------
    
    def handle_capture_and_composite(self):
        """
        Viewからの「画像合成」リクエストを処理する。
        ライブフレームをフリーズし、画像合成処理を実行する。
        """
        if not self.is_live_feed:
             self.view.show_status_message("エラー: ライブフィード中に合成を行ってください。")
             return

        self.view.show_status_message("画像合成処理を実行中...")

        try:
            # Modelに画像合成を依頼
            composite_image = self.model.process_and_capture_composite_image()
            
            if isinstance(composite_image, np.ndarray):
                
                # BGR (OpenCV) -> RGB に変換し、Viewに表示を指示
                image_rgb = cv2.cvtColor(composite_image, cv2.COLOR_BGR2RGB)
                h, w, ch = image_rgb.shape
                bytes_per_line = ch * w
                q_image = QImage(image_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                
                self.view.display_frame(QPixmap.fromImage(q_image)) # <-- 合成画像を中央に表示
                
                # ライブフィードを停止し、フリーズ状態へ
                self._stop_live_feed() 
                
                self.view.show_status_message("画像合成完了: 合成画像を中央に表示中。「再開」ボタンでライブに戻ります。")
            else:
                self.view.show_error_message("合成エラー", "画像合成処理に失敗しました。")
                
        except ValueError as e:
             self.view.show_error_message("処理エラー", str(e))
             
    def handle_save_image(self):
        """
        Viewからの「保存」リクエストを処理する。
        """
        if self.model.get_captured_image() is None:
            self.view.show_status_message("エラー: 保存する画像がありません。「画像合成を実行」ボタンで合成画像をキャプチャしてください。")
            return
            
        file_path = self.view.ask_save_filename("composite_image.png")
        
        if file_path:
            self.view.show_status_message(f"画像を '{file_path}' に保存中...")
            
            try:
                if self.model.save_image(file_path):
                    self.view.show_status_message(f"保存完了: {file_path}")
                else:
                    self.view.show_error_message("保存エラー", "ファイル書き込みに失敗しました。")
            except ValueError as e:
                self.view.show_error_message("保存エラー", str(e))