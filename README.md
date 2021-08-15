# chartspy

[English documents](https://echartspy.icopy.site/en/)
[中文文档](https://echartspy.icopy.site)

帮助用户在python环境使用echarts  g2plot 绘图



不同于pyecharts，不对echarts 概念和属性进行python映射和二次抽象，保证库不依赖于特定echarts版本

* 实现了 python配置<=>JavaScript配置的**双向互转**

* 同时借鉴**plotly.express** 封装了简单图表类型可视化函数


## 使用说明

### 简单模式

```python
import chartspy.express as ex

......
ex.echarts_scatter(df, x='数量', y='价格', size='数量', size_max=50, height='250px', title='scatter').render_notebook()

ex.echarts_pie(df, name='水果', value='数量', rose_type='area', title="pie2", height='350px').render_notebook()

ex.echarts_candlestick(df.reset_index(), left='5%', mas=[5, 10, 30], title='平安银行').render_notebook()
```

### 高级模式

#### 全手工

手工书写，参考 [echarts配置手册](https://echarts.apache.org/zh/option.html#title)

```python
from chartspy import Echarts, Tools

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

#### 半自动

半自动，从[echarts示例](https://echarts.apache.org/examples/zh/index.html) 拷贝js配置，自动生成对应的python配置

convert_js_to_dict(js_str,**print_dict=True**) 会在控制台打印python 配置, 粘贴进行二次加工

```python
from chartspy import Echarts, Tools, Js

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

![自动转换](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/p0.png?raw=true)


## 安装&升级

### 安装

```shell
pip install chartspy
```

### 升级 echartspy
```shell
pip uninstall chartspy -y  && pip install chartspy
```


### 升级echarts版本

```python
from  chartspy import  echarts

echarts.ECHARTS_JS_URL = "https://unpkg.com/echarts@5.1.2/dist/echarts.min.js"
```

## 其他说明参见[chartspy文档](https://chartspy.icopy.site)
