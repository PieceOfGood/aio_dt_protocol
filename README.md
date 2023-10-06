Асинхронная обёртка над [протоколом](https://chromedevtools.github.io/devtools-protocol/) отладчика браузера Chromium.

Запуски проводятся только в ОС Windows и Linux.

Имеет одну зависимость:
https://github.com/aaugustin/websockets

### Установка
```shell
pip install aio-dt-protocol
```

### Примеры:

```python
import asyncio
from aio_dt_protocol import Browser
from aio_dt_protocol import BrowserName
from aio_dt_protocol.data import KeyEvents

DEBUG_PORT: int = 9222
BROWSER_NAME: str = BrowserName.CHROME
PROFILE_NAME: str = BROWSER_NAME.capitalize() + "_Profile"


async def main() -> None:
    # ? Будет печатать в консоль всё, что приходит по соединению со страницей.
    # ? Полезно при разработке.
    # async def action_printer(data: dict) -> None:
    #     print(data)
    # browser, conn = await Browser.run(callback=action_printer)
    
    # ? Если на указанном порту есть запущенный браузер, происходит подключение.
    # ? Иначе, запуск нового браузера.
    browser, conn = await Browser.run(
        debug_port=DEBUG_PORT,
        browser_name=BROWSER_NAME,
        profile_path=PROFILE_NAME
    )
    
    print("[- GO TO GOOGLE ... -]")
    await conn.Page.navigate("https://www.google.com", )
    print("[- EMULATE INPUT TEXT ... -]")

    input_node = await conn.DOM.querySelector("[type=search]")
    
    # ? Эмуляция клика в поисковую строку
    await input_node.click()
    await asyncio.sleep(1)
    
    # ? Вставка текста
    await conn.Input.insertText("github PieceOfGood")
    await asyncio.sleep(1)

    # ? Эмуляция нажатия клавиши Enter
    await conn.extend.action.sendKeyEvent(KeyEvents.enter)
    await asyncio.sleep(1)
    
    # ? Нажатие Enter можно заменить кликом по кнопке
    # ? используя протокол
    # submit_button_selector = "div:not([jsname])>center>[type=submit]:not([jsaction])"
    # submit_button = await conn.DOM.querySelector(submit_button_selector)
    # await submit_button.click()

    # ? Или выполнить клик используя JavaScript
    # click_code = f"""\
    # document.querySelector("{submit_button_selector}").click();
    # """
    # await conn.extend.injectJS(click_code)

    print("[- WAIT FOR CLOSE PAGE ... -]")
    # ? Пока соединение существует, цикл выполняется.
    await conn.waitForClose()
    print("[- DONE -]")


if __name__ == '__main__':
    asyncio.run(main())
```

На страницу можно легко зарегистрировать слушателей, которые будут вызываться на стороне клиентского(Python) кода. Для этого необходимо зарегистрировать вызываемую функцию в качестве такого слушателя. Это возможно выполнить двумя способами:
1. Вручную передав методу `addBinding()` домена `Runtime` имя функции в виде строки.
2. Воспользоваться более функциональной обёрткой первого способа, выраженной в методе `bindFunction()` соединения.

Второй способ менее многословен. Под капотом он добавляет в контекст страницы утилиту `py_call()`, первым аргументом принимающую имя функции(слушателя), после чего, любое кол-во позиционных аргументов, которые ожидает эта функция, а так же позволяет прикрепить любое кол-во аргументов, передаваемых в функцию последними. Например:

```python
    html = """\
    <html lang="ru">
    <head>
        <meta charset="utf-8" />
        <title>Test application</title>
    </head>
    <body>
        <button id="knopka">Push me</button>
    </body>
    <script>
        const btn = document.querySelector('#knopka');
        btn.addEventListener('click', () => {
            py_call("test_func", 1, "test")
        });
    </script>
    </html>"""
    
    # ? number и text будут переданы из браузера, а bind_arg указан при регистрации
    async def test_func(number: int, text: str, bind_arg: dict) -> None:
        print(f"[- test_func -] Called with args:\n\tnumber: {number}"
              f"\n\ttext: {text}\n\tbing_arg: {bind_arg}")
    
    
    await conn.bindFunction(
        test_func,  # ! слушатель
        {"name": "test", "value": True}  # ! bind_arg
    )
    
    # ? Если ожидается внушительный функционал прикрутить к странице, то это можно
    # ? сделать за один раз.
    # await conn.bindFunctions(
    #     (test_func, [ {"name": "test", "value": True} ]),
    #     # (any_awaitable1, [1, 2, 3])
    #     # (any_awaitable2, [])
    # )
    
    await conn.Page.navigate(html)
```
### Headless
Чтобы запустить браузер в безголовом(`headless`) режиме, передайте пустую строку аргументу(`profile_path`) принимающему путь к папке профиля.

```python
import asyncio
from aio_dt_protocol import Browser, BrowserName
from aio_dt_protocol.utils import save_img_as, async_util_call

DEBUG_PORT: int = 9222
BROWSER_NAME: str = BrowserName.CHROME


async def main() -> None:
    # ? Если на указанном порту есть запущенный браузер, происходит подключение.
    # ? Иначе, запуск нового браузера.
    browser, conn = await Browser.run(
        debug_port=DEBUG_PORT,
        browser_name=BROWSER_NAME,
        profile_path=""
    )
    
    print("[- WAITING PAGE -]")
    conn = await browser.waitFirstTab()
    print("[- GO TO GOOGLE -]")
    await conn.Page.navigate("https://www.google.com")

    print("[- MAKE SCREENSHOT -]")
    await async_util_call(
        save_img_as, "google.png", await conn.extend.makeScreenshot()
    )

    print("[- CLOSE BROWSER -]")
    await conn.Browser.close()
    print("[- DONE -]")


if __name__ == '__main__':
    asyncio.run(main())

```

### Custom serializer
Поскольку обмен данными по протоколу использует формат JSON, а под капотом используется стандартная реализация, то чтобы поменять этот механизм используется глобальный объект `Serializer`. Например:
```python
from aio_dt_protocol import Browser, Serializer
from msgspec import json

async def main() -> None:
    
    Serializer.decode = json.decode
    Serializer.encode = lambda x: json.encode(x).decode("utf-8")
    
    browser, conn = await Browser.run()
    ...
```
Будьте внимательны!
Метод, сериализующий данные в JSON, должен возвращать тип `str`, так как [только в этом случае](https://websockets.readthedocs.io/en/stable/reference/asyncio/client.html#websockets.client.WebSocketClientProtocol.send) сообщение отправляется в текстовом фрейме, что и ожидается при обмене по протоколу.