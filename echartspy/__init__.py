#!/usr/bin/env python
# coding=utf-8
import datetime
import re
import uuid
from typing import Optional

import simplejson
from jinja2 import Environment, BaseLoader

GLOBAL_ENV = Environment(loader=BaseLoader)

SEP = "!!-_-____-_-!!"

# language=HTML
JUPYTER_NOTEBOOK_TEMPLATE = """
<script>
  require.config({
    paths: {
      "echarts": "{{plot.js_url}}"
    }
  });
</script>
<div id="{{ plot.plot_id }}"></div>
<script>
  require(['echarts'], function (echarts) {
    var plot_{{ plot.plot_id }} = = echarts.init(document.getElementById('{{ plot.plot_id }}'));
    plot_{{ plot.plot_id }}.setOption({{ plot.js_options }});
  });
</script>
"""

# language=HTML
JUPYTER_LAB_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title></title>
</head>
<body>
  <div id="{{ plot.plot_id }}"></div>
  <script>
    // load javascript
    new Promise(function(resolve, reject) {
      var script = document.createElement("script");
      script.onload = resolve;
      script.onerror = reject;
      script.src = "{{plot.js_url}}";
      document.head.appendChild(script);
    }).then(() => {
       var plot_{{ plot.plot_id }} = = echarts.init(document.getElementById('{{ plot.plot_id }}'));
       plot_{{ plot.plot_id }}.setOption({{ plot.js_options }});
    });
  </script>
</body>
</html>
"""

# language=HTML
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title></title>
   <script type="text/javascript" src="{{ plot.js_url }}"></script>
</head>
<body>
  <div id="{{ plot.plot_id }}"></div>
  <script>
    var plot_{{ plot.plot_id }} = = echarts.init(document.getElementById('{{ plot.plot_id }}'));
    plot_{{ plot.plot_id }}.setOption({{ plot.js_options }});
  </script>
</body>
</html>
"""


class JS:
    def __init__(self, js_code: str):
        self.js_code = "%s%s%s" % (SEP, js_code, SEP)

    def replace(self, pattern: str, repl: str):
        self.js_code = re.sub(pattern, repl, self.js_code)
        return self


class HTML:
    def __init__(self, data: Optional[str] = None):
        self.data = data

    def _repr_html_(self):
        return self.data

    def __html__(self):
        return self._repr_html_()


def _json_dump_default(o: object):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()
    elif isinstance(o, JS):
        return o.replace("\\n|\\t", "").replace(r"\\n", "\n").replace(r"\\t", "\t").js_code
    else:
        return o


class Plot(object):

    def __init__(self, options: object, js_url: str = 'https://unpkg.com/echarts@5.1.2/dist/echarts.min.js'):
        self.options = options
        self.js_options = self.dump_js_options()
        self.plot_id = uuid.uuid4().hex
        self.js_url = js_url
        self.options = {}
        self.page_title = "echarts plot"

    def dump_js_options(self, **kwargs) -> str:
        self.options.update(kwargs)
        return re.sub('"?%s"?' % SEP, "",
                      simplejson.dumps(self.options, indent=2, default=_json_dump_default, ignore_nan=True))

    def render_notebook(self, **kwargs) -> HTML:
        self.js_options = self.dump_js_options(**kwargs)
        html = GLOBAL_ENV.from_string(JUPYTER_NOTEBOOK_TEMPLATE).render(plot=self, **kwargs)
        return HTML(html)

    def render_jupyter_lab(self, **kwargs) -> HTML:
        self.js_options = self.dump_js_options(**kwargs)
        html = GLOBAL_ENV.from_string(JUPYTER_LAB_TEMPLATE).render(plot=self, **kwargs)
        return HTML(html)

    def render_html(self, **kwargs) -> str:
        self.js_options = self.dump_js_options(**kwargs)
        html = GLOBAL_ENV.from_string(HTML_TEMPLATE).render(plot=self, **kwargs)
        return HTML(html)

    def render(self, path: str = "plot.html", **kwargs) -> str:
        html = self.render_html(**kwargs)
        with open(path, "w+", encoding="utf-8") as html_file:
            html_file.write(html)
        return path


__all__ = ["Plot"]
