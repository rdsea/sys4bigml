from setuptools import find_packages, setup

setup(
    name='qoa4ml',
    version='0.0.1',
    description='Quality of Analysis for Machine Learning',
    long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
    long_description_content_type='text/markdown',
    url='https://rdsea.github.io/',
    author='Aaltosea',
    email='tri.m.nguyen@aalto.fi',
    keyword='Monitoring Machine Learning',
    install_requires=['pika','requests'],
    packages=find_packages(),
    license='MIT'
)