import requests

from . import config


class CloudError(Exception):
    """Ошибка при работе с облаком."""


def is_configured():
    """Проверяет наличие настроек Firebase."""
    return bool(
        config.DATABASE_URL.strip()
        and config.API_KEY.strip()
        and config.FIREBASE_EMAIL.strip()
        and config.FIREBASE_PASSWORD
    )


def authenticate():
    """Выполняет вход в Firebase Authentication."""
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

    try:
        response = requests.post(
            url,
            params={"key": config.API_KEY},
            json={
                "email": config.FIREBASE_EMAIL,
                "password": config.FIREBASE_PASSWORD,
                "returnSecureToken": True,
            },
            timeout=config.TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data["idToken"], data["localId"]
    except (requests.RequestException, ValueError, KeyError) as e:
        raise CloudError(f"Ошибка авторизации Firebase: {e}") from e


def _endpoint(uid):
    """Адрес операций конкретного пользователя."""
    base = config.DATABASE_URL.strip().rstrip("/")
    return f"{base}/users/{uid}/transactions.json"


def download(token=None, uid=None):
    """Скачивает операции из Firebase."""
    if token is None or uid is None:
        token, uid = authenticate()

    try:
        response = requests.get(
            _endpoint(uid),
            params={"auth": token},
            timeout=config.TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as e:
        raise CloudError(f"Ошибка загрузки: {e}") from e

    return data if isinstance(data, dict) else {}


def upload(records, token=None, uid=None):
    """Отправляет операции в Firebase."""
    if token is None or uid is None:
        token, uid = authenticate()

    try:
        response = requests.put(
            _endpoint(uid),
            params={"auth": token},
            json=records,
            timeout=config.TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise CloudError(f"Ошибка отправки: {e}") from e


def merge(local, remote):
    """Объединяет локальные и облачные операции."""
    merged = dict(remote)
    merged.update(local)
    return merged


def sync(local):
    """Выполняет полную синхронизацию."""
    if not is_configured():
        raise CloudError("Firebase не настроен")

    token, uid = authenticate()
    remote = download(token, uid)
    merged = merge(local, remote)
    upload(merged, token, uid)

    return merged
