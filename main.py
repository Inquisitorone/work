import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Set TELEGRAM_API_TOKEN")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class OrderState(StatesGroup):
    language = State()
    city = State()
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
    "city": {
        "uk": "Оберіть місто:",
        "ru": "Выберите город:"
    },
    "city_manual": {
        "uk": "Введіть місто вручну:",
        "ru": "Введите город вручную:"
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
    "share_phone_btn": {
        "uk": "Поділитися номером",
        "ru": "Поделиться номером"
    },
    "summary_title": {
        "uk": "Перевірте дані:",
        "ru": "Проверьте данные:"
    },
    "confirm_btn": {
        "uk": "Підтвердити",
        "ru": "Подтвердить"
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

@dp.message_handler(commands=['start'], state='*')
async def start_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language')
    if lang:
        await message.answer(INSTRUCTION[lang])
        city_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        city_kb.add(*CITIES[lang])
        city_kb.add(tr('cancel_form_btn', lang))
        await message.answer(tr("city", lang), reply_markup=city_kb)
        await OrderState.city.set()
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
    city_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    city_kb.add(*CITIES[lang])
    city_kb.add(tr('cancel_form_btn', lang))
    await message.answer(tr("city", lang), reply_markup=city_kb)
    await OrderState.city.set()

@dp.message_handler(lambda m: m.text in ["Скасувати анкету", "Отменить анкету"], state='*')
async def cancel_form(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    start_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_kb.add(tr('new_order_btn', lang))
    await state.finish()
    await message.answer("Анкету скасовано.\nМожете розпочати нову заявку.", reply_markup=start_kb)

@dp.message_handler(state=OrderState.city)
async def set_city(message: types.Message, state: FSMContext):
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return  # Уже обработано выше
    data = await state.get_data()
    lang = data.get('language', 'uk')
    manual_city = "Інше" if lang == "uk" else "Другое"
    if message.text in CITIES[lang] and message.text != manual_city:
        await state.update_data(city=message.text)
        await message.answer("✅")
        await message.answer(tr('vin', lang), reply_markup=get_cancel_kb(lang))
        await OrderState.vin.set()
    elif message.text == manual_city:
        await message.answer(tr('city_manual', lang), reply_markup=get_cancel_kb(lang))
    else:
        await state.update_data(city=message.text)
        await message.answer("✅")
        await message.answer(tr('vin', lang), reply_markup=get_cancel_kb(lang))
        await OrderState.vin.set()

@dp.message_handler(state=OrderState.vin)
async def set_vin(message: types.Message, state: FSMContext):
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await state.update_data(vin=message.text)
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
        # Кнопка для отправки контакта
        phone_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        phone_kb.add(types.KeyboardButton(tr('share_phone_btn', lang), request_contact=True))
        phone_kb.add(tr('cancel_form_btn', lang))
        await message.answer(tr('manager_name', lang), reply_markup=get_cancel_kb(lang))
        await message.answer(tr('manager_phone', lang), reply_markup=phone_kb)
        await OrderState.manager_name.set()
    else:
        await state.update_data(multimedia_lang=message.text)
        await message.answer("✅")
        phone_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        phone_kb.add(types.KeyboardButton(tr('share_phone_btn', lang), request_contact=True))
        phone_kb.add(tr('cancel_form_btn', lang))
        await message.answer(tr('manager_name', lang), reply_markup=get_cancel_kb(lang))
        await message.answer(tr('manager_phone', lang), reply_markup=phone_kb)
        await OrderState.manager_name.set()

@dp.message_handler(state=OrderState.manager_name)
async def set_manager_name(message: types.Message, state: FSMContext):
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await state.update_data(manager_name=message.text)
    await message.answer("✅")
    phone_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    phone_kb.add(types.KeyboardButton(tr('share_phone_btn', lang), request_contact=True))
    phone_kb.add(tr('cancel_form_btn', lang))
    await message.answer(tr('manager_phone', lang), reply_markup=phone_kb)
    await OrderState.manager_phone.set()

@dp.message_handler(content_types=types.ContentType.CONTACT, state=OrderState.manager_phone)
async def handle_manager_phone_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    phone = message.contact.phone_number
    await state.update_data(manager_phone=phone)
    await message.answer("✅")
    # Сразу итоговое резюме
    data = await state.get_data()
    summary = (
        f"Мова: {data.get('language', '').upper() if lang == 'uk' else 'Язык: RUS'}\n"
        f"{'Місто' if lang == 'uk' else 'Город'}: {data.get('city', '')}\n"
        f"VIN: {data.get('vin', '')}\n"
        f"Dlink: {data.get('dlink', '')}\n"
        f"{'Модель' if lang == 'uk' else 'Модель'}: {data.get('model', '')}\n"
        f"{'Мова мультимедіа' if lang == 'uk' else 'Язык мультимедиа'}: {data.get('multimedia_lang', '')}\n"
        f"{'Менеджер' if lang == 'uk' else 'Менеджер'}: {data.get('manager_name', '')}\n"
        f"{'Телефон' if lang == 'uk' else 'Телефон'}: {phone}"
    )
    confirm_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    confirm_kb.add(tr('confirm_btn', lang), tr('cancel_btn', lang))
    await message.answer(f"{tr('summary_title', lang)}\n\n{summary}", reply_markup=confirm_kb)
    await OrderState.confirm.set()

@dp.message_handler(state=OrderState.manager_phone, content_types=types.ContentType.TEXT)
async def set_manager_phone(message: types.Message, state: FSMContext):
    if message.text in ["Скасувати анкету", "Отменить анкету"]:
        return
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await state.update_data(manager_phone=message.text)
    await message.answer("✅")
    # Сразу итоговое резюме
    data = await state.get_data()
    summary = (
        f"Мова: {data.get('language', '').upper() if lang == 'uk' else 'Язык: RUS'}\n"
        f"{'Місто' if lang == 'uk' else 'Город'}: {data.get('city', '')}\n"
        f"VIN: {data.get('vin', '')}\n"
        f"Dlink: {data.get('dlink', '')}\n"
        f"{'Модель' if lang == 'uk' else 'Модель'}: {data.get('model', '')}\n"
        f"{'Мова мультимедіа' if lang == 'uk' else 'Язык мультимедиа'}: {data.get('multimedia_lang', '')}\n"
        f"{'Менеджер' if lang == 'uk' else 'Менеджер'}: {data.get('manager_name', '')}\n"
        f"{'Телефон' if lang == 'uk' else 'Телефон'}: {message.text}"
    )
    confirm_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    confirm_kb.add(tr('confirm_btn', lang), tr('cancel_btn', lang))
    await message.answer(f"{tr('summary_title', lang)}\n\n{summary}", reply_markup=confirm_kb)
    await OrderState.confirm.set()

@dp.message_handler(lambda m: m.text in ["Підтвердити", "Подтвердить"], state=OrderState.confirm)
async def confirm_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    new_order_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    new_order_kb.add(tr('new_order_btn', lang))
    await message.answer(tr('order_accepted', lang), reply_markup=new_order_kb)
    await state.reset_state(with_data=False)

@dp.message_handler(lambda m: m.text in ["Скасувати", "Отменить"], state=OrderState.confirm)
async def cancel_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    new_order_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    new_order_kb.add(tr('new_order_btn', lang))
    await message.answer(tr('operation_canceled', lang), reply_markup=new_order_kb)
    await state.reset_state(with_data=False)

@dp.message_handler(lambda m: m.text in ["Нове замовлення 📝", "Новый заказ 📝"], state='*')
async def new_order_button(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await message.answer(INSTRUCTION[lang])
    city_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    city_kb.add(*CITIES[lang])
    city_kb.add(tr('cancel_form_btn', lang))
    await message.answer(tr("city", lang), reply_markup=city_kb)
    await OrderState.city.set()

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
