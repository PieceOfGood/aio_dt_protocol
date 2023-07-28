from asyncio import run
from aio_dt_protocol import Browser
from aio_dt_protocol.js import noisify_canvas
from random import randint


async def main() -> None:
    """ Пример уникализации отпечатка браузера при внесении
    незначительного шума в его canvas.
    """

    canvas_detect_url = "https://browserleaks.com/canvas"

    browser, conn = await Browser.run()

    # ? Переходим на страницу canvas-детектора
    await conn.Page.navigate(canvas_detect_url)

    # ? Создаём случайные сдвиги
    shifts = {k: randint(-5, 5) for k in "rgba"}

    # ? Добавляем скрипт изменяющий canvas в предзагрузку
    await conn.Page.addScriptOnLoad(
        noisify_canvas(**shifts)
    )

    alert_js = "alert('Обратите внимание на значение `Signature` в " \
            "разделе `Canvas Fingerprint`. Перезагрузите страницу(F5) " \
            "и сравните их.')"
    await conn.extend.injectJS(alert_js)

    await conn.waitForClose()


if __name__ == '__main__':
    run(main())
