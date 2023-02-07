from setuptools import setup

setup(
    name="debugpy-uwsgi",
    version="0.0.5",
    description="A package that patches uwsgi to debug with debugpy.",
    author="Vishal P R",
    author_email="vishal.rayoth@gmail.com",
    url="https://github.com/vishalwy/debugpy-uwsgi",
    packages=["debugpy_uwsgi"],
    install_requires=["debugpy"],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "debugpy-uwsgi=debugpy_uwsgi.executable:main",
            "uwsgi.patch=debugpy_uwsgi.uwsgi:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
)
