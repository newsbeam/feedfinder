from distutils.core import setup

setup(
    name='nm_feedfinder',
    packages=['nm_feedfinder'],
    version='0.3',
    license='ISC',
    description='Find Atom/RSS links of a website given a URL',
    author='newsmail.today',
    author_email='us@newsmail.today',
    url='https://github.com/newsmail-today/feedfinder',
    keywords=['rss', 'atom', 'feed', 'newsmail'],
    install_requires=[
        "bs4",
        "requests",
        "lxml",
    ],
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
