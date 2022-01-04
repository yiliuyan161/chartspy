#!/usr/bin/env python
# coding=utf-8
import copy

import pandas as pd

from chartspy import Echarts
from chartspy.base import Js, Tools

# 二维坐标系统基础配置适用  scatter,bar,line
ECHARTS_BASE_GRID_OPTIONS = {
    'legend': {
        'data': []
    },
    'tooltip': {
        'trigger': 'axis', 'axisPointer': {'type': 'cross'},
        'borderWidth': 1,
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


def scatter_echarts(data_frame: pd.DataFrame, x: str = None, y: str = None, symbol: str = None, size: str = None,
                    size_range=[2, 30], color: str = None,
                    color_sequence: list = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf", "#fee090",
                                            "#fdae61", "#f46d43", "#d73027", "#a50026"], info: str = None,
                    opacity=0.5, tooltip_trigger="axis", title: str = "",
                    width: str = "100%",
                    height: str = "500px") -> Echarts:
    """
    scatter chart

    :param data_frame: 必填 DataFrame
    :param x: 必填 x轴映射的列
    :param y: 必填 y轴映射的列
    :param symbol: 'circle', 'rect', 'roundRect', 'triangle', 'diamond', 'pin', 'arrow', 'none',image://dataURI(), path://(svg)
    :param size: 可选 原点大小列
    :param size_range: 可选 点大小区间
    :param info: 额外信息tooltip显示
    :param color:颜色映射的列
    :param color_sequence:
    :param opacity:
    :param tooltip_trigger: tooltip 触发类型 axis和 item
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    df = data_frame.copy()
    if x is None:
        df["x_col_echartspy"] = df.index
        x = "x_col_echartspy"
    options = copy.deepcopy(ECHARTS_BASE_GRID_OPTIONS)
    options['title'] = {"text": title}
    if "date" in str(df[x].dtype) or "object" in str(df[x].dtype):
        options['xAxis']['type'] = 'category'
    if "date" in str(df[y].dtype) or "object" in str(df[y].dtype):
        options['yAxis']['type'] = 'category'
    title = y if title == '' else title
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
    series['dimensions'] = [x, y]
    series['data'] = df[[x, y]].values.tolist()
    if size is not None or color is not None:
        options['visualMap'] = []
    if size is not None:
        max_size_value = df[size].max()
        min_size_value = df[size].min()
        series['dimensions'].append(size)
        size_list = df[size].tolist()
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
        if "date" in str(df[size].dtype) or "object" in str(df[size].dtype):
            visual_map_size['type'] = 'piecewise'
        else:
            visual_map_size['type'] = 'continuous'
            visual_map_size['min'] = min_size_value
            visual_map_size['max'] = max_size_value
        options['visualMap'].append(visual_map_size)

    if color is not None:
        series['dimensions'].append(color)
        color_list = df[color].tolist()
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
        if "date" in str(df[color].dtype) or "object" in str(df[color].dtype):
            visual_map_color['type'] = 'piecewise'
        else:
            visual_map_color['type'] = 'continuous'
            visual_map_color['min'] = df[color].min()
            visual_map_color['max'] = df[color].max()
        options['visualMap'].append(visual_map_color)

    if info is not None:
        series['dimensions'].append(info)
        info_list = df[info].tolist()
        for i in range(0, len(info_list)):
            series['data'][i].append(info_list[i])
    options['series'].append(series)
    options['legend']['data'].append(title)
    return Echarts(options=options, width=width, height=height)


def line_echarts(data_frame: pd.DataFrame, x: str = None, y: str = None, tooltip_trigger="axis", title: str = "",
                 width: str = "100%", height: str = "500px") -> Echarts:
    """
    绘制线图
    :param data_frame: 必填 DataFrame
    :param x: 必填 x轴映射的列
    :param y: 必填 y轴映射的列
    :param tooltip_trigger: axis item
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    options = copy.deepcopy(ECHARTS_BASE_GRID_OPTIONS)
    title = y if title == '' else title
    df = data_frame.copy()
    if x is None:
        df["x_col_echartspy"] = df.index
        x = "x_col_echartspy"
    options['title'] = {"text": title}
    if "date" in str(df[x].dtype) or "object" in str(df[x].dtype):
        options['xAxis']['type'] = 'category'
    series = {'name': title, 'type': 'line', 'dimensions': [x, y], 'data': df[[x, y]].values.tolist(), 'emphasis': {
        'itemStyle': {
            'borderColor': "#333",
            'borderWidth': 1,
            'shadowColor': 'rgba(0, 0, 0, 0.5)',
            'shadowBlur': 15
        }
    }}
    if tooltip_trigger == 'item':
        del options['axisPointer']
        options['tooltip'] = {
            'trigger': 'item',
            'borderWidth': 1,
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
    options['legend']['data'].append(title)
    options['series'].append(series)

    return Echarts(options=options, width=width, height=height)


def bar_echarts(data_frame: pd.DataFrame, x: str = None, y: str = None, stack: str = "all", tooltip_trigger="axis",
                title: str = "",
                width: str = "100%", height: str = "500px") -> Echarts:
    """

    :param data_frame: 必填 DataFrame
    :param x: 必填 x轴映射的列
    :param y: 必填 y轴映射的列
    :param stack:堆叠分组
    :param tooltip_trigger: axis item
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:Echarts
    """
    options = copy.deepcopy(ECHARTS_BASE_GRID_OPTIONS)
    df = data_frame.copy()
    title = y if title == '' else title
    if x is None:
        df["x_col_echartspy"] = df.index
        x = "x_col_echartspy"
    options['title'] = {"text": title}
    if "date" in str(df[x].dtype) or "object" in str(df[x].dtype):
        options['xAxis']['type'] = 'category'
    series = {'name': title, 'type': 'bar', 'stack': stack, 'dimensions': [x, y], 'data': df[[x, y]].values.tolist(),
              'emphasis': {
                  'itemStyle': {
                      'borderColor': "#333",
                      'borderWidth': 1,
                      'shadowColor': 'rgba(0, 0, 0, 0.5)',
                      'shadowBlur': 15
                  }
              }}
    if tooltip_trigger == 'item':
        del options['axisPointer']
        options['tooltip'] = {
            'trigger': 'item',
            'borderWidth': 1,
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
    options['series'].append(series)
    options['legend']['data'].append(title)
    return Echarts(options=options, width=width, height=height)


def pie_echarts(data_frame: pd.DataFrame, name: str = None, value: str = None, rose_type: str = None, title: str = "",
                width: str = "100%", height: str = "500px") -> Echarts:
    """
    饼图
    :param data_frame: 必填 DataFrame
    :param name: name列名
    :param value: value列名
    :param rose_type: radius/area/None
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    df = data_frame[[name, value]].sort_values(name, ascending=True).copy()
    df.columns = ['name', 'value']
    options = {
        'title': {
            'text': title,
        },
        'tooltip': {
            'trigger': 'item',
            'formatter': '{a} <br/>{b} : {c} ({d}%)'
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


def candlestick_echarts(data_frame: pd.DataFrame, time: str = 'time', opn: str = "open", high: str = 'high',
                        low: str = 'low',
                        clo: str = 'close',
                        vol: str = 'volume', mas: list = [5, 10, 30], log_y: bool = True, title: str = "",
                        width: str = "100%", height: str = "600px", left: str = '10%') -> Echarts:
    """
    绘制K线
    :param data_frame:
    :param time: 时间列名, 如果指定的列不存在，使用index作为time
    :param opn: open列名
    :param high: high列名
    :param low: low列名
    :param clo: close列名
    :param vol: volume列名
    :param mas: 均线组
    :param log_y: y轴 log分布 底为1.1 一个格子对应10%
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :param left: 左侧padding宽度
    :return:
    """
    df = data_frame.copy()
    if time not in data_frame.columns:  # 使用index作为时间
        df[time] = df.index
    df[clo]=df[clo].fillna(method="ffill")
    df[opn]=df[opn].fillna(df[clo])
    df[high]=df[high].fillna(df[clo])
    df[low]=df[low].fillna(df[clo])
    df[vol]=df[vol].fillna(0)
    volumes = (df[vol]).round(2).tolist()
    vol_filter = (df[vol]).quantile([0.05, 0.95]).values
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
        'grid': [
            {'left': left, 'right': '3%', 'height': '70%'},
            {'left': left, 'right': '3%', 'top': '71%', 'height': '16%'}
        ],
        'xAxis': [
            {
                'type': 'category',
                'data': df[time].tolist(),
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
                'data': df[time].tolist(),
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
                'data': df[[opn, clo, low, high]].values.tolist(),
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
        df[name] = df[clo].rolling(ma_len).mean().round(2)
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


def radar_echarts(data_frame: pd.DataFrame, name: str = None, indicators: list = None, fill: bool = True,
                  title: str = "",
                  width: str = "100%", height: str = "500px") -> Echarts:
    """

    :param data_frame:
    :param name: name列
    :param indicators: indicators所有列名list
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
    df = data_frame[[name] + indicators].copy()
    if fill:
        options['series'][0]['areaStyle'] = {'opacity': 0.1}
    indicator_max_dict = df[indicators].max().to_dict()
    options['radar']['indicator'] = [{'name': key, "max": indicator_max_dict[key]} for key in indicator_max_dict.keys()]
    for record in df.to_dict(orient='records'):
        data = {
            'value': [record[indicator] for indicator in indicators],
            'name': record[name]
        }
        options['series'][0]['data'].append(data)
        options['legend']['data'].append(record[name])
    return Echarts(options=options, width=width, height=height)


def heatmap_echarts(data_frame: pd.DataFrame, x: str = None, y: str = None,
                    x_axis_data: list = None,
                    y_axis_data: list = None,
                    color: str = None,
                    color_sequence: list = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf", "#fee090",
                                            "#fdae61", "#f46d43", "#d73027", "#a50026"],
                    label: str = None, label_show=True, label_font_size=8,
                    title: str = "",
                    width: str = "100%", height: str = "500px") -> Echarts:
    """
    二维热度图

    :param data_frame: 必填 DataFrame
    :param x: 必填 x轴映射的列
    :param y: 必填 y轴映射的列
    :param y_axis_data: x轴顺序 不提供直接按值排序
    :param x_axis_data: y轴顺序 不提供直接按值排序
    :param color: color映射列
    :param color_sequence: color色卡序列
    :param label: label映射列 必须是数字类型
    :param label_font_size: 8
    :param label_show: 是否显示label
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    label = color if label is None else label
    df = data_frame[[x, y, label, color]].copy()
    df[x] = df[x].astype(str)
    df[y] = df[y].astype(str)
    df.columns = [x, y, label + '_label', color + '_color']
    options = {
        'title': {'text': title},
        'tooltip': {
            'position': 'top',
            'formatter': "{c}"
        },
        'xAxis': [{
            'type': 'value',
            'data': [str(v) for v in sorted(df[x].unique())] if x_axis_data is None else x_axis_data,
            'splitArea': {
                'show': True
            }
        }, {
            'type': 'value',
            'data': [str(v) for v in sorted(df[x].unique())] if x_axis_data is None else x_axis_data,
            'splitArea': {
                'show': True
            }
        }],
        'yAxis': {
            'type': 'value',
            'data': [str(v) for v in sorted(df[y].unique())] if y_axis_data is None else y_axis_data,
            'splitArea': {
                'show': True
            }
        },
        'visualMap': {
            'min': df[color + '_color'].min(),
            'max': df[color + '_color'].max(),
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
    if "date" in str(df[x].dtype) or "object" in str(df[x].dtype):
        options['xAxis'][0]['type'] = 'category'
        options['xAxis'][1]['type'] = 'category'
    if "date" in str(df[y].dtype) or "object" in str(df[y].dtype):
        options['yAxis']['type'] = 'category'
    return Echarts(options=options, width=width, height=height)


def calendar_heatmap_echarts(data_frame: pd.DataFrame, date: str = None, value: str = None,
                             title: str = "",
                             width: str = "100%", height: str = "300px") -> Echarts:
    """
    日历热度图，显示日期热度
    :param data_frame:
    :param date: 日期列
    :param value: 值列
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    df = data_frame[[date, value]].copy()
    value_max = df[value].max()
    value_min = df[value].min()
    date_start = pd.to_datetime(df[date].min()).strftime("%Y-%m-%d")
    date_end = pd.to_datetime(df[date].max()).strftime("%Y-%m-%d")
    df[date] = pd.to_datetime(df[date]).dt.strftime("%Y-%m-%d")
    options = {
        'title': {
            'text': title
        },
        'tooltip': {'formatter': "{c}"},
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
            'data': df[[date, value]].values.tolist()
        }
    }
    return Echarts(options=options, width=width, height=height)


def parallel_echarts(data_frame: pd.DataFrame, name: str = None, parallel_axis: list = [],
                     title: str = "",
                     width: str = "100%", height: str = "500px") -> Echarts:
    """
    平行坐标图,要求name列每行唯一 比如：显示每个报告期各财务指标
    :param data_frame:
    :param name: name列
    :param parallel_axis: 数据维度列list
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    df = data_frame[list(set([name] + parallel_axis))].copy()
    options = {
        'title': {'text': title},
        'legend': {
            'top': '20',
            'type': 'scroll',
            'data': []
        },
        'parallel': {'top': 80},
        'tooltip': {
            'trigger': 'item',
            'formatter': Js(Tools.wrap_template(""" function(params){
                    var dims={{dims}};
                    var value_dict={};
                    var labels=[params.seriesName+':<br/>'];
                    for(var i=0;i<dims.length;i++){
                        labels.push('<span>'+dims[i]+":"+params['value'][i]+'</span><br/>');
                    }
                    return labels.join("");
            }""", dims=str(parallel_axis))),
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
    for i in range(0, len(parallel_axis)):
        data_min = df[parallel_axis[i]].min()
        data_max = df[parallel_axis[i]].max()
        if 'int' in str(df[parallel_axis[i]].dtype) or 'float' in str(df[parallel_axis[i]].dtype):
            col = {
                'dim': i,
                'name': parallel_axis[i],
                'type': 'value',
                'min': round(data_min - (data_max - data_min) * 0.1, 2),
                'max': round(data_max + (data_max - data_min) * 0.1, 2)
            }
        else:
            col = {'dim': i, 'name': parallel_axis[i], 'type': 'category',
                   'data': sorted(df[parallel_axis[i]].unique())}

        options['parallelAxis'].append(col)
    for value_dict in value_dict_list:
        series = {
            'name': value_dict[name],
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
            'data': [[value_dict[col] for col in parallel_axis]]
        }

        options['series'].append(series)
        options['legend']['data'].append(value_dict[name])
    return Echarts(options=options, width=width, height=height)


def sankey_echarts(data_frame: pd.DataFrame, source: str = None, target: str = None, value: str = None, title: str = "",
                   width: str = "100%", height: str = "500px") -> Echarts:
    """

    :param data_frame:
    :param source: source列
    :param target: target列
    :param value: value列
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    df = data_frame[[source, target, value]].copy()
    names = list(set(df[source].unique()).union(set(df[target].unique())))
    df.columns = ['source', 'target', 'value']
    options = {
        'title': {
            'text': title,
            'left': 'center'
        },
        'series': [{
            'type': 'sankey',
            'data': [{'name': name} for name in names],
            'links': df.to_dict(orient='records'),
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


def theme_river_echarts(data_frame: pd.DataFrame, date: str = None, value: str = None, theme: str = None,
                        title: str = "",
                        width: str = "100%", height: str = "500px") -> Echarts:
    """

    :param data_frame:
    :param date: date列
    :param value: value列
    :param theme: theme列
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    df = data_frame[[date, value, theme]].copy()
    options = {
        'title': {'text': title},
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'cross'}
        },
        'legend': {
            'top': 40,
            'data': list(df[theme].unique())
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


def sunburst_echarts(data_frame: pd.DataFrame, category_cols: list = [], value_col: str = None, title: str = "",
                     font_size: int = 8, node_click=False,
                     width: str = "100%", height: str = "500px") -> Echarts:
    data = Tools.df2tree(data_frame, category_cols, value_col)
    options = {
        'title': {
            'text': title,
        },
        'tooltip': {
            'trigger': 'item',
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
    data = [[{'name': row[label], 'coord': [row[x1], row[y1]]}, {'coord': [row[x2], row[y2]]}] for row in rows]
    base_mark_area_options = {
        'itemStyle': {
            'opacity': fill_opacity
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
        data = [[{'name': str(row[label]), 'coord': [row[x1], row[y1]]}, {'coord': [row[x2], row[y2]]}] for row in rows]
    else:
        rows = data_frame[[x1, y1, x2, y2]].to_dict(orient='records')
        data = [[{'coord': [row[x1], row[y1]]}, {'coord': [row[x2], row[y2]]}] for row in rows]

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


def scatter3d_echarts(data_frame: pd.DataFrame, x: str = None, y: str = None, z: str = None, size: str = None,
                      size_range: list = [2, 10], color: str = None,
                      color_sequence: list = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf",
                                              "#fee090",
                                              "#fdae61", "#f46d43", "#d73027", "#a50026"], info: str = None,
                      title: str = "",
                      width: str = "100%",
                      height: str = "500px"):
    """
    3d 气泡图
    :param data_frame:
    :param x:
    :param y:
    :param z:
    :param size: size对应列，数值类型
    :param size_range: [1,10]
    :param color: 颜色列
    :param color_sequence:
    :param info: 额外信息
    :param title:
    :param width:
    :param height:
    :return:
    """
    options = {
        'title': {'text': title, 'left': 50},
        'tooltip': {},
        'xAxis3D': {
            'name': x,
            'type': 'value'

        },
        'yAxis3D': {
            'name': y,
            'type': 'value'
        },
        'zAxis3D': {
            'name': z,
            'type': 'value'
        },
        'grid3D': {
        }
    }
    if "date" in str(data_frame[x].dtype) or "object" in str(data_frame[x].dtype):
        options['xAxis3D']['type'] = 'category'
        options['xAxis3D']['data'] = sorted(list(data_frame[x].unique()))
    if "date" in str(data_frame[y].dtype) or "object" in str(data_frame[y].dtype):
        options['yAxis3D']['type'] = 'category'
        options['yAxis3D']['data'] = sorted(list(data_frame[y].unique()))
    if "date" in str(data_frame[z].dtype) or "object" in str(data_frame[z].dtype):
        options['zAxis3D']['type'] = 'category'
        options['zAxis3D']['data'] = sorted(list(data_frame[z].unique()))
    series = {
        'type': 'scatter3D',
        'name': title,
        'dimensions': [x, y, z],
        'data': data_frame[[x, y, z]].values.tolist()
    }
    if (color is not None) or (size is not None):
        options['visualMap'] = []
    if size is not None:
        series['dimensions'].append(size)
        size_list = data_frame[size].tolist()
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
            'min': data_frame[size].min(),
            'max': data_frame[size].max()
        }
        options['visualMap'].append(visual_map)

    if color is not None:
        series['dimensions'].append(color)
        color_list = data_frame[color].tolist()
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
        if "date" in str(data_frame[color].dtype) or "object" in str(data_frame[color].dtype):
            visual_map['type'] = 'piecewise'
            visual_map['categories'] = list(data_frame[color].unique())
        else:
            visual_map['type'] = 'continuous'
            visual_map['min'] = data_frame[color].min()
            visual_map['max'] = data_frame[color].max()
        options['visualMap'].append(visual_map)

    if info is not None:
        series['dimensions'].append(info)
        info_list = data_frame[info].tolist()
        for i in range(0, len(info_list)):
            series['data'][i].append(info_list[i])
    options['series'] = [series]
    return Echarts(options, with_gl=True, height=height, width=width)


def bar3d_echarts(data_frame: pd.DataFrame, x: str = None, y: str = None, z: str = None, color: str = None,
                  color_sequence: list = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf",
                                          "#fee090",
                                          "#fdae61", "#f46d43", "#d73027", "#a50026"], info: str = None,
                  title: str = "",
                  width: str = "100%",
                  height: str = "500px"):
    """
    3d bar
    :param data_frame:
    :param x:
    :param y:
    :param z:
    :param color:
    :param color_sequence:
    :param info:
    :param title:
    :param width:
    :param height:
    :return:
    """
    options = {
        'title': {'text': title, 'left': 20},
        'tooltip': {},
        'xAxis3D': {
            'name': x,
            'type': 'value'

        },
        'yAxis3D': {
            'name': y,
            'type': 'value'
        },
        'zAxis3D': {
            'name': z,
            'type': 'value'
        },
        'grid3D': {
        }
    }
    if "date" in str(data_frame[x].dtype) or "object" in str(data_frame[x].dtype):
        options['xAxis3D']['type'] = 'category'
        options['xAxis3D']['data'] = sorted(list(data_frame[x].unique()))
    if "date" in str(data_frame[y].dtype) or "object" in str(data_frame[y].dtype):
        options['yAxis3D']['type'] = 'category'
        options['yAxis3D']['data'] = sorted(list(data_frame[x].unique()))
    if "date" in str(data_frame[z].dtype) or "object" in str(data_frame[z].dtype):
        options['zAxis3D']['type'] = 'category'
        options['zAxis3D']['data'] = sorted(list(data_frame[x].unique()))
    series = {
        'type': 'bar3D',
        'name': title,
        'dimensions': [x, y, z],
        'data': data_frame[[x, y, z]].values.tolist(),
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
    if color is not None:
        options['visualMap'] = []
        series['dimensions'].append(color)
        color_list = data_frame[color].tolist()
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
        if "date" in str(data_frame[color].dtype) or "object" in str(data_frame[color].dtype):
            visual_map['type'] = 'piecewise'
            visual_map['categories'] = list(data_frame[color].unique())
        else:
            visual_map['type'] = 'continuous'
            visual_map['min'] = data_frame[color].min()
            visual_map['max'] = data_frame[color].max()
        options['visualMap'] = [visual_map]

    if info is not None:
        series['dimensions'].append(info)
        info_list = data_frame[info].tolist()
        for i in range(0, len(info_list)):
            series['data'][i].append(info_list[i])
    options['series'] = [series]
    return Echarts(options, with_gl=True, height=height, width=width)


def drawdown_echarts(data_frame: pd.DataFrame, time: str, price: str, code: str, title="", width="100%",
                     height='500px') -> Echarts:
    """
    回撤图
    :param data_frame: pd.DataFrame
    :param time: 时间列名
    :param price: 价格列名
    :param code: 资产编码列名
    :param title: 标题
    :param width: 宽度
    :param height: 高度
    :return:
    """
    df = data_frame[[time, price, code]].copy()
    df_pivot = df.pivot_table(index=time, columns=code, values=price).fillna(method='bfill').fillna(method='ffill')
    df_return = (((df_pivot / df_pivot.iloc[0]) - 1) * 100).round(2)
    df_cummax = df_pivot.cummax()
    df_drawdown = (((df_pivot - df_cummax) / df_cummax) * 100).round(2)
    sorted_date = sorted(df[time].unique())
    codes = df[code].unique()
    colors = ['red', 'blue', 'orange', 'pink', 'green', 'yellow', 'purple', 'sliver', 'gold', 'black']
    color_index = 0
    options = {
        'title': {'text': title},
        'legend': [{
            'type': "scroll",
            'data': list(df[code].unique())
        }],
        'tooltip': {
            'trigger': 'axis', 'axisPointer': {'type': 'cross'},
            'borderWidth': 1,
            'borderColor': '#ccc',
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
            'data': df_drawdown[item].to_frame().reset_index().values.tolist()
        }
        options['series'].append(return_series)
        options['series'].append(drawdown_series)
        color_index = (color_index + 1) % len(colors)
    return Echarts(options, height=height, width=width)


__all__ = ['scatter_echarts', 'line_echarts', 'bar_echarts', 'pie_echarts', 'candlestick_echarts', 'radar_echarts',
           'heatmap_echarts', 'calendar_heatmap_echarts', 'parallel_echarts', 'sankey_echarts', 'theme_river_echarts',
           'sunburst_echarts', 'mark_area_echarts', 'mark_segment_echarts', 'mark_label_echarts',
           'mark_vertical_line_echarts', 'mark_horizontal_line_echarts', 'scatter3d_echarts', 'bar3d_echarts',
           'drawdown_echarts']

if __name__ == "__main__":
    print([func for func in list(locals().keys()) if func[0:2] != '__'])
