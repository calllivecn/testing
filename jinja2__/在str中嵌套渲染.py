
"""
这个有问题，达不到效果。
"""

from jinja2 import Environment, Template

# 定义父模板字符串
parent_template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Parent Page{% endblock %}</title>
</head>
<body>
    <header>
        <h1>{% block header %}Parent Header{% endblock %}</h1>
    </header>
    <main>
        {% block content %}
            This is the parent content.
        {% endblock %}
    </main>
    <footer>
        <p>{% block footer %}Parent Footer{% endblock %}</p>
    </footer>
</body>
</html>
"""

# 定义子模板字符串
child_template_str = """
{% extends "!parent_template" %}

{% block title %}Child Page{% endblock %}

{% block header %}Child Header{% endblock %}

{% block content %}
    <p>This is the child content.</p>
{% endblock %}

{% block footer %}Child Footer{% endblock %}
"""

# 创建一个 Jinja2 环境
env = Environment()

# 解析父模板
parent_template = env.from_string(parent_template_str)

# 解析子模板，并告诉子模板其父模板是哪个
# 注意这里的 "!parent_template" 是一个占位符，实际上我们需要传递真正的父模板对象
child_template = env.from_string(child_template_str)

# 由于子模板使用了继承语法，我们需要在解析子模板时提供父模板
# 我们可以通过 `make_def` 方法生成一个定义，使得子模板可以引用父模板
parent_def = parent_template.make_def("content")
child_template.globals["_parent"] = parent_template
child_template.globals["_parent_def"] = parent_def

# 渲染子模板
rendered_child = child_template.render()

print(rendered_child)

