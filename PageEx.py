
from aio_dt_protocol.Page import Page
from aio_dt_protocol.Actions import Actions
from aio_dt_protocol.DOMElement import Node

import asyncio
import json, os, base64
from urllib.parse import quote
from typing import List, Optional, Union


class PageEx(Page):
    """
    Расширение для 'Page'. Включает сборку наиболее востребованных методов для работы
        с API 'ChromeDevTools Protocol'.
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.storage = {}
        self.action = Actions(self)
        self._root: Union[Node, None] = None
        self.style_sheets = []                  # Если домен CSS активирован, сюда попадут все 'styleSheetId' страницы

        self.loading_state = ""

        self.dom_domain_enabled       = False
        self.log_domain_enabled       = False
        self.network_domain_enabled   = False
        self.page_domain_enabled      = False
        self.fetch_domain_enabled     = False
        self.css_domain_enabled       = False

    # region [ |>*<|=== Domains ===|>*<| ] Browser [ |>*<|=== Domains ===|>*<| ]

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

    async def GetVersion(self) -> dict:
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

    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] DOM [ |>*<|=== Domains ===|>*<| ]
    #   https://chromedevtools.github.io/devtools-protocol/tot/DOM

    async def DOMEnable(self) -> None:
        """
        Включает DOM-агент для данной страницы.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-enable
        :return:
        """
        await self.Call("DOM.enable")
        self.dom_domain_enabled = True

    async def DOMDisable(self) -> None:
        """
        Отключает DOM-агент для данной страницы.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-disable
        :return:
        """
        await self.Call("DOM.disable")
        self.dom_domain_enabled = False

    async def GetRoot(self) -> Node:
        """
        Возвращает корневой узел документа.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-getDocument
        Корневой элемент ВСЕГДА имеет следующую структуру:
        'root': {
            'nodeId': 19,
            'backendNodeId': 2,
            'nodeType': 9,
            'nodeName': '#document',
            'localName': '',
            'nodeValue': '',
            'childNodeCount': 2,
            'children': [
                {
                    'nodeId': 20,
                    'parentId': 19,
                    'backendNodeId': 9,
                    'nodeType': 10,
                    'nodeName': 'html',
                    'localName': '',
                    'nodeValue': '',
                    'publicId': '',
                    'systemId': ''
                }, {
                    'nodeId': 21,
                    'parentId': 19,
                    'backendNodeId': 10,
                    'nodeType': 1,
                    'nodeName': 'HTML',
                    'localName': 'html',
                    'nodeValue': '',
                    'childNodeCount': 2,
                    'children': [
                        {
                            'nodeId': 22,
                            'parentId': 21,
                            'backendNodeId': 11,
                            'nodeType': 1,
                            'nodeName': 'HEAD',
                            'localName': 'head',
                            'nodeValue': '',
                            'childNodeCount': 4,
                            'attributes': [ ]
                        }, {
                            'nodeId': 23,
                            'parentId': 21,
                            'backendNodeId': 12,
                            'nodeType': 1,
                            'nodeName': 'BODY',
                            'localName': 'body',
                            'nodeValue': '',
                            'childNodeCount': 8,
                            'attributes': [ ]
                        }
                    ],
                    'attributes': [
                        'lang',
                        'ru'
                    ],
                    'frameId': 'AF11E1D7BC9DF951D77C6C07C02B98E7'
                }
            ],
            'documentURL': 'url ...',
            'baseURL': 'url ...',
            'xmlVersion': ''
        }
        :return:            <Node>.
        """
        return Node(self, **(await self.Call("DOM.getDocument"))["root"])

    async def QuerySelector(self, selector: str) -> Union[Node, None]:
        """
        Выполняет DOM-запрос, возвращая объект найденного узла, или None.
            Эквивалент  === document.querySelector()
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-querySelector
        :param selector:        Селектор.
        :return:                <Node>
        """
        repeat = 0;
        max_repeat = 2;
        error = ""
        root_node_id = (await self.Call("DOM.getDocument"))["root"]["nodeId"]
        while repeat < max_repeat:
            try:
                node = await self.Call("DOM.querySelector", {
                    "nodeId": root_node_id, "selector": selector
                })
                return Node(self, **node) if node["nodeId"] > 0 else None
            except Exception as e:
                repeat += 1;
                error = str(e)
        raise Exception(error)

    async def QuerySelectorAll(self, selector: str) -> List[Node]:
        """
        Выполняет DOM-запрос, возвращая список объектов найденных узлов, или пустой список.
            Эквивалент  === document.querySelectorAll()
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-querySelectorAll
        :param selector:        Селектор.
                                    поиск. Если не передан, будет использоваться корневой
                                    элемент документа.
        :return:                [ <Node>, <Node>, ... ]
        """
        repeat = 0;
        max_repeat = 2;
        nodes = [];
        error = ""
        root_node_id = (await self.Call("DOM.getDocument"))["root"]["nodeId"]
        while repeat < max_repeat:
            try:
                for node in (await self.Call("DOM.querySelectorAll", {
                    "nodeId": root_node_id, "selector": selector
                }))["nodeIds"]:
                    nodes.append(Node(self, node))
                return nodes
            except Exception as e:
                repeat += 1;
                error = str(e)
        raise Exception(error)

    async def PerformSearch(self, query: str, searchInShadowDOM: Optional[bool] = None) -> dict:
        """
        (EXPERIMENTAL)
        Ищет заданную строку в дереве DOM. Используйте 'GetSearchResults()' для доступа к результатам
            поиска или 'CancelSearch()'( !не найдено! ), чтобы завершить этот сеанс поиска.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-performSearch
        :param query:               Обычный текст, селектор, или поисковый запрос XPath.
        :param searchInShadowDOM:   (optional) True - поиск будет так же выполнен в shadow DOM.
        :return:                    {"searchId": str(searchId), "resultCount": int(resultCount)}
                                        searchId    - уникальный идентификатор сессии поиска.
                                        resultCount - кол-во результатов удовлетворяющих запрос.
        """
        args = {"query": query}
        if searchInShadowDOM is not None:
            args.update({"includeUserAgentShadowDOM": searchInShadowDOM})
        return await self.Call("DOM.performSearch", args)

    async def GetSearchResults(
            self, searchId: str,
            fromIndex: Optional[int] = 0,
              toIndex: Optional[int] = 0
    ) -> List["Node"]:
        """
        (EXPERIMENTAL)
        Возвращает список результатов поиска для поисковой сессии 'searchId', в интервале от 'fromIndex'
            до 'toIndex', полученной в результате вызова PerformSearch().
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-getSearchResults
        :param searchId:        Уникальный идентификатор сессии поиска.
        :param fromIndex:       Начальный индекс результата поиска, который будет возвращен.
        :param toIndex:         Конечный индекс результата поиска, который будет возвращен.
        :return:                [ <Node>, <Node>, ... ]
        """
        nodes = []
        args = {"searchId": searchId, "fromIndex": fromIndex, "toIndex": toIndex}
        for node_id in (await self.Call("DOM.getSearchResults", args))["nodeIds"]:
            nodes.append(Node(self, node_id))
        return nodes

    async def Undo(self) -> None:
        """
        (EXPERIMENTAL)
        Отменяет последнее выполненное действие.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-undo
        :return:
        """
        await self.Call("DOM.undo")

    async def Redo(self) -> None:
        """
        (EXPERIMENTAL)
        Повторно выполняет последнее отмененное действие.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM/#method-redo
        :return:
        """
        await self.Call("DOM.redo")

    async def markUndoableState(self) -> None:
        """
        (EXPERIMENTAL)
        Отмечает последнее состояние, которое нельзя изменить.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM/#method-markUndoableState
        :return:
        """
        await self.Call("DOM.markUndoableState")

    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] Emulation [ |>*<|=== Domains ===|>*<| ]
    #   https://chromedevtools.github.io/devtools-protocol/tot/Emulation

    async def CanEmulate(self) -> bool:
        """
        Сообщает, поддерживается ли эмуляция.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-canEmulate
        :return:                result -> True если эмуляция поддерживается
        """
        return (await self.Call("Emulation.canEmulate"))["result"]

    async def ClearDeviceMetricsOverride(self) -> None:
        """
        Очищает переопределённые метрики устройства.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-clearDeviceMetricsOverride
        :return:
        """
        await self.Call("Emulation.clearDeviceMetricsOverride")

    async def ClearGeolocationOverride(self) -> None:
        """
        Очищает переопределённые позицию геолокации и ошибку.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-clearGeolocationOverride
        :return:
        """
        await self.Call("Emulation.clearGeolocationOverride")

    async def ResetPageScaleFactor(self) -> None:
        """
        Запрашивает сброс масштабирования страницы до начальных значений.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-resetPageScaleFactor
        :return:
        """
        await self.Call("Emulation.resetPageScaleFactor")

    async def SetFocusEmulationEnabled(self, enabled: bool) -> None:
        """
        Включает или отключает симуляцию фокуса(когда страница активна).
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setFocusEmulationEnabled
        :param enabled:         Включает, или отключает эмуляцию фокуса.
        :return:
        """
        await self.Call("Emulation.setFocusEmulationEnabled", {"enabled": enabled})

    async def SetCPUThrottlingRate(self, rate: float) -> None:
        """
        Включает CPU "throttling", эмулируя медленный процессор.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setCPUThrottlingRate
        :param rate:            Коэффициент замедления(1 - без замедления; 2 - 2х кратное, и т.д.).
        :return:
        """
        await self.Call("Emulation.setCPUThrottlingRate", {"rate": rate})

    async def SetDefaultBackgroundColorOverride(self, color: dict) -> None:
        """
        Устанавливает или очищает переопределение цвета фона фрейма по умолчанию. Это переопределение
            используется, если содержимое не указывает его.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setDefaultBackgroundColorOverride
        :param color:            (optional) RGBA цвета фона по умолчанию. Если не указано, любое
                                    существующее переопределение будет очищено. Словарь вида:
                                        {
                                            "r": int[0-255],
                                            "g": int[0-255],
                                            "b": int[0-255],
                                            "a": float[0-1] -> опционально. По умолчанию: 1.
                                        }
        :return:
        """
        await self.Call("Emulation.setDefaultBackgroundColorOverride", {"color": color})

    async def SetDeviceMetricsOverride(
            self, width: int, height: int,
            deviceScaleFactor: Optional[float] = 0,
                        mobile: Optional[bool] = False,
                        scale: Optional[float] = None,
                    screenWidth: Optional[int] = None,
                   screenHeight: Optional[int] = None,
                      positionX: Optional[int] = None,
                      positionY: Optional[int] = None,
            dontSetVisibleSize: Optional[bool] = None,
             screenOrientation: Optional[dict] = None,
                      viewport: Optional[dict] = None
    ) -> None:
        """
        Переопределяет значения размеров экрана устройства (результаты мультимедийного запроса CSS,
            относящиеся к «device-width» / «device-height», связанные с window.screen.width,
            window.screen.height, window.innerWidth, window.innerHeight).
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setDeviceMetricsOverride
        :param width:               Переопределяет значение ширины viewport в пикселях(от 0 до 10_000_000).
                                        window.innerWidth
                                        0 — выключает переопределение.
        :param height:              Переопределяет значение высоты viewport в пикселях(от 0 до 10_000_000).
                                        window.innerHeight
                                        0 — выключает переопределение.
        :param deviceScaleFactor:   Переопределяет значение масштабирования устройства. Отношение размера
                                        одного физического пикселя к размеру одного логического (CSS) пикселя.
                                        window.devicePixelRatio
                                        0 — выключает переопределение.
        :param mobile:              Эмуляция мобильного устройства. Это включает метатег области
                                        просмотра, полосы прокрутки наложения, авторазмер текста
                                        и многое другое.
        :param scale:               (optional, EXPERIMENTAL) Масштаб, применяемый к полученному изображению
                                        представления.
        :param screenWidth:         (optional, EXPERIMENTAL) Переопределяет значения ширины экрана в пикселях
                                        (от 0 до 10_000_000).
        :param screenHeight:        (optional, EXPERIMENTAL) Переопределяет значения высоты экрана в пикселях
                                        (от 0 до 10_000_000).
        :param positionX:           (optional, EXPERIMENTAL) Переопределяет X-позицию области просмотра на
                                        экране, в пикселях (от 0 до 10_000_000).
        :param positionY:           (optional, EXPERIMENTAL) Переопределяет Y-позицию области просмотра на
                                        экране, в пикселях (от 0 до 10_000_000).
        :param dontSetVisibleSize:  (optional, EXPERIMENTAL) Не устанавливайте видимый размер представления,
                                        полагайтесь на явный вызов setVisibleSize(смотри другие методы).
        :param screenOrientation:   (optional, EXPERIMENTAL) Переопределяет ориентацию экрана. Допустимые значения:
                                        {
                                            "type": str,    -> тип ориентации: portraitPrimary,
                                                                portraitSecondary, landscapePrimary,
                                                                landscapeSecondary
                                            "angle": int    -> Угол ориентации
                                        }
        :param viewport:            (optional, EXPERIMENTAL) Если установлено, видимая область страницы будет
                                        переопределена в этом окне просмотра. Это изменение окна просмотра
                                        не наблюдается на странице, например, относящиеся к области
                                        просмотра элементы не меняют позиции. Допустимые значения:
                                        {
                                            "x": float,     -> Смещение по оси X в независимых от устройства
                                                                пикселях (dip).
                                            "y": float,     -> Смещение по оси Y в независимых от устройства
                                                                пикселях (dip).
                                            "width": float, -> Ширина прямоугольника в независимых от устройства
                                                                пикселях (dip).
                                            "height": float,-> Высота прямоугольника в независимых от устройства
                                                                пикселях (dip).
                                            "scale": float  -> Коэффициент масштабирования страницы.
                                        }
        :return:
        """
        args = {"width": width, "height": height, "deviceScaleFactor": deviceScaleFactor, "mobile": mobile}
        if scale is not None:
            args.update({"scale": scale})
        if screenWidth is not None:
            args.update({"screenWidth": screenWidth})
        if screenHeight is not None:
            args.update({"screenHeight": screenHeight})
        if positionX is not None:
            args.update({"positionX": positionX})
        if positionY is not None:
            args.update({"positionY": positionY})
        if dontSetVisibleSize is not None:
            args.update({"dontSetVisibleSize": dontSetVisibleSize})
        if screenOrientation is not None:
            args.update({"screenOrientation": screenOrientation})
        if viewport is not None:
            args.update({"viewport": viewport})
        await self.Call("Emulation.setDeviceMetricsOverride", args)

    async def SetScrollbarsHidden(self, hidden: bool) -> None:
        """
        (EXPERIMENTAL)
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setScrollbarsHidden
        :param hidden:              Должны ли полосы прокрутки быть всегда скрыты.
        :return:
        """
        await self.Call("Emulation.setScrollbarsHidden", {"hidden": hidden})

    async def SetDocumentCookieDisabled(self, disabled: bool) -> None:
        """
        (EXPERIMENTAL)
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setDocumentCookieDisabled
        :param disabled:            Должен ли API document.cookie быть отключен.
        :return:
        """
        await self.Call("Emulation.setDocumentCookieDisabled", {"disabled": disabled})

    async def SetEmitTouchEventsForMouse(self, enabled: bool, configuration: Optional[str] = None) -> None:
        """
        (EXPERIMENTAL)
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setEmitTouchEventsForMouse
        :param enabled:             Должна ли быть включена эмуляция касания на основе ввода от мыши.
        :param configuration:       (optional) Конфигурация событий касания / жеста.
                                        По умолчанию: текущая платформа. Допустимые значения:
                                            mobile, desktop
        :return:
        """
        args = {"enabled": enabled}
        if configuration is not None:
            args.update({"configuration": configuration})
        await self.Call("Emulation.setEmitTouchEventsForMouse", args)

    async def SetEmulatedMedia(self, media: Optional[str] = "", features: Optional[list] = None) -> None:
        """
        Эмулирует переданный тип медиа или медиа-функцию для медиа-запросов CSS.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setEmulatedMedia
        :param media:               (optional) Тип медиа для эмуляции. Пустая строка отключает переопределение.
        :param features:            (optional) Список медиа-функций для эмуляции. Допустимые значения:
                                        [{
                                            "name": str,
                                            "value": str
                                        }, { ... }, ... ]
                                        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#type-MediaFeature
        :return:
        """
        args = {"media": media}
        if features is not None:
            args.update({"features": features})
        await self.Call("Emulation.setEmulatedMedia", args)

    async def SetEmulatedVisionDeficiency(self, type_: Optional[str] = "none") -> None:
        """
        (EXPERIMENTAL)
        Эмулирует переданный дефицит зрения.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setEmulatedVisionDeficiency
        :param type_:                (optional) Недостаток зрения для эмуляции. Допустимые значения:
                                        none, achromatopsia, blurredVision, deuteranopia, protanopia, tritanopia
        :return:
        """
        await self.Call("Emulation.setEmulatedVisionDeficiency", {"type": type_})

    async def SetGeolocationOverride(
            self,
             latitude: Optional[float] = None,
            longitude: Optional[float] = None,
             accuracy: Optional[float] = None
    ) -> None:
        """
        Переопределяет Положение или Ошибку Геолокации. Пропуск любого из параметров эмулирует положение недоступно.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setGeolocationOverride
        :param latitude:            (optional) Широта.
        :param longitude:           (optional) Долгота.
        :param accuracy:            (optional) Точность.
        :return:
        """
        args = {}
        if latitude is not None:
            args.update({"latitude": latitude})
        if longitude is not None:
            args.update({"longitude": longitude})
        if accuracy is not None:
            args.update({"accuracy": accuracy})
        await self.Call("Emulation.setGeolocationOverride", args)

    async def SetPageScaleFactor(self, pageScaleFactor: float) -> None:
        """
        (EXPERIMENTAL)
        Устанавливает переданный коэффициент масштабирования страницы.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setPageScaleFactor
        :param pageScaleFactor:     Коэффициент масштабирования страницы.
        :return:
        """
        await self.Call("Emulation.setPageScaleFactor", {"pageScaleFactor": pageScaleFactor})

    async def SetScriptExecutionDisabled(self, value: bool) -> None:
        """
        Переключает выполнение скриптов на странице.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setScriptExecutionDisabled
        :param value:               Должно ли выполнение скриптов быть отключено на странице.
        :return:
        """
        await self.Call("Emulation.setScriptExecutionDisabled", {"value": value})

    async def SetTouchEmulationEnabled(self, enabled: bool, maxTouchPoints: Optional[int] = None) -> None:
        """
        Включает "касания" для платформ, которые их не поддерживают.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setTouchEmulationEnabled
        :param enabled:             Должна ли эмуляция сенсорного события быть включена.
        :param maxTouchPoints:      (optional) Максимальное количество поддерживаемых точек касания.
                                        По умолчанию 1.
        :return:
        """
        args = {"enabled": enabled}
        if maxTouchPoints is not None:
            args.update({"maxTouchPoints": maxTouchPoints})
        await self.Call("Emulation.setTouchEmulationEnabled", args)

    async def SetLocaleOverride(self, locale: Optional[str] = None) -> None:
        """
        Не работает.
        https://bugs.chromium.org/p/chromium/issues/detail?id=1073363
        Починили с версии Хромиум == 83.0.4103.97

        (EXPERIMENTAL)
        Переопределяет языковой стандарт хост-системы на указанную.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setLocaleOverride
        :param locale:              (optional) Язык C в стиле ICU (например, "en_US"). Если не указано
                                        или не задано, отключает переопределение и восстанавливает
                                        локаль системы хоста по умолчанию.
                                        https://stackoverflow.com/questions/3191664/list-of-all-locales-and-their-short-codes
        :return:
        """
        args = {}
        if locale is not None:
            args.update({"locale": locale})
        await self.Call("Emulation.setLocaleOverride", args)

    async def SetTimezoneOverride(self, timezoneId: Optional[str] = "") -> None:
        """
        (EXPERIMENTAL)
        Переопределяет часовой пояс хост-системы на указанный.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setTimezoneOverride
        :param timezoneId:          Идентификатор часового пояса("Europe/Moscow"). Если пусто,
                                        отключает переопределение и восстанавливает часовой пояс
                                        хост-системы по умолчанию.
                                        https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        :return:
        """
        await self.Call("Emulation.setTimezoneOverride", {"timezoneId": timezoneId})

    async def SetVisibleSize(self, width: int, height: int) -> None:
        """
        (DEPRECATED)
        (EXPERIMENTAL)
        Изменяет размер фрейма / области просмотра страницы. Обратите внимание, что это не влияет
            на контейнер фрейма (например, окно браузера). Может использоваться для создания
            скриншотов указанного размера. Не поддерживается на Android.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setVisibleSize
        :param width:               Ширина фрейма (DIP).
        :param height:              Высота фрейма (DIP).
        :return:            None
        """
        await self.Call("Emulation.setVisibleSize", {"width": width, "height": height})

    async def EmulationSetUserAgent(
            self, userAgent: str,
                acceptLanguage: Optional[str] = None,
                      platform: Optional[str] = None,
            userAgentMetadata: Optional[dict] = None
    ) -> None:
        """
        Переопределяет юзер-агент переданной строкой.
        https://chromedevtools.github.io/devtools-protocol/tot/Emulation#method-setUserAgentOverride
        :param userAgent:           Новый юзер-агент.
        :param acceptLanguage:      (optional) Язык браузера для эмуляции.
        :param platform:            (optional) Платформа браузера, которую возвращает
                                        "navigator.platform".
                                        https://www.w3schools.com/jsref/prop_nav_platform.asp
                                        https://stackoverflow.com/questions/19877924/what-is-the-list-of-possible-values-for-navigator-platform-as-of-today
        :param userAgentMetadata:   (optional, EXPERIMENTAL) Для отправки в заголовках Sec-CH-UA- * и возврата в
                                        navigator.userAgentData. Ожидатся словарь вида:
                                        {
                                            "brands": [{"brand": "brand name", "version": "brand version"}, { ... }, ... ],
                                            "fullVersion": "full version",
                                            "platform": "platform name",
                                            "platformVersion": "platform version",
                                            "architecture": "devise architecture",
                                            "model": "model",
                                            "mobile": boolean,
                                        }
        :return:            None
        """
        args = {"userAgent": userAgent}
        if acceptLanguage is not None:
            args.update({"acceptLanguage": acceptLanguage})
        if platform is not None:
            args.update({"platform": platform})
        if userAgentMetadata is not None:
            args.update({"userAgentMetadata": userAgentMetadata})
        await self.Call("Emulation.setUserAgentOverride", args)

    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] Log [ |>*<|=== Domains ===|>*<| ]
    #   https://chromedevtools.github.io/devtools-protocol/tot/Log
    #   LogEntry -> https://chromedevtools.github.io/devtools-protocol/tot/Log#type-LogEntry

    async def LogEnable(self) -> None:
        """
        Включает 'Log' домен, отправляет записи лога, собранные на данный момент, посредством
            события 'entryAdded'.
        https://chromedevtools.github.io/devtools-protocol/tot/Log#method-enable
        :return:
        """
        await self.Call("Log.enable")
        self.log_domain_enabled = True

    async def LogDisable(self) -> None:
        """
        Выключает 'Log' домен, останавливая отправку сообщений.
        https://chromedevtools.github.io/devtools-protocol/tot/Log#method-disable
        :return:
        """
        await self.Call("Log.disable")
        self.log_domain_enabled = False

    async def ClearLog(self) -> None:
        """
        Очищает список ранее опубликованных сообщений лога.
        https://chromedevtools.github.io/devtools-protocol/tot/Log#method-clear
        :return:
        """
        await self.Call("Log.clear")

    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] Network [ |>*<|=== Domains ===|>*<| ]
    #   https://chromedevtools.github.io/devtools-protocol/tot/Network

    async def NetworkEnable(
            self,
               maxTotalBufferSize: Optional[int] = None,
            maxResourceBufferSize: Optional[int] = None,
                  maxPostDataSize: Optional[int] = None
    ) -> None:
        """
        Включает отслеживание сети, сетевые события теперь будут доставляться клиенту.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-enable
        :param maxTotalBufferSize:      (optional, EXPERIMENTAL) Размер буфера в байтах для использования
                                            при сохранении полезных данных сети (XHR и т. Д.).
        :param maxResourceBufferSize:   (optional, EXPERIMENTAL) Размер буфера для каждого ресурса в
                                            байтах для использования при сохранении полезных данных сети
                                            (XHR и т. Д.).
        :param maxPostDataSize:         (optional) Самый длинный размер тела сообщения (в байтах),
                                            который будет включен в уведомление "requestWillBeSent".
        :return:
        """
        args = {}
        if maxTotalBufferSize is not None:
            args.update({"maxTotalBufferSize": maxTotalBufferSize})
        if maxResourceBufferSize is not None:
            args.update({"maxResourceBufferSize": maxResourceBufferSize})
        if maxPostDataSize is not None:
            args.update({"maxPostDataSize": maxPostDataSize})
        await self.Call("Network.enable", args)
        self.network_domain_enabled = True

    async def NetworkDisable(self) -> None:
        """
        Отключает отслеживание сети, запрещает отправку сетевых событий клиенту.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-disable
        :return:
        """
        await self.Call("Network.disable")
        self.network_domain_enabled = False

    async def EmulateNetworkConditions(
            self, latency: int,
            downloadThroughput: Optional[int] = -1,
              uploadThroughput: Optional[int] = -1,
                      offline: Optional[bool] = False,
                connectionType: Optional[str] = ""
    ) -> None:
        """
        Активирует эмуляцию состояния сети.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-emulateNetworkConditions
        :param latency:             Минимальная задержка от запроса, отправленного полученным заголовкам
                                        ответа (мс).
        :param downloadThroughput:  (optional) Максимальная агрегированная скорость скачивания (байт / с).
                                        -1 отключает регулирование.
        :param uploadThroughput:    (optional) Максимальная агрегированная скорость загрузки (байт / с).
                                        -1 отключает регулирование.
        :param offline:             (optional) 'True' — эмулирует отключение от интернета.
        :param connectionType:      (optional) Основная технология подключения, которую, предположительно
                                        использует браузер.
                                        Allowed values: none, cellular2g, cellular3g, cellular4g,
                                        bluetooth, ethernet, wifi, wimax, other
        :return:
        """
        args = {"latency": latency, "offline": offline}
        if downloadThroughput > -1:
            args.update({"downloadThroughput": downloadThroughput})
        if uploadThroughput > -1:
            args.update({"uploadThroughput": uploadThroughput})
        if connectionType:
            args.update({"connectionType": connectionType})
        await self.Call("Network.emulateNetworkConditions", args)

    async def ClearBrowserCache(self) -> None:
        """
        Clears browser cache.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-clearBrowserCache
        :return:
        """
        await self.Call("Network.clearBrowserCache")

    async def ClearBrowserCookies(self) -> None:
        """
        Clears browser cookies.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-clearBrowserCookies
        :return:
        """
        await self.Call("Network.clearBrowserCookies")

    async def SetBlockedURLs(self, urls: List[str]) -> None:
        """
        (EXPERIMENTAL)
        Блокирует загрузку URL-адресов.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setBlockedURLs
        :param urls:            Шаблоны URL для блокировки. Подстановочные знаки ('*') разрешены.
        :return:
        """
        await self.Call("Network.setBlockedURLs", {"urls": urls})

    async def SetCacheDisabled(self, cacheDisabled: Optional[bool] = True) -> None:
        """
        Включает игнорирование кеша для каждого запроса. Если 'true', кеш не будет использоваться.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setCacheDisabled
        :param cacheDisabled:    Состояние.
        :return:
        """
        await self.Call("Network.setCacheDisabled", {"cacheDisabled": cacheDisabled})

    async def GetAllCookies(self) -> list:
        """
        Возвращает все куки браузера. В зависимости от поддержки бэкэнда, вернет подробную
            информацию о куки в поле куки.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-getAllCookies
        :return: cookies -> (array Cookie) Array of cookie objects.
        """
        return (await self.Call("Network.getAllCookies"))["cookies"]

    async def GetCookies(self, urls: Optional[list] = None) -> list:
        """
        Возвращает все куки браузера для текущего URL. В зависимости от поддержки бэкэнда,
            вернет подробную информацию о куки в поле куки.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-getCookies
        :param urls: список строк содержащих адреса, для которых будут извлечены Cookies [ "https://google.com", ... ]
        :return: cookies -> (array Cookie) Array of cookie objects.
        """
        args = {}
        if urls:
            args.update({"urls": urls})
        return (await self.Call("Network.getCookies", args))["cookies"]

    async def DeleteCookies(
            self, name: str,
               url: Optional[str] = "",
            domain: Optional[str] = "",
              path: Optional[str] = ""
    ) -> None:
        """
        Удаляет файлы cookie браузера с соответствующими именами и URL-адресами или парой домен / путь.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-deleteCookies
        :param name:    Имя куки для удаления.
        :param url:     (optional) Если указан, удаляет все куки с указанным именем, где 'domain' и
                            'path' соответствуют указанному URL.
        :param domain:  (optional) Если указан, удаляет только те куки, что точно соответствуют 'domain'.
        :param path:    (optional) Если указан, удаляет только те куки, что точно соответствуют 'path'.
        :return:
        """
        args = {"name": name}
        if url:
            args.update({"url": url})
        if domain:
            args.update({"domain": domain})
        if path:
            args.update({"path": path})
        await self.Call("Network.deleteCookies", args)

    async def SetCookie(
            self, name: str, value: str,
                  url: Optional[str] = "",
               domain: Optional[str] = "",
                 path: Optional[str] = "",
              secure: Optional[bool] = None,
            httpOnly: Optional[bool] = None,
             sameSite: Optional[str] = "",
              expires: Optional[int] = -1,
             priority: Optional[str] = ""
    ) -> bool:
        """
        Устанавливает cookie с указанными данными cookie. Если они существуют, то будут перезаписаны.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setCookie
        :param name:        Cookie name.
        :param value:       Cookie value.
        :param url:         (optional) The request-URI to associate with the setting of
                                the cookie. This value can affect the default domain and
                                path values of the created cookie.
        :param domain:      (optional) Cookie domain.
        :param path:        (optional) Cookie path.
        :param secure:      (optional) True if cookie is secure.
        :param httpOnly:    (optional) True if cookie is http-only.
        :param sameSite:    (optional) Cookie SameSite type. Represents the cookie's 'SameSite'
                                status: https://tools.ietf.org/html/draft-west-first-party-cookies
                                Allowed values: Strict, Lax, None
        :param expires:     (optional) Cookie expiration date, session cookie if not set.
                                UTC time in seconds, counted from January 1, 1970.
        :param priority:    (optional, EXPERIMENTAL) Cookie Priority type. Represents the cookie's 'Priority'
                                status: https://tools.ietf.org/html/draft-west-cookie-priority-00
                                Allowed values: Low, Medium, High
        :return:            True if successfully set cookie.
        """
        args = {"name": name, "value": value}
        if url:
            args.update({"url": url})
        if domain:
            args.update({"domain": domain})
        if path:
            args.update({"path": path})
        if secure is not None:
            args.update({"secure": secure})
        if secure is not None:
            args.update({"httpOnly": httpOnly})
        if sameSite:
            args.update({"sameSite": sameSite})
        if expires > -1:
            args.update({"expires": expires})
        if priority:
            args.update({"priority": priority})
        return (await self.Call("Network.setCookie", args))["success"]

    async def SetCookies(self, list_cookies: list) -> None:
        """
        Устанавливает сразу список кук
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setCookies
        :param list_cookies:        список куки-параметров
        :return:
        """
        await self.Call("Network.setCookies", {"cookies": list_cookies})

    async def SetExtraHeaders(self, headers: dict) -> None:
        """
        Устанавливает дополнительные заголовки, которые всегда будут отправляться в запросах
            от инстанса текущей страницы.
        https://chromedevtools.github.io/devtools-protocol/tot/Network#method-setExtraHTTPHeaders
        :param headers:        Заголовки запроса / ответа в виде ключей / значений объекта JSON.
        :return:
        """
        await self.Call("Network.setExtraHTTPHeaders", {"headers": headers})

    async def NetworkSetUserAgent(
            self, userAgent: str,
                acceptLanguage: Optional[str] = None,
                      platform: Optional[str] = None,
            userAgentMetadata: Optional[dict] = None
    ) -> None:
        """
        Позволяет переопределить пользовательский агент с заданной строкой. Функционал ничем не
            отличается от одноимённого метода домена 'Emulation'.
        https://chromedevtools.github.io/devtools-protocol/tot/Network/#method-setUserAgentOverride
        :param userAgent:           Новый юзер-агент.
        :param acceptLanguage:      (optional) Язык браузера для эмуляции.
        :param platform:            (optional) Платформа браузера, которую возвращает
                                        "navigator.platform".
                                        https://www.w3schools.com/jsref/prop_nav_platform.asp
        :param userAgentMetadata:   (optional, EXPERIMENTAL) Для отправки в заголовках Sec-CH-UA- * и возврата в
                                        navigator.userAgentData. Ожидатся словарь вида:
                                        {
                                            "brands": [{"brand": "brand name", "version": "brand version"}, { ... }, ... ],
                                            "fullVersion": "full version",
                                            "platform": "platform name",
                                            "platformVersion": "platform version",
                                            "architecture": "devise architecture",
                                            "model": "model",
                                            "mobile": boolean,
                                        }
        :return:            None
        """
        args = {"userAgent": userAgent}
        if acceptLanguage:
            args.update({"acceptLanguage": acceptLanguage})
        if platform:
            args.update({"platform": platform})
        if userAgentMetadata:
            args.update({"userAgentMetadata": userAgentMetadata})
        await self.Call("Network.setUserAgentOverride", args)

    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] Page [ |>*<|=== Domains ===|>*<| ]
    #   https://chromedevtools.github.io/devtools-protocol/tot/Page

    async def BringToFront(self) -> None:
        """
        Выводит страницу на передний план (активирует вкладку).
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-bringToFront
        :return:
        """
        await self.Call("Page.bringToFront")

    async def PageEnable(self) -> None:
        """
        Включает уведомления домена 'Page'.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-enable
        :return:
        """
        await self.AddListenerForEvent("Page.frameStartedLoading", self._StateLoadWatcher, "started")
        await self.AddListenerForEvent("Page.frameNavigated", self._StateLoadWatcher, "navigated")
        await self.AddListenerForEvent("Page.frameStoppedLoading", self._StateLoadWatcher, "stopped")
        await self.Call("Page.enable")
        self.page_domain_enabled = True

    async def PageDisable(self) -> None:
        """
        Выключает уведомления домена 'Page'.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-disable
        :return:
        """
        self.RemoveListenerForEvent("Page.frameStartedLoading", self._StateLoadWatcher)
        self.RemoveListenerForEvent("Page.frameNavigated", self._StateLoadWatcher)
        self.RemoveListenerForEvent("Page.frameStoppedLoading", self._StateLoadWatcher)
        await self.Call("Page.disable")
        self.page_domain_enabled = False

    async def _StateLoadWatcher(self, params: dict, state: str) -> None:
        """
        Устанавливает состояние загрузки фрейма страницы, если включены уведомления
            домена Page.
        """
        frame_id = params["frameId"] if state != "navigated" else params["frame"]["id"]
        if frame_id == self.page_id:
            self.loading_state = state

    async def HandleJavaScriptDialog(self, accept: bool, promptText: Optional[str] = "") -> None:
        """
        Принимает или закрывает диалоговое окно, инициированное JavaScript (предупреждение, подтверждение,
            приглашение или onbeforeunload).
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-handleJavaScriptDialog
        :param accept:          'True' — принять, 'False' — отклонить диалог.
        :param promptText:      Текст для ввода в диалоговом окне, прежде чем принять. Используется,
                                    только если это диалоговое окно с подсказкой.
        :return:
        """
        args = {"accept": accept}
        if promptText:
            args.update({"promptText": promptText})
        await self.Call("Page.handleJavaScriptDialog", args)

    async def Navigate(
            self,
            url: Optional[Union[str, bytes]] = "about:blank",
            default_tab: Optional[bool] = False,
            wait_for_load: Optional[bool] = True
    ) -> None:
        """
        Переходит на адрес указанного 'url'.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-navigate
        :param url:             Адрес, по которому происходит навигация.
        :param default_tab:     Переход в дефолтное состояние вкладки, не зависимо от url.
        :param wait_for_load:   Если 'True' - ожидает 'complete' у 'document.readyState' страницы,
                                    на которую осуществляется переход.
        :return:
        """
        if default_tab: url = "chrome://newtab/"
        if self.page_domain_enabled: self.loading_state = "do_navigate"
        _url_ = ("data:text/html," + quote(url)
            # передать разметку как data-url, если начало этой строки
            # не содержит признаков url-адреса или передать "как есть",
            if type(url) is str and "http" != url[:4] and "chrome" != url[:6] and url != "about:blank" else url
                # раз это строка содержащая url, или переход на пустую страницу
                if type(url) is str and "http" == url[:4] or "chrome" == url[:6] or url == "about:blank" else
                    # иначе декодировать и установить её как Base64
                    "data:text/html;Base64," + url.decode()
        )

        await self.Call("Page.navigate", {"url": _url_}, False)
        if wait_for_load:
            await self.WaitForLoad()

    async def WaitForLoad(
            self, desired_state: Optional[str] = "complete", interval: Optional[float] = .1
    ) -> None:
        """
        Дожидается указанного состояния загрузки документа.
            Если включены уведомления домена Page — дожидается, пока основной фрейм
            страницы не перестанет загружаться.
        :param desired_state:       Желаемое состояние загрузки. По умолчанию == полное.
        :param interval:            Таймаут ожидания.
        :return:        None
        """

        if self.page_domain_enabled:
            while self.loading_state != "stopped":
                await asyncio.sleep(.1)
        else:
            await asyncio.sleep(1)

        while (await self.Eval("document.readyState"))["value"] != desired_state:
            await asyncio.sleep(interval)

    async def AddScriptOnLoad(self, src: str) -> str:
        """
        Запускает полученный 'src' скрипта в каждом фрейме и перед загрузкой скриптов самого фрейма.
            Так же, такой скрипт будет запускаться автоматически в течении всей жизни инстанса,
            включая перезагрузку страницы.
        Требует включения( PageEnable() ) уведомлений домена "Page".
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-addScriptToEvaluateOnNewDocument
        :param src:             Текст сценария.
        :return:                identifier -> Уникальный идентификатор скрипта.
        """
        if not self.page_domain_enabled:
            await self.PageEnable()
        return (await self.Call("Page.addScriptToEvaluateOnNewDocument", {"source": src}))["identifier"]

    async def RemoveScriptOnLoad(self, identifier: str) -> None:
        """
        Удаляет данный скрипт из списка запускаемых при загрузке фрейма.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-removeScriptToEvaluateOnNewDocument
        :param identifier:      Иденификатор сценария.
        :return:
        """
        await self.Call("Page.removeScriptToEvaluateOnNewDocument", {"identifier": identifier})

    async def SetDocumentContent(self, frameId: str, html: str) -> None:
        """
        Удаляет данный скрипт из списка запускаемых при загрузке фрейма.
            frameId — можно найти среди параметров события 'Runtime.executionContextCreated',
            а так же у конрневого элемента документа root.children[1].frameId
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-setDocumentContent
        :param frameId:         Иденификатор фрейма, которому предназначается html.
        :param html:            HTML-разметка.
        :return:
        """
        await self.Call("Page.setDocumentContent", {"frameId": frameId, "html": html})

    async def SetAdBlockingEnabled(self, enabled: bool) -> None:
        """
        (EXPERIMENTAL)
        Включите экспериментальный рекламный фильтр Chrome на всех сайтах.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-setAdBlockingEnabled
        :param enabled:         Включить?
        :return:
        """
        if not self.page_domain_enabled:
            await self.PageEnable()
        await self.Call("Page.setAdBlockingEnabled", {"enabled": enabled})

    async def SetFontFamilies(self, fontFamilies: dict) -> None:
        """
        (EXPERIMENTAL)
        Установить общие семейства шрифтов.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-setFontFamilies
        :param fontFamilies:    Семейства шрифтов:
                                    {
                                        "standard":   str(), -> (optional)
                                        "fixed":      str(), -> (optional)
                                        "serif":      str(), -> (optional)
                                        "sansSerif":  str(), -> (optional)
                                        "cursive":    str(), -> (optional)
                                        "fantasy":    str(), -> (optional)
                                        "pictograph": str(), -> (optional)
                                    }
        :return:
        """
        await self.Call("Page.setFontFamilies", {"fontFamilies": fontFamilies})

    async def SetFontSizes(self, fontSizes: dict) -> None:
        """
        (EXPERIMENTAL)
        Установите размеры шрифта по умолчанию.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-setFontSizes
        :param fontSizes:       Определяет размеры шрифта для установки. Если размер шрифта не
                                    указан, он не будет изменен:
                                    {
                                        "standard": int(), -> (optional)
                                        "fixed":    int(), -> (optional)
                                    }
        :return:
        """
        await self.Call("Page.setFontSizes", {"fontSizes": fontSizes})

    async def CaptureScreenshot(
            self,
                 format_: Optional[str] = "",
                 quality: Optional[int] = -1,
                   clip: Optional[dict] = None,
            fromSurface: Optional[bool] = True
    ) -> str:
        """
        Сделать скриншот. Возвращает кодированное base64 представление скриншота.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-captureScreenshot
        :param format_:         string => Image compression format (defaults to png) (jpeg or png).
        :param quality:         integer => Compression quality from range [0..100] (jpeg only).
        :param clip:            {
                                    "x": "number => X offset in device independent pixels (dip).",
                                    "y": "number => Y offset in device independent pixels (dip).",
                                    "width": "number => Rectangle width in device independent pixels (dip).",
                                    "height": "number => Rectangle height in device independent pixels (dip).",
                                    "scale": "number => Page scale factor."
                                }
        :param fromSurface:     boolean => Capture the screenshot from the surface, rather than the view.
                                    Defaults to true.
        :return:                string => Base64-encoded image data.
        """
        args = {"fromSurface": fromSurface}
        if format_:
            args.update({"format": format_})
        if quality > -1 and format_ == "jpeg":
            args.update({"quality": quality})
        if clip:
            args.update({"clip": clip})
        return (await self.Call("Page.captureScreenshot", args))["data"]

    async def PrintToPDF(
            self,
                          landscape: Optional[bool] = None,
                displayHeaderFooter: Optional[bool] = None,
                    printBackground: Optional[bool] = None,
                             scale: Optional[float] = None,
                        paperWidth: Optional[float] = None,
                       paperHeight: Optional[float] = None,
                         marginTop: Optional[float] = None,
                      marginBottom: Optional[float] = None,
                        marginLeft: Optional[float] = None,
                       marginRight: Optional[float] = None,
                          pageRanges: Optional[str] = None,
            ignoreInvalidPageRanges: Optional[bool] = None,
                      headerTemplate: Optional[str] = None,
                      footerTemplate: Optional[str] = None,
                  preferCSSPageSize: Optional[bool] = None,
                        transferMode: Optional[str] = None
    ) -> dict:
        """
        Печатает страницу как PDF.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-printToPDF
        :param landscape:               (optional) Ориентация бумаги. По умолчанию false.
        :param displayHeaderFooter:     (optional) Отобразить header и footer. По умолчанию false.
        :param printBackground:         (optional) Печать фоновой графики. По умолчанию false.
        :param scale:                   (optional) Масштаб рендеринга веб-страницы. По умолчанию 1.
        :param paperWidth:              (optional) Ширина бумаги в дюймах. По умолчанию 8,5 дюймов.
        :param paperHeight:             (optional) Высота бумаги в дюймах. По умолчанию 11 дюймов.
        :param marginTop:               (optional) Верхний отступ в дюймах. По умолчанию 1 см (~ 0,4 дюйма).
        :param marginBottom:            (optional) Нижний отступ в дюймах. По умолчанию 1 см (~ 0,4 дюйма).
        :param marginLeft:              (optional) Левый отступ в дюймах. По умолчанию 1 см (~ 0,4 дюйма).
        :param marginRight:             (optional) Правый отступ в дюймах. По умолчанию 1 см (~ 0,4 дюйма).
        :param pageRanges:              (optional) Диапазон бумаги для печати, например, '1-5, 8, 11-13'. По
                                            умолчанию используется пустая строка, что означает печать всех страниц.
        :param ignoreInvalidPageRanges: (optional) Следует ли игнорировать недействительные, но успешно
                                            проанализированные диапазоны страниц, например '3-2'. По умолчанию false.
        :param headerTemplate:          (optional) HTML-шаблон для печатного заголовка. Должна быть допустимая
                                            разметка HTML со следующими классами, используемыми для вставки
                                            значений печати в них:
                                                * date:       formatted print date
                                                * title:      document title
                                                * url:        document location
                                                * pageNumber: current page number
                                                * totalPages: total pages in the document
                                                    Например, <span class=title></span> будет генерировать span,
                                                        содержащий заголовок.
        :param footerTemplate:          (optional) HTML-шаблон для печати 'footer'. Следует использовать тот же
                                            формат, что и headerTemplate.
        :param preferCSSPageSize:       (optional) Предпочитать или нет размер страницы, как определено CSS. По
                                            умолчанию установлено значение false, и в этом случае содержимое будет
                                            масштабироваться по размеру бумаги.
        :param transferMode:            (optional, EXPERIMENTAL) вернуть как поток. Допустимые значения:
                                            ReturnAsBase64, ReturnAsStream
        :return:                        {
                                            "data": str(Данные PDF, кодированные в Base64.),
                                                ->  Будет пустым если в 'transferMode' выбрано 'ReturnAsStream'.
                                            "stream": str(Это либо получается из другого метода, либо указывается как blob <uuid> это UUID Blob.)
                                                -> StreamHandle
                                        }
        """
        args = {}
        if landscape is not None:
            args.update({"landscape": landscape})
        if displayHeaderFooter is not None:
            args.update({"displayHeaderFooter": displayHeaderFooter})
        if printBackground is not None:
            args.update({"printBackground": printBackground})
        if scale is not None:
            args.update({"scale": scale})
        if paperWidth is not None:
            args.update({"paperWidth": paperWidth})
        if paperHeight is not None:
            args.update({"paperHeight": paperHeight})
        if marginTop is not None:
            args.update({"marginTop": marginTop})
        if marginBottom is not None:
            args.update({"marginBottom": marginBottom})
        if marginLeft is not None:
            args.update({"marginLeft": marginLeft})
        if marginRight is not None:
            args.update({"marginRight": marginRight})
        if pageRanges is not None:
            args.update({"pageRanges": pageRanges})
        if ignoreInvalidPageRanges is not None:
            args.update({"ignoreInvalidPageRanges": ignoreInvalidPageRanges})
        if headerTemplate is not None:
            args.update({"headerTemplate": headerTemplate})
        if footerTemplate is not None:
            args.update({"footerTemplate": footerTemplate})
        if preferCSSPageSize is not None:
            args.update({"preferCSSPageSize": preferCSSPageSize})
        if transferMode is not None:
            args.update({"transferMode": transferMode})

        return await self.Call("Page.printToPDF", args)

    async def Reload(
            self,
                      ignoreCache: Optional[bool] = False,
            scriptToEvaluateOnLoad: Optional[str] = "",
                    wait_for_load: Optional[bool] = True
    ) -> None:
        """
        Перезагружает страницу инстанса, при необходимости игнорируя кеш.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-reload
        :param ignoreCache:             (optional) Игнорировать кеш?
        :param scriptToEvaluateOnLoad:  (optional) Если установлено, сценарий будет вставлен во все
                                            фреймы проверяемой страницы после перезагрузки. Аргумент
                                            будет игнорироваться при перезагрузке источника dataURL.
        :param wait_for_load:           (optional) По умолчанию — дожидается полного завершения
                                            загрузки страницы(document.readyState === "complete").
                                            Установите False, если это поведение не требуется.
        :return:
        """
        if self.page_domain_enabled: self.loading_state = "do_reload"
        args = {}
        if ignoreCache:
            args.update({"ignoreCache": ignoreCache})
        if scriptToEvaluateOnLoad:
            args.update({"scriptToEvaluateOnLoad": scriptToEvaluateOnLoad})
        await self.Call("Page.reload", args)
        if wait_for_load:
            await self.WaitForLoad()

    async def GetNavigationHistory(self) -> None:
        """
        Возвращает историю навигации для текущей страницы.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-getNavigationHistory
        :return:            {
                                "currentIndex": int(), -> Индекс текущей записи истории навигации.
                                "entries": list({
                                    "id": int(),  -> Уникальный идентификатор записи истории навигации.
                                    "url": str(), -> URL записи истории навигации.
                                    "userTypedURL": str(), -> URL, который пользователь ввел в строке URL.
                                    "title": str(), -> Название записи истории навигации.
                                    "transitionType": str(
                                        link, typed, address_bar, auto_bookmark, auto_subframe,
                                        manual_subframe, generated, auto_toplevel, form_submit,
                                        reload, keyword, keyword_generated, other
                                    ) -> Тип перехода.
                                }, ... ) -> Список записей истории навигации.
                            }
        """
        return await self.Call("Page.getNavigationHistory")

    async def NavigateToHistoryEntry(self, entryId: int) -> None:
        """
        Навигация текущей страницы к выбранной записи в истории навгации.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-navigateToHistoryEntry
        :param entryId:             Уникальный идентификатор записи для перехода.
        :return:
        """
        await self.Call("Page.navigateToHistoryEntry", {"entryId": entryId})

    async def ResetNavigationHistory(self) -> None:
        """
        Сбрасывает историю навигации для текущей страницы.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-resetNavigationHistory
        :return:
        """
        await self.Call("Page.resetNavigationHistory")

    async def SetDownloadBehavior(self, behavior: str, downloadPath: Optional[str] = "") -> None:
        """
        Устанавливает поведение при загрузке файлов.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-setDownloadBehavior
        :param behavior:            Разрешить все или отклонить все запросы на загрузку, или использовать поведение
                                        Chrome по умолчанию, если доступно (в противном случае запретить).
                                        deny = запрет, allow = разрешить, default
        :param downloadPath:        (optional) Путь по умолчанию для сохранения загруженных файлов в. Это необходимо,
                                        если для поведения установлено значение 'allow' и если путь не передан, будет
                                        установлен текущее расположение.
        :return:
        """
        args = {"behavior": behavior}
        if (behavior == "allow" or behavior == "default") and downloadPath == "":
            args.update({"downloadPath": os.path.abspath(".")})
        await self.Call("Page.setDownloadBehavior", args)

    async def SetInterceptFileChooserDialog(self, enabled: bool) -> None:
        """
        Перехватывает запросы выбора файлов и передает управление клиентам протокола. Когда включен перехват
            файлов, диалоговое окно выбора файлов не отображается. Вместо этого генерируется событие
            протокола Page.fileChooserOpened.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-setInterceptFileChooserDialog
        :param enabled:             Включить перехват?
        :return:
        """
        await self.Call("Page.setInterceptFileChooserDialog", {"enabled": enabled})

    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] Runtime [ |>*<|=== Domains ===|>*<| ]
    #   https://chromedevtools.github.io/devtools-protocol/tot/Runtime

    async def AwaitPromise(
            self, promiseObjectId: str, returnByValue: bool = False, generatePreview: bool = False
    ) -> any:
        """
        Добавляет обработчик к промису с переданным идентификатором.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-awaitPromise
        :param promiseObjectId:     Идентификатор промиса.
        :param returnByValue:       (optional) Ожидается ли результат в виде объекта JSON,
                                        который должен быть отправлен по значению.
        :param generatePreview:     (optional) Должен ли предварительный просмотр
                                        генерироваться для результата.
        :return:                    {
                                        "result": dict(https://chromedevtools.github.io/devtools-protocol/tot/Runtime#type-RemoteObject)
                                        "exceptionDetails": dict(https://chromedevtools.github.io/devtools-protocol/tot/Runtime#type-ExceptionDetails)
                                    }
        """
        args = {"promiseObjectId": promiseObjectId, "returnByValue": returnByValue, "generatePreview": generatePreview}
        response = await self.Call("Runtime.awaitPromise", args)
        if "exceptionDetails" in response:
            raise Exception(response["result"]["description"] + "\n" + json.dumps(response["exceptionDetails"]))
        return response["result"]

    async def CallFunctionOn(
            self, functionDeclaration: str,
                      objectId: Optional[str] = None,
                    arguments: Optional[list] = None,
                       silent: Optional[bool] = None,
                returnByValue: Optional[bool] = None,
              generatePreview: Optional[bool] = None,
                  userGesture: Optional[bool] = None,
                 awaitPromise: Optional[bool] = None,
            executionContextId: Optional[int] = None,
                   objectGroup: Optional[str] = None
    ) -> dict:
        """
        Вызывает функцию с заданным объявлением для данного объекта. Группа объектов результата
            наследуется от целевого объекта.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-callFunctionOn
        :param functionDeclaration:     Объявление функции для вызова.
        :param objectId:                (optional) Идентификатор объекта для вызова функции.
                                            Должен быть указан либо objectId, либо executeContextId.
        :param arguments:               (optional) Аргументы. Все аргументы вызова должны
                                            принадлежать тому же миру JavaScript, что и целевой
                                            объект.
        :param silent:                  (optional) В тихом режиме исключения, выданные во время оценки,
                                            не регистрируются и не приостанавливают выполнение.
                                            Переопределяет 'setPauseOnException' состояние.
        :param returnByValue:           (optional) Ожидается ли результат в виде объекта JSON,
                                            который должен быть отправлен по значению.
        :param generatePreview:         (optional, EXPERIMENTAL) Должен ли предварительный
                                            просмотр генерироваться для результата.
        :param userGesture:             (optional) Должно ли выполнение рассматриваться как
                                            инициированное пользователем в пользовательском интерфейсе.
        :param awaitPromise:            (optional) Решено ли выполнение awaitдля полученного значения
                                            и возврата после ожидаемого обещания.
        :param executionContextId:      (optional) Определяет контекст выполнения, в котором будет
                                            использоваться глобальный объект для вызова функции.
                                            Должен быть указан либо executeContextId, либо objectId.
        :param objectGroup:             (optional) Символическое имя группы, которое можно
                                            использовать для освобождения нескольких объектов. Если
                                            objectGroup не указан, а objectId равен, objectGroup
                                            будет унаследован от объекта.
        :return:                        { ... } - https://chromedevtools.github.io/devtools-protocol/tot/Runtime/#type-RemoteObject
        """
        args = {"functionDeclaration": functionDeclaration}
        if objectId is not None:
            args.update({"objectId": objectId})
        if arguments is not None:
            args.update({"arguments": arguments})
        if silent is not None:
            args.update({"silent": silent})
        if returnByValue is not None:
            args.update({"returnByValue": returnByValue})
        if generatePreview is not None:
            args.update({"generatePreview": generatePreview})
        if userGesture is not None:
            args.update({"userGesture": userGesture})
        if awaitPromise is not None:
            args.update({"awaitPromise": awaitPromise})
        if executionContextId is not None:
            args.update({"executionContextId": executionContextId})
        if objectGroup is not None:
            args.update({"objectGroup": objectGroup})
        response = await self.Call("Runtime.callFunctionOn", args)
        if "exceptionDetails" in response:
            raise Exception(response["result"]["description"] + "\n" + json.dumps(response["exceptionDetails"]))
        return response["result"]

    async def RuntimeEnable(self) -> None:
        """
        Включает создание отчетов о создании контекстов выполнения с помощью события executeContextCreated.
            При включении, событие будет отправлено немедленно для каждого существующего контекста выполнения.

        Позволяет так же организовать обратную связь со страницей, посылая из её контекста, данные, в консоль.
            В этом случае будет генерироваться событие 'Runtime.consoleAPICalled':
            https://chromedevtools.github.io/devtools-protocol/tot/Runtime#event-consoleAPICalled
            {
                'method': 'Runtime.consoleAPICalled',
                params': {
                    'type': 'log',
                    'args': [{'type': 'string', 'value': 'you console data passed was be here'}],
                    'executionContextId': 2,
                    'timestamp': 1583582949679.153,
                    'stackTrace': {
                        'callFrames': [{'functionName': '', 'scriptId': '48', 'url': '', 'lineNumber': 0, 'columnNumber': 8}]
                    }
                }
            }

        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-enable
        :return:
        """
        await self.Call("Runtime.enable")
        self.runtime_enabled = True

    async def RuntimeDisable(self) -> None:
        """
        Отключает создание отчетов о создании контекстов выполнения.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-disable
        :return:
        """
        await self.Call("Runtime.disable")
        self.runtime_enabled = False

    async def DiscardConsoleEntries(self) -> None:
        """
        Отбрасывает собранные исключения и вызовы API консоли.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-discardConsoleEntries
        :return:
        """
        await self.Call("Runtime.discardConsoleEntries")

    async def ReleaseObjectGroup(self, objectGroup: str) -> None:
        """
        Освобождает все удаленные объекты, принадлежащие данной группе.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-releaseObjectGroup
        :param objectGroup:             Символическое имя группы.
        :return:
        """
        await self.Call("Runtime.releaseObjectGroup", {"objectGroup": objectGroup})

    async def CompileScript(
            self, expression: str,
                     sourceURL: Optional[str] = "",
                persistScript: Optional[bool] = True,
            executionContextId: Optional[int] = None
    ) -> dict:
        """
        Компилирует выражение.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-compileScript
        :param expression:              Выражение для компиляции.
        :param sourceURL:               Исходный URL для скрипта.
        :param persistScript:           Указывает, следует ли сохранить скомпилированный скрипт.
        :param executionContextId:      (optional) Указывает, в каком контексте выполнения выполнять сценарий.
                                            Если параметр не указан, выражение будет выполняться в контексте
                                            проверяемой страницы.
        :return:                        {
                                            "scriptId": str()
                                            "exceptionDetails": dict(https://chromedevtools.github.io/devtools-protocol/tot/Runtime#type-ExceptionDetails)
                                        }
        """
        args = {"expression": expression, "sourceURL": sourceURL, "persistScript": persistScript}
        if executionContextId is not None:
            args.update({"executionContextId": executionContextId})

        response = await self.Call("Runtime.compileScript", args)
        if "exceptionDetails" in response:
            raise Exception(response["exceptionDetails"]["text"] + "\n" + json.dumps(response["exceptionDetails"]))
        return response["scriptId"]

    async def RunScript(
            self, scriptId: str,
                executionContextId: Optional[int] = None,
                       objectGroup: Optional[str] = "console",
                           silent: Optional[bool] = False,
            includeCommandLineAPI: Optional[bool] = True,
                    returnByValue: Optional[bool] = False,
                  generatePreview: Optional[bool] = False,
                     awaitPromise: Optional[bool] = True
    ) -> dict:
        """
        Запускает скрипт с заданным идентификатором в заданном контексте.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-runScript
        :param scriptId:                ID сценария для запуска.
        :param executionContextId:      (optional) Указывает, в каком контексте выполнения выполнять сценарий.
                                            Если параметр не указан, выражение будет выполняться в контексте
                                            проверяемой страницы.
        :param objectGroup:             (optional) Символическое имя группы, которое можно использовать для
                                            освобождения нескольких объектов.
        :param silent:                  (optional) В тихом режиме исключения, выданные во время оценки, не
                                            сообщаются и не приостанавливают выполнение. Переопределяет
                                            состояние setPauseOnException.
        :param includeCommandLineAPI:   (optional) Определяет, должен ли API командной строки быть доступным
                                            во время оценки.
        :param returnByValue:           (optional) Ожидается ли результат в виде объекта JSON, который должен
                                            быть отправлен по значению.
        :param generatePreview:         (optional) Должен ли предварительный просмотр генерироваться для результата.
        :param awaitPromise:            (optional) Будет ли выполнено ожидание выполнения для полученного значения
                                            и возврата после ожидаемого 'promise'.
        :return:                        {
                                            "result": dict(https://chromedevtools.github.io/devtools-protocol/tot/Runtime#type-RemoteObject)
                                            "exceptionDetails": dict(https://chromedevtools.github.io/devtools-protocol/tot/Runtime#type-ExceptionDetails)
                                        }
        """
        args = {
            "scriptId": scriptId, "objectGroup": objectGroup, "silent": silent,
            "includeCommandLineAPI": includeCommandLineAPI, "returnByValue": returnByValue,
            "generatePreview": generatePreview, "awaitPromise": awaitPromise
        }
        if executionContextId is not None:
            args.update({"executionContextId": executionContextId})

        response = await self.Call("Runtime.runScript", args)
        if "exceptionDetails" in response:
            raise Exception(response["result"]["description"] + "\n" + json.dumps(response["exceptionDetails"]))
        return response["result"]

    async def AddBinding(self, name: str, executionContextId: Optional[int] = None) -> None:
        """
        (EXPERIMENTAL)
        Если executeContextId пуст, добавляет привязку с заданным именем к глобальным объектам всех
            проверенных контекстов, включая созданные позже, привязки переживают перезагрузки. Если
            указан executeContextId, добавляет привязку только к глобальному объекту данного
            контекста выполнения. Функция привязки принимает ровно один аргумент, этот аргумент
            должен быть строкой, в случае любого другого ввода функция выдает исключение. Каждый
            вызов функции привязки создает уведомление Runtime.bindingCalled.
        https://chromedevtools.github.io/devtools-protocol/tot/Runtime#method-addBinding
        :param name:                    Имя привязки.
        :param executionContextId:      (optional) Идентификатор контекста исполнения.
        :return:
        """
        args = {"name": name}
        if executionContextId is not None:
            args.update({"executionContextId": executionContextId})

        await self.Call("Runtime.addBinding", args)

    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] Target [ |>*<|=== Domains ===|>*<| ]
    #   https://chromedevtools.github.io/devtools-protocol/tot/Target

    async def GetTargetInfo(self, targetId: Optional[str] = "") -> dict:
        """
        (EXPERIMENTAL)
        Возвращает информацию о "target", или о себе, если идентификатор не передан.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-getTargetInfo
        :param targetId:            Идентификатор страницы/сервиса/воркера/...
        :return:                    targetInfo -> {
                                        "targetId":         str,
                                        "type":             str,
                                        "title":            str,
                                        "url":              str,
                                        "attached":         bool,
                                        "openerId":         str,
                                        "browserContextId": str,
                                    }
        """
        if not targetId:
            targetId = self.page_id
        return (await self.Call("Target.getTargetInfo", {"targetId": targetId}))["targetInfo"]

    async def GetTargets(self) -> List[dict]:
        """
        Возвращает список 'targetInfo' о доступных 'targets'.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-getTargets
        :return:                [ targetInfo, targetInfo, ... ]
        """
        return (await self.Call("Target.getTargets"))["targetInfos"]

    async def ActivateTarget(self, targetId: str) -> None:
        """
        Активирует (создаёт фокус) "target".
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-activateTarget
        :param targetId:        Строка, представляющая идентификатор созданной страницы.
        :return:
        """
        await self.Call("Target.activateTarget", {"targetId": targetId})

    async def AttachToTarget(self, targetId: str, flatten: Optional[bool] = None) -> str:
        """
        Присоединяется к 'target' по указанному 'targetId'.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-attachToTarget
        :param targetId:        Строка, представляющая идентификатор созданной страницы.
        :param flatten:         (optional) Разрешает "flat" доступ к сеансу с помощью указания атрибута
                                    sessionId в командах.
        :return:                sessionId -> Идентификатор, назначенный сеансу.
        """
        args = {"targetId": targetId}
        if flatten is not None:
            args.update({"flatten": flatten})
        return (await self.Call("Target.attachToTarget", args))["sessionId"]

    async def DetachFromTarget(self, sessionId: Optional[str] = "") -> None:
        """
        Отключается от сессии переданного 'sessionId'.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-detachFromTarget
        :param sessionId:       (optional) Строка, представляющая идентификатор созданной страницы.
        :return:
        """
        args = {}
        if sessionId:
            args.update({"sessionId": sessionId})
        await self.Call("Target.detachFromTarget", args)

    async def CreateTarget(
            self,
                    url: Optional[str] = "about:blank",
           default_tab: Optional[bool] = False,
             newWindow: Optional[bool] = False,
            background: Optional[bool] = False
    ) -> str:
        """
        Создаёт новую страницу и возвращает её идентификатор. Чтобы затем управлять новой
            вкладкой, воспользуйтесь методом инстанса самого браузера GetPageByID(), или
            сразу методом CreatePage(), который проделывает все эти операции под капотом
            и возвращает готовый инстанс новой страницы.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-createTarget
        :param url:             Адрес будет открыт при создании.
        :param default_tab:     Если 'True' — будет открыт дефолтный бэкграунд, как
                                    при обычном создании новой вкладки.
        :param newWindow:       Если 'True' — страница будет открыта в новом окне.
        :param background:      Если 'True' — страница будет открыта в фоне.
        :return:                targetId -> строка, представляющая идентификатор созданной страницы.
        """
        url = "chrome://newtab/" if default_tab else url
        return (await self.Call("Target.createTarget", {
            "url": url,
            "newWindow": False if self.is_headless_mode else newWindow,
            "background": False if self.is_headless_mode else background
        }))["targetId"]

    async def CloseTarget(self, targetId: Optional[str] = None) -> None:
        """
        Закрывает вкладку указанного идентификатора, или завершает собственный инстанс,
            если идентификатор не передан.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-closeTarget
        :param targetId:        Строка, представляющая идентификатор созданной страницы.
        :return:                None
        """
        if targetId is None:
            targetId = self.page_id
        await self.Call("Target.closeTarget", {"targetId": targetId})

    async def SetDiscoverTargets(self, discover: bool) -> None:
        """
        Управляет обнаружением доступных 'targets' уведомляя об их состоянии с помощью событий
            targetCreated / targetInfoChanged / targetDestroyed.
        https://chromedevtools.github.io/devtools-protocol/tot/Target#method-setDiscoverTargets
        :param discover:            'True' — включает эту надстройку, 'False' — выключает.
        :return:
        """
        await self.Call("Target.setDiscoverTargets", {"discover": discover})

    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] Overlay [ |>*<|=== Domains ===|>*<| ]
    #   Этот домен предоставляет различные функции, связанные с рисованием на проверяемой странице.
    #   https://chromedevtools.github.io/devtools-protocol/tot/Overlay

    async def SetShowFPSCounter(self) -> None:
        """
        Запрашивает бэкэнд показ счетчика FPS.
        https://chromedevtools.github.io/devtools-protocol/tot/Overlay#method-setShowFPSCounter
        :return:
        """
        await self.Call("Overlay.setShowFPSCounter")

    # TODO
    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] CSS [ |>*<|=== Domains ===|>*<| ]
    #   https://chromedevtools.github.io/devtools-protocol/tot/CSS

    async def _CSS_sheet_catcher(self, data: dict) -> None:
        """
        Колбэк вызываемый для каждого 'CSS.styleSheetAdded'-события, если
            включён агент домена 'CSS'.
        """
        self.style_sheets.append(data["header"]["styleSheetId"])

    async def CSSEnable(self) -> None:
        """
        Включает агент CSS. Клиент не должен предполагать, что агент CSS включен,
            пока не будет получен результат этой команды.
        https://chromedevtools.github.io/devtools-protocol/tot/CSS/#method-disable
        :return:
        """
        if not self.css_domain_enabled:
            await self.AddListenerForEvent("CSS.styleSheetAdded", self._CSS_sheet_catcher)
            await self.Call("CSS.enable")
            self.css_domain_enabled = True

    async def CSSDisable(self) -> None:
        """
        Отключает агент CSS.
        https://chromedevtools.github.io/devtools-protocol/tot/CSS/#method-disable
        :return:
        """
        if self.css_domain_enabled:
            self.RemoveListenerForEvent("CSS.styleSheetAdded", self._CSS_sheet_catcher)
            await self.Call("CSS.disable")
            self.css_domain_enabled = False

    # TODO
    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] DeviceOrientation [ |>*<|=== Domains ===|>*<| ]
    #   https://chromedevtools.github.io/devtools-protocol/tot/DeviceOrientation

    async def ClearDeviceOrientationOverride(self) -> None:
        """
        Очищает переопределенную ориентацию устройства.
        https://chromedevtools.github.io/devtools-protocol/tot/DeviceOrientation/#method-clearDeviceOrientationOverride
        :return:
        """
        await self.Call("DeviceOrientation.clearDeviceOrientationOverride")

    async def SetDeviceOrientationOverride(self, alpha: float, beta: float, gamma: float) -> None:
        """
        Переопределяет ориентацию устройства, принудительно изменяя значения сенсоров, котоые так же
            можно найти в консоли браузера по Ctrl+Shift+P и в поиске ввести 'Show Sensors'.
        https://chromedevtools.github.io/devtools-protocol/tot/DeviceOrientation/#method-setDeviceOrientationOverride
        :return:
        """
        args = {"alpha": alpha, "beta": beta, "gamma": gamma}
        await self.Call("DeviceOrientation.setDeviceOrientationOverride", args)

    # TODO
    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] DOMStorage [ |>*<|=== Domains ===|>*<| ]
    #   https://chromedevtools.github.io/devtools-protocol/tot/DOMStorage

    # TODO
    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] Fetch [ |>*<|=== Domains ===|>*<| ]
    #   https://chromedevtools.github.io/devtools-protocol/tot/Fetch

    async def FetchEnable(
            self,
              patterns: Optional[ List[dict] ] = None,
            handleAuthRequests: Optional[bool] = False,
              fetch_onResponse: Optional[bool] = False
    ) -> None:
        """
        Включает выдачу событий requestPaused. Запрос будет приостановлен до тех пор,
            пока клиент не вызовет одну из функций failRequest, fulfillRequest или
            continueRequest / continueWithAuth.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-enable
        :param patterns:            (optional) Если указано, только запросы,
                                        соответствующие любому из этих шаблонов, будут
                                        вызывать событие fetchRequested и будут
                                        приостановлены до ответа клиента. Если не
                                        установлен, все запросы будут затронуты.
                                            https://chromedevtools.github.io/devtools-protocol/tot/Fetch#type-RequestPattern
        :param handleAuthRequests:  (optional) Если True - события authRequired будут
                                        выдаваться и запросы будут приостановлены в
                                        ожидании вызова continueWithAuth.
        :param fetch_onResponse:    (optional) Если True - добавляет в шаблон остлеживание
                                        этапа запроса с перехватом в состоянии "ответ".
        :return:
        """
        args = {}; patterns = patterns if patterns is not None else []
        if fetch_onResponse:
            patterns.append({"requestStage": "Response"})
        if patterns:
            args.update({"patterns": patterns})
        if handleAuthRequests:
            args.update({"handleAuthRequests": handleAuthRequests})
        await self.Call("Fetch.enable", args)
        self.fetch_domain_enabled = True

    async def FetchDisable(self) -> None:
        """
        Отключает взаимодействие с доменом.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-disable
        :return:
        """
        await self.Call("Fetch.disable")
        self.fetch_domain_enabled = False

    async def FailRequest(self, requestId: str, errorReason: str) -> None:
        """
        Вызывает сбой запроса по указанной причине.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-failRequest
        :param requestId:           Идентификатор, полученный клиентом в событии requestPaused.
        :param errorReason:         Причина сбоя выборки на уровне сети. Возможные значения:
                                        Failed, Aborted, TimedOut, AccessDenied,
                                        ConnectionClosed, ConnectionReset,
                                        ConnectionRefused, ConnectionAborted,
                                        ConnectionFailed, NameNotResolved,
                                        InternetDisconnected, AddressUnreachable,
                                        BlockedByClient, BlockedByResponse
        :return:
        """
        await self.Call("Fetch.failRequest", {"requestId": requestId, "errorReason": errorReason})

    async def FulfillRequest(
            self, requestId: str,
                        responseCode: Optional[int] = 200,
            responseHeaders: Optional[ List[dict] ] = None,
               binaryResponseHeaders: Optional[str] = None,
                                body: Optional[str] = None,
                      responsePhrase: Optional[str] = None,
                  wait_for_response: Optional[bool] = False
    ) -> None:
        """
        Предоставляет ответ на запрос.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-fulfillRequest
        :param requestId:               Идентификатор, полученный клиентом в событии requestPaused.
        :param responseCode:            Код ответа HTTP(например - 200).
        :param responseHeaders:         (optional) Заголовки ответа. Например:
                                            [
                                                { "name": "User-Agent", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36" },
                                                { "name": "Content-Type", "value": "application/json; charset=UTF-8" }
                                            ]
        :param binaryResponseHeaders:   (optional) Альтернативный способ указания заголовков ответа в
                                            виде разделенных \0 серий пар имя-значение. Описанный выше
                                            метод предпочтительней, если вам не нужно представлять
                                            некоторые значения, отличные от UTF8, которые не могут быть
                                            переданы по протоколу, в виде текста.
        :param body:                    (optional) Тело ответа, кодированное в строку формата base64.
        :param responsePhrase:          (optional) Текстовое представление responseCode. Если
                                            отсутствует, используется стандартная фраза,
                                            соответствующая responseCode.
        :return:
        """
        args = {"requestId": requestId, "responseCode": responseCode}
        if responseHeaders is not None:
            args.update({"responseHeaders": responseHeaders})
        if binaryResponseHeaders is not None:
            args.update({"binaryResponseHeaders": binaryResponseHeaders})
        if body is not None:
            args.update({"body": body})
        if responsePhrase is not None:
            args.update({"responsePhrase": responsePhrase})
        # print("fulfillRequest args", json.dumps(args, indent=4))
        await self.Call("Fetch.fulfillRequest", args, wait_for_response=wait_for_response)

    async def ContinueRequest(
            self, requestId: str,
                           url: Optional[str] = None,
                        method: Optional[str] = None,
                      postData: Optional[str] = None,
              headers: Optional[ List[dict] ] = None,
            wait_for_response: Optional[bool] = False
    ) -> None:
        """
        Продолжает запрос, дополнительно изменяя некоторые его параметры.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-continueRequest
        :param requestId:           Идентификатор, полученный клиентом в событии requestPaused.
        :param url:                 (optional) Если установлено, URL-адрес запроса будет изменен так,
                                        чтобы страница не наблюдалась.
        :param method:              (optional) Переопределяет метод запроса переданным значением.
        :param postData:            (optional) Переопределяет данные запроса переданными.
        :param headers:             (optional) Переопределяет заголовки запроса переданными. . Например:
                                        [
                                            { "name": "User-Agent", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36" },
                                            { "name": "Content-Type", "value": "application/json; charset=UTF-8" }
                                        ]
        :return:
        """
        args = {"requestId": requestId}
        if url is not None:
            args.update({"url": url})
        if method is not None:
            args.update({"method": method})
        if postData is not None:
            args.update({"postData": postData})
        if headers is not None:
            args.update({"headers": headers})
        await self.Call("Fetch.continueRequest", args, wait_for_response=wait_for_response)

    async def ContinueWithAuth(self, requestId: str, authChallengeResponse: list) -> None:
        """
        Продолжает запрос, предоставляющий authChallengeResponse после события authRequired.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-continueWithAuth
        :param requestId:               Идентификатор, полученный клиентом в событии requestPaused.
        :param authChallengeResponse:   Ответ с помощью authChallenge.
                                            {
                                                "response": str(), -> Решение о том, что делать в ответ
                                                    на запрос авторизации. По умолчанию означает
                                                    использование стандартного поведения сетевого стека,
                                                    что, скорее всего, приведет к отмене проверки
                                                    подлинности или появлению всплывающего диалогового
                                                    окна. Возможные значения:
                                                        Default, CancelAuth, ProvideCredentials
                                                "username": str(), -> (optional) Имя пользователя для
                                                    предоставления, может быть пустым. Устанавливается,
                                                    только если ответом является ProvideCredentials.
                                                "password": str(), -> (optional) Пароль пользователя для
                                                    предоставления, может быть пустым. Устанавливается,
                                                    только если ответом является ProvideCredentials.
                                            }
        :return:
        """
        args = {"requestId": requestId, "authChallengeResponse": authChallengeResponse}
        await self.Call("Fetch.continueWithAuth", args)

    async def GetResponseBody(self, requestId: str) -> dict:
        """
        Вызывает тело ответа, получаемого от сервера и возвращаемого в виде одной строки. Может
            выдаваться только для запроса, который приостановлен на этапе ответа и является
            взаимоисключающим с "takeResponseBodyForInterceptionAsStream". Вызов других методов,
            влияющих на запрос, или отключение домена выборки до получения тела приводит к
            неопределенному поведению.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-getResponseBody
        :param requestId:               Идентификатор перехваченного запроса для получения его тела.
        :return:                        {
                                            "body": str(),        -> Тело ответа.
                                            "base64Encoded": bool -> True - если контент кодирован
                                                                        как base64.
                                        }
        """
        return await self.Call("Fetch.getResponseBody", {"requestId": requestId})

    async def TakeResponseBodyAsStream(self, requestId: str) -> dict:
        """
        Возвращает дескриптор потока, представляющего тело ответа. Запрос должен быть приостановлен
            на этапе HeadersReceived. Обратите внимание, что после этой команды запрос не может быть
            продолжен как есть - клиент должен либо отменить его, либо предоставить тело ответа.
            Поток поддерживает только последовательное чтение, IO.read потерпит неудачу, если указана
            позиция. Этот метод является взаимоисключающим с getResponseBody. Вызов других методов,
            влияющих на запрос, или отключение домена выборки до получения тела приводит к
            неопределенному поведению.
        https://chromedevtools.github.io/devtools-protocol/tot/Fetch#method-takeResponseBodyAsStream
        :param requestId:               Идентификатор перехваченного запроса для получения его тела.
        :return:                        {
                                            "stream": str(), -> Это либо получается из другого метода,
                                                либо указывается как blob <uuid> это UUID Blob.
                                                    IO.StreamHandle:
                                                    https://chromedevtools.github.io/devtools-protocol/tot/IO#type-StreamHandle
                                        }
        """
        return await self.Call("Fetch.takeResponseBodyAsStream", {"requestId": requestId})

    # TODO
    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] IndexedDB [ |>*<|=== Domains ===|>*<| ]
    #   https://chromedevtools.github.io/devtools-protocol/tot/IndexedDB

    # TODO
    # endregion

    # region [ |>*<|=== Domains ===|>*<| ] Other [ |>*<|=== Domains ===|>*<| ]
    #

    async def GetUrl(self):
        return (await self.GetTargetInfo())["url"]

    async def GetTitle(self):
        return (await self.GetTargetInfo())["title"]

    async def MakeScreenshot(
            self,
                 format_: Optional[str] = "",
                 quality: Optional[int] = -1,
                   clip: Optional[dict] = None,
            fromSurface: Optional[bool] = True
    ) -> bytes:
        """
        Сделать скриншот. Возвращает набор байт, представляющий скриншот.
        :param format_:         jpeg или png (по умолчанию png).
        :param quality:         Качество изображения в диапазоне [0..100] (только для jpeg).
        :param clip:            {
                                    "x": "number => X offset in device independent pixels (dip).",
                                    "y": "number => Y offset in device independent pixels (dip).",
                                    "width": "number => Rectangle width in device independent pixels (dip).",
                                    "height": "number => Rectangle height in device independent pixels (dip).",
                                    "scale": "number => Page scale factor."
                                }
        :param fromSurface:     boolean => Capture the screenshot from the surface, rather than the view.
                                    Defaults to true.
        :return:                bytes
        """
        shot = await self.CaptureScreenshot(format_, quality, clip, fromSurface)
        return base64.b64decode(shot.encode("utf-8"))

    async def SelectInputContentBy(self, css: str) -> None:
        await self.InjectJS(f"let _i_ = document.querySelector('{css}'); _i_.focus(); _i_.select();")

    async def ScrollIntoViewJS(self, selector: str):
        await self.InjectJS(
            "document.querySelector(\"" +
            selector +
            "\").scrollIntoView({'behavior':'smooth', 'block': 'center'});"
        )

    async def InjectJS(self, code: str):
        try:
            result = await self.Eval(code)
        except Exception as error:
            print("InjectJS() Exception with injected code ->\n", code, "\n")
            raise
        return result.get('value')

    async def CatchMetaForUrl(self, url: str, uniq_key: Optional[str] = None) -> None:
        """
        Получает заголовки запроса, ответа, а так же cookie для конкретного url и сохраняет их
            в виде словарей в поле собственного инстанса, доступного как:
            page_instance.storage[uniq_key]. Если 'uniq_key' не указан, в его качестве будет
            использован 'url'.

        Для работы будет активирован домен Fetch со значением "True" для "fetch_onResponse".
        :param url:             Адрес ресурса, или его уникальная часть.
        :param uniq_key:        Идентификатор, под которым будут сохраняться данные перехвата.
        :return:
        """
        if not self.fetch_domain_enabled:
            await self.FetchEnable(fetch_onResponse=True)
        key = uniq_key if uniq_key else url
        await self.AddListenerForEvent("Fetch.requestPaused", catch_headers_for_url, self, url, self.storage, key)


    # endregion

async def catch_headers_for_url(data: dict, instance: 'PageEx', url: str, storage: dict, storage_key: str) -> None:
    """
    Получает заголовки запроса, ответа, а так же cookie для конкретного url и сохраняет их
    в виде словарей в переданном по ссылке 'storage'. Требует активации домена Fetch со значением
    "True" для "fetch_onResponse", после чего, инстансу страницы, эта корутина добавляется как
     слушатель транслирующий через 'data' параметры перехваченных запросов. Например:
            await page.FetchEnable( fetch_onResponse=True )
            await page.AddListenerForEvent(
                "Fetch.requestPaused",
                catch_headers_for_url,
                page,
                "persistentBadging",
                GLOBAL_STORAGE,
                "storage_key"
            )
    Структура сохранённых данных: (dict) {
        "request_url":      (str) - полный url перехваченного запроса,
        "request_headers":  (dict) - {"hdr_name": "hdr_value", "hdr_name": "hdr_value", ... },
        "response_headers": (dict) - {"hdr_name": "hdr_value", "hdr_name": "hdr_value", ... },
        "response_cookies": (dict) - {"cook_name": "cook_value", "cook_name": "cook_value", ... },
        "full_cookie_data": (list[ dict ]) - [
            {
                "name": "cookie name",
                "value": "cookie value",
                "domain": ".instagram.com",
                "path": "/",
                "expires": -1,
                "size": 149,
                "httpOnly": true,
                "secure": true,
                "session": true,
                "priority": "Medium"
            }, { ... }
        ]
    }
    :param data:            Содержимое перехваченного запроса. Эти данные будут переданы в слушатель из браузера.
                                Структура: {
                                    requestId: (str),
                                    request: {
                                        url: (str),
                                        method: (str),
                                        headers: (dict) — Все заголовки запроса включая куки,
                                        postData: (str) — payload POST-запросов,
                                        initialPriority: (str),
                                        referrerPolicy: (str),
                                        Возможно какие-то ещё ...
                                    },
                                    frameId: (str) — like "75ED3620550E8F5E16B8F6D1FF2EE4D1",
                                    resourceType: (str) — like "XHR",
                                    responseStatusCode: (int) — like 200,
                                    responseHeaders: (List[dict]) — заголовки ответа, не включая куки:
                                        [ {'name': 'content-type', 'value': '"application/json; charset=utf-8'}, ... ]
                                }
    :param instance:        Инстанс страницы, от лица которой происходит перехват.
    :param url:             Адрес ресурса, или его уникальная часть.
    :param storage:         Ссылка на словарь, в который будет сохранён результат.
    :param storage_key:     Идентификатор, под которым сохранится запись в 'storage'.
    :return:    None
    """
    asyncio.create_task(instance.ContinueRequest(data["requestId"]))
    if url in data["request"]["url"]:
        response_headers = {}; response_cookies = {}
        for item in data["responseHeaders"]: response_headers[item["name"]] = item["value"]
        full_cookie_data = await instance.GetCookies()
        for item in full_cookie_data:
            response_cookies[item["name"]] = item["value"]
        storage[storage_key] = {
            "request_url":      data["request"]["url"],
            "request_headers":  data["request"]["headers"],
            "response_headers": response_headers,
            "response_cookies": response_cookies,
            "full_cookie_data": full_cookie_data
        }
