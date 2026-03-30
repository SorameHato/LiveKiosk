import sys, pathlib, os, sqlite3, bcrypt, keyring, hashlib, base64, json, uuid
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from typing import Literal, get_args
db_ver = 1

'''
DB 구조
operation_times = 기존과 구조 동일
env = name, value의 2행따리 (아래 참고)
'''

EnvName = Literal[
    'ver', # db 버전
    'pw', #해시된 비밀번호
    'mac', #이 PC의 MAC 주소
    'setting_finished', #초기설정이 끝났는지
    'essential_mode_enabled', #LiveKiosk Essential (경량모드) 활성화됐는지

    # 1. 방송 장비, 시스템과 관련된 항목
    'center_name',              # 오락실 명
    'device_name',              # 기기명 (장비 위치, 기체 명 등)
    'record_loc',               # 방송 파일 위치
    'record_delete_enabled',    # 방송 파일 자동삭제 활성화 여부
    'record_delete_dur',        # 며칠 이상 지난 방송 파일을 지울지
    'channel_name',             # 연결된 채널의 이름
    'channel_stream_id',        # 채널 스트리밍 키 ID
    'channel_stream_key',       # 채널 스트리밍 키
    'streamkey_renew_enabled',  # 채널 스트림키 자동 renew 활성화할지
    'shutdown_enabled',         # 자동 종료 (영업시간 체크) 활성화 여부 (영업 종료시 자동 shutdown)
    'shutdown_outside_operation_times_enabled',     # 영업시간 아닐 때 부팅되면 종료할 지 여부

    # 2. 방송, OBS Studio와 관련된 항목
    'stream_title',                 # 방송 타이틀
    'stream_desc',                  # 방송 설명
    'stream_center',                # 방송 타이틀, 설명에 표시할 오락실 명
    'stream_device',                # 방송 타이틀, 설명에 표시할 기기명
    'stream_autocreate_enabled',    # 스트리밍 자동 생성 사용 여부
    'stream_autorestart_enabled',   # 방송 자동 재시작 사용 여부
    'stream_autorestart_dur',       # 방송 자동 재시작 시간 (분 단위, 기본 710)
    'obs_renew_enabled',            # OBS 프로파일 초기화 사용 여부
    'obs_renew_pf_dir',             # OBS 프로파일 dir
    'obs_renew_scene_dir',          # OBS 장면 파일 dir
    'obs_path',                     # OBS 경로
    'obs_record_button_enabled',    # OBS 위젯에 녹화버튼 추가 여부
    'obs_widget_information'        # OBS 위젯에 표시할 공지사항
]

TempName = Literal['hash_pf_basic', 'hash_pf_service', 'hash_pf_streamencoder','hash_scene','broadcast_id']

def get_mac():
    mac_num = uuid.getnode()
    mac_str = f"{mac_num:012X}"
    return mac_str

db_default = [('ver',str(db_ver)),('pw',''),('mac',get_mac()),('center_name',''),('device_name',''),
    ('record_loc',''),('record_delete_enabled','0'),('record_delete_dur','90'),('channel_name',''),
    ('channel_stream_id',''),('channel_stream_key',''),('streamkey_renew_enabled','0'),('shutdown_enabled','0'),
    ('stream_title',''),('stream_desc',''),('stream_center',''),('stream_device',''),('stream_autocreate_enabled','1'),
    ('stream_autorestart_enabled','0'),('stream_autorestart_dur','710'),('obs_renew_enabled','1'),('obs_renew_pf_dir',''),
    ('obs_renew_scene_dir',''),('obs_path',str(pathlib.Path(os.getenv('APPDATA')).joinpath('obs-studio'))),
    ('obs_record_button_enabled','0'),('obs_widget_information',''),('setting_finished','0'),
    ('shutdown_outside_operation_times_enabled','0'),('essential_mode_enabled','0') #5.0버전 신기능
]

def _create_db():
    if not db_exist():
        with __connectDB() as (sql_con, sql_cur):
            sql_cur.execute('CREATE TABLE IF NOT EXISTS "env" ("name" TEXT NOT NULL UNIQUE, "value" TEXT NOT NULL, PRIMARY KEY("name"))')
            sql_cur.execute('CREATE TABLE IF NOT EXISTS "operation_time" ( "week" INTEGER NOT NULL UNIQUE, "start_time" INTEGER NOT NULL DEFAULT 0,'+
                            '"end_time" INTEGER NOT NULL DEFAULT 1439, PRIMARY KEY("week"));''')
            sql_cur.execute('CREATE TABLE IF NOT EXISTS "restart_time" ( "week" INTEGER NOT NULL UNIQUE, "time1" INTEGER, "time2" INTEGER, PRIMARY KEY("week"))')
            sql_cur.execute('CREATE TABLE IF NOT EXISTS "temp" ("name" TEXT NOT NULL UNIQUE, "value" TEXT NOT NULL, PRIMARY KEY("name"))')

            sql_cur.executemany('INSERT INTO env VALUES (?, ?)', db_default)
            rows = [(name, '') for name in get_args(TempName)]
            sql_cur.executemany('INSERT INTO temp VALUES (?, ?)',rows)

            for i in range(0,7):
                sql_cur.execute('INSERT INTO operation_time("week") VALUES (?)',(i,))
                sql_cur.execute('INSERT INTO restart_time("week") VALUES (?)',(i,))

def getTimeCode(hour, min):
    if hour >= 6:
        tc = (hour - 6) * 60
    else:
        tc = (hour + 18) * 60
    tc += min
    return tc

def getTimeStamp(tc):
    hour = tc // 60 + 6
    if hour >= 24:
        hour -= 24
    min = tc % 60
    return f'{str(hour).zfill(2)}:{str(min).zfill(2)}'

def getTimeStamp2(tc):
    hour = tc // 60 + 6
    if hour >= 24:
        hour -= 24
    min = tc % 60
    return hour, min

def getWeekdayCode(now):
    week = now.weekday()
    if now.hour < 6:
        week -= 1
    if week < 0:
        week = 6
    return week

db_path = pathlib.Path(os.getenv('APPDATA')).joinpath('SkyWare','LiveKiosk','db.db')

class __connectDB():
    '''
    DB에 연결한 다음 con과 cur을 return하고, 자동으로 commit과 close를 하는 클래스
    이 함수를 쓸 때에는 with __connectDB() as (sql_con, sql_cur): 처럼
    with문에 변수를 두 개 줘야 한다
    '''
    def __init__(self):
        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()

    def __enter__(self) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
        return self.con, self.cur

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.con.rollback()
        else:
            self.con.commit()
        self.con.close()

def db_exist():
    return db_path.is_file()

def fetch_operation_times():
    with __connectDB() as (sql_con, sql_cur):
        sql_cur.execute("SELECT * FROM operation_time")
        result = sql_cur.fetchall()
    return result

def fetch_operation_time(week):
    with __connectDB() as (sql_con, sql_cur):
        sql_cur.execute('SELECT start_time, end_time from operation_time where week=:week;',{'week':week})
        sql_data = sql_cur.fetchall()
    start_time = int(sql_data[0][0])
    end_time = int(sql_data[0][1])
    return start_time, end_time

def update_operation_time(week, start_time=None, end_time=None):
    with __connectDB() as (sql_con, sql_cur):
        if start_time is not None:
            sql_cur.execute("UPDATE operation_time SET start_time = :time WHERE week = :week", {'time':start_time, 'week':week})
        if end_time is not None:
            sql_cur.execute("UPDATE operation_time SET end_time = :time WHERE week = :week", {'time':end_time, 'week':week})

def update_operation_times(weeks:list[int], start_time=None, end_time=None):
    with __connectDB() as (sql_con, sql_cur):
        if start_time is not None:
            for week in weeks:
                sql_cur.execute("UPDATE operation_time SET start_time = :time WHERE week = :week", {'time':start_time, 'week':week})
        if end_time is not None:
            for week in weeks:
                sql_cur.execute("UPDATE operation_time SET end_time = :time WHERE week = :week", {'time':end_time, 'week':week})

def fetch_restart_times():
    with __connectDB() as (sql_con, sql_cur):
        sql_cur.execute("SELECT * FROM restart_time")
        result = sql_cur.fetchall()
    return result

def fetch_restart_time(week):
    with __connectDB() as (sql_con, sql_cur):
        sql_cur.execute('SELECT time1, time2 from restart_time where week=:week;',{'week':week})
        sql_data = sql_cur.fetchall()
    start_time = int(sql_data[0][0])
    end_time = int(sql_data[0][1])
    return start_time, end_time

def update_restart_time(week, index:int, time=None):
    with __connectDB() as (sql_con, sql_cur):
        match index:
            case 1:
                sql_cur.execute("UPDATE restart_time SET time1 = :time WHERE week = :week", {'time':time, 'week':week})
            case 2:
                sql_cur.execute("UPDATE restart_time SET time2 = :time WHERE week = :week", {'time':time, 'week':week})

def update_restart_times(weeks:list[int], index:int, time=None):
    with __connectDB() as (sql_con, sql_cur):
        match index:
            case 1:
                for week in weeks:
                    sql_cur.execute("UPDATE restart_time SET time1 = :time WHERE week = :week", {'time':time, 'week':week})
            case 2:
                for week in weeks:
                    sql_cur.execute("UPDATE restart_time SET time2 = :time WHERE week = :week", {'time':time, 'week':week})

def get_setting(name:EnvName) -> str:
    with __connectDB() as (sql_con, sql_cur):
        sql_cur.execute('SELECT value from env where name=:name', {'name':name})
        sql_data = sql_cur.fetchall()
    return sql_data[0][0]

def update_setting(name:EnvName, value:str) -> None:
    with __connectDB() as (sql_con, sql_cur):
        sql_cur.execute('UPDATE env set value = :value where name=:name', {'name':name,'value':value})

def get_temp(name:TempName) -> str:
    with __connectDB() as (sql_con, sql_cur):
        sql_cur.execute('SELECT value from temp where name=:name', {'name':name})
        sql_data = sql_cur.fetchall()
    if len(sql_data) == 0:
        return ''
    else:
        return sql_data[0][0]

def update_temp(name:TempName, value:str) -> None:
    with __connectDB() as (sql_con, sql_cur):
        sql_cur.execute('INSERT INTO temp (name, value) VALUES (:name, :value) ON CONFLICT(name) DO UPDATE SET value = excluded.value;', {'name':name,'value':value})

def db_upg_0to1():
    with __connectDB() as (sql_con, sql_cur):
        db_default = [('shutdown_outside_operation_times_enabled','0'),('essential_mode_enabled','0')]
        sql_cur.executemany('INSERT INTO env VALUES (?, ?)', db_default)

UPGRADES = [db_upg_0to1]

def db_update():
    cur_db_ver = int(get_setting('ver'))
    while cur_db_ver < db_ver:
        UPGRADES[cur_db_ver]()   # 해당 단계 업그레이드 실행
        cur_db_ver += 1
        update_setting('ver', cur_db_ver)  # 버전 업데이트



########################################
##                                    ##
##              비밀번호              ##
##                                    ##
########################################

def login(pw:str) -> bool:
    # 임시 비번 : SkyRabbITs@AmenyanDaisuki!!
    # 비번 1031로 바꿈
    # 입력된 평문 비밀번호를 인코딩하고 기존 해시와 비교
    return bcrypt.checkpw(pw.encode('utf-8'), get_setting('pw').encode('utf-8'))

def __update_pw(pw:str) -> None:
    # 비밀번호를 utf-8 바이트로 인코딩 후 해싱
    hashed_pw: bytes = bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt())
    # 해시된 바이트를 다시 문자열로 디코딩하여 저장 가능
    update_setting('pw',hashed_pw.decode("utf-8"))



########################################
##                                    ##
##             OBS Studio             ##
##                                    ##
########################################

def OBSProfilesPath():
    return pathlib.Path(get_setting('obs_path')).joinpath('basic','profiles')
def OBSScenesPath():
    return pathlib.Path(get_setting('obs_path')).joinpath('basic','scenes')

def getOBSProfiles():
    result = []
    for i in OBSProfilesPath().iterdir():
        result.append(i.name)
    return result

def getOBSProfilesPath(name):
    return str(OBSProfilesPath().joinpath(name))

def getOBSScenes():
    result = []
    for i in OBSScenesPath().iterdir():
        if i.suffix == '.json':
            result.append(i.stem)
    return result

def getOBSScenesPath(name):
    return str(OBSScenesPath().joinpath(name + '.json'))






























#########################################
##                                     ##
##             Credentials             ##
##                                     ##
#########################################

def get_credentials():
    data = _get_keyring_data(f'SkyWare - LiveKiosk:Client={_get_nonce('#鈴木羽那可愛過ぎて','おえんよ部')}',_get_nonce('いきづらい部！','ラブライブ！ブルーバード'))
    if data is None:
        return None
    else:
        return json.loads(data)

def update_credentials(json):
    _update_keyring_data(f'SkyWare - LiveKiosk:Client={_get_nonce('#鈴木羽那可愛過ぎて','おえんよ部')}',_get_nonce('いきづらい部！','ラブライブ！ブルーバード'),json)

def get_secret():
    data = _get_keyring_data(f'SkyWare - LiveKiosk:Secret={_get_nonce('#鈴木羽那可愛過ぎて','おえんよ部')}',_get_nonce('シャインポスト！','Be your アイドル！'))
    if data is None:
        return None
    else:
        return json.loads(data)

def update_secret(json):
    _update_keyring_data(f'SkyWare - LiveKiosk:Secret={_get_nonce('#鈴木羽那可愛過ぎて','おえんよ部')}',_get_nonce('シャインポスト！','Be your アイドル！'),json)

def _get_nonce(before, after):
    # 1. MAC 주소 얻기 (16진수 문자열 형식)
    mac = get_setting('mac').lower()  # 예: 'a1b2c3d4e5f6'
    mac_str = ":".join([mac[i:i+2] for i in range(0, 12, 2)])  # 'a1:b2:c3:d4:e5:f6'
    result_str = f'{before}||{mac_str}||{after}'

    # 2. MD5 해시 생성
    md5_hash = hashlib.sha512(result_str.encode()).hexdigest()
    return md5_hash

def _get_key(I):
    il = I[:-21];li = I[-21:];ii = ll = l = str()
    for i in range(len(il)):ii+=(hashlib.sha512(f'{il[i]}{i+1:03d}'.encode()).hexdigest());ll+=(hashlib.sha512(f'{li[i]}{i+1:03d}'.encode()).hexdigest())
    for i in range(len(ii)):l += ii[i] + ll[i]
    return hashlib.sha256(l.encode()).digest()

def _get_keyring_data(service, id):
    data = keyring.get_password(service,id)
    if data is None:
        return None
    key = _get_key('空目ハトはアメにゃんがだーい好き好きです！アメにゃんはあたしの女神ちゃまぁなのですぅ')
    enc = base64.b64decode(data)
    iv_dec = enc[:16]
    enc_txt = enc[16:]

    cipher_dec = AES.new(key, AES.MODE_CBC, iv_dec)
    decrypted = cipher_dec.decrypt(enc_txt)
    s = decrypted.decode()
    pad_len = ord(s[-1])
    dec_text = s[:-pad_len]
    return dec_text

def _update_keyring_data(service, id, data:str):
    key = _get_key('空目ハトはアメにゃんがだーい好き好きです！アメにゃんはあたしの女神ちゃまぁなのですぅ')
    pad_len = 16 - len(data) % 16
    b_data = data + chr(pad_len) * pad_len
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(b_data.encode())
    enc_b64 = base64.b64encode(iv + encrypted).decode()
    keyring.set_password(service, id, enc_b64)

'''
file_loc = pathlib.Path(__file__).parent
if file_loc.name == 'api':
    file_loc = file_loc.parent
client_secrets_file = file_loc.joinpath('client_secret.json')
token_path = str(file_loc.joinpath('token.json'))
'''