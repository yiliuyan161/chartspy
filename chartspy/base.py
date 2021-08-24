#!/usr/bin/env python
# coding=utf-8
import datetime
import re
from typing import Optional

import numpy as np
import pandas as pd
import simplejson
from jinja2 import Environment, BaseLoader

# jinja2模板引擎env
GLOBAL_ENV = Environment(loader=BaseLoader)
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

    def __init__(self, data: Optional[str] = None):
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
    def wrap_template(js_options_template: str, **kwargs):
        """
        组装模板和数据生成配置字符串，模板可以从echarts例子修改而来，使用jinja2模板引擎
        :param js_options_template:
        :param kwargs:
        :return:
        """
        return GLOBAL_ENV.from_string(js_options_template).render(**kwargs)

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
            return "'" + match_obj.group(1) + "':" + match_obj.group(2)

        # 去除注释
        js_code = re.sub(r"[\s]+//[^\n]+\n", "", js_code)
        # 对象key 增加单引号
        js_code = re.sub(r"([a-zA-Z0-9]+):\s*([\{'\"\[]|true|false|[\d\.]+|function)", rep1, js_code)
        # true，false,null 替换
        js_code = re.sub("true", "True", js_code)
        js_code = re.sub("false", "False", js_code)
        js_code = re.sub("null", "None", js_code)
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
        dict_options = eval(dict_str)
        return dict_options

    @staticmethod
    def convert_dict_to_js(options):
        """
        转换 python dict 成 JavaScript Object
        先simplejson序列化,再特殊处理函数
        :return: JavaScript 对象的字符串表示
        """
        json_str = simplejson.dumps(options, indent=2, default=json_type_convert, ignore_nan=True)
        segs = []
        function_start = 0
        # 找到所有函数声明的起止位置,处理双引号转移，再把包裹函数的特征串删除
        mask_length = len(FUNCTION_BOUNDARY_MARK)
        for i in range(mask_length, len(json_str)):
            if json_str[i - mask_length - 1:i] == '"' + FUNCTION_BOUNDARY_MARK:
                function_start = i - mask_length
            elif json_str[i - mask_length - 1:i] == FUNCTION_BOUNDARY_MARK + '"':
                segs.append([function_start, i])
        left_index = 0
        parts = []
        for seg in segs:
            parts.append(json_str[left_index:seg[0]])
            parts.append(json_str[seg[0]:(seg[1] + 1)].replace('\\"', '"'))
            left_index = seg[1] + 1
        parts.append(json_str[left_index:])
        dict_str = "".join(parts)
        return re.sub('"?' + FUNCTION_BOUNDARY_MARK + '"?', "", dict_str)


json_encoder = simplejson.JSONEncoder()


def json_type_convert(o: object):
    """
    python 类型转换成js类型
    :param o: simplejson序列化不了的对象
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
    else:
        return json_encoder.default(o)


__all__ = ["Tools", "json_type_convert", "Html", "Js", "GLOBAL_ENV"]
