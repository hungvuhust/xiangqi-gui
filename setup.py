from setuptools import setup, find_packages

package_name = 'xiangqi_gui'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your_email@example.com',
    description='Xiangqi GUI with ROS2 integration',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'xiangqi_gui = xiangqi_gui.main:main',
            'xiangqi_ros_service = xiangqi_gui.ros_service_node:main',
        ],
    },
)
