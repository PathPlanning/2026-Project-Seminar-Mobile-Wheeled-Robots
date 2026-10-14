from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'example_webots'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.[pxy][yma]*")),
        ),
        (
            os.path.join("share", package_name, "worlds"),
            glob(os.path.join("worlds", "*.wbt")),
        ),
        (
            os.path.join("share", package_name, "protos"),
            glob(os.path.join("protos", "*.proto")),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sadergachev',
    maintainer_email='sadergachev@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
