import os

from scrapy.utils.project import get_project_settings

settings = get_project_settings()

# LOGS_FOLDER_NAME = settings.get("LOGS_FOLDER_NAME")
# ITEMS_FOLDER_NAME = settings.get("ITEMS_FOLDER_NAME")

ITEMS_FOLDER_NAME = "items"
LOGS_FOLDER_NAME = "logs"


def setup_project_folders():
    # fmt: off
    try:os.mkdir(str(LOGS_FOLDER_NAME))
    except:pass
    
    try:os.mkdir(str(ITEMS_FOLDER_NAME))
    except:pass
    # fmt: on


if __name__ == "__main__":
    setup_project_folders()
