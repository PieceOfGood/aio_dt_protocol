from typing import Optional, List, TYPE_CHECKING
from ...data import DomainEvent
from .types import Version, Bounds, WindowInfo
if TYPE_CHECKING:
    from ...connection import Connection


class Browser:
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Browser/
    """
    __slots__ = ("_connection",)

    def __init__(self, conn) -> None:
        self._connection: Connection = conn

    async def setPermission(
            self, permission: dict, setting: str, origin: str = None,
            browserContextId: str = None
    ) -> None:
        """
        (EXPERIMENTAL)
        Устанавливает настройки разрешений для данного источника.
        https://chromedevtools.github.io/devtools-protocol/tot/Browser#method-setPermission
        :param permission:          Дескриптор разрешения для переопределения, определяется
                                        словарём, с обязательным атрибутом "name". Подробней:
                                            {
                                                "name": str(),             -> Имя разрешения.
                                                            https://cs.chromium.org/chromium/src/third_party/blink/renderer/modules/permissions/permission_descriptor.idl
                                                "sysex": bool(),           -> (optional) Для разрешения
                                                            «midi» может также указываться sysex control.
                                                "userVisibleOnly": bool(), -> (optional) Для разрешения
                                                            «push» можно указать userVisibleOnly. Обратите
                                                            внимание, что userVisibleOnly = true -
                                                            единственный поддерживаемый в настоящее время тип.
                                                "type": str(),             -> (optional) Для разрешения
                                                            "wake-lock" необходимо указать тип "screen"
                                                            или "system".
                                                "allowWithoutSanitization": bool() -> (optional) Для
                                                            разрешения "clipboard" можно указать
                                                            allowWithoutSanitization.
                                            }
        :param setting:             Настройки разрешения. Могут быть: granted, denied, prompt
        :param origin:              (optional) Источник, к которому относится разрешение. Если не указано,
                                        подразумеваются все.
        :param browserContextId:    (optional) Контекст для переопределения. Если не указано, используется
                                        контекст браузера по умолчанию.
        :return:
        """
        args = {"permission": permission, "setting": setting}
        if origin is not None:
            args.update({"origin": origin})
        if browserContextId is not None:
            args.update({"browserContextId": browserContextId})
        await self._connection.call("Browser.setPermission", args)

    async def grantPermissions(
            self, permissions: List[str],
            origin: Optional[str] = None,
            browserContextId: Optional[str] = None
    ) -> None:
        """
        (EXPERIMENTAL)
        Предоставляет определенные разрешения данному источнику, отклоняя все остальные.
        https://chromedevtools.github.io/devtools-protocol/tot/Browser#method-grantPermissions
        :param permissions:         Возможные значения:
                                        accessibilityEvents, audioCapture, backgroundSync, backgroundFetch,
                                        clipboardReadWrite, clipboardSanitizedWrite, durableStorage, flash,
                                        geolocation, midi, midiSysex, nfc, notifications, paymentHandler,
                                        periodicBackgroundSync, protectedMediaIdentifier, sensors, videoCapture,
                                        idleDetection, wakeLockScreen, wakeLockSystem
        :param origin:              (optional) Источник, к которому относится разрешение. Если не указано,
                                        подразумеваются все.
        :param browserContextId:    (optional) Контекст для переопределения. Если не указано, используется
                                        контекст браузера по умолчанию.
        :return:
        """
        args = {"permissions": permissions}
        if origin is not None:
            args.update({"origin": origin})
        if browserContextId is not None:
            args.update({"browserContextId": browserContextId})
        await self._connection.call("Browser.grantPermissions", args)

    async def resetPermissions(self, browserContextId: Optional[str] = None) -> None:
        """
        Сбросить все управление разрешениями для всех источников.
        https://chromedevtools.github.io/devtools-protocol/tot/Browser#method-resetPermissions
        :param browserContextId:    (optional) Контекст для переопределения. Если не указано, используется
                                        контекст браузера по умолчанию.
        :return:
        """
        args = {}
        if browserContextId is not None:
            args.update({"browserContextId": browserContextId})
        await self._connection.call("Browser.resetPermissions", args)

    async def getVersion(self) -> Version:
        """
        Возвращает словарь с информацией о текущем билде браузера.
        https://chromedevtools.github.io/devtools-protocol/tot/Browser#method-getVersion
        :return:                {
                                    "protocolVersion":  str( ... ), -> Protocol version.
                                    "product":          str( ... ), -> Product name.
                                    "revision":         str( ... ), -> Product revision.
                                    "userAgent":        str( ... ), -> User-Agent.
                                    "jsVersion":        str( ... )  -> V8 version.
                                }
        """
        return Version(
            **(await self._connection.call("Browser.getVersion")))

    async def getWindowBounds(self, windowId: int = None) -> Bounds:
        """
        (EXPERIMENTAL)
        Возвращает позицию и размер окна.
        https://chromedevtools.github.io/devtools-protocol/tot/Browser#method-getWindowBounds
        :param windowId:        Идентификатор окна браузера.
        :return:                {
                                    "left":       int(), -> (optional) Смещение от левого
                                                                края экрана до окна в пикселях.
                                    "top":        int(), -> (optional) Смещение от верхнего
                                                                края экрана до окна в пикселях.
                                    "width":      int(), -> (optional) Ширина окна в пикселях.
                                    "height":     int(), -> (optional) Высота окна в пикселях
                                    "windowState": str() -> (optional) normal, minimized,
                                                                maximized, fullscreen
                                }
        """
        if windowId is None:
            windowId = (await self._connection.Target.getWindowForTarget()).windowId
        return Bounds(
            **(await self._connection.call("Browser.getWindowBounds", {"windowId": windowId}))["bounds"])

    async def getWindowForTarget(self, targetId: Optional[str] = None) -> WindowInfo:
        """
        (EXPERIMENTAL)
        Возвращает идентификатор, а так же позицию и размер окна.
        https://chromedevtools.github.io/devtools-protocol/tot/Browser#method-getWindowForTarget
        :param targetId:        (optional) Идентификатор хоста агента Devtools. Если вызывается
                                    как часть сеанса, используется связанный targetId.
        :return:                {
                                    "windowId": int(), -> Идентификатор окна.
                                    "bounds":   dict() -> То же, что возвращает GetWindowBounds().
                                }
        """
        if targetId is None:
            targetId = self._connection.conn_id
        result = await self._connection.call("Browser.getWindowForTarget", {"targetId": targetId})
        return WindowInfo(windowId=result["windowId"], bounds=Bounds(**result["bounds"]))

    async def setDockTile(self, badgeLabel: Optional[str] = None, image: Optional[str] = None) -> None:
        """
        !(EXPERIMENTAL)
        Задать сведения о док-плитке для конкретной платформы.
        https://chromedevtools.github.io/devtools-protocol/tot/Browser#method-setDockTile
        :param badgeLabel:      (optional) Значок метки(?)
        :param image:           (optional) PNG кодированное изображение.
        :return:
        """
        args = {}
        if badgeLabel is not None:
            args.update({"badgeLabel": badgeLabel})
        if image is not None:
            args.update({"image": image})
        if not args:
            return
        await self._connection.call("Browser.setDockTile", args)

    async def setDownloadBehavior(
            self, behavior: str,
            browserContextId: Optional[str] = None,
            downloadPath: Optional[str] = None,
            eventsEnabled: Optional[bool] = None
    ) -> None:
        """  Устанавливает поведение при загрузке файлов.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-setDownloadBehavior
        :param behavior:            Разрешить все или отклонить все запросы на загрузку, или использовать поведение
                                        Chrome по умолчанию, если доступно (в противном случае запретить).
                                        deny = запрет, allow = разрешить, default
        :param browserContextId:    (optional) Если не указано, используется контекст браузера по умолчанию.
        :param downloadPath:        (optional) Путь по умолчанию для сохранения загруженных файлов. Это необходимо,
                                        если для поведения установлено значение 'allow' и если путь не передан, будет
                                        установлено текущее расположение.
        :param eventsEnabled:       (optional) Если не указано, используется контекст браузера по умолчанию.
        :return:
        """
        args = {"behavior": behavior}
        if browserContextId is not None: args.update(browserContextId=browserContextId)
        if downloadPath is not None: args.update(downloadPath=downloadPath)
        if eventsEnabled is not None: args.update(eventsEnabled=eventsEnabled)
        await self._connection.call("Browser.setDownloadBehavior", args)

    async def setWindowBounds(self, bounds: Bounds, windowId: Optional[int] = None) -> None:
        """ Устанавливает позицию и/или размер окна.
        !(EXPERIMENTAL)
        https://chromedevtools.github.io/devtools-protocol/tot/Browser#method-setWindowBounds
        :param bounds:          Новые границы окна, а так же состояние.
        :param windowId:        Идентификатор окна.
        """
        if windowId is None:
            windowId = (await self._connection.Target.getWindowForTarget()).windowId
        await self._connection.call(
            "Browser.setWindowBounds",
            {"windowId": windowId, "bounds": bounds.to_dict()}
        )

    async def close(self) -> bool:
        """ Изящно завершает работу браузера.
        https://chromedevtools.github.io/devtools-protocol/tot/Browser#method-close
        :return:        Закрылся/был закрыт
        """
        if self._connection.connected:
            await self._connection.call("Browser.close")
            return True
        return False


class BrowserEvent(DomainEvent):
    downloadProgress = "Browser.downloadProgress"
    downloadWillBegin = "Browser.downloadWillBegin"
