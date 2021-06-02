
from aio_dt_protocol.Browser import Browser
from aio_dt_protocol.PageEx import PageEx

from urllib.parse import urlparse
import re
from typing import Union, Callable, Optional

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
                    or (match_mode == "startswith" and data.find(v) == 0)) and counter == index:
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
    ) -> PageEx:
        return await self.GetPageBy("type", page_type, "exact", index, callback)

    async def GetPageByID(
            self, page_id: str, index: int = 0,
            callback: Callable = None
    ) -> PageEx:
        return await self.GetPageBy("id", page_id, "exact", index, callback)

    async def GetPageByTitle(
            self, value: any, match_mode: str = "startswith",
            index: int = 0, callback: Callable = None
    ) -> PageEx:
        return await self.GetPageBy("title", value, match_mode, index, callback)

    async def GetPageByURL(
            self, value: any, match_mode: str = "startswith",
            index: int = 0, callback: Callable = None
    ) -> PageEx:
        return await self.GetPageBy("url", value, match_mode, index, callback)

    async def CreatePage(
        self,  url: Optional[str] = "about:blank",
        newWindow: Optional[bool] = False, background: Optional[bool] = False
    ) -> PageEx:
        """
        Создаёт новую вкладку в браузере.
        :param url:                     - (optional) Адрес будет открыт при создании.
        :param newWindow:               - (optional) Если 'True' — страница будет открыта в новом окне.
        :param background:              - (optional) Если 'True' — страница будет открыта в фоне.
        :return:                    * Инстанс страницы <PageEx>
        """
        return await self.GetPageByID(
            (await (await self.GetPage()).CreateTarget(url, newWindow=newWindow, background=background))
        )

    async def ShowInspector(self, page: PageEx, new_window: bool = True) -> PageEx:
        """
        Открывает новую вкладку с дебаггером для инспектируемой страницы.
        :param page:            - Инспектируемая страница
        :param new_window:      - Создать target в отдельном окне?
        :return:        <PageEx>
        """
        return await self.CreatePage(
            "http://127.0.0.1:" + str(self.debug_port) + page.frontend_url, new_window
        )
