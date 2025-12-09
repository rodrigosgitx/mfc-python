import logging
logging.basicConfig(
    format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    filename="logs/info.log",
    encoding="utf-8",
    filemode="a",
)
logging.info("Something went wrong!")