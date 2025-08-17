import requests
import logging
import json

logger = logging.getLogger("hh_api")

url = "https://api.hh.ru/vacancies"


def get_vacancies_by_page(url: str, page: int = 0):
    query_params = {
        "page": 0,
        "per_page": 20,
        "text": "fastapi OR django OR asyncio",
        "work_format": "REMOTE",
    }
    response = requests.get(url, query_params)

    if response.status_code != 200:
        logger.info("request failed with error", response.text)

    logger.info(f"Vacancies received {page=}")

    return response.json()


def prepare_data_for_send(vacancies_data):
    prepared_data = []
    for vacancy in vacancies_data:
        data = {
            "job name": vacancy["name"],
            "area": vacancy["area"]["name"],
            "salary": vacancy.get("salary", {}),
            "url": vacancy["url"],
            "work_format": vacancy["work_format"],
            "experience": vacancy["experience"]["name"],
        }
        prepared_data.append(data)
    return prepared_data


def get_all_vacancies(url: str):
    page = 0
    vacancies_data = []

    while page < 2:
        vacancies = get_vacancies_by_page(url, page)

        if len(vacancies["items"]) == 0:
            break

        vacancies_data.extend(vacancies["items"])

        page += 1

    return vacancies_data


def main():
    vacancies = get_all_vacancies(url)
    prepared_data = prepare_data_for_send(vacancies)
    print(prepared_data)


if __name__ == "__main__":
    main()
