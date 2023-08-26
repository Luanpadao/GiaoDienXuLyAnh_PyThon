import sys
from PyQt5.QtWidgets import QApplication,QMainWindow,QTableView, QStandardItemModel, QHeaderView
from PyQt5 import QtCore, QtGui, QtWidgets
import cv2
import numpy as np
import snap7
import snap7.client
from pyzbar import pyzbar
import time
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
import mysql.connector
from sc import Ui_MainWindow

class Uii_MainWindow:
    def __init__(self):
        # ------------------------------------------------------BẮT ĐẦU---------------------------------------------------
        global uic
        self.plc = snap7.client.Client()
        uic.ip_plc.setText('192.168.1.15')
        uic.bt_off.setVisible(False)
        uic.bt_disconnect.setVisible(False)
        uic.value_threshold.setText(str(uic.slider_threshold.value()))
        uic.sw_manual.setStyleSheet("background-color: blue")
        uic.bt_scan.setVisible(True)
        self.mode = 0
        uic.bt_scan.setDisabled(True)
        uic.sw_auto.setDisabled(True)
        uic.sw_manual.setDisabled(True)
        uic.content.setCurrentWidget(uic.page_home)
        uic.bt_home.setStyleSheet("background-color: blue")
        uic.title.setText('HOME')
        self.thread = {}
         # Thiết lập kết nối tới csdl MySQL
        self.mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="012321323Vn",
            database="python_project_1"
        )
        # Kiểm tra kết nối
        if self.mydb.is_connected():
            print("Kết nối thành công tới mysql!")
        else:
            print("Kết nối không thành công!")
        # Lấy danh sách thiết bị camera
        self.get_camera_list()
        # Kết nối sự kiện click của nút "on" với hàm xử lý
        uic.bt_on.clicked.connect(self.turnon_camera)
        uic.bt_off.clicked.connect(self.turnoff_camera)
        uic.bt_connect.clicked.connect(self.connect_plc)
        uic.bt_disconnect.clicked.connect(self.disconnect_plc)
        uic.slider_threshold.valueChanged.connect(self.value_slider_change)
        uic.value_threshold.returnPressed.connect(self.update_value_thresshold)
        uic.sw_manual.clicked.connect(lambda:self.change_mode(0))
        uic.sw_auto.clicked.connect(lambda:self.change_mode(1))
        uic.bt_scan.clicked.connect(self.event_scan)
        uic.bt_home.clicked.connect(lambda:self.change_screen(0))
        uic.bt_sc1.clicked.connect(lambda:self.change_screen(1))
        uic.bt_sc2.clicked.connect(lambda:self.change_screen(2))
        uic.bt_exit.clicked.connect(lambda:sys.exit(1))
        # ---------------------------------------------------------------------------------------------------------------
    def change_screen(self,number):
        if number == 0:
            uic.content.setCurrentWidget(uic.page_home)
            uic.title.setText('HOME')
            uic.bt_home.setStyleSheet("background-color: blue")
            uic.bt_sc1.setStyleSheet("background-color: #c1c1c1")
            uic.bt_sc2.setStyleSheet("background-color: #c1c1c1")
        elif number == 1:
            uic.content.setCurrentWidget(uic.page_sc2)
            uic.title.setText('Digital image processing')
            uic.bt_sc1.setStyleSheet("background-color: blue")
            uic.bt_home.setStyleSheet("background-color: #c1c1c1")
            uic.bt_sc2.setStyleSheet("background-color: #c1c1c1")
        elif number == 2:
            uic.content.setCurrentWidget(uic.page_sc3)
            uic.title.setText('TABLE')
            uic.bt_sc2.setStyleSheet("background-color: blue")
            uic.bt_home.setStyleSheet("background-color: #c1c1c1")
            uic.bt_sc1.setStyleSheet("background-color: #c1c1c1")
    def event_scan(self):
        self.read_qr_code(self.img_origin)
    def change_mode(self,value):
        if value == 0:          #manual
            uic.sw_manual.setStyleSheet("background-color: blue")
            uic.sw_auto.setStyleSheet("background-color:#c1c1c1")
            uic.bt_scan.setVisible(True)
            uic.lb_xla.clear()
            self.mode = 0
        else:                   #auto               
            uic.sw_auto.setStyleSheet("background-color: blue")
            uic.sw_manual.setStyleSheet("background-color:#c1c1c1")
            uic.bt_scan.setVisible(False)
            self.mode = 1

    def update_value_thresshold(self):
        uic.slider_threshold.setValue(int(uic.value_threshold.text()))
    def value_slider_change(self):
        uic.value_threshold.setText(str(uic.slider_threshold.value()))
    def get_camera_list(self):
        camera_list = []
        index = 0
        while True:
            # Thử mở camera với từng index cho đến khi không thể mở
            cap = cv2.VideoCapture(index)
            if not cap.isOpened():
                break
            else:
                # Lấy thông tin thiết bị camera và thêm vào danh sách
                camera_info = f"Camera {index}: {cap.getBackendName()}"
                camera_list.append(camera_info)
                cap.release()
            index += 1
        uic.camera.addItems(camera_list)
    def turnoff_camera(self):
        uic.bt_on.setVisible(True)
        uic.bt_off.setVisible(False)
        uic.camera.setDisabled(False)
        self.stop_capture_video()
    def turnon_camera(self):
        global camera_index 
        camera_index = uic.camera.currentIndex()
        print("Connecting camera " + str(camera_index) + "....")
        uic.bt_on.setVisible(False)
        uic.bt_off.setVisible(True)
        uic.camera.setDisabled(True)
        uic.bt_scan.setDisabled(False)
        uic.sw_auto.setDisabled(False)
        uic.sw_manual.setDisabled(False)
        self.start_capture_video()

    def start_capture_video(self):
        self.thread[1] = capture_video(index=1)
        self.thread[1].start()
        self.thread[1].signal.connect(self.show_webcam)
    def closeEvent(self, event):
        self.stop_capture_video()
        uic.lb_origin.clear()
        uic.lb_xla.clear()
    def stop_capture_video(self):
        self.thread[1].stop()
        uic.lb_origin.clear()
        uic.lb_xla.clear()
    def show_webcam(self,img):
        """Updates the image_label with a new opencv image"""
        rgb_image = self.convert_cv_qt(img)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(400, 300, QtCore.Qt.KeepAspectRatio)
        qt_img = QtGui.QPixmap.fromImage(p)
        uic.lb_origin.setPixmap(qt_img)
        self.show_xla(rgb_image)

    def show_xla(self,img):
        # img = self.convert_hsv(img)
        img = self.convert_gray(img)
        img = self.convert_to_binary(img,uic.slider_threshold.value())
        if self.mode == 1:
            img = self.read_qr_code(img)
            if (img.ndim == 2):
                h, w = img.shape
                bytes_per_line = w
            else:
                h, w, ch = img.shape
                bytes_per_line = ch * w
            convert_to_Qt_format = QtGui.QImage(img.data, w, h, bytes_per_line, QtGui.QImage.Format_Grayscale8)
            p = convert_to_Qt_format.scaled(400, 300, QtCore.Qt.KeepAspectRatio)
            qrcode_img = QtGui.QPixmap.fromImage(p)
            uic.lb_xla.setPixmap(qrcode_img)

    #------------------------------------------------------------Xử lý ảnh----------------------------------------------------------------
    def convert_cv_qt(self, cv_img):
        return cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

    def convert_hsv(self,img):
        return cv2.cvtColor(img,cv2.COLOR_RGB2HSV)
    
    def convert_gray(self,img):
        return cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    
    def convert_to_binary(self, img, threshold):
        _, binary_image = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
        return binary_image

    def read_qr_code(self,img):
        barcodes = pyzbar.decode(img)
        for barcode in barcodes:                #lấy thông tin từng barcode từ những barcodes
            (x,y,w,h) = barcode.rect                                #lay thong tin kích thước để vẽ hinh chu nhat
            cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,255),2)       #ve hinh chu nhat lên bức ảnh
            barcodeData = barcode.data.decode("utf-8")              #Lấy thông tin dữ liệu mà barcode mã hóa
            barcodeType = barcode.type                              #kiểu barcode
            # text = "{} - {} ".format(barcodeData,barcodeType)       #tổng hợp thông tin từ barcode vào biến text
            text = barcodeData
            print(text)                                             #in dữ liệu lấy được từ barcode lên terminal để xem
            uic.label_5.setText(text)
            myOutput = text
            myColor = (255,255,0)
            cv2.putText(img,myOutput,(x-10,y-10),cv2.FONT_HERSHEY_SIMPLEX,1,myColor,3)        #hiển thị chữ lên barcode trên ảnh
        return img

        #------------------------------------------------------------Kết thúc xử lý ảnh----------------------------------------------------------------
    def connect_plc(self):
        # Kết nối tới PLC S7-1200
        # self.plc = snap7.client.Client()
        ip = uic.ip_plc.text()
        if ip == "":
            print("Vui lòng nhập địa chỉ ip!")
        else:
            try:
                self.plc.connect(ip, 0, 1)
                print("Kết nối thành công tới PLC!")
                uic.bt_connect.setVisible(False)
                uic.bt_disconnect.setVisible(True)
                uic.ip_plc.setDisabled(True)
                self.start_plc()
            except Exception as e:
                print("Lỗi kết nối tới PLC:", str(e))
    def disconnect_plc(self):
        # Ngắt kết nối PLC
        try:
            self.thread[2].stop()
            self.plc.disconnect()
            print("Ngắt kết nối thành công!")
            uic.bt_connect.setVisible(True)
            uic.bt_disconnect.setVisible(False)
            uic.ip_plc.setDisabled(False)
        except Exception as e:
            print("Lỗi khi ngắt kết nối:", str(e))
    def start_plc(self):
        self.thread[2] = read_plc(index=2)
        self.thread[2].start()
        self.thread[2].signal.connect(self.plc_communication)
    
    # Ghi giá trị vào một biến trong PLC
    def write_plc_variable(self,variable_name, value):
        data = bytearray(snap7.util.get_real(value))
        self.plc.write_area(snap7.types.Areas.DB, 1, 0, data)  # Ghi 4 byte vào DB1, offset 0
        print(f'{variable_name} đã được ghi với giá trị: {value}')
    
    def plc_communication(self):
        print('alo')

class read_plc(QtCore.QThread):
    signal = QtCore.pyqtSignal(int)
    def __init__(self, ui , index = 0):
        self.main_win = main_win
    def __init__(self, index = 0):
        self.index = index
        print("start threading", self.index)
        super(read_plc, self).__init__()
    def run(self):
        while True:
            bool = self.read_plc_variable(1,'bool',1,78,3)              #Tag bool (DB: 1, ofset: 78.3)
            string = self.read_plc_variable(10,'string', 1, 66, 10)     #Tag string [10] (DB: 1, ofset: 66.0 )
            uic.label_4.setText(string)
            print('------------------------')
            print('Tag_bool: '+str(bool) +'\n'+'Tag_string: '+ string )
            print('------------------------')
            if(bool == True):
                cursor = main_win.mydb.cursor()
                # SELECT
                cursor.execute("SELECT * FROM pre_data")
                # Lấy tất cả các dòng dữ liệu từ kết quả truy vấn
                result = cursor.fetchall()
                for row in result:
                    column2_value = row[1]  # Cột 2 có chỉ số 1
                cursor.close()
                self.write_string_plc_variable(1,66,10,str(uic.label_5.text()))
                self.write_bool(1,78,3,False)
            time.sleep(1)

    def stop(self):
        print("stop threading", self.index)
        self.terminate()
        
        # Đọc giá trị từ một biến trong PLC
    def read_plc_variable(self, length, variable_name, DB, offset, address):
        data = main_win.plc.read_area(snap7.types.Areas.DB, DB, offset, length)  # Đọc dữ liệu từ DB
        if(length == 1):
            value = snap7.util.get_bool(data,0,address)         # Đọc tag là bool  
        elif(length > 1):  
            value = snap7.util.get_string(data,0)      # Đọc tag là chuỗi
        return value

    def write_string_plc_variable(self,db, start, size_string, string): 
        byte_array = bytearray(10)  # Khởi tạo bytearray với độ dài 10
        snap7.util.set_string(byte_array, 0, string, size_string )  # Chuyển đổi chuỗi thành bytearray
        main_win.plc.db_write(db, start, byte_array)  # Ghi bytearray vào PLC
        print("Đã ghi dữ liệu chuỗi vào PLC thành công.")
    
    def write_bool(self,db_num,start_byte,boolean_index,bool_value): #Bool yazma 
        data = bytearray(1)
        snap7.util.set_bool(data,0,boolean_index,bool_value)
        main_win.plc.db_write(db_num,start_byte,data)
    

class capture_video(QtCore.QThread):
    signal = QtCore.pyqtSignal(np.ndarray)
    def __init__(self, index):
        self.index = index
        print("start threading", self.index)
        super(capture_video, self).__init__()
    def run(self):
        global camera_index
        cap = cv2.VideoCapture(camera_index)
        while True:
            ret,img = cap.read()
            if ret:
                self.signal.emit(img)
    def stop(self):
        print("stop threading", self.index)
        self.terminate()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    uic = Ui_MainWindow()
    uic.setupUi(MainWindow)
    main_win = Uii_MainWindow()
    MainWindow.show()
    # class_plc = read_plc()
    # read_plc(main_win)
    # main_win.setupUi(MainWindow)
    # main_win.show()
    sys.exit(app.exec())
