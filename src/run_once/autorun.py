import sys
import os
import pathlib
import winreg as reg

parent_folder = pathlib.Path(__file__).parent.parent
python_install_path = parent_folder.joinpath('python','PCbuild','amd64')
python_path = python_install_path.joinpath('python.exe')
script_path = parent_folder.joinpath('update.pyw')  # 현재 실행 중인 스크립트 경로
reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
key = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_path, 0, reg.KEY_SET_VALUE)
reg.SetValueEx(key, "LiveKiosk", 0, reg.REG_SZ, f'"{str(python_path)}" "{str(script_path)}"')
reg.CloseKey(key)

import os
from pathlib import Path
import pythoncom
from win32comext.shell import shell

# 현재 스크립트 파일의 폴더 경로 선택
# 상위 폴더의 settings.pyw 경로
setting_path = parent_folder.joinpath("setting.pyw")
pythonw_path = python_install_path.joinpath('pythonw.exe')
shortcut_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\LiveKiosk')
# 폴더가 없으면 생성
os.makedirs(shortcut_folder, exist_ok=True)
shortcut_path1 = os.path.join(shortcut_folder, 'LiveKiosk 설정.lnk')

shell_link1 = pythoncom.CoCreateInstance(
    shell.CLSID_ShellLink, None,
    pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
)
shell_link1.SetPath(str(pythonw_path))
shell_link1.SetArguments(f'"{str(setting_path)}"')
shell_link1.SetDescription('LiveKiosk의 설정을 엽니다.')
persist_file = shell_link1.QueryInterface(pythoncom.IID_IPersistFile)
persist_file.Save(shortcut_path1, 0)

shortcut_path3 = os.path.join(shortcut_folder, 'LiveKiosk.lnk')
init_path = parent_folder.joinpath("init.pyw")

shell_link3 = pythoncom.CoCreateInstance(
    shell.CLSID_ShellLink, None,
    pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
)
shell_link3.SetPath(str(pythonw_path))
shell_link3.SetArguments(f'"{str(init_path)}"')
shell_link3.SetDescription('LiveKiosk를 실행합니다. LiveKiosk는 보통 컴퓨터를 켤 때 자동으로 실행되므로, 이 프로그램은 오류가 발생해 자동으로 실행되지 않은 경우나 테스트용으로만 실행해 주세요.')
persist_file = shell_link3.QueryInterface(pythoncom.IID_IPersistFile)
persist_file.Save(shortcut_path3, 0)

shortcut_path2 = os.path.join(shortcut_folder, 'LiveKiosk 설치폴더.lnk')

shell_link2 = pythoncom.CoCreateInstance(
    shell.CLSID_ShellLink, None,
    pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
)
shell_link2.SetPath(str(parent_folder))  # 바로가기가 열 폴더 경로 설정
shell_link2.SetDescription('LiveKiosk가 설치된 폴더를 엽니다.')
persist_file = shell_link2.QueryInterface(pythoncom.IID_IPersistFile)
persist_file.Save(shortcut_path2, 0)

obs_path = pathlib.Path(os.getenv('APPDATA')).joinpath('obs-studio')
obs_setting_ini = obs_path.joinpath('user.ini')
python_Settings_Found = False
if not obs_setting_ini.is_file():
    obs_setting_ini = obs_path.joinpath('global.ini')
with obs_setting_ini.open('r',encoding='utf-8-sig') as f:
    global_txt = f.readlines()
for i in range(len(global_txt)):
    if global_txt[i].startswith('Path64bit='):
        python_Settings_Found = True
        global_txt[i] = 'Path64bit=' + str(python_install_path) + '\n'
        break
if not python_Settings_Found:
    global_txt.append('\n','[Python]\n','Path64bit=' + str(python_install_path) + '\n')
with obs_setting_ini.open('w', encoding='utf-8-sig') as f:
    f.writelines(global_txt)