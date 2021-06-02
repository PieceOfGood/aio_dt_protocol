from abc import ABC, abstractmethod
from typing import Optional, Union, List
from aio_dt_protocol.DOMElement import Node

class DOM(ABC):
    """
    #   https://chromedevtools.github.io/devtools-protocol/tot/DOM
    """
    __slots__ = ()

    def __init__(self):
        self.dom_domain_enabled = False

    @property
    def connected(self) -> bool:
        return False

    @property
    def verbose(self) -> bool:
        return False

    @property
    def page_id(self) -> str:
        return ""

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
        node: dict = (await self.Call("DOM.getDocument"))["root"]
        node["selector"] = ""
        return Node(self, **node)

    async def QuerySelector(self, selector: str) -> Union[Node, None]:
        """
        Выполняет DOM-запрос, возвращая объект найденного узла, или None.
            Эквивалент  === document.querySelector()
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-querySelector
        :param selector:        Селектор.
        :return:                <Node>
        """
        repeat = 0; max_repeat = 2; error = ""
        root_node_id = (await self.Call("DOM.getDocument"))["root"]["nodeId"]
        while repeat < max_repeat:
            try:
                node: dict = await self.Call("DOM.querySelector", {
                    "nodeId": root_node_id, "selector": selector
                })
                node["selector"] = selector
                return Node(self, **node) if node["nodeId"] > 0 else None
            except Exception as e:
                repeat += 1; error = str(e)
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
        repeat = 0; max_repeat = 2; nodes = []; error = ""
        root_node_id = (await self.Call("DOM.getDocument"))["root"]["nodeId"]
        while repeat < max_repeat:
            try:
                for node in (await self.Call("DOM.querySelectorAll", {
                    "nodeId": root_node_id, "selector": selector
                }))["nodeIds"]:
                    nodes.append(Node(self, node, selector))
                return nodes
            except Exception as e:
                repeat += 1; error = str(e)
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
            if self.verbose:
                print("[SearchResults] node_id =", node_id)
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

    @abstractmethod
    async def Call(
            self, domain_and_method: str,
            params: Optional[dict] = None,
            wait_for_response: Optional[bool] = True
    ) -> Union[dict, None]: raise NotImplementedError("async method Call() — is not implemented")
