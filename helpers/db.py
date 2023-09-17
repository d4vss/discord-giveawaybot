import aiosqlite, sqlite3

DATABASE_PATH = 'database.db'

async def fetch(table_name, columns, fetch_all, where=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query = f'SELECT {columns} FROM {table_name} {where}'
        async with db.execute(query) as cursor:
            if fetch_all:
                return await cursor.fetchall()
            return await cursor.fetchone()

def dfetch(table_name, colums, fetch_all, where=None):
    with sqlite3.connect(DATABASE_PATH) as db:
        query = f'SELECT {colums} FROM {table_name} {where}'
        cursor = db.execute(query)
        if fetch_all:
            return cursor.fetchall()
        return cursor.fetchone()

async def insert(table_name, columns, values):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query = f'INSERT OR IGNORE INTO {table_name} ({columns}) VALUES ({values})'
        await db.execute(query)
        await db.commit()

async def update(table_name, columns, values, where=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query = f'UPDATE {table_name} SET {columns} = {values} {where}'
        await db.execute(query)
        await db.commit()

async def delete(table_name, where=None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query = f'DELETE FROM {table_name} {where}'
        await db.execute(query)
        await db.commit()

async def create(table_name, columns):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        query = f'CREATE TABLE IF NOT EXISTS {table_name} ({columns})'
        await db.execute(query)
        await db.commit()