import json
from os import path
from os import mkdir
from pathlib import Path
from shutil import unpack_archive
from typing import Any

import requests
from requests import HTTPError
from tqdm import tqdm

from berpublicsearch.convert import convert_to_parquet


HERE = Path(__file__).parent


def download_file_from_response(response: requests.Response, filepath: str) -> None:
    """Download file to filepath via a HTTP response from a POST or GET request.

    Args:
        response (requests.Response): A HTTP response from a POST or GET request
        filepath (str): Save path destination for downloaded file
    """
    total_size_in_bytes = int(response.headers.get("content-length", 0))
    block_size = 1024  # 1 Kilobyte
    progress_bar = tqdm(total=total_size_in_bytes, unit="iB", unit_scale=True)

    with open(filepath, "wb") as save_destination:

        for stream_data in response.iter_content(block_size):
            progress_bar.update(len(stream_data))
            save_destination.write(stream_data)

    progress_bar.close()


def download_berpublicsearch(email_address: str, filepath: str) -> None:
    """Login & Download BER data.

    Warning:
        Email address must first be registered with SEAI at


    Args:
        email_address (str): Registered Email address with SEAI
        filepath (str): Save path for data
    """
    with open(HERE / "request.json", "r") as json_file:
        ber_form_data = json.load(json_file)

    # Register login email address
    ber_form_data["login"][
        "ctl00$DefaultContent$Register$dfRegister$Name"
    ] = email_address

    with requests.Session() as session:

        # Login to BER Research Tool using email address
        response = session.post(
            url="https://ndber.seai.ie/BERResearchTool/Register/Register.aspx",
            headers=ber_form_data["headers"],
            data=ber_form_data["login"],
        )

        if "not registered" in str(response.content):
            raise ValueError(
                f"{email_address} does not have access to the BER Public"
                f" search database, please login to {email_address} and"
                " respond to your registration email and try again."
            )

        # Download Ber data via a post request
        with session.post(
            url="https://ndber.seai.ie/BERResearchTool/ber/search.aspx",
            headers=ber_form_data["headers"],
            data=ber_form_data["download_all_data"],
            stream=True,
        ) as response:

            download_file_from_response(response, filepath)


def get_berpublicsearch_parquet(
    email_address: str,
    savedirpath: str = Path.cwd(),
) -> None:
    """Login, download & convert BER data to parquet.

    Warning:
        Email address must first be registered with SEAI at
            https://ndber.seai.ie/BERResearchTool/Register/Register.aspx

    Args:
        email_address (str): Registered Email address with SEAI
        filepath (str): Save path for data
    """
    print("Download BERPublicsearch.zip...")
    path_to_zipped = f"{savedirpath}/BERPublicsearch.zip"
    download_berpublicsearch(email_address, path_to_zipped)

    path_to_unzipped = f"{savedirpath}/BERPublicsearch"
    unpack_archive(path_to_zipped, path_to_unzipped)

    print("Converting BERPublicsearch to BERPublicsearch_parquet...")
    path_to_parquet = f"{savedirpath}/BERPublicsearch_parquet"
    convert_to_parquet(path_to_unzipped, path_to_parquet)