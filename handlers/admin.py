from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from config import ADMIN_IDS
from database import models as db

router = Router()

def is_admin(uid): return uid in ADMIN_IDS


@router.message(Command("admin"))
async def admin_p(message: Message):
    if not is_admin(message.from_user.id): return
    await message.answer("Admin Panel:\n\n/stats - Statistika\n/users - Foydalanuvchilar\n/broadcast - Xabar yuborish\n/ban ID - Bloklash\n/unban ID - Chiqarish")


@router.message(Command("stats"))
async def stats(message: Message):
    if not is_admin(message.from_user.id): return
    t = await db.get_user_count()
    td = await db.get_today_users()
    a = await db.get_active_users(7)
    await message.answer(f"Jami: {t}\nBugun: {td}\nFaol 7kun: {a}")


@router.message(Command("users"))
async def users(message: Message):
    if not is_admin(message.from_user.id): return
    u = await db.get_all_users()
    await message.answer(f"Jami: {len(u)} ta\n\n" + "\n".join(map(str, u[:50])))


@router.message(Command("ban"))
async def ban(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Foydalanish: /ban USER_ID"); return
    try: await db.ban_user(int(args[1])); await message.answer("Bloklandi")
    except: pass


@router.message(Command("unban"))
async def unban(message: Message):
    if not is_admin(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2: return
    try: await db.unban_user(int(args[1])); await message.answer("Chiqarildi")
    except: pass


@router.message(Command("broadcast"))
async def bc(message: Message):
    if not is_admin(message.from_user.id): return
    if not message.reply_to_message:
        await message.answer("Xabarga reply qilib /broadcast yozing"); return
    users = await db.get_all_users()
    s = fc = 0
    for uid in users:
        try: await message.reply_to_message.send_copy(uid); s += 1
        except: fc += 1
    await message.answer(f"Yuborildi: {s}, Xato: {fc}")