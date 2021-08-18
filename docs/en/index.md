# chartspy

Help users to use echarts,g2plot drawing in python environment

Unlike pyecharts, it does not perform python mapping and secondary abstraction of echarts concepts and attributes, ensuring that the library does not depend on a specific echarts version

* implemented **two-way conversion** of python configuration<=>JavaScript configuration

* offer simple visualization functions like plotly.express



## instructions for use

### simple mode

```python
from  chartspy import *

......
express.scatter_echarts(df, x='数量', y='价格', size='数量', group='水果', size_max=50, height='250px', title='scatter').render_notebook()

express.pie_echarts(df, name='水果', value='数量', rose_type='area', title="pie2", height='350px').render_notebook()

express.candlestick_echarts(df, left='5%', mas=[5, 10, 30], title='平安银行').render_notebook()
```
!!! note ""
    ![scatter](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/scatter.png?raw=true)

!!! note ""
    ![line](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/pie.png?raw=true)

!!! note ""
    ![kline](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/kline.png?raw=true)

### advanced mode

#### handmade

handmade，reference [echarts onfiguration manual](https://echarts.apache.org/zh/option.html#title)

```python
from chartspy import *

options = {
    'xAxis': {},
    'yAxis': {},
    'series': [{
        'symbolSize': 20,
        'data': [
            [10.0, 8.04],
            [8.07, 6.95],
            [13.0, 7.58],
            [9.05, 8.81],
            [11.0, 8.33]
        ],
        'type': 'scatter'
    }]
}
Echarts(options, height='600px', title='散点图测试').render_notebook()
```

```python
from chartspy import *

# G2PLOT
df= ...
# Echarts
options = {
    'xField':'time',
    'yField':'close'
}
G2PLOT(df,plot_type='Line',options=options).render_notebook()
```

#### semi-automatic

from [echarts examples](https://echarts.apache.org/examples/zh/index.html) copy js configuration ,auto convert to python dict

convert_js_to_dict(js_str,**print_dict=True**) will print python configuration dict in console, manually modify after copy and paste

```python
from chartspy import *

js_str = """
{
    xAxis: {
        type: 'category',
        data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    },
    yAxis: {
        type: 'value'
    },
    series: [{
        data: [820, 932, 901, 934, 1290, 1330, 1320],
        type: 'line',
        smooth: true
    }]
}
"""
options = Tools.convert_js_to_dict(js_str, print_dict=False)
Echarts(options, height='300px', width='300px').render_notebook()
```






