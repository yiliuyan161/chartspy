# pyecharts迁移

## dump_options 输出js 配置

以pyecharts示例图表举例，dump_options赋值给js_str

```python
from pyecharts import options as opts
from pyecharts.charts import Bar
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType

list2 = [
    {"value": 12, "percent": 12 / (12 + 3)},
    {"value": 23, "percent": 23 / (23 + 21)},
    {"value": 33, "percent": 33 / (33 + 5)},
    {"value": 3, "percent": 3 / (3 + 52)},
    {"value": 33, "percent": 33 / (33 + 43)},
]

list3 = [
    {"value": 3, "percent": 3 / (12 + 3)},
    {"value": 21, "percent": 21 / (23 + 21)},
    {"value": 5, "percent": 5 / (33 + 5)},
    {"value": 52, "percent": 52 / (3 + 52)},
    {"value": 43, "percent": 43 / (33 + 43)},
]

js_str=Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT)).add_xaxis([1, 2, 3, 4, 5]).add_yaxis("product1", list2, stack="stack1", category_gap="50%").add_yaxis("product2", list3, stack="stack1", category_gap="50%").set_series_opts(
        label_opts=opts.LabelOpts(
            position="right",
            formatter=JsCode(
                "function(x){return Number(x.data.percent * 100).toFixed() + '%';}"
            ),
        )
    ).dump_options()

```
## 从js 配置 生成 python配置 dict

打印python配置

```python
from chartspy import *

options = Tools.convert_js_to_dict(js_str, print_dict=False)

Echarts(options).print_options(drop_data=False)  # 打印python dict配置
```

## 复制 粘贴 修改
```python
options={
  "animation": True,
  "animationThreshold": 2000,
  "animationDuration": 1000,
  "animationEasing": "cubicOut",
  "animationDelay": 0,
  "animationDurationUpdate": 300,
  "animationEasingUpdate": "cubicOut",
  "animationDelayUpdate": 0,
  "series": [
    {
      "type": "bar",
      "name": "product1",
      "legendHoverLink": True,
      "data": [
   ......
}
Echarts(options) # notebook或者jupyterlab平台会自动输出图表
```