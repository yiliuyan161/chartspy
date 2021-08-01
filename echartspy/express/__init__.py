import pandas as pd

from echartspy import Echarts, Js, wrap_template

BASE_GRID_OPTIONS = {
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
        'min': 'dataMin',
        'max': 'dataMax'
    },
    'yAxis': {
        'type': 'value',
        'min': 'dataMin',
        'max': 'dataMax',
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


def scatter(data_frame: pd.DataFrame, x: str = None, y: str = None, group: str = None, size: str = None,
            size_max: int = 10, title: str = "", width: str = "100%", height: str = "500px") -> Echarts:
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
    options = BASE_GRID_OPTIONS.copy()
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
                series['symbolSize'] = Js(wrap_template("""
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
            series['symbolSize'] = Js(wrap_template("""
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
    options = BASE_GRID_OPTIONS.copy()
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
    options = BASE_GRID_OPTIONS.copy()
    df = data_frame.sort_values(x, ascending=True).copy()
    options['title'] = {"text": title}
    if "date" in str(df[x].dtype) or "object" in str(df[x].dtype):
        options['xAxis']['type'] = 'category'
    if group is not None:
        groups = df[group].unique()
        for group_value in groups:
            df_series = df[df[group] == group_value]
            series = {'name': group_value, 'type': 'bar', 'data': df_series[[x, y]].values.tolist()}
            if stacked:
                series['stack'] = "all"
            options['legend']['data'].append(group_value)
            options['series'].append(series)
    else:
        series = {'type': 'bar', 'data': df[[x, y]].values.tolist()}
        options['series'].append(series)
    return Echarts(options=options, width=width, height=height)


def pie(data_frame: pd.DataFrame, name: str = None, value: str = None, rose_type: str = None, title: str = "",
        width: str = "100%", height: str = "500px") -> Echarts:
    """

    :param data_frame: 必填 DataFrame
    :param name: name列名
    :param value: value列名
    :param rose_type: radius/area/None
    :param title:
    :param width:
    :param height:
    :return:
    """
    df = data_frame[[name, value]].sort_values(name, ascending=True).copy()
    df.columns = ['name', 'value']
    options = {
        'title': {
            'text': title,
            'left': 'center'
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
                vol: str = 'vol', mas: list = [5, 10, 30], title: str = "",
                width: str = "100%", height: str = "500px") -> Echarts:
    df = data_frame[[time, opn, high, low, clo, vol]].sort_values(time, ascending=True).copy()
    options = {
        'animation': False,
        'title': {'text': title},
        'legend': {'top': 10, 'left': 'center', 'data': ["K线"]},
        'tooltip': {
            'trigger': 'axis', 'axisPointer': {'type': 'cross'},
            'borderWidth': 1,
            'borderColor': '#ccc',
            'padding': 10,
            'formatter': Js("""function(params){
                    var dt = params[0]['axisValue']
                    var labels=[],
                    labels.append('时间: ' + dt + '<br/>)
                    params.sort(function(a, b) {
                      if (a.seriesName < b.seriesName ) {return -1;}
                      else if (a.seriesName > b.seriesName ) {return 1;}else{return 0;}
                    })
                    for (var i=0;i<params.length;i++)
                    { 
                       var param= params[i];
                       if(param.seriesType =="candlestick"){
                         labels.append('open: ' + param.data[1] + '<br/>');
                         labels.append('close: ' + param.data[2] + '<br/>');
                         labels.append('low: ' + param.data[3] + '<br/>');
                         labels.append('high: ' + param.data[4] + '<br/>');
                       }else{
                         labels.append(param.seriesName+': ' + param.data + '<br/>');
                       }
                    }
                    return labels.join('');
                }"""),
            'textStyle': {'color': '#000'},
            'position': Js("""
                function (pos, params, el, elRect, size) {
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
            {'left': '10%', 'right': '8%', 'height': '70%'},
            {'left': '10%', 'right': '8%', 'top': '71%', 'height': '16%'}
        ],
        'xAxis': [
            {
                'type': 'category',
                'data': df[time],
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
                'data': df[time],
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
                'axisLabel': {'show': True},
                'axisLine': {'show': False},
                'axisTick': {'show': True},
                'splitLine': {'show': False}
            },
            {
                'scale': True,
                'gridIndex': 1,
                'splitNumber': 2,
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
                'start': 80,
                'end': 100
            }
        ],
        'series': [
            {
                'name': 'K线',
                'type': 'candlestick',
                'data': df[[opn, clo, high, low]],

            },
            {
                'name': 'Volume',
                'type': 'bar',
                'xAxisIndex': 1,
                'yAxisIndex': 1,
                'data': df[vol]
            }
        ]
    }
    for ma_len in mas:
        name = "MA" + str(ma_len)
        df[name] = df[clo].rolling(ma_len).mean()
        series_ma = {
            'name': name,
            'type': 'line',
            'data': df[name],
            'smooth': True,
            'showSymbol': False,
            'lineStyle': {'opacity': 0.5}
        }
        options['series'].append(series_ma)
        options['legend']['data'].append(name)
    return Echarts(options=options, width=width, height=height)
