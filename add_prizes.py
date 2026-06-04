# add_prizes.py
from app import SessionLocal, Prize
from sqlalchemy import create_engine
from app import Base, engine

# Создаём таблицы, если их нет
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Удаляем старые призы, если есть
db.query(Prize).delete()
db.commit()

# Список призов
prizes = [
    {"name": "Сертификат 'Скидка на уроки 200 рублей'", "description": "Скидка 200 рублей на следующие уроки", "cost": 50, "icon": "fa-percent"},
    {"name": "Сертификат на ОЗОН 300 рублей", "description": "Подарочный сертификат OZON на 300 рублей", "cost": 100, "icon": "fa-box"},
    {"name": "Золотое яблоко 300 рублей", "description": "Подарочный сертификат 'Золотое яблоко' на 300 рублей", "cost": 100, "icon": "fa-apple"},
    {"name": "Скидка на уроки 400 рублей", "description": "Скидка 400 рублей на следующие уроки", "cost": 300, "icon": "fa-percent"},
    {"name": "Сертификат Золотое яблоко 500 рублей", "description": "Подарочный сертификат 'Золотое яблоко' на 500 рублей", "cost": 500, "icon": "fa-apple"},
    {"name": "Сертификат на Вайлдберис 500 рублей", "description": "Подарочный сертификат Wildberries на 500 рублей", "cost": 500, "icon": "fa-shopping-bag"},
]

for p in prizes:
    prize = Prize(
        name=p["name"],
        description=p["description"],
        cost=p["cost"],
        icon=p["icon"]
    )
    db.add(prize)
    print(f"Добавлен: {p['name']} - {p['cost']} кубков")

db.commit()
db.close()
print("Готово! Призы добавлены.")