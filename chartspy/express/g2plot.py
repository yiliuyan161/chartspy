from chartspy.g2plot import G2PLOT
from chartspy.base import Js, Tools


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
            'content': Js(Tools.wrap_template("""
                    function(item){
                      return (item['{{y_field}}'] * 100).toFixed(2);
                    }
                """, y_field=y_field))
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


def treemap_g2plot(df, category_cols: list = [], value_col: str = None, width="100%",
                   height='500px'):
    """
    treemap
    :param df: cat1,cat2,...,catN,value
    :param category_cols:类别列表
    :param value_col:值列表
    :param width:
    :param height:
    :return:
    """
    data = Tools.df2tree(df, category_cols=category_cols, value_col=value_col)
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
    options = {'xField': x_field, 'yField': y_field}
    if series_field is not None:
        options['seriesField'] = series_field
    return G2PLOT(df, plot_type='Line', options=options, width=width, height=height)


def scatter_g2plot(df, x_field=None, y_field=None, color_field=None, size_field=None, shape_field=None, width='100%',
                   height='500px'):
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
    options = {'xField': x_field, 'yField': y_field}
    if series_field is not None:
        options['seriesField'] = series_field
    if is_stack:
        options['isStack'] = True
    elif is_group:
        options['isGroup'] = True
    return G2PLOT(df, plot_type='Rose', options=options, width=width, height=height)


def pie_g2plot(df, angle_field=None, color_field=None, width='100%', height='500px'):
    options = {'angleField': angle_field, 'colorField': color_field}
    return G2PLOT(df, plot_type='Pie', options=options, width=width, height=height)


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


__all__ = ['bullet_g2plot', 'chord_g2plot', 'waterfall_g2plot', 'liquid_g2plot', 'wordcloud_g2plot',
           'column_stack_percent_g2plot', 'column_stack_g2plot', 'area_g2plot', 'area_percent_g2plot', 'treemap_g2plot',
           'violin_g2plot', 'line_g2plot', 'scatter_g2plot', 'column_g2plot', 'rose_g2plot', 'pie_g2plot',
           'gauge_g2plot', 'sankey_g2plot', 'heatmap_g2plot', 'radar_g2plot', 'funnel_g2plot', 'histogram_g2plot']

if __name__ == "__main__":
    print([func for func in list(locals().keys()) if func[0:2] != '__'])
