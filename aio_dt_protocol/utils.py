import asyncio
import subprocess
import re
import sys
import urllib.request
from typing import Optional, Dict, Callable


def get_request(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode('utf-8')


def find_browser_executable_path(exe="chrome") -> str:
    """ Возвращает путь до EXE. """
    if not sys.platform == "win32":
        raise OSError("registry_read_key() is only available on Windows")

    if exe == "chromium":
        import os
        from pathlib import Path

        app_data = Path(os.getenv('APPDATA')).parent
        browser_path = app_data / "Local/Chromium/Application/chrome.exe"
        if not browser_path.exists():
            return ""
        return browser_path.as_posix()

    import winreg

    reg_path = f"HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{exe}.exe"
    key, path = re.findall(r"(^[^\\/]+)[\\/](.*)", reg_path)[0]
    connect_to = eval(f"winreg.{key}")
    try: h_key = winreg.OpenKey( winreg.ConnectRegistry(None, connect_to), path )
    except FileNotFoundError: return ""
    result = winreg.QueryValue(h_key, None)
    winreg.CloseKey(h_key)
    return result


def log(data: any = "", lvl: str = "[<- V ->]", eol: str = "\n") -> None:
    print(f"\x1b[32m{lvl} \x1b[38m\x1b[3m{data}\x1b[0m", end=eol)


def save_img_as(path: str, data: bytes) -> None:
    """ Сохраняет по пути 'path' набор байт 'data', которые можно прислать
    из метода страницы MakeScreenshot()
    """
    with open(path, "wb") as f:
        f.write(data)


async def async_util_call(function: Callable, *args) -> any:
    """ Позволяет выполнять неблокирующий вызов блокирующих функций. Например:
    await async_util_call(
        save_img_as, "ScreenShot.png", await page_instance.MakeScreenshot()
    )
    """
    return await asyncio.get_running_loop().run_in_executor(
        None, function, *args
    )


def find_instances(for_port: Optional[int] = None, browser: str = "chrome") -> Dict[int, int]:
    """ !!! ВНИМАНИЕ !!! На Windows 11 может быть отключен компонент WMI("Windows Management
    Instrumentation"), его нужно либо включить в разделе “Программы и компоненты” панели
    управления, либо установить из официальных источников.

    Используется для обнаружения уже запущенных браузеров в режиме отладки.
    Например:
            if browser_instances := find_instances():
                port, pid = [(k, v) for k, v in browser_instances.items()][0]
                browser_instance = Browser(debug_port=port, chrome_pid=pid)
            else:
                browser_instance = Browser()

            # Или для конкретного, известного порта:
            if browser_instances := find_instances(port):
                pid = browser_instances[port]
                browser_instance = Browser(debug_port=port, chrome_pid=pid)
            else:
                browser_instance = Browser()
    :param for_port:    - порт, для которого осуществляется поиск.
    :param browser:     - браузер, для которого запрашивается поиск.
    :return:            - словарь, ключами которого являются используемые порты запущенных
                            браузеров, а значениями, их ProcessID, или пустой словарь,
                            если ничего не найдено.
                            { 9222: 16017, 9223: 2001, ... }
    """
    result = {}
    if sys.platform == "win32":
        if "chrom" in browser: browser = "chrome.exe"
        elif "brave" in browser: browser = "brave.exe"
        elif "edge" in browser: browser = "msedge.exe"
        # else: ValueError("Not support browser: " + browser)
        cmd = f"WMIC PROCESS WHERE NAME='{browser}' GET Commandline,Processid"
        for line in subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout:
            if b"--type=renderer" not in line and b"--remote-debugging-port=" in line:
                port, pid = re.findall(r"--remote-debugging-port=(\d+).*?(\d+)\s*$", line.decode())[0]
                port, pid = int(port), int(pid)
                if for_port == port: return {port: pid}
                result[port] = pid

    elif sys.platform == "linux":
        if "chrom" in browser: browser = "chrome"
        elif "brave" in browser: browser = "brave"
        elif "edge" in browser: browser = "msedge"
        # else: ValueError("Not support browser: " + browser)
        try: itr = map(int, subprocess.check_output(["pidof", browser]).split())
        except subprocess.CalledProcessError: itr = []
        for pid in itr:
            with open("/proc/" + str(pid) + "/cmdline") as f: cmd_line =  f.read()[:-1]
            if "--type=renderer" not in cmd_line and "--remote-debugging-port=" in cmd_line:
                port = int(re.findall(r"--remote-debugging-port=(\d+)", cmd_line)[0])
                if for_port == port: return {port: pid}
                result[port] = pid
    else:
        raise OSError(f"Platform '{sys.platform}' — not supported")
    return {} if for_port else result
