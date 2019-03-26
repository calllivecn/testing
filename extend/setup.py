from distutils.core import setup,Extension


setup(name="spam",
    ext_modules=[
        Extension('spam',
            ['spam_module.c'],
            include_dirs=['/usr/include/python3.5'],
            )
        ]
    )


