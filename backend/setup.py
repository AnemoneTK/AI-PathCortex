from setuptools import setup, find_packages

setup(
    name="career-ai-advisor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "numpy",
        "faiss-cpu",
        "pandas",
        "requests",
        "beautifulsoup4",
        "tqdm",
        "PyPDF2",
        "python-docx",
        "python-multipart",
    ],
)