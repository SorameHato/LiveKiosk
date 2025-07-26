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