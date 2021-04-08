import re
import asyncio
from typing import List, Tuple, Dict, Optional, Union
# from Chrome.PageEx import PageEx


class Node:

    def __init__(
        self, page_instance, nodeId: int,
        backendNodeId:         Optional[int] = None,
        nodeType:              Optional[int] = None,
        nodeName:              Optional[str] = None,
        localName:             Optional[str] = None,
        nodeValue:             Optional[str] = None,
        parentId:              Optional[int] = None,
        publicId:              Optional[str] = None,
        systemId:              Optional[str] = None,
        childNodeCount:        Optional[int] = None,
        children:       Optional[List[dict]] = None,
        attributes:      Optional[List[str]] = None,    # Идут в списке парами ['имя атрибута', 'значение атрибута', 'имя атрибута', 'значение атрибута', ... ]
        frameId:               Optional[str] = None,    # доступен по дефолту в свойствах второго потомка рута  root.children[1].frameId
        documentURL:           Optional[str] = None,
        baseURL:               Optional[str] = None,
        xmlVersion:            Optional[str] = None,
        shadowRoots:  Optional[List["Node"]] = None,    # Появляются так же у <input /> вместо 'children'
        shadowRootType:        Optional[str] = None,

    ):
        self.page_instance = page_instance  # PageEx
        self.nodeId = nodeId
        self.backendNodeId = backendNodeId
        self.nodeType = nodeType
        self.nodeName = nodeName
        self.localName = localName
        self.nodeValue = nodeValue

        self.parentId = parentId
        self.publicId = publicId
        self.systemId = systemId

        self.childNodeCount = childNodeCount
        self.children = self._AddChildren(children)
        self.attributes = attributes
        self.frameId = frameId
        self.documentURL = documentURL
        self.baseURL = baseURL
        self.xmlVersion = xmlVersion

        self.shadowRoots = shadowRoots
        self.shadowRootType = shadowRootType


    def _AddChildren(self, children_list: Optional[List[dict]] = None) -> List["Node"]:
        """
        Вызывается рекурсивно всякий раз, когда описание нового узла содержит
            список потомков, а так же, когда уже созданному узлу запрашиваются
            его потомки посредством метода GetChildNodes().
        :param children_list:        Список словарей, описывающих свойства потомков.
        :return:        List[Node]
        """
        if not children_list: return []
        list_nodes = []
        for child in children_list:
            list_nodes.append(Node(self.page_instance, **child))
        return list_nodes


    async def QuerySelector(self, selector: str) -> Union["Node", None]:
        """
        Выполняет DOM-запрос, возвращая объект найденного узла, или None.
            Эквивалент  === element.querySelector()
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-querySelector
        :param selector:        Селектор.
        :return:        <Node>
        """
        repeat = 0; max_repeat = 2; error = ""
        while repeat < max_repeat:
            try:
                node_id = (
                    await self.page_instance.Call("DOM.querySelector", {
                        "nodeId": self.nodeId, "selector": selector
                    }))["nodeId"]
                return Node(node_id, self.page_instance) if node_id else None
            except Exception as e:
                repeat += 1; error = str(e)
        raise Exception(error)

    async def QuerySelectorAll(self, selector: str) -> List["Node"]:
        """
        Выполняет DOM-запрос, возвращая список объектов найденных узлов, или пустой список.
            Эквивалент  === element.querySelectorAll()
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-querySelectorAll
        :param selector:        Селектор.
        :return:        [ <Node>, <Node>, ... ]
        """
        repeat = 0; max_repeat = 2; nodes = []; error = ""
        while repeat < max_repeat:
            try:
                for node_id in (await self.page_instance.Call("DOM.querySelectorAll", {
                            "nodeId": self.nodeId, "selector": selector
                        }))["nodeIds"]:
                    nodes.append(Node(node_id, self.page_instance))
                return nodes
            except Exception as e:
                repeat += 1; error = str(e)
        raise Exception(error)

    async def GetChildNodes(self, depth: Optional[int] = -1, pierce: Optional[bool] = False) -> None:
        """
        Запрашивает событие 'DOM.setChildNodes' для собственного узла и устанавливает слушателя.
            Как только событие будет сгенерировано для текущего идентификатора узла, слушатель
            будет отменён. Список полученных потомков узла, включая текстовые будет доступен
            через его свойство 'children'.

        !ВНИМАНИЕ! Запрос потомков у <input /> не генерирует событие 'DOM.setChildNodes',
            потому как это одиночный тег, внутри которого не может быть потомков.
        :param depth:           Глубина иерархии, до которой будут получены все потомки.
                                    По умолчанию -1 == все. Чтобы задать конкретное значение,
                                    укажите любое целое число больше нуля.
        :param pierce:          Получать содержимое теневых узлов(shadowRoots, shadowDOM)?
        :return:        None
        """
        async def catch(data: dict) -> None:
            if data["parentId"] == self.nodeId:
                self.page_instance.RemoveListenerForEvent("DOM.setChildNodes", catch)
                self.children = self._AddChildren(data["nodes"])

        self.children = None
        await self.page_instance.AddListenerForEvent("DOM.setChildNodes", catch)
        await self.RequestChildNodes(depth, pierce)
        while self.children is None: await asyncio.sleep(.01)

    async def ScrollIntoView(self, rect: dict = None) -> None:
        """
        (EXPERIMENTAL)
        Прокручивает указанный прямоугольник, в котором находится узел, если он еще не виден.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-scrollIntoViewIfNeeded
        :param rect:        (optional) Прямоугольник, который будет прокручиваться в поле зрения относительно
                                поля границы узла, в пикселях CSS. Если не указан, будет использоваться
                                центр узла, аналогично Element.scrollIntoView.
                                Ожидается словарь, вида: {"x": 100, "y": 100, "width", 200, "height": 200}
        :return:        None
        """
        args = {"nodeId": self.nodeId}
        if rect:
            args.update({"rect": rect})
        await self.page_instance.Call("DOM.scrollIntoViewIfNeeded", args)

    async def FocusNode(self) -> bool:
        """
        Фокусируется на элементе.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-focus
        :return:            Была ли фокуссировака успешной
        """
        try:
            await self.page_instance.Call("DOM.focus", {"nodeId": self.nodeId})
            return True
        except:
            return False

    async def GetAttributes(self) -> list:
        """
        Возвращает список атрибутов элемента.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-getAttributes
        :return:            array [ string ] - Чередующийся массив имен и значений атрибутов элемента.
        """
        return (await self.page_instance.Call("DOM.getAttributes", {"nodeId": self.nodeId}))["attributes"]

    async def RemoveAttribute(self, name: str) -> None:
        """
        Удаляет атрибут по 'name'.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-removeAttribute
        :param name:        Имя удаляемого атрибута.
        :return:
        """
        await self.page_instance.Call("DOM.removeAttribute", {"nodeId": self.nodeId, "name": name})

    async def RemoveNode(self) -> None:
        """
        Удаляет себя из документа.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-removeNode
        :return:
        """
        await self.page_instance.Call("DOM.removeNode", {"nodeId": self.nodeId})

    async def GetBoxModel(self) -> list:
        """
        Возвращает 'box-model' элемента.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-getBoxModel
        :return:            {
                                "content": Quad,                    -> Content box
                                "padding": Quad,                    -> Padding box
                                "border": Quad,                     -> Border box
                                "margin": Quad,                     -> Margin box
                                "width": Integer,                   -> Node width
                                "height": Integer,                  -> Node height
                                "shapeOutside": ShapeOutsideInfo    -> (optional) внешняя форма
                            }
        """
        return (await self.page_instance.Call("DOM.getBoxModel", {"nodeId": self.nodeId}))["model"]

    async def GetOuterHTML(self) -> str:
        """
        Возвращает HTML-разметку элемента включая внешние границы тега.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-getOuterHTML
        :return:            Строка HTML-разметки. '<div>Inner div text</div>'.
        """
        return (await self.page_instance.Call("DOM.getOuterHTML", {"nodeId": self.nodeId}))["outerHTML"]

    async def GetInnerHTML(self) -> str:
        """
        Возвращает HTML-разметку элемента НЕ включая внешние границы тега.
        :return:            Строка HTML-разметки. 'Inner div <div>text</div> with HTML'.
        """
        html = await self.GetOuterHTML()
        return re.findall(r"^<.*?>(.*)<.*?>$", html)[0]

    async def GetInnerText(self, with_new_line_symbols: Optional[bool] = True) -> str:
        """
        Возвращает текстовое содержимое элемента.
        :param with_new_line_symbols:     (optional) — Оставлять символы новой строки?
        :return:                        Текст.
        """
        pattern = r"<.*?>" if with_new_line_symbols else r"(<.*?>)|\n"
        html = await self.GetOuterHTML()
        return re.sub(pattern, "", html).strip()

    async def SetOuterHTML(self, outerHTML: str) -> None:
        """
        Устанавливает HTML-разметку для элемента. !Внимание! После этого преобразования, элемент
            получит новый идентификатор и повтороно обратиться к нему уже не получится.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-setOuterHTML
        :param outerHTML:       Строка HTML-разметки. '<div>Inner div text</div>'.
        :return:
        """
        await self.page_instance.Call("DOM.setOuterHTML", {"nodeId": self.nodeId, "outerHTML": outerHTML})

    async def MoveTo(
            self, targetNodeId: int,
            insertBeforeNodeId: Optional[int] = None
    ) -> None:
        """
        Перемещает узел в новый контейнер, помещает его перед заданным якорем. В результате,
            внутренний идентификатор узла будет сменён.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-moveTo
        :param targetNodeId:        Идентификатор элемента, куда будет помещён элемент.
        :param insertBeforeNodeId   (optional) Попытается поместить в этот элемент, но если он
                                        не будет найден, то перемещаемый элемент становится
                                        последним дочерним элементом 'targetNodeId'.
        :return:
        """
        args = {"nodeId": self.nodeId, "targetNodeId": targetNodeId}
        if insertBeforeNodeId:
            args.update({"insertBeforeNodeId": insertBeforeNodeId})
        self.nodeId = (await self.page_instance.Call("DOM.moveTo", args))["nodeId"]

    async def CopyTo(
            self, targetNodeId: int, insertBeforeNodeId: Optional[int] = None
    ) -> "Node":
        """
        Создает глубокую копию текущего узла и помещает ее в 'targetNodeId' перед 'insertBeforeNodeId',
            если последний указан и будет найден. Возвращает склонированный узел.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-moveTo
        :param targetNodeId:        Идентификатор элемента, куда будет скопирован текущий элемент.
        :param insertBeforeNodeId   (optional) Попытается поместить в этот элемент, но если он
                                        не будет найден, то копируемый элемент становится
                                        последним дочерним элементом 'targetNodeId'.
        :return:                    <Node> - клона.
        """
        args = {"nodeId": self.nodeId, "targetNodeId": targetNodeId}
        if insertBeforeNodeId:
            args.update({"insertBeforeNodeId": insertBeforeNodeId})
        node_id = (await self.page_instance.Call("DOM.copyTo", args))["nodeId"]
        return Node(node_id, self.page_instance)

    async def GetContentQuads(
            self,
            backendNodeId: Optional[int] = None,
                 objectId: Optional[str] = None
    ) -> List[List[int]]:
        """
        (EXPERIMENTAL)
        Возвращает квадраты, которые описывают положение узла на странице. Этот метод может вернуть
            несколько квадратов для встроенных узлов.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM/#method-getContentQuads
        :param backendNodeId:       Бэкенд идентификатор нода.
        :param objectId:            Идентификатор объекта JavaScript обертки узла.
        :return:                    quads - Массив четырехугольных вершин, где за  x всегда следует y,
                                        указывая точки по часовой стрелке.
        """
        args = {"nodeId": self.nodeId}
        if not args and backendNodeId is not None:
            args.update({"backendNodeId": backendNodeId})
        if not args and objectId is not None:
            args.update({"objectId": objectId})
        if args:
            return (await self.page_instance.Call("DOM.getContentQuads", args))["quads"]

    async def SetAttributeValue(self, attributeName: str, value: str) -> None:
        """
        Устанавливает атрибут для элемента с данным идентификатором.
            Например: await node.SetAttributeValue('class', 'class-name')
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-setAttributeValue
        :param attributeName:   Attribute name.
        :param value:           Attribute value.
        :return:
        """
        await self.page_instance.Call("DOM.setAttributeValue", {"nodeId": self.nodeId, "name": attributeName, "value": value})

    async def RequestChildNodes(self, depth: Optional[int] = 1, pierce: Optional[bool] = False) -> None:
        """
        Запрашивает, чтобы дочерние элементы узла с данным идентификатором возвращались
            вызывающей стороне в форме событий DOM.setChildNodes, при которых извлекаются
            не только непосредственные дочерние элементы, но и все дочерние элементы до
            указанной глубины.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-requestChildNodes
        :param depth:           (optional) - Максимальная глубина, на которой должны быть получены
                                    дочерние элементы, по умолчанию равна 1. Используйте -1 для
                                    всего поддерева или укажите целое число больше 0.
        :param pierce:           (optional) - Должны ли проходить фреймы и теневые корни при
                                    возврате поддерева (по умолчанию false).
        :return:
        """
        args = {"nodeId": self.nodeId, "depth": depth, "pierce": pierce}
        await self.page_instance.Call("DOM.requestChildNodes", args)

    async def SetAttributesAsText(self, text: str, name: Optional[str] = "") -> None:
        """
        Устанавливает атрибуты для элемента с заданным идентификатором. Этот метод полезен, когда пользователь
            редактирует некоторые существующие значения и типы атрибутов в нескольких парах имя/значение атрибута.
            Например(!не проверено!): await node.SetAttributesAsText("'class: class-name' 'data-id: new data-id'")
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-setAttributesAsText
        :param text:            Текст с рядом атрибутов. Будет анализировать этот текст с помощью HTML-парсера.
        :param name:            (optional) Имя атрибута для замены новыми атрибутами, полученными из текста,
                                    в случае успешного анализа текста.
        :return:
        """
        args = {"nodeId": self.nodeId, "text": text}
        if name:
            args.update({"name": name})
        await self.page_instance.Call("DOM.setAttributesAsText", args)

    async def SetFileInputFiles(self, files: List[str]) -> None:
        """
        Устанавливает файлы для '<input />'- элемента с заданным идентификатором.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-setFileInputFiles
        :param files:           Список файлов. [ "path", "path", ... ]
        :return:
        """
        await self.page_instance.Call("DOM.setFileInputFiles", {"nodeId": self.nodeId, "files": files})

    async def SetNewName(self, name: str) -> None:
        """
        Устанавливает новое имя узла для узла. В результате узел получит новый иденификатор.
            Например: await node.SetNewName('span')
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-setNodeName
        :param name:            Новое имя элемента(узла).
        :return:
        """

        self.nodeId = (await self.page_instance.Call("DOM.setNodeName", {"nodeId": self.nodeId, "name": name}))["nodeId"]

    async def SetNewValue(self, value: str) -> None:
        """
        Устанавливает значение.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-setNodeValue
        :param value:           Новое значение элемента(узла).
        :return:
        """
        await self.page_instance.Call("DOM.setNodeValue", {"nodeId": self.nodeId, "value": value})

    async def SetInspectedNode(self) -> None:
        """
        Позволяет консоли обращаться к этому узлу с через $ x (см. Более подробную
            информацию о функциях $ x в API командной строки).
        https://chromedevtools.github.io/devtools-protocol/tot/DOM#method-setInspectedNode
        :return:        None
        """
        await self.page_instance.Call("DOM.setInspectedNode", {"nodeId": self.nodeId})

    async def CollectClassNames(self) -> List[str]:
        """
        Собирает имена классов для выбранного узла и всех его потомков.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM/#method-collectClassNamesFromSubtree
        :return:                Список имён классов.
        """
        return (await self.page_instance.Call("DOM.collectClassNamesFromSubtree", {"nodeId": self.nodeId}))["classNames"]

    async def GetNodesForSubtreeByStyle(
            self, computedStyles: List[dict],
            pierce: Optional[bool] = False
    ) -> List["Node"]:
        """
        Находит узлы с заданным вычисленным стилем в поддереве текущего узла.
        https://chromedevtools.github.io/devtools-protocol/tot/DOM/#method-collectClassNamesFromSubtree
        :param computedStyles:  Список вычисляемых CSS-свойств, соответствие которым будет проверяться.
                                    Например, найти все узлы, ширина которых = 50px, а высота = 15px
                                    [{'name': 'width', 'value': '50px'}, {'name': 'height', 'value': '15px'}]
        :param pierce:          (optional) - Следует ли исследовать так же фреймы и shadow-DOM.
        :return:                Список узлов.
        """
        args = {"nodeId": self.nodeId, "computedStyles": computedStyles}
        if pierce: args.update({"pierce": True})
        nodes = []
        for node_id in (await self.page_instance.Call("DOM.getNodesForSubtreeByStyle", args))["nodeIds"]:
            nodes.append(Node(node_id, self.page_instance))
        return nodes

    # ==================================================================================================================

    async def GetCenter(self) -> Tuple[int, int]:
        """ Возвращает координаты центра узла """
        quad = (await self.GetContentQuads())[0]
        x = (quad[2] - quad[0]) // 2 + quad[0]
        y = (quad[7] - quad[1]) // 2 + quad[1]
        return (x, y)

    async def GetRect(self) -> Dict[str, int]:
        """ Возвращает словарь свойств, описывающих пространственное положение узла """
        q = (await self.GetContentQuads())[0]
        return {"x": q[0], "y": q[1], "w": q[2] - q[0], "h": q[7] - q[1], "l": q[0], "r": q[2], "t": q[1], "b": q[7]}

    async def Click(self) -> None:
        """ Кликает в середину себя """
        (x, y) = await self.GetCenter()
        await self.page_instance.action.MouseMoveTo(x, y)
        await self.page_instance.action.ClickTo(x, y)
