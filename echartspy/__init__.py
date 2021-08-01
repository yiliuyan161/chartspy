#!/usr/bin/env python
# coding=utf-8
import datetime
import os
import re
import uuid
from typing import Optional

import numpy as np
import pandas as pd
import simplejson
from jinja2 import Environment, BaseLoader

# jinja2模板引擎env
GLOBAL_ENV = Environment(loader=BaseLoader)

# 引用的echarts js文件路径
ECHARTS_JS_URL = "https://unpkg.com/echarts@5.1.2/dist/echarts.min.js"

# language=HTML
JUPYTER_NOTEBOOK_TEMPLATE = """
<script>
  require.config({
    paths: {
      "echarts": "{{plot.js_url[:-3]}}"
    }
  });
</script>
<style>
  #{{plot.plot_id}} {
    width:{{plot.width}};
    height:{{plot.height}};
 }
</style>
<div id="{{ plot.plot_id }}"></div>
<script>
  require(['echarts'], function (echarts) {
    var plot_{{ plot.plot_id }} = echarts.init(document.getElementById('{{ plot.plot_id }}'));
    {{plot.extra_js}}
    plot_{{ plot.plot_id }}.setOption({{ plot.js_options }})
  });
</script>
"""

# language=HTML
JUPYTER_LAB_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title></title>
  <style>
 #{{plot.plot_id}} {
    width:{{plot.width}};
    height:{{plot.height}};
 }
</style>
</head>
<body>
  <div id="{{ plot.plot_id }}"></div>
  <script>
    // load javascript
    new Promise(function(resolve, reject) {
      var script = document.createElement("script");
      script.onload = resolve;
      script.onerror = reject;
      script.src = "{{plot.js_url}}";
      document.head.appendChild(script);
    }).then(() => {
       var plot_{{ plot.plot_id }} = echarts.init(document.getElementById('{{ plot.plot_id }}'));
       {{plot.extra_js}}
       plot_{{ plot.plot_id }}.setOption({{ plot.js_options }})
    });
  </script>
</body>
</html>
"""

# language=HTML
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title></title>
    <style>
      #{{plot.plot_id}} {
            width:{{plot.width}};
            height:{{plot.height}};
         }
    </style>
   <script type="text/javascript" src="{{ plot.js_url }}"></script>
</head>
<body>
  <div id="{{ plot.plot_id }}" ></div>
  <script>
    var plot_{{ plot.plot_id }} = echarts.init(document.getElementById('{{ plot.plot_id }}'));
    {{plot.extra_js}}
    plot_{{ plot.plot_id }}.setOption({{ plot.js_options }})
  </script>
</body>
</html>
"""


class Js:
    """
    JavaScript代码因为不是标准json,先以特殊字符包裹字符串形式保存
    dump成标准json字符串后，再用正则根据特殊字符，恢复成JavaScript函数
    """

    def __init__(self, js_code: str):
        js_code = re.sub("\\n|\\t", "", js_code)
        js_code = re.sub(r"\\n", "\n", js_code)
        js_code = re.sub(r"\\t", "\t", js_code)
        self.js_code = "ECHARTS_BOUNDARY_MARK" + js_code + "ECHARTS_BOUNDARY_MARK"


class Html:
    """
    在 jupyter notebook 或者 jupyterlab 中输出html内容需要用此对象包裹
    """

    def __init__(self, data: Optional[str] = None):
        self.data = data

    def _repr_html_(self):
        return self.data

    def __html__(self):
        return self._repr_html_()


def wrap_template(js_options_template: str, **kwargs):
    """
    组装模板和数据生成配置字符串，模板可以从echarts例子修改而来，使用jinja2模板引擎
    :param js_options_template:
    :param kwargs:
    :return:
    """
    return GLOBAL_ENV.from_string(js_options_template).render(**kwargs)


def js_str(data: object) -> str:
    """
    转换python数据变成JavaScript对应数据的字符串形式
    :param data: python数据
    :return: str 类型option
    """
    if isinstance(data, pd.DataFrame):
        data = data.values.tolist()
    elif isinstance(data, pd.Series):
        data = data.tolist()
    elif isinstance(data, np.ndarray):
        # 只有一列的datetime64[ns] tolist会变成long型，需要特殊处理
        if data.dtype == np.dtype("datetime64[ns]") and len(data.shape) == 1:
            data = [pd.to_datetime(item) for item in data]
        data = data.tolist()
    return re.sub('"?ECHARTS_BOUNDARY_MARK"?', "",
                  simplejson.dumps(data, indent=2, default=_type_convert, ignore_nan=True))


def _type_convert(o: object):
    """
    python 类型转换成js类型
    :param o:
    :return:
    """
    if isinstance(o, datetime.datetime):
        if o.hour + o.minute + o.second == 0:
            return o.strftime("%Y-%m-%d")
        else:
            return o.isoformat()
    elif isinstance(o, datetime.date):
        return o.isoformat()
    elif isinstance(o, Js):
        return o.js_code
    else:
        return o


class Echarts(object):
    """
    echarts
    """

    def __init__(self, options: dict = None, js_options: str = None, extra_js: str = "", width: str = "100%",
                 height: str = "500px"):
        """
        :param options: python词典类型的echarts option
        :param js_options: 转换后的字符串形式的 echarts option
        :param extra_js: 复杂图表需要声明定义额外js函数的，通过这个字段传递
        :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
        :param height: 输出div的高度 支持像素和百分比 比如800px/100%
        """
        self.options = options
        self.js_options = js_options
        self.width = width
        self.height = height
        self.plot_id = uuid.uuid4().hex
        self.js_url = ECHARTS_JS_URL
        self.extra_js = extra_js

    def dump_options(self):
        """
         导出 js option字符串表示
        :return:
        """
        self._ensure_js_options()
        return self.js_options

    def render_notebook(self) -> Html:
        """
        在jupyter notebook 环境输出
        :return:
        """
        self._ensure_js_options()
        html = GLOBAL_ENV.from_string(JUPYTER_NOTEBOOK_TEMPLATE).render(plot=self)
        return Html(html)

    def render_jupyterlab(self) -> Html:
        """
        在jupyterlab 环境输出
        :return:
        """
        self._ensure_js_options()
        html = GLOBAL_ENV.from_string(JUPYTER_LAB_TEMPLATE).render(plot=self)
        return Html(html)

    def render_file(self, path: str = "plot.html") -> str:
        """
        输出html到文件
        :param path:
        :return: 文件路径
        """
        self._ensure_js_options()
        html = GLOBAL_ENV.from_string(HTML_TEMPLATE).render(plot=self)
        with open(path, "w+", encoding="utf-8") as html_file:
            html_file.write(html)
        abs_path = os.path.abspath(path)
        return Html("<p>{path}</p>".format(path=abs_path))

    def _ensure_js_options(self):
        if self.js_options is None:
            self.js_options = js_str(self.options)

    def render_html(self) -> str:
        """
        渲染html字符串，可以用于 streamlit
        :return:
        """
        self._ensure_js_options()
        html = GLOBAL_ENV.from_string(HTML_TEMPLATE).render(plot=self)
        return html


__all__ = ["Echarts", "Js", "Html", "ECHARTS_JS_URL", 'js_str', 'wrap_template']
