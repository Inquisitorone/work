import os
if not os.path.isfile('google-credentials.json'):
    creds_json = os.getenv("GOOGLE_CREDS")
    if creds_json:
        with open("google-credentials.json", "w") as f:
            f.write(creds_json)
import re
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

logging.basicConfig(level=logging.INFO)

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
    "order_accepted": {
        "uk": "Замовлення прийняте! Дякую! ✅",
        "ru": "Заказ принят! Спасибо! ✅"
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

CITIES = {
    "uk": ["Київ", "Львів", "Одеса", "Харків", "Вінниця", "Дніпро", "Ужгород", "Інше"],
    "ru": ["Киев", "Львов", "Одесса", "Харьков", "Винница", "Днепр", "Ужгород", "Другое"]
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

ZEEKR_MODELS = [
    "001", "7X", "X", "007", "Інше", "Другое"
]

def tr(key, lang):
    return TEXTS.get(key, {}).get(lang, key)

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

def append_to_gsheet(data):
    logging.warning("append_to_gsheet STARTED!")
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name('google-credentials.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open("Заявки АвтоБота").sheet1  # <-- Имя таблицы!

        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            data.get('username', ''),
            data.get('brand', ''),
            data.get('city', ''),
            data.get('service_type', ''),
            data.get('service_price', ''),
            data.get('service_payment', ''),
            data.get('vin', ''),
            data.get('dlink', ''),
            data.get('model', ''),
            data.get('multimedia_lang', ''),
            data.get('manager_name', ''),
            data.get('manager_phone', ''),
        ]
        sheet.append_row(row, value_input_option='USER_ENTERED')
        logging.warning("append_to_gsheet FINISHED!")
    except Exception as e:
        logging.error(f"append_to_gsheet ERROR: {e}")

# /start и выбор языка
@dp.message_handler(commands=['start'], state='*')
async def start_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language')
    if lang:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(tr('new_order_btn', lang))
        await message.answer("Для початку виберіть замовлення.", reply_markup=kb)
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
    brands_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    brands_kb.add(*BRANDS[lang])
    await message.answer("✅", reply_markup=types.ReplyKeyboardRemove())
    await message.answer(tr('choose_brand', lang), reply_markup=brands_kb)
    await OrderState.brand.set()

@dp.message_handler(lambda m: m.text in ["Нове замовлення 📝", "Новый заказ 📝"], state='*')
async def new_order_button(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language')
    if not lang:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("🇺🇦 Українська", "🇷🇺 Русский")
        await message.answer("Оберіть мову / Выберите язык:", reply_markup=kb)
        await OrderState.language.set()
        return
    brands_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    brands_kb.add(*BRANDS[lang])
    await message.answer(tr('choose_brand', lang), reply_markup=brands_kb)
    await OrderState.brand.set()

# Выбор бренда (BYD или Zeekr)
@dp.message_handler(state=OrderState.brand)
async def set_brand(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get('language', 'uk')
    if message.text == "BYD":
        await state.update_data(brand="BYD")
        city_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        city_kb.add(*CITIES[lang])
        await message.answer(tr('city', lang), reply_markup=city_kb)
        await OrderState.city.set()
    elif message.text == "Zeekr":
        await state.update_data(brand="Zeekr")
        city_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        city_kb.add(*CITIES[lang])
        await message.answer(tr('city', lang), reply_markup=city_kb)
        await OrderState.city.set()
    else:
        brands_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        brands_kb.add(*BRANDS[lang])
        await message.answer(tr('choose_brand', lang), reply_markup=brands_kb)

# Город
@dp.message_handler(state=OrderState.city)
async def set_city(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get('language', 'uk')
    await state.update_data(city=message.text)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(*TEXTS['service_types'][lang])
    await message.answer(tr('service_type', lang), reply_markup=kb)
    await OrderState.service_type.set()

# Тип услуги
@dp.message_handler(state=OrderState.service_type)
async def set_service_type(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get('language', 'uk')
    match = None
    for opt in TEXTS["service_types"][lang]:
        if message.text.strip().startswith(opt.split()[0]):
            match = opt
            break
    if match:
        await state.update_data(service_type=match)
        await message.answer("✅")
        await message.answer("Введіть суму вартості послуги:")
        await OrderState.service_price.set()
    else:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(*TEXTS['service_types'][lang])
        await message.answer(tr('service_type', lang), reply_markup=kb)

# Сумма услуги
@dp.message_handler(state=OrderState.service_price)
async def set_service_price(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get('language', 'uk')
    price = message.text.strip()
    if not price.isdigit():
        await message.answer("Введіть коректну суму:")
        return
    await state.update_data(service_price=price)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Оплата Салон", "Оплата СТО")
    await message.answer("Оберіть спосіб оплати:", reply_markup=kb)
    await OrderState.service_payment.set()

# Оплата
@dp.message_handler(state=OrderState.service_payment)
async def set_service_payment(message: types.Message, state: FSMContext):
    if message.text not in ["Оплата Салон", "Оплата СТО"]:
        await message.answer("Оберіть спосіб оплати: (кнопкою)")
        return
    await state.update_data(service_payment=message.text)
    lang = (await state.get_data()).get('language', 'uk')
    await message.answer(tr('vin', lang), reply_markup=types.ReplyKeyboardRemove())
    await OrderState.vin.set()

# VIN
@dp.message_handler(state=OrderState.vin)
async def set_vin(message: types.Message, state: FSMContext):
    vin = message.text.strip().upper()
    if not is_valid_vin(vin):
        await message.answer("Некоректний VIN! Має бути 17 символів.")
        return
    await state.update_data(vin=vin)
    lang = (await state.get_data()).get('language', 'uk')
    brand = (await state.get_data()).get('brand', 'BYD')
    if brand == "BYD":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(*DLINKS[lang])
        await message.answer(tr('dlink', lang), reply_markup=kb)
        await OrderState.dlink.set()
    else:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(*ZEEKR_MODELS)
        await message.answer("Оберіть модель Zeekr:", reply_markup=kb)
        await OrderState.model.set()

# Dlink (только BYD)
@dp.message_handler(state=OrderState.dlink)
async def set_dlink(message: types.Message, state: FSMContext):
    dlink_choice = message.text.strip()  # сохраняем с эмодзи!
    await state.update_data(dlink=dlink_choice)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    dlink_key = dlink_choice.split()[0] + " " + dlink_choice.split()[1] if dlink_choice.startswith("Dlink") else dlink_choice
    if dlink_key in DLINK_MODELS:
        kb.add(*DLINK_MODELS[dlink_key])
    await message.answer(tr('model', (await state.get_data()).get('language', 'uk')), reply_markup=kb)
    await OrderState.model.set()

# Модель (и BYD и Zeekr)
@dp.message_handler(state=OrderState.model)
async def set_model(message: types.Message, state: FSMContext):
    await state.update_data(model=message.text)
    lang = (await state.get_data()).get('language', 'uk')
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(*MULTIMEDIA_LANGS[lang])
    await message.answer(tr('multimedia_lang', lang), reply_markup=kb)
    await OrderState.multimedia_lang.set()

# Язык мультимедиа
@dp.message_handler(state=OrderState.multimedia_lang)
async def set_multimedia_lang(message: types.Message, state: FSMContext):
    await state.update_data(multimedia_lang=message.text)
    lang = (await state.get_data()).get('language', 'uk')
    await message.answer(tr('manager_name', lang), reply_markup=types.ReplyKeyboardRemove())
    await OrderState.manager_name.set()

# Менеджер
@dp.message_handler(state=OrderState.manager_name)
async def set_manager_name(message: types.Message, state: FSMContext):
    await state.update_data(manager_name=message.text)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("📱 Поділитися телефоном", request_contact=True))
    kb.add("Ввести вручну")
    await message.answer(tr('manager_phone', (await state.get_data()).get('language', 'uk')), reply_markup=kb)
    await OrderState.manager_phone.set()

@dp.message_handler(state=OrderState.manager_phone, content_types=types.ContentTypes.CONTACT)
async def set_manager_phone_contact(message: types.Message, state: FSMContext):
    if message.contact and message.contact.phone_number:
        await state.update_data(manager_phone=message.contact.phone_number)
        await send_summary(message, state)

@dp.message_handler(state=OrderState.manager_phone)
async def set_manager_phone_manual(message: types.Message, state: FSMContext):
    if message.text == "Ввести вручну":
        await message.answer("Введіть телефон вручну:")
        return
    await state.update_data(manager_phone=message.text)
    await send_summary(message, state)

# Финальное подтверждение и отправка админу
async def send_summary(message, state):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    brand = data.get('brand', 'BYD')
    if brand == "Zeekr":
        summary = (
            f"Бренд: Zeekr\n"
            f"Місто: {data.get('city', '')}\n"
            f"Тип послуги: {data.get('service_type', '')}\n"
            f"Вартість послуги: {data.get('service_price', '')}\n"
            f"Спосіб оплати: {data.get('service_payment', '')}\n"
            f"VIN: {data.get('vin', '')}\n"
            f"Модель: {data.get('model', '')}\n"
            f"Мова мультимедіа: {display_multimedia_lang(data.get('multimedia_lang', ''), lang)}\n"
            f"Менеджер: {data.get('manager_name', '')}\n"
            f"Телефон: {data.get('manager_phone', '')}"
        )
    else: # BYD
        summary = (
            f"Мова: {display_user_language(data.get('language', ''))}\n"
            f"Бренд: BYD\n"
            f"Місто: {data.get('city', '')}\n"
            f"Тип послуги: {data.get('service_type', '')}\n"
            f"Вартість послуги: {data.get('service_price', '')}\n"
            f"Спосіб оплати: {data.get('service_payment', '')}\n"
            f"VIN: {data.get('vin', '')}\n"
            f"Dlink: {data.get('dlink', '')}\n"
            f"Модель: {data.get('model', '')}\n"
            f"Мова мультимедіа: {display_multimedia_lang(data.get('multimedia_lang', ''), lang)}\n"
            f"Менеджер: {data.get('manager_name', '')}\n"
            f"Телефон: {data.get('manager_phone', '')}"
        )
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(tr('confirm_btn', lang))
    await message.answer(f"{tr('summary_title', lang)}\n\n{summary}", reply_markup=kb)
    await OrderState.confirm.set()

@dp.message_handler(lambda m: m.text in ["Підтвердити", "Подтвердить"], state=OrderState.confirm)
async def confirm_order(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get('language', 'uk')
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(tr('new_order_btn', lang))
    await message.answer(tr('order_accepted', lang), reply_markup=kb)
    data = await state.get_data()
    data['username'] = message.from_user.username or ""
    append_to_gsheet(data)  # <<--- тут всё пишется в таблицу
    await send_admin_order(message.from_user, data)
    await state.finish()

async def send_admin_order(user, data):
    lang = data.get('language', 'uk')
    username = user.username or "Без юзернейму"
    if data.get('brand') == "Zeekr":
        summary = (
            f"Нова заявка від @{username}\n"
            f"Бренд: Zeekr\n"
            f"Місто: {data.get('city', '')}\n"
            f"Тип послуги: {data.get('service_type', '')}\n"
            f"Вартість послуги: {data.get('service_price', '')}\n"
            f"Спосіб оплати: {data.get('service_payment', '')}\n"
            f"VIN: {data.get('vin', '')}\n"
            f"Модель: {data.get('model', '')}\n"
            f"Мова мультимедіа: {display_multimedia_lang(data.get('multimedia_lang', ''), lang)}\n"
            f"Менеджер: {data.get('manager_name', '')}\n"
            f"Телефон: {data.get('manager_phone', '')}"
        )
    else:
        summary = (
            f"Нова заявка від @{username}\n"
            f"Мова: {display_user_language(data.get('language', ''))}\n"
            f"Бренд: BYD\n"
            f"Місто: {data.get('city', '')}\n"
            f"Тип послуги: {data.get('service_type', '')}\n"
            f"Вартість послуги: {data.get('service_price', '')}\n"
            f"Спосіб оплати: {data.get('service_payment', '')}\n"
            f"VIN: {data.get('vin', '')}\n"
            f"Dlink: {data.get('dlink', '')}\n"
            f"Модель: {data.get('model', '')}\n"
            f"Мова мультимедіа: {display_multimedia_lang(data.get('multimedia_lang', ''), lang)}\n"
            f"Менеджер: {data.get('manager_name', '')}\n"
            f"Телефон: {data.get('manager_phone', '')}"
        )
    for admin_id in ADMIN_USER_IDS:
        try:
            await bot.send_message(admin_id, summary)
        except Exception as e:
            print(f"Ошибка при отправке админ-уведомления: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
