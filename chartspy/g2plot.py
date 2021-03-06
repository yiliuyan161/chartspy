#!/usr/bin/env python
# coding=utf-8
import copy
import os
import uuid

import pandas as pd

from .base import Tools, GLOBAL_ENV, Html

G2PLOT_JS_URL: str = "https://cdn.staticfile.org/g2plot/2.4.16/g2plot.min.js"

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
  var options_{{ plot.plot_id }} = {{ plot.js_options }}
  if (typeof require !== 'undefined'){
      require.config({
        paths: {
          "G2Plot": "{{plot.js_url[:-3]}}"
        }
      });
      require(['G2Plot'], function (G2Plot) {
        var plot_{{ plot.plot_id }} = new G2Plot.{{plot.plot_type}}("{{ plot.plot_id }}", options_{{ plot.plot_id }}); 
        plot_{{ plot.plot_id }}.render();
      });
  }else{
    new Promise(function(resolve, reject) {
      var script = document.createElement("script");
      script.onload = resolve;
      script.onerror = reject;
      script.src = "{{plot.js_url}}";
      document.head.appendChild(script);
    }).then(() => {
       var plot_{{ plot.plot_id }} = new G2Plot.{{plot.plot_type}}("{{ plot.plot_id }}", options_{{ plot.plot_id }}); 
       plot_{{ plot.plot_id }}.render();
    });
  }

</script>
"""

# language=HTML
JUPYTER_NOTEBOOK_TEMPLATE = """
<script>
  require.config({
    paths: {
      "G2Plot": "{{plot.js_url[:-3]}}"
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
  require(['G2Plot'], function (G2Plot) {
    var plot_{{ plot.plot_id }} = new G2Plot.{{plot.plot_type}}("{{ plot.plot_id }}", {{ plot.js_options }}) 
    plot_{{ plot.plot_id }}.render();
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
  var plot_{{ plot.plot_id }} = new G2Plot.{{plot.plot_type}}("{{ plot.plot_id }}", {{ plot.js_options }}) 
  plot_{{ plot.plot_id }}.render();
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
     var plot_{{ plot.plot_id }} = new G2Plot.{{plot.plot_type}}("{{ plot.plot_id }}", {{ plot.js_options }}) 
     plot_{{ plot.plot_id }}.render();
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
    var plot_{{ plot.plot_id }} = new G2Plot.{{plot.plot_type}}("{{ plot.plot_id }}", {{ plot.js_options }}) 
    plot_{{ plot.plot_id }}.render();
  </script>
</div>
"""


class G2PLOT(object):
    """
    g2plot
    """

    def __init__(self, data=None, plot_type: str = None, options: dict = {}, extra_js: str = "", width: str = "100%",
                 height: str = "500px"):
        """
        :param options: python???????????????echarts option
        :param extra_js: ????????????????????????????????????js????????????????????????????????????
        :param width: ??????div????????? ???????????????????????? ??????800px/100%
        :param height: ??????div????????? ???????????????????????? ??????800px/100%
        """
        if isinstance(data, pd.DataFrame):
            data = data.reset_index().to_dict(orient='records')
        self.options = options
        self.options['data'] = data
        self.plot_type = plot_type
        self.js_options = ""
        self.width = width
        self.height = height
        self.plot_id = "u" + uuid.uuid4().hex
        self.js_url = G2PLOT_JS_URL
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
