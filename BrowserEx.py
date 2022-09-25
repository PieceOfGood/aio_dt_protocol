import asyncio
from asyncio import sleep, wait_for
from urllib.error import URLError

from aio_dt_protocol.Browser import Browser
from aio_dt_protocol.PageEx import PageEx
from aio_dt_protocol.exceptions import NoTargetWithGivenIdFound

from urllib.parse import urlparse
import re
from typing import Union, Callable, Optional, List

class BrowserEx(Browser):
    """
    Расширение для 'Browser'. Включает в себя один новый метод CreatePage()
        создающий новые вкладки(процессы страниц), а так же, все методы
        получения инстансов вкладок, возвращают их с расширенным функционалом.
    """

    @staticmethod
    def get_domain(url):
        if url == "about:blank":
            return "about:blank"
        return re.search(r"^[^.]+", urlparse(url).netloc)[0]

    async def GetPageBy(
            self, key: str, value: str, match_mode: Optional[str] = "exact",
            index: Optional[int] = 0, callback: Optional[Callable] = None
    ) -> Union[PageEx, None]:
        counter = 0; v = value.lower()
        for page_data in await self.GetPageList():
            data = page_data[key].lower()
            if ((match_mode == "exact" and data == v)
                or (match_mode == "contains" and data.find(v) > -1)
                    or (match_mode == "startswith" and data.find(v) == 0)):
                if counter == index:
                    page = PageEx(
                        page_data["webSocketDebuggerUrl"],
                        page_data["id"],
                        page_data["devtoolsFrontendUrl"],
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
            self, index: int = 0, page_type: str = "page",
            callback: Callable = None
    ) -> Union[PageEx, None]:
        return await self.GetPageBy("type", page_type, "exact", index, callback)

    async def GetPageByID(
            self, page_id: str, index: int = 0,
            callback: Callable = None
    ) -> Union[PageEx, None]:
        return await self.GetPageBy("id", page_id, "exact", index, callback)

    async def GetPageByTitle(
            self, value: any, match_mode: str = "startswith",
            index: int = 0, callback: Callable = None
    ) -> Union[PageEx, None]:
        return await self.GetPageBy("title", value, match_mode, index, callback)

    async def GetPageByURL(
            self, value: any, match_mode: str = "startswith",
            index: int = 0, callback: Callable = None
    ) -> Union[PageEx, None]:
        return await self.GetPageBy("url", value, match_mode, index, callback)

    async def CreatePage(
        self,  url: Optional[str] = "about:blank",
        newWindow: Optional[bool] = False, background: Optional[bool] = False,
        wait_for_create: Optional[bool] = True
    ) -> Union[PageEx, None]:
        """
        Создаёт новую вкладку в браузере.
        :param url:                     - (optional) Адрес будет открыт при создании.
        :param newWindow:               - (optional) Если 'True' — страница будет открыта в новом окне.
        :param background:              - (optional) Если 'True' — страница будет открыта в фоне.
        :return:                    * Инстанс страницы <PageEx>
        """
        while not (tmp := await self.GetPage()):
            await sleep(.5)
        page_id = await tmp.CreateTarget(url, newWindow=newWindow, background=background)
        if wait_for_create:
            while not(page := await self.GetPageByID(page_id)):
                await sleep(.5)
        else:
            page = await self.GetPageByID(page_id)
        return page

    async def ShowInspector(self, page: PageEx, new_window: bool = True) -> Union[PageEx, None]:
        """
        Открывает новую вкладку с дебаггером для инспектируемой страницы.
        :param page:            - Инспектируемая страница. Может принадлежать любому браузеру.
        :param new_window:      - Создать target в отдельном окне?
        :return:        <PageEx>
        """
        return await self.CreatePage(
            "http://127.0.0.1:" + str(self.debug_port) + page.frontend_url, new_window
        )

    async def CreatePopupWindow(self, page: PageEx, url: str = "about:blank") -> Union[PageEx, None]:
        """
        Создаёт всплывающее окно с минимумом интерфейса браузера".
        :param url:             - Адрес, ресурс которого будет загружен
        :param page:            - Родительская страница, инициатор
        :return:        PageEx or None
        """
        await page.InjectJS(f'window.open("{url}", "blank_window_name", "popup,noopener,noreferrer");')
        return await self.GetPageByOpener(page)

    async def GetPageByOpener(self, page: PageEx) -> Union[PageEx, None]:
        """
        Возвращает последний созданный инстанс страницы, открытие которого инициировано с конкретной страницы.
            Например, при использовании JavaScript "window.open()".
        :param page:            - Родительская страница, инициатор
        :return:        PageEx or None
        """
        for target_info in await page.GetTargets():
            if target_info.openerId == page.page_id:
                return await self.GetPageByID(target_info.targetId)
        return None

    async def GetPagesByOpener(self, page: PageEx) -> List[PageEx]:
        """
        Возвращает список всех инстансов страниц, открытие которых инициировано с конкретной страницы.
            Например, при использовании JavaScript "window.open()".
        :param page:            - Родительская страница, инициатор открытых окон
        :return:        List[PageEx]
        """
        pages = []
        for target_info in await page.GetTargets():
            if target_info.openerId == page.page_id:
                pages.append(await self.GetPageByID(target_info.targetId))
        return pages

    async def WaitFirstTab(self, timeout: float = 20.0) -> PageEx:
        """
        Вызывает исключение 'asyncio.exceptions.TimeoutError' по истечении таймаута, или возвращает инстанс.
        """
        return await wait_for(self.GetFirstTab(), timeout)

    async def GetFirstTab(self) -> PageEx:
        """
        Безусловно дожидается соединения со страницей.
        """
        while True:
            try:
                while (page := await self.GetPage()) is None:
                    await sleep(.5)
                return page
            except URLError: await sleep(1)

    async def Close(self) -> None:
        """ Корректно закрывает браузер если остались ещё его инстансы """
        if page := await self.GetPage():
            await page.CloseBrowser()

    async def CloseAllPagesExcept(self, *except_list: PageEx) -> None:
        """ Закрывает все страницы браузера, кроме переданных """
        for conn in await self.GetTargetConnectionInfoList():
            if conn.type == "page":
                condition = False
                for page in except_list:
                    condition |= page.page_id == conn.id
                if not condition:
                    i = 4
                    try:
                        while (tab := await self.GetPageByID(conn.id)) is None and i:
                            await asyncio.sleep(.5)
                            i -= 1
                        if tab: await tab.Close()
                    except NoTargetWithGivenIdFound:
                        pass

    async def GetFramesFor(self, page: PageEx) -> List[PageEx]:
        """ Возвращает список iFrame для указанного инстанса """
        result = []
        for conn in await self.GetPageList():
            if conn["type"] == "iframe" and conn["parentId"] == page.page_id:
                result.append( await self.GetPageByID(conn["id"]) )
        return result

    def __eq__(self, other: "BrowserEx") -> bool:
        return self.debug_port == other.debug_port

    def __hash__(self) -> int:
        return hash(self.debug_port)
