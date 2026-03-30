import sys, pathlib, os, datetime, subprocess, hashlib, shutil, json, ctypes
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout
)
from PySide6.QtGui import (
    QPixmap, QFontDatabase, QFont,
    QGuiApplication
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer,
    QParallelAnimationGroup, QRect, QThread, Signal
)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from __init__ import version, version_build, version_branch, __version__
now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=9)))
file_loc = pathlib.Path(__file__).parent

MESSAGE_COUNT = 9
MESSAGE_LIST = ['LiveKiosk를 실행하는 중…\nLoading LiveKiosk…',
                'DB를 읽는 중…\nReading DB…',
                'Google API의 토큰 상태를 확인하는 중…\nChecking token status of Google API…',
                '영업시간을 확인하는 중…\nChecking operation time…',
                '스트리밍을 생성하는 중…\nCreating Streaming…',
                '오래된 녹화 파일을 삭제하는 중…\nDeleting old recording files…',
                'OBS Studio 설정을 백업하는 중…\nBacking settings of OBS Studio up…',
                'YouTube 채널의 스트림 키를 불러오는 중…\nGetting stream key of YouTube Channel…',
                'OBS Studio를 실행하는 중…\n이 창은 약 10초 후 자동으로 닫힙니다.\nRunning OBS Studio…']

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # self.dev_mode = 1
        # self._drag_pos = None
        self._is_closing = False
        self._close_fin = False
        self.cur_step = 0

        self.setFixedSize(960, 400)
        self.setWindowTitle(f"LiveKiosk")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #1c1b39;")

        font_id = QFontDatabase.addApplicationFont("Pretendard-Regular.otf")
        family = QFontDatabase.applicationFontFamilies(font_id)[0]

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # 상단
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(8, 4, 8, 0)

        #left_label = QLabel("고객의 자유를 보장하는 오픈 소스 소프트웨어")
        left_label = QLabel('')
        left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        left_label.setStyleSheet("color: #ffffff; font-size: 20px;")
        left_label.setFont(QFont(family))
        self.ad_label = left_label

        right_label = QLabel(f"v{version}-{version_branch}.{version_build}")
        right_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        right_label.setStyleSheet("color: #ffffff; font-size: 20px;")
        right_label.setFont(QFont(family))

        top_layout.addWidget(left_label)
        top_layout.addWidget(right_label)

        top_widget = QWidget()
        top_widget.setLayout(top_layout)
        top_widget.setFixedHeight(30)
        main_layout.addWidget(top_widget)

        # 이미지
        image_label = QLabel()
        image_label.setFixedHeight(100)

        pixmap = QPixmap(".\\image\\cover.png")

        screen = QGuiApplication.primaryScreen()
        dpr = screen.devicePixelRatio()   # 보통 1.0, 1.25, 1.5, 2.0 등
        target_w = int(640 * dpr)
        target_h = int(100 * dpr)

        scaled = pixmap.scaled(target_w, target_h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

        x = (scaled.width() - target_w) // 2
        y = (scaled.height() - target_h) // 2
        cropped = scaled.copy(x, y, target_w, target_h)
        cropped.setDevicePixelRatio(dpr)

        image_label.setPixmap(cropped)
        image_label.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(image_label)

        # 중앙
        center_label = QLabel("방송을 준비하는 중입니다.<br>\nPC를 <span style=\"color:#ff6666;\">조작하지 말고</span>, 잠시만 기다려 주십시오.")
        center_label.setTextFormat(Qt.RichText)
        center_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        center_label.setStyleSheet("color: #ffffff; font-size: 40px;")
        center_label.setFont(QFont(family))
        center_label.setFixedHeight(90)

        main_layout.addWidget(center_label)

        # 상태표시용
        log_label = QLabel('')
        log_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        log_label.setStyleSheet("color: #ffffff; font-size: 35px;")
        log_label.setFont(QFont(family))
        log_label.setFixedHeight(130)
        log_label.setWordWrap(True) #자동 줄바꿈
        self.log_label = log_label

        main_layout.addWidget(log_label)
        self.goNextStep()

        # 하단
        bottom_label = QLabel("LiveKiosk™& ⓒ2011-2026 SkyWare <Hato Sorame> All Rights Reserved.")
        bottom_label.setAlignment(Qt.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        bottom_label.setStyleSheet("color: #ffffff; font-size: 25px;")
        bottom_label.setFont(QFont(family))
        bottom_label.setContentsMargins(8, 0, 8, 4)

        main_layout.addWidget(bottom_label)

        self.center_on_screen()
        self.setWindowOpacity(0.0)

        self.init_thread = init()
        self.init_thread.setLogTextSignal.connect(self.setLogText)
        self.init_thread.goNextStepSignal.connect(self.goNextStep)
        self.init_thread.setErrorLogSignal.connect(self.setErrorLogText)
        self.init_thread.finishApp.connect(QApplication.quit)

    def start_init(self):
        if not self.init_thread.isRunning():  # 이미 실행 중이면 중복 방지
            self.init_thread.start()

    def setLogText(self, text:str):
        self.log_label.setText(text)

    def setErrorLogText(self, text:str):
        self.log_label.setText(text)
        self.log_label.setStyleSheet("color: #ffffff; font-size: 20px;")

    def goNextStep(self):
        if self.cur_step >= MESSAGE_COUNT:
            return
        self.setLogText(f'[{self.cur_step+1}/{MESSAGE_COUNT}] {MESSAGE_LIST[self.cur_step]}')
        self.cur_step += 1


    # 여기부턴 ChatGPT가 자동으로 생성해 준 코드들

    def center_on_screen(self):
        screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()

        x = geo.x() + (geo.width() - self.width()) // 2
        y = geo.y() + (geo.height() - self.height()) // 2

        self.move(x, y)

    # ===== Mac 스타일 fade + scale =====
    def showEvent(self, event):
        self.mac_fade_in()
        super().showEvent(event)

    def mac_fade_in(self):
        end_rect = self.geometry()

        scale = 0.96
        w = int(end_rect.width() * scale)
        h = int(end_rect.height() * scale)

        start_rect = QRect(
            end_rect.center().x() - w // 2,
            end_rect.center().y() - h // 2,
            w, h
        )

        # opacity
        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setDuration(300)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.OutCubic)

        # geometry (scale)
        # geo_anim = QPropertyAnimation(self, b"geometry")
        # geo_anim.setDuration(300)
        # geo_anim.setStartValue(start_rect)
        # geo_anim.setEndValue(end_rect)
        # geo_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(opacity_anim)
        #self.anim_group.addAnimation(geo_anim)
        self.anim_group.start()

    def fade_out_and_close(self):
        if self._is_closing:
            return

        self._is_closing = True

        start_rect = self.geometry()

        scale = 0.96
        w = int(start_rect.width() * scale)
        h = int(start_rect.height() * scale)

        end_rect = QRect(
            start_rect.center().x() - w // 2,
            start_rect.center().y() - h // 2,
            w, h
        )

        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setDuration(300)
        opacity_anim.setStartValue(1.0)
        opacity_anim.setEndValue(0.0)
        opacity_anim.setEasingCurve(QEasingCurve.InCubic)

        # geo_anim = QPropertyAnimation(self, b"geometry")
        # geo_anim.setDuration(300)
        # geo_anim.setStartValue(start_rect)
        # geo_anim.setEndValue(end_rect)
        # geo_anim.setEasingCurve(QEasingCurve.InCubic)

        self.anim_group = QParallelAnimationGroup()
        self.anim_group.addAnimation(opacity_anim)
        #self.anim_group.addAnimation(geo_anim)

        self.anim_group.finished.connect(self.final_close)
        self.anim_group.start()

    def final_close(self):
        self._close_fin = True
        QApplication.quit()

    def closeEvent(self, event):
        if self._close_fin:
            event.accept()
        elif not self._is_closing:
            event.ignore()
            self.fade_out_and_close()
        else:
            event.ignore()

    # 드래그
    # def mousePressEvent(self, event):
    #     if self.dev_mode == 1 and event.button() == Qt.LeftButton:
    #         self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
    #         event.accept()

    # def mouseMoveEvent(self, event):
    #     if self.dev_mode == 1 and self._drag_pos and event.buttons() & Qt.LeftButton:
    #         self.move(event.globalPosition().toPoint() - self._drag_pos)
    #         event.accept()

    # def mouseReleaseEvent(self, event):
    #     self._drag_pos = None

class init(QThread):
    setLogTextSignal = Signal(str)
    setErrorLogSignal = Signal(str)
    goNextStepSignal = Signal()
    finishApp = Signal()

    def run(self):
        self.goNextStep() #먼저 2단계로 넘어가줌
        # 1. DB 존재여부 확인 및 import
        db_path = pathlib.Path(os.getenv('APPDATA')).joinpath('SkyWare','LiveKiosk','db.db')
        if not db_path.is_file(): #만약 DB 없으면 오류메세지 띄우고 끝
            self.setErrorLog('오류가 발생했습니다. 관리자에게 문의해 주십시오.\n오류 : DB 설정파일이 존재하지 않습니다. LiveKiosk를 다시 설치해 주십시오. 다시 설치해도 해결되지 않으면, 개발자인 소라메 하토에게 이메일 SorameHato@protonmail.ch 로 문의해 주십시오.')
            return
        else: #만약 존재하면 youtube, db 모듈 import
            from api import youtube, db
            from api.db import getTimeCode, getWeekdayCode, getTimeStamp
            essential_mode = db.get_setting('essential_mode_enabled') == '1'
        self.goNextStep()

        # 2. 토큰 상태 확인
        # 스트림키 초기화, 스트림 자동생성 중 하나라도 활성화되어있고 에센셜모드가 아닌 경우에만 실행
        if ((db.get_setting('streamkey_renew_enabled') != '0' or db.get_setting('stream_autocreate_enabled') != '0') and not essential_mode):
            ## Youtube API 인증정보 가지고 오기
            candidate = youtube.auth()

            # 만약 만료시나 미연동시엔 오류메세지 띄우고 끝
            if candidate is None or db.get_setting('channel_name') == '※ 다시 연동 필요 ※':
                self.setErrorLog('오류가 발생했습니다. 관리자에게 문의해 주십시오.\n오류 : YouTube 토큰이 만료되었습니다. 설정 > YouTube API 연동 설정 > Google 계정으로 로그인 버튼을 클릭해 다시 연동해 주십시오.')
                return
        self.goNextStep()

        # 3. 영업시간 확인 및 자동종료 설정
        # 해당 기능 켜져있을 때만 실행
        if db.get_setting('shutdown_enabled') == '1':
            # 일단 영업시간을 가져옴
            start_time, end_time = db.fetch_operation_time(getWeekdayCode(now))

            try:
                now_tc = getTimeCode(now.hour, now.minute) #현재시간을 타임코드로 가져와서 비교
                if (not (now_tc >= (start_time - 10) and now_tc < end_time)): #영업시간 아니면
                    if (db.get_setting('shutdown_outside_operation_times_enabled') == '1'): #자동종료 켜져있음?
                        self.setErrorLog('영업시간이 아닙니다. 60초 후 시스템을 종료합니다.') #그럼 끔
                        subprocess.check_call(['shutdown','-s','-t','60','-c','영업시간이 아닙니다.'])
                        return
                    else: #자동종료 꺼져있음?
                        #그럼 영업시간 시작 전은 오늘, 영업시간 종료 후는 내일 영업종료시간까지 운영
                        subprocess.check_call(['shutdown','-s','-t',str((end_time-now_tc)*60) if end_time > now_tc else str((end_time-now_tc+1440)*60),'-c',f'"오늘의 영업시간은 {getTimeStamp(end_time)} 까지입니다."'])
                else: #영업시간이면 그냥 종료 설정
                    subprocess.check_call(['shutdown','-s','-t',str((end_time-now_tc)*60),'-c',f'"오늘의 영업시간은 {getTimeStamp(end_time)} 까지입니다."'])
            except Exception:
                pass
        self.goNextStep()

        # 4. 스트리밍 생성
        # 스트림 자동생성 커져있음 + 에센셜모드 아닐때만 실행
        if db.get_setting('stream_autocreate_enabled') == '1' and not essential_mode:
            # 일단 변수 설정
            date1 = now.strftime('%Y년 %m월 %d일')
            date2 = now.strftime('%Y-%m-%d')
            date3 = now.strftime('%Y/%m/%d')

            # 가지고 온 변수로 타이틀, 설명 생성하고 그걸로 유튜브 방송 생성
            b_title = db.get_setting('stream_title').replace('{date1}',date1).replace('{date2}',date2).replace('{date3}',date3).replace('{center}',db.get_setting('stream_center')).replace('{device}',db.get_setting('stream_device'))
            b_desc = db.get_setting('stream_desc').replace('{date1}',date1).replace('{date2}',date2).replace('{date3}',date3).replace('{center}',db.get_setting('stream_center')).replace('{device}',db.get_setting('stream_device'))
            youtube.create_broadcast(b_title, b_desc, candidate)
        self.goNextStep()

        # 5. 오래된 녹화 파일 삭제
        # 해당 기능 켜져있을 때만 실행
        ## 녹화본 위치 가져와서, 14일 이상 경과한 파일 삭제
        if db.get_setting('record_delete_enabled') == '1':
            self.delete_old_files(pathlib.Path(db.get_setting('record_loc')),int(db.get_setting('record_delete_dur')))
        self.goNextStep()

        # 6, 7번에서 쓰이는 변수 불러오기
        if (db.get_setting('obs_renew_enabled') == '1') or (db.get_setting('streamkey_renew_enabled') == '1' and not essential_mode):
            pf_dir = pathlib.Path(db.getOBSProfilesPath(db.get_setting('obs_renew_pf_dir')))
            basic_ini = pf_dir.joinpath('basic.ini')
            service = pf_dir.joinpath('service.json')
            obs_path = pathlib.Path(db.get_setting('obs_path'))

        # 6. OBS 스튜디오 설정 백업
        # 해당 기능 켜져있을 때만 실행
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
        self.goNextStep()

        # 7. YouTube 채널 스트림키 불러와서 OBS 스튜디오 프로파일에 집어넣기
        # 해당 기능 켜져있고 에센셜모드 아닐때만 실행
        if db.get_setting('streamkey_renew_enabled') == '1' and not essential_mode:
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
        self.goNextStep()

        # 8. OBS Studio 실행
        # goNextStep 한 후 10초 있다가 닫기
        if db.get_setting('stream_autocreate_enabled') == '1':
            ctypes.windll.shell32.ShellExecuteA(0, b'open', b'obs64.exe',b'--startstreaming',b'C:\\Program Files\\obs-studio\\bin\\64bit',1)
        else:
            ctypes.windll.shell32.ShellExecuteA(0, b'open', b'obs64.exe',b'',b'C:\\Program Files\\obs-studio\\bin\\64bit',1)
        self.sleep(10)
        self.finishApp.emit()

    def setLog(self,log:str):
        self.setLogTextSignal.emit(log)

    def setErrorLog(self, log:str):
        self.setErrorLogSignal.emit(log)

    def goNextStep(self):
        self.goNextStepSignal.emit()

    def delete_old_files(self, file_loc: pathlib.Path, days_old: int = 30):
        threshold = now - datetime.timedelta(days=days_old)
        old_files:list[pathlib.Path] = []

        # 디렉터리 존재 및 유효성 체크
        if not file_loc.exists() or not file_loc.is_dir():
            self.setErrorLog(f"디렉터리가 존재하지 않거나 디렉터리가 아닙니다: {file_loc}")
            return

        for file in file_loc.iterdir():
            if file.is_file():
                try:
                    created_time = datetime.datetime.fromtimestamp(file.stat().st_birthtime)
                except AttributeError:
                    # 일부 시스템은 생성 시간이 없을 수 있으므로, 수정 시간(st_mtime) 사용
                    created_time = datetime.datetime.fromtimestamp(file.stat().st_mtime)
                created_time = created_time.astimezone(tz=datetime.timezone(datetime.timedelta(hours=9)))
                if created_time < threshold:
                    old_files.append(file)

        for old_file in old_files:
            old_file.unlink(True)  # 파일 삭제

        return f"녹화된 지 {days_old}일이 지난 녹화 파일 {len(old_files)}개를 삭제했습니다."


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    QTimer.singleShot(1000, window.start_init)

    sys.exit(app.exec())