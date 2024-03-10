import asyncio
import subprocess
import re
import sys
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Callable, Union
from urllib.parse import quote
from urllib.error import HTTPError
from .data import BrowserInstanceInfo


def make_request(url: str, method="GET") -> str:
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode("utf-8")
    except HTTPError as e:
        return f"{e.code}: {e.reason}"


def find_browser_executable_path(exe="chrome") -> str:
    """ Возвращает путь до EXE. """
    if not sys.platform == "win32":
        raise OSError("find_browser_executable_path() is only available on Windows")

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


def save_img_as(path: Union[str, Path], data: bytes) -> None:
    """ Сохраняет набор байт возвращаемый из conn.extend.makeScreenshot(), как изображение.
    :param path:    Путь, или имя файла сохраняемого изображения.
    :param data:    Данные изображения.
    """
    with open(path, "wb") as f:
        f.write(data)


async def async_util_call(function: Callable, *args) -> any:
    """ Позволяет выполнять неблокирующий вызов блокирующих функций. Например:
    await async_util_call(
        save_img_as, "ScreenShot.png", await conn.extend.makeScreenshot()
    )
    """
    return await asyncio.get_running_loop().run_in_executor(
        None, function, *args
    )


def find_instances(for_port: Optional[int] = None, browser: str = "chrome") -> Dict[int, BrowserInstanceInfo]:
    """ !!! ВНИМАНИЕ !!! На Windows 11 может быть отключен компонент WMI("Windows Management
    Instrumentation"), его нужно либо включить в разделе “Программы и компоненты” панели
    управления, либо установить из официальных источников.

    Используется для обнаружения уже запущенных браузеров в режиме отладки.
    Например:
            if browser_instances := find_instances():
                port, instance_info = [(k, v) for k, v in browser_instances.items()][0]
                browser_instance = Browser(instance_info=instance_info)
            else:
                browser_instance = Browser()

            # Или для конкретного, известного порта:
            if browser_instances := find_instances(port):
                instance_info = browser_instances[port]
                browser_instance = Browser(instance_info=instance_info)
            else:
                browser_instance = Browser()
    :param for_port:    - порт, для которого осуществляется поиск.
    :param browser:     - браузер, для которого запрашивается поиск.
    :return:
    """
    win_exp = re.compile(r"^\"[^\"]+(?<=\\)(\w+\.\w+)\".*?--remote-debugging-port=(\d+).*?(\d+)\s*$")
    linux_exp = re.compile(r"^[/\w]+/(\w+).*?--remote-debugging-port=(\d+)")

    result = {}
    if sys.platform == "win32":
        if "chrom" in browser: browser = "chrome.exe"
        elif "brave" in browser: browser = "brave.exe"
        elif "edge" in browser: browser = "msedge.exe"
        # else: ValueError("Not support browser: " + browser)
        cmd = f"WMIC PROCESS WHERE NAME='{browser}' GET Commandline,Processid"
        for line in subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout:
            if b"--type=renderer" not in line and b"--remote-debugging-port=" in line:
                name, port, pid = win_exp.findall(line.decode())[0]
                inst = BrowserInstanceInfo(
                    name=name,
                    port=(port := int(port)),
                    pid=int(pid),
                    headless=b"--headless" in line
                )
                if for_port == port:
                    return {port: inst}
                result[port] = inst

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
                name, port = linux_exp.findall(cmd_line)[0]
                inst = BrowserInstanceInfo(
                    name=name,
                    port=(port := int(port)),
                    pid=pid,
                    headless="--headless" in cmd_line
                )
                if for_port == port:
                    return {port: inst}
                result[port] = inst
    else:
        raise OSError(f"Platform '{sys.platform}' — not supported")
    return {} if for_port else result


def prepare_url(url: Union[str, bytes, None], browser_name: str, app: bool = False) -> Optional[str]:
    """ Подготавливает строку для передачи в navigate(), или в конструкторе Browser."""

    # Если url == None
    if url is None:
        return "--app=data:text/html," if app else None

    # Если передали строку
    if type(url) is str:

        # И эта строка - пустая
        if url == "":
            return "--app=data:text/html," if app else "about:blank"

        # Но если строка не содержит признаков url-адреса, то
        # считаем это HTML-разметкой
        if not url.startswith(("http", browser_name)):
            url = "data:text/html," + quote(url)
            return "--app=" + url if app else url

        # Иначе - это адрес
        return "--app=" + url if app else url

    # Иначе считаем, что это не конвертированный набор байт
    # из base64, в котором HTML-разметка
    url = "data:text/html;Base64," + url.decode()
    return "--app=" + url if app else url
