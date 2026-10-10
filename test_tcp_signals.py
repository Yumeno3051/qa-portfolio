# test_tcp_signals.py
"""
Автотест для проверки критического сценария:
установка TCP-соединения с сервисом-симулятором (порт 2001)
и получение 10 сигналов.

Запуск:
    1. Сначала запустить сервис-симулятор (отдельный процесс).
    2. Затем: pytest test_tcp_signals.py -v
"""

import socket
import pytest
import json
import time


# ---------- Конфигурация ----------
HOST = "127.0.0.1"      # localhost — сервис-симулятор на этой же машине
PORT = 2001             # порт из условия задачи
TIMEOUT = 5             # таймаут подключения в секундах
EXPECTED_SIGNALS = 10   # ожидаемое количество сигналов
BUFFER_SIZE = 4096      # размер буфера для чтения


# ---------- Фикстура: TCP-подключение ----------
@pytest.fixture
def tcp_connection():
    """
    Устанавливает TCP-соединение с сервисом-симулятором.
    Автоматически закрывает соединение после теста.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)

    try:
        sock.connect((HOST, PORT))
        print(f"\n✅ Подключение к {HOST}:{PORT} установлено")
    except (socket.timeout, ConnectionRefusedError) as e:
        pytest.fail(f"❌ Не удалось подключиться к {HOST}:{PORT}: {e}")

    yield sock

    sock.close()
    print("🔌 Соединение закрыто")


# ---------- Фикстура: получение данных ----------
@pytest.fixture
def received_data(tcp_connection):
    """
    Отправляет запрос на сервис и получает ответ.
    Возвращает распарсенные данные (список сигналов).
    """
    # Отправляем запрос на получение данных
    tcp_connection.sendall(b"GET_SIGNALS\n")

    # Ждём немного, чтобы сервис успел ответить
    time.sleep(0.5)

    # Читаем ответ
    try:
        raw_data = tcp_connection.recv(BUFFER_SIZE)
    except socket.timeout:
        pytest.fail("❌ Сервис не ответил в течение таймаута")

    if not raw_data:
        pytest.fail("❌ Получен пустой ответ от сервиса")

    print(f"📦 Получено {len(raw_data)} байт")

    # Парсим данные: предполагаем JSON-формат
    # Если формат другой — адаптировать под реальный ответ
    try:
        data = json.loads(raw_data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Если формат — не JSON, вернуть как строки для ручного разбора
        data = raw_data.decode("utf-8", errors="ignore").strip().split("\n")

    return data


# ---------- ТЕСТ 1: Соединение устанавливается ----------
def test_connection_established(tcp_connection):
    """
    Проверка: TCP-соединение с сервисом успешно установлено.
    """
    assert tcp_connection is not None, "Соединение не установлено"
    print("✅ Тест 1: соединение установлено")


# ---------- ТЕСТ 2: Получены данные ----------
def test_data_received(received_data):
    """
    Проверка: сервис вернул непустой ответ.
    """
    assert received_data, "Ответ от сервиса пустой"
    print(f"✅ Тест 2: получены данные ({len(received_data)} записей)")


# ---------- ТЕСТ 3: Количество сигналов ----------
def test_signals_count(received_data):
    """
    Проверка: сервис прислал ровно 10 сигналов (по условию задачи).
    """
    if isinstance(received_data, list):
        count = len(received_data)
    else:
        # Если данные — одна строка, разбиваем по разделителям
        count = len([s for s in received_data.split(";") if s.strip()])

    assert count == EXPECTED_SIGNALS, (
        f"Ожидалось {EXPECTED_SIGNALS} сигналов, получено {count}"
    )
    print(f"✅ Тест 3: получено ровно {EXPECTED_SIGNALS} сигналов")


# ---------- ТЕСТ 4: Структура сигнала ----------
def test_signal_structure(received_data):
    """
    Проверка: каждый сигнал содержит обязательные поля:
    ID, имя, значение, качество, время.
    """
    required_fields = {"id", "name", "value", "quality", "time"}

    # Берём первый сигнал для проверки
    if isinstance(received_data, list) and received_data:
        first_signal = received_data[0]
        if isinstance(first_signal, dict):
            actual_fields = set(first_signal.keys())
            missing = required_fields - actual_fields
            assert not missing, f"В сигнале отсутствуют поля: {missing}"
            print(f"✅ Тест 4: структура сигнала корректна")
        else:
            pytest.skip("Формат данных не JSON — структура не проверяется")
    else:
        pytest.skip("Нет данных для проверки структуры")


# ---------- ТЕСТ 5: Значения сигналов меняются ----------
def test_values_change_over_time(tcp_connection):
    """
    Проверка: значения сигналов обновляются между запросами
    (синусоида/случайные значения по условию задачи).
    """
    # Первый запрос
    tcp_connection.sendall(b"GET_SIGNALS\n")
    time.sleep(0.5)
    data1 = tcp_connection.recv(BUFFER_SIZE)

    # Второй запрос через паузу
    time.sleep(1.5)
    tcp_connection.sendall(b"GET_SIGNALS\n")
    time.sleep(0.5)
    data2 = tcp_connection.recv(BUFFER_SIZE)

    assert data1 != data2, (
        "Значения сигналов не изменились между запросами — "
        "возможно, сервис не обновляет данные"
    )
    print("✅ Тест 5: значения сигналов меняются во времени")


# ---------- ТЕСТ 6: Обработка отключения ----------
def test_connection_closed_gracefully():
    """
    Проверка: соединение корректно закрывается без ошибок.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)

    try:
        sock.connect((HOST, PORT))
        sock.close()
        print("✅ Тест 6: соединение закрыто корректно")
    except Exception as e:
        pytest.fail(f"❌ Ошибка при закрытии соединения: {e}")