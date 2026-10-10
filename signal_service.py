# signal_service.py
"""
Сервис-симулятор для тестирования десктоп-приложения.

Отправляет 10 сигналов с изменяющимися значениями (синусоида/случайные).
Работает на порту 2001.

Запуск:
    python signal_service.py
"""

import socket
import threading
import time
import json
import math
import random
from datetime import datetime


HOST = "0.0.0.0"    # слушаем все интерфейсы
PORT = 2001         # порт из условия задачи
SIGNALS_COUNT = 10  # количество сигналов


def generate_signals(tick: int) -> list:
    """
    Генерирует список из 10 сигналов.
    tick — счётчик времени для изменения значений.
    """
    signals = []
    for i in range(1, SIGNALS_COUNT + 1):
        # Синусоида для чётных, случайные для нечётных
        if i % 2 == 0:
            value = round(math.sin(tick * 0.5 + i) * 100, 2)
        else:
            value = round(random.uniform(-50, 150), 2)

        signals.append({
            "id": i,
            "name": f"Signal_{i}",
            "value": value,
            "quality": "Good",
            "time": datetime.now().strftime("%H:%M:%S")
        })
    return signals


def handle_client(conn: socket.socket, addr):
    """Обработка одного подключённого клиента."""
    print(f"✅ Клиент подключён: {addr}")
    tick = 0

    try:
        while True:
            # Ждём запрос от клиента
            data = conn.recv(1024)
            if not data:
                break

            command = data.decode("utf-8", errors="ignore").strip()
            print(f"📩 Получено: {command}")

            # Обрабатываем запрос
            if "GET_SIGNALS" in command:
                tick += 1
                signals = generate_signals(tick)
                response = json.dumps(signals, ensure_ascii=False)
                conn.sendall(response.encode("utf-8"))
                print(f"📤 Отправлено {len(signals)} сигналов")

            elif "PING" in command:
                conn.sendall(b"PONG\n")

            else:
                conn.sendall(b'{"error": "unknown command"}\n')

    except (ConnectionResetError, BrokenPipeError):
        print(f"❌ Клиент отключился: {addr}")
    finally:
        conn.close()
        print(f"🔌 Соединение с {addr} закрыто")


def main():
    """Запуск TCP-сервера."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"🚀 Сервис-симулятор запущен на {HOST}:{PORT}")
    print(f"📡 Ожидаю подключения клиентов...")

    try:
        while True:
            conn, addr = server.accept()
            # Каждого клиента обрабатываем в отдельном потоке
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\n🛑 Остановка сервиса...")
    finally:
        server.close()


if __name__ == "__main__":
    main()