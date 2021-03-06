#!/usr/bin/env python
# coding=utf-8
import copy
import os
import uuid

from .base import Tools, GLOBAL_ENV, Html

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
        :param options: python???????????????echarts option
        :param extra_js: ????????????????????????????????????js????????????????????????????????????
        :param width: ??????div????????? ???????????????????????? ??????800px/100%
        :param height: ??????div????????? ???????????????????????? ??????800px/100%
        """
        self.options = options
        self.js_options = ""
        self.width = width
        self.height = height
        self.plot_id = "u" + uuid.uuid4().hex
        self.extra_js = extra_js

    def print_options(self, drop_data=False):
        """
        ???????????????options ??????????????????
        :param drop_data: ???????????????data????????????????????????????????????
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
         ?????? js option???????????????
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        return self.js_options

    def render_notebook(self) -> Html:
        """
        ???jupyter notebook ????????????
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        html = GLOBAL_ENV.from_string(JUPYTER_NOTEBOOK_TEMPLATE).render(plot=self)
        return Html(html)

    def render_jupyterlab(self) -> Html:
        """
        ???jupyterlab ????????????
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        html = GLOBAL_ENV.from_string(JUPYTER_LAB_TEMPLATE).render(plot=self)
        return Html(html)

    def render_file(self, path: str = "plot.html") -> Html:
        """
        ??????html?????????
        :param path:
        :return: ????????????
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        html = GLOBAL_ENV.from_string(HTML_TEMPLATE).render(plot=self)
        with open(path, "w+", encoding="utf-8") as html_file:
            html_file.write(html)
        abs_path = os.path.abspath(path)
        return Html("<p>{path}</p>".format(path=abs_path))

    def render_html(self) -> str:
        """
        ??????html???????????????????????? streamlit
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        html = GLOBAL_ENV.from_string(HTML_TEMPLATE).render(plot=self)
        return html

    def render_html_fragment(self):
        """
        ??????html ?????????????????????????????????????????????
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        html = GLOBAL_ENV.from_string(HTML_FRAGMENT_TEMPLATE).render(plot=self)
        return html

    def _repr_html_(self):
        """
        jupyter ?????????????????????
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        html = GLOBAL_ENV.from_string(JUPYTER_ALL_TEMPLATE).render(plot=self)
        return Html(html).data
