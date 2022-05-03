import copy

import pandas as pd
from ..highcharts import HighCharts


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
        data = df[col].values
        options['series'].append({'name': col, 'data': data})
    return HighCharts(options)


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


__all__ = ['streamgraph_highcharts', 'arcdiagram_highcharts', 'dependency_wheel_highcharts']
