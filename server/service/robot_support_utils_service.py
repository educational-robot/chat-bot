import requests

from server.core.config import settings


class RobotSupportUtilsService:
    def __init__(self):
        self.api_key = settings.ROBOT_SUPPORT_API_KEY
        pass

    def take_picture(self) -> bytes | None:
        response = requests.get(
            url=settings.ROBOT_SUPPORT_URL + f"/camera/take-picture",
            json={
                "api_key": self.api_key
            }
        )

        if response.status_code != 200:
            return None

        return response.content

    def take_video(self) -> bytes | None:
        response = requests.get(
            url=settings.ROBOT_SUPPORT_URL + f"/camera/take-video",
            json={
                "api_key": self.api_key
            }
        )

        if response.status_code != 200:
            return None

        return response.content