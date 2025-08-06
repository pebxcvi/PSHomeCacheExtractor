from cx_Freeze import setup, Executable
import os
import sys

# Common build options for all executables
build_exe_options = {
    "packages": ["os", "sys", "hashlib", "PIL", "subprocess", "logging", "re", "shutil", "datetime", "pathlib"],
    "excludes": [
        "tkinter", "unittest", "email", "email.mime", "email.header", "email.charset", "email.contentmanager",
        "email.errors", "email.feedparser", "email.generator", "email.iterators", "email.message",
        "email.parser", "email.policy", "email.utils", "email.base64mime", "email.encoders",
        "email._parseaddr", "email.quoprimime", "email._header_value_parser", "email._encoded_words",
        "html", "http", "xml", "pydoc", "test", "asyncio", "concurrent", "ctypes"
    ],
    "include_files": [],
    "optimize": 2  # optimization level: 2 is best for release
}

# Determine the base for Windows
base = "Console" if sys.platform == "win32" else None

# Shared metadata to make files look legit
common_metadata = dict(
    base=base,
    icon=None,  # add .ico path if you have one
    copyright="Home Laboratory (c)2025 PSHOME Revival Project",
)

# Define all executables
executables = [
    Executable("file_analysis.py", target_name="file_analysis.exe", **common_metadata),
    Executable("check_for_new_objects.py", target_name="check_for_new_objects.exe", **common_metadata),
    Executable("cache_copy_single.py", target_name="cache_copy_single.exe", **common_metadata),
    Executable("cache_copy_combined.py", target_name="cache_copy_combined.exe", **common_metadata),
    Executable("log_thumbnails.py", target_name="log_thumbnails.exe", **common_metadata),
    Executable("log_sdats.py", target_name="log_sdats.exe", **common_metadata),
    Executable("merge_inflogs.py", target_name="merge_inflogs.exe", **common_metadata),
    Executable("custom_query.py", target_name="custom_query.exe", **common_metadata),
]

setup(
    name="PSHomeCacheTools",
    version="1.0.0",
    description="PSHome Cache Analysis Tools",
    author="PaulB",
    author_email="pbuckleyxcvi@gmail.com",
    options={"build_exe": build_exe_options},
    executables=executables
)

