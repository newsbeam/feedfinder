from distutils.core import setup

setup(
    name="nm_feedfinder",
    packages=["nm_feedfinder"],
    version="0.5",
    license="ISC",
    description="Find Atom/RSS links of a website given a URL",
    author="newsmailer.io",
    author_email="us@newsmailer.io",
    url="https://github.com/newsmailerio/feedfinder",
    keywords=["rss", "atom", "feed", "newsmail"],
    install_requires=["beautifulsoup4>=4.9,<5", "requests>=2.25,<3", "lxml>=4.6,<5"],
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Programming Language :: Python :: 3",
    ],
)
