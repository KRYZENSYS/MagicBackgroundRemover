"""FSM states for conversational flows."""
from aiogram.fsm.state import State, StatesGroup


class MainMenu(StatesGroup):
    idle = State()


class ImageProcessing(StatesGroup):
    waiting_photo = State()
    waiting_option = State()
    waiting_param = State()
    processing = State()


class BackgroundFlow(StatesGroup):
    choose_color = State()
    enter_gradient = State()
    enter_image = State()


class UpscaleFlow(StatesGroup):
    choose_factor = State()


class PassportFlow(StatesGroup):
    choose_size = State()
    choose_color = State()


class PremiumFlow(StatesGroup):
    choose_plan = State()
    choose_provider = State()
    waiting_payment = State()


class SettingsFlow(StatesGroup):
    choose_language = State()


class AdminFlow(StatesGroup):
    main = State()
    broadcast_text = State()
    broadcast_confirm = State()
    user_search = State()
    user_action = State()
    promo_create = State()
    plan_create = State()


class CaptchaFlow(StatesGroup):
    waiting_answer = State()


__all__ = [
    "MainMenu",
    "ImageProcessing",
    "BackgroundFlow",
    "UpscaleFlow",
    "PassportFlow",
    "PremiumFlow",
    "SettingsFlow",
    "AdminFlow",
    "CaptchaFlow",
]