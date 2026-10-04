import sqlite3
from datetime import datetime
from config import DATABASE 
import os
import cv2

class DatabaseManager:
    
    def __init__(self, database):
        self.database = database

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                user_name TEXT
            )
        ''')

            conn.execute('''
            CREATE TABLE IF NOT EXISTS prizes (
                prize_id INTEGER PRIMARY KEY,
                image TEXT,
                used INTEGER DEFAULT 0
            )
        ''')

            conn.execute('''
            CREATE TABLE IF NOT EXISTS winners (
                user_id INTEGER,
                prize_id INTEGER,
                win_time TEXT,
                delivered INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(prize_id) REFERENCES prizes(prize_id)
            )
        ''')

            winner_columns = {row[1] for row in conn.execute('PRAGMA table_info(winners)')}
            if 'delivered' not in winner_columns:
                conn.execute('ALTER TABLE winners ADD COLUMN delivered INTEGER NOT NULL DEFAULT 0')

            conn.commit()

    def add_user(self, user_id, user_name):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('INSERT INTO users VALUES (?, ?)', (user_id, user_name))
            conn.commit()

    def add_prize(self, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany('''INSERT INTO prizes (image) VALUES (?)''', data)
            conn.commit()

    def add_winner(self, user_id, prize_id):
        win_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM winners WHERE user_id = ? AND prize_id = ?", (user_id, prize_id))
            if cur.fetchone():
                return 0
            conn.execute('''INSERT INTO winners (user_id, prize_id, win_time) VALUES (?, ?, ?)''', (user_id, prize_id, win_time))
            conn.commit()
            return 1

    def get_next_user_prize(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT p.prize_id, p.image, w.win_time
                FROM winners w
                JOIN prizes p ON p.prize_id = w.prize_id
                WHERE w.user_id = ? AND w.delivered = 0
                ORDER BY w.win_time ASC
                LIMIT 1
            ''', (user_id,))
            return cur.fetchone()

    def mark_prize_delivered(self, user_id, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''
                UPDATE winners SET delivered = 1
                WHERE user_id = ? AND prize_id = ? AND delivered = 0
            ''', (user_id, prize_id))

    def mark_prize_used(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''UPDATE prizes SET used = 1 WHERE prize_id = ?''', (prize_id,))
            conn.commit()


    def get_users(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT user_id FROM users')
            rows = cur.fetchall()
        return [x[0] for x in rows]

    def get_prize_img(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT image FROM prizes WHERE prize_id = ?', (prize_id,))
            row = cur.fetchone()
        if row is None:
            raise ValueError(f'Prize with id {prize_id} not found')
        return row[0]

    def get_random_prize(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM prizes WHERE used = 0 ORDER BY RANDOM() LIMIT 1')
            row = cur.fetchone()
        if row is None:
            raise ValueError('No unused prizes available')
        return row
    def get_winners_count(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM winners WHERE prize_id = ?', (prize_id,))
            return cur.fetchall()[0][0]
   
   
    
    def get_rating(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT user_id, prize_id FROM winners ' \
            'INNER JOIN users ON winners.user_id = users.user_id ' \
            'ORDER BY count_prize ' \
            'LIMIT 10')
            return cur.fetchall()
  
def hide_img(img_name):
    image = cv2.imread(f'img/{img_name}')
    blurred_image = cv2.GaussianBlur(image, (15, 15), 0)
    pixelated_image = cv2.resize(blurred_image, (30, 30), interpolation=cv2.INTER_NEAREST)
    pixelated_image = cv2.resize(pixelated_image, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(f'hidden_img/{img_name}', pixelated_image)

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    manager.create_tables()
    prizes_img = os.listdir('img')
    data = [(x,) for x in prizes_img]
    manager.add_prize(data)
