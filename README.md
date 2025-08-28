## pustoProject — модели игроков и бустов (SQLAlchemy)

Этот репозиторий содержит модели и примеры работы с системой игроков, их бустов/наградами на SQLAlchemy

### Структура
- `app/extensions.py` — инициализация `db` (`SQLAlchemy`).
- `app/config.py` — конфиг проекта, читает переменные из `.env` (например, `DAILY_LOGIN_POINTS`).
- `app/models/` — модели и перечисления:
  - `player.py` — модель `Player` и методы работы с поинтами/бустами.
  - `boost.py` — модель `Boost` с типом буста, сроком действия и связью с игроком.
  - `enums.py` — перечисление `BoostType`.
  - `all_models.py` — альтернативная/расширенная схема уровней и призов (`dj_*` таблицы).

### Требования
- Python 3.10+
- Рекомендуется виртуальное окружение (`venv`)

Зависимости (минимум):
```
pip install Flask Flask-SQLAlchemy SQLAlchemy python-dotenv
```

Если используете PostgreSQL: добавьте `psycopg2-binary`.

### Быстрый старт
1) Клонируйте проект и создайте окружение:
```
python -m venv .venv
.venv\\Scripts\\activate  # Windows PowerShell
pip install Flask Flask-SQLAlchemy SQLAlchemy python-dotenv
```

2) Создайте файл `.env` в корне проекта (рядом с `app/`):
```
DAILY_LOGIN_POINTS=10
```

3) Проверьте конфиг: `app/config.py` читает `.env` и выставляет `Config.DAILY_LOGIN_POINTS`.

### Инициализация приложения (пример)
Если у вас ещё нет Flask‑приложения, минимальный пример:
```python
from flask import Flask
from app.extensions import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dev.db'  # замените на свою БД
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    with app.app_context():
        db.create_all()
    return app

app = create_app()
```

После запуска приложение создаст таблицы для моделей, если они импортированы (см. ниже).

### Подключение моделей
Чтобы таблицы `Player` и `Boost` попали в metadata при `create_all()`, импортируйте их до миграций/создания таблиц:
```python
from app.models.player import Player
from app.models.boost import Boost
```

### Запуск примера
Примеры не требуют поднятого Flask‑сервера, они демонстрируют работу API объектов в памяти.
```
python app/examples/boost_usage_example.py
```

### Ключевые сущности
- `Player`:
  - поля: `id`, `email`, `full_name`, даты логинов, `points`.
  - методы: `register_login()`, `add_points()`, `add_boost()`, `add_level_completion_boost()`, `add_manual_boost()`.
- `Boost`:
  - поля: `type` (`BoostType`), `amount`, `expires_at`, связь с `Player`.
  - метод: `is_active(now=None)`.
- `BoostType` — перечисление типов бустов: `HANDS`, `BOOMB`, `SHIELD`, `FREEZE`, `MAGNET`.
- `all_models.py` — дополнительная схема уровней и призов (`Player`, `Level`, `Prize`, `PlayerLevel`, `LevelPrize`) и сервисы:
  - `assign_prize_to_player_level(...)`
  - `export_player_levels_to_csv(file_path, ...)`

### Частые сценарии (фрагменты)
Добавить поинты за ежедневный логин:
```python
from app.models.player import Player

player = Player(id="player_123", email="player@example.com")
player.register_login()  # при смене даты добавит Config.DAILY_LOGIN_POINTS
```

Выдать буст за прохождение уровня:
```python
from app.models.player import Player
from app.models.enums import BoostType

player = Player(id="player_123", email="player@example.com")
boost = player.add_level_completion_boost(level_id="level_5", boost_type=BoostType.SHIELD, amount=2, duration_hours=24)
```

Ручная выдача бессрочного буста админом:
```python
from app.models.player import Player
from app.models.enums import BoostType

player = Player(id="player_123", email="player@example.com")
boost = player.add_manual_boost(boost_type=BoostType.MAGNET, amount=3, granted_by_user_id="admin_456", duration_hours=None)
```

### Настройка окружения
- `DAILY_LOGIN_POINTS` — количество очков за вход в день (используется в `Player.points` по умолчанию и при `register_login()`).
