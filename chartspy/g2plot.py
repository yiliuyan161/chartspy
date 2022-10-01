#!/usr/bin/env python
# coding=utf-8
import copy
import uuid

import pandas as pd

from .base import Tools, Html

G2PLOT_JS_URL: str = "https://cdn.staticfile.org/g2plot/2.4.16/g2plot.min.js"


# language=HTML


class G2PLOT(object):
    """
    g2plot
    """

    def __init__(self, data=None, plot_type: str = None, options: dict = {}, extra_js: str = "", width: str = "100%",
                 height: str = "500px"):
        """
        :param options: python词典类型的echarts option
        :param extra_js: 复杂图表需要声明定义额外js函数的，通过这个字段传递
        :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
        :param height: 输出div的高度 支持像素和百分比 比如800px/100%
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
        plot = self
        html = f"""
        <script>
            require.config({{
                paths: {{
                  "G2Plot": "{plot.js_url[:-3]}"
                }}
            }});
        </script>
        <style>
          #{plot.plot_id} {{
            width:{{plot.width}};
            height:{{plot.height}};
         }}
        </style>
        <div id="{plot.plot_id}"></div>
        <script>
          {{plot.extra_js}}
          require(['G2Plot'], function (G2Plot) {{
            var plot_{plot.plot_id} = new G2Plot.{plot.plot_type}("{plot.plot_id}", {plot.js_options}) 
            plot_{plot.plot_id}.render();
          }});
        </script>
        """

        return Html(html)

    def render_jupyterlab(self) -> Html:
        """
        在jupyterlab 环境输出
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        plot = self
        html = f"""
            <style>
             #{plot.plot_id} {{
                width:{plot.width};
                height:{plot.height};
             }}
            </style>
            <div id="{plot.plot_id}"></div>
            <script>
            // load javascript
            
            {plot.extra_js}
            new Promise(function(resolve, reject) {{
              var script = document.createElement("script");
              script.onload = resolve;
              script.onerror = reject;
              script.src = "{plot.js_url}";
              document.head.appendChild(script);
            }}).then(() => {{
              var plot_{plot.plot_id} = new G2Plot.{plot.plot_type}("{plot.plot_id}", {plot.js_options}) 
              plot_{plot.plot_id}.render();
            }});
            </script>
            """
        return Html(html)

    def render_html(self) -> str:
        """
        渲染html字符串，可以用于 streamlit
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        plot = self
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <title></title>
            <style>
              #{plot.plot_id} {{
                    width:{plot.width};
                    height:{plot.height};
                 }}
            </style>
           <script type="text/javascript" src="{plot.js_url}"></script>
        </head>
        <body>
          <div id="{plot.plot_id}" ></div>
          <script>
             {plot.extra_js}
             var plot_{plot.plot_id} = new G2Plot.{plot.plot_type}("{plot.plot_id}", {plot.js_options}) 
             plot_{plot.plot_id}.render();
          </script>
        </body>
        </html>
        """
        return html

    def render_html_fragment(self):
        """
        渲染html 片段，方便一个网页输出多个图表
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        plot = self
        html = f"""
        <div>
         <script type="text/javascript" src="{plot.js_url}"></script>
         <style>
              #{plot.plot_id} {{
                    width:{plot.width};
                    height:{plot.height};
                 }}
         </style>
         <div id="{plot.plot_id}" ></div>
          <script>
            {plot.extra_js}
            var plot_{plot.plot_id} = new G2Plot.{plot.plot_type}("{plot.plot_id}", {plot.js_options}) 
            plot_{plot.plot_id}.render();
          </script>
        </div>
        """
        return html

    def _repr_html_(self):
        """
        jupyter 环境，直接输出
        :return:
        """
        self.js_options = Tools.convert_dict_to_js(self.options)
        plot = self
        html = f"""
        <style>
          #{plot.plot_id} {{
            width:{plot.width};
            height:{plot.height};
         }}
        </style>
        <div id="{plot.plot_id}"></div>
        <script>
          {plot.extra_js}
          var options_{plot.plot_id} = {plot.js_options}
          if (typeof require !== 'undefined'){{
              require.config({{
                paths: {{
                  "G2Plot": "{plot.js_url[:-3]}"
                }}
              }});
              require(['G2Plot'], function (G2Plot) {{
                var plot_{plot.plot_id} = new G2Plot.{plot.plot_type}("{plot.plot_id}", options_{plot.plot_id}); 
                plot_{plot.plot_id}.render();
              }});
          }}else{{
            new Promise(function(resolve, reject) {{
              var script = document.createElement("script");
              script.onload = resolve;
              script.onerror = reject;
              script.src = "{plot.js_url}";
              document.head.appendChild(script);
            }}).then(() => {{
               var plot_{plot.plot_id} = new G2Plot.{plot.plot_type}("{plot.plot_id}", options_{plot.plot_id}); 
               plot_{plot.plot_id}.render();
            }});
          }}
        </script>
        """
        return Html(html).data
