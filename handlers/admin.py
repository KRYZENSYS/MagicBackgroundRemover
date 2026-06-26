"""Admin panel handlers."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from core.settings import settings
from core.logger import logger
from database.engine import async_session
from database.repositories.user_repo import UserRepository
from database.repositories.image_repo import ImageRepository
from database.repositories.payment_repo import PaymentRepository
from keyboards.inline import admin_menu
from localization import get_text

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("\ud83d\udd11 Admin panel:", reply_markup=admin_menu())


@router.message(Command("stats_global"))
async def cmd_stats_global(message: Message):
    if not is_admin(message.from_user.id):
        return
    async with async_session() as session:
        user_repo = UserRepository(session)
        img_repo = ImageRepository(session)
        pay_repo = PaymentRepository(session)
        total = await user_repo.count()
        active_7d = await user_repo.count_active(7)
        premium = await user_repo.count_premium()
        today = await user_repo.count_today()
        images_total = await img_repo.total_count()
        images_today = await img_repo.today_count()
        revenue = await pay_repo.total_revenue()
        revenue_today = await pay_repo.revenue_today()
        await message.answer(
            f"\ud83d\udcca Global statistika:\n\n"
            f"👥 Users:\n  Total: {total}\n  Today: {today}\n  Active 7d: {active_7d}\n  Premium: {premium}\n\n"
            f"🖼 Images:\n  Total: {images_total}\n  Today: {images_today}\n\n"
            f"💰 Revenue:\n  Total: {revenue} {settings.CURRENCY}\n  Today: {revenue_today} {settings.CURRENCY}"
        )


@router.message(Command("ban"))
async def cmd_ban(message: Message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Foydalanish: /ban <user_id> [sabab]")
        return
    target = int(args[1])
    reason = " ".join(args[2:]) if len(args) > 2 else "No reason"
    async with async_session() as session:
        await UserRepository(session).ban(target, reason)
    await message.answer(f"🚫 {target} ban qilindi: {reason}")


@router.message(Command("unban"))
async def cmd_unban(message: Message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Foydalanish: /unban <user_id>")
        return
    async with async_session() as session:
        await UserRepository(session).unban(int(args[1]))
    await message.answer(f"✅ {args[1]} unban qilindi")


@router.message(Command("grant_premium"))
async def cmd_grant(message: Message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Foydalanish: /grant_premium <user_id> <days>")
        return
    async with async_session() as session:
        await UserRepository(session).set_premium(int(args[1]), int(args[2]))
    await message.answer(f"✅ {args[1]} ga {args[2]} kun premium berildi")


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        return
    if not message.reply_to_message:
        await message.answer("Reply qilib xabar yozing")
        return
    async with async_session() as session:
        users = await UserRepository(session).list_all(limit=10000)
    sent = 0
    failed = 0
    for u in users:
        try:
            await message.reply_to_message.send_copy(u.telegram_id)
            sent += 1
        except Exception:
            failed += 1
    await message.answer(f"📊 Broadcast yakunlandi:\nYuborildi: {sent}\nXato: {failed}")


@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await cmd_stats_global(callback.message)
    await callback.answer()