import io, os, sys, pyperclip, pandas
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from pytesseract import pytesseract, Output
from plyer import notification

pytesseract.tesseract_cmd = os.path.expanduser("~") + r"\Desktop\Code\Python\tools\tesseract-ocr\tesseract.exe"


class Snipper(QtWidgets.QWidget):
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog)
        self.setWindowState(self.windowState() | Qt.WindowFullScreen)

        self.screen = QtWidgets.QApplication.screenAt(QtGui.QCursor.pos()).grabWindow(0)
        palette = QtGui.QPalette()
        palette.setBrush(self.backgroundRole(), QtGui.QBrush(self.screen))
        self.setPalette(palette)

        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))

        self.start, self.end = QtCore.QPoint(), QtCore.QPoint()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QtWidgets.QApplication.quit()
        return super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 100))
        painter.drawRect(0, 0, self.width(), self.height())

        if self.start == self.end:
            return super().paintEvent(event)

        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 3))
        painter.setBrush(painter.background())
        painter.drawRect(QtCore.QRect(self.start, self.end))
        return super().paintEvent(event)

    def mousePressEvent(self, event):
        self.start = self.end = event.pos()
        self.update()
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.start == self.end:
            return super().mouseReleaseEvent(event)

        self.hide()
        QtWidgets.QApplication.processEvents()
        shot = self.screen.copy(
            min(self.start.x(), self.end.x()),
            min(self.start.y(), self.end.y()),
            abs(self.start.x() - self.end.x()),
            abs(self.start.y() - self.end.y()),
        )
        processImage(shot)
        QtWidgets.QApplication.quit()


def processImage(img):
    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QBuffer.ReadWrite)
    img.save(buffer, "PNG")
    pil_img = Image.open(io.BytesIO(buffer.data()))
    buffer.close()
    custom_config = r"-c preserve_interword_spaces=1 --oem 1 --psm 1 -l eng+ukr+rus"
    df = pandas.DataFrame(pytesseract.image_to_data(pil_img, config=custom_config, output_type=Output.DICT))
    df1 = df[(df.conf != "-1") & (df.text != " ") & (df.text != "")]
    text = ""
    for block in df1.groupby("block_num").first().sort_values("top").index.tolist():
        curr = df1[df1["block_num"] == block]
        sel = curr[curr.text.str.len() > 3]
        char_w = (sel.width / sel.text.str.len()).mean()
        prev_par, prev_line, prev_left = 0, 0, 0
        text = ""
        for ix, ln in curr.iterrows():
            if prev_par != ln["par_num"]:
                text += "\n"
                prev_par = ln["par_num"]
                prev_line = ln["line_num"]
                prev_left = 0
            elif prev_line != ln["line_num"]:
                text += "\n"
                prev_line = ln["line_num"]
                prev_left = 0

            added = 0
            if ln["left"] / char_w > prev_left + 1:
                added = int((ln["left"]) / char_w) - prev_left
                text += " " * added
            text += ln["text"] + " "
            prev_left += len(ln["text"]) + added + 1
    if text:
        pyperclip.copy(text.strip())
        print(f'INFO: Copied "{text}" to the clipboard')
        notification.notify(
            title = "OCR Screenshot",
            message = f'INFO: Copied "{text}" to the clipboard',
        )


QtCore.QCoreApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QMainWindow()
snipper = Snipper(window)
snipper.show()
sys.exit(app.exec_())
