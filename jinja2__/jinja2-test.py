#!/usr/bin/env py3
#coding=utf-8
# date 2018-11-07 16:14:26
# author calllivecn <c-all@qq.com>


from jinja2 import Environment as Env, FileSystemLoader as Fsl


env = Env(loader = Fsl('.'))

temp1 = env.get_template('temp1.txt')

#with open('temp1-output.txt','w+') as f:
#render_content = temp1.render(var1="var1",var2="var2",number=1234567)
render_content = temp1.render({"var1":"变量1","var2":"变量2","number":1234567})

print(render_content)
