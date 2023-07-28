"""
    Набор готового JS-функционала.
"""


# Конвертирует секунды в строку вида:
#   parse_sec(1) => 00:00:01
# Игнорирует дни при переполнении ёмкости:
#   parse_sec(86_401) => 00:00:01
PARSE_SEC = """
function parse_sec(sec) {
    return new Date(Math.abs(sec) * 1000).toISOString().substr(11, 8);
}"""

# Конвертирует секунды в строку. Отображает знак:
#   parse_sec(-1) => -00:00:01
# Игнорирует дни при переполнении ёмкости:
#   parse_sec(-86_401) => -00:00:01
PARSE_SEC_SIGN = """
function parse_sec_sign(sec) {
    return (sec < 0 ? "-" : "") + new Date(Math.abs(sec) * 1000).toISOString().substr(11, 8);
}"""

# Отображает дни при переполнении ёмкости, или days === true:
#   parse_sec_days(86_401) => 01д 00:00:01
#   parse_sec_days(6_401) => 01:46:41
PARSE_SEC_DAYS = """
function parse_sec_days(sec, days=false) {
    const d = (new Date(Math.abs(sec) * 1000) - new Date(0)) /864e5|0;
    const p = new Date(Math.abs(sec) * 1000).toISOString().substr(11, 8);
    return (d || days ? String(d).padStart(2,"0") + "д " : "") + p;
}"""

# Отображает дни при переполнении ёмкости, или days === true. Отображает знак:
#   parse_sec_days(-86_401) => -01д 00:00:01
#   parse_sec_days(-6_401) => -01:46:41
PARSE_SEC_DAYS_SIGN = """
function parse_sec_days_sign(sec, days=false) {
    const d = (new Date(Math.abs(sec) * 1000) - new Date(0)) /864e5|0;
    const p = new Date(Math.abs(sec) * 1000).toISOString().substr(11, 8);
    return (sec < 0 ? "-" : "") + (d || days ? String(d).padStart(2,"0") + "д " : "") + p;
}"""


# Создаёт элемент <style> и заполняет его правилами, пришедшими в base64-строке
ADD_RULES_FROM_B64 = """
function add_rules_from_b64(b64_rules) {
    const style = document.createElement("style");
    style.appendChild(document.createTextNode(atob(b64_rules)));
    document.head.appendChild(style);
}"""

# Создаёт элемент <style> и заполняет его правилами, пришедшими в строке
ADD_RULES_FROM_STR = """
function add_rules(str_rules) {
    const style = document.createElement("style");
    style.appendChild(document.createTextNode(str_rules));
    document.head.appendChild(style);
}"""

# Получает самый последний styleSheet и вставляет в него правило самым последним
INJECT_RULE = """
function inject_rule(rule) {
    const sheets = document.styleSheets;
    const last_sheet = sheets.length - 1;
    const to_last_pos = sheets[last_sheet].length;
    sheets[last_sheet].insertRule(rule, to_last_pos);
}"""

# Возвращает полный CSS-путь(селектор) до переданного элемента
#   от ближайшего идентификатора, или body, если не будет встречен по пути
#   #uniq-id>:nth-child(3)>:nth-child(1)>:nth-child(1)>:nth-child(27)> ...
CSS_PATH = """
function css_path(e) {
    if(e.id)return "#"+e.id;if(e.tagName.toLowerCase()==="body")return "body";
    let n=1,s=e;while(s&&(s=s.previousElementSibling)){n+=1;}
    return cssPath(e.parentNode)+">:nth-child("+n+")";
}"""

# Создаёт textarea элемент и размещает его в body за краем вьюпорта, а
# так же объявляет функцию clip_copy() отправляющую текст в буфер обмена
CLIP_COPY = """
const CLIP_NODE = document.createElement("textarea");
CLIP_NODE.value = "";
Object.assign(CLIP_NODE.style, { position: "fixed", left: "-1000px", top: "-1000px" });
document.body.appendChild(CLIP_NODE);

function clip_copy(text) {
    CLIP_NODE.value = text;
    CLIP_NODE.select();
    document.execCommand("copy");
    CLIP_NODE.value = ""
}"""

# Динамически создаёт текстовый файл, наполняет его контентом
#   и предлагает скачать, вызывая соответствующий диалог.
DYNAMIC_CREATE_TXT_FILE = """
function dyn_file_create(content, name="file.txt") {
    const link = document.createElement("a");
    link.download = name;
    const blob = new Blob([content], {type: "text/plain;charset=utf-8;"});
    link.href = URL.createObjectURL(blob);
    link.click();
    URL.revokeObjectURL(link.href);
}"""

# Возвращает Base64 строку для переданного <img ...>
IMG_TO_B64 = """
function image_to_b64(img_node) {
    const canvas = document.createElement("canvas");
    canvas.height = img_node.naturalHeight;
    canvas.width = img_node.naturalWidth;
    canvas.getContext("2d").drawImage(img_node, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL().replace("data:image/png;base64,", "");
}"""

# Возвращает простой хэш строки
HASH_CODE = """
String.prototype.hashCode=function(){return this.split("").reduce((a,b)=>{
a=((a<<5)-a)+b.charCodeAt(0);return a&a},0);}"""

# Добавляет строкам прототип format
# "{0} is dead, but {1} is alive! {0} {2}".format(111, "ASP.NET", "tri", "chetyre")
STRING_FORMAT = r"""
String.prototype.format=function(){const a = arguments;
return this.replace(/{(\d+)}/g,function(m,n){return typeof a[n]!='undefined'?a[n]:m;});};"""

# Первую букву слова заглавной
#   "string data".capitalize() => "String data"
CAPITALIZE = r"""
String.prototype.capitalize=function(){return this.replace(/^\w/,function(c){return c.toUpperCase()})}"""

# Перемешивание для массивов
ARR_SHUFFLE = """
Array.prototype.shuffle=function(){for (let i=this.length-1;i>0;i--){
let t,j=Math.floor(Math.random()*(i+1));t=this[i];this[i]=this[j];this[j]=t;}}"""

# Возвращает Y-координату элемента на странице, или текущее
#   положение вертикального скролла, если элемент не указан.
GET_Y = """
function get_y(node=null){return pageYOffset+(node!==null ? node.getBoundingClientRect().y:0);}"""

# random
RANDINT = """
function randint(min,max){return Math.floor(min+Math.random()*(max+1-min))}"""

UNIFORM = """
function uniform(min,max){return Math.random()*(max-min)+min}"""

# function get_roots(el) - возвращает список всех shadowDOM-потомков
#   элемента, не включая их потомков.
# function in_root(root_element, selector) - возвращает найденный по
#   селектору элемент у root-элемента.
# Рекурсия in_root(), не погружается настолько, чтобы найти очень
#   глубокие элементы, поэтому её приходится запускать вручную несколько раз:
#       const settings = in_root(get_roots($("body"))[0], "settings-privacy-page");
#       const category = in_root(settings, "category-default-setting");
#       const control  = in_root(category, "#control");
#       control.click();
SHADOW_DOM = """
function get_roots(el) {
    if (!!el.shadowRoot) {
        return [el.shadowRoot];
    } const roots = [];
    [...el.children].forEach((e) => {
        roots.push(...get_roots(e));
    }); return roots;
}

function in_root(root_element, selector) {
    const el = root_element.querySelector(selector);
    if (el) { return el; }
    let find;
    for (let r of get_roots(root_element)) {
        if ((find = in_root(r, selector))) { return find; }
    }
}"""

# Возвращает булево значение описывающее, достигла ли прокрутка страницы
#   максимума высоты прокрутки, или лимита, если его значение больше нуля.
#   true - если корневой элемент === null.
IS_BOTTOM_SCROLL = """
function is_bottom_scroll(limit=10_000) {
    if (!document.documentElement) { return true; }
    const sh = window.pageYOffset + document.documentElement.clientHeight;
    if (limit <= 0) {
        return sh >= document.documentElement.scrollHeight;
    } return sh >= document.documentElement.scrollHeight || sh > limit;
}"""

# Возвращает (JSON) список из двух величин, описывающих текущую прокрутку по
#   X и Y координатам для элемента. Если элемент не передан, вычисляется
#   прокрутка вьюпорта.
HOW_SCROLL = """
function how_scroll(element=null) {
    const root = element || document.documentElement;
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    return JSON.stringify([root.scrollTop, root.scrollLeft]);
}"""

# Асинхронный слип
SLEEP = """
async function sleep(delay=1000) {await new Promise(r => setTimeout(r, delay));}"""

# Перетаскивает элемент относительно текущей позиции
DRAG_NODE = SLEEP + """
async function drag_node(node, x=0, y=0) {
    const options = {
        clientX: node.getBoundingClientRect().left,
        clientY: node.getBoundingClientRect().top,
        bubbles: true, cancelable: true
    };
    node.dispatchEvent(new MouseEvent("mousedown", options));
    await sleep(100);
    options.clientX += x; options.clientY += y;
    node.dispatchEvent(new MouseEvent("mousemove", options));
    await sleep(100);
    node.dispatchEvent(new MouseEvent("mouseup", options));
}"""


def noisify_canvas(*, r: int = 0, g: int = 0, b: int = 0, a: int = 0) -> str:
    """ Возвращает самовызываемый объект, при выполнении которого на странице,
    добавляется шум в канвас.
    https://browserleaks.com/canvas
    """
    canvas_noisify_src = """
    ((r=0, g=0, b=0, a=0) => {{
        const toBlob = HTMLCanvasElement.prototype.toBlob;
        const toDataURL = HTMLCanvasElement.prototype.toDataURL;
        const getImageData = CanvasRenderingContext2D.prototype.getImageData;
        const noisify = function (canvas, context) {{
            const shift = {{'r': r, 'g': g, 'b': b, 'a': a}};
            const width = canvas.width, height = canvas.height;
            const imageData = getImageData.apply(context, [0, 0, width, height]);
            for (let i = 0; i < height; i++) {{
                for (let j = 0; j < width; j++) {{
                    const n = ((i * (width * 4)) + (j * 4));
                    imageData.data[n + 0] = imageData.data[n + 0] + shift.r;
                    imageData.data[n + 1] = imageData.data[n + 1] + shift.g;
                    imageData.data[n + 2] = imageData.data[n + 2] + shift.b;
                    imageData.data[n + 3] = imageData.data[n + 3] + shift.a;
                }}
            }}
            context.putImageData(imageData, 0, 0);
        }}; Object.defineProperty(HTMLCanvasElement.prototype, "toBlob", {{
            "value": function () {{
                noisify(this, this.getContext("2d"));
                return toBlob.apply(this, arguments);
            }}
        }}); Object.defineProperty(HTMLCanvasElement.prototype, "toDataURL", {{
            "value": function () {{
                noisify(this, this.getContext("2d"));
                return toDataURL.apply(this, arguments);
            }}
        }});  Object.defineProperty(CanvasRenderingContext2D.prototype, "getImageData", {{
            "value": function () {{
                noisify(this.canvas, this);
                return getImageData.apply(this, arguments);
            }}
        }});
    }})({r}, {g}, {b}, {a});
    """
    return canvas_noisify_src.format(r=r, g=g, b=b, a=a)
