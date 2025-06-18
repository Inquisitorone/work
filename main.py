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
    service_price = State()         # ← новое состояние для суммы услуги
    service_payment = State()       # ← новое состояние для оплаты
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
        "uk": "Введіть телефон менеджера:",
        "ru": "Введите телефон менеджера:"
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
    "edit_field": {
        "uk": "Що ви хочете змінити?",
        "ru": "Что вы хотите изменить?"
    },
    "fields": {
        "uk": [
            "Місто", "Тип послуги", "Вартість послуги", "Спосіб оплати", "VIN", "Dlink", "Модель", "Мова мультимедіа", "Ім'я менеджера", "Телефон менеджера"
        ],
        "ru": [
            "Город", "Тип услуги", "Стоимость услуги", "Способ оплаты", "VIN", "Dlink", "Модель", "Язык мультимедиа", "Имя менеджера", "Телефон менеджера"
        ]
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
    new_order_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    new_order_kb.add(tr('new_order_btn', lang))
    await message.answer("Для початку виберіть замовлення.", reply_markup=new_order_kb)

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
    elif message.text == "Zeekr":
        await state.update_data(brand="Zeekr")
        await message.answer("Логіка для Zeekr буде додана пізніше. Поки що зверніться до менеджера 🚗", reply_markup=get_cancel_kb(lang))
        await state.finish()
    else:
        brands_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        brands_kb.add(*BRANDS[lang])
        brands_kb.add(tr('cancel_form_btn', lang))
        await message.answer(tr('choose_brand', lang), reply_markup=brands_kb)

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
    if message.text in TEXTS["service_types"][lang]:
        await state.update_data(service_type=message.text)
        await message.answer("✅")
        price_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        price_kb.add(tr('cancel_form_btn', lang))
        await message.answer("Введіть суму вартості послуги:", reply_markup=price_kb)
        await OrderState.service_price.set()
    else:
        await message.answer(tr('service_type', lang), reply_markup=get_cancel_kb(lang, TEXTS["service_types"][lang]))

@dp.message_handler(state=OrderState.service_price)
async def set_service_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    price = message.text.strip()
    if not price:
        await message.answer("Введіть коректну суму:", reply_markup=get_cancel_kb(lang))
        return
    await state.update_data(service_price=price)
    pay_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    pay_kb.add("Оплата Салон", "Оплата СТО")
    pay_kb.add(tr('cancel_form_btn', lang))
    await message.answer("Оберіть спосіб оплати:", reply_markup=pay_kb)
    await OrderState.service_payment.set()

@dp.message_handler(state=OrderState.service_payment)
async def set_service_payment(message: types.Message, state: FSMContext):
    if message.text in ["Оплата Салон", "Оплата СТО"]:
        await state.update_data(service_payment=message.text)
        data = await state.get_data()
        lang = data.get('language', 'uk')
        await message.answer("✅")
        await message.answer(tr('vin', lang), reply_markup=get_cancel_kb(lang))
        await OrderState.vin.set()
    elif message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    else:
        pay_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        pay_kb.add("Оплата Салон", "Оплата СТО")
        data = await state.get_data()
        lang = data.get('language', 'uk')
        pay_kb.add(tr('cancel_form_btn', lang))
        await message.answer("Оберіть спосіб оплати:", reply_markup=pay_kb)

@dp.message_handler(state=OrderState.vin)
async def set_vin(message: types.Message, state: FSMContext):
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    data = await state.get_data()
    lang = data.get('language', 'uk')
    vin = message.text.strip().upper()
    if not is_valid_vin(vin):
        msg = "Некоректний VIN! Має бути 17 символів, лише латинські літери та цифри, без I, O, Q." \
            if lang == "uk" else \
            "Некорректный VIN! Должно быть 17 символов, только латинские буквы и цифры, без I, O, Q."
        await message.answer(f"❗️ {msg}\n\n{tr('vin', lang)}", reply_markup=get_cancel_kb(lang))
        return
    await state.update_data(vin=vin)
    await message.answer("✅")
    dlink_kb = get_cancel_kb(lang, DLINKS[lang])
    await message.answer(tr('dlink', lang), reply_markup=dlink_kb)
    await OrderState.dlink.set()

@dp.message_handler(state=OrderState.dlink)
async def set_dlink(message: types.Message, state: FSMContext):
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    data = await state.get_data()
    lang = data.get('language', 'uk')
    manual = "Інше" if lang == "uk" else "Другое"
    for dlink_key in DLINK_MODELS:
        if dlink_key in message.text:
            await state.update_data(dlink=message.text)
            await message.answer("✅")
            models_kb = get_cancel_kb(lang, DLINK_MODELS[dlink_key])
            await message.answer(tr('model', lang), reply_markup=models_kb)
            await OrderState.model.set()
            return
    if message.text == manual:
        await message.answer(tr('dlink', lang) + " (Введіть свій варіант / Введите свой вариант):", reply_markup=get_cancel_kb(lang))
    else:
        await state.update_data(dlink=message.text)
        await message.answer("✅")
        models_kb = get_cancel_kb(lang, ["Інше" if lang == "uk" else "Другое"])
        await message.answer(tr('model', lang), reply_markup=models_kb)
        await OrderState.model.set()

@dp.message_handler(state=OrderState.model)
async def set_model(message: types.Message, state: FSMContext):
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    data = await state.get_data()
    lang = data.get('language', 'uk')
    manual = "Інше" if lang == "uk" else "Другое"
    if message.text not in [manual]:
        await state.update_data(model=message.text)
        await message.answer("✅")
        multimedia_kb = get_cancel_kb(lang, MULTIMEDIA_LANGS[lang])
        await message.answer(tr('multimedia_lang', lang), reply_markup=multimedia_kb)
        await OrderState.multimedia_lang.set()
    else:
        await message.answer(tr('model_manual', lang), reply_markup=get_cancel_kb(lang))

@dp.message_handler(state=OrderState.multimedia_lang)
async def set_multimedia_lang(message: types.Message, state: FSMContext):
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    data = await state.get_data()
    lang = data.get('language', 'uk')
    if message.text in MULTIMEDIA_LANGS[lang]:
        await state.update_data(multimedia_lang=message.text)
        await message.answer("✅")
        await message.answer(tr('manager_name', lang), reply_markup=get_cancel_kb(lang))
        await OrderState.manager_name.set()
    else:
        await state.update_data(multimedia_lang=message.text)
        await message.answer("✅")
        await message.answer(tr('manager_name', lang), reply_markup=get_cancel_kb(lang))
        await OrderState.manager_name.set()

@dp.message_handler(state=OrderState.manager_name)
async def set_manager_name(message: types.Message, state: FSMContext):
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await state.update_data(manager_name=message.text)
    await message.answer("✅")
    await message.answer(tr('manager_phone', lang), reply_markup=get_cancel_kb(lang))
    await OrderState.manager_phone.set()

@dp.message_handler(state=OrderState.manager_phone)
async def set_manager_phone(message: types.Message, state: FSMContext):
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await state.update_data(manager_phone=message.text)
    await message.answer("✅")
    # Итоговое резюме
    data = await state.get_data()
    summary = (
        f"{'Мова' if lang == 'uk' else 'Язык'}: {display_user_language(data.get('language', ''))}\n"
        f"{'Бренд' if lang == 'uk' else 'Бренд'}: {data.get('brand', '')}\n"
        f"{'Місто' if lang == 'uk' else 'Город'}: {data.get('city', '')}\n"
        f"{'Тип послуги' if lang == 'uk' else 'Тип услуги'}: {data.get('service_type', '')}\n"
        f"{'Вартість послуги' if lang == 'uk' else 'Стоимость услуги'}: {data.get('service_price', '')}\n"
        f"{'Спосіб оплати' if lang == 'uk' else 'Способ оплаты'}: {data.get('service_payment', '')}\n"
        f"VIN: {data.get('vin', '')}\n"
        f"Dlink: {data.get('dlink', '')}\n"
        f"{'Модель' if lang == 'uk' else 'Модель'}: {data.get('model', '')}\n"
        f"{'Мова мультимедіа' if lang == 'uk' else 'Язык мультимедиа'}: {display_multimedia_lang(data.get('multimedia_lang', ''), lang)}\n"
        f"{'Менеджер' if lang == 'uk' else 'Менеджер'}: {data.get('manager_name', '')}\n"
        f"{'Телефон' if lang == 'uk' else 'Телефон'}: {message.text}"
    )
    confirm_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    confirm_kb.add(tr('confirm_btn', lang), tr('edit_btn', lang), tr('cancel_btn', lang))
    await message.answer(f"{tr('summary_title', lang)}\n\n{summary}", reply_markup=confirm_kb)
    await OrderState.confirm.set()

@dp.message_handler(lambda m: m.text in ["Підтвердити", "Подтвердить"], state=OrderState.confirm)
async def confirm_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    new_order_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    new_order_kb.add(tr('new_order_btn', lang))
    await message.answer(tr('order_accepted', lang), reply_markup=new_order_kb)
    await send_admin_order(message.from_user, data)
    await state.reset_state(with_data=False)

async def send_admin_order(user, data):
    lang = data.get('language', 'uk')
    username = user.username or ("Новий користувач" if lang == "uk" else "Новый пользователь")
    summary = (
        f"Нова заявка від @{username}\n"
        f"{'Мова' if lang == 'uk' else 'Язык'}: {display_user_language(data.get('language', ''))}\n"
        f"{'Бренд' if lang == 'uk' else 'Бренд'}: {data.get('brand', '')}\n"
        f"{'Місто' if lang == 'uk' else 'Город'}: {data.get('city', '')}\n"
        f"{'Тип послуги' if lang == 'uk' else 'Тип услуги'}: {data.get('service_type', '')}\n"
        f"{'Вартість послуги' if lang == 'uk' else 'Стоимость услуги'}: {data.get('service_price', '')}\n"
        f"{'Спосіб оплати' if lang == 'uk' else 'Способ оплаты'}: {data.get('service_payment', '')}\n"
        f"VIN: {data.get('vin', '')}\n"
        f"Dlink: {data.get('dlink', '')}\n"
        f"{'Модель' if lang == 'uk' else 'Модель'}: {data.get('model', '')}\n"
        f"{'Мова мультимедіа' if lang == 'uk' else 'Язык мультимедиа'}: {display_multimedia_lang(data.get('multimedia_lang', ''), lang)}\n"
        f"{'Менеджер' if lang == 'uk' else 'Менеджер'}: {data.get('manager_name', '')}\n"
        f"{'Телефон' if lang == 'uk' else 'Телефон'}: {data.get('manager_phone', '')}"
    )
    for admin_id in ADMIN_USER_IDS:
        try:
            await bot.send_message(admin_id, summary)
        except Exception as e:
            print(f"Ошибка при отправке админ-уведомления: {e}")

@dp.message_handler(lambda m: m.text in ["Змінити дані", "Изменить данные"], state=OrderState.confirm)
async def edit_data(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    fields_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    fields_kb.add(*TEXTS["fields"][lang])
    fields_kb.add(tr('cancel_form_btn', lang))
    await message.answer(tr('edit_field', lang), reply_markup=fields_kb)
    await state.set_state("edit_field_choice")

@dp.message_handler(state="edit_field_choice")
async def choose_field_to_edit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    field_map = {
        ("Місто", "Город"): OrderState.city,
        ("Тип послуги", "Тип услуги"): OrderState.service_type,
        ("Вартість послуги", "Стоимость услуги"): OrderState.service_price,
        ("Спосіб оплати", "Способ оплаты"): OrderState.service_payment,
        ("VIN",): OrderState.vin,
        ("Dlink",): OrderState.dlink,
        ("Модель",): OrderState.model,
        ("Мова мультимедіа", "Язык мультимедиа"): OrderState.multimedia_lang,
        ("Ім'я менеджера", "Имя менеджера"): OrderState.manager_name,
        ("Телефон менеджера",): OrderState.manager_phone,
    }
    for keys, state_obj in field_map.items():
        if message.text in keys:
            await message.answer(
                f"Оберіть заново: {message.text}" if lang == "uk" else f"Выберите заново: {message.text}",
                reply_markup=get_cancel_kb(lang)
            )
            await state.set_state(state_obj.state)
            return
    await message.answer(tr('edit_field', lang), reply_markup=get_cancel_kb(lang))

@dp.message_handler(lambda m: m.text in ["Скасувати", "Отменить"], state=OrderState.confirm)
async def cancel_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    new_order_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    new_order_kb.add(tr('new_order_btn', lang))
    await message.answer(tr('operation_canceled', lang), reply_markup=new_order_kb)
    await state.reset_state(with_data=False)

@dp.message_handler(state=None)
async def echo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    new_order_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    new_order_kb.add(tr('new_order_btn', lang))
    await message.answer(
        "Напишіть /start для початку нового замовлення.\nНапишите /start для начала нового заказа.",
        reply_markup=new_order_kb
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
