from distutils.core import setup

setup(
    name='TAServer',
    version='0.0.1',
    license='AGPLv3',
    description='A reference implementation of the tribes ascend server',
    install_requires=[
        "gevent",
        "click"
    ],
)
