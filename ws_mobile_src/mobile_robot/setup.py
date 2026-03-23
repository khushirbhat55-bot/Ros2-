from setuptools import setup
import glob

package_name = 'mobile_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob.glob('launch/*.py')),
        ('share/' + package_name + '/model',  glob.glob('model/*')),
        ('share/' + package_name + '/parameters', glob.glob('parameters/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='khushi',
    maintainer_email='khushi@todo.todo',
    description='Mobile robot package',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'obstacle_avoidance = mobile_robot.obstacle_avoidance:main',
        ],
    },
)
