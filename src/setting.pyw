from api.db import (update_operation_times, fetch_operation_times, update_restart_times, fetch_restart_times, login, get_setting, get_secret,
                    update_setting, update_secret, getOBSProfiles, getOBSScenes, db_exist, getTimeCode, getWeekdayCode, getTimeStamp)
from api.db import __update_pw as update_pw
from api.db import _create_db as create_db
if not db_exist():
    create_db()

import sys, pathlib, os
from api.youtube import re_auth, get_channel_name, get_stream_key, get_mac
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QFileDialog, QButtonGroup, QScrollArea,
    QPushButton, QTableWidget, QTableWidgetItem, QCheckBox, QHeaderView, QTimeEdit, QMessageBox, QComboBox, QRadioButton
)
from PyQt6.QtGui import QFont, QGuiApplication, QIntValidator
from PyQt6.QtCore import Qt, QTimer
from __init__ import __version__

# class InstallUI(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setting_ui = SettingUI()  # 또는 해당 코드의 설정 화면 생성 기능만 분리해도 됨
#         self.current_step = 0
#         self.steps = [
#             self.show_set_password,
#             self.setting_ui.SettingUI8,
#             self.setting_ui.SettingUI1,
#             self.setting_ui.SettingUI2,
#             self.setting_ui.SettingUI3,
#             self.setting_ui.SettingUI4,
#             self.setting_ui.SettingUI5,
#             self.setting_ui.SettingUI6,
#             self.setting_ui.SettingUI9
#         ]
#         self.next_step()

#     def next_step(self):
#         if self.current_step < len(self.steps):
#             self.clearLayout(self.layout())
#             self.steps[self.current_step](self.layout())
#             # “다음” 버튼에 self.next_step 연결
#             self.current_step += 1

#     def show_set_password(self, layout):
#         # 새로운 비밀번호 설정 UI 구현
#         # 완료 시 self.next_step() 호출
#         pass 


class SettingUI(QWidget):

    def __init__(self): #초기화 코드
        super().__init__() #QWidget 초기화
        self.steps = [
            [self.SettingUI8,'client_secret 설정','발급받은 client_secret을 입력해주세요. 만약 초기 설정 중에 프로그램이 다운되었고 이미 저장된 client_secret이 있는 경우, 다음으로 넘어가셔도 됩니다.',8],
            [self.SettingUI4_1,'YouTube API 연동 설정','LiveKiosk에서 사용하실 YouTube API와 스트림 키를 연동하실 수 있습니다.',4],
            [self.SettingUI9,'OBS 프로파일, 장면 변경','OBS Studio에서 사용하고 있는 프로파일과 장면을 선택해 주세요. 현재 사용중인 프로파일과 장면은 OBS Studio의 제목 표시줄에 표시됩니다.',9],
            [self.SettingUI1,'점포명, 기기명 설정','LiveKiosk 프로그램 내외부와 스트리밍의 제목, 설명에 표시되는 점포명과 기기명을 설정하실 수 있습니다.',1],
            [self.SettingUI0,'영업시간 설정','영업시간을 설정하실 수 있습니다. LiveKiosk를 이용하면 영업시간에 맞춰 컴퓨터를 종료하실 수 있습니다.',0],
            [self.SettingUI2,'LiveKiosk 기본 기능 설정','자동 종료 기능, 녹화 파일 자동 삭제 기능과 관련된 설정을 하실 수 있습니다.',2],
            [self.SettingUI3,'스트리밍 설정','스트리밍 자동 생성 기능을 켜고 끄거나, 제목과 설명을 설정하실 수 있습니다.',3],
            [self.SettingUI5,'스트리밍 재시작 기능 설정','스트리밍 재시작 모드와 주기를 설정하실 수 있습니다.',5],
            [self.SettingUI6,'OBS Studio 관련 설정','OBS 프로파일 초기화 기능, OBS Studio 위젯과 관련된 설정을 하실 수 있습니다.',6],
            [self.InstallFinishedUI,'초기 설정 완료','축하드립니다. 이제 LiveKiosk를 사용할 준비가 되었습니다.',10]
        ] #초기 설정 단계
        self.initUI()#UI 설정 코드를 불러옴

    def initUI(self):
        self.setWindowTitle('LiveKiosk 설정') #타이틀 설정
        self.resize(500,120) #화면 크기 설정
        self.move(710, 100) #창 위치 이동
        outer_ui = QVBoxLayout() #모든 것을 감싸는 레이아웃 생성
        self.setLayout(outer_ui) #그리고 그걸 메인 레이아웃으로 설정
        self.layout().setContentsMargins(10, 10, 10, 10)
        self.show() #화면을 보여줌
        self.current_step = 0 # 초기 설정 step
        if get_setting('setting_finished') == '1':
            self.mode = 0
            self.LoginUI() #로그인 UI 호출
        elif get_setting('pw') != '':
            self.mode = 1
            self.LoginUI() #로그인 UI 호출
        else:
            self.mode = 1
            self.SettingUI7_1(outer_ui)
         

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
            if self.mode == 0:
                self.gateUI()  # 로그인 성공 시
            else:
                self.InstallUI()
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
        QTimer.singleShot(0, lambda: self.resize(500,750))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setFixedWidth(500)
        self.setMinimumWidth(120)
        content_widget = QWidget()
        gate_ui = QVBoxLayout(content_widget) #VBoxLayout (세로 방향 박스형 레이아웃) 생성

        gate_ui.addStretch(1) #여백을 1만큼 추가
        title_label = QLabel('LiveKiosk 설정') #제목 추가
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter) #가운데 정렬
        title_label.setFont(QFont('Pretendard',30,500)) #폰트를 프리텐다드 5 Medium, 크기 30으로 설정
        gate_ui.addWidget(title_label) #제목을 UI에 추가
        gate_ui.addSpacing(20) #여백을 3만큼 추가

        self.gateUIAddButton(gate_ui,'영업시간 설정','영업시간을 변경하실 수 있습니다.',lambda:self.SettingUILink(0))
        self.gateUIAddButton(gate_ui,'점포명, 기기명 설정','초기화 화면, OBS 화면과 스트리밍 제목/설명에 표시되는 점포와 기기의 이름을 변경하실 수 있습니다.',lambda:self.SettingUILink(1))
        #self.gateUIAddButton(gate_ui,'녹화 파일 자동 삭제 기능 설정','녹화 파일 자동 삭제 기능을 켜고 끄시거나, 녹화 파일 자동 삭제 기간과 폴더 위치를 변경하실 수 있습니다.',self.SettingUI1)
        self.gateUIAddButton(gate_ui,'LiveKiosk 기본 기능 설정','자동 종료 기능, 녹화 파일 자동 삭제 기능과 관련된 설정을 하실 수 있습니다.',lambda:self.SettingUILink(2))
        self.gateUIAddButton(gate_ui,'스트리밍 설정','스트리밍 자동 생성 기능을 켜고 끄거나, 제목과 설명을 변경하실 수 있습니다.',lambda:self.SettingUILink(3))
        self.gateUIAddButton(gate_ui,'YouTube API 연동 설정','YouTube API와 스트림 키의 연동 상태를 확인하시거나, 다시 연동하실 수 있습니다.',lambda:self.SettingUILink(4))
        self.gateUIAddButton(gate_ui,'스트리밍 재시작 기능 설정','스트리밍 재시작 모드와 주기를 변경하실 수 있습니다.',lambda:self.SettingUILink(5))
        self.gateUIAddButton(gate_ui,'OBS Studio 관련 설정','OBS Studio와 관련된 설정을 하실 수 있습니다.',lambda:self.SettingUILink(6))
        self.gateUIAddButton(gate_ui,'정보, 비밀번호 변경','LiveKiosk의 정보를 확인하시거나, 비밀번호를 변경하실 수 있습니다.',lambda:self.SettingUILink(7))
        gate_ui.addWidget(self.addSettingIndex_Title('환경 변수 설정'))
        gate_ui.addWidget(self.addSettingIndex_Desc('아래의 설정은 특별한 일이 없는 경우 변경하지 않는 것을 추천드립니다.'))
        self.gateUIAddButton(gate_ui,'client_secret 변경','발급받은 client_secret을 변경하실 수 있습니다.',lambda:self.SettingUILink(8))
        self.gateUIAddButton(gate_ui,'OBS 프로파일, 장면 변경','OBS Studio에서 사용하고 있는 프로파일과 장면을 선택할 수 있습니다.',lambda:self.SettingUILink(9),addSpace=False)
        gate_ui.addStretch(1) #여백을 1만큼 추가

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)
        self.layout().addWidget(scroll_area) #그리고 그걸 레이아웃으로 설정

    def SettingUILink(self, ui:int):
        self.clearLayout(self.layout()) #화면 안의 내용을 전부 비움
        outerUILayout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        self.layout().addLayout(outerUILayout) #그리고 그걸 레이아웃으로 설정
        self.layout().setContentsMargins(10, 10, 10, 10)

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
                menu_label.setText('영업시간 설정')
                desc_label.setText('영업시간을 변경하실 수 있습니다.')
                self.SettingUI0(outerUILayout)
            case 1:
                menu_label.setText('점포명, 기기명 설정')
                desc_label.setText('LiveKiosk 프로그램 내외부와 스트리밍의 제목, 설명에 표시되는 점포명과 기기명을 변경하실 수 있습니다.')
                self.SettingUI1(outerUILayout)
            case 2:
                menu_label.setText('LiveKiosk 기본 기능 설정')
                desc_label.setText('자동 종료 기능, 녹화 파일 자동 삭제 기능과 관련된 설정을 하실 수 있습니다.')
                self.SettingUI2(outerUILayout)
            case 3:
                menu_label.setText('스트리밍 설정')
                desc_label.setText('스트리밍 자동 생성 기능을 켜고 끄거나, 제목과 설명을 변경하실 수 있습니다.')
                self.SettingUI3(outerUILayout)
            case 4:
                menu_label.setText('YouTube API 연동 설정')
                desc_label.setText('YouTube API와 스트림 키의 연동 상태를 확인하시거나, 다시 연동하실 수 있습니다.')
                self.SettingUI4(outerUILayout)
            case 5:
                menu_label.setText('스트리밍 재시작 기능 설정')
                desc_label.setText('스트리밍 재시작 모드와 주기를 변경하실 수 있습니다.')
                self.SettingUI5(outerUILayout)
            case 6:
                menu_label.setText('OBS Studio 관련 설정')
                desc_label.setText('OBS 프로파일 초기화 기능, OBS Studio 위젯과 관련된 설정을 하실 수 있습니다.')
                self.SettingUI6(outerUILayout)
            case 7:
                menu_label.setText('정보, 비밀번호 변경')
                desc_label.setText('LiveKiosk의 정보를 확인하시거나, 비밀번호를 변경하실 수 있습니다.\n※ 비밀번호는 \'저장하고 뒤로\' 버튼으로는 변경되지 않습니다. 반드시 비밀번호 변경 버튼을 눌러주세요.')
                self.SettingUI7(outerUILayout)
            case 8:
                menu_label.setText('client_secret 변경')
                desc_label.setText('발급받은 client_secret을 변경하실 수 있습니다. client_secret을 변경하신 후에는 YouTube API를 꼭 다시 연동해주세요. 만약 변경하고 싶지 않은 경우, 입력칸을 비운 채로 \'저장하고 뒤로\' 버튼을 클릭하면 저장되지 않고 뒤로 나가집니다.')
                self.SettingUI8(outerUILayout)
            case 9:
                menu_label.setText('OBS 프로파일, 장면 변경')
                desc_label.setText('OBS Studio에서 사용하고 있는 프로파일과 장면을 선택해 주세요. 현재 사용중인 프로파일과 장면은 OBS Studio의 제목 표시줄에 표시됩니다. 프로파일이 LiveKiosk로 표시되는 경우, \'파일 > 프로파일 폴더 보기\'를 클릭하면 나오는 폴더의 이름을 선택하시면 됩니다.')
                self.SettingUI9(outerUILayout)
        outerUILayout.addStretch(1)

    def gateUILink(self, ui:int): ## 저장하고 뒤로 나갈 때 쓰는 함수
        go_gate = True

        match ui:
            case 0:
                self.changeTime()
            case 1:
                update_setting('center_name',self.inputBox[0].text())
                update_setting('device_name',self.inputBox[1].text())
                update_setting('stream_center',self.inputBox[2].text())
                update_setting('stream_device',self.inputBox[3].text())
            case 2:
                update_setting('shutdown_enabled','1' if self.checkBox[0].isChecked() else '0')
                update_setting('record_delete_enabled','1' if self.checkBox[1].isChecked() else '0')
                update_setting('record_loc',self.selected_dir)
                update_setting('record_delete_dur',self.inputBox[0].text())
            case 3:
                update_setting('stream_autocreate_enabled','1' if self.checkBox[0].isChecked() else '0')
                update_setting('stream_title',self.inputBox[0].text())
                update_setting('stream_desc',self.inputBox[1].toPlainText())
            case 5:
                update_setting('stream_autorestart_enabled',str(self.checkBox[0].currentIndex()))
                update_setting('stream_autorestart_dur',self.inputBox[0].text())
                self.changeTime2()
            case 6:
                update_setting('obs_renew_enabled','1' if self.checkBox[0].isChecked() else '0')
                update_setting('obs_record_button_enabled','1' if self.checkBox[1].isChecked() else '0')
                update_setting('streamkey_renew_enabled','1' if self.checkBox[2].isChecked() else '0')
                update_setting('obs_widget_information',self.inputBox[0].toPlainText())
            case 8:
                secret_text = self.secret_box.toPlainText()
                if secret_text.startswith('{"installed":'):
                    update_secret(secret_text)
                    update_setting('channel_name','※ 다시 연동 필요 ※')
                elif secret_text != '':
                    go_gate = False
                    QMessageBox.warning(self, "변경 실패",
                        "데스크톱 유형의 client_secret이 아닌 것 같습니다. 뒤로 나가시려면 입력 칸을 비워주세요.")
                    self.secret_box.clear()
            case 9:
                update_setting('obs_renew_pf_dir',self.obs_profile_sel.currentText())
                update_setting('obs_renew_scene_dir',self.obs_scene_sel.currentText())
                update_setting('obs_path',self.selected_dir)

        if self.mode == 0 and go_gate:
            self.gateUI()

    def setting4Link(self):
        secret_text = self.secret_box.toPlainText()
        if secret_text.startswith('{"installed":'):
            update_secret(secret_text)
            update_setting('channel_name','※ 다시 연동 필요 ※')
            self.SettingUILink(4)
        elif secret_text == '':
            QMessageBox.warning(
                self,
                "변경 실패",
                "데스크톱 유형의 client_secret이 아닌 것 같습니다. 단순히 YouTube API를 다시 연동하고 싶으신 경우라면, 오류를 방지하기 위해 메인 메뉴를 통해 이동해주세요."
            )
        else:
            QMessageBox.warning(
                self,
                "변경 실패",
                "데스크톱 유형의 client_secret이 아닌 것 같습니다. 올바른 값이 입력되지 않은 경우, 정상적인 연동이 불가능합니다. 단순히 YouTube API를 다시 연동하고 싶으신 경우라면, 오류를 방지하기 위해 메인 메뉴를 통해 이동해주세요."
            )
            self.secret_box.clear()

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

    def addSettingIndex_TextSingleLine(self, layout:QVBoxLayout, title, desc, default):
        layout.addWidget(self.addSettingIndex_Title(title)) #위젯 추가

        input_box = QLineEdit()
        input_box.setFont(QFont('Pretendard',12,500))
        input_box.setText(default)
        layout.addWidget(input_box)

        layout.addWidget(self.addSettingIndex_Desc(desc))
        return input_box

    def addSettingIndex_TextMultiLine(self, layout:QVBoxLayout, title, desc, default):
        layout.addWidget(self.addSettingIndex_Title(title)) #위젯 추가

        input_box = QTextEdit()
        input_box.setFont(QFont('Pretendard',12,500))
        input_box.setText(default)
        layout.addWidget(input_box)

        layout.addWidget(self.addSettingIndex_Desc(desc))
        return input_box

    def addSettingIndex_Dropdown(self, layout:QVBoxLayout, title, desc, list, default):
        layout.addWidget(self.addSettingIndex_Title(title)) #위젯 추가

        input_box = QComboBox()
        input_box.addItems(list)
        input_box.setFont(QFont('Pretendard',12,500))
        input_box.setCurrentIndex(int(default))
        layout.addWidget(input_box)

        layout.addWidget(self.addSettingIndex_Desc(desc))
        return input_box

    def addSettingIndex_CheckBox(self, layout:QVBoxLayout, title, desc, default):
        input_box = QCheckBox(title)
        input_box.setFont(QFont('Pretendard',18,500))
        input_box.setChecked(default != '0')
        layout.addWidget(input_box)

        layout.addWidget(self.addSettingIndex_Desc(desc))
        return input_box

    def addSettingIndex_int(self, layout:QVBoxLayout, title, desc, default):
        layout.addWidget(self.addSettingIndex_Title(title)) #위젯 추가

        input_box = QLineEdit()
        input_box.setFont(QFont('Pretendard',12,500))
        input_box.setText(default)
        input_box.setValidator(QIntValidator())
        layout.addWidget(input_box)

        layout.addWidget(self.addSettingIndex_Desc(desc))
        return input_box

    def addSettingIndex_DirDrawer(self, layout:QVBoxLayout, title, desc, default):
        layout.addWidget(self.addSettingIndex_Title(title)) #위젯 추가

        select_label = QLabel(default)
        select_label.setFont(QFont('Pretendard',12,500))
        select_label.setText(default)
        layout.addWidget(select_label)
        self.selected_dir = default
        self.select_label = select_label

        select_button = QPushButton('폴더 선택')
        select_button.setFont(QFont('Pretendard',14,500)) #버튼 폰트 설정
        select_button.setStyleSheet(f'border:1px solid black; background-color:#eee; border-radius: 10%;') #border, bgcolor 설정
        select_button.setFixedWidth(100)
        select_button.clicked.connect(self.dirDrawerBridge)
        layout.addWidget(select_button)

        layout.addWidget(self.addSettingIndex_Desc(desc))
    
    def dirDrawerBridge(self):
        options = QFileDialog.Option.ShowDirsOnly
        if not pathlib.Path(self.selected_dir).is_dir():
            self.selected_dir = ''
        folder = QFileDialog.getExistingDirectory(self, '폴더를 선택해주세요.',self.selected_dir,options)
        if folder:
            self.selected_dir = folder
            self.select_label.setText(folder)

    def SettingUI0(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정

        layout.addWidget(self.addSettingIndex_Desc('※ 꼭 읽어주세요 ※\n자동 종료 기능을 활성화한 경우, 설정된 영업시간이 아니면 PC가 종료됩니다. PC 시간에 오차가 있을 수 있기 때문에, 실제 영업시간보다 5분 정도 여유롭게 설정해 주시기 바랍니다.\nYouTube와의 안전한 통신 종료를 위해, 스트리밍은 설정된 영업 종료시간보다 2분 일찍 종료됩니다.\n만약 타이머 콘센트, IoT 멀티탭 등을 이용해 영업 종료 후 PC 전원을 차단하는 경우, 영업 종료시간을 전원 차단 시간보다 5~10분 정도 일찍 설정하거나 PC의 전원 차단 시간을 5~10분 정도 늦춰 주세요. 시스템이 완전히 종료되기 전에 PC의 전원이 차단되는 경우, 하드 디스크와 Windows의 핵심 구성 요소(레지스트리 등)에 심각한 손상이 일어날 수 있습니다.'))

        # 표를 추가합니다.
        self.table = QTableWidget()
        self.table.setFixedSize(480,250)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["요일", "운영 시작 시간", "운영 종료 시간"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.load_table_data()

        layout.addWidget(self.table)
        
        # 변경할 수 있는 UI를 추가합니다.
        self.week_checkboxes = []
        week_layout = QHBoxLayout()
        week_labels = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        for i, label in enumerate(week_labels):
            checkbox = QCheckBox(label)
            self.week_checkboxes.append(checkbox)
            week_layout.addWidget(checkbox)
        
        layout.addLayout(week_layout)

        # 운영 시작 시간 입력
        time_layout = QHBoxLayout()
        self.start_time_checkbox = QCheckBox("운영 시작 시간:")
        time_layout.addWidget(self.start_time_checkbox)
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat('hh:mm')
        time_layout.addWidget(self.start_time_edit)

        # 운영 종료 시간 입력
        self.end_time_checkbox = QCheckBox("운영 종료 시간:")
        time_layout.addWidget(self.end_time_checkbox)
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat('hh:mm')
        time_layout.addWidget(self.end_time_edit)

        layout.addLayout(time_layout)

        # 변경 버튼
        self.change_button = QPushButton("변경")
        self.change_button.clicked.connect(self.changeTime)
        layout.addWidget(self.change_button)

        QTimer.singleShot(0, lambda: self.resize(500, 700))

    def SettingUI1(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []

        self.inputBox.append(self.addSettingIndex_TextSingleLine(layout,'점포명','초기화 화면, OBS Studio 위젯 등에 표시되는 점포명을 입력해 주세요.',get_setting('center_name')))
        layout.addSpacing(20)

        self.inputBox.append(self.addSettingIndex_TextSingleLine(layout,'기기명','초기화 화면, OBS Studio 위젯 등에 표시되는 기기명을 입력해 주세요.\n점포명과 기기명은 단순 화면 표시용이므로, 개인 소유 기기 등인 경우 입력하지 않으셔도 무방합니다.',get_setting('device_name')))
        layout.addSpacing(20)

        self.inputBox.append(self.addSettingIndex_TextSingleLine(layout,'스트리밍에 표시되는 점포명','스트리밍의 제목과 설명에 표시되는 점포명을 입력해 주세요.',get_setting('stream_center')))
        layout.addSpacing(20)

        self.inputBox.append(self.addSettingIndex_TextSingleLine(layout,'스트리밍에 표시되는 기기명','스트리밍의 제목과 설명에 표시되는 기기명을 입력해 주세요.\n점포명은 {center}, 기기명은 {device}를 스트리밍 제목과 설명에 입력한 경우에만 표시되며, 표시를 원하지 않으시는 경우 입력하지 않으셔도 무방합니다.',get_setting('stream_device')))

    def SettingUI2(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []

        self.checkBox.append(self.addSettingIndex_CheckBox(layout,'영업시간이 아니면 PC를 자동으로 종료하기','\'영업시간 설정\' 메뉴에서 설정한 영업 종료시간에 스트리밍과 PC를 자동으로 종료할지 선택해주세요.',get_setting('shutdown_enabled')))
        layout.addSpacing(20)

        self.checkBox.append(self.addSettingIndex_CheckBox(layout,'오래된 녹화 파일을 자동으로 삭제하기','오래된 녹화 파일을 자동으로 삭제할지 선택해주세요.',get_setting('record_delete_enabled')))
        layout.addSpacing(20)

        self.addSettingIndex_DirDrawer(layout,'녹화 파일 위치','녹화 파일이 저장되어있는 위치를 선택해주세요.',get_setting('record_loc'))
        layout.addSpacing(20)

        self.inputBox.append(self.addSettingIndex_int(layout,'녹화 파일 보관 기간(일)','녹화 파일을 며칠동안 보관할지, 즉 녹화된 지 얼마나 지난 파일만 삭제할지 입력해주세요.',get_setting('record_delete_dur')))

    def SettingUI3(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []

        self.checkBox.append(self.addSettingIndex_CheckBox(layout,'스트리밍을 자동으로 생성하기','OBS Studio 실행 전 스트리밍을 자동으로 생성할지 선택해주세요. YouTube 정책 변경으로 생성된 스트리밍이 없는 경우 YouTube Studio에 접속하기 전까지 방송이 자동으로 시작되지 않아, 활성화하는 것을 추천합니다.',get_setting('stream_autocreate_enabled')))
        layout.addSpacing(20)

        self.inputBox.append(self.addSettingIndex_TextSingleLine(layout,'스트리밍 제목','자동으로 생성할 스트리밍의 제목을 입력해 주세요. (100자 이내)',get_setting('stream_title')))
        layout.addSpacing(20)

        self.inputBox.append(self.addSettingIndex_TextMultiLine(layout,'스트리밍 설명','자동으로 생성할 스트리밍의 설명을 입력해 주세요.\n(5천자 이내, 엔터(줄바꿈) 사용 가능)',get_setting('stream_desc')))
        layout.addSpacing(20)

        layout.addWidget(self.addSettingIndex_Desc('입력할 수 있는 변수 목록\n{date1} : 오늘 날짜 (2025년 01월 02일 형식)\n{date2} : 오늘 날짜 (2025-01-02 형식)\n{date3} : 오늘 날짜 (2025/01/02 형식)\n{center} : \'점포명, 기기명 설정\' 메뉴에서 설정한 점포명\n{device} : \'점포명, 기기명 설정\' 메뉴에서 설정한 기기명'))

    def SettingUI4(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []

        layout.addWidget(self.addSettingIndex_Title('연결된 계정 정보'))
        self.channel_label = self.addSettingIndex_Desc(f'채널 명 : {get_setting('channel_name')}\n스트림 키 : {get_setting('channel_stream_key')}\n현재 기기 : LiveKiosk {get_mac()}')
        layout.addWidget(self.channel_label)
        layout.addSpacing(10)

        layout.addWidget(self.addSettingIndex_Title('YouTube API 다시 연동하기'))
        button = QPushButton('Google 계정으로 로그인') #각 설정으로 전환되는 위젯 추가
        button.clicked.connect(self.re_auth) #그 버튼을 클릭하면 각 설정의 UI가 호출됨
        button.setFont(QFont('Pretendard',14,500)) #버튼 폰트 설정
        button.setStyleSheet(f'border:1px solid black; background-color:#eee; border-radius: 10%;') #border, bgcolor 설정
        button.setFixedWidth(250)
        layout.addWidget(button) #위젯 추가

        QTimer.singleShot(0, lambda: self.resize(500, 300))

    def SettingUI4_1(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []

        layout.addWidget(self.addSettingIndex_Title('연결된 계정 정보'))
        self.channel_label = self.addSettingIndex_Desc(f'채널 명 : {get_setting('channel_name')}\n스트림 키 : {get_setting('channel_stream_key')}\n현재 기기 : LiveKiosk {get_mac()}')
        layout.addWidget(self.channel_label)
        layout.addSpacing(10)

        layout.addWidget(self.addSettingIndex_Title('YouTube API 연동하기'))
        button = QPushButton('Google 계정으로 로그인') #각 설정으로 전환되는 위젯 추가
        button.clicked.connect(self.re_auth) #그 버튼을 클릭하면 각 설정의 UI가 호출됨
        button.setFont(QFont('Pretendard',14,500)) #버튼 폰트 설정
        button.setStyleSheet(f'border:1px solid black; background-color:#eee; border-radius: 10%;') #border, bgcolor 설정
        button.setFixedWidth(250)
        layout.addWidget(button) #위젯 추가

        QTimer.singleShot(0, lambda: self.resize(500, 300))

    def SettingUI5(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []
        QTimer.singleShot(0, lambda: self.resize(500,920))

        layout.addWidget(self.addSettingIndex_Desc('YouTube는 12시간 미만인 스트리밍만 다시보기를 지원하기 때문에, 영업시간이 12시간을 초과하는 경우 주기적으로 재시작하지 않으면 스트리밍 다시보기가 날라갑니다. 그래서 LiveKiosk에서는 주기적으로 재시작하는 옵션을 제공합니다.\n24시간 스트리밍을 하는 경우 \'주기적으로 재시작\' 모드를, 영업 시간이 정해져 있고 그 영업시간 중에만 스트리밍을 하는 경우 \'정해진 시간에 재시작\' 모드를 추천합니다.\n스트리밍을 재시작하는 동안 30초~1분 정도 스트리밍이 중지됩니다. 한산한 시간에 재시작하게 설정하는 것을 추천합니다.'))

        self.checkBox.append(self.addSettingIndex_Dropdown(layout,'스트리밍 재시작 모드 선택','스트리밍 재시작 모드를 선택해주세요.',['재시작 안 함','주기적으로 재시작','정해진 시간에 재시작'],get_setting('stream_autorestart_enabled')))
        layout.addSpacing(20)

        self.inputBox.append(self.addSettingIndex_int(layout,'스트리밍 재시작 주기(분)','스트리밍을 재시작할 주기를 입력해주세요. 위에서 설명한 문제 때문에, 720분에 가까운 시간(710~715분 등)으로 설정하시는 것을 추천합니다.',get_setting('stream_autorestart_dur')))
        layout.addSpacing(20)

        layout.addWidget(self.addSettingIndex_Title('스트리밍 재시작 시간 설정'))
        self.SettingUI5_1(layout)

    def SettingUI5_1(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정

        # 표를 추가합니다.
        self.table = QTableWidget()
        self.table.setFixedSize(480,250)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["요일", "재시작 시간 1", "재시작 시간 2"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.load_table_data2()

        layout.addWidget(self.table)
        
        # 변경할 수 있는 UI를 추가합니다.
        self.week_checkboxes = []
        week_layout = QHBoxLayout()
        week_labels = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        for i, label in enumerate(week_labels):
            checkbox = QCheckBox(label)
            self.week_checkboxes.append(checkbox)
            week_layout.addWidget(checkbox)
        
        layout.addLayout(week_layout)

        # 재시작 시간 1, 2 둘중 하나 선택
        time_layout = QHBoxLayout()
        self.restart_time_group = QButtonGroup(self)
        self.restart_time_radio1 = QRadioButton("재시작 시간 1")
        self.restart_time_radio2 = QRadioButton("재시작 시간 2")
        self.restart_time_group.addButton(self.restart_time_radio1, 1)
        self.restart_time_group.addButton(self.restart_time_radio2, 2)
        self.restart_time_radio1.setChecked(True)  # 기본 선택
        time_layout.addWidget(self.restart_time_radio1)
        time_layout.addWidget(self.restart_time_radio2)
        layout.addLayout(time_layout)

        # 라디오 버튼: 삭제 / 시간 변경 + QTimeEdit
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("작업 선택:"))

        self.action_group = QButtonGroup(self)
        self.delete_radio = QRadioButton("삭제")
        self.change_radio = QRadioButton("시간 변경")
        self.action_group.addButton(self.delete_radio, 1)
        self.action_group.addButton(self.change_radio, 2)
        self.change_radio.setChecked(True)  # 기본값은 변경

        action_layout.addWidget(self.delete_radio)
        action_layout.addWidget(self.change_radio)

        # 시간 변경 시 사용할 QTimeEdit
        self.modify_time_edit = QTimeEdit()
        self.modify_time_edit.setDisplayFormat("hh:mm")
        action_layout.addWidget(self.modify_time_edit)

        layout.addLayout(action_layout)

        # 변경 버튼
        self.change_button = QPushButton("변경")
        self.change_button.clicked.connect(self.changeTime2)
        layout.addWidget(self.change_button)

    def SettingUI6(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []

        self.checkBox.append(self.addSettingIndex_CheckBox(layout,'OBS 프로파일이 변경된 경우 백업하기','OBS Studio의 프로파일이 변경된 경우, LiveKiosk 설치 폴더에 백업할지 선택해 주세요. 이러면 누군가가 설정을 마음대로 변경해도, OBS 설치 폴더의 Profiles 폴더에 있는 백업본으로 쉽게 백업하실 수 있습니다. 원하는 시점의 백업본 폴더 안에 들어있는 파일 3개를 OBS Studio의 파일 > 프로파일 폴더 보기를 클릭하면 나오는 폴더에 덮어씌워주세요.',get_setting('obs_renew_enabled')))
        layout.addSpacing(20)

        self.checkBox.append(self.addSettingIndex_CheckBox(layout,'위젯에 녹화버튼 추가','OBS Studio의 LiveKiosk 위젯에 녹화버튼을 추가할지 선택해 주세요. 방송 종료를 방지하기 위해 제어 독을 없앤 경우에 유용합니다.',get_setting('obs_record_button_enabled')))
        layout.addSpacing(20)

        self.checkBox.append(self.addSettingIndex_CheckBox(layout,'스트림키 초기화 기능 사용','OBS에서 사용하는 스트림 키를 매일 LiveKiosk의 스트림 키로 초기화할지 선택해 주세요. 누군가가 마음대로 OBS Studio와 자신의 채널을 연결해 놔도, 매일 초기화할 때 자동으로 LiveKiosk와 연동된 채널의 스트림 키로 변경됩니다.',get_setting('streamkey_renew_enabled')))
        layout.addSpacing(20)

        self.inputBox.append(self.addSettingIndex_TextMultiLine(layout,'공지사항','OBS Studio의 LiveKiosk 위젯에 표시할 공지사항을 입력해 주세요.',get_setting('obs_widget_information')))

    def SettingUI7(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []

        layout.addWidget(self.addSettingIndex_Title('LiveKiosk 정보'))
        layout.addWidget(self.addSettingIndex_Desc(f'LiveKiosk v{__version__}\nDB 버전 {get_setting('ver')}'))
        layout.addSpacing(10)

        layout.addWidget(self.addSettingIndex_Title('비밀번호 변경'))
        subLayout1 = QHBoxLayout()
        label_pw = QLabel("현재 비밀번호 : ")
        label_pw.setFont(QFont('Pretendard',12,500)) #버튼 폰트 설정
        self.input_pw2 = QLineEdit()
        self.input_pw2.setEchoMode(QLineEdit.EchoMode.Password)
        subLayout1.addWidget(label_pw)
        subLayout1.addWidget(self.input_pw2)

        subLayout2 = QHBoxLayout()
        label_pw = QLabel("변경할 비밀번호 : ")
        label_pw.setFont(QFont('Pretendard',12,500)) #버튼 폰트 설정
        self.input_pw3 = QLineEdit()
        self.input_pw3.setEchoMode(QLineEdit.EchoMode.Password)
        subLayout2.addWidget(label_pw)
        subLayout2.addWidget(self.input_pw3)

        subLayout3 = QHBoxLayout()
        label_pw = QLabel("변경할 비밀번호 다시 입력 : ")
        label_pw.setFont(QFont('Pretendard',12,500)) #버튼 폰트 설정
        self.input_pw4 = QLineEdit()
        self.input_pw4.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pw4.returnPressed.connect(self.check_login2)
        subLayout3.addWidget(label_pw)
        subLayout3.addWidget(self.input_pw4)

        login_btn = QPushButton("비밀번호 변경하기")
        login_btn.setFont(QFont('Pretendard',12,500)) #버튼 폰트 설정
        login_btn.setStyleSheet(f'border:1px solid black; background-color:#eee; border-radius: 10%;') #border, bgcolor 설정
        login_btn.clicked.connect(self.check_login2)
        layout.addLayout(subLayout1)
        layout.addLayout(subLayout2)
        layout.addLayout(subLayout3)
        layout.addWidget(login_btn)

        QTimer.singleShot(0, lambda: self.resize(500, 400))

    def SettingUI7_1(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []

        layout.addWidget(self.addSettingIndex_Title('LiveKiosk를 선택해주셔서 감사합니다.'))
        layout.addWidget(self.addSettingIndex_Desc(f'LiveKiosk의 정상적인 가동을 위해, 최초 설정을 진행하겠습니다. 먼저, 설정에서 사용할 비밀번호를 입력해주세요.'))
        layout.addSpacing(10)

        layout.addWidget(self.addSettingIndex_Title('비밀번호 설정'))
        subLayout2 = QHBoxLayout()
        label_pw = QLabel("설정할 비밀번호 : ")
        label_pw.setFont(QFont('Pretendard',12,500)) #버튼 폰트 설정
        self.input_pw3 = QLineEdit()
        self.input_pw3.setEchoMode(QLineEdit.EchoMode.Password)
        subLayout2.addWidget(label_pw)
        subLayout2.addWidget(self.input_pw3)

        subLayout3 = QHBoxLayout()
        label_pw = QLabel("설정할 비밀번호 다시 입력 : ")
        label_pw.setFont(QFont('Pretendard',12,500)) #버튼 폰트 설정
        self.input_pw4 = QLineEdit()
        self.input_pw4.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pw4.returnPressed.connect(self.check_login3)
        subLayout3.addWidget(label_pw)
        subLayout3.addWidget(self.input_pw4)

        login_btn = QPushButton("비밀번호 설정하기")
        login_btn.setFont(QFont('Pretendard',12,500)) #버튼 폰트 설정
        login_btn.setStyleSheet(f'border:1px solid black; background-color:#eee; border-radius: 10%;') #border, bgcolor 설정
        login_btn.clicked.connect(self.check_login3)
        layout.addLayout(subLayout2)
        layout.addLayout(subLayout3)
        layout.addWidget(login_btn)

        QTimer.singleShot(0, lambda: self.resize(500, 200))

    def InstallFinishedUI(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []
        update_setting('setting_finished','1')

        layout.addWidget(self.addSettingIndex_Title('설정 완료'))
        layout.addWidget(self.addSettingIndex_Desc('설정 내용을 전부 정확하게 입력하셨다면, 위쪽의 X 버튼을 눌러 이 창을 닫아주세요. 그리고, init.pyw 파일을 더블클릭해 정상적으로 작동하는지 테스트해보세요.'))

        QTimer.singleShot(0, lambda: self.resize(500, 200))

    def SettingUI8(self, outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []
        self.secret_box : QTextEdit = self.addSettingIndex_TextMultiLine(layout,'client_secret 내용 입력','발급받으신 client_secret.json의 내용을 전부 붙여넣기해주세요. (메모장에서 Ctrl+A로 전체 선택 후 Ctrl+C로 복사, 위의 입력 칸 클릭 후 Ctrl+V로 붙여넣기)','')
        layout.addSpacing(20)

        if self.mode == 0:
            layout.addWidget(self.addSettingIndex_Title('YouTube API 다시 연동하기'))
            button = QPushButton('해당 메뉴로 이동 > ') #각 설정으로 전환되는 위젯 추가
            button.clicked.connect(self.setting4Link) #그 버튼을 클릭하면 각 설정의 UI가 호출됨
            button.setFont(QFont('Pretendard',14,500)) #버튼 폰트 설정
            button.setStyleSheet(f'border:1px solid black; background-color:#eee; border-radius: 10%;') #border, bgcolor 설정
            button.setFixedWidth(250)
            layout.addWidget(button) #위젯 추가
        QTimer.singleShot(0, lambda: self.resize(500, 400))

    def SettingUI9(self,outerUILayout:QVBoxLayout):
        layout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        outerUILayout.addLayout(layout) #그리고 그걸 레이아웃으로 설정
        self.inputBox : list[QLineEdit] = []
        self.checkBox : list[QCheckBox] = []

        pf_list = getOBSProfiles()
        if len(pf_list) == 0:
            pf_list = ['검색된 프로파일이 없습니다.']
            pf_default = 0
        else:
            pf_default_str = get_setting('obs_renew_pf_dir')
            try:
                pf_default = pf_list.index(pf_default_str)
            except ValueError:
                pf_default = 0

        sc_list = getOBSScenes()
        if len(sc_list) == 0:
            sc_list = ['검색된 장면이 없습니다.']
            sc_default = 0
        else:
            sc_default_str = get_setting('obs_renew_scene_dir')
            try:
                sc_default = sc_list.index(sc_default_str)
            except ValueError:
                sc_default = 0

        self.addSettingIndex_DirDrawer(layout,'OBS 설정 파일 위치','OBS 설정 파일의 위치를 선택해주세요. OBS Studio에서 \'파일 > 설정 폴더 보기\'를 클릭하면 나오는 폴더를 선택하시면 됩니다.',get_setting('obs_path'))
        layout.addSpacing(20)

        self.obs_profile_sel = self.addSettingIndex_Dropdown(layout,'프로파일 선택','OBS Studio에서 사용 중인 프로파일을 선택해주세요.',pf_list,pf_default)
        layout.addSpacing(20)

        self.obs_scene_sel = self.addSettingIndex_Dropdown(layout,'장면 선택','OBS Studio에서 사용 중인 장면을 선택해주세요.',sc_list,sc_default)
        QTimer.singleShot(0, lambda: self.resize(500, 500))

    def check_login3(self):
        pw2 = self.input_pw3.text()
        pw3 = self.input_pw4.text()

        if pw2 == pw3: # 비밀번호가 서로 일치하면
            update_pw(pw2)
            self.InstallUI()
        else:
            QMessageBox.warning(
            self,
            "비밀번호 변경 실패",
            "변경할 비밀번호와 변경할 비밀번호 다시 입력이 일치하지 않습니다."
        )

    def check_login2(self):
        pw = self.input_pw2.text()
        pw2 = self.input_pw3.text()
        pw3 = self.input_pw4.text()

        if login(pw):  # 로그인 성공 시
            if pw2 == pw3: # 비밀번호가 서로 일치하면
                update_pw(pw2)
                QMessageBox.information(
                    self,
                    '비밀번호 변경 성공',
                    '비밀번호 변경에 성공했습니다.'
                )
            else:
                QMessageBox.warning(
                self,
                "비밀번호 변경 실패",
                "변경할 비밀번호와 변경할 비밀번호 다시 입력이 일치하지 않습니다."
            )
        else:
            QMessageBox.warning(
                self,
                "비밀번호 변경 실패",
                "현재 비밀번호가 틀렸습니다."
            )
            self.input_pw2.clear()

    def re_auth(self):
        credentials = re_auth()
        if credentials is not None:
            channel_name = get_channel_name(credentials)
            channel_stream_key, channel_stream_id = get_stream_key(credentials)
            update_setting('channel_name',channel_name)
            update_setting('channel_stream_key',channel_stream_key)
            update_setting('channel_stream_id',channel_stream_id)
            self.channel_label.setText(f'채널 명 : {get_setting('channel_name')}\n스트림 키 : {get_setting('channel_stream_key')}\n현재 기기 : LiveKiosk {get_mac()}')
            QMessageBox.information(self,"연동 완료",f"{channel_name} 채널로 연동을 완료했습니다.")
        else:
            QMessageBox.warning(self,"연동 오류","client_secret이 입력되지 않았습니다. client_secret 변경 메뉴에서 client_secret을 입력하신 후, 다시 한 번 연동해 주십시오.")

    def load_table_data(self):
        operation_times = fetch_operation_times()
        self.table.setRowCount(len(operation_times))
        for i, (week, start_time, end_time) in enumerate(operation_times):
            week_label = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"][week]
            self.table.setItem(i, 0, QTableWidgetItem(week_label))
            self.table.setItem(i, 1, QTableWidgetItem(getTimeStamp(start_time)))
            self.table.setItem(i, 2, QTableWidgetItem(getTimeStamp(end_time)))
    
    def changeTime(self):
        start_time = self.start_time_edit.time()
        end_time = self.end_time_edit.time()

        if self.start_time_checkbox.isChecked():
            start_time_code = getTimeCode(start_time.hour(),start_time.minute())
        else:
            start_time_code = None
        if self.end_time_checkbox.isChecked():
            end_time_code = getTimeCode(end_time.hour(),end_time.minute())
        else:
            end_time_code = None

        week_list = []
        for i, checkbox in enumerate(self.week_checkboxes):
            if checkbox.isChecked():
                week_list.append(i)
            checkbox.setChecked(False)
        update_operation_times(week_list, start_time_code, end_time_code)

        self.load_table_data()

    def load_table_data2(self):
        operation_times = fetch_restart_times()
        self.table.setRowCount(len(operation_times))
        for i, (week, start_time, end_time) in enumerate(operation_times):
            week_label = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"][week]
            self.table.setItem(i, 0, QTableWidgetItem(week_label))
            self.table.setItem(i, 1, QTableWidgetItem(getTimeStamp(start_time) if start_time is not None else '설정되지 않음'))
            self.table.setItem(i, 2, QTableWidgetItem(getTimeStamp(end_time) if end_time is not None else '설정되지 않음'))
    
    def changeTime2(self):
        selected_restart_time = self.restart_time_group.checkedId()
        selected_action = self.action_group.checkedId()

        if selected_action == 1:  # 삭제
            time_code = None
        elif selected_action == 2:  # 시간 변경
            modify_time = self.modify_time_edit.time()
            time_code = getTimeCode(modify_time.hour(),modify_time.minute())

        week_list = []
        for i, checkbox in enumerate(self.week_checkboxes):
            if checkbox.isChecked():
                week_list.append(i)
            checkbox.setChecked(False)
        update_restart_times(week_list, selected_restart_time, time_code)

        self.load_table_data2()

    def InstallUI(self):
        ui = self.current_step
        self.clearLayout(self.layout()) #화면 안의 내용을 전부 비움
        outerUILayout = QVBoxLayout() #VBoxLayout (세로 방향 박스형 레이아웃) 생성
        self.layout().addLayout(outerUILayout) #그리고 그걸 레이아웃으로 설정
        self.layout().setContentsMargins(10, 10, 10, 10)

        ## TODO : 저장하고 뒤로 버튼 추가
        headerUILayout = QHBoxLayout()
        outerUILayout.addLayout(headerUILayout)

        back_button = QPushButton('< 이전')
        back_button.setFont(QFont('Pretendard',14,500)) #버튼 폰트 설정
        back_button.setStyleSheet(f'border:1px solid black; background-color:#eee; border-radius: 10%;') #border, bgcolor 설정
        back_button.setFixedWidth(100)
        back_button.clicked.connect(lambda:self.InstallUILink(0))
        if ui <= 0:
            back_button.setDisabled(True)
        back_button.setMaximumHeight(30)
        headerUILayout.addWidget(back_button)

        menu_label = QLabel('현재 메뉴')
        menu_label.setAlignment(Qt.AlignmentFlag.AlignCenter) #가운데 정렬
        menu_label.setFont(QFont('Pretendard',14,500)) #폰트를 프리텐다드 5 Medium, 크기 30으로 설정
        menu_label.setMaximumHeight(30)
        headerUILayout.addWidget(menu_label)

        next_button = QPushButton('다음 >')
        next_button.setFont(QFont('Pretendard',14,500)) #버튼 폰트 설정
        next_button.setStyleSheet(f'border:1px solid black; background-color:#eee; border-radius: 10%;') #border, bgcolor 설정
        next_button.setFixedWidth(100)
        if ui >= len(self.steps) - 1:
            next_button.setDisabled(True)
        next_button.clicked.connect(lambda:self.InstallUILink(1))
        next_button.setMaximumHeight(30)
        headerUILayout.addWidget(next_button)

        desc_label = QLabel('설명')
        desc_label.setFont(QFont('Pretendard',12,500)) #폰트를 프리텐다드 5 Medium, 크기 30으로 설정
        desc_label.setWordWrap(True)
        outerUILayout.addWidget(desc_label)

        outerUILayout.addStretch(1)

        menu_label.setText(self.steps[ui][1])
        desc_label.setText(self.steps[ui][2])
        self.steps[ui][0](outerUILayout)

        outerUILayout.addStretch(1)

    def InstallUILink(self, dest):
        go_gate = True
        ui = self.steps[self.current_step][3]
        if ui != 8:
            self.gateUILink(ui)
        else:
            secret_text = self.secret_box.toPlainText()
            if secret_text.startswith('{"installed":'):
                update_secret(secret_text)
                update_setting('channel_name','※ 다시 연동 필요 ※')
            elif secret_text == '' and get_secret() is None:
                QMessageBox.warning(self,"client_secret을 입력하지 않으셨습니다.",
                    "client_secret을 입력하지 않으신 경우, YouTube 스트림 키와 스트리밍의 생성이 불가능합니다.\n해당 기능을 사용하시려면, '이전' 버튼을 눌러 이 페이지로 되돌아오셔서 client_secret을 입력해주세요.\n해당 기능을 사용하지 않으시려면, 다음 페이지에서 YouTube 연동을 진행하지 마시고 다음으로 넘어가주세요.")
            elif secret_text != '':
                go_gate = False
                QMessageBox.warning(self,"변경 실패",
                    "데스크톱 유형의 client_secret이 아닌 것 같습니다. 정확한 유형의 client_secret을 발급받으셨는지 다시 한 번 확인해주세요.")
                self.secret_box.clear()

        if go_gate:
            if dest == 0:
                self.current_step -= 1
            elif dest == 1:
                self.current_step += 1

            self.InstallUI()


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
