"""Set up the patrol package."""

from setuptools import find_packages, setup

package_name = 'patrol'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='anastasiia',
    maintainer_email='darsyeva@mail.ru',
    description='Publish turtle velocity commands using the latest pose.',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'patrol = patrol.patrol:main',
        ],
    },
)
