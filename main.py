
import roslibpy
from roslibpy import actionlib
from twisted.internet import reactor
import base64
import sys
from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QMessageBox

from mainwindow import Ui_MainWindow


class RosThread(QThread):
    text_signal = pyqtSignal(str)
    img_signal = pyqtSignal(QPixmap)

    def __init__(self):
        QThread.__init__(self)
        self.ros = roslibpy.Ros(host='localhost', port=9090)
        self.camera_topic = roslibpy.Topic(self.ros, name='/camera/image_raw/compressed',
                                      message_type='sensor_msgs/CompressedImage')
        self.camera_topic.subscribe(self.image_cb)

        self.navi_goal_client = roslibpy.actionlib.ActionClient(self.ros, server_name="/move_base",
                                                 action_name="move_base_msgs/MoveBaseAction")

        self.ros.on_ready(lambda:
                          self.text_signal.emit(str({'Ok': True}))
                          )

    def run(self):
        reactor.run(installSignalHandlers=False)

    def image_cb(self, img_msg):
        imgbase64str = img_msg['data']
        decodedStr = base64.b64decode(imgbase64str)
        img = QImage()
        assert img.loadFromData(decodedStr)
        pix = QPixmap.fromImage(img)
        self.img_signal.emit(pix)

    def navi_go(self, x, y):
        self.text_signal.emit(str(x)+" "+str(y))

        val = {'target_pose':
                   {'header':
                        {'stamp':
                             {'secs': 0, 'nsecs': 0},
                         'frame_id':
                             'map', 'seq': 0},
                    'pose':
                        {'position': {'y': 1, 'x': 1, 'z': 0.0},
                         'orientation':
                             {'y': 0.0, 'x': 0.0, 'z': 0.0, 'w': 1.0}}}}
        val['target_pose']['pose']['position']['x'] = x
        val['target_pose']['pose']['position']['y'] = y
        val['target_pose']['pose']['orientation']['x'] = 0
        val['target_pose']['pose']['orientation']['y'] = 0
        val['target_pose']['pose']['orientation']['z'] = 0
        val['target_pose']['pose']['orientation']['w'] = 1

        goal = roslibpy.actionlib.Goal(self.navi_goal_client, roslibpy.Message(values=val))
        goal.on('feedback', lambda feedback:
                self.text_signal.emit(str(goal.status) + str(feedback))
                )
        goal.on('result', lambda result: self.text_signal.emit((str(goal.status) + str(goal.feedback)+"到了")))

        # goal.on('timeout', lambda: self.text_signal.emit("TimeOut"))

        goal.send(timeout=100)

    def cancel_goal(self):
        self.navi_goal_client.cancel()

class ExampleApp(QtWidgets.QMainWindow, Ui_MainWindow):
    navi_go_signal = pyqtSignal(float,float)

    def __init__(self, parent=None):
        super(ExampleApp, self).__init__(parent)
        self.setupUi(self)
        self.setup_ros()
        self.setup_signal()

    def setup_ros(self):
        self.ros_thread = RosThread()  # This is the thread object
        self.ros_thread.text_signal.connect(self.show_text)
        self.ros_thread.img_signal.connect(self.show_img)
        self.ros_thread.start()

    def setup_signal(self):
        self.pushButton_go.clicked.connect(self.go_button_handle)
        self.navi_go_signal.connect(self.ros_thread.navi_go)
        self.pushButton_cancel.clicked.connect(self.ros_thread.cancel_goal)

    def show_img(self,img):
        self.label.setPixmap(img)

    def show_text(self, result):
        self.textEdit.setText("{0}".format(result))  # Show the output to the user

    def go_button_handle(self):
        flag = True
        try:
            x = float(self.lineEdit_x.text())
            y = float(self.lineEdit_y.text())
            self.navi_go_signal.emit(x, y)
        except ValueError:
            QMessageBox.warning(self,'输入不合法','请确认输入的坐标格式', QMessageBox.Ok)

def main():
    app = QtWidgets.QApplication(sys.argv)
    form = ExampleApp()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
