import numpy as np
import cv2


class MyVideoCapture:
    """Webカメラから映像を取得し、中心にターゲットマークを描画して表示・保存するクラス。

    Attributes:
        DELAY (int): 各フレームの表示間隔（ミリ秒）。
        cap (cv2.VideoCapture): OpenCVのビデオキャプチャオブジェクト。
        captured_img (np.ndarray | None): 最後にキャプチャされた画像データ。
    """

    DELAY: int = 100  # 100 msecのディレイ

    def __init__(self) -> None:
        """Webカメラを初期化する。

        Notes:
            PCによってはカメラIDが0ではなく1で動作する場合があるため、
            必要に応じて cv2.VideoCapture(1) に変更すること。
        """
        self.cap: cv2.VideoCapture = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.captured_img: np.ndarray | None = None

    def run(self) -> None:
        """カメラ映像を取得してリアルタイムに加工・表示する。

        処理の流れ:
            1. カメラから1フレームを取得。
            2. 取得した画像をコピーして加工（中心に赤いターゲットマークを描画）。
            3. 加工後の画像を左右反転して表示。
            4. 'q' キーが押されるまで処理を継続。

        Notes:
            - フレームの読み込みに失敗した場合（ret=False）、ループを終了する。
            - 終了時には最後にキャプチャした画像を `captured_img` に保持する。
        """
        while True:
            # カメラ画像を１枚キャプチャする
            ret, frame = self.cap.read()

            # リターンコードがFalseなら終了
            if not ret:
                break

            # 加工するともとの画像が保存できないのでコピーを生成
            img: np.ndarray = np.copy(frame)

            # 画像の中心を示すターゲットマークを描画
            rows, cols, _ = img.shape
            center = (int(cols / 2), int(rows / 2))
            img = cv2.circle(img, center, 30, (0, 0, 255), 3)
            img = cv2.circle(img, center, 60, (0, 0, 255), 3)
            img = cv2.line(img, (center[0], center[1] - 80), (center[0], center[1] + 80), (0, 0, 255), 3)
            img = cv2.line(img, (center[0] - 80, center[1]), (center[0] + 80, center[1]), (0, 0, 255), 3)

            # 左右反転（顔を撮るときは左右反転しておくとよい）
            img = cv2.flip(img, flipCode=1)

            # 加工した画像を表示
            cv2.imshow('frame', img)

            # 次の画像を処理するまでに時間間隔（msec）を空ける
            # キーボードの'q'が押されたら終了
            if cv2.waitKey(self.DELAY) & 0xFF == ord('q'):
                self.captured_img = frame
                break

    def get_img(self) -> np.ndarray | None:
        """最後にキャプチャされた画像を取得する。

        Returns:
            np.ndarray | None: キャプチャされた画像（BGR形式）。未取得の場合は None。
        """
        return self.captured_img

    def write_img(self, filepath: str = 'output_images/camera_capture.png') -> None:
        """キャプチャされた画像をファイルに保存する。

        Args:
            filepath (str, optional): 保存先のファイルパス。デフォルトは 'output_images/camera_capture.png'。

        Raises:
            ValueError: キャプチャ画像が存在しない場合。
        """
        if self.captured_img is None:
            raise ValueError("キャプチャ画像が存在しません。run()を実行してから保存してください。")

        cv2.imwrite(filepath, self.captured_img)

    def __del__(self) -> None:
        """終了処理。カメラリソースを解放し、OpenCVウィンドウを閉じる。"""
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    app = MyVideoCapture()
    app.run()
    app.write_img()
