from glob import glob
from setuptools import find_packages, setup

package_name = "axia_d04_vision_demo"
setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml", "README_KO.md"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="AXIA Safety Instructor",
    maintainer_email="noreply@example.invalid",
    description="D04: read-only Nav2 Waffle Pi RGB / yolo_ros teacher demo",
    license="Apache-2.0",
    tests_require=["pytest"],
)
