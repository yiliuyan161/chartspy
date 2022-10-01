#!/usr/bin/env python
# coding=utf-8
import copy
import datetime
import json
import re
import uuid

import numpy as np
import pandas as pd

FUNCTION_BOUNDARY_MARK = "FUNCTION_BOUNDARY_MARK"


class Js:
    """
    JavaScript代码因为不是标准json,先以特殊字符包裹字符串形式保存
    dump成标准json字符串后，再用正则根据特殊字符，恢复成JavaScript函数
    """

    def __init__(self, js_code: str):
        js_code = re.sub("\\n|\\t", "", js_code)
        js_code = re.sub(r"\\n", "\n", js_code)
        js_code = re.sub(r"\\t", "\t", js_code)
        self.js_code = FUNCTION_BOUNDARY_MARK + js_code + FUNCTION_BOUNDARY_MARK


class Html:
    """
    在 jupyter notebook 或者 jupyterlab 中输出html内容需要用此对象包裹
    """

    def __init__(self, data=None):
        self.data = data

    def _repr_html_(self):
        return self.data

    def __html__(self):
        return self._repr_html_()


class Tools(object):

    @staticmethod
    def convert_to_list(data):
        """
        转换DataFrame,Series,ndarray转换成list
        :param data: DataFrame/Series/ndarray
        :return:
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
        return data

    @staticmethod
    def df_uniformize_datetime_columns(data_frame: pd.DataFrame, columns: list = [],
                                       index: bool = False) -> pd.DataFrame:
        """
        data_frame 时间相关的列，统一成datetime格式
        :param data_frame: 源data_frame
        :param columns: 需要转换成datetime格式的列
        :param index: 是否转换index成datetime格式
        :return: 转换过时间格式的DataFrame
        """
        df = data_frame.copy()
        for col in columns:
            df[col] = pd.to_datetime(df[col])
        if index:
            df.index = pd.to_datetime(df.index)
        return df

    @staticmethod
    def df2tree(df: pd.DataFrame = None, category_cols=[], value_col="") -> list:
        """
        cat1,cat2,cat3,...,value格式的DataFrame转换成echarts需要的树形结构
        :param df:
        :param category_cols:
        :param value_col:
        :return:
        """
        cols = category_cols
        df_data = df[category_cols + [value_col]]
        tmp_dict = {}
        # 从最底层2个类别列开始处理，依次往左处理
        for i in range(len(cols) - 1, 0, -1):
            # c1,c0,v0
            parent_idx = i - 1
            child_idx = i
            df_unit = df_data[[cols[parent_idx], cols[child_idx], value_col]]
            # c1:set(c0)
            parent_child_map = df_unit.groupby(cols[parent_idx]).apply(
                lambda dx: list(dx[cols[child_idx]].unique())).to_dict()
            # c1:sum(v0)
            parent_sum_value_dict = df_unit[[cols[parent_idx], value_col]].groupby(cols[parent_idx]).sum()[
                value_col].to_dict()
            # 第一次迭代，拼装子结构放到父节点下
            if i == len(cols) - 1:
                child_sum_value_dict = df_unit[[cols[child_idx], value_col]].groupby(cols[child_idx]).sum()[
                    value_col].to_dict()
                for parent in parent_child_map.keys():
                    children = []
                    for child in parent_child_map[parent]:
                        value = child_sum_value_dict[child]
                        children.append({'name': child, 'value': value})
                    tmp_dict[parent] = {'name': parent, 'value': parent_sum_value_dict[parent], 'children': children}
            else:
                # 非首次迭代,从tmp_dict中取拼装好的子结构放到父节点下
                for parent in parent_child_map.keys():
                    children = []
                    for child in parent_child_map[parent]:
                        children.append(tmp_dict[child])
                    tmp_dict[parent] = {'name': parent, 'value': parent_sum_value_dict[parent], 'children': children}
        data = []
        for cat in df_data[cols[0]].unique():
            data.append(tmp_dict[cat])
        return data

    @staticmethod
    def convert_js_to_dict(js_code: str, print_dict: bool = True) -> dict:
        """
        转换JavaScript Object 成 python dict
        基础类常量替换,去除注释，字段名加单引号，函数变Js函数包裹
        :param js_code:
        :param print_dict: 是否控制台打印
        :return: dict
        """
        js_code = js_code.strip()

        def rep1(match_obj):
            return '"' + match_obj.group(1) + '": ' + match_obj.group(2)

        # 去除注释
        js_code = re.sub(r"[\s]+//[^\n]+\n", "", js_code)
        # 对象key 增加单引号
        js_code = re.sub(r"([a-zA-Z0-9]+):\s*([\{'\"\[]|true|false|[\d\.]+|function)", rep1, js_code)
        # 记录函数开始结束位置数组
        segs = []  # [start,end]
        function_start = 0
        left_bracket_count = 0
        right_bracket_count = 0
        in_function = False
        for i in range(8, len(js_code)):
            if "function" == js_code[i - 8:i] and not in_function:  # 函数位置开始
                function_start = i - 8
                left_bracket_count = 0
                right_bracket_count = 0
                in_function = True
            elif js_code[i] == '{' and in_function:
                left_bracket_count = left_bracket_count + 1
            elif js_code[i] == '}' and in_function:
                right_bracket_count = right_bracket_count + 1
            # 函数结束条件，函数尚未结束，左括号数量和有括号相等且都大于0
            if in_function and left_bracket_count == right_bracket_count and left_bracket_count > 0:
                function_end = i
                segs.append([function_start, function_end])
                left_bracket_count = 0
                right_bracket_count = 0
                in_function = False

        left_index = 0
        parts = []
        for seg in segs:
            parts.append(js_code[left_index:seg[0]])
            parts.append('Js("""' + js_code[seg[0]:(seg[1] + 1)] + '""")')
            left_index = seg[1] + 1
        parts.append(js_code[left_index:])
        dict_str = "".join(parts)
        if print_dict:
            print(dict_str)
        dict_options = json.loads(dict_str)
        return dict_options

    @staticmethod
    def convert_dict_to_js(options):
        """
        转换 python dict 成 JavaScript Object
        先json序列化,再特殊处理函数
        :return: JavaScript 对象的字符串表示
        """
        json_str = json.dumps(options, indent=2, default=json_type_convert)
        code_segments = []
        function_start = 0
        # 找到所有函数声明的起止位置,处理双引号转移，再把包裹函数的特征串删除
        mask_length = len(FUNCTION_BOUNDARY_MARK)
        for i in range(mask_length, len(json_str)):
            if json_str[i - mask_length - 1:i] == '"' + FUNCTION_BOUNDARY_MARK:
                function_start = i - mask_length
            elif json_str[i - mask_length - 1:i] == FUNCTION_BOUNDARY_MARK + '"':
                code_segments.append([function_start, i])
        left_index = 0
        parts = []
        for seg in code_segments:
            parts.append(json_str[left_index:seg[0]])
            parts.append(json_str[seg[0]:(seg[1] + 1)].replace('\\"', '"'))
            left_index = seg[1] + 1
        parts.append(json_str[left_index:])
        dict_str = "".join(parts)
        return re.sub('"?' + FUNCTION_BOUNDARY_MARK + '"?', "", dict_str)


json_encoder = json.JSONEncoder()


def json_type_convert(o: object):
    """
    python 类型转换成js类型
    :param o: json序列化不支持的类型
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
    elif isinstance(o, np.datetime64):
        o1 = pd.to_datetime(o)
        if o1.hour + o1.minute + o1.second == 0:
            return o1.strftime("%Y-%m-%d")
        else:
            return o1.isoformat()
    elif isinstance(o, np.bool_):
        return bool(o)
    elif isinstance(o, np.integer):
        return int(o)
    elif isinstance(o, np.floating):
        return float(o)
    elif isinstance(o, np.complexfloating):
        return float(o)
    elif isinstance(o, np.character):
        return str(o)
    elif isinstance(o, np.ndarray):
        return list(o)
    elif pd.isna(o):
        return None
    else:
        return json_encoder.default(o)


ECHARTS_JS_URL = "https://cdn.staticfile.org/echarts/5.3.2/echarts.min.js"
ECHARTS_GL_JS_URL = "https://cdn.staticfile.org/echarts-gl/2.0.8/echarts-gl.min.js"


class Echarts(object):
    """
    echarts
    """

    def __init__(self, options: dict = None, extra_js: str = "", with_gl=False, width: str = "100%",
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
        self.js_url = ECHARTS_JS_URL
        self.js_url_gl = ECHARTS_GL_JS_URL
        self.extra_js = extra_js
        self.with_gl = with_gl

    @staticmethod
    def timeline(echarts_dict: dict = {}, visual_map_options=None):
        """

        :param echarts_dict: key类型字符串，用作标题, value类型 Echarts对象，或者Echarts对象的options
        :param visual_map_options: visualMap 配置,visualMap最大值最小值需要配置的时候设置,格式参照echarts官方文档
        :return:
        """
        charts_dict = {k: (v.options if isinstance(v, Echarts) else v) for k, v in echarts_dict.items()}
        options = {
            "baseOption": {
                'timeline': {
                    'axisType': 'category',
                    'orient': 'vertical',
                    'autoPlay': True,
                    'inverse': True,
                    'playInterval': 1000,
                    'left': None,
                    'right': 0,
                    'top': 20,
                    'bottom': 20,
                    'width': 55,
                    'height': None,
                    'symbol': 'none',
                    'checkpointStyle': {
                        'borderWidth': 2
                    },
                    'controlStyle': {
                        'showNextBtn': False,
                        'showPrevBtn': False
                    },
                    'data': [],
                },
                'grid': {
                    'top': 100,
                    'containLabel': True,
                    'left': 30,
                    'right': '110'
                },
                'animationDurationUpdate': 1000,
                'animationEasingUpdate': 'quinticInOut'
            },
            'options': []
        }
        keys = list(charts_dict.keys())
        keys.sort()
        options['baseOption']['timeline']['data'] = keys
        if len(keys) > 0:
            if 'tooltip' in charts_dict[keys[0]].keys():
                options['baseOption']['tooltip'] = charts_dict[keys[0]]['tooltip']
            if 'xAxis' in charts_dict[keys[0]].keys():
                options['baseOption']['xAxis'] = charts_dict[keys[0]]['xAxis']
            if 'yAxis' in charts_dict[keys[0]].keys():
                options['baseOption']['yAxis'] = charts_dict[keys[0]]['yAxis']

            if visual_map_options is not None:
                options['baseOption']['visualMap'] = visual_map_options
            elif 'visualMap' in charts_dict[keys[0]].keys():
                options['baseOption']['visualMap'] = charts_dict[keys[0]]['visualMap']
            if 'series' in charts_dict[keys[0]].keys():
                options['baseOption']['series'] = charts_dict[keys[0]]['series']
            for i in range(0, len(keys)):
                options['options'].append({
                    'title': {
                        'show': True,
                        'text': keys[i]
                    },
                    'series': charts_dict[keys[i]]['series']
                })
                if 'visualMap' in charts_dict[keys[i]].keys() and 'visualMap' in options['baseOption'].keys():
                    if isinstance(charts_dict[keys[i]]['visualMap'], list) and isinstance(
                            options['baseOption']['visualMap'], list) and len(charts_dict[keys[i]]['visualMap']) == len(
                        options['baseOption']['visualMap']):
                        for j in range(0, len(options['baseOption']['visualMap'])):
                            if 'min' in options['baseOption']['visualMap'][j].keys():
                                options['baseOption']['visualMap'][j]['min'] = min(
                                    options['baseOption']['visualMap'][j]['min'],
                                    charts_dict[keys[i]]['visualMap'][j]['min'])
                            if 'max' in options['baseOption']['visualMap'][j].keys():
                                options['baseOption']['visualMap'][j]['max'] = min(
                                    options['baseOption']['visualMap'][j]['max'],
                                    charts_dict[keys[i]]['visualMap'][j]['max'])
                    elif isinstance(charts_dict[keys[i]]['visualMap'], dict) and isinstance(
                            options['baseOption']['visualMap'], dict):
                        if 'min' in options['baseOption']['visualMap'].keys():
                            options['baseOption']['visualMap']['min'] = min(
                                options['baseOption']['visualMap']['min'],
                                charts_dict[keys[i]]['visualMap']['min'])
                        if 'max' in options['baseOption']['visualMap'].keys():
                            options['baseOption']['visualMap']['max'] = max(
                                options['baseOption']['visualMap']['max'],
                                charts_dict[keys[i]]['visualMap']['max'])

        return Echarts(options=options)

    def overlap_series(self, other_chart_options: list = [], add_yaxis=False, add_yaxis_grid_index=0):
        """
        叠加其他配置中的Series数据到现有配置，现有配置有多个坐标轴的，建议Series声明对应的axisIndex
        :param other_chart_options:要叠加的Echarts对象列表，或者options列表
        :param add_yaxis: 是否增加一个Y轴
        :param add_yaxis_grid_index: 0
        :return:
        """
        this_options = copy.deepcopy(self.options)
        if add_yaxis:
            this_options['yAxis'].append({'scale': True, 'type': 'value', 'gridIndex': add_yaxis_grid_index})
        if this_options["legend"]["data"] is None:
            this_options["legend"]["data"] = []
        if this_options["series"] is None:
            this_options["series"] = []
        for chart_option in other_chart_options:
            if isinstance(chart_option, Echarts):
                chart_option = chart_option.options
            old_series_count = len(this_options["series"])
            this_options["legend"]["data"].extend(chart_option["legend"]["data"])
            if add_yaxis:
                for seriesIndex in range(len(chart_option["series"])):
                    chart_option["series"][seriesIndex]['yAxisIndex'] = len(this_options['yAxis']) - 1
            this_options["series"].extend(chart_option["series"])
            if "visualMap" in chart_option.keys():
                if "visualMap" not in this_options.keys():
                    this_options["visualMap"] = []
                for i in range(0, len(chart_option["visualMap"])):
                    if "seriesIndex" in chart_option["visualMap"][i].keys():
                        chart_option["visualMap"][i]['seriesIndex'] = chart_option["visualMap"][i][
                                                                          'seriesIndex'] + old_series_count
                    else:
                        chart_option["visualMap"][i]['seriesIndex'] = old_series_count
                this_options["visualMap"].extend(chart_option["visualMap"])
        return Echarts(options=this_options, extra_js=self.extra_js, width=self.width, height=self.height)

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
        if plot.with_gl:
            html = f"""
            <style>
              #{plot.plot_id} {{
                width:{{plot.width}};
                height:{{plot.height}};
             }}
            </style>
            <div id="{plot.plot_id}"></div>
            <script>
                require.config({{
                    paths: {{
                      "echarts": "{plot.js_url[:-3]}",
                      "echartsgl": "{plot.js_url_gl[:-3]}"
                    }}
                  }});
                  require(['echarts','echartsgl'], function (echarts,echartsgl) {{
                    var plot_{plot.plot_id} = echarts.init(document.getElementById('{plot.plot_id}'));
                    {plot.extra_js}
                    var options_{plot.plot_id} = {plot.js_options};
                    plot_{plot.plot_id}.setOption(options_{plot.plot_id})
                  }});
            </script>
            """
        else:
            html = f"""
            <style>
              #{plot.plot_id} {{
                width:{{plot.width}};
                height:{{plot.height}};
             }}
            </style>
            <div id="{plot.plot_id}"></div>
            <script>
                require.config({{
                    paths: {{
                      "echarts": "{plot.js_url[:-3]}",
                    }}
                  }});
                  require(['echarts'], function (echarts) {{
                    var plot_{plot.plot_id} = echarts.init(document.getElementById('{plot.plot_id}'));
                    {plot.extra_js}
                    var options_{plot.plot_id} = {plot.js_options};
                    plot_{plot.plot_id}.setOption(options_{plot.plot_id})
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
        if plot.with_gl:
            html = f"""
                <style>
                 #{plot.plot_id}{{
                    width:{plot.width};
                    height:{plot.height};
                 }}
                </style>
                <div id="{plot.plot_id}"></div>
                  <script>
                    // load javascript
                    new Promise(function(resolve, reject) {{
                      var script = document.createElement("script");
                      script.onload = resolve;
                      script.onerror = reject;
                      script.src = "{plot.js_url}";
                      document.head.appendChild(script);
                      var scriptGL = document.createElement("script");
                      scriptGL.onload = resolve;
                      scriptGL.onerror = reject;
                      scriptGL.src = "{plot.js_url_gl}";
                      document.head.appendChild(scriptGL);
                    }}).then(() => {{
                       var plot_{plot.plot_id} = echarts.init(document.getElementById('{plot.plot_id}'));
                       {plot.extra_js}
                       plot_{plot.plot_id}.setOption({plot.js_options})
                    }});
                  </script>
                """
        else:
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
                new Promise(function(resolve, reject) {{
                    var script =document.createElement("script");
                    script.onload = resolve;
                    script.onerror = reject;
                    script.src = "{plot.js_url}";
                    document.head.appendChild(script);
                }}).then(() => {{
                    var plot_{plot.plot_id} = echarts.init(document.getElementById('{plot.plot_id}'));
                    {plot.extra_js}
                    plot_{plot.plot_id}.setOption({plot.js_options})
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
        if self.with_gl:
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
                <script type="text/javascript" src="{plot.js_url_gl}"></script>
            </head>
            <body>
              <div id="{plot.plot_id}" ></div>
              <script>
                var plot_{plot.plot_id} = echarts.init(document.getElementById('{plot.plot_id}'));
                {plot.extra_js}
                plot_{plot.plot_id}.setOption({plot.js_options})
              </script>
            </body>
            </html>
            """
        else:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="UTF-8">
              <title></title>
                <style>
                  #{plot.plot_id} {{
                        width:{ {plot.width} };
                        height:{ {plot.height} };
                     }}
                </style>
               <script type="text/javascript" src="{plot.js_url}"></script>
            </head>
            <body>
              <div id="{plot.plot_id}" ></div>
              <script>
                var plot_{plot.plot_id} = echarts.init(document.getElementById('{plot.plot_id}'));
                {plot.extra_js}
                plot_{plot.plot_id}.setOption({plot.js_options})
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
        if self.with_gl:
            html = f"""
                <div>
                 <script type="text/javascript" src="{plot.js_url}"></script>
                 <script type="text/javascript" src="{plot.js_url_gl}"></script>
                 <style>
                      #{plot.plot_id} {{
                            width:{plot.width};
                            height:{plot.height};
                         }}
                 </style>
                 <div id="{plot.plot_id}" ></div>
                  <script>
                    var plot_{plot.plot_id} = echarts.init(document.getElementById('{plot.plot_id}'));
                    {plot.extra_js}
                    plot_{plot.plot_id}.setOption({plot.js_options})
                  </script>
                </div>
                """
        else:
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
                    var plot_{plot.plot_id} = echarts.init(document.getElementById('{plot.plot_id}'));
                    {plot.extra_js}
                    plot_{plot.plot_id}.setOption({plot.js_options})
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
        if self.with_gl:
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
          var options_{plot.plot_id} = {plot.js_options};
          if (typeof require !== 'undefined'){{
            require.config({{
                paths: {{
                  "echarts": "{plot.js_url[:-3]}",
                  "echartsgl": "{plot.js_url_gl[:-3]}"
                }}
              }});
              require(['echarts','echartsgl'], function (echarts,echartsgl) {{
                var plot_{plot.plot_id} =
                echarts.init(document.getElementById('{plot.plot_id}'));
                plot_{plot.plot_id}.setOption(options_{plot.plot_id})
              }});
          }}else{{
            new Promise(function(resolve, reject)
        {{
            var script = document.createElement("script");
            script.onload = resolve;
            script.onerror = reject;
            script.src = "{plot.js_url}";
            document.head.appendChild(script);
            var
            scriptGL = document.createElement("script");
            scriptGL.onload = resolve;
            scriptGL.onerror = reject;
            scriptGL.src = "{plot.js_url_gl}";
            document.head.appendChild(scriptGL);
        }}).then(() = > {{
            var plot_{plot.plot_id} = echarts.init(document.getElementById('{plot.plot_id}'));
            plot_{plot.plot_id}.setOption(options_{plot.plot_id})
        }});
        }}
        </script>
        """
        else:
            # language=HTML
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
          var options_{plot.plot_id} = {plot.js_options};
          if (typeof require !== 'undefined'){{
            require.config({{
                paths: {{
                  "echarts": "{plot.js_url[:-3]}",
                }}
              }});
              require(['echarts'], function (echarts) {{
                var plot_{plot.plot_id} = echarts.init(document.getElementById('{plot.plot_id}'));
                plot_{plot.plot_id}.setOption(options_{plot.plot_id})
              }});
          }}else{{
            new Promise(function(resolve, reject) {{
              var script = document.createElement("script");
              script.onload = resolve;
              script.onerror = reject;
              script.src = "{plot.js_url}";
              document.head.appendChild(script);
            }}).then(() => {{
               var plot_{plot.plot_id} = echarts.init(document.getElementById('{plot.plot_id}'));
               plot_{plot.plot_id}.setOption(options_{plot.plot_id})
            }});
          }}
        </script>
        """
        return Html(html).data


G2PLOT_JS_URL: str = "https://cdn.staticfile.org/g2plot/2.4.16/g2plot.min.js"


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
            require.config({{
                    packages: [{{
                        name: 'highcharts',
                        main: 'highcharts'
                    }}],
                    paths: {{
                        'highcharts': 'https://code.highcharts.com'
                    }}
               }});
              require(['highcharts','highcharts/modules/streamgraph','highcharts/modules/arc-diagram','highcharts/modules/sankey','highcharts/modules/dependency-wheel'], function (Highcharts) {{
                {plot.extra_js}
                var options_{plot.plot_id} = {plot.js_options};
                Highcharts.chart('{plot.plot_id}',options_{plot.plot_id})
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
                new Promise(function(resolve, reject) {{
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
                }}).then(() => {{
                   {plot.extra_js}
                   var options_{plot.plot_id} = {plot.js_options};
                   Highcharts.chart('{plot.plot_id}',options_{plot.plot_id})
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
        <script src="https://code.highcharts.com/highcharts.js"></script>
        <script src="https://code.highcharts.com/modules/streamgraph.js"></script>
        <script src="https://code.highcharts.com/modules/dependency-wheel.js"></script>
         <script src="https://code.highcharts.com/modules/arc-diagram.js"></script>
         <script src="https://code.highcharts.com/modules/sankey.js"></script>
        </head>
        <body>
          <div id="{plot.plot_id}" ></div>
          <script>
            {plot.extra_js}
            var options_{plot.plot_id} = {plot.js_options};
            Highcharts.chart('{plot.plot_id}',options_{plot.plot_id})
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
        <script src="https://code.highcharts.com/highcharts.js"></script>
        <script src="https://code.highcharts.com/modules/streamgraph.js"></script>
        <script src="https://code.highcharts.com/modules/dependency-wheel.js"></script>
         <script src="https://code.highcharts.com/modules/arc-diagram.js"></script>
         <script src="https://code.highcharts.com/modules/sankey.js"></script>
         <style>
              #{plot.plot_id} {{
                    width:{plot.width};
                    height:{plot.height};
              }}
         </style>
         <div id="{plot.plot_id}" ></div>
          <script>
            {plot.extra_js}
            var options_{plot.plot_id} = {plot.js_options};
            Highcharts.chart('{plot.plot_id}',options_{plot.plot_id})
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
        <script>

        </script>
        <style>
          #{plot.plot_id} {{
            width:{plot.width};
            height:{plot.height};
         }}
        </style>
        <div id="{plot.plot_id}"></div>
        <script >
          {plot.extra_js}
          var options_{plot.plot_id} = {plot.js_options};
        </script>
        <script>
          if (typeof require !== 'undefined'){{
              require.config({{
                    packages: [{{
                        name: 'highcharts',
                        main: 'highcharts'
                    }}],
                    paths: {{
                        'highcharts': 'https://code.highcharts.com'
                    }}
               }});
              require(['highcharts','highcharts/modules/streamgraph','highcharts/modules/arc-diagram','highcharts/modules/sankey','highcharts/modules/dependency-wheel'], function (Highcharts) {{
                Highcharts.chart('{plot.plot_id}',options_{plot.plot_id})
              }});
          }}else{{
            new Promise(function(resolve, reject) {{
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

            }}).then(() => {{
                {plot.extra_js}
               Highcharts.chart('{plot.plot_id}',options_{plot.plot_id})
            }});
          }}
        </script>
        """
        return Html(html).data


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


# 二维坐标系统基础配置适用  scatter,bar,line
ECHARTS_BASE_GRID_OPTIONS = {
    'legend': {
        'data': []
    },
    'tooltip': {
        'trigger': 'axis', 'axisPointer': {'type': 'cross'},
        'borderWidth': 1,
        'color': "black",
        'backgroundColor': "rgba(255,255,255,0.8)",
        'borderColor': '#ccc',
        'padding': 10,
        'formatter': Js("""
                function(params){
                    window.params=params;
                    var x_value = params[0]['axisValue'];
                    var labels = [];
                    labels.push('<b><span>x轴:&nbsp;</span></b>' + x_value + '<br/>');
                    params.sort(function(a, b) {
                      if (a.seriesName < b.seriesName ) {return -1;}
                      else if (a.seriesName > b.seriesName ) {return 1;}
                      else{ return 0;}
                    });
                    for (let i = 0; i < params.length; i++) {
                        const param = params[i];
                        var label=['<b><span>'+param['seriesName']+'('+param['seriesType']+'):&nbsp;</span></b>'];
                        var dimensionNames=param['dimensionNames'];
                        if (typeof(param['value'])=='object' && dimensionNames.length>=param['data'].length){
                            label.push("<br/>");
                            for (let j = 1; j <param['data'].length; j++) {
                                var value= param['value'][j];
                                if (typeof(value)=='number'){
                                    if (value%1==0 || value>100000){
                                        label.push('<span>'+dimensionNames[j]+':&nbsp;'+value.toFixed(0)+'</span><br/>');
                                    }else{
                                        label.push('<span>'+dimensionNames[j]+':&nbsp;'+value.toFixed(2)+'</span><br/>');
                                    }
                                }else{
                                    label.push("<div style='max-width:15em;word-break: break-all;white-space: normal;'>"+dimensionNames[j]+':&nbsp;'+value+"</div>");
                                }
                            }
                        }else if(typeof(param['value'])=='number'){
                            if (param['value']%1==0){
                                label.push("<span>"+param['value'].toFixed(0)+"</span><br/>");
                            }else{
                                label.push("<span>"+param['value'].toFixed(2)+"</span><br/>");
                            }
                        }else if(param['value']){
                            label.push("<div style='max-width:15em;word-break:break-all;white-space: normal;'>"+value+"</div>");
                        }else{
                            label.push("<br/>");
                        }
                        var cardStr= label.join('');
                        labels.push(cardStr);
                    }
                    return labels.join('');
                }"""),
        'textStyle': {'color': '#000'},
        'position': Js("""
                function (pos, params, el, elRect, size){
                    var obj = {top: 10};
                    obj[['left', 'right'][+(pos[0] < size.viewSize[0] / 2)]] = 30;
                    return obj;
                }
            """)
    },
    'axisPointer': {
        'link': {'xAxisIndex': 'all'},
        'label': {'backgroundColor': '#777'}
    },
    'xAxis': {
        'type': 'value',
    },
    'yAxis': {
        'type': 'value',
        'scale': True,
        'splitLine': {
            'show': True
        }
    },
    'dataZoom': [
        {
            'type': 'inside',
            'xAxisIndex': 0,
            'start': 0,
            'end': 100
        },
        {
            'type': 'inside',
            'yAxisIndex': 0,
            'start': 0,
            'end': 100
        }
    ],
    'series': []
}

ECHARTS_BASE_OVERLAY_OPTIONS = {
    'legend': {
        'data': []
    },
    'series': [{
        'type': 'scatter',
        'data': []
    }]
}


def scatter_echarts(data_frame: pd.DataFrame, x_field: str = None, y_field: str = None, size_field: str = None,
                    color_field: str = None, symbol: str = None,
                    size_range=[2, 30],
                    size_min_max=[None, None],
                    color_sequence: list = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf", "#fee090",
                                            "#fdae61", "#f46d43", "#d73027", "#a50026"], info: str = None,
                    x_field_type: str = None,
                    x_field_log_base: int = 10,
                    x_field_scale: bool = False,
                    y_field_type: str = None,
                    y_field_log_base: int = 10,
                    y_field_scale: bool = False,
                    opacity=0.5, tooltip_trigger="axis", title: str = "",
                    width: str = "100%",
                    height: str = "500px") -> Echarts:
    """
    scatter chart


    :param data_frame: 必填 DataFrame
    :param x_field: 必填 x轴映射的列
    :param y_field: 必填 y轴映射的列
    :param size_field: 可选 原点大小列
    :param color_field:颜色映射的列
    :param symbol: 'circle', 'rect', 'roundRect', 'triangle', 'diamond', 'pin', 'arrow', 'none',image://dataURI(), path://(svg)
    :param size_range: 可选 点大小区间
    :param info: 额外信息tooltip显示
    :param color_sequence:
    :param x_field_type:
    :param x_field_log_base:
    :param x_field_scale:
    :param y_field_type:
    :param y_field_log_base:
    :param y_field_scale:
    :param opacity:
    :param tooltip_trigger: tooltip 触发类型 axis和 item
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    df = data_frame.copy()
    if x_field is None:
        df["x_col_echartspy"] = df.index
        x_field = "x_col_echartspy"
    options = copy.deepcopy(ECHARTS_BASE_GRID_OPTIONS)
    options['title'] = {"text": title}
    options['xAxis']['type'] = x_field_type if x_field_type is not None else (
        "category" if "string" in str(df[x_field].dtype) or 'object' in str(df[x_field].dtype) else "value")
    options['xAxis']['logBase'] = x_field_log_base
    options['xAxis']['scale'] = x_field_scale
    options['yAxis']['type'] = y_field_type if y_field_type is not None else (
        "category" if "string" in str(df[y_field].dtype) or 'object' in str(df[y_field].dtype) else "value")
    options['yAxis']['logBase'] = y_field_log_base
    options['yAxis']['scale'] = y_field_scale

    if "date" in str(df[x_field].dtype) or "object" in str(df[x_field].dtype):
        options['xAxis']['type'] = 'category'
    if "date" in str(df[y_field].dtype) or "object" in str(df[y_field].dtype):
        options['yAxis']['type'] = 'category'
    title = y_field if title == '' else title
    series = {
        'type': 'scatter',
        'itemStyle': {
            'opacity': opacity
        },
        'name': title,
        'emphasis': {
            'itemStyle': {
                'borderColor': "#333",
                'borderWidth': 1,
                'shadowColor': 'rgba(0, 0, 0, 0.5)',
                'shadowBlur': 5
            }
        }
    }
    if tooltip_trigger == 'item':
        del options['axisPointer']
        options['tooltip'] = {
            'trigger': 'item',
            'borderWidth': 1,
            'borderColor': '#ccc',
            'padding': 10,
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)",
            'formatter': Js("""
                        function(params){
                            window.params=params;
                            var labels = [];
                            const param = params;
                            var label=['<b><span>'+param['seriesName']+'('+param['seriesType']+'):&nbsp;</span></b>'];
                            var dimensionNames=param['dimensionNames'];
                            if (typeof(param['value'])=='object' && dimensionNames.length>=param['data'].length){
                                label.push("<br/>");
                                for (let j = 0; j <param['data'].length; j++) {
                                    var value= param['value'][j];
                                    if (typeof(value)=='number'){
                                        if (value%1==0 || value>100000){
                                            label.push('<span>'+dimensionNames[j]+':&nbsp;'+value.toFixed(0)+'</span><br/>');
                                        }else{
                                            label.push('<span>'+dimensionNames[j]+':&nbsp;'+value.toFixed(2)+'</span><br/>');
                                        }
                                    }else{
                                        label.push("<div style='max-width:15em;word-break: break-all;white-space: normal;'>"+dimensionNames[j]+':&nbsp;'+value+"</div>");
                                    }
                                }
                            }else if(typeof(param['value'])=='number'){
                                if (param['value']%1==0){
                                    label.push("<span>"+param['value'].toFixed(0)+"</span><br/>");
                                }else{
                                    label.push("<span>"+param['value'].toFixed(2)+"</span><br/>");
                                }
                            }else if(param['value']){
                                label.push("<div style='max-width:15em;word-break:break-all;white-space: normal;'>"+value+"</div>");
                            }else{
                                label.push("<br/>");
                            }
                            var cardStr= label.join('');
                            labels.push(cardStr);
                            return labels.join('');
                        }"""),
            'textStyle': {'color': '#000'}
        }
    if symbol is not None:
        series['symbol'] = symbol
    series['dimensions'] = [x_field, y_field]
    series['data'] = df[[x_field, y_field]].values.tolist()
    if size_field is not None or color_field is not None:
        options['visualMap'] = []
    if size_field is not None:
        max_size_value = df[size_field].max() if size_min_max[1] is None else size_min_max[1]
        min_size_value = df[size_field].min() if size_min_max[0] is None else size_min_max[0]
        series['dimensions'].append(size_field)
        size_list = df[size_field].tolist()
        for i in range(0, len(size_list)):
            series['data'][i].append(size_list[i])
        visual_map_size = {
            'show': True,
            'orient': 'horizontal',
            'left': 'left',
            'bottom': 0,
            'calculable': True,
            'text': ['大', '小'],
            'dimension': len(series['dimensions']) - 1,
            'inRange': {
                'symbolSize': size_range
            }
        }
        if "date" in str(df[size_field].dtype) or "object" in str(df[size_field].dtype):
            visual_map_size['type'] = 'piecewise'
        else:
            visual_map_size['type'] = 'continuous'
            visual_map_size['min'] = min_size_value
            visual_map_size['max'] = max_size_value
        options['visualMap'].append(visual_map_size)

    if color_field is not None:
        series['dimensions'].append(color_field)
        color_list = df[color_field].tolist()
        for i in range(0, len(color_list)):
            series['data'][i].append(color_list[i])
        visual_map_color = {
            'show': True,
            'orient': 'horizontal',
            'left': 'right',
            'bottom': 0,
            'calculable': True,
            'text': ['高', '低'],
            'dimension': len(series['dimensions']) - 1,
            'inRange': {
                'color': color_sequence
            }
        }
        if "date" in str(df[color_field].dtype) or "object" in str(df[color_field].dtype):
            visual_map_color['type'] = 'piecewise'
        else:
            visual_map_color['type'] = 'continuous'
            visual_map_color['min'] = df[color_field].min()
            visual_map_color['max'] = df[color_field].max()
        options['visualMap'].append(visual_map_color)

    if info is not None:
        series['dimensions'].append(info)
        info_list = df[info].tolist()
        for i in range(0, len(info_list)):
            series['data'][i].append(info_list[i])
    options['series'].append(series)
    options['legend']['data'].append(title)
    options['toolbox'] = {
        'show': True,
        'feature': {
            'restore': {},
            'saveAsImage': {}
        }
    }
    return Echarts(options=options, width=width, height=height)


def line_echarts(data_frame: pd.DataFrame, x_field: str = None, y_field: str = None, series_field: str = None,
                 tooltip_trigger="axis",
                 title: str = "",
                 width: str = "100%", height: str = "500px") -> Echarts:
    """
    绘制线图
    :param data_frame: 必填 DataFrame
    :param x_field: 必填 x轴映射的列
    :param y_field: 必填 y轴映射的列
    :param series_field: 可选 series映射的列
    :param tooltip_trigger: axis item
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    options = copy.deepcopy(ECHARTS_BASE_GRID_OPTIONS)
    title = y_field if title == '' else title
    df = data_frame.copy()
    if x_field is None:
        df["x_col_echartspy"] = df.index
        x_field = "x_col_echartspy"
    options['title'] = {"text": title}
    if "date" in str(df[x_field].dtype) or "object" in str(df[x_field].dtype):
        options['xAxis']['type'] = 'category'
    if series_field is not None:
        series_list = list(df[series_field].unique())
        for s in series_list:
            series = {'name': s, 'type': 'line', 'dimensions': [x_field, y_field],
                      'data': df[df[series_field] == s][[x_field, y_field]].values.tolist(), 'emphasis': {
                    'itemStyle': {
                        'borderColor': "#333",
                        'borderWidth': 1,
                        'shadowColor': 'rgba(0, 0, 0, 0.5)',
                        'shadowBlur': 15
                    }
                }}
            options['legend']['data'].append(s)
            options['series'].append(series)
    else:
        series = {'name': title, 'type': 'line', 'dimensions': [x_field, y_field],
                  'data': df[[x_field, y_field]].values.tolist(), 'emphasis': {
                'itemStyle': {
                    'borderColor': "#333",
                    'borderWidth': 1,
                    'shadowColor': 'rgba(0, 0, 0, 0.5)',
                    'shadowBlur': 15
                }
            }}
        options['legend']['data'].append(title)
        options['series'].append(series)
    if tooltip_trigger == 'item':
        del options['axisPointer']
    options['tooltip'] = {
        'trigger': 'axis',
        'borderWidth': 1,
        'borderColor': '#ccc',
        'padding': 10,
        'color': "black",
        'backgroundColor': "rgba(255,255,255,0.8)",
        'formatter': Js("""
                function(params){
                    var dt = params[0]['axisValue'];
                    var labels = [];
                    labels.push('<b><span>时间:&nbsp;</span></b>' + dt + '<br/>');
                    params.sort(function(a, b) {
                      if (a.seriesName < b.seriesName ) {return -1;}
                      else if (a.seriesName > b.seriesName ) {return 1;}
                      else{ return 0;}
                    });
                    for (let i = 0; i < params.length; i++) {
                        const param = params[i];
                        var label=["<b><span>"+param['seriesName']+"("+param['seriesType']+"):&nbsp;</span></b>"];
                        var dimensionNames=param["dimensionNames"];
                        if (typeof(param['value'])=='object' && dimensionNames.length==param['data'].length){
                            label.push("<br/>");
                            for (let j = 1; j <dimensionNames.length; j++) {
                                    var value= param['data'][j];
                                    if (typeof(value)=='number'){
                                        if (value%1==0 || value>100000){
                                            label.push("<span>"+dimensionNames[j]+':&nbsp;'+value.toFixed(0)+"</span><br/>");
                                        }else{
                                            label.push("<span>"+dimensionNames[j]+':&nbsp;'+value.toFixed(2)+"</span><br/>");
                                        }
                                    }else{
                                        label.push("<div style='max-width:15em;word-break:break-all;white-space: normal;'>"+dimensionNames[j]+':&nbsp;'+value+"</div>");
                                    }
                            }
                        }else if(param['seriesType']=="candlestick"){
                                label.push("<br/>");
                                label.push("<span>open:&nbsp;"+param['data'][1].toFixed(2)+"</span><br/>");
                                label.push("<span>close:&nbsp;"+param['data'][2].toFixed(2)+"</span><br/>");
                                label.push("<span>high:&nbsp;"+param['data'][4].toFixed(2)+"</span><br/>");
                                label.push("<span>low:&nbsp;"+param['data'][3].toFixed(2)+"</span><br/>");   
                        }else if(typeof(param['value'])=='number'){
                            if (param['value']%1==0){
                                label.push("<span>"+param['value'].toFixed(0)+"</span><br/>");
                            }else{
                                label.push("<span>"+param['value'].toFixed(2)+"</span><br/>");
                            }
                        }else if(param['value']){
                            label.push("<div style='max-width:15em;word-break:break-all;white-space: normal;'>"+value+"</div>");
                        }else{
                            label.push("<br/>");
                        }
                        var cardStr= label.join('');
                        labels.push(cardStr);
                    }
                    return labels.join('');
                }"""),
        'textStyle': {'color': '#000'}
    }
    options['toolbox'] = {
        'show': True,
        'feature': {
            'restore': {},
            'saveAsImage': {}
        }
    }

    return Echarts(options=options, width=width, height=height)


def bar_echarts(data_frame: pd.DataFrame, x_field: str = None, y_field: str = None, series_field: str = None,
                stack: str = "all",
                tooltip_trigger="axis",
                title: str = "",
                width: str = "100%", height: str = "500px") -> Echarts:
    """

    :param data_frame: 必填 DataFrame
    :param x_field: 必填 x轴映射的列
    :param y_field: 必填 y轴映射的列
    :param series_field: 选填 series 对应列
    :param stack:堆叠分组
    :param tooltip_trigger: axis item
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:Echarts
    """
    options = copy.deepcopy(ECHARTS_BASE_GRID_OPTIONS)
    df = data_frame.copy()
    title = y_field if title == '' else title
    if x_field is None:
        df["x_col_echartspy"] = df.index
        x_field = "x_col_echartspy"
    options['title'] = {"text": title}
    if "date" in str(df[x_field].dtype) or "object" in str(df[x_field].dtype):
        options['xAxis']['type'] = 'category'
    if series_field is not None:
        series_list = list(df[series_field].unique())
        for s in series_list:
            series = {'name': s, 'type': 'bar', 'stack': stack, 'dimensions': [x_field, y_field], 'sampling': 'lttb',
                      'data': df[df[series_field] == s][[x_field, y_field]].values.tolist(), 'emphasis': {
                    'itemStyle': {
                        'borderColor': "#333",
                        'borderWidth': 1,
                        'shadowColor': 'rgba(0, 0, 0, 0.5)',
                        'shadowBlur': 15
                    }
                }}
            options['legend']['data'].append(s)
            options['series'].append(series)
    else:
        series = {'name': title, 'type': 'bar', 'stack': stack, 'dimensions': [x_field, y_field], 'sampling': 'lttb',
                  'data': df[[x_field, y_field]].values.tolist(), 'emphasis': {
                'itemStyle': {
                    'borderColor': "#333",
                    'borderWidth': 1,
                    'shadowColor': 'rgba(0, 0, 0, 0.5)',
                    'shadowBlur': 15
                }
            }}
        options['legend']['data'].append(title)
        options['series'].append(series)
    if tooltip_trigger == 'item':
        del options['axisPointer']
        options['tooltip'] = {
            'trigger': 'item',
            'borderWidth': 1,
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)",
            'borderColor': '#ccc',
            'padding': 10,
            'formatter': Js("""
                                function(params){
                                    window.params=params;
                                    var labels = [];
                                    const param = params;
                                    var label=['<b><span>'+param['seriesName']+'('+param['seriesType']+'):&nbsp;</span></b>'];
                                    var dimensionNames=param['dimensionNames'];
                                    if (typeof(param['value'])=='object' && dimensionNames.length>=param['data'].length){
                                        label.push("<br/>");
                                        for (let j = 0; j <param['data'].length; j++) {
                                            var value= param['value'][j];
                                            if (typeof(value)=='number'){
                                                if (value%1==0 || value>100000){
                                                    label.push('<span>'+dimensionNames[j]+':&nbsp;'+value.toFixed(0)+'</span><br/>');
                                                }else{
                                                    label.push('<span>'+dimensionNames[j]+':&nbsp;'+value.toFixed(2)+'</span><br/>');
                                                }
                                            }else{
                                                label.push("<div style='max-width:15em;word-break: break-all;white-space: normal;'>"+dimensionNames[j]+':&nbsp;'+value+"</div>");
                                            }
                                        }
                                    }else if(typeof(param['value'])=='number'){
                                        if (param['value']%1==0){
                                            label.push("<span>"+param['value'].toFixed(0)+"</span><br/>");
                                        }else{
                                            label.push("<span>"+param['value'].toFixed(2)+"</span><br/>");
                                        }
                                    }else if(param['value']){
                                        label.push("<div style='max-width:15em;word-break:break-all;white-space: normal;'>"+value+"</div>");
                                    }else{
                                        label.push("<br/>");
                                    }
                                    var cardStr= label.join('');
                                    labels.push(cardStr);
                                    return labels.join('');
                                }"""),
            'textStyle': {'color': '#000'}
        }
    options['toolbox'] = {
        'show': True,
        'feature': {
            'restore': {},
            'saveAsImage': {}
        }
    }
    return Echarts(options=options, width=width, height=height)


def pie_echarts(data_frame: pd.DataFrame, name_field: str = None, value_field: str = None, rose_type: str = None,
                title: str = "",
                width: str = "100%", height: str = "500px") -> Echarts:
    """
    饼图
    :param data_frame: 必填 DataFrame
    :param name_field: name列名
    :param value_field: value列名
    :param rose_type: radius/area/None
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    df = data_frame[[name_field, value_field]].sort_values(name_field, ascending=True).copy()
    df.columns = ['name', 'value']
    options = {
        'title': {
            'text': title,
        },
        'tooltip': {
            'trigger': 'item',
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)",
            'formatter': '{a} <br/>{b} : {c} ({d}%)'
        },
        'toolbox': {
            'show': True,
            'feature': {
                'restore': {},
                'saveAsImage': {}
            }
        },
        'legend': {
            'left': 'center',
            'type': 'scroll',
            'show': True,
            'top': 'top',
            'data': list(df['name'].unique())
        },
        'series': [
            {
                'name': title,
                'type': 'pie',
                'radius': [20, 140],
                'center': ['25%', '50%'],
                'roseType': rose_type if rose_type in ['area', 'radius'] else False,
                'itemStyle': {
                    'borderRadius': 5
                },
                'label': {
                    'show': False
                },
                'emphasis': {
                    'itemStyle': {
                        'borderColor': "#333",
                        'borderWidth': 1
                    },
                    'label': {
                        'show': True
                    }
                },
                'data': df[['name', 'value']].to_dict(orient="records")
            }
        ]
    }
    return Echarts(options=options, width=width, height=height)


def candlestick_echarts(data_frame: pd.DataFrame, time_field: str = 'time', open_field: str = "open",
                        high_field: str = 'high',
                        low_field: str = 'low',
                        close_field: str = 'close',
                        volume_field: str = 'volume', mas: list = [5, 10, 30], log_y: bool = True, title: str = "",
                        width: str = "100%", height: str = "600px", left_padding: str = '5%',
                        right_padding: str = '3%') -> Echarts:
    """
    绘制K线
    :param data_frame:
    :param time_field: 时间列名, 如果指定的列不存在，使用index作为time
    :param open_field: open列名
    :param high_field: high列名
    :param low_field: low列名
    :param close_field: close列名
    :param volume_field: volume列名
    :param mas: 均线组
    :param log_y: y轴 log分布 底为1.1 一个格子对应10%
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :param left_padding: 左侧padding宽度
    :param right_padding: 右侧padding宽度
    :return:
    """
    df = data_frame.copy()
    if time_field not in data_frame.columns:  # 使用index作为时间
        df[time_field] = df.index
    df[close_field] = df[close_field].fillna(method="ffill")
    df[open_field] = df[open_field].fillna(df[close_field])
    df[high_field] = df[high_field].fillna(df[close_field])
    df[low_field] = df[low_field].fillna(df[close_field])
    df[volume_field] = df[volume_field].fillna(0)
    volumes = (df[volume_field]).round(2).tolist()
    vol_filter = (df[volume_field]).quantile([0.05, 0.95]).values
    bar_items = [({"value": vol} if vol >= vol_filter[0] and vol <= vol_filter[1] else (
        {"value": vol, "itemStyle": {"color": "red"}} if vol > vol_filter[1] else {"value": vol,
                                                                                   "itemStyle": {"color": "green"}}))
                 for vol in volumes]

    options = {
        'animation': False,
        'title': {'text': title},
        'legend': {'top': 10, 'left': 'center', 'data': [title]},
        'tooltip': {
            'trigger': 'axis', 'axisPointer': {'type': 'cross'},
            'borderWidth': 1,
            'borderColor': '#ccc',
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)",
            'padding': 10,
            'formatter': Js("""
                function(params){
                    var dt = params[0]['axisValue'];
                    var labels = [];
                    labels.push('<b><span>时间:&nbsp;</span></b>' + dt + '<br/>');
                    params.sort(function(a, b) {
                      if (a.seriesName < b.seriesName ) {return -1;}
                      else if (a.seriesName > b.seriesName ) {return 1;}
                      else{ return 0;}
                    });
                    for (let i = 0; i < params.length; i++) {
                        const param = params[i];
                        var label=["<b><span>"+param['seriesName']+"("+param['seriesType']+"):&nbsp;</span></b>"];
                        var dimensionNames=param["dimensionNames"];
                        if (typeof(param['value'])=='object' && dimensionNames.length==param['data'].length){
                            label.push("<br/>");
                            for (let j = 1; j <dimensionNames.length; j++) {
                                    var value= param['data'][j];
                                    if (typeof(value)=='number'){
                                        if (value%1==0 || value>100000){
                                            label.push("<span>"+dimensionNames[j]+':&nbsp;'+value.toFixed(0)+"</span><br/>");
                                        }else{
                                            label.push("<span>"+dimensionNames[j]+':&nbsp;'+value.toFixed(2)+"</span><br/>");
                                        }
                                    }else{
                                        label.push("<div style='max-width:15em;word-break:break-all;white-space: normal;'>"+dimensionNames[j]+':&nbsp;'+value+"</div>");
                                    }
                            }
                        }else if(param['seriesType']=="candlestick"){
                                label.push("<br/>");
                                label.push("<span>open:&nbsp;"+param['data'][1].toFixed(2)+"</span><br/>");
                                label.push("<span>close:&nbsp;"+param['data'][2].toFixed(2)+"</span><br/>");
                                label.push("<span>high:&nbsp;"+param['data'][4].toFixed(2)+"</span><br/>");
                                label.push("<span>low:&nbsp;"+param['data'][3].toFixed(2)+"</span><br/>");   
                        }else if(typeof(param['value'])=='number'){
                            if (param['value']%1==0){
                                label.push("<span>"+param['value'].toFixed(0)+"</span><br/>");
                            }else{
                                label.push("<span>"+param['value'].toFixed(2)+"</span><br/>");
                            }
                        }else if(param['value']){
                            label.push("<div style='max-width:15em;word-break:break-all;white-space: normal;'>"+value+"</div>");
                        }else{
                            label.push("<br/>");
                        }
                        var cardStr= label.join('');
                        labels.push(cardStr);
                    }
                    return labels.join('');
                }"""),
            'textStyle': {'color': '#000'},
            'position': Js("""
                function (pos, params, el, elRect, size){
                    var obj = {top: 10};
                    obj[['left', 'right'][+(pos[0] < size.viewSize[0] / 2)]] = 30;
                    return obj;
                }
            """)
        },
        'axisPointer': {
            'link': {'xAxisIndex': 'all'},
            'label': {'backgroundColor': '#777'}
        },
        'toolbox': {
            'show': True,
            'feature': {
                'restore': {},
                'saveAsImage': {}
            }
        },
        'grid': [
            {'left': left_padding, 'right': right_padding, 'height': '70%'},
            {'left': left_padding, 'right': right_padding, 'top': '71%', 'height': '16%'}
        ],
        'xAxis': [
            {
                'type': 'category',
                'data': df[time_field].tolist(),
                'scale': True,
                'boundaryGap': False,
                'axisLine': {'show': False},
                'axisLabel': {'show': False},
                'axisTick': {'show': False},
                'splitLine': {'show': True},
                'splitNumber': 20,
                'min': 'dataMin',
                'max': 'dataMax',
                'axisPointer': {
                    'z': 100
                }
            },
            {
                'type': 'category',
                'gridIndex': 1,
                'data': df[time_field].tolist(),
                'scale': True,
                'boundaryGap': False,
                'axisLine': {'onZero': False, 'show': True},
                'axisLine': {'show': True},
                'axisLabel': {'show': True},
                'axisTick': {'show': True},
                'splitLine': {'show': True},
                'axisLabel': {'show': True},
                'splitNumber': 20,
                'min': 'dataMin',
                'max': 'dataMax'
            }
        ],
        'yAxis': [
            {
                'scale': True,
                'type': 'log' if log_y else 'value',
                'logBase': 1.1,
                'splitNumber': 10,
                'axisLabel': {'show': True,
                              'formatter': Js("""
                               function(value,index){
                                   return value.toFixed(2);
                               }
                             """)},
                'axisLine': {'show': False},
                'axisTick': {'show': True},
                'splitLine': {'show': True}
            },
            {
                'scale': True,
                'gridIndex': 1,
                'splitNumber': 2,
                'axisLabel': {'show': True,
                              'formatter': Js("""
                                function(value,index){
                                    var si = [
                                        { value: 1, symbol: "" },
                                        { value: 1E3, symbol: "K" },
                                        { value: 1E6, symbol: "M" },
                                        { value: 1E9, symbol: "G" },
                                        { value: 1E12, symbol: "T" },
                                        { value: 1E15, symbol: "P" },
                                        { value: 1E18, symbol: "E" }
                                    ];
                                    var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
                                    var i;
                                    for (i = si.length - 1; i > 0; i--) {
                                        if (value >= si[i].value) {
                                            break;
                                        }
                                    }
                                    return (value / si[i].value).toFixed(2).replace(rx, "$1") + si[i].symbol;
                                }
                              """)
                              },
                'axisLine': {'show': False},
                'axisTick': {'show': False},
                'splitLine': {'show': False}
            }
        ],
        'dataZoom': [
            {
                'type': 'inside',
                'xAxisIndex': [0, 1],
                'start': 0,
                'end': 100
            }
        ],
        'series': [
            {
                'name': title,
                'type': 'candlestick',
                'data': df[[open_field, close_field, low_field, high_field]].values.tolist(),
                'emphasis': {
                    'itemStyle': {
                        'borderColor': "#333",
                        'borderWidth': 1,
                        'shadowColor': 'rgba(0, 0, 0, 0.5)',
                        'shadowBlur': 15
                    }
                }
            },
            {
                'name': 'Volume',
                'type': 'bar',
                'xAxisIndex': 1,
                'yAxisIndex': 1,
                'data': bar_items,
                'emphasis': {
                    'itemStyle': {
                        'borderColor': "#333",
                        'borderWidth': 1,
                        'shadowColor': 'rgba(0, 0, 0, 0.5)',
                        'shadowBlur': 15
                    }
                }
            }
        ]
    }
    for ma_len in mas:
        name = "MA" + str(ma_len)
        df[name] = df[close_field].rolling(ma_len).mean().round(2)
        series_ma = {
            'name': name,
            'type': 'line',
            'data': df[name].tolist(),
            'smooth': True,
            'showSymbol': False,
            'lineStyle': {'opacity': 0.5}
        }
        options['series'].append(series_ma)
        options['legend']['data'].append(name)
    return Echarts(options=options, width=width, height=height)


def heatmap_echarts(data_frame: pd.DataFrame, x_field: str = None, y_field: str = None, color_field: str = None,
                    label_field: str = None,
                    x_axis_data: list = None,
                    y_axis_data: list = None,
                    color_sequence: list = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf", "#fee090",
                                            "#fdae61", "#f46d43", "#d73027", "#a50026"],
                    label_show=True, label_font_size=8,
                    title: str = "",
                    width: str = "100%", height: str = "500px") -> Echarts:
    """
    二维热度图

    :param data_frame: 必填 DataFrame
    :param x_field: 必填 x轴映射的列
    :param y_field: 必填 y轴映射的列
    :param color_field: color映射列
    :param label_field: label映射列 必须是数字类型
    :param y_axis_data: x轴顺序 不提供直接按值排序
    :param x_axis_data: y轴顺序 不提供直接按值排序
    :param color_sequence: color色卡序列
    :param label_font_size: 8
    :param label_show: 是否显示label
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    label_field = color_field if label_field is None else label_field
    df = data_frame[[x_field, y_field, label_field, color_field]].copy()
    df[x_field] = df[x_field].astype(str)
    df[y_field] = df[y_field].astype(str)
    df.columns = [x_field, y_field, label_field + '_label', color_field + '_color']
    options = {
        'title': {'text': title},
        'tooltip': {
            'position': 'top',
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)",
            'formatter': "{c}"
        },
        'toolbox': {
            'show': True,
            'feature': {
                'restore': {},
                'saveAsImage': {}
            }
        },
        'xAxis': [{
            'type': 'value',
            'data': [str(v) for v in sorted(df[x_field].unique())] if x_axis_data is None else x_axis_data,
            'splitArea': {
                'show': True
            }
        }, {
            'type': 'value',
            'data': [str(v) for v in sorted(df[x_field].unique())] if x_axis_data is None else x_axis_data,
            'splitArea': {
                'show': True
            }
        }],
        'yAxis': {
            'type': 'value',
            'data': [str(v) for v in sorted(df[y_field].unique())] if y_axis_data is None else y_axis_data,
            'splitArea': {
                'show': True
            }
        },
        'visualMap': {
            'min': df[color_field + '_color'].min(),
            'max': df[color_field + '_color'].max(),
            'calculable': True,
            'orient': 'horizontal',
            'left': 'center',
            'bottom': '0',
            'dimension': 3,
            'inRange': {
                'color': color_sequence
            }

        },
        'series': [{
            'name': title,
            'type': 'heatmap',
            'data': df.values.tolist(),
            'label': {
                'show': label_show,
                'fontSize': label_font_size
            },
            'emphasis': {
                'itemStyle': {
                    'shadowBlur': 15,
                    'shadowColor': 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    }
    if "date" in str(df[x_field].dtype) or "object" in str(df[x_field].dtype):
        options['xAxis'][0]['type'] = 'category'
        options['xAxis'][1]['type'] = 'category'
    if "date" in str(df[y_field].dtype) or "object" in str(df[y_field].dtype):
        options['yAxis']['type'] = 'category'
    return Echarts(options=options, width=width, height=height)


def radar_echarts(data_frame: pd.DataFrame, name_field: str = None, indicator_field_list: list = None,
                  fill: bool = True,
                  title: str = "",
                  width: str = "100%", height: str = "500px") -> Echarts:
    """

    :param data_frame:
    :param name_field: name列
    :param indicator_field_list: indicators所有列名list
    :param fill: 是否填充背景色
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    options = {
        'title': {
            'text': title
        },
        'legend': {
            'top': 20,
            'type': 'scroll',
            'data': []
        },
        'radar': {
            'center': ['50%', '55%'],
            'shape': 'circle',
            'indicator': []
        },
        'tooltip': {
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)",
        },
        'toolbox': {
            'show': True,
            'feature': {
                'restore': {},
                'saveAsImage': {}
            }
        },
        'series': [{
            'name': title,
            'type': 'radar',
            'emphasis': {
                'lineStyle': {
                    "shadowBlur": 15,
                    "width": 6,
                    "type": 'dotted',
                    "shadowOffsetX": 0,
                    "shadowColor": 'rgba(0, 0, 0, 0.9)',
                    "opacity": 1
                },
                'inactiveOpacity': 0.05
            },
            'data': []
        }]
    }
    df = data_frame[[name_field] + indicator_field_list].copy()
    if fill:
        options['series'][0]['areaStyle'] = {'opacity': 0.1}
    indicator_max_dict = df[indicator_field_list].max().to_dict()
    options['radar']['indicator'] = [{'name': key, "max": indicator_max_dict[key]} for key in indicator_max_dict.keys()]
    for record in df.to_dict(orient='records'):
        data = {
            'value': [record[indicator] for indicator in indicator_field_list],
            'name': record[name_field]
        }
        options['series'][0]['data'].append(data)
        options['legend']['data'].append(record[name_field])
    return Echarts(options=options, width=width, height=height)


def calendar_heatmap_echarts(data_frame: pd.DataFrame, date_field: str = None, value_field: str = None,
                             title: str = "",
                             width: str = "100%", height: str = "300px") -> Echarts:
    """
    日历热度图，显示日期热度
    :param data_frame:
    :param date_field: 日期列
    :param value_field: 值列
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    df = data_frame[[date_field, value_field]].copy()
    value_max = df[value_field].max()
    value_min = df[value_field].min()
    date_start = pd.to_datetime(df[date_field].min()).strftime("%Y-%m-%d")
    date_end = pd.to_datetime(df[date_field].max()).strftime("%Y-%m-%d")
    df[date_field] = pd.to_datetime(df[date_field]).dt.strftime("%Y-%m-%d")
    options = {
        'title': {
            'text': title
        },
        'tooltip': {
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)",
            'formatter': "{c}"
        },
        'toolbox': {
            'show': True,
            'feature': {
                'restore': {},
                'saveAsImage': {}
            }
        },
        'visualMap': {
            'text': ['高', '低'],
            'min': value_min,
            'max': value_max,
            'type': 'continuous',
            'orient': 'horizontal',
            'inRange': {
                'color': ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf", "#fee090", "#fdae61",
                          "#f46d43", "#d73027", "#a50026"]
            },
            'left': 'center',
            'top': 0,
            'hoverLink': True
        },
        'calendar': {
            'top': 60,
            'left': 30,
            'right': 30,
            'cellSize': ['auto', 'auto'],
            'range': [date_start, date_end],
            'itemStyle': {
                'borderWidth': 0.5
            },
            'dayLabel': {
                'firstDay': 1
            },
            'monthLabel': {
                'nameMap': 'cn'
            },
            'yearLabel': {'show': True}
        },
        'series': {
            'type': 'heatmap',
            'coordinateSystem': 'calendar',
            'emphasis': {
                'itemStyle': {
                    'borderColor': "#333",
                    'borderWidth': 1,
                    'shadowColor': 'rgba(0, 0, 0, 0.5)',
                    'shadowBlur': 15
                }
            },
            'data': df[[date_field, value_field]].values.tolist()
        }
    }
    return Echarts(options=options, width=width, height=height)


def parallel_echarts(data_frame: pd.DataFrame, name_field: str = None, indicator_field_list: list = [],
                     title: str = "",
                     width: str = "100%", height: str = "500px") -> Echarts:
    """
    平行坐标图,要求name列每行唯一 比如：显示每个报告期各财务指标
    :param data_frame:
    :param name_field: name列
    :param indicator_field_list: 数据维度列list
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    df = data_frame[list(set([name_field] + indicator_field_list))].copy()
    dims = str(indicator_field_list)
    options = {
        'title': {'text': title},
        'legend': {
            'top': '20',
            'type': 'scroll',
            'data': []
        },
        'toolbox': {
            'show': True,
            'feature': {
                'restore': {},
                'saveAsImage': {}
            }
        },
        'parallel': {'top': 80},
        'tooltip': {
            'trigger': 'item',
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)",
            'formatter': Js(f""" function(params){{
                    var dims={dims};
                    var value_dict={{}};
                    var labels=[params.seriesName+':<br/>'];
                    for(var i=0;i<dims.length;i++){{
                        labels.push('<span>'+dims[i]+":"+params['value'][i]+'</span><br/>');
                    }}
                    return labels.join("");
            }}"""),
            'position': Js("""
                function (pos, params, el, elRect, size){
                    var obj = {top: 20};
                    obj[['left', 'right'][+(pos[0] < size.viewSize[0] / 2)]] = 30;
                    return obj;
                }
            """)},
        'parallelAxis': [],
        'series': []
    }
    value_dict_list = df.to_dict(orient='records')
    for i in range(0, len(indicator_field_list)):
        data_min = df[indicator_field_list[i]].min()
        data_max = df[indicator_field_list[i]].max()
        if 'int' in str(df[indicator_field_list[i]].dtype) or 'float' in str(df[indicator_field_list[i]].dtype):
            col = {
                'dim': i,
                'name': indicator_field_list[i],
                'type': 'value',
                'min': round(data_min - (data_max - data_min) * 0.1, 2),
                'max': round(data_max + (data_max - data_min) * 0.1, 2)
            }
        else:
            col = {'dim': i, 'name': indicator_field_list[i], 'type': 'category',
                   'data': sorted(df[indicator_field_list[i]].unique())}

        options['parallelAxis'].append(col)
    for value_dict in value_dict_list:
        series = {
            'name': value_dict[name_field],
            'type': 'parallel',
            'lineStyle': {'width': 2},
            'emphasis': {
                'lineStyle': {
                    'width': 5,
                    'borderColor': "black",
                    'borderWidth': 2,
                    'shadowColor': 'rgba(0, 0, 0, 1)',
                    'shadowBlur': 15
                }
            },
            'data': [[value_dict[col] for col in indicator_field_list]]
        }

        options['series'].append(series)
        options['legend']['data'].append(value_dict[name_field])
    return Echarts(options=options, width=width, height=height)


def sankey_echarts(data_frame: pd.DataFrame, source_field: str = None, target_field: str = None,
                   value_field: str = None, source_depth_field: str = None, target_depth_field: str = None,
                   title: str = "",
                   width: str = "100%", height: str = "500px") -> Echarts:
    """


    :param data_frame:
    :param source_field: source列
    :param target_field: target列
    :param value_field: value列
    :param source_depth_field:
    :param target_depth_field:
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    names = list(
        set(data_frame[source_field].dropna().unique()).union(set(data_frame[target_field].dropna().unique())))
    depth_dict = {}
    if source_depth_field is not None:
        depth_dict.update(
            data_frame[[source_field, source_depth_field]].drop_duplicates(subset=[source_field]).dropna(
                subset=[source_field]).set_index(
                source_field)[source_depth_field].to_dict())
    if target_depth_field is not None:
        depth_dict.update(
            data_frame[[target_field, target_depth_field]].drop_duplicates(subset=[target_field]).dropna(
                subset=[target_field]).set_index(
                target_field)[target_depth_field].to_dict())

    df = data_frame.rename(columns={source_field: "source", target_field: 'target', value_field: 'value'})
    options = {
        'title': {
            'text': title,
            'left': 'center'
        },
        'tooltip': {
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)"
        },
        'toolbox': {
            'show': True,
            'feature': {
                'restore': {},
                'saveAsImage': {}
            }
        },
        'series': [{
            'type': 'sankey',
            'data': [{'name': name} for name in names] if len(depth_dict) == 0 else [
                {'name': name, 'depth': depth_dict[name] if name in depth_dict else 0} for name in names],
            'links': df[['source', 'target', 'value']].dropna().to_dict(orient='records'),
            'lineStyle': {
                'color': 'source',
                'curveness': 0.5
            },
            'emphasis': {
                'focus': 'adjacency',
                'itemStyle': {
                    'borderColor': "#333",
                    'borderWidth': 1,
                    'shadowColor': 'rgba(0, 0, 0, 0.5)',
                    'shadowBlur': 15
                }
            },
            'label': {
                'color': 'rgba(0,0,0,0.7)',
                'fontFamily': 'Arial',
                'fontSize': 10
            }
        }]
    }
    return Echarts(options=options, width=width, height=height)


def theme_river_echarts(data_frame: pd.DataFrame, date_field: str = None, value_field: str = None,
                        theme_field: str = None,
                        title: str = "",
                        width: str = "100%", height: str = "500px") -> Echarts:
    """

    :param data_frame:
    :param date_field: date列
    :param value_field: value列
    :param theme_field: theme列
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    df = data_frame[[date_field, value_field, theme_field]].copy()
    options = {
        'title': {'text': title},
        'tooltip': {
            'trigger': 'axis',
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)",
            'axisPointer': {'type': 'cross'}
        },
        'toolbox': {
            'show': True,
            'feature': {
                'restore': {},
                'saveAsImage': {}
            }
        },
        'legend': {
            'top': 40,
            'data': list(df[theme_field].unique())
        },
        'singleAxis': {
            'top': 50,
            'bottom': 50,
            'axisTick': {},
            'axisLabel': {},
            'type': 'time',
            'splitLine': {
                'show': True,
                'lineStyle': {
                    'type': 'dashed',
                    'opacity': 0.2
                }
            }
        },
        'series': [
            {
                'type': 'themeRiver',
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 20,
                        'shadowColor': 'rgba(0, 0, 0, 0.8)'
                    }
                },
                'data': df.values.tolist()
            }
        ]
    }
    return Echarts(options=options, width=width, height=height)


def sunburst_echarts(data_frame: pd.DataFrame, category_field_list: list = [], value_field: str = None,
                     title: str = "",
                     font_size: int = 8, node_click=False,
                     width: str = "100%", height: str = "500px") -> Echarts:
    data = Tools.df2tree(data_frame, category_field_list, value_field)
    options = {
        'title': {
            'text': title,
        },
        'tooltip': {
            'trigger': 'item',
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)",
            'formatter': Js("""
                function(params){
                    var pathInfo= params['treePathInfo'];
                    var labels = [];
                    for(var i=0; i<pathInfo.length; i++){
                        labels.push(pathInfo[i].name +':'+ pathInfo[i].value + '<br/>');
                    }
                    return labels.join('');
                }
        """)

        },
        'toolbox': {
            'show': True,
            'feature': {
                'restore': {},
                'saveAsImage': {}
            }
        },
        'series': {
            'type': 'sunburst',
            'nodeClick': node_click,
            'label': {'fontSize': font_size},
            'data': data,
            'radius': [0, '95%'],
            'emphasis': {
                'focus': 'ancestor',
                'itemStyle': {
                    'borderColor': "#333",
                    'borderWidth': 1,
                    'shadowColor': 'rgba(0, 0, 0, 0.5)',
                    'shadowBlur': 15
                }
            }
        }
    }
    return Echarts(options, height=height, width=width)


def mark_area_echarts(data_frame: pd.DataFrame, x1: str, y1: str, x2: str, y2: str, label: str, title: str = 'area',
                      label_position: str = "top", label_font_size: int = 10, label_distance: int = 10,
                      label_font_color: str = 'inherit', fill_color: str = "inherit", fill_opacity: float = 0.3
                      ):
    """
    在现有图表上叠加矩形，不能单独显示
    :param data_frame:
    :param x1: 左上方顶点x坐标对应列
    :param y1: 左上方顶点y坐标对应列
    :param x2: 右下方顶点x坐标对应列
    :param y2: 右下方顶点y坐标对应列
    :param label: 矩形标签文字对应列
    :param title: 用于在legend显示，控制叠加矩形显示隐藏
    :param label_position:top / left / right / bottom / inside / insideLeft / insideRight / insideTop / insideBottom / insideTopLeft / insideBottomLeft / insideTopRight / insideBottomRight
    :param label_distance:
    :param label_font_size:
    :param label_font_color:
    :param fill_opacity:
    :param fill_color:

    :return:
    """
    options = copy.deepcopy(ECHARTS_BASE_OVERLAY_OPTIONS)
    rows = data_frame[[x1, y1, x2, y2, label]].to_dict(orient='records')
    data = [[{'name': row[label], 'coord': [row[x1], row[y1]]},
             {'coord': [row[x2], row[y2]]}] for row in rows]
    base_mark_area_options = {
        'itemStyle': {
            'opacity': fill_opacity
        },
        'tooltip': {
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)"
        },
        'label': {
            'show': True,
            'position': label_position,
            'distance': label_distance,
            'fontSize': label_font_size,
            'color': label_font_color
        },
        'data': data
    }
    options['series'][0]['name'] = title
    options['series'][0]['markArea'] = base_mark_area_options
    options['legend']['data'] = [title]
    return Echarts(options)


def mark_segment_echarts(data_frame: pd.DataFrame, x1: str, y1: str, x2: str, y2: str, label: str, title="segment",
                         show_label: bool = False,
                         label_position: str = "middle", label_font_size: int = 10, label_distance: int = 10,
                         label_font_color: str = 'inherit', symbol_start: str = 'circle', symbol_end: str = 'circle',
                         line_width: int = 2, line_type: str = "solid"):
    """
    在现有图表上叠加线段，不能单独显示

    :param data_frame:
    :param x1: 左上方顶点x坐标对应列
    :param y1: 左上方顶点y坐标对应列
    :param x2: 右下方顶点x坐标对应列
    :param y2: 右下方顶点y坐标对应列
    :param label: 矩形标签文字对应列
    :param title: 用于在legend显示，控制叠加矩形显示隐藏
    :param show_label: 是否显示label
    :param label_position:top / left / right / bottom / inside / insideLeft / insideRight / insideTop / insideBottom / insideTopLeft / insideBottomLeft / insideTopRight / insideBottomRight
    :param label_distance: 10
    :param label_font_color:inherit
    :param label_font_size:12
    :param symbol_start:circle
    :param symbol_end:circle
    :param line_type: solid/dashed/dotted
    :param line_width: 2
    :param line_color: inherit
    :return:
    """
    options = copy.deepcopy(ECHARTS_BASE_OVERLAY_OPTIONS)
    if show_label:
        rows = data_frame[[x1, y1, x2, y2, label]].to_dict(orient='records')
        data = [[{'name': str(row[label]), 'coord': [row[x1], row[y1]]},
                 {'coord': [row[x2], row[y2]]}] for row in rows]
    else:
        rows = data_frame[[x1, y1, x2, y2]].to_dict(orient='records')
        data = [[{'coord': [row[x1], row[y1]]},
                 {'coord': [row[x2], row[y2]]}] for row in rows]

    base_mark_line_options = {
        'symbol': [symbol_start, symbol_end],
        'label': {
            'show': show_label,
            'position': label_position,
            'distance': label_distance,
            'fontSize': label_font_size,
            'color': label_font_color
        },
        'lineStyle': {
            'width': line_width,
            'type': line_type
        },
        'data': data
    }
    options['series'][0]['name'] = title
    options['series'][0]['markLine'] = base_mark_line_options
    options['legend']['data'] = [title]
    return Echarts(options)


def mark_label_echarts(data_frame: pd.DataFrame, x: str, y: str, label: str, title="point",
                       label_position: str = "top", label_font_size: int = 10, label_distance: int = 10,
                       label_font_color: str = 'inherit', label_background_color: str = "transparent"):
    """
    在现有图表上叠加标签，不能单独显示
    :param data_frame:
    :param x: 左上方顶点x坐标对应列
    :param y: 左上方顶点y坐标对应列
    :param label: 矩形标签文字对应列
    :param title: 用于在legend显示，控制叠加矩形显示隐藏
    :param label_position:top / left / right / bottom / inside / insideLeft / insideRight / insideTop / insideBottom / insideTopLeft / insideBottomLeft / insideTopRight / insideBottomRight
    :param label_distance: 10
    :param label_font_color:inherit
    :param label_font_size:12
    :param label_background_color:transparent
    :return:
    """
    options = copy.deepcopy(ECHARTS_BASE_OVERLAY_OPTIONS)
    rows = data_frame[[x, y, label]].to_dict(orient='records')
    data = [{'value': row[label], 'coord': [row[x], row[y]]} for row in rows]
    base_mark_point_options = {
        'symbol': 'circle',
        'symbolSize': 0,
        'label': {
            'show': True,
            'position': label_position,
            'distance': label_distance,
            'fontSize': label_font_size,
            'color': label_font_color,
            'backgroundColor': label_background_color,
            'padding': 2

        },
        'data': data
    }
    options['series'][0]['markPoint'] = base_mark_point_options
    options['series'][0]['name'] = title
    options['legend']['data'] = [title]
    return Echarts(options)


def mark_vertical_line_echarts(data_frame: pd.DataFrame, x: str, label: str, title="vertical_line",
                               label_position: str = 'middle', label_font_size: int = 10, label_distance: int = 10,
                               label_font_color: str = 'inherit'):
    """
    在现有图表上叠加竖线，不能单独显示
    :param data_frame:
    :param x:
    :param label:
    :param title:
    :param label_position: 'start', 'middle', 'end', 'insideStartTop', 'insideStartBottom', 'insideMiddleTop', 'insideMiddleBottom', 'insideEndTop', 'insideEndBottom'
    :param label_font_color: inherit
    :param label_distance: 10
    :param label_font_size: 10
    :return:
    """
    options = copy.deepcopy(ECHARTS_BASE_OVERLAY_OPTIONS)
    rows = data_frame[[x, label]].to_dict(orient='records')
    data = [{'name': row[label], 'xAxis': row[x]} for row in rows]
    base_mark_line_options = {
        'label': {
            'position': label_position,
            'distance': label_distance,
            'fontSize': label_font_size,
            'color': label_font_color,
            'show': True,
            'formatter': "{b}"
        },
        'symbol': [None, None],
        'data': data
    }
    options['series'][0]['markLine'] = base_mark_line_options
    options['legend']['data'] = [title]
    options['series'][0]['name'] = title
    return Echarts(options)


def mark_horizontal_line_echarts(data_frame: pd.DataFrame, y: str, label: str, title="vertical_line",
                                 label_position: str = 'middle', label_font_size: int = 10, label_distance: int = 10,
                                 label_font_color: str = 'inherit'):
    """
    在现有图表上叠加横线，不能单独显示
    :param data_frame:
    :param y:
    :param label:
    :param title:
    :param label_position: 'start', 'middle', 'end', 'insideStartTop', 'insideStartBottom', 'insideMiddleTop', 'insideMiddleBottom', 'insideEndTop', 'insideEndBottom'
    :param label_font_color: inherit
    :param label_distance: 10
    :param label_font_size: 10
    :return:
    """
    options = copy.deepcopy(ECHARTS_BASE_OVERLAY_OPTIONS)
    rows = data_frame[[y, label]].to_dict(orient='records')
    data = [{'name': row[label], 'yAxis': row[y]} for row in rows]
    base_mark_line_options = {
        'label': {
            'position': label_position,
            'distance': label_distance,
            'fontSize': label_font_size,
            'color': label_font_color,
            'show': True,
            'formatter': "{b}"
        },
        'symbol': [None, None],
        'data': data
    }
    options['series'][0]['markLine'] = base_mark_line_options
    options['legend']['data'] = [title]
    options['series'][0]['name'] = title
    return Echarts(options)


def scatter3d_echarts(data_frame: pd.DataFrame, x_field: str = None, y_field: str = None, z_field: str = None,
                      size_field: str = None, color_field: str = None,
                      size_range: list = [2, 10],
                      size_min_max=[None, None],
                      color_sequence: list = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf",
                                              "#fee090",
                                              "#fdae61", "#f46d43", "#d73027", "#a50026"], info: str = None,
                      x_field_type: str = "value",
                      y_field_type: str = "value",
                      z_field_type: str = "value",
                      x_field_log_base: int = 10,
                      y_field_log_base: int = 10,
                      z_field_log_base: int = 10,
                      x_field_scale: bool = False,
                      y_field_scale: bool = False,
                      z_field_scale: bool = False,
                      title: str = "",
                      width: str = "100%",
                      height: str = "500px"):
    """
    3d 气泡图


    :param data_frame:
    :param x_field:
    :param y_field:
    :param z_field:
    :param size_field: size对应列，数值类型
    :param size_range: [2,10]
    :param color_field: 颜色列
    :param color_sequence:
    :param info: 额外信息
    :param z_field_type: value/log/category/time
    :param y_field_type:
    :param x_field_type:
    :param z_field_scale:
    :param y_field_scale:
    :param x_field_scale:
    :param z_field_log_base:
    :param y_field_log_base:
    :param x_field_log_base:
    :param title:
    :param width:
    :param height:
    :return:
    """
    options = {
        'title': {'text': title, 'left': 50},
        'tooltip': {
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)"
        },
        'xAxis3D': {
            'name': x_field,
            'type': x_field_type,
            'scale': x_field_scale,
            'logBase': x_field_log_base,

        },
        'yAxis3D': {
            'name': y_field,
            'type': y_field_type,
            'scale': y_field_scale,
            'logBase': y_field_log_base,
        },
        'zAxis3D': {
            'name': z_field,
            'type': z_field_type,
            'scale': z_field_scale,
            'logBase': z_field_log_base,
        },
        'grid3D': {
        }
    }
    if "date" in str(data_frame[x_field].dtype) or "object" in str(data_frame[x_field].dtype):
        options['xAxis3D']['type'] = 'category'
        options['xAxis3D']['data'] = sorted(list(data_frame[x_field].unique()))
    if "date" in str(data_frame[y_field].dtype) or "object" in str(data_frame[y_field].dtype):
        options['yAxis3D']['type'] = 'category'
        options['yAxis3D']['data'] = sorted(list(data_frame[y_field].unique()))
    if "date" in str(data_frame[z_field].dtype) or "object" in str(data_frame[z_field].dtype):
        options['zAxis3D']['type'] = 'category'
        options['zAxis3D']['data'] = sorted(list(data_frame[z_field].unique()))
    series = {
        'type': 'scatter3D',
        'name': title,
        'dimensions': [x_field, y_field, z_field],
        'data': data_frame[[x_field, y_field, z_field]].values.tolist()
    }
    if (color_field is not None) or (size_field is not None):
        options['visualMap'] = []
    if size_field is not None:
        series['dimensions'].append(size_field)
        size_list = data_frame[size_field].tolist()
        for i in range(0, len(size_list)):
            series['data'][i].append(size_list[i])
        visual_map = {
            'show': True,
            'orient': 'vertical',
            'left': 0,
            'top': 0,
            'calculable': True,
            'text': ['高', '低'],
            'dimension': len(series['dimensions']) - 1,
            'inRange': {
                'symbolSize': size_range,
            },
            'type': 'continuous',
            'min': data_frame[size_field].min() if size_min_max[0] is None else size_min_max[0],
            'max': data_frame[size_field].max() if size_min_max[1] is None else size_min_max[1]
        }
        options['visualMap'].append(visual_map)

    if color_field is not None:
        series['dimensions'].append(color_field)
        color_list = data_frame[color_field].tolist()
        for i in range(0, len(color_list)):
            series['data'][i].append(color_list[i])
        visual_map = {
            'show': True,
            'orient': 'vertical',
            'left': 0,
            'bottom': 0,
            'calculable': True,
            'text': ['高', '低'],
            'dimension': len(series['dimensions']) - 1,
            'inRange': {
                'color': color_sequence
            }
        }
        if "date" in str(data_frame[color_field].dtype) or "object" in str(data_frame[color_field].dtype):
            visual_map['type'] = 'piecewise'
            visual_map['categories'] = list(data_frame[color_field].unique())
        else:
            visual_map['type'] = 'continuous'
            visual_map['min'] = data_frame[color_field].min()
            visual_map['max'] = data_frame[color_field].max()
        options['visualMap'].append(visual_map)

    if info is not None:
        series['dimensions'].append(info)
        info_list = data_frame[info].tolist()
        for i in range(0, len(info_list)):
            series['data'][i].append(info_list[i])
    options['series'] = [series]
    options['toolbox'] = {
        'show': True,
        'feature': {
            'restore': {},
            'saveAsImage': {}
        }
    }
    return Echarts(options, with_gl=True, height=height, width=width)


def bar3d_echarts(data_frame: pd.DataFrame, x_field: str = None, y_field: str = None, z_field: str = None,
                  color_field: str = None,
                  color_sequence: list = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf",
                                          "#fee090",
                                          "#fdae61", "#f46d43", "#d73027", "#a50026"], info: str = None,
                  title: str = "",
                  width: str = "100%",
                  height: str = "500px"):
    """
    3d bar
    :param data_frame:
    :param x_field:
    :param y_field:
    :param z_field:
    :param color_field:
    :param color_sequence:
    :param info:
    :param title:
    :param width:
    :param height:
    :return:
    """
    options = {
        'title': {'text': title, 'left': 20},
        'tooltip': {
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)",
        },
        'xAxis3D': {
            'name': x_field,
            'type': 'value'

        },
        'yAxis3D': {
            'name': y_field,
            'type': 'value'
        },
        'zAxis3D': {
            'name': z_field,
            'type': 'value'
        },
        'grid3D': {
        }
    }
    if "date" in str(data_frame[x_field].dtype) or "object" in str(data_frame[x_field].dtype):
        options['xAxis3D']['type'] = 'category'
        options['xAxis3D']['data'] = sorted(list(data_frame[x_field].unique()))
    if "date" in str(data_frame[y_field].dtype) or "object" in str(data_frame[y_field].dtype):
        options['yAxis3D']['type'] = 'category'
        options['yAxis3D']['data'] = sorted(list(data_frame[x_field].unique()))
    if "date" in str(data_frame[z_field].dtype) or "object" in str(data_frame[z_field].dtype):
        options['zAxis3D']['type'] = 'category'
        options['zAxis3D']['data'] = sorted(list(data_frame[x_field].unique()))
    series = {
        'type': 'bar3D',
        'name': title,
        'dimensions': [x_field, y_field, z_field],
        'data': data_frame[[x_field, y_field, z_field]].values.tolist(),
        'label': {
            'show': False
        },
        'itemStyle': {
            'opacity': 0.5
        },
        'emphasis': {
            'itemStyle': {
                'color': '#900'
            },
            'label': {'show': False}
        }
    }
    if color_field is not None:
        options['visualMap'] = []
        series['dimensions'].append(color_field)
        color_list = data_frame[color_field].tolist()
        for i in range(0, len(color_list)):
            series['data'][i].append(color_list[i])
        visual_map = {
            'show': True,
            'orient': 'vertical',
            'left': 0,
            'bottom': 0,
            'calculable': True,
            'text': ['高', '低'],
            'dimension': len(series['dimensions']) - 1,
            'inRange': {
                'color': color_sequence
            }
        }
        if "date" in str(data_frame[color_field].dtype) or "object" in str(data_frame[color_field].dtype):
            visual_map['type'] = 'piecewise'
            visual_map['categories'] = list(data_frame[color_field].unique())
        else:
            visual_map['type'] = 'continuous'
            visual_map['min'] = data_frame[color_field].min()
            visual_map['max'] = data_frame[color_field].max()
        options['visualMap'] = [visual_map]

    if info is not None:
        series['dimensions'].append(info)
        info_list = data_frame[info].tolist()
        for i in range(0, len(info_list)):
            series['data'][i].append(info_list[i])
    options['series'] = [series]
    options['toolbox'] = {
        'show': True,
        'feature': {
            'restore': {},
            'saveAsImage': {}
        }
    }
    return Echarts(options, with_gl=True, height=height, width=width)


def drawdown_echarts(data_frame: pd.DataFrame, time_field: str, value_field: str, code_field: str, title="",
                     width="100%",
                     height='500px') -> Echarts:
    """
    回撤图
    :param data_frame: pd.DataFrame
    :param time_field: 时间列名
    :param value_field: 价格列名
    :param code_field: 资产编码列名
    :param title: 标题
    :param width: 宽度
    :param height: 高度
    :return:
    """
    df = data_frame[[time_field, value_field, code_field]].copy().sort_values(time_field, ascending=True).reset_index()
    df_pivot = df.pivot_table(index=time_field, columns=code_field, values=value_field).fillna(method='bfill').fillna(
        method='ffill')
    df_return = (((df_pivot / df_pivot.iloc[0]) - 1) * 100).round(2)
    df_cummax = df_pivot.cummax()
    df_drawdown = (((df_pivot - df_cummax) / df_cummax) * 100).round(2)
    sorted_date = sorted(df[time_field].unique())
    codes = df[code_field].unique()
    colors = ['red', 'blue', 'orange', 'pink', 'green', 'yellow', 'purple', 'sliver', 'gold', 'black']
    color_index = 0
    options = {
        'title': {'text': title},
        'legend': [{
            'type': "scroll",
            'data': list(df[code_field].unique())
        }],
        'tooltip': {
            'trigger': 'axis', 'axisPointer': {'type': 'cross'},
            'borderWidth': 1,
            'borderColor': '#ccc',
            'backgroundColor': "rgba(255,255,255,0.8)",
            'color': "black",
            'padding': 10,
            'formatter': Js("""function (params) {
                const x_value = params[0]['axisValue'];
                const labels = [];
                labels.push('<b><span>时间:&nbsp;</span></b>' + x_value + '<br/>');
                params.sort(function (a, b) {
                  if (a.seriesId.substr(-1, 1) < b.seriesId.substr(-1, 1)) {
                    return -1;
                  } else if (a.seriesId.substr(-1, 1) > b.seriesId.substr(-1, 1)) {
                    return 1;
                  } else {
                    return 0;
                  }
                });
                labels.push('<b><span>收益:</span></b><br/>');
                for (let i = 0; i < params.length; i++) {
                  const param = params[i];
                  if (param.seriesId.substr(-1, 1) == '0') {
                    const label = ['<span><b>' + param['seriesName'] + '</b>:' + (param['value'][1]?(param['value'][1]).toFixed(2):"") + '%</span><br/>'];
                    labels.push(label);
                  }
                }
                labels.push('<b><span>回撤:</span></b><br/>');
                for (let i = 0; i < params.length; i++) {
                  const param = params[i];
                  if (param.seriesId.substr(-1, 1) == '1') {
                    const label = ['<span><b>' + param['seriesName'] + '</b>:' + (param['value'][1]?(-param['value'][1]).toFixed(2):"")+ '%</span><br/>'];
                    labels.push(label);
                  }
                }
                return labels.join('');

            }""")
        },
        'axisPointer': {
            'link': {'xAxisIndex': 'all'},
            'label': {'backgroundColor': '#777'}
        },
        'xAxis': [
            {
                'type': 'category',
                'data': sorted_date,
                'scale': True,
                'boundaryGap': False,
                'axisLine': {'onZero': False, 'show': True},
                'axisLabel': {'show': True},
                'axisTick': {'show': True},
                'splitLine': {'show': True},
                'splitNumber': 20,
                'min': 'dataMin',
                'max': 'dataMax'
            }
        ],
        'yAxis': [
            {
                'scale': True,
                'type': 'value',
                'splitNumber': 10,
                'axisLabel': {
                    'show': True
                },
                'axisLine': {'show': False},
                'axisTick': {'show': True},
                'splitLine': {'show': True}
            },
            {
                'scale': True,
                'type': 'value',
                'splitNumber': 10,
                'axisLabel': {
                    'show': True
                },
                'axisLine': {'show': False},
                'axisTick': {'show': True},
                'splitLine': {'show': True}
            }
        ],
        'dataZoom': [
            {
                'type': 'inside',
                'xAxisIndex': [0, 1],
                'start': 0,
                'end': 100
            }
        ],
        'series': []
    }
    for item in codes:
        end_time = df_drawdown[item].idxmin()
        begin_time = \
            df_drawdown[item][(df_drawdown[item] >= 0) & (df_drawdown[item].index < df_drawdown[item].idxmin())].index[
                -1]

        return_series = {
            "name": item,
            'itemStyle': {'color': colors[color_index]},
            'type': 'line',
            'data': df_return[item].to_frame().reset_index().values.tolist(),
            'markPoint': {
                'data': [{'type': 'max', 'name': '最大值'}],
                'label': {
                    'formatter': '{c}%',
                    'position': 'top',
                },
            },
            'markArea': {
                'itemStyle': {'borderWidth': 2, 'borderType': 'dashed', 'opacity': 1, 'color': 'rgba(0, 0, 0, 0)'},
                'data': [
                    [
                        {
                            'name': item + '最大回撤区间' + str(round(-df_drawdown[item].min(), 2)) + '%',
                            'coord': [
                                begin_time, df_return[item].loc[begin_time]
                            ],
                        },
                        {
                            'coord': [end_time, df_return[item].loc[end_time]],
                        },
                    ],
                ],
            }
        }
        drawdown_series = {
            'name': item,
            'type': 'line',
            'areaStyle': {'opacity': 0.3, 'color': colors[color_index]},
            'lineStyle': {'opacity': 0},
            'yAxisIndex': 1,
            'data': df_drawdown[item].to_frame().reset_index().values.tolist()
        }
        options['series'].append(return_series)
        options['series'].append(drawdown_series)
        options['toolbox'] = {
            'show': True,
            'feature': {
                'restore': {},
                'saveAsImage': {}
            }
        }
        color_index = (color_index + 1) % len(colors)
    return Echarts(options, height=height, width=width)


def minute_echarts(data_frame: pd.DataFrame, time_field="time", price_field='price', volume_field="volume", title="",
                   width="100%",
                   height='500px'):
    """

    :param data_frame:
    :param time_field:
    :param price_field:
    :param volume_field:
    :param title:
    :param width:
    :param height:
    :return:
    """

    def agg_ohlcv(x):
        arr = x[price_field].values
        names = {
            'low': min(arr) if len(arr) > 0 else np.nan,
            'high': max(arr) if len(arr) > 0 else np.nan,
            'open': arr[0] if len(arr) > 0 else np.nan,
            'close': arr[-1] if len(arr) > 0 else np.nan,
            'volume': sum(x[volume_field].values) if len(x[volume_field].values) > 0 else 0,
        }
        return pd.Series(names)

    df1min = data_frame.set_index(time_field).resample('1min').apply(agg_ohlcv)
    df1min = df1min.ffill()
    df1min['avg_price'] = (df1min['close'] * df1min['volume']).cumsum() / df1min['volume'].cumsum()
    return candlestick_echarts(df1min[df1min['volume'] > 0], log_y=False, mas=[], title=title, width=width,
                               height=height).overlap_series(
        [line_echarts(df1min, y_field='avg_price')])


def bullet_g2plot(title: str = "", range_field: list = [], measure_field: list = [], target_field: int = None,
                  width="100%", height="50px") -> G2PLOT:
    """
    子弹图
    :param title: 标题
    :param range_field: 区间数组
    :param measure_field: 实际值数组 多个值会堆叠显示，
    :param target_field: 目标值
    :param width:
    :param height:
    :return:
    """
    return G2PLOT([{'title': title, '区间': range_field, '实际值': measure_field, '目标': target_field}],
                  plot_type='Bullet', options={
            'measureField': '实际值',
            'rangeField': '区间',
            'targetField': '目标',
            'xField': 'title'
        }, height=height, width=width)


def chord_g2plot(df, source_field: str = None, target_field: str = None, weight_field: str = None, width="100%",
                 height="500px"):
    """
    关系图
    :param df:
    :param source_field:
    :param target_field:
    :param weight_field:
    :param width:
    :param height:
    :return:
    """
    return G2PLOT(df, plot_type='Chord', options={
        'sourceField': source_field,
        'targetField': target_field,
        'weightField': weight_field
    }, height=height, width=width)


def waterfall_g2plot(df, x_field: str = None, y_field: str = None, width="100%", height="500px"):
    """
    瀑布图
    :param df:
    :param x_field:
    :param y_field:
    :param width:
    :param height:
    :return:
    """
    return G2PLOT(df, plot_type='Waterfall', options={
        'xField': x_field,
        'yField': y_field
    }, width=width, height=height)


def liquid_g2plot(percent: float = 1, width='200px', height='200px'):
    """
    水波图
    :param percent:百分比
    :param width:
    :param height:
    :return:
    """
    return G2PLOT([], plot_type='Liquid', options={
        'percent': percent,
        'autoFit': True,
        'outline': {
            'border': 4,
            'distance': 8,
        }
    }, width=width, height=height)


def wordcloud_g2plot(df, word_field: str = None, weight_field: str = None, width='100%', height='500px'):
    """
    词云
    :param df:
    :param word_field: 词列
    :param weight_field: 权重列
    :param width:
    :param height:
    :return:
    """
    return G2PLOT(df, plot_type="WordCloud", options={
        'wordField': word_field,
        'weightField': weight_field,
        'colorField': word_field,
        'wordStyle': {
            'fontSize': [15, 100],
        },
        'interactions': [{'type': 'element-active'}],
        'state': {
            'active': {
                'style': {
                    'lineWidth': 3,
                },
            },
        }
    }, width=width, height=height)


def column_stack_percent_g2plot(df, x_field: str = None, y_field: str = None, series_field: str = None,
                                show_label: bool = True, width='100%',
                                height='500px'):
    """
    柱状图百分比堆叠，查看组成部分，占比随时间变化，x_field时间，y_field比例，series_field 类别
    :param df:
    :param x_field:
    :param y_field:
    :param series_field:
    :param show_label: 图形上是否显示标签
    :param width:
    :param height:
    :return:
    """
    options = {
        'xField': x_field,
        'yField': y_field,
        'seriesField': series_field,
        'isPercent': True,
        'isStack': True,
        'tooltip': False,
        'interactions': [{'type': 'element-highlight-by-color'}, {'type': 'element-link'}]
    }
    if show_label:
        options['label'] = {
            'position': 'middle',
            'content': Js(f"""
                    function(item){{
                      return (item['{y_field}'] * 100).toFixed(2);
                    }}
                """)
        }
    return G2PLOT(df, plot_type="Column", options=options, width=width, height=height)


def column_stack_g2plot(df, x_field: str = None, y_field: str = None, series_field: str = None, show_label: bool = True,
                        width='100%',
                        height='500px'):
    """
    柱状图堆叠，查看组成部分，占比随时间变化，x_field时间，y_field比例，series_field 类别
    :param df:
    :param x_field:
    :param y_field:
    :param series_field:
    :param show_label: 是否数据上显示标签
    :param width:
    :param height:
    :return:
    """
    options = {
        'xField': x_field,
        'yField': y_field,
        'seriesField': series_field,
        'isStack': True,
        'tooltip': {
            'shared': False
        },
        'interactions': [{'type': 'element-highlight-by-color'}, {'type': 'element-link'}]
    }
    if show_label:
        options['label'] = {'position': 'middle'}
    return G2PLOT(df, plot_type="Column", options=options, width=width, height=height)


def area_g2plot(df, x_field: str = None, y_field: str = None, series_field: str = None, width='100%', height='500px'):
    """
    area chart
    :param df:
    :param x_field:
    :param y_field:
    :param series_field:
    :param width:
    :param height:
    :return:
    """
    options = {
        'xField': x_field,
        'yField': y_field
    }
    if series_field is not None:
        options['seriesField'] = series_field
    return G2PLOT(df, plot_type="Area", options=options, width=width, height=height)


def area_percent_g2plot(df, x_field: str = None, y_field: str = None, series_field: str = None, width='100%',
                        height='500px'):
    """
    area stack percent chart
    :param df:
    :param x_field:
    :param y_field:
    :param series_field:
    :param width:
    :param height:
    :return:
    """
    options = {
        'xField': x_field,
        'yField': y_field,
        'seriesField': series_field,
        'areaStyle': {
            'fillOpacity': 0.6,
        },
        'appendPadding': 10,
        'isPercent': True,
    }
    return G2PLOT(df, plot_type="Area", options=options, width=width, height=height)


def circle_packing_g2plot(df, category_field_list: list = [], value_field: str = None, width="100%",
                          height='500px'):
    data = Tools.df2tree(df, category_cols=category_field_list, value_col=value_field)
    root = {
        'name': 'root',
        'children': data
    }
    options = {
        'autoFit': True,
        'padding': 0,
        'sizeField': value_field,
        'colorField': value_field,
        'label': False,
        'drilldown': {
            'enabled': True,
            'breadCrumb': {
                'position': 'top-left',
            },
        },
    }
    return G2PLOT(root, plot_type='CirclePacking', options=options, width=width, height=height)


def treemap_g2plot(df, category_field_list: list = [], value_field: str = None, width="100%",
                   height='500px'):
    """
    treemap
    :param df: cat1,cat2,...,catN,value
    :param category_field_list:类别列表
    :param value_field:值列表
    :param width:
    :param height:
    :return:
    """
    data = Tools.df2tree(df, category_cols=category_field_list, value_col=value_field)
    root = {
        'name': 'root',
        'children': data
    }
    options = {
        'legend': {
            'position': 'top-left',
        },
        'tooltip': {
            'formatter': Js("""
            function(v){
                var root = v.path[v.path.length - 1];
                return {
                    name: v.name,
                    value: v.value+'(总占比'+((v.value / root.value) * 100).toFixed(2)+')'
                };
            }
        """)
        },
        'interactions': [{'type': 'treemap-drill-down'}],
        'animation': {},
    }
    return G2PLOT(root, plot_type='Treemap', options=options, width=width, height=height)


def violin_g2plot(df, x_field: str = None, y_field: str = None, series_field: str = None, width="100%",
                  height='500px'):
    """
    小提琴图，展示y列的分布
    :param df:
    :param x_field: 类别列
    :param y_field: 数值列
    :param series_field: 分组列
    :param width:
    :param height:
    :return:
    """
    options = {
        'xField': x_field,
        'yField': y_field,
        'meta': {
            'high': {'alias': '最大值'},
            'low': {'alias': '最小值'},
            'q1': {'alias': '上四分位数'},
            'q3': {'alias': '下四分位数'}
        }
    }
    if series_field is not None:
        options['seriesField'] = series_field

    return G2PLOT(df, plot_type='Violin', options=options, width=width, height=height)


def line_g2plot(df, x_field=None, y_field=None, series_field=None, width='100%', height='500px'):
    """
    线图
    """
    options = {'xField': x_field, 'yField': y_field}
    if series_field is not None:
        options['seriesField'] = series_field
    return G2PLOT(df, plot_type='Line', options=options, width=width, height=height)


def scatter_g2plot(df, x_field=None, y_field=None, color_field=None, size_field=None, shape_field=None,
                   width='100%',
                   height='500px'):
    """
    点图
    """
    options = {'xField': x_field, 'yField': y_field}
    if color_field is not None:
        options['colorField'] = color_field
    if size_field is not None:
        options['sizeField'] = size_field
    if shape_field is not None:
        options['shapeField'] = shape_field
    return G2PLOT(df, plot_type='Scatter', options=options, width=width, height=height)


def column_g2plot(df, x_field=None, y_field=None, series_field=None, is_stack=False, is_group=False, is_range=False,
                  width='100%', height='500px'):
    """
    柱状图
    """
    options = {'xField': x_field, 'yField': y_field}
    if series_field is not None:
        options['seriesField'] = series_field
    if is_stack:
        options['isStack'] = True
    elif is_group:
        options['isGroup'] = True
    elif is_range:
        options['isRange'] = True
    return G2PLOT(df, plot_type='Column', options=options, width=width, height=height)


def rose_g2plot(df, x_field=None, y_field=None, series_field=None, is_stack=False, is_group=False, width='100%',
                height='500px'):
    """
    玫瑰图
    """
    options = {'xField': x_field, 'yField': y_field}
    if series_field is not None:
        options['seriesField'] = series_field
    if is_stack:
        options['isStack'] = True
    elif is_group:
        options['isGroup'] = True
    return G2PLOT(df, plot_type='Rose', options=options, width=width, height=height)


def pie_g2plot(df, angle_field=None, color_field=None, width='100%', height='500px'):
    """
    饼图
    """
    options = {'angleField': angle_field, 'colorField': color_field}
    return G2PLOT(df, plot_type='Pie', options=options, width=width, height=height)


def radial_bar_g2plot(df, x_field=None, y_field=None, color_field=None, width='100%', height='500px'):
    options = {'xField': x_field, 'yField': y_field, 'colorField': color_field, 'tooltip': {'showMarkers': True},
               'type': 'line'}

    return G2PLOT(df, plot_type='RadialBar', options=options, width=width, height=height)


def gauge_g2plot(df, percent=0.25, width='100%', height='500px'):
    options = {'percent': percent}
    return G2PLOT(df, plot_type='Gauge', options=options, width=width, height=height)


def sankey_g2plot(df, source_field=None, target_field=None, weight_field=None, width='100%', height='500px'):
    options = {'sourceField': source_field, 'targetField': target_field, 'weightField': weight_field}
    return G2PLOT(df, plot_type='Sankey', options=options, width=width, height=height)


def heatmap_g2plot(df, x_field=None, y_field=None, color_field=None, width='100%', height='500px'):
    options = {'xField': x_field, 'yField': y_field, 'colorField': color_field}
    options["meta"]: {
        x_field: {
            "type": "cat"
        },
        y_field: {
            "type": "cat"
        },
    }
    return G2PLOT(df, plot_type='Heatmap', options=options, width=width, height=height)


def radar_g2plot(df, x_field=None, y_field=None, width='100%', height='500px'):
    options = {'xField': x_field, 'yField': y_field, 'area': {}}
    return G2PLOT(df, plot_type='Radar', options=options, width=width, height=height)


def funnel_g2plot(df, x_field=None, y_field=None, width='100%', height='500px'):
    options = {'xField': x_field, 'yField': y_field}
    return G2PLOT(df, plot_type='Funnel', options=options, width=width, height=height)


def histogram_g2plot(df, bin_field=None, bin_width=None, width='100%', height='500px'):
    options = {'binField': bin_field, 'binWidth': bin_width}
    return G2PLOT(df, plot_type='Histogram', options=options, width=width, height=height)


def streamgraph_highcharts(data_frame: pd.DataFrame, time_field: str = None, series_field: str = None,
                           value_field: str = None,
                           title: str = "", height='600px') -> HighCharts:
    """

    :param data_frame:
    :param time_field:
    :param series_field:
    :param value_field:
    :param title:
    :param width:
    :param height:
    :return:
    """
    df = data_frame.pivot(index=time_field, columns=series_field, values=value_field).fillna(0)
    x_category = list(df.index)
    options = {'chart': {'type': 'streamgraph', 'marginBottom': 30, 'zoomType': 'x', 'height': height},
               'title': {'floating': True, 'align': 'left', 'text': title},
               'xAxis': {'maxPadding': 0, 'type': 'category', 'crosshair': True,
                         'categories': x_category,
                         'labels': {'align': 'left', 'reserveSpace': False, 'rotation': 270}, 'lineWidth': 0,
                         'margin': 20, 'tickWidth': 0},
               'yAxis': {'visible': False, 'startOnTick': False, 'endOnTick': False}, 'legend': {'enabled': False},
               'series': []}
    for col in df.columns:
        data = list(df[col].values)
        options['series'].append({'name': col, 'data': data})
    return HighCharts(options, height=height)


def dependency_wheel_highcharts(data_frame: pd.DataFrame, from_field=None, to_field=None, weight_field=None,
                                title="", height='600px') -> HighCharts:
    options = {'title': {'text': title},
               'chart': {'height': height},
               'series': [{'keys': ['from', 'to', 'weight'],
                           'data': data_frame[[from_field, to_field, weight_field]].values(),
                           'type': 'dependencywheel',
                           'name': title,
                           'dataLabels': {'color': '#333',
                                          'textPath': {
                                              'enabled': True,
                                              'attributes': {
                                                  'dy': 5}},
                                          'distance': 10},
                           'size': '95%'}]}
    return HighCharts(options)


def arcdiagram_highcharts(data_frame: pd.DataFrame, from_field=None, to_field=None, weight_field=None,
                          title="", height='600px') -> HighCharts:
    options = {'title': {'text': title}, 'chart': {'height': height}, 'series': [
        {'keys': ['from', 'to', 'weight'], 'type': 'arcdiagram', 'name': title, 'linkWeight': 1,
         'centeredLinks': True, 'dataLabels': {'rotation': 90, 'y': 30, 'align': 'left', 'color': 'black'},
         'offset': '65%',
         'data': data_frame[[from_field, to_field, weight_field]].values()}]}
    return HighCharts(options)
