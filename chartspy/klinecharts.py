#!/usr/bin/env python
# coding=utf-8
import copy
import os
import re
import uuid

import pandas as pd
import simplejson

from .base import Tools, GLOBAL_ENV, Html, json_type_convert, FUNCTION_BOUNDARY_MARK

KlineCharts_JS_URL: str = "https://cdn.jsdelivr.net/npm/klinecharts@latest/dist/klinecharts.min.js"

# language=HTML
JUPYTER_ALL_TEMPLATE = """

<style>
  #{{plot.plot_id}} {
    width:{{plot.width}};
    height:{{plot.height}};
 }
</style>
<div id="{{ plot.plot_id }}"></div>
<script>
  {{plot.extra_js}}
  var data_{{ plot.plot_id }} = {{ plot.data}}
  if (typeof require !== 'undefined'){
      require.config({
        paths: {
          "klinecharts": "{{plot.js_url[:-3]}}"
        }
      });
      require(['klinecharts'], function (klinecharts) {
        var chart_{{ plot.plot_id }} = klinecharts.init("{{ plot.plot_id }}",{'candle':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}},'technicalIndicator':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}}});
        var btm_paneId_{{ plot.plot_id }} = chart_{{ plot.plot_id }}.createTechnicalIndicator('VOL', false)
        var btm1_paneId_{{ plot.plot_id }} = chart_{{ plot.plot_id }}.createTechnicalIndicator('MACD', false)
        chart_{{ plot.plot_id }}.createTechnicalIndicator('MA', false,{id:"candle_pane"})
        chart_{{ plot.plot_id }}.overrideTechnicalIndicator({name: 'MA',calcParams: [5,10,30,60,120,250]},"candle_pane")
        chart_{{ plot.plot_id }}.applyNewData(data_{{ plot.plot_id }})
      });
  }else{
    new Promise(function(resolve, reject) {
      var script = document.createElement("script");
      script.onload = resolve;
      script.onerror = reject;
      script.src = "{{plot.js_url}}";
      document.head.appendChild(script);
    }).then(() => {
       var chart_{{ plot.plot_id }} = klinecharts.init("{{ plot.plot_id }}",{'candle':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}},'technicalIndicator':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}}});
       var btm_paneId_{{ plot.plot_id }} = chart_{{ plot.plot_id }}.createTechnicalIndicator('VOL', false)
       var btm1_paneId_{{ plot.plot_id }} = chart_{{ plot.plot_id }}.createTechnicalIndicator('MACD', false)
       chart_{{ plot.plot_id }}.createTechnicalIndicator('MA', false,{id:"candle_pane"})
       chart_{{ plot.plot_id }}.overrideTechnicalIndicator({name: 'MA',calcParams: [5,10,30,60,120,250]},"candle_pane")
       chart_{{ plot.plot_id }}.applyNewData(data_{{ plot.plot_id }})
    });
  }

</script>
"""

# language=HTML
JUPYTER_NOTEBOOK_TEMPLATE = """
<script>
  require.config({
    paths: {
      "klinecharts": "{{plot.js_url[:-3]}}"
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
  {{plot.extra_js}}
  var data_{{ plot.plot_id }} = {{ plot.data}}
  require(['klinecharts'], function (klinecharts) {
    var chart_{{ plot.plot_id }} = klinecharts.init("{{ plot.plot_id }}",{'candle':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}},'technicalIndicator':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}}});
    var btm_paneId_{{ plot.plot_id }} = chart_{{ plot.plot_id }}.createTechnicalIndicator('VOL', false)
    var btm1_paneId_{{ plot.plot_id }} = chart_{{ plot.plot_id }}.createTechnicalIndicator('MACD', false)
    chart_{{ plot.plot_id }}.createTechnicalIndicator('MA', false,{id:"candle_pane"})
    chart_{{ plot.plot_id }}.overrideTechnicalIndicator({name: 'MA',calcParams: [5,10,30,60,120,250]},"candle_pane")
    chart_{{ plot.plot_id }}.applyNewData(data_{{ plot.plot_id }})
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

{{plot.extra_js}}
new Promise(function(resolve, reject) {
  var script = document.createElement("script");
  script.onload = resolve;
  script.onerror = reject;
  script.src = "{{plot.js_url}}";
  document.head.appendChild(script);
}).then(() => {
  var data_{{ plot.plot_id }} = {{ plot.data}};  
  var chart_{{ plot.plot_id }} = klinecharts.init("{{ plot.plot_id }}",{'candle':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}},'technicalIndicator':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}}});
  var btm_paneId_{{ plot.plot_id }} = chart_{{ plot.plot_id }}.createTechnicalIndicator('VOL', false)
  var btm1_paneId_{{ plot.plot_id }} = chart_{{ plot.plot_id }}.createTechnicalIndicator('MACD', false)
  chart_{{ plot.plot_id }}.createTechnicalIndicator('MA', false,{id:"candle_pane"})
  chart_{{ plot.plot_id }}.overrideTechnicalIndicator({name: 'MA',calcParams: [5,10,30,60,120,250]},"candle_pane")
  chart_{{ plot.plot_id }}.applyNewData(data_{{ plot.plot_id }})
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
   <script type="text/javascript" src="{{ plot.js_url }}"></script>
</head>
<body>
  <div id="{{ plot.plot_id }}" ></div>
  <script>
     {{plot.extra_js}}
     var data_{{ plot.plot_id }} = {{ plot.data}};  
     var chart_{{ plot.plot_id }} = klinecharts.init("{{ plot.plot_id }}",{'candle':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}},'technicalIndicator':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}}});
     var btm_paneId_{{ plot.plot_id }} = chart_{{ plot.plot_id }}.createTechnicalIndicator('VOL', false)
     var btm1_paneId_{{ plot.plot_id }} = chart_{{ plot.plot_id }}.createTechnicalIndicator('MACD', false)
     chart_{{ plot.plot_id }}.createTechnicalIndicator('MA', false,{id:"candle_pane"})
     chart_{{ plot.plot_id }}.overrideTechnicalIndicator({name: 'MA',calcParams: [5,10,30,60,120,250]},"candle_pane")
     chart_{{ plot.plot_id }}.applyNewData(data_{{ plot.plot_id }})
     
  </script>
</body>
</html>
"""

# language=HTML
HTML_FRAGMENT_TEMPLATE = """
<div>
 <script type="text/javascript" src="{{ plot.js_url }}"></script>
 <style>
      #{{plot.plot_id}} {
            width:{{plot.width}};
            height:{{plot.height}};
         }
 </style>
 <div id="{{ plot.plot_id }}" ></div>
  <script>
    {{plot.extra_js}}
     var data_{{ plot.plot_id }} = {{ plot.data}};  
     var chart_{{ plot.plot_id }} = klinecharts.init("{{ plot.plot_id }}",{'candle':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}},'technicalIndicator':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}}});
     chart_{{ plot.plot_id }}.createTechnicalIndicator('MA', false,{id:"candle_pane"})
     chart_{{ plot.plot_id }}.overrideTechnicalIndicator({name: 'MA',calcParams: [5,10,30,60,120,250]},"candle_pane")
     var btm_paneId_{{ plot.plot_id }} = chart_{{ plot.plot_id }}.createTechnicalIndicator('VOL', false)
     var btm1_paneId_{{ plot.plot_id }} = chart_{{ plot.plot_id }}.createTechnicalIndicator('MACD', false)
     chart_{{ plot.plot_id }}.applyNewData(data_{{ plot.plot_id }})
  </script>
</div>
"""


class KlineCharts(object):
    """
    g2plot
    """

    def __init__(self, df: pd.DataFrame, options: dict = {}, extra_js: str = "", width: str = "100%",
                 height: str = "500px"):
        """
        :param options: python词典类型的echarts option
        :param df:[open,high,low,close,volume,turnover,timestamp]
        :param extra_js: 复杂图表需要声明定义额外js函数的，通过这个字段传递
        :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
        :param height: 输出div的高度 支持像素和百分比 比如800px/100%
        """
        data = df.copy()
        data['timestamp'] = (pd.to_datetime(data['timestamp']) - pd.Timedelta(hours=8)).astype("i8") // 10 ** 6
        data = data.sort_values(by=['timestamp'])
        self.data = Tools.convert_dict_to_js(data.to_dict(orient='records'))
        self.options = options
        self.js_options = ""
        self.width = width
        self.height = height
        self.plot_id = "u" + uuid.uuid4().hex
        self.js_url = KlineCharts_JS_URL
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
