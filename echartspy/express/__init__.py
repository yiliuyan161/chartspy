import pandas as pd

from echartspy import Echarts, Js, Tools


def scatter(data_frame: pd.DataFrame, x: str = None, y: str = None, group: str = None, size: str = None,
            size_max: int = 30, title: str = "", width: str = "100%", height: str = "500px") -> Echarts:
    """
    绘制scatter图
    :param data_frame: 必填 DataFrame
    :param x: 必填 x轴映射的列
    :param y: 必填 y轴映射的列
    :param group: 可选 分组列，不同颜色表示
    :param size: 可选 原点大小列
    :param size_max: 可选
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    options = {
        'animation': True,
        'legend': {
            'data': []
        },
        'tooltip': {
            'trigger': 'item',
            'backgroundColor': 'rgba(255, 255, 255, 0.8)'
        },
        'xAxis': {
            'type': 'value',
        },
        'yAxis': {
            'type': 'value',
            'splitLine': {
                'show': True
            }
        },
        'dataZoom': [
            {
                'type': 'inside',
                'xAxisIndex': 0,
                'start': 1,
                'end': 100
            },
            {
                'type': 'inside',
                'yAxisIndex': 0,
                'start': 1,
                'end': 100
            }
        ],
        'series': []
    }
    df = data_frame.sort_values(x, ascending=True).copy()
    options['title'] = {"text": title}
    if "date" in str(df[x].dtype) or "object" in str(df[x].dtype):
        options['xAxis']['type'] = 'category'
    if group is not None:
        groups = df[group].unique()
        for group_value in groups:
            df_series = df[df[group] == group_value]
            series = {
                'name': group_value,
                'type': 'scatter'
            }
            if size is not None:
                max_size_value = df[size].max()
                series['symbolSize'] = Js(Tools.wrap_template("""
                        function(val) {
                         return val[2]/{{max_size_value}}*{{size_max}};
                        }
                    """, **locals()))
                series['data'] = df_series[[x, y, size]].values.tolist()
            else:
                series['data'] = df_series[[x, y]].values.tolist()
            options['legend']['data'].append(group_value)
            options['series'].append(series)
    else:
        series = {
            'type': 'scatter'
        }
        if size is not None:
            max_size_value = df[size].max()
            series['symbolSize'] = Js(Tools.wrap_template("""
                    function(val) {
                        return val[2]/{{max_size_value}}*{{size_max}};
                    }
                """, **locals()))
            series['data'] = df[[x, y, size]].values.tolist()
        else:
            series['data'] = df[[x, y]].values.tolist()
        options['series'].append(series)
    return Echarts(options=options, width=width, height=height)


def line(data_frame: pd.DataFrame, x: str = None, y: str = None, group: str = None, title: str = "",
         width: str = "100%", height: str = "500px") -> Echarts:
    """
    绘制线图
    :param data_frame: 必填 DataFrame
    :param x: 必填 x轴映射的列
    :param y: 必填 y轴映射的列
    :param group: 可选 分组列，不同颜色表示
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    options = {
        'animation': True,
        'legend': {
            'data': []
        },
        'tooltip': {
            'trigger': 'item',
            'backgroundColor': 'rgba(255, 255, 255, 0.8)'
        },
        'xAxis': {
            'type': 'value',
        },
        'yAxis': {
            'type': 'value',
            'splitLine': {
                'show': True
            }
        },
        'dataZoom': [
            {
                'type': 'inside',
                'xAxisIndex': 0,
                'start': 1,
                'end': 100
            },
            {
                'type': 'inside',
                'yAxisIndex': 0,
                'start': 1,
                'end': 100
            }
        ],
        'series': []
    }
    df = data_frame.sort_values(x, ascending=True).copy()
    options['title'] = {"text": title}
    if "date" in str(df[x].dtype) or "object" in str(df[x].dtype):
        options['xAxis']['type'] = 'category'
    if group is not None:
        groups = df[group].unique()
        for group_value in groups:
            df_series = df[df[group] == group_value]
            series = {'name': group_value, 'type': 'line', 'data': df_series[[x, y]].values.tolist()}
            options['legend']['data'].append(group_value)
            options['series'].append(series)
    else:
        series = {'type': 'line', 'data': df[[x, y]].values.tolist()}
        options['series'].append(series)
    return Echarts(options=options, width=width, height=height)


def bar(data_frame: pd.DataFrame, x: str = None, y: str = None, group: str = None, stacked: bool = False,
        title: str = "",
        width: str = "100%", height: str = "500px") -> Echarts:
    """

    :param data_frame: 必填 DataFrame
    :param x: 必填 x轴映射的列
    :param y: 必填 y轴映射的列
    :param group: 可选 分组列，不同颜色表示
    :param stacked:是否堆叠
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    options = {
        'animation': True,
        'legend': {
            'data': []
        },
        'tooltip': {
            'trigger': 'item',
            'backgroundColor': 'rgba(255, 255, 255, 0.8)'
        },
        'xAxis': {
            'type': 'value'
        },
        'yAxis': {
            'type': 'value',
            'splitLine': {
                'show': True
            }
        },
        'dataZoom': [
            {
                'type': 'inside',
                'xAxisIndex': 0,
                'start': 1,
                'end': 100
            },
            {
                'type': 'inside',
                'yAxisIndex': 0,
                'start': 1,
                'end': 100
            }
        ],
        'series': []
    }
    df = data_frame.sort_values(x, ascending=True).copy()
    options['title'] = {"text": title}
    if "date" in str(df[x].dtype) or "object" in str(df[x].dtype):
        options['xAxis']['type'] = 'category'
    if group is not None:
        groups = df[group].unique()
        for group_value in groups:
            df_series = df[df[group] == group_value]
            series = {'name': group_value, 'type': 'bar', 'data': df_series[[x,y]].values.tolist()}
            if stacked:
                series['stack'] = "all"
            options['legend']['data'].append(group_value)
            options['series'].append(series)
    else:
        series = {'type': 'bar', 'data': df[[x,y]].values.tolist()}
        options['series'].append(series)
    return Echarts(options=options, width=width, height=height)


def pie(data_frame: pd.DataFrame, name: str = None, value: str = None, rose_type: str = None, title: str = "",
        width: str = "100%", height: str = "500px") -> Echarts:
    """

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
                'roseType': False if rose_type is None else rose_type,
                'itemStyle': {
                    'borderRadius': 5
                },
                'label': {
                    'show': False
                },
                'emphasis': {
                    'label': {
                        'show': True
                    }
                },
                'data': df[['name', 'value']].to_dict(orient="records")
            }
        ]
    }
    return Echarts(options=options, width=width, height=height)


def candlestick(data_frame: pd.DataFrame, time: str = 'time', opn: str = "open", high: str = 'high', low: str = 'low',
                clo: str = 'close',
                vol: str = 'volume', mas: list = [5, 10, 30], kline_overlap_options: list = [], title: str = "",
                width: str = "100%", height: str = "600px", left: str = '10%') -> Echarts:
    """
    绘制K线
    :param data_frame:
    :param time: 时间列名
    :param opn: open列名
    :param high: high列名
    :param low: low列名
    :param clo: close列名
    :param vol: volume列名
    :param mas: 均线组
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :param left: 左侧padding宽度
    :return:
    """
    df = data_frame[[time, opn, high, low, clo, vol]].sort_values(time, ascending=True).copy()
    volumes = list((df[vol] / 1000000).round(2).values)
    vol_filter = (df[vol] / 1000000).quantile([0.05, 0.95]).values
    bar_items = [({"value": vol} if vol >= vol_filter[0] and vol <= vol_filter[1] else (
        {"value": vol, "itemStyle": {"color": "red"}} if vol > vol_filter[1] else {"value": vol,
                                                                                   "itemStyle": {"color": "green"}}))
                 for vol in volumes]

    options = {
        'animation': False,
        'title': {'text': title},
        'legend': {'top': 10, 'left': 'center', 'data': ["K线"]},
        'tooltip': {
            'trigger': 'axis', 'axisPointer': {'type': 'cross'},
            'borderWidth': 1,
            'borderColor': '#ccc',
            'padding': 10,
            'formatter': Js("""
                function(params){
                    console.log(params);
                    var dt = params[0]['axisValue'];
                    var labels = [];
                    labels.push('时间: ' + dt + '<br/>');
                    params.sort(function(a, b) {
                      if (a.seriesName < b.seriesName ) {return -1;}
                      else if (a.seriesName > b.seriesName ) {return 1;}
                      else{ return 0;}
                    });
                    for (var i=0;i<params.length;i++)
                    { 
                       var param= params[i];
                       if(param.seriesType =='candlestick'){
                         labels.push('open: ' + param.data[1] + '<br/>');
                         labels.push('close: ' + param.data[2] + '<br/>');
                         labels.push('low: ' + param.data[3] + '<br/>');
                         labels.push('high: ' + param.data[4] + '<br/>');
                       }else{
                         labels.push(param.seriesName+': ' + param.data + '<br/>');
                       }
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
            {'left': left, 'right': '0%', 'height': '70%'},
            {'left': left, 'right': '0%', 'top': '71%', 'height': '16%'}
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
                'type': 'log',
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
                'axisLabel': {'show': True, 'formatter': '{value}M'},
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
                'name': 'K线',
                'type': 'candlestick',
                'data': df[[opn, clo, high, low]].values.tolist(),

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
    if len(kline_overlap_options) > 0:
        for overlap_option in kline_overlap_options:
            options["legend"]["data"] = options["legend"]["data"].extend(overlap_option["legend"]["data"])
            options["series"] = options['series'].extend(overlap_option["series"])
    return Echarts(options=options, width=width, height=height)


def radar(data_frame: pd.DataFrame, name: str = None, indicators: list = None, fill: bool = True, title: str = "",
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
            'data': []
        },
        'radar': {
            'shape': 'circle',
            'indicator': []
        },
        'series': [{
            'name': title,
            'type': 'radar',
            'data': []
        }]
    }
    df = data_frame[[name] + indicators].copy()
    if fill:
        options['series'][0]['areaStyle'] = {'opacity': 0.2}
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


def heatmap(data_frame: pd.DataFrame, x: str = None, y: str = None, value: str = None, title: str = "",
            width: str = "100%", height: str = "500px") -> Echarts:
    """
    二维热力图
    :param data_frame: 必填 DataFrame
    :param x: 必填 x轴映射的列
    :param y: 必填 y轴映射的列
    :param value: 可选 分组列，不同颜色表示
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    df = data_frame[[x, y, value]].copy()
    options = {
        'title': {'text': title},
        'tooltip': {'position': 'top'},
        'grid': {
            'height': '50%',
            'top': '10%'
        },
        'xAxis': {
            'type': 'category',
            'data': sorted(df[x].tolist()),
            'splitArea': {
                'show': True
            }
        },
        'yAxis': {
            'type': 'category',
            'data': sorted(df[y].tolist()),
            'splitArea': {
                'show': True
            }
        },
        'visualMap': {
            'min': 0,
            'max': 10,
            'calculable': True,
            'orient': 'horizontal',
            'left': 'center',
            'bottom': '15%'
        },
        'series': [{
            'name': 'Punch Card',
            'type': 'heatmap',
            'data': df[[x, y, value]].values.tolist(),
            'label': {
                'show': True
            },
            'emphasis': {
                'itemStyle': {
                    'shadowBlur': 10,
                    'shadowColor': 'rgba(0, 0, 0, 0.5)'
                }
            }
        }]
    }
    return Echarts(options=options, width=width, height=height)


def calendar_heatmap(data_frame: pd.DataFrame, date: str = None, value: str = None,
                     title: str = "",
                     width: str = "100%", height: str = "300px") -> Echarts:
    """

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
            'top': 30,
            'left': 'center',
            'text': title
        },
        'tooltip': {'formatter': "{c}"},
        'visualMap': {
            'min': value_min,
            'max': value_max,
            'type': 'piecewise',
            'orient': 'horizontal',
            'left': 'center',
            'top': 65,
            'hoverLink': True
        },
        'calendar': {
            'top': 120,
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
            'data': df[[date, value]].values.tolist()
        }
    }
    return Echarts(options=options, width=width, height=height)


def parallel(data_frame: pd.DataFrame, name: str = None, axis: list = [],
             title: str = "",
             width: str = "100%", height: str = "500px") -> Echarts:
    """

    :param data_frame:
    :param name: name列
    :param axis: 维度列list
    :param title: 可选标题
    :param width: 输出div的宽度 支持像素和百分比 比如800px/100%
    :param height: 输出div的高度 支持像素和百分比 比如800px/100%
    :return:
    """
    df = data_frame[[name] + axis].copy()
    options = {
        'title': {'text': title},
        'legend': {
            'data': []
        },
        'parallelAxis': [],
        'series': []
    }
    value_dict_list = df.to_dict(orient='records')
    for i in range(0, len(axis)):
        if "object" in str(df[axis[i]].dtype):
            col = {'dim': i, 'name': axis[i], 'type': 'category', 'data': sorted(df[axis[i]].unique())}
        else:
            col = {'dim': i, 'name': axis[i], 'min': "dataMin", 'max': "dataMax"}
        options['parallelAxis'].append(col)
    for value_dict in value_dict_list:
        series = {
            'name': value_dict[name],
            'type': 'parallel',
            'lineStyle': {width: 3},
            'data': [[value_dict[col] for col in axis]]
        }
        options['series'].append(series)
        options['legend']['data'].append(value_dict[name])
    return Echarts(options=options, width=width, height=height)


def sankey(data_frame: pd.DataFrame, source: str = None, target: str = None, value: str = None, title: str = "",
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
    df.columns = ['source', 'target', 'value']
    names = list(set(df[source].unique()).union(set(df[target].unique())))
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
            'label': {
                'color': 'rgba(0,0,0,0.7)',
                'fontFamily': 'Arial',
                'fontSize': 10
            }
        }]
    }
    return Echarts(options=options, width=width, height=height)


def theme_river(data_frame: pd.DataFrame, date: str = None, value: str = None, theme: str = None, title: str = "",
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
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'line',
                'lineStyle': {
                    'color': 'rgba(0,0,0,0.2)',
                    'width': 1,
                    'type': 'solid'
                }
            }
        },
        'legend': {
            'data': list(df[theme].unique())
        },
        'singleAxis': {
            'top': 50,
            'bottom': 50,
            'axisTick': {},
            'axisLabel': {},
            'type': 'time',
            'axisPointer': {
                'animation': True,
                'label': {
                    'show': True
                }
            },
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
