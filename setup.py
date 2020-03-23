from setuptools import setup, find_packages

setup(name='exchange',
      version='0.0.1',
      description='MD2NFV Platform',
      author='Raphael Vicente Rosa <raphaelvrosa@gmail.com>,',
      namespace_packages=["exchange",],
      packages=find_packages(),
      scripts=["exchange/exchange_app"],
      install_requires = [
        'gevent',
        'requests',
        'Flask>=0.11',
        'Flask-RESTful>=0.3.5',
        'PyYAML>=3.10',
        'py-solc',
      ]
)
