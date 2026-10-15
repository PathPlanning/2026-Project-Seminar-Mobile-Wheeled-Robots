import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'draw_number'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nocha7',
    maintainer_email='nochaloxushka@gmail.com',
    description='Practice number 1. Draw digit 16 with turtlesim.',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'draw_digit = draw_number.draw_digit:main',
        ],
    },
)
