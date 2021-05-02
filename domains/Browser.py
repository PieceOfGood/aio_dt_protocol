from abc import ABC, abstractmethod
from typing import Optional, Union, Dict, List

class Browser(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Browser/
    """

    @property
    def connected(self) -> bool:
        return False

    @property
    def verbose(self) -> bool:
        return False

    @property
    def page_id(self) -> str:
        return ""

    async def SetPermission(
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
        await self.Call("Browser.setPermission", args)

    async def GrantPermissions(
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
        await self.Call("Browser.grantPermissions", args)

    async def ResetPermissions(self, browserContextId: Optional[str] = None) -> None:
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
        await self.Call("Browser.resetPermissions", args)

    async def CloseBrowser(self) -> bool:
        """
        Изящно завершает работу браузера.
        https://chromedevtools.github.io/devtools-protocol/tot/Browser#method-close
        :return:        Успех/неудача
        """
        if self.connected:
            await self.Call("Browser.close")
            return True
        return False

    async def GetVersion(self) -> Dict[str, str]:
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
        return await self.Call("Browser.getVersion")

    async def GetWindowBounds(self, windowId: int) -> dict:
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
        return (await self.Call("Browser.getWindowBounds", {"windowId": windowId}))["bounds"]

    async def GetWindowForTarget(self, targetId: Optional[str] = None) -> dict:
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
            targetId = self.page_id
        return await self.Call("Browser.getWindowForTarget", {"targetId": targetId})

    async def SetDockTile(self, badgeLabel: Optional[str] = None, image: Optional[str] = None) -> None:
        """
        (EXPERIMENTAL)
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
        await self.Call("Browser.setDockTile", args)

    async def SetDownloadBehavior(
            self, behavior: str,
            browserContextId: Optional[str] = None,
            downloadPath: Optional[str] = None,
            eventsEnabled: Optional[bool] = None
    ) -> None:
        """
        Устанавливает поведение при загрузке файлов.
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
        await self.Call("Browser.setDownloadBehavior", args)

    @abstractmethod
    async def Call(
            self, domain_and_method: str,
            params: Optional[dict] = None,
            wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")