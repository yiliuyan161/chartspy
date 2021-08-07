# echartspy

Help users to use echarts drawing in python environment

Unlike pyecharts, it does not perform python mapping and secondary abstraction of echarts concepts and attributes, ensuring that the library does not depend on a specific echarts version

* Implemented **two-way conversion** of python configuration<=>JavaScript configuration

* At the same time, drawing on **plotly.express** to encapsulate simple chart type visualization functions



## instructions for use

### simple mode
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

### advanced mode

#### handmade

handmade，reference [echarts onfiguration manual](https://echarts.apache.org/zh/option.html#title)

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

#### semi-automatic

from [echarts examples](https://echarts.apache.org/examples/zh/index.html) copy js configuration ,auto convert to python dict

convert_js_to_dict(js_str,**print_dict=True**) will print python configuration dict in console, manually modify after copy and paste

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





