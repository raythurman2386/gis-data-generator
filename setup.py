from setuptools import setup, find_packages

setup(
    name="gis-data-generator",
    version="0.1.0",
    description="A Python tool for generating synthetic geospatial data.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Raymond Thurman",
    author_email="raymond.thurman@gmail.com",
    url="https://github.com/raythurman2386/gis-data-generator",
    packages=find_packages(),
    install_requires=[
        "folium==0.19.4",
        "geodatasets==2024.8.0",
        "matplotlib==3.10.0",
        "networkx==3.4.2",
        "numpy==2.2.1",
        "pandas==2.2.3",
        "pillow==11.1.0",
        "requests==2.32.3",
        "scikit-learn==1.6.1",
        "scipy==1.15.1",
        "seaborn~=0.13.2",
        "shapely==2.0.6",
        "osmnx~=2.0.1",
        "click~=8.1.7",
        "seamless_3dep",
        "rasterio",
        "geopandas[all]",
        "git+https://github.com/raythurman2386/pysheds.git@main",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-mock>=3.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "gis-generator=src.main:cli",
        ],
    },
)
