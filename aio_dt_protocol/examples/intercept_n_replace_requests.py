import re
from asyncio import run
from base64 import b64decode, b64encode
from pprint import pprint
from aio_dt_protocol import BrowserEx, PageEx, find_instances
from aio_dt_protocol.Data import CommonCallback
from aio_dt_protocol.domains.Fetch import FetchType


# ? Описываем шаблон с признаком конкретного адреса
# ? и указанием стадии "во время ответа" и привязкой
# ? к типу ресурса.
# ? Прочие подробности в комментариях к типу.
REQ_PATTERN = FetchType.RequestPattern(
    urlPattern="*www.python.org/", resourceType="Document", requestStage="Response")


async def run_browser(
        dbp: int = 9222,
        bro_exe: str = "chrome",
        callback: CommonCallback = None) -> tuple[BrowserEx, PageEx]:

    if browser_instances := find_instances(dbp, bro_exe):
        browser = BrowserEx(debug_port=dbp, browser_pid=browser_instances[dbp])
    else:
        profile_name = bro_exe.capitalize() + "_Profile"
        browser = BrowserEx(
            debug_port=dbp, browser_exe=bro_exe, profile_path=profile_name
        )

    return browser, await browser.WaitFirstTab(callback=callback)


async def intercept() -> None:
    """ Пример получения данных страницы ещё
    до их включения в рендер.
    """

    browser, page = await run_browser()

    # ? Корутина, которая будет вызываться всякий раз, когда удовлетворяются
    # ? условия шаблона "req_pattern"
    async def catch_data_for_response(data: FetchType.EventRequestPaused) -> None:
        print("REQUEST HEADERS:")
        pprint(data.request.headers)

        print("RESPONSE HEADERS:")
        pprint(data.responseHeaders)

        body = await page.GetResponseBody(data.requestId)
        print("\nRESPONSE BODY:\n", b64decode(body["body"]))

        print("\nLIST COOKIES:")
        pprint(await page.GetAllCookies())

        await page.ContinueRequest(data.requestId)

    # ? Включаем уведомления домена, передаём ему список шаблонов
    # ? и ссылку на обработчик события "on_pause"
    await page.FetchEnable([REQ_PATTERN], on_pause=catch_data_for_response)

    await page.Navigate("https://www.python.org/")

    # await page.CloseBrowser()
    await page.WaitForClose()


async def replace() -> None:
    """ Пример подмены входящих данных.
    Здесь часть HTML-разметки(тег <header>) заменяется
    кастомной кнопкой, пример которой взят из стартового
    шаблона, отчего демонстрирует то же поведение.
    """

    html = """\
        <button id="knopka" style="margin: 20px 45%;">
            Push me
        </button>
        <script>
            const btn = document.querySelector('#knopka');
            btn.addEventListener("click", () => {
                py_exec("test_func", 1, "testtt");
            });
        </script>"""

    browser, page = await run_browser()

    # ? number и text будут переданы из браузера, а bind_arg указан при регистрации
    async def test_func(number: int, text: str, bind_arg: dict) -> None:
        print("[- test_func -] Called with args:\n\tnumber: "
              f"{number}\n\ttext: {text}\n\tbind_arg: {bind_arg}")

    await page.AddListener(
        test_func,  # ! слушатель
        {"name": "test", "value": True}  # ! bind_arg
    )

    await page.PyExecAddOnload()

    async def catch_data_for_response(data: FetchType.EventRequestPaused) -> None:

        body = await page.GetResponseBody(data.requestId)
        body = re.sub(
            br"<header class.*?</header>",
            html.encode("utf-8"),
            b64decode(body["body"]),
            flags=re.DOTALL
        )

        await page.FulfillRequest(
            data.requestId,
            body=b64encode(body).decode("utf-8")
        )

    # ? Включаем уведомления домена, передаём ему список шаблонов
    # ? и ссылку на обработчик события "on_pause"
    await page.FetchEnable([REQ_PATTERN], on_pause=catch_data_for_response)

    await page.Navigate("https://www.python.org/")

    # await page.CloseBrowser()
    await page.WaitForClose()


async def re_proxy() -> None:
    """ Пример того, как выполнять HTTP-запросы вместо браузера,
    с возможным участием любой конфигурации прокси, для конкретной
    страницы.
    """

    from aiohttp import request

    # ? Адрес прокси
    # https://docs.aiohttp.org/en/stable/client_advanced.html?highlight=proxy#proxy-support
    proxy = "http://proxy-address.com:9876" or "http://username:password@proxy-address.com:9876"

    async def req(
            method: str,
            url: str,
            headers: dict,
            post_data: str | None
    ) -> tuple[list[FetchType.HeaderEntry], str]:
        request_data = dict(
            method=method,
            url=url,
            headers=headers,
            data=post_data,
            proxy=proxy,        # ! Можно установить None и тогда все запросы
        )                       # ! будут выполнены через клиент без проксирования

        async with request(**request_data) as resp:
            out_headers = [
                FetchType.HeaderEntry(name, value)
                for name, value in resp.headers.items()]

            body = await resp.read()

            return out_headers, b64encode(body).decode("utf-8")

    # ? В этом шаблоне проксируем абсолютно все исходящие запросы
    req_pattern = FetchType.RequestPattern(
        urlPattern="*", requestStage="Request"
    )
    browser, page = await run_browser()

    async def catch_data_for_response(data: FetchType.EventRequestPaused) -> None:
        headers, body = await req(
            data.request.method,
            data.request.url,
            data.request.headers,
            data.request.postData,
        )

        await page.FulfillRequest(
            data.requestId, responseHeaders=headers, body=body)

    await page.FetchEnable([req_pattern], on_pause=catch_data_for_response)

    await page.Navigate("https://www.python.org/")

    # await page.CloseBrowser()
    await page.WaitForClose()


if __name__ == '__main__':
    run(intercept())
