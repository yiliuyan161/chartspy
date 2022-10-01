#!/usr/bin/env python
# coding=utf-8
import uuid

import pandas as pd

from .base import Tools, Html, Js


def tabulator_segment(plot):
    return f"""
        var lineFormatter = function(cell, formatterParams, onRendered){{
            onRendered(function(){{ 
                $(cell.getElement()).sparkline(cell.getValue(), {{width:"100%", type:"line"}});
            }});
        }};
        
        var barFormatter = function(cell, formatterParams, onRendered){{
            onRendered(function(){{ 
                $(cell.getElement()).sparkline(cell.getValue(), {{width:"100%", type:"bar"}});
            }});
        }};
        
        var tristateFormatter = function(cell, formatterParams, onRendered){{
            onRendered(function(){{ 
                $(cell.getElement()).sparkline(cell.getValue(), {{width:"100%", type:"tristate"}});
            }});
        }};
        
        var boxFormatter = function(cell, formatterParams, onRendered){{
            onRendered(function(){{
                $(cell.getElement()).sparkline(cell.getValue(), {{width:"100%", type:"box"}});
            }});
        }};
        var pieFormatter = function(cell, formatterParams, onRendered){{
            onRendered(function(){{
                $(cell.getElement()).sparkline(cell.getValue(), {{width:"100%", type:"pie"}});
            }});
        }};
        var bulletFormatter = function(cell, formatterParams, onRendered){{
            onRendered(function(){{
                $(cell.getElement()).sparkline(cell.getValue(), {{width:"100%", type:"bullet"}});
            }});
        }};
        var discreteFormatter = function(cell, formatterParams, onRendered){{
            onRendered(function(){{
                $(cell.getElement()).sparkline(cell.getValue(), {{width:"100%", type:"discrete"}});
            }});
        }};
        var tabledata = {plot.tabledata};
        var table = new Tabulator("#{plot.plot_id}", {{
            height:{plot.height},
            data:tabledata,
            layout:"fitColumns",
            columns:{plot.columns},
        }});
        """


class Tabulator(object):
    """
    g2plot
    """

    def __init__(self, df: pd.DataFrame, sparkline_dict=None, width_dict=None, formatter_dict=None,
                 height: str = "500"):
        """
        tabulator
        :param df: []
        :param sparkline_dict: {'col':'line/bar/tristate/discrete/bullet/pie/box'}
        :param width_dict: {'col':'120'}
        :param formatter_dict: {'col':'progress/star/tickCross/color'}
        :param height:500
        """
        self.tabledata = Tools.convert_dict_to_js(df.to_dict(orient='records'))
        cols = []
        for col in df.columns:
            column = {'title': col, 'field': col}
            if sparkline_dict is not None and col in sparkline_dict.keys():
                column['formatter'] = Js(sparkline_dict[col] + "Formatter")
            if width_dict is not None and col in width_dict.keys():
                column['width'] = width_dict[col]
            if formatter_dict is not None and col in formatter_dict.keys():
                column['formatter'] = formatter_dict[col]
                if formatter_dict[col] == 'progress':
                    column['formatterParams'] = {"color": ["green", "orange", "red"]}
            cols.append(column)
        self.columns = Tools.convert_dict_to_js(cols)
        self.height = height
        self.plot_id = "u" + uuid.uuid4().hex
        self.width = "100%"

    @staticmethod
    def reduce_dataframe(df: pd.DataFrame, reduce_axis='index'):
        """
        :param df: 示例 pd.DataFrame(index=['2021-01-01','2021-01-02'],columns=['000001.SZ','000002.SZ'])
        :param reduce_axis: index按索引方向合并值到数组，columns 按列方向合并值到数组
        :return:
        """
        return df.apply(lambda s: s.tolist(), axis=reduce_axis, result_type='reduce')

    def render_notebook(self) -> Html:
        """
        在jupyter notebook 环境输出
        :return:
        """
        plot = self
        html = f"""
        <script>
          requirejs.config(
                     {{paths: {{ 
                        'tabulator': ['https://cdn.staticfile.org/tabulator/5.2.3/js/tabulator.min'],
                        'jquery':['https://cdn.staticfile.org/jquery/3.6.0/jquery.min'],
                        'sparkline':['https://cdn.staticfile.org/jquery-sparklines/2.1.2/jquery.sparkline.min'],
                     }},}}
                );
        </script>
        <style>
          #{plot.plot_id} {{
            width:{plot.width};
            height:{plot.height};
         }}
         .jqstooltip {{
          -webkit-box-sizing: content-box;
          -moz-box-sizing: content-box;
          box-sizing: content-box;
        }}
        </style>
        <div id="{plot.plot_id}"></div>
        <script>
         require(['tabulator','jquery','sparkline'],function(Tabulator,$,sparkline) {{
                var element = document.createElement("link");
                        element.setAttribute("rel", "stylesheet");
                        element.setAttribute("type", "text/css");
                        element.setAttribute("href", "https://cdn.staticfile.org/tabulator/5.2.3/css/tabulator.min.css");
                        document.getElementsByTagName("head")[0].appendChild(element);
                window.Tabulator=tabulator;
                """ + tabulator_segment(plot) + f"""
            }});
        </script>

        """
        return Html(html)

    def render_jupyterlab(self) -> Html:
        """
        在jupyterlab 环境输出
        :return:
        """
        plot = self
        html = f"""
            <style>
             #{plot.plot_id} {{
                width:{plot.width};
                height:{plot.height};
             }}
             .jqstooltip {{
              -webkit-box-sizing: content-box;
              -moz-box-sizing: content-box;
              box-sizing: content-box;
            }}
            </style>
            <div id="{plot.plot_id}"></div>
            <script>
            // load javascript
            
            new Promise(function(resolve, reject) {{
              var script = document.createElement("script");
              script.onload = resolve;
              script.onerror = reject;
              script.src = "https://cdn.staticfile.org/tabulator/5.2.3/js/tabulator.min.js";
              document.head.appendChild(script);
                var jq = document.createElement("script");
              script.onload = resolve;
              script.onerror = reject;
              script.src = "https://cdn.staticfile.org/jquery/3.6.0/jquery.min.js";
              document.head.appendChild(jq);
                var sparkline = document.createElement("script");
              script.onload = resolve;
              script.onerror = reject;
              script.src = "https://cdn.staticfile.org/jquery-sparklines/2.1.2/jquery.sparkline.min.js";
              document.head.appendChild(sparkline);
                var element = document.createElement("link");
                element.setAttribute("rel", "stylesheet");
                element.setAttribute("type", "text/css");
                element.setAttribute("href", "https://cdn.staticfile.org/tabulator/5.2.3/css/tabulator.min.css");
                document.getElementsByTagName("head")[0].appendChild(element);
            }}).then(() => {{
              """ + tabulator_segment(plot) + f"""
            }});
            </script>
            """
        return Html(html)

    def render_html(self) -> str:
        """
        渲染html字符串，可以用于 streamlit
        :return:
        """
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
                    .jqstooltip {{
              -webkit-box-sizing: content-box;
              -moz-box-sizing: content-box;
              box-sizing: content-box;
            }}
                </style>
                <script type="text/javascript" src="https://cdn.staticfile.org/tabulator/5.2.3/js/tabulator.min.js"></script>
             <script type="text/javascript" src="https://cdn.staticfile.org/jquery/3.6.0/jquery.min.js"></script>
             <script type="text/javascript" src="https://cdn.staticfile.org/jquery-sparklines/2.1.2/jquery.sparkline.min.js"></script>
            <link rel='stylesheet' href='https://cdn.staticfile.org/tabulator/5.2.3/css/tabulator.min.css'>
            </head>
            <body>
              <div id="{plot.plot_id}" ></div>
              <script>
                 {plot.extra_js}
            """ + tabulator_segment(plot) + f"""
            
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
        plot = self
        html = f"""
            <div>
             <script type="text/javascript" src="https://cdn.staticfile.org/tabulator/5.2.3/js/tabulator.min.js"></script>
             <script type="text/javascript" src="https://cdn.staticfile.org/jquery/3.6.0/jquery.min.js"></script>
             <script type="text/javascript" src="https://cdn.staticfile.org/jquery-sparklines/2.1.2/jquery.sparkline.min.js"></script>
            <link rel='stylesheet' href='https://cdn.staticfile.org/tabulator/5.2.3/css/tabulator.min.css'>
             <style>
                  #{plot.plot_id} {{
                        width:{plot.width};
                        height:{plot.height};
                     }}
                     .jqstooltip {{
              -webkit-box-sizing: content-box;
              -moz-box-sizing: content-box;
              box-sizing: content-box;
            }}
             </style>
             <div id="{plot.plot_id}" ></div>
              <script>
            """ + tabulator_segment(plot) + f"""
              </script>
            </div>
            """
        return html

    def _repr_html_(self):
        """
        jupyter 环境，直接输出
        :return:
        """
        plot = self
        html = f"""

        <style>
          #{plot.plot_id} {{
            width:{plot.width};
            height:{plot.height};
         }}
         .jqstooltip {{
          -webkit-box-sizing: content-box;
          -moz-box-sizing: content-box;
          box-sizing: content-box;
        }}
        </style>
        <div id="{plot.plot_id}"></div>
        <script>
          if (typeof require !== 'undefined'){{
                requirejs.config(
                     {{paths: {{ 
                        'tabulator': ['https://cdn.staticfile.org/tabulator/5.2.3/js/tabulator.min'],
                        'jquery':['https://cdn.staticfile.org/jquery/3.6.0/jquery.min'],
                        'sparkline':['https://cdn.staticfile.org/jquery-sparklines/2.1.2/jquery.sparkline.min'],
                     }},}}
                );
                require(['tabulator','jquery','sparkline'],function(Tabulator,$,sparkline) {{

                       var element = document.createElement("link");
                        element.setAttribute("rel", "stylesheet");
                        element.setAttribute("type", "text/css");
                        element.setAttribute("href", "https://cdn.staticfile.org/tabulator/5.2.3/css/tabulator.min.css");
                        document.getElementsByTagName("head")[0].appendChild(element);
                        """ + tabulator_segment(plot) + f"""
                    }});
             }}else{{
               new Promise(function(resolve, reject) {{
                  var script = document.createElement("script");
                  script.onload = resolve;
                  script.onerror = reject;
                  script.src = "https://cdn.staticfile.org/tabulator/5.2.3/js/tabulator.min.js";
                  document.head.appendChild(script);
                    var jq = document.createElement("script");
                  script.onload = resolve;
                  script.onerror = reject;
                  script.src = "https://cdn.staticfile.org/jquery/3.6.0/jquery.min.js";
                  document.head.appendChild(jq);
                    var sparkline = document.createElement("script");
                  script.onload = resolve;
                  script.onerror = reject;
                  script.src = "https://cdn.staticfile.org/jquery-sparklines/2.1.2/jquery.sparkline.min.js";
                  document.head.appendChild(sparkline);
                    var element = document.createElement("link");
                    element.setAttribute("rel", "stylesheet");
                    element.setAttribute("type", "text/css");
                    element.setAttribute("href", "https://cdn.staticfile.org/tabulator/5.2.3/css/tabulator.min.css");
                    document.getElementsByTagName("head")[0].appendChild(element);
                }}).then(() => {{
                  """ + tabulator_segment(plot) + f"""
                }});
             }}

        </script>
        """
        return Html(html).data
