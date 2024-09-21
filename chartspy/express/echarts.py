#!/usr/bin/env python
# coding=utf-8
import copy

import pandas as pd
import numpy as np
from .. import Echarts
from ..base import Js, Tools

# 二维坐标系统基础配置适用  scatter,bar,line
ECHARTS_BASE_GRID_OPTIONS = {
    'animation': False,
    'legend': {
        'data': []
    },
    'grid': {'left': 0, 'right': '3%'},
    'tooltip': {
        'trigger': 'axis', 'axisPointer': {'type': 'cross','snap':True},
        'borderWidth': 0,
        'borderColor': 'transparent',
        'color': "black",
        'backgroundColor': "rgba(0,0,0,0)",
        'alwaysShowContent': False,
        'padding': 0,
        'formatter': Js("""
            function(params){
                var dt = params[0]['axisValue'];
                var labels = [];
                labels.push('<span>时间:&nbsp;</span>' + dt + '&nbsp;');
                params.sort(function(a, b) {
                    if (a.seriesName < b.seriesName ) {return -1;}
                    else if (a.seriesName > b.seriesName ) {return 1;}
                    else{ return 0;}
                });
                for (let i = 0; i < params.length; i++) {
                    const param = params[i];
                    const label = [];
                    const dimensionNames = param["dimensionNames"];
                    if (typeof (param['value']) == 'object' && dimensionNames.length == param['data'].length) {
                        for (let j = 1; j < dimensionNames.length; j++) {
                            const value = param['data'][j];
                            if (typeof (value) == 'number') {
                                if (value % 1 == 0 || value > 100000) {
                                    label.push("<span>" + dimensionNames[j] + ':&nbsp;' + value + "</span>&nbsp;");
                                } else {
                                    label.push("<span>" + dimensionNames[j] + ':&nbsp;' + value  + "</span>&nbsp;");
                                }
                            } else {
                                label.push("<div style='max-width:15em;word-break:break-all;white-space: normal;'>" + dimensionNames[j] + ':&nbsp;' + value + "</div>&nbsp;");
                            }
                        }
                    } else if (param['seriesType'] == "candlestick") {
                        label.push("<span>开:&nbsp;" + param['value'][1].toFixed(2) + "</span>&nbsp;");
                        label.push("<span>高:&nbsp;" + param['value'][4].toFixed(2) + "</span>&nbsp;");
                        label.push("<span>低:&nbsp;" + param['value'][3].toFixed(2) + "</span>&nbsp;");
                        label.push("<span>收:&nbsp;" + param['value'][2].toFixed(2) + "</span>&nbsp;");
                        const increase = (param['value'][5] * 100);
                        const colors=['#254000','#3f6600','#5b8c00','#7cb305','#a0d911','#f5222d','#cf1322','#a8071a','#820014',"#5c0011"];
                        var color_index = Math.round((Math.min(Math.max(-10,increase),10)+10)/2-1);
                        label.push("<span>涨幅:&nbsp;<span style='color:" + colors[color_index%20] + "'<b>" + increase.toFixed(2) + "</b></span></span>&nbsp;");
                        label.push("<span>振幅:&nbsp;" + ((param['value'][4] / param['value'][3] - 1) * 100).toFixed(2) + "</span>&nbsp;");
                    } else if (typeof (param['value']) == 'number') {
                        if (param['value'] > 10000) {
                            if (param['value'] % 1 == 0) {
                                label.push("<span>" + param["seriesName"] + ":" + (param['value'] / 10000).toFixed(0) + "万</span>&nbsp;");
                            } else {
                                label.push("<span>" + param["seriesName"] + ":" + (param['value'] / 10000).toFixed(2) + "万</span>&nbsp;");
                            }
                        } else {
                            if (param['value'] % 1 == 0) {
                                label.push("<span>" + param["seriesName"] + ":" + param['value'].toFixed(0) + "</span>&nbsp;");
                            } else {
                                label.push("<span>" + param["seriesName"] + ":" + param['value'].toFixed(2) + "</span>&nbsp;");
                            }
                        }
                    } else if (param['value']) {
                        label.push("<div style='max-width:15em;word-break:break-all;white-space: normal;'>" + param['value'] + "</div>&nbsp;");
                    } else {
                        label.push("&nbsp;");
                    }
                    const cardStr = label.join('');
                    labels.push(cardStr);
                }
                return labels.join('');
            }"""),
        'textStyle': {'color': '#000'},
        'position': Js("""
            function (pos, params, el, elRect, size){
                return {top: 30, left: 5};
            }
        """),
        'extraCssText': 'box-shadow: 0 0 0 rgba(0, 0, 0, 0);'
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
        'position':'right',
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
                    height: str = "500px",**kwargs) -> Echarts:
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
        options['grid']['bottom']=70
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
        options['grid']['bottom']=70
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
    options.update(kwargs)
    return Echarts(options=options, width=width, height=height)


def line_echarts(data_frame: pd.DataFrame, x_field: str = None, y_field: str = None, series_field: str = None,
                 tooltip_trigger="axis",
                 y_scale=True,
                 title: str = "",
                 width: str = "100%", height: str = "500px",**kwargs) -> Echarts:
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
    options['yAxis']['scale'] = y_scale
    if series_field is not None:
        series_list = list(df[series_field].unique())
        for s in series_list:
            series = {'name': s, 'type': 'line', 'dimensions': [x_field, y_field],
                      'data': df[df[series_field] == s][[x_field, y_field]].values.tolist()}
            options['legend']['data'].append(s)
            options['series'].append(series)
    else:
        series = {'name': title, 'type': 'line', 'dimensions': [x_field, y_field],
                  'data': df[[x_field, y_field]].values.tolist()}
        options['legend']['data'].append(title)
        options['series'].append(series)
    if tooltip_trigger == 'item':
        del options['axisPointer']
    options['toolbox'] = {
        'show': True,
        'feature': {
            'restore': {},
            'saveAsImage': {}
        }
    }
    options.update(kwargs)
    return Echarts(options=options, width=width, height=height)


def bar_echarts(data_frame: pd.DataFrame, x_field: str = None, y_field: str = None, series_field: str = None,
                stack: str = "all",
                tooltip_trigger="axis",
                y_scale=True,
                title: str = "",
                width: str = "100%", height: str = "500px",**kwargs) -> Echarts:
    """

    :param data_frame: 必填 DataFrame
    :param x_field: 必填 x轴映射的列
    :param y_field: 必填 y轴映射的列
    :param series_field: 选填 series 对应列
    :param stack: 堆叠分组
    :param tooltip_trigger: axis item
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return: Echarts
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
    options['yAxis']['scale'] = y_scale
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
                  'data': df[[x_field, y_field]].values.tolist()}
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
    options.update(kwargs)
    return Echarts(options=options, width=width, height=height)


def pie_echarts(data_frame: pd.DataFrame, name_field: str = None, value_field: str = None, rose_type: str = None,
                title: str = "",
                width: str = "100%", height: str = "500px",**kwargs) -> Echarts:
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
    options.update(kwargs)
    return Echarts(options=options, width=width, height=height)

def candlestick_echarts(data_frame: pd.DataFrame, time_field: str = 'time', open_field: str = "open",
                        high_field: str = 'high',
                        low_field: str = 'low',
                        close_field: str = 'close',
                        volume_field: str = 'volume', mas: list = [5, 10, 30], log_y: bool = True, title: str = "",
                        width: str = "100%", height: str = "600px", left_padding: str = '0%',
                        right_padding: str = '3%',**kwargs) -> Echarts:
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
    df[close_field] = df[close_field].ffill()
    df[open_field] = df[open_field].fillna(df[close_field])
    df[high_field] = df[high_field].fillna(df[close_field])
    df[low_field] = df[low_field].fillna(df[close_field])
    df['uplimit'] = df[close_field] > df[close_field].shift(1) * 1.098
    df['dnlimit'] = df[close_field] < df[close_field].shift(1) * 0.902
    df['pct_change']=df[close_field].pct_change()
    bars = [{'value': [row[open_field], row[close_field], row[low_field], row[high_field],row['pct_change']],
             'itemStyle': ({"borderWidth": 4} if (row['uplimit'] or row['dnlimit']) else {})} for row in
            df.to_dict(orient="records")]
    df[volume_field] = df[volume_field].fillna(0)
    volumes = (df[volume_field]).round(2).tolist()
    vol_filter = (df[volume_field]).quantile([0.10, 0.90]).values
    bar_items = [({"value": vol} if vol >= vol_filter[0] and vol <= vol_filter[1] else (
        {"value": vol, "itemStyle": {"color": "red"}} if vol > vol_filter[1] else {"value": vol,
                                                                                   "itemStyle": {"color": "green"}}))
                 for vol in volumes]

    options = {
        'animation': False,
        'title': {'text': title,'padding':[5,0]},
        'legend': {'top': 0,'padding':[5,10], 'left': 'right', 'data': [title]},
        'tooltip': {
            'trigger': 'axis', 'axisPointer': {'type': 'cross','snap':True},
            'borderWidth': 0,
            'borderColor': 'transparent',
            'color': "black",
            'backgroundColor': "rgba(0,0,0,0)",
            'alwaysShowContent': False,
            'padding': 0,
            'formatter': Js("""
                function(params){
                    var dt = params[0]['axisValue'];
                    var labels = [];
                    labels.push('<span>时间:&nbsp;</span>' + dt + '&nbsp;');
                    params.sort(function(a, b) {
                      if (a.seriesName < b.seriesName ) {return -1;}
                      else if (a.seriesName > b.seriesName ) {return 1;}
                      else{ return 0;}
                    });
                    for (let i = 0; i < params.length; i++) {
                        const param = params[i];
                        const label = [];
                        const dimensionNames = param["dimensionNames"];
                        if (typeof (param['value']) == 'object' && dimensionNames.length == param['data'].length) {
                            for (let j = 1; j < dimensionNames.length; j++) {
                                const value = param['data'][j];
                                if (typeof (value) == 'number') {
                                    if (value % 1 == 0 || value > 100000) {
                                        label.push("<span>" + dimensionNames[j] + ':&nbsp;' + (value / 10000).toFixed(0) + "万</span>&nbsp;");
                                    } else {
                                        label.push("<span>" + dimensionNames[j] + ':&nbsp;' + (value / 10000).toFixed(2) + "万</span>&nbsp;");
                                    }
                                } else {
                                    label.push("<div style='max-width:15em;word-break:break-all;white-space: normal;'>" + dimensionNames[j] + ':&nbsp;' + value + "</div>&nbsp;");
                                }
                            }
                        } else if (param['seriesType'] == "candlestick") {
                            label.push("<span>开:&nbsp;" + param['value'][1].toFixed(2) + "</span>&nbsp;");
                            label.push("<span>高:&nbsp;" + param['value'][4].toFixed(2) + "</span>&nbsp;");
                            label.push("<span>低:&nbsp;" + param['value'][3].toFixed(2) + "</span>&nbsp;");
                            label.push("<span>收:&nbsp;" + param['value'][2].toFixed(2) + "</span>&nbsp;");
                            const increase = (param['value'][5] * 100);
                            const colors=['#254000','#3f6600','#5b8c00','#7cb305','#a0d911','#f5222d','#cf1322','#a8071a','#820014',"#5c0011"];
                            var color_index = Math.round((Math.min(Math.max(-10,increase),10)+10)/2-1);
                            label.push("<span>涨幅:&nbsp;<span style='color:" + colors[color_index%20] + "'<b>" + increase.toFixed(2) + "</b></span></span>&nbsp;");
                            label.push("<span>振幅:&nbsp;" + ((param['value'][4] / param['value'][3] - 1) * 100).toFixed(2) + "</span>&nbsp;");
                        } else if (typeof (param['value']) == 'number') {
                            if (param['value'] > 10000) {
                                if (param['value'] % 1 == 0) {
                                    label.push("<span>" + param["seriesName"] + ":" + (param['value'] / 10000).toFixed(0) + "万</span>&nbsp;");
                                } else {
                                    label.push("<span>" + param["seriesName"] + ":" + (param['value'] / 10000).toFixed(2) + "万</span>&nbsp;");
                                }
                            } else {
                                if (param['value'] % 1 == 0) {
                                    label.push("<span>" + param["seriesName"] + ":" + param['value'].toFixed(0) + "</span>&nbsp;");
                                } else {
                                    label.push("<span>" + param["seriesName"] + ":" + param['value'].toFixed(2) + "</span>&nbsp;");
                                }
                            }
                        } else if (param['value']) {
                            label.push("<div style='max-width:15em;word-break:break-all;white-space: normal;'>" + param['value'] + "</div>&nbsp;");
                        } else {
                            label.push("&nbsp;");
                        }
                        const cardStr = label.join('');
                        labels.push(cardStr);
                    }
                    return labels.join('');
                }"""),
            'textStyle': {'color': '#000'},
            'position': Js("""
                function (pos, params, el, elRect, size){
                   return {top: 30, left: 5};
                }
            """),
            'extraCssText': 'box-shadow: 0 0 0 rgba(0, 0, 0, 0);'
        },
        'axisPointer': {
            'link': {'xAxisIndex': [1]},
            'label': {
                'backgroundColor': '#777',
                'formatter': Js("""
                    function(params) {
                    if (typeof params.value === 'number') {
                        return params.value.toFixed(2);
                    }
                    return params.value;
                }
                """)
            }
        },
        'toolbox': {
            'show': False,
            'feature': {
                'restore': {},
                'saveAsImage': {}
            }
        },
        'grid': [
            {'left': left_padding, 'right': right_padding, 'height': '79%'},
            {'left': left_padding, 'right': right_padding, 'top': '80%', 'height': '17%'}
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
                'splitNumber': 20,
                'position':'right',
                'minorSplitLine': {
                    'show': True
                },
                'minorTick': {
                    'show': True
                },
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
                'position':'right',
                'axisLabel': {'show': False},
                'axisLine': {'show': False},
                'axisTick': {'show': False},
                'splitLine': {'show': False}
            }
        ],
        'dataZoom': [
            {
                'type': 'inside',
                'xAxisIndex': [0, 1],
                'start': max(0, round(100 * (1 - 450 / df.shape[0]))),
                'end': 100
            }, {
                'type': 'slider',
                'xAxisIndex': [0, 1],
                'start': max(0, round(100 * (1 - 450 / df.shape[0]))),
                'end': 100,
                'height': 25
            }
        ],
        'series': [
            {
                'name': title,
                'type': 'candlestick',
                'data': bars,
            },
            {
                'name': 'Volume',
                'type': 'bar',
                'xAxisIndex': 1,
                'yAxisIndex': 1,
                'data': bar_items
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
            'symbol': 'none',
            'lineStyle': {'opacity': 0.5}
        }
        options['series'].append(series_ma)
        options['legend']['data'].append(name)
    options.update(kwargs)
    return Echarts(options=options, width=width, height=height)


def heatmap_echarts(data_frame: pd.DataFrame, x_field: str = None, y_field: str = None, color_field: str = None,
                    label_field: str = None,
                    x_axis_data: list = None,
                    y_axis_data: list = None,
                    color_sequence: list = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf", "#fee090",
                                            "#fdae61", "#f46d43", "#d73027", "#a50026"],
                    label_show=False, label_font_size=8,
                    title: str = "",
                    width: str = "100%", height: str = "500px",**kwargs) -> Echarts:
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
    df = data_frame[[x_field, y_field]].copy()
    df[x_field] = df[x_field].astype(str)
    df[y_field] = df[y_field].astype(str)
    df[label_field + '_label'] = data_frame[label_field]
    df[color_field + '_color'] = data_frame[color_field]
    options = {
        'animation': False,
        'title': {'text': title},
        'tooltip': {
            'position': 'top',
            'color': "black",
            'backgroundColor': "rgba(255,255,255,0.8)",
            'formatter': "{c}"
        },
        'grid': {'left': "2%", 'right': '3%'},
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
            }
        }]
    }
    if "date" in str(df[x_field].dtype) or "object" in str(df[x_field].dtype):
        options['xAxis'][0]['type'] = 'category'
        options['xAxis'][1]['type'] = 'category'
    if "date" in str(df[y_field].dtype) or "object" in str(df[y_field].dtype):
        options['yAxis']['type'] = 'category'

    options.update(kwargs)
    return Echarts(options=options, width=width, height=height)


def radar_echarts(data_frame: pd.DataFrame, name_field: str = None, indicator_field_list: list = None,
                  fill: bool = True,
                  title: str = "",
                  width: str = "100%", height: str = "500px",**kwargs) -> Echarts:
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
        'animation': False,
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
    options.update(kwargs)
    return Echarts(options=options, width=width, height=height)


def calendar_heatmap_echarts(data_frame: pd.DataFrame, date_field: str = None, value_field: str = None,
                             title: str = "",
                             width: str = "100%", height: str = "300px",**kwargs) -> Echarts:
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
        'animation': False,
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
    options.update(kwargs)
    return Echarts(options=options, width=width, height=height)


def parallel_echarts(data_frame: pd.DataFrame, name_field: str = None, indicator_field_list: list = [],
                     title: str = "",
                     width: str = "100%", height: str = "500px",**kwargs) -> Echarts:
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
    options.update(kwargs)
    return Echarts(options=options, width=width, height=height)


def sankey_echarts(data_frame: pd.DataFrame, source_field: str = None, target_field: str = None,
                   value_field: str = None, source_depth_field: str = None, target_depth_field: str = None,
                   title: str = "",
                   width: str = "100%", height: str = "500px",**kwargs) -> Echarts:
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
    options.update(kwargs)
    return Echarts(options=options, width=width, height=height)


def theme_river_echarts(data_frame: pd.DataFrame, date_field: str = None, value_field: str = None,
                        theme_field: str = None,
                        title: str = "",
                        width: str = "100%", height: str = "500px",**kwargs) -> Echarts:
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
    options.update(kwargs)
    return Echarts(options=options, width=width, height=height)


def sunburst_echarts(data_frame: pd.DataFrame, category_field_list: list = [], value_field: str = None,
                     title: str = "",
                     font_size: int = 8, node_click=False,
                     width: str = "100%", height: str = "500px",**kwargs) -> Echarts:
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
    options.update(kwargs)
    return Echarts(options, height=height, width=width)


def mark_area_echarts(data_frame: pd.DataFrame, x1: str, y1: str, x2: str, y2: str, label: str, title: str = 'area',
                      label_position: str = "top", label_font_size: int = 10, label_distance: int = 10,
                      label_font_color: str = 'inherit', fill_color: str = "inherit", fill_opacity: float = 0.3,**kwargs
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
    :param label_position: top / left / right / bottom / inside / insideLeft / insideRight / insideTop / insideBottom / insideTopLeft / insideBottomLeft / insideTopRight / insideBottomRight
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
    options.update(kwargs)
    return Echarts(options)


def mark_background_echarts(data_frame: pd.DataFrame, x1: str, x2: str, label: str, title: str = 'area',
                      label_position: str = "top", label_font_size: int = 10, label_distance: int = 10,
                      label_font_color: str = 'inherit', fill_color: str = "inherit", fill_opacity: float = 0.3,**kwargs
                      ):
    """
    在现有图表上叠加背景，不能单独显示

    :param data_frame:
    :param x1: 左上方顶点x坐标对应列
    :param x2: 右下方顶点x坐标对应列
    :param label: 矩形标签文字对应列
    :param title: 用于在legend显示，控制叠加矩形显示隐藏
    :param label_position: top / left / right / bottom / inside / insideLeft / insideRight / insideTop / insideBottom / insideTopLeft / insideBottomLeft / insideTopRight / insideBottomRight
    :param label_distance:
    :param label_font_size:
    :param label_font_color:
    :param fill_opacity:
    :param fill_color:

    :return:
    """
    options = copy.deepcopy(ECHARTS_BASE_OVERLAY_OPTIONS)
    rows = data_frame[[x1, x2, label]].to_dict(orient='records')
    data = [[{'name': row[label], 'xAxis': row[x1]},
             {'xAxis': row[x2]}] for row in rows]
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
    options.update(kwargs)
    return Echarts(options)



def mark_segment_echarts(data_frame: pd.DataFrame, x1: str, y1: str, x2: str, y2: str, label: str, title="segment",
                         show_label: bool = False,
                         label_position: str = "middle", label_font_size: int = 10, label_distance: int = 10,
                         label_font_color: str = 'inherit', symbol_start: str = 'circle', symbol_end: str = 'circle',
                         line_width: int = 2, line_type: str = "solid",**kwargs):
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
    :param label_position: top / left / right / bottom / inside / insideLeft / insideRight / insideTop / insideBottom / insideTopLeft / insideBottomLeft / insideTopRight / insideBottomRight
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
    options.update(kwargs)
    return Echarts(options)


def mark_label_echarts(data_frame: pd.DataFrame, x: str, y: str, label: str, title="point",
                       label_position: str = "top", label_font_size: int = 10, label_distance: int = 10,
                       label_font_color: str = 'inherit', label_background_color: str = "transparent",**kwargs):
    """
    在现有图表上叠加标签，不能单独显示

    :param data_frame:
    :param x: 左上方顶点x坐标对应列
    :param y: 左上方顶点y坐标对应列
    :param label: 矩形标签文字对应列
    :param title: 用于在legend显示，控制叠加矩形显示隐藏
    :param label_position: top / left / right / bottom / inside / insideLeft / insideRight / insideTop / insideBottom / insideTopLeft / insideBottomLeft / insideTopRight / insideBottomRight
    :param label_distance: 10
    :param label_font_color: inherit
    :param label_font_size: 12
    :param label_background_color: transparent
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
    options.update(kwargs)
    return Echarts(options)


def mark_vertical_line_echarts(data_frame: pd.DataFrame, x: str, label: str, title="vertical_line",
                               label_position: str = 'insideStartTop', label_font_size: int = 10, label_distance: int = 10,
                               label_font_color: str = 'inherit',**kwargs):
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
            'borderWidth':1,
            'borderColor':'#000',
            'backgroundColor':"white",
            'padding':5,
            'width':150,
            'overflow':'breakAll',
            'show': False,
            'formatter': "{b}",
            'rotate': 0  # 设置为0度以横向显示
        },
        'emphasis':{'label':{'show':True}},
        'symbol': [None, None],
        'data': data
    }
    options['series'][0]['markLine'] = base_mark_line_options
    options['legend']['data'] = [title]
    options['series'][0]['name'] = title
    options.update(kwargs)
    return Echarts(options)


def mark_horizontal_line_echarts(data_frame: pd.DataFrame, y: str, label: str, title="vertical_line",
                                 label_position: str = 'middle', label_font_size: int = 10, label_distance: int = 10,
                                 label_font_color: str = 'inherit',**kwargs):
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
    options.update(kwargs)
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
                      height: str = "500px",**kwargs):
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
    options.update(kwargs)
    return Echarts(options, with_gl=True, height=height, width=width)


def bar3d_echarts(data_frame: pd.DataFrame, x_field: str = None, y_field: str = None, z_field: str = None,
                  color_field: str = None,
                  color_sequence: list = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf",
                                          "#fee090",
                                          "#fdae61", "#f46d43", "#d73027", "#a50026"], info: str = None,
                  title: str = "",
                  width: str = "100%",
                  height: str = "500px",**kwargs):
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
    options.update(kwargs)
    return Echarts(options, with_gl=True, height=height, width=width)


def drawdown_echarts(data_frame: pd.DataFrame, time_field: str, value_field: str, code_field: str, title="",
                     width="100%",
                     height='500px',**kwargs) -> Echarts:
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
    df_pivot = df.pivot_table(index=time_field, columns=code_field, values=value_field).bfill().ffill()
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
    options.update(kwargs)
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


__all__ = ['scatter_echarts', 'line_echarts', 'bar_echarts', 'pie_echarts', 'candlestick_echarts', 'radar_echarts',
           'heatmap_echarts', 'calendar_heatmap_echarts', 'parallel_echarts', 'sankey_echarts', 'theme_river_echarts',
           'sunburst_echarts', 'mark_area_echarts', 'mark_segment_echarts', 'mark_label_echarts',
           'mark_vertical_line_echarts', 'mark_horizontal_line_echarts', 'scatter3d_echarts', 'bar3d_echarts',
           'drawdown_echarts', 'minute_echarts','mark_background_echarts']

if __name__ == "__main__":
    print([func for func in list(locals().keys()) if func[0:2] != '__'])
