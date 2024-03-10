import asyncio
from typing import Optional, Union, Callable, Awaitable, TYPE_CHECKING
from ...data import DomainEvent
from ...utils import prepare_url
from .types import FrameTree, LifecycleEventData
if TYPE_CHECKING:
    from ...connection import Connection


class Page:
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/Page
    """
    __slots__ = (
        "_connection", "enabled", "loading_state_watcher_enabled", "network_idle_state_watcher_enabled",
        "lifecycle_events_enabled", "loading_state", "network_idle_state"
    )
    def __init__(self, conn) -> None:
        self._connection: Connection = conn
        self.enabled = False
        self.loading_state_watcher_enabled = False
        self.network_idle_state_watcher_enabled = False
        self.loading_state = asyncio.Event()
        self.lifecycle_events_enabled = False
        self.network_idle_state = asyncio.Event()

    async def enable(self) -> None:
        """
        Включает уведомления домена 'Page'.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-enable
        """
        if not self.enabled:
            await self._connection.call("Page.enable")
            self.enabled = True

    async def disable(self) -> None:
        """
        Выключает уведомления домена 'Page'.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-disable
        """
        if self.enabled:
            if self.loading_state_watcher_enabled:
                await self.enableLoadWatcher(False)
            if self.network_idle_state_watcher_enabled:
                await self.enableNetworkIdleWatcher(False)
            await self._connection.call("Page.disable")
            self.enabled = False

    async def enableLoadWatcher(self, state: bool) -> None:
        """ Уведомляет событие loading_state, что основной фрейм страницы завершил загрузку.
        :param state:           Вкл/выкл
        """
        async def load_watcher_wrapper(params: dict, *_) -> None:
            if params["frameId"] == self._connection.conn_id:
                self.loading_state.set()

        if state != self.loading_state_watcher_enabled:
            if state:
                await self._connection.addListenerForEvent(
                    PageEvent.frameStoppedLoading, load_watcher_wrapper)
            else:
                self._connection.removeListenerForEvent(
                    PageEvent.frameStoppedLoading, load_watcher_wrapper)
            self.loading_state_watcher_enabled = state

    async def createIsolatedWorld(
            self, frameId: str, worldName: Optional[str] = None, grantUniversalAccess: Optional[bool] = None) -> int:
        """
        Создаёт изолированный мир для указанного фрейма.
        https://chromedevtools.github.io/devtools-protocol/1-3/Page/#method-createIsolatedWorld
        :param frameId:                 Идентификатор фрейма, в котором должен быть создан изолированный мир.
        :param worldName:               Необязательное имя, о котором сообщается в контексте выполнения.
        :param grantUniversalAccess:    Должен ли быть предоставлен универсальный доступ к изолированному миру.
                                            Это мощная опция, используйте ее с осторожностью.
        :return:            Runtime.ExecutionContextId
        """
        args = dict(frameId=frameId)
        if worldName is not None: args.update(worldName=worldName)
        if grantUniversalAccess is not None: args.update(grantUniversalAccess=grantUniversalAccess)
        result: dict = await self._connection.call("Page.createIsolatedWorld", args)
        return result.get("executionContextId")

    async def getFrameTree(self) -> 'FrameTree':
        """
        Возвращает структуру присутствующих на странице фреймов. !!! Справедливо только в рамках одного домена.
        https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-getFrameTree
        """
        result = await self._connection.call("Page.getFrameTree")
        return FrameTree(**result.get("frameTree"))


    async def handleJavaScriptDialog(self, accept: bool, promptText: str = "") -> None:
        """
        Подтверждает или закрывает диалоговое окно, инициированное JavaScript (alert, confirm,
            prompt или для onbeforeunload).
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-handleJavaScriptDialog
        :param accept:          'True' — принять, 'False' — отклонить диалог.
        :param promptText:      (optional) Текст для ввода в диалоговом окне, прежде чем принять.
                                    Используется, только если это диалоговое окно с подсказкой.
        :return:
        """
        args = {"accept": accept}
        if promptText: args.update({"promptText": promptText})
        await self._connection.call("Page.handleJavaScriptDialog", args)

    async def navigate(
            self,
            url:  Union[str,     bytes] = "about:blank",
            wait_for_load:         bool = True,
            wait_for_network_idle: bool = False
    ) -> None:
        """
        Переходит на адрес указанного 'url'.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-navigate
        :param url:                     Адрес, по которому происходит навигация.
        :param wait_for_load:           (optional) Если 'True' - ожидает состояния остановки
                                            загрузки ресурсов, если активны уведомления домена Page.
        :param wait_for_network_idle:   (optional) Если 'True' - ожидает прекращения активности сети
        :return:
        """
        url = prepare_url(url, self._connection.browser_name)

        await self._connection.call("Page.navigate", {"url": url})
        if wait_for_load or wait_for_network_idle:
            await self.waitForLoad(wait_for_load, wait_for_network_idle)

    async def waitForLoad(self, by_load_state: bool = False, by_network_idle: bool = True) -> None:
        """ Дожидается указанного состояния.
        :param by_load_state:       Ожидать завершения загрузки страницы.
        :param by_network_idle:     Ожидать завершения активности сети.
        """

        if not by_load_state and not by_network_idle:
            raise ValueError("'by_load_state' or 'by_network_idle' must be a True")

        if not self.enabled:
            await self.enable()

        if by_load_state:
            if not self.loading_state_watcher_enabled:
                await self.enableLoadWatcher(True)
                self.loading_state_watcher_enabled = True
            await self.loading_state.wait()

        if by_network_idle:
            if not self.network_idle_state_watcher_enabled:
                await self.enableNetworkIdleWatcher(True)
            await self.network_idle_state.wait()

    async def addScriptOnLoad(self, src: str) -> str:
        """
        Запускает полученный 'src' скрипта в каждом фрейме и перед загрузкой скриптов самого фрейма.
            Так же, такой скрипт будет запускаться автоматически в течении всей жизни инстанса,
            включая перезагрузку страницы.
        Требует включения( Enable() ) уведомлений домена "Page".
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-addScriptToEvaluateOnNewDocument
        :param src:             Текст сценария.
        :return:                identifier -> Уникальный идентификатор скрипта.
        """
        if not self.enabled: await self.enable()
        return (await self._connection.call("Page.addScriptToEvaluateOnNewDocument", {"source": src}))["identifier"]

    async def removeScriptOnLoad(self, identifier: str) -> None:
        """
        Удаляет данный скрипт из списка запускаемых при загрузке фрейма.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-removeScriptToEvaluateOnNewDocument
        :param identifier:      Идентификатор сценария.
        :return:
        """
        await self._connection.call("Page.removeScriptToEvaluateOnNewDocument", {"identifier": identifier})

    async def setDocumentContent(self, html: str, frameId: str = None) -> None:
        """
        Устанавливает полученную разметку как HTML-код документа.
            frameId — можно найти среди параметров события 'Runtime.executionContextCreated',
            а так же у корневого элемента документа root.children[1].frameId
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-setDocumentContent
        :param html:            HTML-разметка.
        :param frameId:         Идентификатор фрейма, которому предназначается html.
        :return:
        """
        if frameId is None: frameId = self._connection.conn_id
        await self._connection.call("Page.setDocumentContent", {"frameId": frameId, "html": html})

    async def stopLoading(self) -> None:
        """
        Останавливает загрузку страницы.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-stopLoading
        :return:
        """
        await self._connection.call("Page.stopLoading")

    async def setAdBlockingEnabled(self, enabled: bool) -> None:
        """
        (EXPERIMENTAL)
        Включите экспериментальный рекламный фильтр Chrome на всех сайтах.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-setAdBlockingEnabled
        :param enabled:         Включить?
        :return:
        """
        if not self.enabled: await self.enable()
        await self._connection.call("Page.setAdBlockingEnabled", {"enabled": enabled})

    async def setFontFamilies(self, fontFamilies: dict) -> None:
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
        await self._connection.call("Page.setFontFamilies", {"fontFamilies": fontFamilies})

    async def setFontSizes(self, fontSizes: dict) -> None:
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
        await self._connection.call("Page.setFontSizes", {"fontSizes": fontSizes})

    async def captureScreenshot(
        self,
        format_: str = "",
        quality: int = -1,
        clip: Optional[dict] = None,
        fromSurface: bool = True
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
        if format_: args.update({"format": format_})
        if quality > -1 and format_ == "jpeg": args.update({"quality": quality})
        if clip: args.update({"clip": clip})
        return (await self._connection.call("Page.captureScreenshot", args))["data"]

    async def printToPDF(
        self,
        landscape:               Optional[bool] = None,
        displayHeaderFooter:     Optional[bool] = None,
        printBackground:         Optional[bool] = None,
        scale:                  Optional[float] = None,
        paperWidth:             Optional[float] = None,
        paperHeight:            Optional[float] = None,
        marginTop:              Optional[float] = None,
        marginBottom:           Optional[float] = None,
        marginLeft:             Optional[float] = None,
        marginRight:            Optional[float] = None,
        pageRanges:               Optional[str] = None,
        ignoreInvalidPageRanges: Optional[bool] = None,
        headerTemplate:           Optional[str] = None,
        footerTemplate:           Optional[str] = None,
        preferCSSPageSize:       Optional[bool] = None,
        transferMode:             Optional[str] = None
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
        if landscape is not None:               args.update({"landscape": landscape})
        if displayHeaderFooter is not None:     args.update({"displayHeaderFooter": displayHeaderFooter})
        if printBackground is not None:         args.update({"printBackground": printBackground})
        if scale is not None:                   args.update({"scale": scale})
        if paperWidth is not None:              args.update({"paperWidth": paperWidth})
        if paperHeight is not None:             args.update({"paperHeight": paperHeight})
        if marginTop is not None:               args.update({"marginTop": marginTop})
        if marginBottom is not None:            args.update({"marginBottom": marginBottom})
        if marginLeft is not None:              args.update({"marginLeft": marginLeft})
        if marginRight is not None:             args.update({"marginRight": marginRight})
        if pageRanges is not None:              args.update({"pageRanges": pageRanges})
        if ignoreInvalidPageRanges is not None: args.update({"ignoreInvalidPageRanges": ignoreInvalidPageRanges})
        if headerTemplate is not None:          args.update({"headerTemplate": headerTemplate})
        if footerTemplate is not None:          args.update({"footerTemplate": footerTemplate})
        if preferCSSPageSize is not None:       args.update({"preferCSSPageSize": preferCSSPageSize})
        if transferMode is not None:            args.update({"transferMode": transferMode})

        return await self._connection.call("Page.printToPDF", args)

    async def reload(
            self,
            ignoreCache: bool = False,
            scriptToEvaluateOnLoad: str = "",
            wait_for_load: bool = False,
            wait_for_network_idle: bool = True
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
        if self.enabled:
            self.loading_state.clear()
        if self.lifecycle_events_enabled:
            self.network_idle_state.clear()
        args = {}
        if ignoreCache:            args.update({"ignoreCache": ignoreCache})
        if scriptToEvaluateOnLoad: args.update({"scriptToEvaluateOnLoad": scriptToEvaluateOnLoad})
        await self._connection.call("Page.reload", args)
        if wait_for_load or wait_for_network_idle:
            await self.waitForLoad(wait_for_load, wait_for_network_idle)

    async def getNavigationHistory(self) -> dict:
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
        return await self._connection.call("Page.getNavigationHistory")

    async def navigateToHistoryEntry(self, entryId: int) -> None:
        """
        Навигация текущей страницы к выбранной записи в истории навгации.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-navigateToHistoryEntry
        :param entryId:             Уникальный идентификатор записи для перехода.
        :return:
        """
        if self.enabled: self.loading_state.clear()
        await self._connection.call("Page.navigateToHistoryEntry", {"entryId": entryId})

    async def resetNavigationHistory(self) -> None:
        """
        Сбрасывает историю навигации для текущей страницы.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-resetNavigationHistory
        :return:
        """
        await self._connection.call("Page.resetNavigationHistory")

    async def setInterceptFileChooserDialog(self, enabled: bool) -> None:
        """
        Перехватывает запросы выбора файлов и передает управление клиентам протокола. Когда включен перехват
            файлов, диалоговое окно выбора файлов не отображается. Вместо этого генерируется событие
            протокола Page.fileChooserOpened.
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-setInterceptFileChooserDialog
        :param enabled:             Включить перехват?
        :return:
        """
        await self._connection.call("Page.setInterceptFileChooserDialog", {"enabled": enabled})

    async def setLifecycleEventsEnabled(
            self, enabled: bool,
            handler: Optional[Callable[[LifecycleEventData], Awaitable[None]]] = None,
    ) -> None:
        """
        Определяет, будет ли страница генерировать события жизненного цикла.
        https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-setLifecycleEventsEnabled
        :param enabled:            Если true, начинает генерировать события жизненного цикла.
        :param handler:            Awaitable объект, которому будут переданы данные события.
        :return:
        """
        async def life_cycle_event_wrapper(params: dict, *_) -> None:
            await handler(LifecycleEventData(**params))

        if self.lifecycle_events_enabled != enabled:
            if enabled and handler is not None:
                await self._connection.addListenerForEvent(
                    PageEvent.lifecycleEvent, life_cycle_event_wrapper)
            else:
                self._connection.removeListenersForEvent(PageEvent.lifecycleEvent)

            await self._connection.call("Page.setLifecycleEventsEnabled", {"enabled": enabled})
            self.lifecycle_events_enabled = enabled

    async def enableNetworkIdleWatcher(self, state: bool) -> None:
        """ [Вк/Вык]лючает наблюдение за событием жизненного цикла ресурса, когда
        у него возникает состояние с именем `networkIdle`, говорящее о простое сети.

        Этот метод активируется автоматически при совершении переходов по URL-адресам
        """
        async def idle_watcher_wrapper(params: dict, *_) -> None:
            if params["frameId"] == self._connection.conn_id:
                if params["name"] == "networkIdle":
                    self.network_idle_state.set()

        if state:
            if not self.lifecycle_events_enabled:
                await self.setLifecycleEventsEnabled(True)
            if not self.network_idle_state_watcher_enabled:
                await self._connection.addListenerForEvent(
                    PageEvent.lifecycleEvent, idle_watcher_wrapper)
        elif not state and self.network_idle_state_watcher_enabled:
            self._connection.removeListenerForEvent(
                PageEvent.lifecycleEvent, idle_watcher_wrapper)
        self.network_idle_state_watcher_enabled = state

    async def bringToFront(self) -> None:
        """
        Выводит страницу на передний план (активирует вкладку).
        https://chromedevtools.github.io/devtools-protocol/tot/Page#method-bringToFront
        :return:
        """
        await self._connection.call("Page.bringToFront")


class PageEvent(DomainEvent):
    domContentEventFired = "Page.domContentEventFired"
    fileChooserOpened = "Page.fileChooserOpened"
    frameAttached = "Page.frameAttached"
    frameDetached = "Page.frameDetached"
    frameNavigated = "Page.frameNavigated"
    interstitialHidden = "Page.interstitialHidden"
    interstitialShown = "Page.interstitialShown"
    javascriptDialogClosed = "Page.javascriptDialogClosed"
    javascriptDialogOpening = "Page.javascriptDialogOpening"
    lifecycleEvent = "Page.lifecycleEvent"
    loadEventFired = "Page.loadEventFired"
    windowOpen = "Page.windowOpen"
    frameClearedScheduledNavigation = "Page.frameClearedScheduledNavigation"    # DEPRECATED
    frameScheduledNavigation = "Page.frameScheduledNavigation"                  # DEPRECATED
    backForwardCacheNotUsed = "Page.backForwardCacheNotUsed"                    # ! EXPERIMENTAL
    compilationCacheProduced = "Page.compilationCacheProduced"                  # ! EXPERIMENTAL
    documentOpened = "Page.documentOpened"                                      # ! EXPERIMENTAL
    frameRequestedNavigation = "Page.frameRequestedNavigation"                  # ! EXPERIMENTAL
    frameResized = "Page.frameResized"                                          # ! EXPERIMENTAL
    frameStartedLoading = "Page.frameStartedLoading"                            # ! EXPERIMENTAL
    frameStoppedLoading = "Page.frameStoppedLoading"                            # ! EXPERIMENTAL
    navigatedWithinDocument = "Page.navigatedWithinDocument"                    # ! EXPERIMENTAL
    screencastFrame = "Page.screencastFrame"                                    # ! EXPERIMENTAL
    screencastVisibilityChanged = "Page.screencastVisibilityChanged"            # ! EXPERIMENTAL
    downloadProgress = "Page.downloadProgress"                                  # * EXPERIMENTAL DEPRECATED
    downloadWillBegin = "Page.downloadWillBegin"                                # * EXPERIMENTAL DEPRECATED
