from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog,
    QStatusBar, QSizePolicy, QScrollArea, QFrame, QToolBar,
    QMessageBox # メッセージ表示に使用
)
from typing import Optional

class MainWindow(QMainWindow):
    """
    アプリケーションのView（GUI）を担当するクラス。
    
    責務:
    1. ウィンドウ、ウィジェットの作成とレイアウト。
    2. ユーザー操作（ボタンクリックなど）を検知し、シグナルを発行する。
    3. Controllerから指示された画像データを表示する。
    
    コンストラクタの引数は parent=None のみ。
    """

    # ----------------------------------------------------
    # 🔔 Controller へ飛ばすシグナルの定義 (引数なし)
    # ----------------------------------------------------
    save_requested = Signal()           # 画像を保存
    capture_toggle_requested = Signal() # カメラ撮影開始/停止要求 (トグル動作)
    composite_requested = Signal()      # 画像合成を実行する要求 
    
    # ----------------------------------------------------
    # コンストラクタ
    # ----------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Camera Composite App")
        self.resize(800, 600)
        
        self._create_actions()
        self._create_toolbar()
        self._create_central_widget()
        self._create_status_bar()

    # -------------------------
    # Actions, Toolbar, Layout (中略)
    # -------------------------

    def _create_actions(self):
        # 保存アクション
        self.act_save = QAction("保存", self)
        self.act_save.setShortcut("Ctrl+S")
        self.act_save.triggered.connect(self.save_requested.emit)

    def _create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        toolbar.addAction(self.act_save)

    def _create_central_widget(self):
        central = QWidget()
        layout = QVBoxLayout(central)

        # 画像/カメラ映像表示エリア
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True) 

        self.image_label = QLabel("撮影開始ボタンを押してカメラを起動してください")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFrameShape(QFrame.Shape.Box)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

        self.scroll.setWidget(self.image_label)
        layout.addWidget(self.scroll)

        # ボタンフレーム
        button_frame = QWidget()
        button_layout = QHBoxLayout(button_frame)
        
        # 撮影開始/停止ボタン
        self.capture_toggle_button = QPushButton("撮影開始")
        self.capture_toggle_button.clicked.connect(self.capture_toggle_requested.emit) 
        button_layout.addWidget(self.capture_toggle_button)
        
        # 画像合成実行ボタン
        self.composite_button = QPushButton("画像合成を実行")
        self.composite_button.clicked.connect(self.composite_requested.emit)
        button_layout.addWidget(self.composite_button)

        layout.addWidget(button_frame)
        self.setCentralWidget(central)

    def _create_status_bar(self):
        """ステータスバーを初期化し、メッセージラベルを設定する"""
        sb = QStatusBar()
        self.status_label = QLabel("Ready")
        sb.addWidget(self.status_label)
        self.setStatusBar(sb)


    # -------------------------
    # View API (Controllerから呼ばれるメソッド)
    # -------------------------

    def display_frame(self, pixmap: Optional[QPixmap]):
        """Controller がカメラ映像や合成画像を表示するために呼び出す"""
        if pixmap is None:
            self.image_label.clear()
            self.image_label.setText("撮影開始ボタンを押してカメラを起動してください")
            return
        
        # ラベルのサイズに合わせて画像をスケーリング（アスペクト比を維持）
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setText("") 
    
    def show_status_message(self, message: str):
        """ステータスバーにメッセージを表示する"""
        self.status_label.setText(message)

    def set_toggle_button_text(self, text: str):
        """撮影開始/停止ボタンのテキストを更新する"""
        self.capture_toggle_button.setText(text)

    # -------------------------
    # Controllerが使用するヘルパー
    # -------------------------
    def ask_save_filename(self, start="") -> str:
        """Controller が保存ファイル名を尋ねるために呼び出す"""
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "画像を保存", 
            start, 
            "PNG (*.png);;JPG (*.jpg)"
        )
        return path

    def show_error_message(self, title: str, message: str):
        """エラーメッセージボックスを表示する"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()