import requests


def sing_in(lgn, pswd):
    """Запрос к Django api/token для аутентификации:"""
    try:
        url = "http://localhost:8000/api/token/bot/"
        data_sing = {"email": lgn, "password": pswd}
        response_sing = requests.post(url, data_sing)
        return response_sing
    except requests.ConnectionError:
        return None


def tasks_load(access_token):
    """Запрос к Django api/v1/task для авторизации и получения списка заданий:"""
    try:
        url = "http://127.0.0.1:8000/api/v1/task/"
        response_tasks = requests.get(url, access_token)
        return response_tasks
    except requests.ConnectionError:
        return None


def descr_load(response_list, user_tasks_id):
    """Создание словаря с задачами: все задачи, мои задачи:"""
    tasks_all = []
    tasks_my = {}

    for i in response_list:
        tasks_all.append(f"Task id: { i['id']}\nFirst name: {i['user_first_name']}\nLast name: {i['user_last_name']}\nUser id: {i['user']}\nDescription: {i['description']}\nStatus: {i['status']}")

    for j in response_list:
        if user_tasks_id == j['user'] and j['id'] not in tasks_my:
            tasks_my.update({f"task {j['id']}": f"Task id: { j['id']}\nFirst name: {j['user_first_name']}\nLast Name: {j['user_last_name']}\nUser id: {j['user']}\nDescription: {j['description']}\nStatus: {j['status']}"})

    if not tasks_my:
        tasks_my = None

    download = dict(all=tasks_all, my=tasks_my)
    return download


def task_change(task_id_to_change, status_to_change, access_token):
    """Запрос к Django api/v1/task/id/ для изменения статуса задачи:"""
    try:
        url = "http://127.0.0.1:8000/api/v1/task/" + f"{task_id_to_change}/"
        response_task = requests.get(url, access_token)
        result = response_task.json()
        result['status'] = status_to_change
        response_change = requests.put(url, result)
        return response_change
    except requests.ConnectionError:
        return None
