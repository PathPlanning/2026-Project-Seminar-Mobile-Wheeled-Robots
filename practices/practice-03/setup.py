import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'practice_03_odometry'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'resource'), glob('resource/*.urdf')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.wbt')),
        (os.path.join('share', package_name, 'protos'), glob('protos/*.proto')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nocha7',
    maintainer_email='nochaloxushka@gmail.com',
    description='Odometry error study of TurtleBot3 in Webots',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'odometry_recorder = practice_03_odometry.odometry_recorder:main',
            'cmd_vel_publisher = practice_03_odometry.cmd_vel_publisher:main',
        ],
    },
)
