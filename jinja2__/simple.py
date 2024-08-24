from jinja2 import Template




text = """
这是模板内容。

这是是渲染内容: {{ ctx }}
"""


temp = Template(text)

print(temp.render(ctx="哈哈，成功了～～～～"))
