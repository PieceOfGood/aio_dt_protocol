import asyncio
from urllib.error import URLError

try:
    import ujson as json
    HAS_UJSON = True
except ModuleNotFoundError:
    HAS_UJSON = False
    import json
import warnings
import re, os, sys, signal, subprocess
from urllib.parse import quote
from os.path import expanduser
from inspect import iscoroutinefunction
from typing import List, Dict, Union, Optional, Tuple
from collections.abc import Sequence
from enum import Enum
from .connection import Connection
from .data import TargetConnectionInfo, TargetConnectionType, CommonCallback
from .exceptions import FlagArgumentContainError, NoTargetWithGivenIdFound
from .utils import get_request, registry_read_key, log, async_util_call


class Browser:

    def __init__(
            self,
            profile_path: str = "testProfile",
            dev_tool_profiles:  bool = False,
            url: Optional[Union[str, bytes]] = None,
            flags:  Optional["FlagBuilder"] = None,
            browser_path: str = "",
            debug_port:   Union[str, int] = 9222,
            browser_pid:  int = 0,
            app:         bool = False,
            browser_exe:  str = "chrome",
            proxy_address:str = "http://127.0.0.1",
            proxy_port:   Union[str, int] = "",
            verbose:     bool = False,
            position: Optional[Tuple[int, int]] = None,
            sizes:    Optional[Tuple[int, int]] = None,
            prevent_restore: bool = False,

    ) -> None:
        """
        Все параметры — не обязательны.
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

        :param prevent_restore: Предотвращать восстановление предыдущей сессии после крашей.
        """
        if sys.platform not in ("win32", "linux"): raise OSError(f"Platform '{sys.platform}' — not supported")
        self.dev_tool_profiles = dev_tool_profiles if profile_path else False

        if verbose and not HAS_UJSON:
            log("Call 'python -m pip install ujson' for install", lvl="[- UJSON IS NOT INSTALLED -]")

        if self.dev_tool_profiles:
            self.profile_path = os.path.join(expanduser("~"), "DevTools_Profiles", profile_path)
        elif profile_path != "":
            self.profile_path = os.path.abspath(profile_path)
        else:
            self.profile_path = ""

        preferences_path = ""
        if self.profile_path:
            preferences_path = os.path.join(self.profile_path, "Default", "Preferences")

        self.first_run = self.profile_path == "" or not os.path.exists(self.profile_path)

        # ? Предотвращать восстановление предыдущей сессии
        if not self.first_run and prevent_restore and preferences_path and os.path.exists(preferences_path):
            READ_WRITE = 33206 if sys.platform == "win32" else 33152
            READ_ONLY  = 33060 if sys.platform == "win32" else 33024
            # print("file attr =", os.stat(preferences_path).st_mode)
            # ? НЕ только для чтения
            if os.stat(preferences_path).st_mode == READ_WRITE:
                with open(preferences_path, "r") as f:
                    preferences = f.read()
                # ? тип завершения
                if exit_type := re.search(r'"exit_type":"(\w+)"', preferences):
                    # ? НЕ нормальный
                    if exit_type.group(1) != "Normal":
                        result = re.sub(r'"exit_type":"\w+"', '"exit_type":"Normal"', preferences)
                        with open(preferences_path, "w") as f: f.write(result)
                # ? Только для чтения
                # os.chmod(preferences_path, READ_ONLY)
                if verbose: log("Файл настроек — изменён и сохранён")
            else:
                # os.chmod(preferences_path, READ_WRITE)
                if verbose: log("Файл настроек — только для чтения")

        if browser_exe == "chrome":
            self.browser_name = "chrome"
            browser_exe = "chrome" if sys.platform == "win32" else "google-chrome"
        elif browser_exe == "brave":
            self.browser_name = "brave"
            browser_exe = "brave" if sys.platform == "win32" else "brave-browser"
        elif browser_exe == "chromium":
            self.browser_name = "chrome"
            browser_exe = "chrome" if sys.platform == "win32" else "chromium-browser"
        elif "edge" in browser_exe:
            self.browser_name = "edge"
            browser_exe = "msedge" if sys.platform == "win32" else "msedge" # !?

        # ? Константы URL соответствующих вкладок
        self.NEW_TAB:       str = self.browser_name + "://newtab/"          # дефолтная вкладка
        self.SETTINGS:      str = self.browser_name + "://settings/"        # настройки
        self.BRAVE_REWARDS: str = self.browser_name + "://rewards/"         # вознаграждения (brave only)
        self.HISTORY:       str = self.browser_name + "://history/"         # история переходов
        self.BOOKMARKS:     str = self.browser_name + "://bookmarks/"       # закладки
        self.DOWNLOADS:     str = self.browser_name + "://downloads/"       # загрузки
        self.WALLET:        str = self.browser_name + "://wallet/"          # кошельки (brave only)
        self.EXTENSIONS:    str = self.browser_name + "://extensions/"      # расширения
        self.FLAGS:         str = self.browser_name + "://flags/"           # экспериментальные технологии

        if sys.platform == "win32":
            browser_path = browser_path if browser_path else registry_read_key(browser_exe)
        else:   #  ! sys.platform == "linux"
            browser_path = browser_path if browser_path else os.popen("which " + browser_exe).read().strip()

        if not os.path.exists(browser_path) or not os.path.isfile(browser_path):
            raise FileNotFoundError(f"Переданный 'browser_path' => '{browser_path}' — не существует, или содержит ошибку")
        self.browser_path = browser_path

        if int(debug_port) <= 0:
            raise ValueError(f"Значение 'debug_port' => '{debug_port}' — должно быть положительным целым числом!")
        self.debug_port = str(debug_port)
        self.proxy_addres = proxy_address
        self.proxy_port = str(proxy_port)
        self.verbose = verbose

        # https://stackoverflow.com/questions/2381241/what-is-the-subprocess-popen-max-length-of-the-args-parameter
        # data_url_len_is_high = len(url[0]) > 32_767
        data_url_len = len(url) if url else 0
        # print("url =", url)
        if data_url_len > 30_000:
            warnings.warn(f"Length data url ({data_url_len}) is approaching to critical length = 32767 symbols!")

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

        self.is_headless_mode = False
        self.browser_pid = browser_pid if browser_pid > 0 else self._RunBrowser(_url_, flags, position, sizes)

    def _RunBrowser(self, url: str, flags: "FlagBuilder", position: Optional[Tuple[int, int]] = None,
                    sizes: Optional[Tuple[int, int]] = None) -> int:
        """
        Запускает браузер с переданными флагами.
        :param url:             Адрес. Если передан, будет загружен в первой вкладке.
        :param flags:           Флаги
        :return:                ProcessID запущенного браузера
        """
        flag_box = FlagBuilder()
        flag_box.set(
            (CMDFlags.Common.remote_debugging_port, [self.debug_port]),
            (CMDFlags.Common.no_first_run, []),
            (CMDFlags.Common.no_default_browser_check, []),
            (CMDFlags.Test.log_file, ["null"]),
            (CMDFlags.Background.disable_breakpad, []),
            (CMDFlags.Background.no_recovery_component, []),
            (CMDFlags.Background.disable_sync, []),
            (CMDFlags.Background.disable_domain_reliability, []),
            (CMDFlags.Background.no_service_autorun, []),
            (CMDFlags.Performance.disable_gpu_shader_disk_cache, []),
            (CMDFlags.Performance.disk_cache_dir, ["null"]),
            (CMDFlags.Performance.media_cache_dir, ["null"]),
            (CMDFlags.Render.enable_features_WebUIDarkMode, []),
            (CMDFlags.Render.force_dark_mode, []),
        )
        run_args = [ self.browser_path ]
        flag_box.custom(url)

        # ! Default mode
        if self.profile_path:
            flag_box.add(CMDFlags.Common.user_data_dir, self.profile_path)
            if position is not None:
                flag_box.add(CMDFlags.Screen.window_position, *position)
            if sizes is not None:
                flag_box.add(CMDFlags.Screen.window_size, *sizes)

        # ! Headless mode
        else:
            flag_box.add(CMDFlags.Headless.headless)
            self.is_headless_mode = True

        if self.proxy_port:
            flag_box.add(CMDFlags.Other.proxy_server, self.proxy_addres + ":" + self.proxy_port)
            if self.verbose:
                log(f"Run browser {self.browser_name!r} on port: {self.debug_port} with proxy " +
                      f"on http://127.0.0.1:{self.proxy_port}")
        else:
            if self.verbose:
                log(f"Run browser {self.browser_name!r} on port: {self.debug_port}")

        if flags is not None:
            flag_box += flags

        run_args += flag_box.flags()
        return subprocess.Popen(run_args).pid

    def kill(self) -> None:
        """  Убивает процесс браузера. """
        try:
            os.kill(self.browser_pid, signal.SIGTERM)
        except PermissionError:
            pass

    async def getTargetConnectionInfoList(self) -> List[TargetConnectionInfo]:
        return [TargetConnectionInfo(**i) for i in await self.getPageList()]

    async def getTargetConnectionInfo(
            self, key: str = "type",
            connection_type: Union[str, TargetConnectionType] = "page") -> TargetConnectionInfo:
        v = connection_type if type(connection_type) is str else connection_type.value
        for page_data in await self.getPageList():
            data = page_data[key]
            if v in data: return TargetConnectionInfo(**page_data)
        raise ValueError(f"No have value {v} for key {key} in active target list")

    async def getConnectionsByType(
            self, connection_type: Union[str, TargetConnectionType]) -> List[TargetConnectionInfo]:
        t = connection_type if type(connection_type) is str else connection_type.value
        return [ti for ti in await self.getTargetConnectionInfoList() if ti.type == t]

    async def getPageList(self) -> List[dict]:
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
        result = await async_util_call(
            get_request, f"http://127.0.0.1:{self.debug_port}/json/list")

        if self.verbose: log("GetPageList() => " + result)
        return json.loads(result)

    async def getPageBy(
            self, key: Union[str, int],
            value: Union[str, int],
            match_mode: str = "exact",
            index: int = 0,
            callback: CommonCallback = None
    ) -> Optional[Connection]:
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

        :return:        <Connection>
        """

        if callback is not None and not iscoroutinefunction(callback):
            raise TypeError("Argument 'callback' must be a coroutine")

        counter = 0; v = value.lower()
        for page_data in await self.getPageList():
            data = page_data[key]
            if ((match_mode == "exact" and data == v)
                or (match_mode == "contains" and data.find(v) > -1 )
                    or (match_mode == "startswith" and data.find(v) == 0)):
                if counter == index:
                    conn = Connection(
                        page_data["webSocketDebuggerUrl"],
                        page_data["id"],
                        page_data["devtoolsFrontendUrl"],
                        callback,
                        self.profile_path == "",
                        self.verbose,
                        self.browser_name
                    )

                    await conn.activate()
                    return conn
                counter += 1
        return None

    async def getPage(
            self,
            index: int = 0, page_type: str = "page",
            callback: CommonCallback = None
    ) -> "Connection":
        """
        Получает страницу браузера по индексу. По умолчанию, первую.
        :param index:       - Желаемый индекс страницы начиная с нуля.
        :param page_type:   - Тип "page" | 'background_page' | 'service_worker' | ???
        :param callback:    - Корутина, которой будет передаваться контекст абсолютно
                                всех событий страницы в виде словаря.
        :return:        <Connection>
        """
        return await self.getPageBy("type", page_type, "exact", index, callback)

    async def getPageByID(
            self, conn_id: str,
            callback: CommonCallback = None
    ) -> "Connection":
        """
        Получает страницу браузера по уникальному идентификатору.
        :param conn_id:     - Желаемый идентификатор страницы. Метод GetPageList()
                                возвращает список доступных инстансов и словарь
                                каждого из них содержит 'id'. Так же создание инстансов
                                страниц через домен 'Target' возвращает 'targetId',
                                который используется с этой же целью.
        :param callback:    - Корутина, которой будет передаваться контекст абсолютно
                                всех событий страницы в виде словаря.
        :return:        <Connection>
        """
        return await self.getPageBy("id", conn_id, "exact", 0, callback)

    async def getPageByTitle(
            self, value: str,
            match_mode: str = "startswith",
            index: int = 0,
            callback: CommonCallback = None
    ) -> "Connection":
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
        :return:        <Connection>
        """
        return await self.getPageBy("title", value, match_mode, index, callback)

    async def getPageByURL(
            self, value: str,
            match_mode: str = "startswith",
            index: int = 0,
            callback: CommonCallback = None
    ) -> "Connection":
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
        :return:        <Connection>
        """
        return await self.getPageBy("url", value, match_mode, index, callback)

    async def createPage(
            self, url: str = "about:blank",
            newWindow: bool = False,
            background: bool = False,
            wait_for_create: bool = True,
            callback: CommonCallback = None
    ) -> Optional[Connection]:
        """
        Создаёт новую вкладку в браузере.
        :param url:                     - (optional) Адрес будет открыт при создании.
        :param newWindow:               - (optional) Если 'True' — страница будет открыта в новом окне.
        :param background:              - (optional) Если 'True' — страница будет открыта в фоне.
        :return:                    * <Connection>
        """
        while not (tmp := await self.getPage(callback=callback)):
            await asyncio.sleep(.5)
        page_id = await tmp.Target.createTarget(url, newWindow=newWindow, background=background)
        if wait_for_create:
            while not (page := await self.getPageByID(page_id)):
                await asyncio.sleep(.5)
        else:
            page = await self.getPageByID(page_id)
        return page
    
    async def showInspector(self, conn: Connection, new_window: bool = True,
                            callback: CommonCallback = None) -> Optional[Connection]:
        """
        Открывает новую вкладку с дебаггером для инспектируемой страницы.
        :param conn:            - Инспектируемая страница. Может принадлежать любому браузеру.
        :param new_window:      - Создать target в отдельном окне?
        :return:        <Connection>
        """
        return await self.createPage(
            "http://127.0.0.1:" + str(self.debug_port) + conn.frontend_url, new_window, callback=callback
        )

    async def createPopupWindow(self, conn: Connection, url: str = "about:blank",
                                callback: CommonCallback = None) -> Optional[Connection]:
        """
        Создаёт всплывающее окно с минимумом интерфейса браузера".
        :param url:             - Адрес, ресурс которого будет загружен
        :param conn:            - Родительская страница, инициатор
        :return:        Connection or None
        """
        await conn.extend.injectJS(f'window.open("{url}", "blank_window_name", "popup,noopener,noreferrer");')
        return await self.getPageByOpener(conn, callback=callback)

    async def getPageByOpener(self, conn: Connection, callback: CommonCallback = None) -> Optional[Connection]:
        """
        Возвращает последний созданный инстанс страницы, открытие которого инициировано с конкретной страницы.
            Например, при использовании JavaScript "window.open()".
        :param conn:            - Родительская страница, инициатор
        :return:        Connection or None
        """
        for target_info in await conn.Target.getTargets():
            if target_info.openerId == conn.conn_id:
                return await self.getPageByID(target_info.targetId, callback=callback)
        return None

    async def getPagesByOpener(self, conn: Connection, callback: CommonCallback = None) -> List[Connection]:
        """
        Возвращает список всех инстансов страниц, открытие которых инициировано с конкретной страницы.
            Например, при использовании JavaScript "window.open()".
        :param conn:            - Родительская страница, инициатор открытых окон
        :return:        List[Connection]
        """
        pages = []
        for target_info in await conn.Target.getTargets():
            if target_info.openerId == conn.conn_id:
                pages.append(await self.getPageByID(target_info.targetId, callback=callback))
        return pages

    async def waitFirstTab(self, timeout: float = 20.0, callback: CommonCallback = None) -> Connection:
        """
        Вызывает исключение 'asyncio.exceptions.TimeoutError' по истечении таймаута, или возвращает инстанс.
        """
        return await asyncio.wait_for(self.getFirstTab(callback), timeout)

    async def getFirstTab(self, callback: CommonCallback = None) -> Connection:
        """
        Безусловно дожидается соединения со страницей.
        """
        while True:
            try:
                while (conn := await self.getPage(callback=callback)) is None:
                    await asyncio.sleep(.5)
                return conn
            except URLError: await asyncio.sleep(1)

    async def close(self) -> None:
        """ Корректно закрывает браузер если остались ещё его инстансы """
        if conn := await self.getPage():
            await conn.Browser.close()

    async def closeAllPagesExcept(self, *except_list: Connection) -> None:
        """ Закрывает все страницы браузера, кроме переданных """
        for conn in await self.getTargetConnectionInfoList():
            if conn.type == "page":
                condition = False
                for conn in except_list:
                    condition |= conn.conn_id == conn._id
                if not condition:
                    i = 4
                    try:
                        while (tab := await self.getPageByID(conn._id)) is None and i:
                            await asyncio.sleep(.5)
                            i -= 1
                        if tab: await tab.Target.close()
                    except NoTargetWithGivenIdFound:
                        pass

    async def getFramesFor(self, conn: Connection) -> List[Connection]:
        """ Возвращает список iFrame для указанного инстанса """
        result = []
        for data in await self.getPageList():
            if data["type"] == "iframe" and data["parentId"] == conn.conn_id:
                result.append(await self.getPageByID(data["id"]))
        return result

    def __eq__(self, other: "Browser") -> bool:
        return self.debug_port == other.debug_port

    def __hash__(self) -> int:
        return hash(self.debug_port)


class FlagBuilder:
    """ Обеспечивает последовательность неповторяющихся флагов
    для запуска браузера.
    """
    def __init__(self):
        self._flags: Dict[str, Tuple[str]] = {}

    def add(self, flag: "CMDFlag", *args: Union[str, int, float]) -> None:
        """ Принимает один флаг и его аргументы. """
        f: str = flag.value
        if f[-1] == "=":
            if not args:
                raise FlagArgumentContainError(
                    f"Для флага {flag.name} ожидается аргумент, или список аргументов.")

            self._flags[f] = tuple(map(str, args))
        else:
            self._flags[f] = tuple()

    def set(self, *flags: Tuple["CMDFlag", Sequence[Union[str, int, float]]]) -> None:
        """ Принимает произвольную последовательность флагов, из кортежей,
         содержащих сам флаг и его аргументы:
            object.set(
                (CMDFlags.Background.disable_breakpad, []),
                (CMDFlags.Background.no_recovery_component, [])
            )
        """
        for cmd_flag, args in flags:
            self.add(cmd_flag, *args)

    def custom(self, flag: str) -> None:
        """ Принимает строку в качестве флага.
        object.custom("--mute-audio")
        """
        self._flags[flag] = tuple()

    def flags(self) -> List[str]:
        result: List[str] = []
        for cmd_flag, args in self._flags.items():
            result.append(cmd_flag + ",".join(args))
        return result

    def __str__(self) -> str:
        return str(self.flags())

    def __add__(self, other: "FlagBuilder") -> "FlagBuilder":
        if not isinstance(other, FlagBuilder):
            raise TypeError(f"Ожидаемый тип: {self.__class__.__name__}; "
                            f"полученный тип: {other.__class__.__name__}")

        flags = {}
        for cmd_flag, args in self._flags.items():
            flags[cmd_flag] = args
        for cmd_flag, args in other._flags.items():
            flags[cmd_flag] = args

        result = FlagBuilder()
        setattr(result, "_flags", flags)
        return result


class CMDFlag(Enum): pass

class CMDFlags:
    """https://github.com/GoogleChrome/chrome-launcher/blob/master/docs/chrome-flags-for-tools.md"""

    class Common(CMDFlag):
        # ? Commonly unwanted browser features
        # ! Порт подключения
        remote_debugging_port = "--remote-debugging-port="
        # ! Отключает обнаружение фишинга на стороне клиента.
        disable_client_side_phishing_detection = "--disable-client-side-phishing-detection"
        # ! Отключить все расширения Chrome.
        disable_extensions = "--disable-extensions"
        # ! Отключить некоторые встроенные расширения, на которые не влияет --disable-extensions.
        disable_component_extensions_with_background_pages = "--disable-component-extensions-with-background-pages"
        # ! Отключить установку приложений по умолчанию.
        disable_default_apps = "--disable-default-apps"
        # ! Беззвучный режим.
        mute_audio = "--mute-audio"
        # ! Отключить проверку браузера по умолчанию, не предлагать установить ее как таковую
        no_default_browser_check = "--no-default-browser-check"
        # ! Пропустить мастера первого запуска.
        no_first_run = "--no-first-run"
        # ! Используйте поддельное устройство для Media Stream, чтобы заменить камеру и микрофон.
        use_fake_device_for_media_stream = "--use-fake-device-for-media-stream"
        # ! Использовать файл для фальшивого захвата видео (.y4m или .mjpeg).--use-fake-device-for-media-stream
        # !     Принимает путь к файлу.
        use_file_for_fake_video_capture = "--use-file-for-fake-video-capture="  # * $
        # ! Отключает WebGL
        disable_webgl = "--disable-webgl"
        # ! Запускает браузер в режиме "Инкогнито"
        incognito = "--incognito"
        # ! Принимает путь к каталогу, где будет позиционирован весь кеш браузера, включая профили и прочее.
        user_data_dir = "--user-data-dir="      # * $

    class Performance(CMDFlag):
        # ? Performance & web platform behavior
        # ! Следующие два флага применяются вместе, отключая применение одного и того же происхождения (не рекомендуется).
        disable_web_security = "--disable-web-security"
        allow_running_insecure_content = "--allow-running-insecure-content"
        # --------------------------------
        # ! Отключить автоплей видео.
        autoplay_policy_user_gesture_required = "--autoplay-policy=user-gesture-required"
        # ! Отключить регулировку таймеров на фоновых страницах/вкладках.
        disable_background_timer_throttling = "--disable-background-timer-throttling"
        # ! Отключите фоновую визуализацию для закрытых окон. Сделано для тестов, чтобы избежать недетерминированного
        # !     поведения.
        disable_backgrounding_occluded_windows = "--disable-backgrounding-occluded-windows"
        # ! Отключает потоковую передачу сценариев V8.
        disable_features_ScriptStreaming = "--disable-features=ScriptStreaming"
        # ! Подавляет диалоги зависания монитора в процессах визуализации. Это может позволить обработчикам медленной
        # !     выгрузки на странице предотвратить закрытие вкладки, но в этом случае можно использовать диспетчер задач
        # !     для завершения вызывающего нарушение процесса.
        disable_hang_monitor = "--disable-hang-monitor"
        # ! Некоторые функции javascript можно использовать для заполнения процесса браузера IPC. По умолчанию защита
        # !     включена, чтобы ограничить количество отправляемых IPC до 10 в секунду на кадр. Этот флаг отключает его.
        disable_ipc_flooding_protection = "--disable-ipc-flooding-protection"
        # ! отключает веб-уведомления и API-интерфейсы Push.
        disable_notifications = "--disable-notifications"
        # ! отключить блокировку всплывающих окон.
        disable_popup_blocking = "--disable-popup-blocking"
        # ! перезагрузка страницы, полученной с помощью POST, обычно выводит пользователю запрос.
        disable_prompt_on_repost = "--disable-prompt-on-repost"
        # ! отключает вкладки, не находящиеся на переднем плане, от получения более низкого приоритета процесса. Это (само
        # !     по себе) не влияет на таймеры или поведение рисования.
        disable_renderer_backgrounding = "--disable-renderer-backgrounding"
        # ! https://stackoverflow.com/questions/59462637/list-of-js-flags-that-can-be-used-for-chrome-on-windows
        js_flags = "--js-flags="                # * $
        # ! Отключает шейдеры GPU в кеше на диске.
        disable_gpu_shader_disk_cache = "--disable-gpu-shader-disk-cache"
        # ! Принимает путь расположения кэша на диске, отличный от UserDatadir. Отключить: '--disk-cache-dir=null'
        disk_cache_dir = "--disk-cache-dir="    # * $
        # ! Задает максимальное дисковое пространство, используемое дисковым кешем, в байтах.
        disk_cache_size = "--disk-cache-size="  # * $
        # ! Принимает путь расположения media-кэша на диске, отличный от UserDatadir. Отключить: '--media-cache-dir=null'
        media_cache_dir = "--media-cache-dir="    # * $
        # ! Задает максимальное дисковое пространство, используемое дисковым кешем для медиа, в байтах.
        media_cache_size = "--media-cache-size="  # * $

    class Test(CMDFlag):
        # ? Test & debugging flags
        # ! Сообщает, выполняются ли в коде тесты браузера (это изменяет URL-адрес запуска, используемый оболочкой
        # !     содержимого, а также отключает функции, которые могут сделать тесты ненадежными [например, мониторинг
        # !     нехватки памяти]).
        browser_test = "--browser-test"
        # ! Избегает сообщений типа «Новый принтер в вашей сети».
        disable_device_discovery_notifications = "--disable-device-discovery-notifications"
        # ! Отключает несколько вещей, которые не подходят для автоматизации:
        # !     * отключает всплывающие уведомления о запущенных разработках/распакованных расширениях
        # !     * отключает пользовательский интерфейс сохранения пароля (который охватывает вариант использования
        # !         удаленного --disable-save-password-bubble флага)
        # !     * отключает анимацию информационной панели
        # !     * отключает автоперезагрузку при сетевых ошибках
        # !     * означает, что запрос проверки браузера по умолчанию не отображается
        # !     * избегает отображения этих 3 информационных панелей: ShowBadFlagsPrompt, GoogleApiKeysInfoBarDelegate,
        # !         ObsoleteSystemInfoBarDelegate
        # !     * добавляет эту информационную панель:
        # !         https://user-images.githubusercontent.com/39191/30349667-92a7a086-97c8-11e7-86b2-1365e3d407e3.png
        enable_automation = "--enable-automation"
        # ! Включает ведения журнала. Больше подходит для процесса серверного типа.
        enable_logging_stderr = "--enable-logging=stderr"
        # ! 0 — означает INFO и выше
        log_level = "--log-level="              # * $
        # ! Переопределяет дефолтное имя файла лога. Чтобы отключить: '--log-file=null'
        log_file = "--log-file="                # * $
        # ! Избегает потенциальной нестабильности при использовании Gnome Keyring или кошелька KDE.
        password_store_basic = "--password-store=basic"
        # ! Более безопасно, чем использование протокола через веб-сокет
        remote_debugging_pipe = "--remote-debugging-pipe"
        # ! Информационная панель не отображается, когда расширение Chrome подключается к странице с помощью
        # !     chrome.debuggerpage. Требуется для прикрепления к фоновым страницам расширения.
        silent_debugger_extension_api = "--silent-debugger-extension-api"
        # ! Похож на флаг --enable-automation
        # !     * позволяет избежать создания заглушек приложений в ~/Applications на Mac.
        # !     * делает коды выхода немного более правильными
        # !     * списки переходов для навигации в Windows не обновляются
        # !     * не запускается какой-либо хром StartPageService
        # !     * отключает инициализацию службы chromecast
        # !     * расширения компонентов с фоновыми страницами не включаются во время тестов, потому что они создают много
        # !         фонового поведения, которое может мешать
        # !     * при выходе из браузера он отключает дополнительные проверки, которые могут остановить этот процесс выхода.
        # !         (например, несохраненные изменения формы или необработанные уведомления профиля..)
        test_type = "--test-type"

    class Background(CMDFlag):
        # ? Background updates, networking, reporting
        # ! Отключить различные фоновые сетевые службы, включая обновление расширений, службу безопасного просмотра,
        # !     детектор обновлений, перевод, UMA.
        disable_background_networking = "--disable-background-networking"
        # ! Отключает сбор аварийных дампов (отчеты уже отключены в Chromium)
        disable_breakpad = "--disable-breakpad"
        # ! Не обновлять «компоненты» браузера, перечисленные в chrome://components/
        disable_component_update = "--disable-component-update"
        # ! Отключает мониторинг надежности домена, который отслеживает, возникают ли у браузера проблемы с доступом к
        # !     сайтам, принадлежащим Google, и загружает отчеты в Google.
        disable_domain_reliability = "--disable-domain-reliability"
        # ! Отключает синхронизацию с учетной записью Google.
        disable_sync = "--disable-sync"
        # ! Используется для включения отчетов о сбоях Breakpad в среде отладки, где отчеты о сбоях обычно скомпилированы,
        # !     но отключены.
        enable_crash_reporter_for_testing = "--enable-crash-reporter-for-testing"
        # ! Отключить отправку отчетов в UMA, но разрешить сбор.
        metrics_recording_only = "--metrics-recording-only"
        # ! Предотвращает загрузку и выполнение компонентов восстановления.
        no_recovery_component = "--no-recovery-component"
        # ! Запрещает процессам-сервисам добавлять себя в автозапуск. Это не удаляет существующие регистрации
        # !    автозапуска, а просто предотвращает регистрацию новых служб.
        no_service_autorun = "--no-service-autorun"

    class Render(CMDFlag):
        # ? Rendering & GPU
        # ! экспериментальный мета-флаг. Устанавливает приведенные ниже 7 флагов, переводящие браузер в режим, в котором
        # !     рендеринг (радиус границы и т. д.) является детерминированным, а начальные кадры должны выдаваться по
        # !     протоколу DevTools.
        deterministic_mode = "--deterministic-mode"

        run_all_compositor_stages_before_draw = "--run-all-compositor-stages-before-draw"
        disable_new_content_rendering_timeout = "--disable-new-content-rendering-timeout"
        enable_begin_frame_control = "--enable-begin-frame-control"
        disable_threaded_animation = "--disable-threaded-animation"
        disable_threaded_scrolling = "--disable-threaded-scrolling"
        disable_checker_imaging = "--disable-checker-imaging"
        disable_image_animation_resync = "--disable-image-animation-resync"
        # -------------
        # ! не откладывать отрисовку коммитов (обычно используется, чтобы избежать мигания нестилизованного содержимого).
        disable_features_PaintHolding = "--disable-features=PaintHolding"
        disable_partial_raster = "--disable-partial-raster"
        # ! Не используйте оптимизацию высокопроизводительного ЦП, обнаруженную во время выполнения, в Skia.
        disable_skia_runtime_opts = "--disable-skia-runtime-opts"
        # ! Экономит немного памяти, перемещая процесс графического процессора в поток процесса браузера.
        in_process_gpu = "--in-process-gpu"
        # ! выберите, какую реализацию GL должен использовать процесс GPU. Возможные варианты: desktop — любой рабочий стол
        # !     OpenGL, установленный пользователем (по умолчанию для Linux и Mac). egl — любой EGL / GLES2, который
        # !     пользователь установил (по умолчанию для Windows - фактически ANGLE). swiftshader — Программный рендерер
        # !     SwiftShader.
        use_gl = "--use-gl="    # * $
        # + DARK_MODE -- требует двух следующих флагов
        # ! Включает тёмный режим в браузере.
        enable_features_WebUIDarkMode = "--enable-features=WebUIDarkMode"
        # ! Принуждает использовать темный режим в пользовательском интерфейсе для платформ, которые его поддерживают.
        force_dark_mode = "--force-dark-mode"



    class Screen(CMDFlag):
        # ? Window & screen management
        # ! Запускает браузер в режиме KIOSK
        kiosk = "--kiosk"
        # ! Запрещает браузеру resize и убирает некоторые его элементы.
        force_app_mode = "--force-app-mode"
        # ! Все всплывающие окна и вызовы window.open завершатся ошибкой.
        block_new_web_contents = "--block-new-web-contents"
        # ! Заставить все мониторы обрабатываться так, как если бы они имели указанный цветовой профиль.
        force_color_profile_SRGB = "--force-color-profile=srgb"
        # ! Переопределяет коэффициент масштабирования устройства для пользовательского интерфейса браузера и содержимого.
        # !     int or float
        force_device_scale_factor = "--force-device-scale-factor="
        # ! Каждая ссылка запускается в новом окне.
        new_window = '--new-window'
        # ! Принимает X и Y позицию верхнего левого угла, окна браузера.
        window_position="--window-position="            # * $
        # ! Принимает ширину и высоту окна браузера.
        window_size = "--window-size="                  # * $

    class Process(CMDFlag):
        # ? Process management
        # ! Отключает OOPIF. https://www.chromium.org/Home/chromium-security/site-isolation
        disable_features_site_per_process = "--disable-features=site-per-process"
        # ! Запускает визуализатор и плагины в том же процессе, что и браузер.
        single_process = "--single-process"

    class Headless(CMDFlag):
        # ? Headless
        # ! Headless
        headless = "--headless"
        # ! Часто используется в сценариях Lambda, Cloud Functions.
        disable_dev_shm_usage = "--disable-dev-shm-usage"
        # ! Запуск без песочницы. НЕ РЕКОМЕНДУЕТСЯ!!!
        no_sandbox = "--no-sandbox"
        # ! С 2021 года не требуется.
        disable_gpu = "--disable-gpu"

    class Other(CMDFlag):
        """ https://niek.github.io/chrome-features/ """
        # ? Принимают любое кол-во аргументов
        enable_features = "--enable-features="      # * $
        disable_features = "--disable-features="    # * $
        # ! Принимает адрес и порт прокси:
        # !     http://192.168.0.1:2233
        proxy_server = "--proxy-server="            # * $
