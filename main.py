import sys
from PySide6.QtWidgets import QApplication
from app.view import MainWindow
from app.model import ImageProcessingModel
from app.interface import Interface

def main():
    """
    アプリケーションのエントリーポイント。
    Model, View, Interfaceのインスタンス化と接続を行う。
    """
    # 1. Qtアプリケーションのインスタンス化
    app = QApplication(sys.argv)
    
    # 2. Model, View, Interfaceのインスタンス化
    
    # Model: データとロジック (引数なし)
    model = ImageProcessingModel()
    
    # View: GUIの見た目 (引数なし)
    view = MainWindow()
    
    # Interface (Controller): ModelとViewの仲介
    # Interfaceを初期化する際に、ModelとViewの両方を渡して紐づける
    interface = Interface(view=view, model=model)
    
    # 3. Viewの表示
    # Interfaceの初期化時に、ViewのシグナルはInterfaceのメソッドに接続済み
    view.show()
    
    # 4. イベントループの開始
    sys.exit(app.exec())

if __name__ == '__main__':
    # アプリケーションの実行
    main()