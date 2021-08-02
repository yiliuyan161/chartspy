# echartspy

帮助用户在python环境使用echarts绘图

[echartspy文档](https://echartspy.icopy.site)

不同于pyecharts，不对echarts 概念和属性进行python映射和二次抽象，保证库不依赖于特定echarts版本

实现了 python配置<=>JavaScript配置 的双向互转

同时借鉴plotly.express 封装了简单图表类型可视化函数


## 使用说明

### 简单模式
```python
import echartspy.express as ex
...... 
ex.scatter(df,x='数量',y='价格',size='数量',group='水果',size_max=50,height='250px',title='scatter').render_notebook()
ex.pie(df,name='水果',value='数量',rose_type='area',title="pie2",height='350px').render_notebook()
ex.candlestick(df.reset_index(),left='5%',mas=[5,10,30],title='平安银行').render_notebook()
```

### 高级模式

#### 全手工

手工书写，参考 [echarts配置手册](https://echarts.apache.org/zh/option.html#title)

```python
from echartspy import Echarts,Tools
options={
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
Echarts(options,height='600px',title='散点图测试').render_notebook()

```

#### 半自动

半自动，从[echarts示例](https://echarts.apache.org/examples/zh/index.html) 拷贝js配置，自动生成对应的python配置

convert_js_to_dict(js_str,**print_dict=True**) 会在控制台打印python 配置, 粘贴进行二次加工

```python
from echartspy import Echarts,Tools,Js
js_str="""
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
options=Tools.convert_js_to_dict(js_str,print_dict=False)
Echarts(options,height='300px',width='300px').render_notebook()
```

![自动转换](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/p0.png?raw=true)


## 安装&升级

### 安装
```shell
pip install git+https://gitee.com/yiliuyan161/echartspy.git
```

### 升级 echartspy
```shell
pip uninstall echartspy -y  && pip install git+https://gitee.com/yiliuyan161/echartspy.git
```


### 升级echarts版本
```python
import echartspy
echartspy.ECHARTS_JS_URL = "https://unpkg.com/echarts@5.1.2/dist/echarts.min.js"
```

## 代码说明

### 包结构说明

#### echartspy包下使用两个对象 Echarts,Tools

Echarts对象接受 python配置，输出图表

Tools对象的静态方法有三个

* convert_js_to_dict JavaScript配置转换成python配置
* convert_to_list 辅助用户把DataFrame,Series,ndarray转换成list结构
* wrap_template 是一个模板工具函数，构建复杂图表可能会用到

#### echartspy.express包下是封装好的pandas DataFrame绘图函数

包含 bar,scatter,line,pie,candlestick,sankey,parallel,theme_river,heatmap,calendar_heatmap等

## API使用的具体例子

[notebook](https://github.com/yiliuyan161/echartspy/blob/master/docs/echartspy.ipynb)

### echartspy.express包  pandas DataFrame 可视化

```python
from echartspy import Echarts,Tools
import echartspy.express as ex
import pandas as pd
df = pd.DataFrame(
    {
       '水果':['苹果','梨','草莓','香蕉'],
       '数量':[3,2,5,4],
       '价格':[10,9,8,5],
       '类别':['硬','硬','软','软']
    })
```

```python
ex.scatter(df,x='数量',y='价格',size='数量',group='水果',size_max=50,height='250px',title='scatter').render_notebook()
```

![scatter](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/scatter.png?raw=true)

```python
ex.line(df,x='水果',y='价格',title="line",height='250px').render_notebook()
```

![line](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/line.png?raw=true)

```python
ex.bar(df,x='水果',y='价格',group='类别',title="bar2",height='250px').render_notebook()
```

![line](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/bar2.png?raw=true)

```python
ex.pie(df,name='水果',value='数量',rose_type='area',title="pie2",height='350px').render_notebook()
```

![line](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/pie2.png?raw=true)



```python
from stocksdk import *
df=api.get_price("000001.XSHE") # 包含 time,open,high,low,close,volume 这些列
ex.candlestick(df.reset_index(),left='5%',mas=[5,10,30],title='平安银行').render_notebook()
```

![line](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/kline.png?raw=true)

### Tools工具API使用

工具函数都是Tools类的静态方法

#### JavaScript配置自动转换成python配置
```python
from echartspy import Echarts,Tools
js_str="""
{
    title: {
        text: 'Male and female height and weight distribution',
        subtext: 'Data from: Heinz 2003'
    },
    grid: {
        left: '3%',
        right: '7%',
        bottom: '7%',
        containLabel: true
    },
    tooltip: {
        // trigger: 'axis',
        showDelay: 0,
    ......    
}
"""
options=Tools.convert_js_to_dict(js_str,print_dict=False)
Echarts(options,height='600px').render_notebook()
```

![line](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/p1.png?raw=true)


#### DataFrame Series ndarray 转换成list类型

```python
import pandas as pd
from echartspy import Tools
df = pd.DataFrame(
    {
       '水果':['苹果','梨','草莓','香蕉'],
       '数量':[3,2,5,4],
       '价格':[10,9,8,5],
       '类别':['硬','硬','软','软']
    })
list_data = Tools.convert_to_list(df)
```

输出:

```python
[['苹果', 3, 10, '硬'], ['梨', 2, 9, '硬'], ['草莓', 5, 8, '软'], ['香蕉', 4, 5, '软']]
```

#### 模板工具方法
封装了jinja2,主要用于Js函数

```python
from echartspy import Tools
max_size_value = 100
size_max =30
# **locals() 是上下文变量词典，这是偷懒的写法， 也可以命名参数方式传递: max_size_value=max_size_value,size_max=size_max
Tools.wrap_template(
"""
    function(val) {
     return val[2]/{{max_size_value}}*{{size_max}};
    }
""", **locals())
```



