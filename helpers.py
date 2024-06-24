import os

from scrapy.utils.project import get_project_settings

settings = get_project_settings()


def setup_project_folders(logs_folder_name, items_folder_name):
    # fmt: off
    try:os.mkdir(str(logs_folder_name))
    except:pass
    # fmt: on


if __name__ == "__main__":
    setup_project_folders("logs")
