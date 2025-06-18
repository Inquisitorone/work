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
    order_number = State()
    confirm = State()

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
        "uk": "Введіть Dlink:",
        "ru": "Введите Dlink:"
    },
    "model": {
        "uk": "Введіть модель:",
        "ru": "Введите модель:"
    },
    "multimedia_lang": {
        "uk": "Введіть мову мультимедіа:",
        "ru": "Введите язык мультимедиа:"
    },
    "manager_name": {
        "uk": "Введіть ім'я менеджера:",
        "ru": "Введите имя менеджера:"
    },
    "manager_phone": {
        "uk": "Введіть телефон менеджера:",
        "ru": "Введите телефон менеджера:"
    },
    "order_number": {
        "uk": "Введіть номер замовлення або напишіть 'Пропустити':",
        "ru": "Введите номер заказа или напишите 'Пропустить':"
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
        "uk": "Замовлення прийняте! Дякую!",
        "ru": "Заказ принят! Спасибо!"
    },
    "operation_canceled": {
        "uk": "Операцію скасовано.",
        "ru": "Операция отменена."
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

@dp.message_handler(commands=['start'], state='*')
async def start_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language')
    if lang:
        # Язык уже выбран — сразу предлагаем выбрать город
        city_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        city_kb.add(*CITIES[lang])
        await message.answer(tr("city", lang), reply_markup=city_kb)
        await OrderState.city.set()
    else:
        # Первый запуск — просим выбрать язык
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
    city_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    city_kb.add(*CITIES[lang])
    await message.answer(tr("city", lang), reply_markup=city_kb)
    await OrderState.city.set()

@dp.message_handler(state=OrderState.city)
async def set_city(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    manual_city = "Інше" if lang == "uk" else "Другое"
    if message.text in CITIES[lang] and message.text != manual_city:
        await state.update_data(city=message.text)
        await message.answer(tr('vin', lang), reply_markup=types.ReplyKeyboardRemove())
        await OrderState.vin.set()
    elif message.text == manual_city:
        await message.answer(tr('city_manual', lang), reply_markup=types.ReplyKeyboardRemove())
        # Следующее сообщение — ручной ввод города
    else:
        # Ручной ввод города
        await state.update_data(city=message.text)
        await message.answer(tr('vin', lang))
        await OrderState.vin.set()

@dp.message_handler(state=OrderState.vin)
async def set_vin(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await state.update_data(vin=message.text)
    await message.answer(tr('dlink', lang))
    await OrderState.dlink.set()

@dp.message_handler(state=OrderState.dlink)
async def set_dlink(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await state.update_data(dlink=message.text)
    await message.answer(tr('model', lang))
    await OrderState.model.set()

@dp.message_handler(state=OrderState.model)
async def set_model(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await state.update_data(model=message.text)
    await message.answer(tr('multimedia_lang', lang))
    await OrderState.multimedia_lang.set()

@dp.message_handler(state=OrderState.multimedia_lang)
async def set_multimedia_lang(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await state.update_data(multimedia_lang=message.text)
    await message.answer(tr('manager_name', lang))
    await OrderState.manager_name.set()

@dp.message_handler(state=OrderState.manager_name)
async def set_manager_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await state.update_data(manager_name=message.text)
    await message.answer(tr('manager_phone', lang))
    await OrderState.manager_phone.set()

@dp.message_handler(state=OrderState.manager_phone)
async def set_manager_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await state.update_data(manager_phone=message.text)
    await message.answer(tr('order_number', lang))
    await OrderState.order_number.set()

@dp.message_handler(state=OrderState.order_number)
async def set_order_number(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    if (lang == "uk" and message.text != "Пропустити") or (lang == "ru" and message.text != "Пропустить"):
        await state.update_data(order_number=message.text)
    else:
        await state.update_data(order_number="Немає" if lang == "uk" else "Нет")
    data = await state.get_data()
    summary = (
        f"Мова: {data.get('language', '').upper() if lang == 'uk' else 'Язык: RUS'}\n"
        f"{'Місто' if lang == 'uk' else 'Город'}: {data.get('city', '')}\n"
        f"VIN: {data.get('vin', '')}\n"
        f"Dlink: {data.get('dlink', '')}\n"
        f"{'Модель' if lang == 'uk' else 'Модель'}: {data.get('model', '')}\n"
        f"{'Мова мультимедіа' if lang == 'uk' else 'Язык мультимедиа'}: {data.get('multimedia_lang', '')}\n"
        f"{'Менеджер' if lang == 'uk' else 'Менеджер'}: {data.get('manager_name', '')}\n"
        f"{'Телефон' if lang == 'uk' else 'Телефон'}: {data.get('manager_phone', '')}\n"
        f"{'Номер замовлення' if lang == 'uk' else 'Номер заказа'}: {data.get('order_number', '')}"
    )
    confirm_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    confirm_kb.add(tr('confirm_btn', lang), tr('cancel_btn', lang))
    await message.answer(f"{tr('summary_title', lang)}\n\n{summary}", reply_markup=confirm_kb)
    await OrderState.confirm.set()

@dp.message_handler(lambda m: m.text in ["Підтвердити", "Подтвердить"], state=OrderState.confirm)
async def confirm_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await message.answer(tr('order_accepted', lang), reply_markup=types.ReplyKeyboardRemove())
    await state.reset_state(with_data=False)  # исправлено

@dp.message_handler(lambda m: m.text in ["Скасувати", "Отменить"], state=OrderState.confirm)
async def cancel_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uk')
    await message.answer(tr('operation_canceled', lang), reply_markup=types.ReplyKeyboardRemove())
    await state.reset_state(with_data=False)  # исправлено

# Echo fallback
@dp.message_handler(state=None)
async def echo(message: types.Message):
    await message.answer("Напишіть /start для початку нового замовлення.\nНапишите /start для начала нового заказа.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
