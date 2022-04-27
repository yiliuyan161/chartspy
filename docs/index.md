# chartspy

帮助用户在python环境使用echarts g2plot KLineChart 绘图

不同于pyecharts，不对echarts 概念和属性进行python映射和二次抽象，保证库不依赖于特定echarts版本

* 实现了 python配置<=>JavaScript配置的**双向互转**

* 同时借鉴**plotly.express** 封装了简单图表类型可视化函数



## 使用说明

### 简单模式   
直接选择合适的图表类型，展示DataFrame

```python
from chartspy import *

express.scatter_echarts(df, x_field='数量', y_field='价格', size_field='数量', size_max=50, height='250px',
                        title='scatter')

express.pie_echarts(df, name_field='水果', value_field='数量', rose_type='area', title="pie2", height='350px')

express.candlestick_echarts(df, left_padding='5%', mas=[5, 10, 30], title='平安银行')
```
!!! note ""
    ![scatter](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/scatter.png?raw=true)

!!! note ""
    ![line](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/pie.png?raw=true)

!!! note ""
    ![kline](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/kline.png?raw=true)

### 高级模式

#### 同js写法

同js写法，只是js 函数要包裹下Js("""function(){}"""),库会自动转换python类型到对应的js类型
手工书写，参考 [echarts配置手册](https://echarts.apache.org/zh/option.html#title)
[g2plot官方文档](https://g2plot.antv.vision/zh/docs/manual/plots/line)

```python
from chartspy import *

# Echarts
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
Echarts(options, height='600px').render_notebook()
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

```python
from chartspy import KlineCharts
import tushare as ts
df=ts.pro_bar(ts_code="000001.SZ",adj='qfq')
df.rename(columns={'trade_date':'timestamp','vol':'volume'},inplace=True)
KlineCharts(df,height='800px')
```


#### 半自动JavaScript配置->Python配置

半自动，从[echarts示例](https://echarts.apache.org/examples/zh/index.html) 拷贝js配置，自动生成对应的python配置

convert_js_to_dict(js_str,**print_dict=True**) 会在控制台打印python 配置, 方便拷贝粘贴后进行二次加工

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




