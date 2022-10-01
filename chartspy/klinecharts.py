#!/usr/bin/env python
# coding=utf-8
import uuid

import pandas as pd

from .base import Tools, Html

KlineCharts_JS_URL: str = "https://cdn.jsdelivr.net/npm/klinecharts@latest/dist/klinecharts.min.js"


# language=jinja2

def kline_chart_segment(plot):
    parts = []
    parts.append(
        f"""var chart_{plot.plot_id} = klinecharts.init("{plot.plot_id}",
        {{
            grid: {{ 
                show: true, horizontal: {{ show: true, size: 2, color: '#CFCFCF', style: 'dash'}},
                vertical: {{ show: true, size: 2, color: '#CFCFCF',  style: 'dash'}},
                'candle':{{'bar':{{'upColor':'#EF5350','downColor':'#26A69A'}} }},
                'technicalIndicator':{{
                    'bar':{{'upColor':'#EF5350','downColor':'#26A69A'}} 
                 }}
            }}
         }}
         );""")
    for bt in plot.bottom_indicators:
        parts.append(f"""var btm_{bt}_{plot.plot_id} = chart_{plot.plot_id}.createTechnicalIndicator('{bt}', false)""")
    for mi in plot.main_indicators:
        parts.append(f"""chart_{plot.plot_id}.createTechnicalIndicator('{mi}', true,{{id:"candle_pane"}})""")
    if len(plot.mas) > 0:
        parts.append(
            f"""chart_{plot.plot_id}.overrideTechnicalIndicator({{name: 'MA',calcParams: {str(plot.mas)} }},"candle_pane")""")
    if len(plot.segments) > 0:
        for seg in plot.segments:
            parts.append(f"""
            chart_{plot.plot_id}.createShape({{name: 'segment',points:[{{timestamp:{seg['start_time']},value:{seg['start_price']}}},{{timestamp:{seg['end_time']},value:{seg['end_price']}}}]}},"candle_pane")
            """)
    parts.append(f"""chart_{plot.plot_id}.applyNewData(data_{plot.plot_id})""")
    return "\n".join(parts)


class KlineCharts(object):
    """
    g2plot
    """

    def __init__(self, df: pd.DataFrame, mas=[5, 10, 30, 60, 120, 250], main_indicators=["MA"],
                 bottom_indicators=["VOL", "MACD"], df_segments: pd.DataFrame = None,
                 extra_js: str = "", width: str = "100%",
                 height: str = "500px"):
        """
        k线图
        :param df: [open,high,low,close,volume,turnover,timestamp]
        :param mas: [5, 10, 30, 60, 120, 250]
        :param main_indicators: 主图显示的指标列表 MA,EMA,SMA,BOLL,SAR,BBI
        :param bottom_indicators:副图显示指标列表 VOL,MACD,KDJ,RSI,BIAS,BBAR,CCI,DMI,CR,PSY,DMA,TRIX,OBV,VR,WR,MTM,EMV,SAR,SMA,ROC,PVT,BBI,AO
        :param df_segments:[start_time,start_price,end_time,end_price]
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
        if df_segments is not None:
            df_seg = df_segments.copy()
            df_seg['start_time'] = (pd.to_datetime(df_seg['start_time']) - pd.Timedelta(hours=8)).view(
                "i8") // 10 ** 6
            df_seg['end_time'] = (pd.to_datetime(df_seg['end_time']) - pd.Timedelta(hours=8)).view("i8") // 10 ** 6
            self.segments = df_seg.to_dict(orient='records')
        else:
            self.segments = []
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
        plot = self

        html = f"""
        <script>
          require.config({{
            paths: {{
              "klinecharts": "{plot.js_url[:-3]}"
            }}
          }});
        </script>
        <style>
          #{plot.plot_id} {{
            width:{plot.width};
            height:{plot.height};
         }}
        </style>
        <div id="{plot.plot_id}"></div>
        <script>
          {plot.extra_js}
          var data_{plot.plot_id} = {plot.data}
          require(['klinecharts'], function (klinecharts) {{
            """ + kline_chart_segment(plot) + f"""
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
              """ + kline_chart_segment(plot) + f"""
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
            </style>
           <script type="text/javascript" src="{plot.js_url}"></script>
        </head>
        <body>
          <div id="{plot.plot_id}" ></div>
          <script>
             {plot.extra_js}
        """ + kline_chart_segment(plot) + f"""

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
        """ + kline_chart_segment(plot) + f"""
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
        </style>
        <div id="{plot.plot_id}"></div>
        <script>
          {plot.extra_js}
          var data_{plot.plot_id} = {plot.data}
          if (typeof require !== 'undefined'){{
              require.config({{
                paths: {{
                  "klinecharts": "{plot.js_url[:-3]}"
                }}
              }});
              require(['klinecharts'], function (klinecharts) {{
                """ + kline_chart_segment(plot) + f"""
             }});
             }}else{{
               new Promise(function(resolve, reject) {{
                 var script = document.createElement("script");
                 script.onload = resolve;
                 script.onerror = reject;
                 script.src = "{plot.js_url}";
                 document.head.appendChild(script);
               }}).then(() => {{
                 """ + kline_chart_segment(plot) + f"""
               }});
             }}
        
        </script>
        """
        return Html(html).data
