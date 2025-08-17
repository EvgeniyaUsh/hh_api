import requests
import logging

from settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


logger = logging.getLogger("hh_api")


url = "https://api.hh.ru/vacancies"


def get_vacancies_by_page(url: str, page: int = 0):
    query_params = {
        "page": page,
        "per_page": 20,
        "text": "fastapi OR django OR asyncio",
        "work_format": "REMOTE",
    }
    response = requests.get(url, params=query_params, timeout=30)

    if response.status_code != 200:
        logger.error("request failed with error %s", response.text)

    logger.info("Vacancies received page=%s", page)

    return response.json()


def prepare_data_for_send(vacancies_data):
    prepared_data = []
    for vacancy in vacancies_data:
        data = {
            "job name": vacancy["name"],
            "company": vacancy.get("employer", {}).get("name", "не указано"),
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

    while page < 1:
        vacancies = get_vacancies_by_page(url, page)

        if len(vacancies["items"]) == 0:
            break

        vacancies_data.extend(vacancies["items"])

        page += 1

    return vacancies_data


def format_salary(salary):
    if not salary:
        return "не указана"
    parts = []
    salary_from = salary.get("from") if isinstance(salary, dict) else None
    salary_to = salary.get("to") if isinstance(salary, dict) else None
    currency = salary.get("currency") if isinstance(salary, dict) else None
    if salary_from:
        parts.append(f"от {salary_from}")
    if salary_to:
        parts.append(f"до {salary_to}")
    amount = " ".join(parts) if parts else "не указана"
    return f"{amount} {currency}" if currency and parts else amount


def format_vacancy_message(data):
    job_name = data.get("job name", "")
    company = data.get("company")
    area = data.get("area", "")
    work_format = data.get("work_format", "")
    experience = data.get("experience", "")
    salary_text = format_salary(data.get("salary"))
    url_text = data.get("url", "")
    return (
        f"Вакансия: {job_name}\n"
        f"Компания: {company}\n"
        f"Город: {area}\n"
        f"Формат: {work_format}\n"
        f"Опыт: {experience}\n"
        f"Зарплата: {salary_text}\n"
        f"{url_text}"
    )


def send_telegram_message(text: str, token: str, chat_id: str):
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    try:
        response = requests.post(api_url, data=payload, timeout=15)
        if response.status_code != 200:
            logger.error("Telegram send failed: %s", response.text)

        resp_json = response.json()
        if not resp_json.get("ok", False):
            logger.error("Telegram send returned not ok: %s", response.text)

        return True
    except Exception:
        logger.exception("Telegram send exception")


def send_prepared_data_to_telegram(prepared_data):
    token = TELEGRAM_BOT_TOKEN
    chat_id = TELEGRAM_CHAT_ID
    if not token or not chat_id:
        logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set in environment")
        return

    for item in prepared_data:
        message = format_vacancy_message(item)
        send_telegram_message(message, token, chat_id)


def main():
    vacancies = get_all_vacancies(url)
    prepared_data = prepare_data_for_send(vacancies)
    send_prepared_data_to_telegram(prepared_data)


if __name__ == "__main__":
    main()
