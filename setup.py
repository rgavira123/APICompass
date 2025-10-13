from setuptools import setup, find_packages

setup(
    name='APICompass',
    version='0.2.1',
    packages=find_packages(),
    license='MIT',
    author='Daniel Ruiz López, Ramón Gavira Sánchez',
    author_email='danruilop1@alum.us.es, rgavira@us.es',
    description='Python library for calculating properties related to Pricings and Plans',
    install_requires=[
        'contourpy==1.2.0',
        'cycler==0.12.1',
        'fonttools==4.47.2',
        'kiwisolver==1.4.5',
        'matplotlib==3.8.2',
        'numpy==1.26.3',
        'packaging==23.2',
        'pandas==2.2.0',
        'pillow==10.2.0',
        'pyparsing==3.1.1',
        'python-dateutil==2.8.2',
        'pytz==2023.3.post1',
        'six==1.16.0',
        'tzdata==2023.4',
        'ipywidgets==8.1.0',
        'pyarrow',
        'PyYAML==6.0.2',
        'requests==2.32.3',
        'asyncio==3.4.3',
        'httpx==0.28.1',
        'python-dotenv==1.0.1',
        'plotly==5.24.1',
        'nbformat==5.10.4'
    ]
)
