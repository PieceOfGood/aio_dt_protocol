from asyncio import run
from aio_dt_protocol import Browser


async def main() -> None:
    """ Пример вызова метода протокола, не реализованного
    в библиотеке. Например:
    https://chromedevtools.github.io/devtools-protocol/tot/Tethering/#method-bind
    """

    browser, conn = await Browser.run()

    await conn.call(
        domain_and_method="Tethering.bind",
        params={"port": 10101}
    )


if __name__ == '__main__':
    run(main())
