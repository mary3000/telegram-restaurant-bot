import sqlite3

conn = sqlite3.connect('Restaurant.db')
c = conn.cursor()
c.execute('''
PRAGMA foreign_keys = ON;
''')
conn.commit()

c.execute('''
CREATE TABLE IF NOT EXISTS Заказы(
    Заказ INTEGER PRIMARY KEY AUTOINCREMENT,
    Столик INTEGER NOT NULL,
    Дата DATETIME NOT NULL,
    FOREIGN KEY(Столик) REFERENCES Столики(Столик)
); 
''')
conn.commit()

c.execute('''
CREATE TABLE IF NOT EXISTS Заказы_Блюда(
    Заказ INTEGER NOT NULL,
    Блюдо INTEGER NOT NULL,
    FOREIGN KEY(Заказ) REFERENCES Заказы(Заказ),
    FOREIGN KEY(Блюдо) REFERENCES Блюда(Блюдо)
); 
''')
conn.commit()

c.execute('''
CREATE TABLE IF NOT EXISTS Блюда (
    Блюдо INTEGER PRIMARY KEY AUTOINCREMENT,
    Название TEXT UNIQUE NOT NULL,
    Тип TEXT NOT NULL CHECK (Тип IN ('Горячие закуски', 'Холодные закуски', 'Супы', 'Основные блюда', 'Десерты')),
    Ингредиенты TEXT,
    Цена INTEGER NOT NULL,
    Наличие BOOLEAN NOT NULL,
    Скидка INTEGER,
    Вегетарианское BOOLEAN NOT NULL
);
''')
conn.commit()

c.execute('''
CREATE INDEX IF NOT EXISTS my_index ON Блюда(Наличие, Тип, Вегетарианское);
''')
conn.commit()
c.execute('''
CREATE TABLE IF NOT EXISTS Столики (
    Столик INTEGER PRIMARY KEY AUTOINCREMENT,
    Тип TEXT NOT NULL CHECK (Тип IN ('VIP', 'У окна', 'В зале')),
    Места INTEGER NOT NULL,
    Цена INTEGER NOT NULL
);
''')
conn.commit()

c.execute('''
CREATE TABLE IF NOT EXISTS Бронирования (
    Столик INTEGER NOT NULL,
    Дата DATETIME NOT NULL,
    FOREIGN KEY(Столик) REFERENCES Столики(Столик),
    CONSTRAINT Бронь UNIQUE (Столик, Дата)
);
''')
conn.commit()

c.execute('''
CREATE TABLE IF NOT EXISTS Доходы (
    Дата DATETIME NOT NULL,
    Доход INTEGER NOT NULL,
    Состояние_счета INTEGER NOT NULL
);
''')
conn.commit()

c.close()
conn.close()
