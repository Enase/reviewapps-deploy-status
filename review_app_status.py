import logging
import os
import time
from dataclasses import dataclass
from enum import Enum

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("review_app_status")


class BuildStates(Enum):
    """Expected reviewapp app build states"""

    success = "success"


@dataclass(frozen=True)
class Args:
    """User input arguments"""

    # Delay for the application to be built in Heroku
    build_time_delay: int

    # Interval for the repeating checks
    interval: int

    # Max time to be spent retrying for the response check
    create_timeout: int

    # App name
    app_name: str
    heroku_api_key: str


def _make_heroku_api_request(url: str, heroku_api_key: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/vnd.heroku+json",
        "Authorization": f"Bearer {heroku_api_key}",
    }

    logger.info(f"url: {url}")
    logger.info(f"heroku_api_key: {heroku_api_key}")
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()


def _check_review_app_deployment_status(
  review_app_name: str, heroku_api_key: str, timeout: int, interval: int
):
    if interval > timeout:
        raise ValueError("Interval can't be greater than create_timeout.")

    while timeout > 0:
        r = _make_heroku_api_request(
            f"https://api.heroku.com/review-apps/{review_app_name}",
            heroku_api_key
        )
        review_app_status = r.status
        logger.info(f"Review app status: {review_app_status}")
        if review_app_status in 'created':
            return
        time.sleep(interval)
        timeout -= interval

    raise TimeoutError(
        f"Did not get any of the accepted status in the given time."
    )


def main() -> None:
    """Main workflow.
    
    All the inputs are received from workflow as environment variables.
    """

    args = Args(
        build_time_delay=int(os.environ["INPUT_BUILD_TIME_DELAY"]),
        interval=int(os.environ["INPUT_INTERVAL"]),
        app_name=str(os.environ["INPUT_APP_NAME"]),
        heroku_api_key=str(os.environ["INPUT_HEROKU_API_KEY"]),
        create_timeout=int(os.environ["INPUT_CREATE_TIMEOUT"]),
    )

    # Delay the checks till the app is built
    logger.info(f"Build time delay: {args.build_time_delay} seconds")
    time.sleep(args.build_time_delay)

    review_app_name = args.app_name
    review_app_url = f"https://{review_app_name}.herokuapp.com"

    # Check the HTTP response from app URL
    _check_review_app_deployment_status(
        review_app_name=review_app_name,
        heroku_api_key=args.heroku_api_key,
        timeout=args.create_timeout,
        interval=args.interval,
    )

    print(f"::set-output name=review_app_name::{review_app_name}")
    print(f"::set-output name=review_app_url::{review_app_url}")
    print("Successful")


if __name__ == "__main__":  # pragma: no cover
    main()
