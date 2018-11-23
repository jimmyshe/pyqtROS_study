
import roslibpy
from twisted.internet import reactor
import base64
import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from mainwindow import Ui_MainWindow


class RosThread(QThread):
    text_signal = pyqtSignal(str)
    img_signal = pyqtSignal(QPixmap)

    def __init__(self):
        QThread.__init__(self)
        self.ros = roslibpy.Ros(host='192.168.1.164', port=9090)
        self.camera_topic = roslibpy.Topic(self.ros, name='/camera/color/image_raw/compressed',
                                      message_type='sensor_msgs/CompressedImage')
        self.camera_topic.subscribe(self.image_cb)
        self.ros.on_ready(self.connected_cb)


    # run method gets called when we start the thread
    def run(self):
        reactor.run(installSignalHandlers=False)

    def image_cb(self,img_msg):
        imgbase64str = img_msg['data']
        decodedStr = base64.b64decode(imgbase64str)
        img = QImage()
        assert img.loadFromData(decodedStr)
        pix = QPixmap.fromImage(img)
        self.img_signal.emit(pix)


    def connected_cb(self):
        self.text_signal.emit(str({'Ok': True}))


class ExampleApp(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):
        super(ExampleApp, self).__init__(parent)
        self.setupUi(self)
        self.setupRos()

    def setupRos(self):
        self.ros_thread = RosThread()  # This is the thread object
        self.ros_thread.text_signal.connect(self.show_text)
        self.ros_thread.img_signal.connect(self.show_img)
        self.ros_thread.start()

    def show_img(self,img):
        self.label.setPixmap(img)


    def show_text(self, result):
        self.textEdit.setText("{0}".format(result))  # Show the output to the user


def main():
    app = QtWidgets.QApplication(sys.argv)
    form = ExampleApp()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
