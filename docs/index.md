# ECAHRTSPY

定位：在notebook，jupyterlab等python环境使用echarts图表的工具库

不同于pyecharts，不对echarts 概念和接口进行python映射和二次抽象，更新echarts的js url就能用上最新echarts



## 使用说明

### 简单模式
```python
import echartspy.express as ex
...... 
ex.scatter(df,x='数量',y='价格',size='数量',group='水果',size_max=50,height='250px',title='scatter').render_notebook()

ex.pie(df,name='水果',value='数量',rose_type='area',title="pie2",height='350px').render_notebook()

ex.candlestick(df.reset_index(),left='5%',mas=[5,10,30],title='平安银行').render_notebook()
```
!!! note ""
    ![scatter](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/scatter.png?raw=true)

!!! note ""
    ![line](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/pie2.png?raw=true)

!!! note ""
    ![kline](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/kline.png?raw=true)

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

!!! note ""
    ![line](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/p1.png?raw=true)

!!! note ""
    ![自动转换](https://github.com/yiliuyan161/echartspy/blob/master/docs/images/p0.png?raw=true)





