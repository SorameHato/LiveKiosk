## todo : 메인 창 생성, 항목 : 왼쪽엔 간단한 그림, 오른쪽엔
## 맨 위 : 오락실 명, 기기 명 등
## 아래 : 왼쪽(완료 여부 표시), 오른쪽(각 항목 이름)의 표
## 항목 이름 : DB 연결, 운영시간 확인, 자동 종료 설정, 방송 생성, 녹화본 삭제, OBS 계정 연결 초기화, OBS 실행행
## <a href="https://www.flaticon.com/free-icons/tick" title="tick icons">Tick icons created by Maxim Basinski Premium - Flaticon</a>
## <a href="https://www.flaticon.com/free-icons/continue" title="continue icons">Continue icons created by meaicon - Flaticon</a>

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QGridLayout
from PyQt6.QtGui import QPixmap, QFontDatabase
from PyQt6.QtCore import Qt, QTimer, QCoreApplication, QThread, pyqtSignal
import pathlib, datetime, os, sys, subprocess, ctypes, time, hashlib, shutil, json
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from api import youtube, db
from api.db import getTimeCode, getWeekdayCode, getTimeStamp
from __init__ import version, version_build, version_branch, __version__
now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=9)))
file_loc = pathlib.Path(__file__).parent

right_width = 530
work_count = 7

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_list : list[list[QLabel]] = []
        self.log_label : QLabel = None
        self.setWindowTitle(f"LiveKiosk v{version}-{version_branch}.{version_build}")
        self.setFixedSize(400+right_width, 700)  # 1. 창 크기 고정

        # 메인 수평 레이아웃
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # QV1 (왼쪽 영역)
        left_widget = QWidget()
        left_widget.setFixedSize(387, 688)
        v1_layout = QVBoxLayout(left_widget)
        v1_layout.setContentsMargins(0,0,0,0)
        v1_layout.setSpacing(0)
        
        # 3. 이미지 로딩 (369x656)
        image_label = QLabel()
        image_label.setFixedSize(387,688)
        pixmap = QPixmap(str(file_loc.joinpath('image','cover.png'))).scaled(387, 688, Qt.AspectRatioMode.KeepAspectRatio)
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v1_layout.addWidget(image_label)

        # QV2 (오른쪽 영역)
        right_widget = QWidget()
        right_widget.setFixedSize(right_width, 700)
        v2_layout = QVBoxLayout(right_widget)
        v2_layout.setContentsMargins(0, 0, 0, 0)
        v2_layout.setSpacing(4)

        # 4-I. 상단 텍스트 레이블
        top_label = QLabel(f"LiveKiosk v{version}\n분기 : {version_branch}, 분기 내 버전 : {version_build}")
        top_label.setFixedSize(right_width, 55)
        top_label.setStyleSheet("font-size: 20px;")
        top_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        v2_layout.addWidget(top_label)

        top_label2 = QLabel(f"방송장비를 초기화하는 중…\nDeveloped by 2011-2025 SkyWare <Hato Sorame> License: GPL v3\n")
        top_label2.setFixedWidth(right_width)
        top_label2.setStyleSheet("font-size: 14px;")
        top_label2.setAlignment(Qt.AlignmentFlag.AlignLeft)
        top_label2.setWordWrap(True) # 자동 줄바꿈 설정
        self.log_label = top_label2
        v2_layout.addWidget(top_label2)

        # 4-II. 그리드 레이아웃
        grid = QGridLayout()
        for row in range(work_count):
            # 50x50 이미지
            icon = QLabel()
            pixmap = QPixmap(str(file_loc.joinpath('image','load.png'))).scaled(40, 40)
            icon.setPixmap(pixmap)
            
            # 250x50 텍스트
            text = QLabel("Hello World")
            text.setFixedSize(right_width-40, 40)
            text.setStyleSheet("font-size:18px;")
            
            # 행 구성
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.addWidget(icon)
            container_layout.addWidget(text)
            
            grid.addWidget(container, row, 0)
            self.load_list.append([icon, text])

        v2_layout.addLayout(grid)
        
        # 레이아웃 조립
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)

        # 각 리스트 설명 수정
        self.load_list[0][1].setText('DB 연결')
        self.load_list[1][1].setText('Youtube API 채널 인증정보 연결')
        self.load_list[2][1].setText('영업시간 확인, 자동 종료 설정')
        self.load_list[3][1].setText('스트리밍 생성')
        self.load_list[4][1].setText('오래된 녹화 파일 삭제')
        self.load_list[5][1].setText('OBS Studio 프로파일, 장면 백업')
        self.load_list[6][1].setText('YouTube 채널 스트림키 초기화')

        self.init_thread = init()   # ✔ QThread 수명 관리 (self의 속성으로 보관)
        self.init_thread.addLogSignal.connect(self.addLog)      # UI 갱신용 슬롯 연결
        self.init_thread.setLogTextSignal.connect(self.setLogText)
        self.init_thread.changeWorkingSignal.connect(self.changeWorking)
        self.init_thread.changeFinSignal.connect(self.changeFin)
        self.init_thread.changePassSignal.connect(self.changePass)
        self.init_thread.finishApp.connect(QCoreApplication.quit)

    def start_init(self):
        if not self.init_thread.isRunning():  # 이미 실행 중이면 중복 방지
            self.init_thread.start()

    def changeWorking(self, index:int):
        label:QLabel=self.load_list[index][0]
        pixmap = QPixmap(str(file_loc.joinpath('image','pass.png'))).scaled(40, 40)
        label.setPixmap(pixmap)

    def changeFin(self, index:int):
        label:QLabel=self.load_list[index][0]
        pixmap = QPixmap(str(file_loc.joinpath('image','fin.png'))).scaled(40, 40)
        label.setPixmap(pixmap)

    def changePass(self, index:int):
        label:QLabel=self.load_list[index][0]
        pixmap = QPixmap(str(file_loc.joinpath('image','working.png'))).scaled(40, 40)
        label.setPixmap(pixmap)

    def addLog(self, text:str):
        self.log_label.setText(self.log_label.text() + '\n' + text)

    def setLogText(self, text:str):
        self.log_label.setText(text)

def delete_old_files(file_loc: pathlib.Path, days_old: int = 30):
    threshold = now - datetime.timedelta(days=days_old)
    old_files = []

    # 디렉터리 존재 및 유효성 체크
    if not file_loc.exists() or not file_loc.is_dir():
        return f"디렉터리가 존재하지 않거나 디렉터리가 아닙니다: {file_loc}"

    for file in file_loc.iterdir():
        if file.is_file():
            try:
                created_time = datetime.datetime.fromtimestamp(file.stat().st_ctime)
            except AttributeError:
                # 일부 시스템은 생성 시간이 없을 수 있으므로, 수정 시간(st_mtime) 사용
                created_time = datetime.datetime.fromtimestamp(file.stat().st_mtime)
            created_time = created_time.astimezone(tz=datetime.timezone(datetime.timedelta(hours=9)))
            if created_time < threshold:
                old_files.append(file)

    for old_file in old_files:
        old_file.unlink()  # 파일 삭제

    return f"녹화된 지 {days_old}일이 지난 녹화 파일 {len(old_files)}개를 삭제했습니다."


class init(QThread):
    addLogSignal = pyqtSignal(str)
    setLogTextSignal = pyqtSignal(str)
    changeWorkingSignal = pyqtSignal(int)
    changeFinSignal = pyqtSignal(int)
    changePassSignal = pyqtSignal(int)
    finishApp = pyqtSignal()  # 프로그램 종료 요청 신호

    def run(self):
        self.changeWorking(0)
        db_path = pathlib.Path(os.getenv('APPDATA')).joinpath('SkyWare','LiveKiosk','db.db')
        if not db_path.is_file():
            self.addLog('오류가 발생했습니다. 관리자에게 문의해 주십시오.')
            self.addLog('오류 : DB 설정파일이 존재하지 않습니다. LiveKiosk를 다시 설치해 주십시오. 다시 설치해도 해결되지 않으면, 개발자인 소라메 하토에게 이메일 SorameHato@protonmail.ch 로 문의해 주십시오.')
            return
        ## DB 연결 완료 표시
        self.changeWorking(1)

        ## DB에서 사전 설정된 title, desc 가져오기
        date1 = now.strftime('%Y년 %m월 %d일')
        date2 = now.strftime('%Y-%m-%d')
        date3 = now.strftime('%Y/%m/%d')
        center_location = db.get_setting('center_name')
        device_location = db.get_setting('device_name')
        self.setLogTextSignal.emit(f"방송장비를 초기화하는 중…\n{center_location}\n{device_location}\nDeveloped by 2011-2025 SkyWare <Hato Sorame> License: GPL v3\n")

        b_title = db.get_setting('stream_title').replace('{date1}',date1).replace('{date2}',date2).replace('{date3}',date3).replace('{center}',db.get_setting('stream_center')).replace('{device}',db.get_setting('stream_device'))
        b_desc = db.get_setting('stream_desc').replace('{date1}',date1).replace('{date2}',date2).replace('{date3}',date3).replace('{center}',db.get_setting('stream_center')).replace('{device}',db.get_setting('stream_device'))

        if not(db.get_setting('streamkey_renew_enabled') == '0' and db.get_setting('stream_autocreate_enabled') == '0'):
            ## Youtube API 인증정보 가지고 오기
            candidate = youtube.auth()

            if candidate is None or db.get_setting('channel_name') == '※ 다시 연동 필요 ※':
                self.addLog('오류가 발생했습니다. 관리자에게 문의해 주십시오.')
                self.addLog('오류 : YouTube 토큰이 만료되었습니다. 설정 > YouTube API 연동 설정 > Google 계정으로 로그인 버튼을 클릭해 다시 연동해 주십시오.')
                return
                    
            self.changeWorking(2)
        else:
            self.changePass(2)

        if db.get_setting('shutdown_enabled') == '1':
            start_time, end_time = db.fetch_operation_time(getWeekdayCode(now))
            ## 영업시간 확인 완료 표시

            try:
                now_tc = getTimeCode(now.hour, now.minute)
                if not (now_tc >= (start_time - 10) and now_tc < end_time):
                    self.addLog('영업시간이 아닙니다. 60초 후 시스템을 종료합니다.')
                    subprocess.check_call(['shutdown','-s','-t','60','-c','영업시간이 아닙니다.'])
                else:
                    self.addLog(f'오늘의 영업시간 : {getTimeStamp(start_time)} ~ {getTimeStamp(end_time)}')
                    subprocess.check_call(['shutdown','-s','-t',str((end_time-getTimeCode(now.hour,now.minute))*60),'-c',f'"오늘의 영업시간은 {getTimeStamp(end_time)} 까지입니다."'])
            except Exception:
                self.addLog('shutdown 설정이 이미 설정되어있는 것 같습니다.')
            ## 자동 종료 설정 완료 표시
            self.changeWorking(3)
        else:
            self.changePass(3)

        if db.get_setting('stream_autocreate_enabled') == '1':
            youtube.create_broadcast(b_title, b_desc, candidate)
            ## 방송 생성 완료 표시
            self.changeWorking(4)
        else:
            self.changePass(4)

        ## 녹화본 위치 가져와서, 14일 이상 경과한 파일 삭제
        if db.get_setting('record_delete_enabled') == '1':
            result = delete_old_files(pathlib.Path(db.get_setting('record_loc')),int(db.get_setting('record_delete_dur')))
            self.addLog(result)
            self.changeWorking(5)
        else:
            self.changePass(5)

        ## TODO : OBS 프로파일, 장면 백업
        pf_dir = pathlib.Path(db.getOBSProfilesPath(db.get_setting('obs_renew_pf_dir')))
        basic_ini = pf_dir.joinpath('basic.ini')
        service = pf_dir.joinpath('service.json')
        obs_path = pathlib.Path(db.get_setting('obs_path'))
        if db.get_setting('obs_renew_enabled') == '1':
            with basic_ini.open('rb') as f:
                pf_basic = hashlib.sha512(f.read()).hexdigest()
            with service.open('rb') as f:
                pf_service = hashlib.sha512(f.read()).hexdigest()
            stream_encoder = pf_dir.joinpath('streamEncoder.json')
            if stream_encoder.is_file():
                with stream_encoder.open('rb') as f:
                    pf_streamEncoder = hashlib.sha512(f.read()).hexdigest()
            else:
                pf_streamEncoder=''
            with pathlib.Path(db.getOBSScenesPath(db.get_setting('obs_renew_scene_dir'))).open('rb') as f:
                scene_dir = hashlib.sha512(f.read()).hexdigest()

            if not(pf_basic == db.get_temp('hash_pf_basic') and pf_service == db.get_temp('hash_pf_service') and pf_streamEncoder == db.get_temp('hash_pf_streamencoder') and scene_dir == db.get_temp('hash_scene')):
                folder_name = now.strftime("%Y-%m-%d %H-%M-%S")
                target_folder = file_loc.joinpath('obs-profile',folder_name)
                source_folder = obs_path.joinpath('basic')
                shutil.copytree(source_folder,target_folder)
                db.update_temp('hash_pf_basic',pf_basic)
                db.update_temp('hash_pf_service',pf_service)
                db.update_temp('hash_pf_streamencoder',pf_streamEncoder)
                db.update_temp('hash_scene',scene_dir)

            self.changeWorking(6)
        else:
            self.changePass(6)

        if db.get_setting('streamkey_renew_enabled') == '1':
            ## TODO : youtube api에서 계정 스트림 키 가져와서, OBS 프로파일에 붙여넣기 하는 거
            stream_key = db.get_setting('channel_stream_key')

            profile_title = f'LiveKiosk v{__version__} (클라이언트명 : LiveKiosk {youtube.get_mac()}, 마지막 초기화 : {now.isoformat(timespec='milliseconds')})'

            # ConfigParser 객체 생성
            obs_setting_ini = obs_path.joinpath('user.ini')
            if not obs_setting_ini.is_file():
                obs_setting_ini = obs_path.joinpath('global.ini')
            with obs_setting_ini.open('r',encoding='utf-8-sig') as f:
                global_txt = f.readlines()
            for i in range(len(global_txt)):
                if global_txt[i].startswith('Profile='):
                    global_txt[i] = 'Profile=' + profile_title + '\n'
                    break
            with obs_setting_ini.open('w', encoding='utf-8-sig') as f:
                f.writelines(global_txt)

            # ini 파일 읽기
            with basic_ini.open('r',encoding='utf-8-sig') as f:
                basic_ini_text = f.readlines()
            # 특정 섹션(section)과 키(key)의 값(value) 수정
            for i in range(len(basic_ini_text)):
                if basic_ini_text[i].startswith('Name='):
                    basic_ini_text[i] = 'Name=' + profile_title + '\n'
                    break
            # 변경된 내용 저장 (기존 파일 덮어쓰기)
            with open(str(basic_ini), 'w', encoding='utf-8-sig') as f:
                f.writelines(basic_ini_text)

            service_json = {'type':'rtmp_custom','settings':{'server':'rtmps://a.rtmps.youtube.com/live2','use_auth':False,'bwtest':False,'key':stream_key}}
            with service.open('w',encoding='utf-8') as f:
                json.dump(service_json,f,ensure_ascii=False)

            if db.get_setting('obs_renew_enabled') == '1':
                with basic_ini.open('rb') as f:
                    pf_basic2 = hashlib.sha512(f.read()).hexdigest()
                with service.open('rb') as f:
                    pf_service2 = hashlib.sha512(f.read()).hexdigest()
                db.update_temp('hash_pf_basic',pf_basic2)
                db.update_temp('hash_pf_service',pf_service2)

            self.changeFin(6)
        else:
            self.changePassFin(6)

        ## OBS 실행
        if db.get_setting('stream_autocreate_enabled') == '1':
            ctypes.windll.shell32.ShellExecuteA(0, b'open', b'obs64.exe',b'--startstreaming',b'C:\\Program Files\\obs-studio\\bin\\64bit',1)
        else:
            ctypes.windll.shell32.ShellExecuteA(0, b'open', b'obs64.exe',b'',b'C:\\Program Files\\obs-studio\\bin\\64bit',1)

        ## TODO : 이거 팝업창이나 하단 라벨로 띄우기
        self.addLog('자동 초기화가 완료되었습니다. 이 창은 1분 후 자동으로 닫힙니다.')
        time.sleep(60)
        self.finishApp.emit()
    
    def addLog(self,log:str):
        self.addLogSignal.emit(log)
    
    def changeFin(self,index:int):
        self.changeFinSignal.emit(index)
    
    def changeWorking(self,index:int):
        if index >= 1:
            self.changeFinSignal.emit(index-1)
        if index < work_count:
            self.changeWorkingSignal.emit(index)

    def changePass(self,index:int):
        if index >= 1:
            self.changePassSignal.emit(index-1)
        if index < work_count:
            self.changeWorkingSignal.emit(index)

    def changePassFin(self,index:int):
        self.changePassSignal.emit(index)

def main():
    sys.argv += ['-platform', 'windows:darkmode=1']
    app = QApplication(sys.argv)
    font_id = QFontDatabase.addApplicationFont('Pretendard-Regular.otf')
    print(font_id)
    window = MainWindow()
    window.show()
    QTimer.singleShot(1000, window.start_init)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()