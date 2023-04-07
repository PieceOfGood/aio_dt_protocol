import asyncio
import sys, re
import urllib.request
if sys.platform == "win32":
    import winreg


def get_request(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode('utf-8')


def registry_read_key(exe="chrome") -> str:
    """ Возвращает путь до EXE.
    """
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


def save_img_as(path: str, data: bytes)-> None:
    """ Сохраняет по пути 'path' набор байт 'data', которые можно прислать
    из метода страницы MakeScreenshot()
    """
    with open(path, "wb") as f:
        f.write(data)


async def async_util_call(function: callable, *args) -> any:
    """ Позволяет выполнять неблокирующий вызов блокирующих функций. Например:
    await async_util_call(
        save_img_as, "ScreenShot.png", await page_instance.MakeScreenshot()
    )
    """
    return await asyncio.get_running_loop().run_in_executor(
        None, function, *args
    )
