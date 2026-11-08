from setuptools import find_packages, setup
from pathlib import Path

NAME = 'axia_d3_demo'
setup(
    name=NAME,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + NAME]),
        ('share/' + NAME, ['package.xml']),
        ('share/' + NAME + '/models', ['models/pedestrian_proxy.sdf']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='AXIA Safety Instructor',
    maintainer_email='noreply@example.invalid',
    description='Simulation-only D3 classroom obstacle + P1 read-only observer',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={'console_scripts': [
        'd3_demo = axia_d3_demo.cli:main',
        'd3_observer = axia_d3_demo.observer:main',
        'd3_scene = axia_d3_demo.scenario:main',
    ]},
)