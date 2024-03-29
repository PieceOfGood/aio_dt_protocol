import re
from asyncio import run
from base64 import b64decode, b64encode
from pprint import pprint
from aio_dt_protocol import Browser
from aio_dt_protocol.domains.fetch.types import EventRequestPaused, RequestPattern, HeaderEntry


# ? Описываем шаблон с признаком конкретного адреса
# ? и указанием стадии "во время ответа" и привязкой
# ? к типу ресурса.
# ? Прочие подробности в комментариях к типу.
REQ_PATTERN = RequestPattern(
    urlPattern="*www.python.org/", resourceType="Document", requestStage="Response")


async def intercept() -> None:
    """ Пример получения данных страницы ещё
    до их включения в рендер.
    """

    browser, conn = await Browser.run()

    # ? Корутина, которая будет вызываться всякий раз, когда удовлетворяются
    # ? условия шаблона "req_pattern"
    async def catch_data_for_response(data: EventRequestPaused) -> None:
        print("REQUEST HEADERS:")
        pprint(data.request.headers)

        print("RESPONSE HEADERS:")
        pprint(data.responseHeaders)

        body = await conn.Fetch.getResponseBody(data.requestId)
        print("\nRESPONSE BODY:\n", b64decode(body["body"]))

        print("\nLIST COOKIES:")
        pprint(await conn.Network.getAllCookies())

        await conn.Fetch.continueRequest(data.requestId)

    # ? Включаем уведомления домена, передаём ему список шаблонов
    # ? и ссылку на обработчик события "on_pause"
    await conn.Fetch.enable([REQ_PATTERN], on_pause=catch_data_for_response)

    await conn.Page.navigate("https://www.python.org/")

    # await conn.Browser.close()
    await conn.waitForClose()


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

    browser, conn = await Browser.run()

    # ? number и text будут переданы из браузера, а bind_arg указан при регистрации
    async def test_func(number: int, text: str, bind_arg: dict) -> None:
        print("[- test_func -] Called with args:\n\tnumber: "
              f"{number}\n\ttext: {text}\n\tbind_arg: {bind_arg}")

    await conn.bindFunction(
        test_func,  # ! слушатель
        {"name": "test", "value": True}  # ! bind_arg
    )

    # ! pyCallAddOnload() автоматически включается в предзагрузку
    # ! при вызове bindFunction()
    # await conn.extend.pyCallAddOnload()

    async def catch_data_for_response(data: EventRequestPaused) -> None:

        body = await conn.Fetch.getResponseBody(data.requestId)
        body = re.sub(
            br"<header class.*?</header>",
            html.encode("utf-8"),
            b64decode(body["body"]),
            flags=re.DOTALL
        )

        await conn.Fetch.fulfillRequest(
            data.requestId,
            body=b64encode(body).decode("utf-8")
        )

    # ? Включаем уведомления домена, передаём ему список шаблонов
    # ? и ссылку на обработчик события "on_pause"
    await conn.Fetch.enable([REQ_PATTERN], on_pause=catch_data_for_response)

    await conn.Page.navigate("https://www.python.org/")

    # await conn.Browser.close()
    await conn.waitForClose()


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
    ) -> tuple[list[HeaderEntry], str]:
        request_data = dict(
            method=method,
            url=url,
            headers=headers,
            data=post_data,
            proxy=proxy,        # ! Можно установить None и тогда все запросы
        )                       # ! будут выполнены через клиент без проксирования

        async with request(**request_data) as resp:
            out_headers = [
                HeaderEntry(name, value)
                for name, value in resp.headers.items()]

            body = await resp.read()

            return out_headers, b64encode(body).decode("utf-8")

    # ? В этом шаблоне проксируем абсолютно все исходящие запросы
    req_pattern = RequestPattern(
        urlPattern="*", requestStage="Request"
    )
    browser, conn = await Browser.run()

    async def catch_data_for_response(data: EventRequestPaused) -> None:
        headers, body = await req(
            data.request.method,
            data.request.url,
            data.request.headers,
            data.request.postData,
        )

        await conn.Fetch.fulfillRequest(
            data.requestId, responseHeaders=headers, body=body)

    await conn.Fetch.enable([req_pattern], on_pause=catch_data_for_response)

    await conn.Page.navigate("https://www.python.org/")

    # await conn.Browser.close()
    await conn.waitForClose()


if __name__ == '__main__':
    run(intercept())
