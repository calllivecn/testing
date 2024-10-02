
from jinja2 import Template

# 子模板1
child_template1 = Template("Hello, {{ name }}!")

# 子模板2
child_template2 = Template("You are a {{ profession }}.")

# 主模板
main_template_str = """
{{ child_template1.render(name="World") }}
{{ child_template2.render(profession="programmer") }}
"""

# 创建主模板对象并渲染
main_template = Template(main_template_str)
rendered_str = main_template.render()

print(rendered_str)  # 输出: Hello, World! You are a programmer.

