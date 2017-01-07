

from distutils.core import setup,Extension

setup(name='example',
	ext_modules=[
	Extension('example',
		['1.c'],
		include_dirs=[''],
		define_macros=[('FOO','1')],
		undef_macros=['BAR'],
		library_dirs=['/usr/local/lib'],
		libaraies=['example']
		)
	]
)
