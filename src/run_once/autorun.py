import sys
import os
import pathlib
import winreg as reg

python_path = sys.executable  # 실행 중인 python.exe 경로
script_path = str(pathlib.Path(os.path.abspath(__file__)).parent.parent.joinpath('update.pyw'))  # 현재 실행 중인 스크립트 경로
reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
key = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_path, 0, reg.KEY_SET_VALUE)
reg.SetValueEx(key, "LiveKiosk", 0, reg.REG_SZ, f'"{python_path}" "{script_path}"')
reg.CloseKey(key)

import os
from pathlib import Path
import pythoncom
from win32comext.shell import shell, shellcon
from pyshortcuts import make_shortcut

# 현재 스크립트 파일의 폴더 경로 선택
# 상위 폴더의 settings.pyw 경로
parent_folder = Path(__file__).parent.parent
setting_path = parent_folder.joinpath("setting.pyw")
pythonw_path = os.path.join(sys.exec_prefix, 'pythonw.exe')
shortcut_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\LiveKiosk')
# 폴더가 없으면 생성
os.makedirs(shortcut_folder, exist_ok=True)
shortcut_path1 = os.path.join(shortcut_folder, 'LiveKiosk 설정.lnk')

shell_link1 = pythoncom.CoCreateInstance(
    shell.CLSID_ShellLink, None,
    pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
)
shell_link1.SetPath(pythonw_path)
shell_link1.SetArguments(f'"{setting_path}"')
shell_link1.SetDescription('LiveKiosk의 설정을 엽니다.')
persist_file = shell_link1.QueryInterface(pythoncom.IID_IPersistFile)
persist_file.Save(shortcut_path1, 0)


shortcut_path2 = os.path.join(shortcut_folder, 'LiveKiosk 설치폴더.lnk')

shell_link2 = pythoncom.CoCreateInstance(
    shell.CLSID_ShellLink, None,
    pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
)
shell_link2.SetPath(str(parent_folder))  # 바로가기가 열 폴더 경로 설정
shell_link2.SetDescription('LiveKiosk가 설치된 폴더를 엽니다.')
persist_file = shell_link2.QueryInterface(pythoncom.IID_IPersistFile)
persist_file.Save(shortcut_path2, 0)