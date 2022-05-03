#!/usr/bin/env python
# coding=utf-8
import copy
import os
import re
import uuid

import simplejson

from .base import Tools, GLOBAL_ENV, Html, json_type_convert, FUNCTION_BOUNDARY_MARK

# language=HTML
JUPYTER_ALL_TEMPLATE = """
<script>

</script>
<style>
  #{{plot.plot_id}} {
    width:{{plot.width}};
    height:{{plot.height}};
 }
</style>
<div id="{{ plot.plot_id }}"></div>
<script >
  {{plot.extra_js}}
  var options_{{ plot.plot_id }} = {{ plot.js_options }};
</script>
<script>
  if (typeof require !== 'undefined'){
      require.config({
            packages: [{
                name: 'highcharts',
                main: 'highcharts'
            }],
            paths: {
                'highcharts': 'https://code.highcharts.com'
            }
       });
      require(['highcharts','highcharts/modules/streamgraph','highcharts/modules/arc-diagram','highcharts/modules/sankey','highcharts/modules/dependency-wheel'], function (Highcharts) {
        Highcharts.chart('{{ plot.plot_id }}',options_{{ plot.plot_id }})
      });


  }else{
    new Promise(function(resolve, reject) {
         var script = document.createElement("script");
      script.onload = resolve;
      script.onerror = reject;
      script.src = "https://code.highcharts.com/highcharts.js";
      document.head.appendChild(script);
      var scriptSG = document.createElement("script");
          scriptSG.onload = resolve;
          scriptSG.onerror = reject;
          scriptSG.src = "https://code.highcharts.com/modules/streamgraph.js";
          document.head.appendChild(scriptSG);
      var wheel = document.createElement("script");
          scriptSG.onload = resolve;
          scriptSG.onerror = reject;
          scriptSG.src = "https://code.highcharts.com/modules/dependency-wheel.js";
          document.head.appendChild(wheel);
      var sankey = document.createElement("script");
          scriptSG.onload = resolve;
          scriptSG.onerror = reject;
          scriptSG.src = "https://code.highcharts.com/modules/sankey.js";
          document.head.appendChild(sankey);
      var arc_diagram = document.createElement("script");
          scriptSG.onload = resolve;
          scriptSG.onerror = reject;
          scriptSG.src = "https://code.highcharts.com/modules/arc-diagram.js";
          document.head.appendChild(arc_diagram);
    
    }).then(() => {
        {{plot.extra_js}}
       Highcharts.chart('{{ plot.plot_id }}',options_{{ plot.plot_id }})
    });
  }

</script>
"""

# language=HTML
JUPYTER_NOTEBOOK_TEMPLATE = """

<style>
  #{{plot.plot_id}} {
    width:{{plot.width}};
    height:{{plot.height}};
 }
</style>
<div id="{{ plot.plot_id }}"></div>
<script>
    require.config({
            packages: [{
                name: 'highcharts',
                main: 'highcharts'
            }],
            paths: {
                'highcharts': 'https://code.highcharts.com'
            }
       });
      require(['highcharts','highcharts/modules/streamgraph','highcharts/modules/arc-diagram','highcharts/modules/sankey','highcharts/modules/dependency-wheel'], function (Highcharts) {
        {{plot.extra_js}}
        var options_{{ plot.plot_id }} = {{ plot.js_options }};
        Highcharts.chart('{{ plot.plot_id }}',options_{{ plot.plot_id }})
      });
</script>
"""

# language=HTML
JUPYTER_LAB_TEMPLATE = """
<style>
 #{{plot.plot_id}} {
    width:{{plot.width}};
    height:{{plot.height}};
 }
</style>
<div id="{{ plot.plot_id }}"></div>
  <script>
    // load javascript
    new Promise(function(resolve, reject) {
      var script = document.createElement("script");
      script.onload = resolve;
      script.onerror = reject;
      script.src = "https://code.highcharts.com/highcharts.js";
      document.head.appendChild(script);
      var scriptSG = document.createElement("script");
          scriptSG.onload = resolve;
          scriptSG.onerror = reject;
          scriptSG.src = "https://code.highcharts.com/modules/streamgraph.js";
          document.head.appendChild(scriptSG);
      var wheel = document.createElement("script");
          scriptSG.onload = resolve;
          scriptSG.onerror = reject;
          scriptSG.src = "https://code.highcharts.com/modules/dependency-wheel.js";
          document.head.appendChild(wheel);
      var sankey = document.createElement("script");
          scriptSG.onload = resolve;
          scriptSG.onerror = reject;
          scriptSG.src = "https://code.highcharts.com/modules/sankey.js";
          document.head.appendChild(sankey);
      var arc_diagram = document.createElement("script");
          scriptSG.onload = resolve;
          scriptSG.onerror = reject;
          scriptSG.src = "https://code.highcharts.com/modules/arc-diagram.js";
          document.head.appendChild(arc_diagram);
    }).then(() => {
       {{plot.extra_js}}
       var options_{{ plot.plot_id }} = {{ plot.js_options }};
       Highcharts.chart('{{ plot.plot_id }}',options_{{ plot.plot_id }})
    });
  </script>
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
<script src="https://code.highcharts.com/highcharts.js"></script>
<script src="https://code.highcharts.com/modules/streamgraph.js"></script>
<script src="https://code.highcharts.com/modules/dependency-wheel.js"></script>
 <script src="https://code.highcharts.com/modules/arc-diagram.js"></script>
 <script src="https://code.highcharts.com/modules/sankey.js"></script>
</head>
<body>
  <div id="{{ plot.plot_id }}" ></div>
  <script>
    {{plot.extra_js}}
    var options_{{ plot.plot_id }} = {{ plot.js_options }};
    Highcharts.chart('{{ plot.plot_id }}',options_{{ plot.plot_id }})
  </script>
</body>
</html>
"""

# language=HTML
HTML_FRAGMENT_TEMPLATE = """
<div>
<script src="https://code.highcharts.com/highcharts.js"></script>
<script src="https://code.highcharts.com/modules/streamgraph.js"></script>
<script src="https://code.highcharts.com/modules/dependency-wheel.js"></script>
 <script src="https://code.highcharts.com/modules/arc-diagram.js"></script>
 <script src="https://code.highcharts.com/modules/sankey.js"></script>
 <style>
      #{{plot.plot_id}} {
            width:{{plot.width}};
            height:{{plot.height}};
         }
 </style>
 <div id="{{ plot.plot_id }}" ></div>
  <script>
    {{plot.extra_js}}
    var options_{{ plot.plot_id }} = {{ plot.js_options }};
    Highcharts.chart('{{ plot.plot_id }}',options_{{ plot.plot_id }})
  </script>
</div>
"""


class HighCharts(object):
    """
    echarts
    """

    def __init__(self, options: dict = None, extra_js: str = "", width: str = "100%",
                 height: str = "500px"):
        """
        :param options: python词典类型的echarts option
        :param extra_js: 复杂图表需要声明定义额外js函数的，通过这个字段传递
        :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
        :param height: 输出div的高度 支持像素和百分比 比如800px/100%
        """
        self.options = options
        self.js_options = ""
        self.width = width
        self.height = height
        self.plot_id = "u" + uuid.uuid4().hex
        self.extra_js = extra_js

    def print_options(self, drop_data=False):
        """
        格式化打印options 方便二次修改
        :param drop_data: 是否过滤掉data，减小打印长度，方便粘贴
        :return:
        """
        dict_options = copy.deepcopy(self.options)
        if drop_data:
            series_count = len(dict_options['series'])
            for i in range(0, series_count):
                dict_options['series'][i]['data'] = []
        Tools.convert_js_to_dict(Tools.convert_dict_to_js(dict_options), print_dict=True)

    def dump_options(self):
        """
         导出 js option字符串表示
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        return self.js_options

    def render_notebook(self) -> Html:
        """
        在jupyter notebook 环境输出
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        html = GLOBAL_ENV.from_string(JUPYTER_NOTEBOOK_TEMPLATE).render(plot=self)
        return Html(html)

    def render_jupyterlab(self) -> Html:
        """
        在jupyterlab 环境输出
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        html = GLOBAL_ENV.from_string(JUPYTER_LAB_TEMPLATE).render(plot=self)
        return Html(html)

    def render_file(self, path: str = "plot.html") -> Html:
        """
        输出html到文件
        :param path:
        :return: 文件路径
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        html = GLOBAL_ENV.from_string(HTML_TEMPLATE).render(plot=self)
        with open(path, "w+", encoding="utf-8") as html_file:
            html_file.write(html)
        abs_path = os.path.abspath(path)
        return Html("<p>{path}</p>".format(path=abs_path))

    def render_html(self) -> str:
        """
        渲染html字符串，可以用于 streamlit
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        html = GLOBAL_ENV.from_string(HTML_TEMPLATE).render(plot=self)
        return html

    def render_html_fragment(self):
        """
        渲染html 片段，方便一个网页输出多个图表
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        html = GLOBAL_ENV.from_string(HTML_FRAGMENT_TEMPLATE).render(plot=self)
        return html

    def _repr_html_(self):
        """
        jupyter 环境，直接输出
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        html = GLOBAL_ENV.from_string(JUPYTER_ALL_TEMPLATE).render(plot=self)
        return Html(html).data
