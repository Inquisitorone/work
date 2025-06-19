import os
import re
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Set TELEGRAM_API_TOKEN")

ADMIN_USER_IDS = [6418780785, 1234567890]

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class OrderState(StatesGroup):
    language = State()
    brand = State()
    city = State()
    service_type = State()
    service_price = State()
    service_payment = State()
    vin = State()
    dlink = State()
    model = State()
    multimedia_lang = State()
    manager_name = State()
    manager_phone = State()
    confirm = State()

INSTRUCTION = {
    "uk": (
        "Цей бот допоможе оформити заявку на автомобіль.\n"
        "Просто обирайте варіанти або відповідайте на питання.\n"
        "Для скасування — натисніть «Скасувати анкету».\n"
        "Щоб переглянути свої заявки, напишіть /myorders."
    ),
    "ru": (
        "Этот бот поможет оформить заявку на автомобиль.\n"
        "Просто выбирайте варианты или отвечайте на вопросы.\n"
        "Для отмены — нажмите «Отменить анкету».\n"
        "Чтобы посмотреть свои заявки, напишите /myorders."
    )
}

TEXTS = {
    "choose_lang": {
        "uk": "Оберіть мову:",
        "ru": "Выберите язык:"
    },
    "choose_brand": {
        "uk": "Оберіть бренд:",
        "ru": "Выберите бренд:"
    },
    "city": {
        "uk": "Оберіть місто:",
        "ru": "Выберите город:"
    },
    "city_manual": {
        "uk": "Введіть місто вручну:",
        "ru": "Введите город вручную:"
    },
    "service_type": {
        "uk": "Послуга віддалена чи фактична на СТО?",
        "ru": "Услуга удалённая или фактическая на СТО?"
    },
    "service_types": {
        "uk": ["Віддалена 🏠", "Фактична на СТО 🏢"],
        "ru": ["Удалённая 🏠", "Фактическая на СТО 🏢"]
    },
    "vin": {
        "uk": "Введіть VIN:",
        "ru": "Введите VIN:"
    },
    "dlink": {
        "uk": "Оберіть Dlink:",
        "ru": "Выберите Dlink:"
    },
    "model": {
        "uk": "Оберіть модель:",
        "ru": "Выберите модель:"
    },
    "model_manual": {
        "uk": "Введіть свою модель:",
        "ru": "Введите свою модель:"
    },
    "multimedia_lang": {
        "uk": "Оберіть мову мультимедіа:",
        "ru": "Выберите язык мультимедиа:"
    },
    "manager_name": {
        "uk": "Введіть ім'я менеджера:",
        "ru": "Введите имя менеджера:"
    },
    "manager_phone": {
        "uk": "Введіть телефон менеджера або поділіться контактом:",
        "ru": "Введите телефон менеджера или поделитесь контактом:"
    },
    "summary_title": {
        "uk": "Перевірте дані:",
        "ru": "Проверьте данные:"
    },
    "confirm_btn": {
        "uk": "Підтвердити",
        "ru": "Подтвердить"
    },
    "edit_btn": {
        "uk": "Змінити дані",
        "ru": "Изменить данные"
    },
    "cancel_btn": {
        "uk": "Скасувати",
        "ru": "Отменить"
    },
    "order_accepted": {
        "uk": "Замовлення прийняте! Дякую! ✅",
        "ru": "Заказ принят! Спасибо! ✅"
    },
    "operation_canceled": {
        "uk": "Операцію скасовано.",
        "ru": "Операция отменена."
    },
    "new_order_btn": {
        "uk": "Нове замовлення 📝",
        "ru": "Новый заказ 📝"
    },
    "cancel_form_btn": {
        "uk": "Скасувати анкету",
        "ru": "Отменить анкету"
    }
}

def tr(key, lang):
    return TEXTS.get(key, {}).get(lang, key)

CITIES = {
    "uk": [
        "Київ", "Львів", "Одеса", "Харків", "Вінниця", "Дніпро", "Ужгород", "Інше"
    ],
    "ru": [
        "Киев", "Львов", "Одесса", "Харьков", "Винница", "Днепр", "Ужгород", "Другое"
    ]
}

BRANDS = {
    "uk": ["BYD", "Zeekr"],
    "ru": ["BYD", "Zeekr"]
}

DLINKS = {
    "uk": ["Dlink 3 🔌", "Dlink 4 ⚡️", "Dlink 5 🔋", "Інше"],
    "ru": ["Dlink 3 🔌", "Dlink 4 ⚡️", "Dlink 5 🔋", "Другое"]
}

DLINK_MODELS = {
    "Dlink 3": [
        "Qin Plus", "DM-i", "EV", "Song Pro", "Yuan Plus", "Song Max",
        "Destroyer 05", "Dolphins", "Tang Dm-i", "Інше", "Другое"
    ],
    "Dlink 4": [
        "Han 22", "Tang 22", "Song Plus", "Song Champ", "Frigate 07", "Seal EV", "Інше", "Другое"
    ],
    "Dlink 5": [
        "Song Plus", "Song L", "Song L DMI", "Seal", "Sealion 07", "Інше", "Другое"
    ]
}

MULTIMEDIA_LANGS = {
    "uk": ["Українська", "Російська"],
    "ru": ["Украинский", "Русский"]
}

def get_cancel_kb(lang, extra_buttons=None):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if extra_buttons:
        kb.add(*extra_buttons)
    kb.add(tr('cancel_form_btn', lang))
    return kb

def is_valid_vin(vin):
    vin = vin.strip().upper()
    return (
        len(vin) == 17 and
        re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin) is not None
    )

def display_user_language(code):
    if code == "uk":
        return "УКРАЇНСЬКА"
    if code == "ru":
        return "РУССКИЙ"
    return code.upper()

def display_multimedia_lang(value, lang):
    if value.lower().startswith("укр"):
        return "Українська" if lang == "uk" else "Украинский"
    if value.lower().startswith("рос") or value.lower().startswith("рус"):
        return "Російська" if lang == "uk" else "Русский"
    return value

@dp.message_handler(commands=['start'], state='*')
async def start_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language')
    if lang:
        await message.answer(INSTRUCTION[lang])
        new_order_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        new_order_kb.add(tr('new_order_btn', lang))
        await message.answer("Для початку виберіть замовлення.", reply_markup=new_order_kb)
    else:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🇺🇦 Українська", "🇷🇺 Русский")
        await message.answer("Оберіть мову / Выберите язык:", reply_markup=kb)
        await OrderState.language.set()

@dp.message_handler(state=OrderState.language)
async def set_language(message: types.Message, state: FSMContext):
    text = message.text.lower()
    if "україн" in text:
        lang = "uk"
    elif "рус" in text:
        lang = "ru"
    else:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🇺🇦 Українська", "🇷🇺 Русский")
        await message.answer("Оберіть мову / Выберите язык:", reply_markup=kb)
        return
    await state.update_data(language=lang)
    await message.answer("✅")
    await message.answer(INSTRUCTION[lang])

    brands_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    brands_kb.add(*BRANDS[lang])
    brands_kb.add(tr('cancel_form_btn', lang))
    await message.answer(tr('choose_brand', lang), reply_markup=brands_kb)
    await OrderState.brand.set()

@dp.message_handler(lambda m: m.text in ["Скасувати анкету", "Отменить анкету"], state='*')
async def cancel_form(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    start_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_kb.add(tr('new_order_btn', lang))
    await state.finish()
    await message.answer("Анкету скасовано.\nМожете розпочати нову заявку.", reply_markup=start_kb)

@dp.message_handler(lambda m: m.text in ["Нове замовлення 📝", "Новый заказ 📝"], state='*')
async def new_order_button(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    brands_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    brands_kb.add(*BRANDS[lang])
    brands_kb.add(tr('cancel_form_btn', lang))
    await message.answer(tr('choose_brand', lang), reply_markup=brands_kb)
    await OrderState.brand.set()

@dp.message_handler(state=OrderState.brand)
async def set_brand(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    if message.text == "BYD":
        await state.update_data(brand="BYD")
        city_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        city_kb.add(*CITIES[lang])
        city_kb.add(tr('cancel_form_btn', lang))
        await message.answer(tr("city", lang), reply_markup=city_kb)
        await OrderState.city.set()
    # ЗEEKR ветка — см. выше твой последний код (оставлю как было)
    # ...

@dp.message_handler(state=OrderState.city)
async def set_city(message: types.Message, state: FSMContext):
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    data = await state.get_data()
    lang = data.get('language', 'uk')
    manual_city = "Інше" if lang == "uk" else "Другое"
    if message.text in CITIES[lang] and message.text != manual_city:
        await state.update_data(city=message.text)
        await message.answer("✅")
        service_kb = get_cancel_kb(lang, TEXTS["service_types"][lang])
        await message.answer(tr('service_type', lang), reply_markup=service_kb)
        await OrderState.service_type.set()
    elif message.text == manual_city:
        await message.answer(tr('city_manual', lang), reply_markup=get_cancel_kb(lang))
    else:
        await state.update_data(city=message.text)
        await message.answer("✅")
        service_kb = get_cancel_kb(lang, TEXTS["service_types"][lang])
        await message.answer(tr('service_type', lang), reply_markup=service_kb)
        await OrderState.service_type.set()

@dp.message_handler(state=OrderState.service_type)
async def set_service_type(message: types.Message, state: FSMContext):
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    data = await state.get_data()
    lang = data.get('language', 'uk')
    match = None
    for opt in TEXTS["service_types"][lang]:
        if message.text.strip().startswith(opt.split()[0]):
            match = opt
            break
    if match:
        await state.update_data(service_type=match)
        await message.answer("✅")
        price_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        price_kb.add(tr('cancel_form_btn', lang))
        await message.answer("Введіть суму вартості послуги:", reply_markup=price_kb)
        await OrderState.service_price.set()
    else:
        await message.answer(tr('service_type', lang), reply_markup=get_cancel_kb(lang, TEXTS["service_types"][lang]))

# ----- ОБЯЗАТЕЛЬНО! Хендлер для BYD - ввод суммы -----

@dp.message_handler(state=OrderState.service_price)
async def set_service_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    price = message.text.strip()
    if not price.isdigit():
        await message.answer("Введіть коректну суму:", reply_markup=get_cancel_kb(lang))
        return
    await state.update_data(service_price=price)
    pay_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    pay_kb.add("Оплата Салон", "Оплата СТО")
    pay_kb.add(tr('cancel_form_btn', lang))
    await message.answer("Оберіть спосіб оплати:", reply_markup=pay_kb)
    await OrderState.service_payment.set()

# ...далее все шаги BYD: способ оплаты, VIN, Dlink, модель, мультимедиа, менеджер и финал...

# Остальная логика (Zeekr, подтверждение, админ-отчёт) — как выше в твоём последнем рабочем варианте.

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
