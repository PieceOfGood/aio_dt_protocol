import asyncio
import urllib.request
from urllib.parse import quote
import json, re, os, sys, signal, subprocess
from os.path import expanduser
if sys.platform == "win32": import winreg
from typing import Callable, List, Dict, Union, Optional, Awaitable, Tuple
from aio_dt_protocol.Page import Page

class Browser:

    @staticmethod
    def FindInstances(for_port: int = None, browser: str = "chrome.exe") -> Dict[int, int]:
        """
        WINDOWS ONLY
        Используется для обнаружения уже запущенных инстансов браузера в режиме отладки.
        Например:
                if browser_instances := Browser.FindInstances():
                    port, pid = [(k, v) for k, v in browser_instances.items()][0]
                    browser_instance = Browser(debug_port=port, chrome_pid=pid)
                else:
                    browser_instance = Browser()

                # Или для конкретного, известного порта:
                if browser_instances := Browser.FindInstances(port):
                    pid = browser_instances[port]
                    browser_instance = Browser(debug_port=port, chrome_pid=pid)
                else:
                    browser_instance = Browser()
        :param browser:     - браузер, для которого запрашивается поиск.
        :param for_port:    - порт, для которого осуществляется поиск.
        :return:            - словарь, ключами которого являются используемые порты запущенных
                                браузеров, а значениями, их ProcessID, или пустой словарь,
                                если ничего не найдено.
                                { 9222: 16017, 9223: 2001, ... }
        """
        result = {}; all_data = []; count = 0; browser = browser.encode()
        cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        for line in proc.stdout:
            if browser in line and b"--remote-debugging-port=" in line:
                s_line = line.decode("utf-8"); count += 1
                all_data.append(re.findall(r"--remote-debugging-port=(\d+).*?(\d+)\s*$", s_line)[0])
        while count > 0:
            count -= 1; port, pid = int(all_data[count][0]), int(all_data[count][1])
            if for_port is None: result[port] = pid; break
            elif for_port == port: result[port] = pid
        return result

    def __init__(
            self,
            profile_path: Optional[str] = "testProfile",
            dev_tool_profiles:      Optional[bool] = False,
            url: Optional[Union[str, bytes, None]] = None,
            flags:       Optional[list] = None,
            default_tab: Optional[bool] = False,
            browser_path: Optional[str] = "",
            debug_port:   Optional[any] = 9222,
            browser_pid:  Optional[int] = 0,
            app:         Optional[bool] = False,
            browser_exe:  Optional[str] = "chrome",
            proxy_port:   Optional[any] = "",
            verbose:     Optional[bool] = False,
            position: Optional[Tuple[int, int]] = None,
            sizes:    Optional[Tuple[int, int]] = None,
            f_no_first_run:  Optional[bool] = True,
            f_default_check: Optional[bool] = True,
            f_browser_test:  Optional[bool] = False,
            f_incognito:     Optional[bool] = False,
            f_kiosk:         Optional[bool] = False,

    ) -> None:
        """
        Все параметры — не обязательны.
        ==============================================================================================
        Refused Error: <urlopen error [Errno 111] Connection refused>
        !!! ВНИМАНИЕ !!! — на Linux, после получения инстанса браузера, часто встречается
            невозможность установить HTTP соединение для получения инстансов его страниц(табов/вкладок).
            Связано это(возможно) с тем, что браузер ещё не успел инициализировать свои службы.
            Преодолевается простым ожиданием, например:
                while True:
                    try:
                        while (page := await browser.GetPage()) is None:
                            await asyncio.sleep(.1)
                        break
                    except urllib.error.URLError as e:
                        await asyncio.sleep(.5)
        ==============================================================================================

        :param profile_path:    Путь до каталога, в который будет сохранена сессия профиля.
                                    Если не передан, или указано название папки, браузер
                                    сам создаст папку, по месту вызывающего кода. Если указан
                                    несуществующий путь, он будет создан.

                                        [-!!!-] ВАЖНО [-!!!-] - для запуска в режиме "headless",
                                        в "profile_path" нужно передать пустую строку.

        :param dev_tool_profiles:   Если 'profile_path' указан как имя папки, а не путь,
                                    профиль с указанным именем будет создан/получен в домашней
                                    дирректории пользователя, из каталога 'DevTools_Profiles',
                                    если значение установлено в True. (Linux, Windows)

        :param url:             Адрес, которым будет инициирован старт браузера.
                                    Со значением по умолчанию, будет открыта пустая страница.

        :param flags:           Список аргументов командной строки. Например:
                                    [ "--no-first-run", "--no-default-browser-check", "--browser-test",
                                    "--window-position=400,100", "--window-size=800,600", ... ]
                                    https://peter.sh/experiments/chromium-command-line-switches/

        :param default_tab:     Если 'True' вкладка будет открыта с дефолтным бэкграундом, как если бы
                                    пользователь открыл её обычным способом, не зависимо от того, что
                                    было передано в параметре 'url'.

        :param browser_path:    Путь до исполняемого файла браузера. Если не указан, в реестре
                                    будет произведён поиск установленного браузера Chrome.

        :param debug_port:      Используется порт по умолчанию 9222.

        :param browser_pid:     ProcessID браузера. Используется методом KillChrome(). Если
                                    передано значение большее нуля, считается, что производится
                                    подключение к уже существующему инстансу браузера. Подробнее
                                    в описании статического метода FindInstances().

        :param app:             Запускает браузер в окне без пользовательского интерфейса,
                                    вроде адресной строки, кнопок навигации и прочих атрибутов.
                                    Распространяется только на первый инстанс страниц браузера,
                                    что означает, что все следующие инстансы будут открываться
                                    в интерфейсе страниц браузера, в отдельном от первого окне.

        :param browser_exe:     Имя исполняемого файла браузера, который будет автоматизирован.
                                    Например: chrome, brave. Если 'browser_path' окажется пустым,
                                    путь до исполняемого файла будет найден в реестре.

        :param proxy_port:      Если установлено, браузер будет запущен с флагом 'proxy' и
                                    все его запросы будут перенаправляться на этот порт, на
                                    локальном хосте.

        :param verbose:         Печатать некие подробности процесса?

        :param position:        Кортеж с иксом и игреком, в которых откроется окно браузера.
                                    Не имеет смысла для Headless.

        :param sizes:           Кортеж с длиной и шириной в которые будет установлено окно браузера.
                                    Не имеет смысла для Headless.

        :param f_no_first_run:  По умолчанию True == добавляет к флагам запуска, отключающий
                                    процедуру ознакомиления с браузером.

        :param f_default_check: По умолчанию True == добавляет к флагам запуска, отключающий
                                    проверку "браузера по умолчанию". Полезно при тестах, чтобы
                                    UI браузера не перегружался ненужным функционалом.

        :param f_browser_test:  По умолчанию False == добавляет к флагам запуска, признак
                                    тестирования, что в конечном итоге, должно положительно
                                    сказываться на стабильности некоторых тестов(например,
                                    мониторинг нехватки памяти)

        :param f_incognito:     По умолчанию False == добавляет к флагам запуска, incognito,
                                    запускающий браузет в соответствующем режиме.

        :param f_kiosk:         По умолчанию False == добавляет к флагам запуска, kiosk,
                                    запускающий браузет в соответствующем режиме.
        """

        self.dev_tool_profiles = dev_tool_profiles if profile_path else False

        if self.dev_tool_profiles and not re.search(r"[\\/]", profile_path):
            self.profile_path = os.path.join(expanduser("~"), "DevTools_Profiles", profile_path)
        else:
            self.profile_path = profile_path

        self.first_run = profile_path == "" or not os.path.exists(profile_path)

        if browser_exe == "chrome":
            self.browser_name = "chrome"
            browser_exe = "chrome" if sys.platform == "win32" else "google-chrome"
        elif browser_exe == "brave":
            self.browser_name = "brave"
            browser_exe = "brave" if sys.platform == "win32" else "brave-browser"
        else:
            raise ValueError(browser_exe + " — not supported")

        # ? Константы URL соответствующих вкладок
        self.NEW_TAB:       str = self.browser_name + "://newtab/"          # дефолтная вкладка
        self.SETTINGS:      str = self.browser_name + "://settings/"        # настройки
        self.BRAVE_REWARDS: str = self.browser_name + "://rewards/"         # вознаграждения (brave only)
        self.HISTORY:       str = self.browser_name + "://history/"         # история переходов
        self.BOOKMARKS:     str = self.browser_name + "://bookmarks/"       # закладки
        self.DOWNLOADS:     str = self.browser_name + "://downloads/"       # загрузки
        self.BRAVE_WALLET:  str = self.browser_name + "://wallet/"          # кошельки (brave only)
        self.EXTENSIONS:    str = self.browser_name + "://extensions/"      # расширения

        if sys.platform == "win32":
            browser_path = browser_path if browser_path else registry_read_key(browser_exe)
        elif sys.platform == "linux":
            browser_path = browser_path if browser_path else os.popen("which " + browser_exe).read().strip()
        else: raise OSError(f"Платформа '{sys.platform}' — не поддерживается")

        if not os.path.exists(browser_path) or not os.path.isfile(browser_path):
            raise FileNotFoundError(f"Переданный 'browser_path' => '{browser_path}' — не существует, или содержит ошибку")
        self.browser_path = browser_path

        if int(debug_port) <= 0:
            raise ValueError(f"Значение 'debug_port' => '{debug_port}' — должно быть положителным целым числом!")
        self.debug_port = str(debug_port)
        self.proxy_port = str(proxy_port)
        self.verbose = verbose

        # https://stackoverflow.com/questions/2381241/what-is-the-subprocess-popen-max-length-of-the-args-parameter
        # data_url_len_is_high = len(url[0]) > 32_767
        data_url_len = len(url) if url else 0
        if data_url_len > 30_000:
            Warning(f"Length data url ({data_url_len}) is approaching to critical length = 32767 symbols!")

        if default_tab:
            url = self.NEW_TAB
            # ! app не может быть True, если браузер стартует с дефолтной страницы
            app = False

        b_name_len = len(self.browser_name)
        # Если "app" == True:
        _url_ = (
            # открыть dataURL без содержимого, если в "url" ничего не передано
            "--app=data:text/html," if url is None else
                # иначе установить переданную разметку, если она пришла как строка
                # и начало этой строки не содержит признаков url-адреса
                "--app=data:text/html," + quote(url)
                    if type(url) is str and "http" != url[:4] and self.browser_name != url[:b_name_len] else "--app=" + url
                        # передать "как есть", раз это строка содержащая url
                        if type(url) is str and "http" == url[:4] or self.browser_name == url[:b_name_len] else
                            # иначе декодировать и установить её как Base64
                            "--app=data:text/html;Base64," + url.decode()

            # иначе, открыть пустую страницу, если в "url" ничего не передано
        ) if app else "about:blank" if url is None else (
            # иначе передать разметку как data-url, если начало этой строки
            # не содержит признаков url-адреса
            "data:text/html," + quote(url)
                if type(url) is str and "http" != url[:4] and self.browser_name != url[:b_name_len] else url
                    # или передать "как есть", раз это строка содержащая url
                    if type(url) is str and "http" == url[:4] or self.browser_name == url[:b_name_len] else
                        # иначе декодировать и установить её как Base64
                        "data:text/html;Base64," + url.decode()
        )

        self.position = position
        self.sizes    = sizes
        self.f_no_first_run  = f_no_first_run
        self.f_default_check = f_default_check
        self.f_browser_test  = f_browser_test
        self.f_incognito     = f_incognito
        self.f_kiosk         = f_kiosk
        self.browser_pid = browser_pid if browser_pid > 0 else self._RunBrowser(_url_, flags)

    def _RunBrowser(self, url: str, flags: list) -> int:
        """
        Запускает браузер с переданными флагами.
        :param url:             Адрес. Если передан, будет загружен в первой вкладке.
        :param flags:           Флаги
        :return:                ProcessID запущенного браузера
        """

        run_args = [
            self.browser_path,
            f"--remote-debugging-port={self.debug_port}",
            "--disable-gpu-shader-disk-cache", "--disable-sync-preferences",
            ("--log-file=null" if sys.platform == "win32" else "--log-file=/dev/null"),
            "--force-dark-mode", "--enable-features=WebUIDarkMode",
            ("--disk-cache-dir=null" if sys.platform == "win32" else "--disk-cache-dir=/dev/null"),
            "--disk-cache-size=1000000"
        ]

        # ! Default mode
        if self.profile_path:
            run_args.append( f"--user-data-dir={self.profile_path}")
            if self.position is not None:
                run_args.append("--window-position={},{}".format(*self.position))
            if self.sizes is not None:
                run_args.append("--window-size={},{}".format(*self.sizes))

        # ! Headless mode
        else: run_args += ["--disable-gpu", "--headless"]

        if self.f_no_first_run:  run_args.append("--no-first-run")
        if self.f_default_check: run_args.append("--no-default-browser-check")
        if self.f_browser_test:  run_args.append("--browser-test")
        if self.f_incognito:     run_args.append("--incognito")
        if self.f_kiosk:         run_args.append("--kiosk")

        if self.proxy_port:
            run_args.append("--proxy-server=http://127.0.0.1:" + self.proxy_port)
            if self.verbose:
                print(f"[<- V ->] | --- Запуск браузера на порту '{self.debug_port}' с проксификацией " +
                      f"на локальном хосте, через порт '{self.proxy_port}' --- |")
        else:
            if self.verbose:
                print(f"[<- V ->] | --- Запуск браузера на порту '{self.debug_port}' --- |")

        run_args.append(url)

        if flags is not None:
            run_args += flags
        return subprocess.Popen(run_args).pid

    def KillBrowser(self) -> None:
        """
        "Убивает" процесс браузера. Рекомендуется только в крайних случаях.
            Лучше всего вызывать метод Call("Browser.close") у инстанса страницы
        :return:
        """
        try: os.kill(self.browser_pid, signal.SIGTERM)
        except PermissionError: pass

    async def GetPageList(self) -> List[dict]:
        """
        Запрашивает у браузера список всех его дочерних процессов,
        включая табы(вкладки/страницы), воркеры, расширения, сервисы и прочее.

        :return: [ {
                    "description": "",
                    "devtoolsFrontendUrl": "/devtools/inspector.html?ws=localhost:9222/devtools/page/DAB7FB6187B554E10B0BD18821265734",
                    "id": "DAB7FB6187B554E10B0BD18821265734",
                    "title": "Yahoo",
                    "type": "page",
                    "url": "https://www.yahoo.com/",
                    "webSocketDebuggerUrl": "ws://localhost:9222/devtools/page/DAB7FB6187B554E10B0BD18821265734"
                }, { ... } ]
        """
        result = await self._Get(f"http://127.0.0.1:{self.debug_port}/json/list")
        if self.verbose: print("[<- V ->] GetPageList() => " + result)
        return json.loads( result )

    async def GetPageBy(
            self, key: Union[str, int], value: Union[str, int],
            match_mode: Optional[str] = "exact", index: Optional[int] = 0,
            callback: Optional[Awaitable] = None
    ) -> Union[Page, None]:
        """
        Организует выбор нужного инстанса из процессов браузера по следующим критериям:
        :param key:                 По ключу из словаря. Список ключей смотри
                                        в возвращаемых значениях GetPageList()
        :param value:               Значение ключа, которому должен соответствовать выбор
        :param match_mode:          Значение ключа:
                                        "exact"      - полностью совпадает с value,
                                        "contains"   - содержит value,
                                        "startswith" - начинается с value
        :param index:               Поскольку открытых страниц с одинаковым ключём может
                                        быть несколько, предоставляется возможность выбрать
                                        по индексу. По умолчанию = 0
        :param callback:            Корутина, которой будет передаваться контекст абсолютно
                                        всех событий страницы в виде словаря. Если передан,
                                        включает уведомления домена "Runtime" для общения
                                        со страницей.
                                            https://chromedevtools.github.io/devtools-protocol/tot/Console#method-enable

        :return:        <Page> - инстанс страницы с подключением по WebSocket или None, если не найдено
        """
        counter = 0; v = value.lower()
        for page_data in await self.GetPageList():
            data = page_data[key].lower()
            if ((match_mode == "exact" and data == v)
                or (match_mode == "contains" and data.find(v) > -1 )
                    or (match_mode == "startswith" and data.find(v) == 0)) and counter == index:
                page = Page(
                    page_data["webSocketDebuggerUrl"],
                    page_data["id"],
                    callback,
                    self.profile_path == "",
                    self.verbose,
                    self.browser_name
                )
                await page.Activate()
                return page
            counter += 1
        return None

    async def GetPage(
            self,
            index: Optional[int] = 0, page_type: Optional[str] = "page",
            callback: Optional[Callable[[dict], Awaitable[None]]] = None
    ) -> 'Page':
        """
        Получает страницу браузера по индексу. По умолчанию, первую.
        :param index:       - Желаемый индекс страницы начиная с нуля.
        :param page_type:   - Тип 'page' | 'background_page' | 'service_worker' | ???
        :param callback:    - Корутина, которой будет передаваться контекст абсолютно
                                всех событий страницы в виде словаря.
        :return:        <Page>
        """
        return await self.GetPageBy("type", page_type, "exact", index, callback)

    async def GetPageByID(
            self, page_id: str,
            callback: Optional[Callable[[dict], Awaitable[None]]] = None
    ) -> 'Page':
        """
        Получает страницу браузера по уникальному идентификатору.
        :param page_id:     - Желаемый идентификатор страницы. Метод GetPageList()
                                возвращает список доступных инстансов и словарь
                                каждого из них содержит 'id'. Так же создание инстансов
                                страниц через домен 'Target' возвращает 'targetId',
                                который используется с этой же целью.
        :param callback:    - Корутина, которой будет передаваться контекст абсолютно
                                всех событий страницы в виде словаря.
        :return:        <Page>
        """
        return await self.GetPageBy("id", page_id, "exact", 0, callback)

    async def GetPageByTitle(
            self, value: str,
            match_mode: Optional[str] = "startswith", index: Optional[int] = 0,
            callback: Optional[Callable[[dict], Awaitable[None]]] = None
    ) -> 'Page':
        """
        Получает страницу браузера по заголовку. По умолчанию, первую.
        :param value:       - Текст, который будет сопоставляться при поиске.
        :param match_mode:  - Тип сопоставления(по умолчанию 'startswith').
                                Может быть только:
                                    * exact      - полное соответствие заголовка и value
                                    * contains   - заголовок содержит value
                                    * startswith - заголовок начинается с value
        :param index:       - Желаемый индекс страницы начиная с нуля.
        :param callback:    - Корутина, которой будет передаваться контекст абсолютно
                                всех событий страницы в виде словаря.
        :return:        <Page>
        """
        return await self.GetPageBy("title", value, match_mode, index, callback)

    async def GetPageByURL(
            self, value: str,
            match_mode: Optional[str] = "startswith", index: Optional[int] = 0,
            callback: Optional[Callable[[dict], Awaitable[None]]] = None
    ) -> 'Page':
        """
        Получает страницу браузера по её URL. По умолчанию, первую.
        :param value:       - Текст, который будет сопоставляться при поиске.
        :param match_mode:  - Тип сопоставления(по умолчанию 'startswith').
                                Может быть только:
                                    * exact      - полное соответствие URL и value
                                    * contains   - URL содержит value
                                    * startswith - URL начинается с value
        :param index:       - Желаемый индекс страницы начиная с нуля.
        :param callback:    - Корутина, которой будет передаваться контекст абсолютно
                                всех событий страницы в виде словаря.
        :return:        <Page>
        """
        return await self.GetPageBy("url", value, match_mode, index, callback)

    @staticmethod
    async def _Get(url: str) -> str:
        return await asyncio.get_running_loop().run_in_executor(
            None, get_request, url
        )


def get_request(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode('utf-8')


def registry_read_key(exe="chrome") -> str:
    reg_path = f"HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{exe}.exe"
    key, path = re.findall(r"(^[^\\\/]+)[\\\/](.*)", reg_path)[0]
    connect_to = eval(f"winreg.{key}")
    try: h_key = winreg.OpenKey( winreg.ConnectRegistry(None, connect_to), path )
    except FileNotFoundError: return ""
    result = winreg.QueryValue(h_key, None)
    winreg.CloseKey(h_key)
    return result


async def test():
    async def printer(data: dict):
        print(data)
    js = """
        document.querySelector('body').addEventListener('click', (e) => { console.log(`Click at ${e.clientX}x ${e.clientY}y`) });
    """
    state = 0
    data_url = "<h1>Hello world!</h1>"
    chrome_instances = Browser.FindInstances()
    if chrome_instances:
        port, pid = [(k, v) for k, v in chrome_instances.items()][0]
        c_rdp = Browser(debug_port=port, browser_pid=pid)
        state = 1
    else:
        c_rdp = Browser(url=data_url, app=True, flags=["--window-position=400,100", "--window-size=1000,1000"])

    print(await c_rdp.GetPageList())
    print("pid =", c_rdp.browser_pid)

    page = await c_rdp.GetPage(callback=printer)
    print("\n", page.ws_url, "\n")

    await asyncio.sleep(5)

    if state:
        await page.Call("Page.navigate", {"url": "https://google.com/"})
    else:
        await page.Call("Page.navigate", {"url": "https://www.python.org/"})

    await asyncio.sleep(5)

    result = await page.Eval(js)
    print("Eval() =>", result)

    # await page.Detach()

    while page.connected:
        await asyncio.sleep(1)

    print("Page disconnected")

if __name__ == '__main__':

    asyncio.run(test())



