# echartspy

echarts库的 python 封装



考虑升级维护以及使用者学习负担，本库不对echarts的模型和属性进行python的对等映射

核心功能

* python配置转换成JavaScript的配置
  
* 渲染html文件，html字符串，jupyterlab输出，jupyter-notebook输出

辅助功能

* JavaScript配置 自动转换成 python配置
  
* pandas DataFrame可视化



## 使用说明

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

### 手写python配置绘图
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

### JavaScript配置自动转换
```python
from echartspy import Echarts,Tools
import echartspy.express as ex
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
![notebook环境输出](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/p0.png?raw=true）


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

### API使用举例

[notebook](https://github.com/yiliuyan161/echartspy/blob/master/docs/echartspy.ipynb)

#### echartspy.express包  pandas DataFrame 可视化

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

```python
ex.line(df,x='水果',y='价格',title="line",height='250px').render_notebook()
```

```python
ex.bar(df,x='水果',y='价格',group='类别',title="bar2",height='250px').render_notebook()
```

```python
ex.pie(df,name='水果',value='数量',rose_type='area',title="pie2",height='350px').render_notebook()
```

```python
ex.line(df,x='水果',y='价格',title="line",height='250px').render_notebook()
```

```python
from stocksdk import *
df=api.get_price("000001.XSHE") # 包含 time,open,high,low,close,volume 这些列
ex.candlestick(df.reset_index(),left='5%',mas=[5,10,30],title='平安银行').render_notebook()
```

#### Tools工具API使用

工具函数都是Tools类的静态方法

##### JavaScript配置自动转换成python配置
```python
from echartspy import Echarts,Tools
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
```

##### DataFrame Series ndarray 转换成list类型

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

##### 模板工具方法
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



## 效果展示

![效果展示1](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/p1.png?raw=true)
![效果展示2](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/p2.png?raw=true)
![效果展示3](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/p3.png?raw=true)
![效果展示4](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/p4.png?raw=true)
