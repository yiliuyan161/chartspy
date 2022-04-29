#!/usr/bin/env python
# coding=utf-8
import copy
import os
import re
import uuid

import pandas as pd
import simplejson

from .base import Tools, GLOBAL_ENV, Html, json_type_convert

KlineCharts_JS_URL: str = "https://cdn.jsdelivr.net/npm/klinecharts@latest/dist/klinecharts.min.js"
# language=jinja2
SEGMENT = """
        var chart_{{ plot.plot_id }} = klinecharts.init("{{ plot.plot_id }}",{grid: { show: true, horizontal: { show: true, size: 2, color: '#CFCFCF', style: 'dash'}, vertical: { show: true, size: 2, color: '#CFCFCF',  style: 'dash'} },'candle':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}},'technicalIndicator':{'bar':{'upColor':'#EF5350','downColor':'#26A69A'}}});
        {% for bt in plot.bottom_indicators %}
           var btm_{{bt}}_{{ plot.plot_id }} = chart_{{ plot.plot_id }}.createTechnicalIndicator('{{bt}}', false)
        {% endfor %}
        {% for mi in plot.main_indicators %}
          chart_{{ plot.plot_id }}.createTechnicalIndicator('{{mi}}', true,{id:"candle_pane"})
        {% endfor %}
        {% if plot.mas|length>0 %}
            chart_{{ plot.plot_id }}.overrideTechnicalIndicator({name: 'MA',calcParams: {{plot.mas|string}}},"candle_pane")
        {% endif %}
        chart_{{ plot.plot_id }}.applyNewData(data_{{ plot.plot_id }})
"""

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
        """ + SEGMENT + """
     });
     }else{
       new Promise(function(resolve, reject) {
         var script = document.createElement("script");
         script.onload = resolve;
         script.onerror = reject;
         script.src = "{{plot.js_url}}";
         document.head.appendChild(script);
       }).then(() => {
         """ + SEGMENT + """
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
    """ + SEGMENT + """
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
  """ + SEGMENT + """
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
""" + SEGMENT + """
     
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
""" + SEGMENT + """
  </script>
</div>
"""


class KlineCharts(object):
    """
    g2plot
    """

    def __init__(self, df: pd.DataFrame, mas=[5, 10, 30, 60, 120, 250], main_indicators=["MA"],
                 bottom_indicators=["VOL", "MACD"],
                 extra_js: str = "", width: str = "100%",
                 height: str = "500px"):
        """
        k线图
        :param df: [open,high,low,close,volume,turnover,timestamp]
        :param mas: [5, 10, 30, 60, 120, 250]
        :param main_indicators: 主图显示的指标列表 MA,EMA,SMA,BOLL,SAR,BBI
        :param bottom_indicators:副图显示指标列表 VOL,MACD,KDJ,RSI,BIAS,BBAR,CCI,DMI,CR,PSY,DMA,TRIX,OBV,VR,WR,MTM,EMV,SAR,SMA,ROC,PVT,BBI,AO
        :param extra_js:
        :param width:
        :param height:
        """
        data = df.copy()
        data['timestamp'] = (pd.to_datetime(data['timestamp']) - pd.Timedelta(hours=8)).view("i8") // 10 ** 6
        data = data.sort_values(by=['timestamp'])
        if len(mas) > 0 and "MA" not in main_indicators:
            main_indicators.append("MA")
        self.data = Tools.convert_dict_to_js(data.to_dict(orient='records'))
        self.mas = mas
        self.main_indicators = main_indicators
        self.bottom_indicators = bottom_indicators
        self.width = width
        self.height = height
        self.plot_id = "u" + uuid.uuid4().hex
        self.js_url = KlineCharts_JS_URL
        self.extra_js = extra_js

    def render_notebook(self) -> Html:
        """
        在jupyter notebook 环境输出
        :return:
        """
        html = GLOBAL_ENV.from_string(JUPYTER_NOTEBOOK_TEMPLATE).render(plot=self)
        return Html(html)

    def render_jupyterlab(self) -> Html:
        """
        在jupyterlab 环境输出
        :return:
        """
        html = GLOBAL_ENV.from_string(JUPYTER_LAB_TEMPLATE).render(plot=self)
        return Html(html)

    def render_file(self, path: str = "plot.html") -> Html:
        """
        输出html到文件
        :param path:
        :return: 文件路径
        """
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
        html = GLOBAL_ENV.from_string(HTML_TEMPLATE).render(plot=self)
        return html

    def render_html_fragment(self):
        """
        渲染html 片段，方便一个网页输出多个图表
        :return:
        """
        html = GLOBAL_ENV.from_string(HTML_FRAGMENT_TEMPLATE).render(plot=self)
        return html

    def _repr_html_(self):
        """
        jupyter 环境，直接输出
        :return:
        """
        html = GLOBAL_ENV.from_string(JUPYTER_ALL_TEMPLATE).render(plot=self)
        return Html(html).data
