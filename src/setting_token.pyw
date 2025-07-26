import sys, pathlib, os
from api.db import update_secret, login, get_setting, update_setting
from api.youtube import re_auth, get_channel_name, get_stream_key, get_mac
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QCheckBox, QMessageBox
)
from PyQt6.QtGui import QFont, QGuiApplication
from PyQt6.QtCore import Qt, QTimer
from __init__ import __version__

class SettingUI(QWidget):

    def __init__(self): #초기화 코드
        super().__init__() #QWidget 초기화
        self.initUI() #UI 설정 코드를 불러옴

    def initUI(self):
        self.setWindowTitle('LiveKiosk 토큰 설정') #타이틀 설정
        self.resize(500,120) #화면 크기 설정
        self.move(710, 100) #창 위치 이동
        outer_ui = QVBoxLayout() #모든 것을 감싸는 레이아웃 생성
        self.setLayout(outer_ui) #그리고 그걸 메인 레이아웃으로 설정
        self.show() #화면을 보여줌
        self.LoginUI() #로그인 UI 호출

    def LoginUI(self): #맨 처음 UI 생성
        self.clearLayout(self.layout()) #화면 안의 내용을 전부 비움
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        self.layout().addLayout(layout) #그리고 그걸 레이아웃으로 설정

        # self.label_id = QLabel("아이디:")
        # self.input_id = QLineEdit()
        # layout.addWidget(self.label_id)
        # layout.addWidget(self.input_id)

        label_pw = QLabel("LiveKiosk 설치 시 설정한 비밀번호를 입력해주세요.")
        label_pw.setFont(QFont('Pretendard',12,500)) #버튼 폰트 설정
        self.input_pw = QLineEdit()
        self.input_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pw.returnPressed.connect(self.check_login)
        layout.addWidget(label_pw)
        layout.addWidget(self.input_pw)

        login_btn = QPushButton("로그인")
        login_btn.setFont(QFont('Pretendard',12,500)) #버튼 폰트 설정
        login_btn.setStyleSheet(f'border:1px solid black; background-color:#eee; border-radius: 10%;') #border, bgcolor 설정
        login_btn.clicked.connect(self.check_login)
        layout.addWidget(login_btn)

    def check_login(self):
        # user_id = self.input_id.text()
        pw = self.input_pw.text()

        if login(pw):
            self.gateUI()  # 로그인 성공 시
        else:
            QMessageBox.warning(
                self,
                "로그인 실패",
                "비밀번호가 틀렸습니다."
            )
            self.input_pw.clear()

    def gateUIAddButton(self, gate_ui:QVBoxLayout, name, desc, func,addSpace=True):
        button = QPushButton(name) #각 설정으로 전환되는 위젯 추가
        button.clicked.connect(func) #그 버튼을 클릭하면 각 설정의 UI가 호출됨
        button.setFont(QFont('Pretendard',18,500)) #버튼 폰트 설정
        button.setStyleSheet(f'border:1px solid black; background-color:#eee; border-radius: 10%;') #border, bgcolor 설정
        gate_ui.addWidget(button) #위젯 추가
        label = QLabel(desc) #설명 추가
        label.setFont(QFont('Pretendard',14,500)) #설명 폰트 설정
        label.setWordWrap(True) #자동 줄바꿈 설정
        gate_ui.addWidget(label) #위젯 추가
        if addSpace:
            gate_ui.addSpacing(10) #여백을 1만큼 추가

    def gateUI(self):
        self.clearLayout(self.layout()) #화면 안의 내용을 전부 비움
        QTimer.singleShot(0, lambda: self.resize(500,300))
        self.setFixedWidth(500)
        self.setMinimumWidth(120)
        gate_ui = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        self.layout().addLayout(gate_ui) #그리고 그걸 레이아웃으로 설정

        gate_ui.addStretch(1) #여백을 1만큼 추가
        title_label = QLabel('LiveKiosk 토큰 설정') #제목 추가
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter) #가운데 정렬
        title_label.setFont(QFont('Pretendard',30,500)) #폰트를 프리텐다드 5 Medium, 크기 30으로 설정
        gate_ui.addWidget(title_label) #제목을 UI에 추가
        gate_ui.addSpacing(20) #여백을 3만큼 추가

        self.gateUIAddButton(gate_ui,'client_secret 변경','발급받은 client_secret을 변경하실 수 있습니다.',lambda:self.SettingUILink(0))
        self.gateUIAddButton(gate_ui,'YouTube API 연동 설정','YouTube API를 다시 연동하실 수 있습니다. client_secret을 변경하신 후에는 꼭 다시 연동해주세요.',lambda:self.SettingUILink(1),addSpace=False)
        gate_ui.addStretch(1) #여백을 1만큼 추가

    def SettingUILink(self, ui:int):
        self.clearLayout(self.layout()) #화면 안의 내용을 전부 비움
        outerUILayout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        self.layout().addLayout(outerUILayout) #그리고 그걸 레이아웃으로 설정

        ## TODO : 저장하고 뒤로 버튼 추가
        headerUILayout = QHBoxLayout()
        outerUILayout.addLayout(headerUILayout)

        back_button = QPushButton('< 저장하고 뒤로')
        back_button.setFont(QFont('Pretendard',14,500)) #버튼 폰트 설정
        back_button.setStyleSheet(f'border:1px solid black; background-color:#eee; border-radius: 10%;') #border, bgcolor 설정
        back_button.setFixedWidth(180)
        back_button.clicked.connect(lambda:self.gateUILink(ui))
        back_button.setMaximumHeight(30)
        headerUILayout.addWidget(back_button)

        menu_label = QLabel('현재 메뉴')
        menu_label.setAlignment(Qt.AlignmentFlag.AlignRight) #가운데 정렬
        menu_label.setFont(QFont('Pretendard',14,500)) #폰트를 프리텐다드 5 Medium, 크기 30으로 설정
        menu_label.setMaximumHeight(30)
        headerUILayout.addWidget(menu_label)

        desc_label = QLabel('설명')
        desc_label.setFont(QFont('Pretendard',12,500)) #폰트를 프리텐다드 5 Medium, 크기 30으로 설정
        desc_label.setWordWrap(True)
        outerUILayout.addWidget(desc_label)

        outerUILayout.addStretch(1)

        match ui:
            case 0:
                menu_label.setText('client_secret 변경')
                desc_label.setText('발급받은 client_secret을 변경하실 수 있습니다.')
                self.SettingUI1(outerUILayout)
            case 1:
                menu_label.setText('YouTube API 연동 설정')
                desc_label.setText('YouTube API와 스트림 키의 연동 상태를 확인하시거나, 다시 연동하실 수 있습니다. client_secret을 변경하신 후에는 꼭 다시 연동해주세요.')
                self.SettingUI2(outerUILayout)
        outerUILayout.addStretch(1)

    def gateUILink(self, ui:int): ## 저장하고 뒤로 나갈 때 쓰는 함수

        match ui:
            case 0:
                secret_text = self.secret_box.toPlainText()
                if secret_text.startswith('{"installed":'):
                    update_secret(secret_text)
                    self.gateUI()
                elif secret_text == '':
                    self.gateUI()
                else:
                    QMessageBox.warning(
                        self,
                        "변경 실패",
                        "데스크톱 유형의 client_secret이 아닌 것 같습니다. 뒤로 나가시려면 입력 칸을 비워주세요."
                    )
                    self.secret_box.clear()
            case 1:
                self.gateUI()


    def addSettingIndex_Title(self, title):
        title_label = QLabel(title)
        title_label.setFont(QFont('Pretendard',18,500)) #설명 폰트 설정
        title_label.setWordWrap(True) #자동 줄바꿈 설정
        return title_label

    def addSettingIndex_Desc(self, desc):
        desc_label = QLabel(desc)
        desc_label.setFont(QFont('Pretendard',12,500)) #설명 폰트 설정
        desc_label.setWordWrap(True) #자동 줄바꿈 설정
        return desc_label

    def addSettingIndex_TextMultiLine(self, layout:QVBoxLayout, title, desc, default):
        layout.addWidget(self.addSettingIndex_Title(title)) #위젯 추가

        input_box = QTextEdit()
        input_box.setFont(QFont('Pretendard',12,500))
        input_box.setText(default)
        layout.addWidget(input_box)

        layout.addWidget(self.addSettingIndex_Desc(desc))
        return input_box

    def SettingUI1(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []
        self.secret_box : QTextEdit = self.addSettingIndex_TextMultiLine(layout,'client_secret 내용 입력','발급받으신 client_secret.json의 내용을 전부 붙여넣기해주세요. (메모장에서 Ctrl+A로 전체 선택 후 Ctrl+C로 복사, 위의 입력 칸 클릭 후 Ctrl+V로 붙여넣기)','')
        QTimer.singleShot(0, lambda: self.resize(500, 300))

    def SettingUI2(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []

        layout.addWidget(self.addSettingIndex_Title('YouTube API 다시 연동하기'))
        button = QPushButton('Google 계정으로 로그인') #각 설정으로 전환되는 위젯 추가
        button.clicked.connect(self.re_auth) #그 버튼을 클릭하면 각 설정의 UI가 호출됨
        button.setFont(QFont('Pretendard',14,500)) #버튼 폰트 설정
        button.setStyleSheet(f'border:1px solid black; background-color:#eee; border-radius: 10%;') #border, bgcolor 설정
        button.setFixedWidth(250)
        layout.addWidget(button) #위젯 추가

        QTimer.singleShot(0, lambda: self.resize(500, 300))

    def re_auth(self):
        credentials = re_auth()
        if credentials is not None:
            channel_name = get_channel_name(credentials)
            channel_stream_key = get_stream_key(credentials)
            update_setting('channel_name',channel_name)
            update_setting('channel_stream_key',channel_stream_key)
            QMessageBox.information(self,"연동 완료",f"{channel_name} 채널로 연동을 완료했습니다.")
        else:
            QMessageBox.warning(self,"연동 오류","client_secret이 입력되지 않았습니다. client_secret 변경 메뉴에서 client_secret을 입력하신 후, 다시 한 번 연동해 주십시오.")

    # ref : https://stackoverflow.com/questions/9374063/remove-all-items-from-a-layout/9383780#9383780
    def clearLayout(self, layout):
        if layout is not None: #레이아웃이 비어있지 않으면
            while layout.count(): #레이아웃 수가 0 초과인 경우 반복
                item = layout.takeAt(0) #맨 위의 아이템을 가지고 오고
                widget = item.widget() #그 안에 위젯을 가지고 옴
                if widget is not None: #만약 위젯이 있으면
                    widget.deleteLater() #삭제
                else: #아니라면
                    self.clearLayout(item.layout()) #레이아웃을 삭제함

if __name__ == "__main__":
    sys.argv += ['-platform', 'windows:darkmode=1']
    app = QApplication(sys.argv)
    # 현재 시스템 컬러 테마 가져오기 (Qt 6.5+)
    color_scheme = QGuiApplication.styleHints().colorScheme()
    if color_scheme == Qt.ColorScheme.Dark:
        app.setStyle("fusion")  # 다크모드면 fusion 스타일 적용
    window = SettingUI()
    window.show()
    sys.exit(app.exec())
