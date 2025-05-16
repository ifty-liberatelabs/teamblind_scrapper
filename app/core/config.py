from pydantic_settings import BaseSettings
import logging

class Settings(BaseSettings):
    TEAMBLIND_USER_EMAIL: str
    TEAMBLIND_USER_PASS: str
    LOG_LEVEL: str = "INFO"
    PORT: int


    # Header Config
    User_Agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/133.0.5648.0 Safari/537.36"
    )

    next_router_state_tree: str = "%5B%22%22%2C%7B%22children%22%3A%5B%22(main)%22%2C%7B%22children%22%3A%5B%22company%22%2C%7B%22children%22%3A%5B%5B%22companyUrlAlias%22%2C%22Outreach%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22reviews%22%2C%7B%22children%22%3A%5B%22__PAGE__%3F%7B%5C%22page%5C%22%3A%5C%222%5C%22%7D%22%2C%7B%7D%2C%22%2Fcompany%2FOutreach%2Freviews%3Fpage%3D2%22%2C%22refetch%22%5D%7D%5D%7D%5D%7D%5D%7D%5D%7D%5D"
    rsc: str = "1"

    class Config:
        env_file = ".env"

settings = Settings()

# Logger setup
logger = logging.getLogger("app")
logger.setLevel(settings.LOG_LEVEL)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler) 