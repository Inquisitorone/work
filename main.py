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

# ... (INSTRUCTION, TEXTS, tr, CITIES, BRANDS, DLINKS, DLINK_MODELS, MULTIMEDIA_LANGS, display_user_language, display_multimedia_lang, get_cancel_kb, is_valid_vin - см. выше, оставь как было) ...

@dp.message_handler(commands=['start'], state='*')
async def start_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language')
    if lang:
        await message.answer("Для початку виберіть замовлення.", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(TEXTS['new_order_btn'][lang]))
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
    await message.answer(TEXTS['choose_brand'][lang], reply_markup=brands_kb)
    await OrderState.brand.set()

@dp.message_handler(lambda m: m.text in ["Нове замовлення 📝", "Новый заказ 📝"], state='*')
async def new_order_button(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get('language', 'uk')
    brands_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    brands_kb.add(*BRANDS[lang])
    await message.answer(TEXTS['choose_brand'][lang], reply_markup=brands_kb)
    await OrderState.brand.set()

@dp.message_handler(state=OrderState.brand)
async def set_brand(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get('language', 'uk')
    if message.text == "BYD":
        await state.update_data(brand="BYD")
        city_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        city_kb.add(*CITIES[lang])
        await message.answer(TEXTS['city'][lang], reply_markup=city_kb)
        await OrderState.city.set()
    else:
        # ... обработка Zeekr или др. брендов ...
        pass

@dp.message_handler(state=OrderState.city)
async def set_city(message: types.Message, state: FSMContext):
    lang = (await state.get_data()).get('language', 'uk')
    if message.text in CITIES[lang]:
        await state.update_data(city=message.text)
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(*TEXTS['service_types'][lang])
        await message.answer(TEXTS['service_type'][lang], reply_markup=kb)
        await OrderState.service_type.set()
    else:
        await state.update_data(city=message.text)
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(*TEXTS['service_types'][lang])
        await message.answer(TEXTS['service_type'][lang], reply_markup=kb)
        await OrderState.service_type.set()

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
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        await message.answer("Введіть суму вартості послуги:", reply_markup=kb)
        await OrderState.service_price.set()
    else:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(*TEXTS['service_types'][lang])
        await message.answer(TEXTS['service_type'][lang], reply_markup=kb)

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

@dp.message_handler(state=OrderState.service_payment)
async def set_service_payment(message: types.Message, state: FSMContext):
    if message.text not in ["Оплата Салон", "Оплата СТО"]:
        await message.answer("Оберіть спосіб оплати: (кнопкою)")
        return
    await state.update_data(service_payment=message.text)
    lang = (await state.get_data()).get('language', 'uk')
    await message.answer("Введіть VIN:", reply_markup=types.ReplyKeyboardRemove())
    await OrderState.vin.set()

@dp.message_handler(state=OrderState.vin)
async def set_vin(message: types.Message, state: FSMContext):
    vin = message.text.strip().upper()
    if not is_valid_vin(vin):
        await message.answer("Некоректний VIN! Має бути 17 символів.")
        return
    await state.update_data(vin=vin)
    lang = (await state.get_data()).get('language', 'uk')
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(*DLINKS[lang])
    await message.answer("Оберіть Dlink:", reply_markup=kb)
    await OrderState.dlink.set()

@dp.message_handler(state=OrderState.dlink)
async def set_dlink(message: types.Message, state: FSMContext):
    dlink_choice = message.text.split()[0]  # Dlink 3/4/5 или Инше
    await state.update_data(dlink=dlink_choice)
    # Выбор моделей по Dlink
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if dlink_choice in DLINK_MODELS:
        kb.add(*DLINK_MODELS[dlink_choice])
    await message.answer("Оберіть модель:", reply_markup=kb)
    await OrderState.model.set()

@dp.message_handler(state=OrderState.model)
async def set_model(message: types.Message, state: FSMContext):
    await state.update_data(model=message.text)
    lang = (await state.get_data()).get('language', 'uk')
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(*MULTIMEDIA_LANGS[lang])
    await message.answer("Оберіть мову мультимедіа:", reply_markup=kb)
    await OrderState.multimedia_lang.set()

@dp.message_handler(state=OrderState.multimedia_lang)
async def set_multimedia_lang(message: types.Message, state: FSMContext):
    await state.update_data(multimedia_lang=message.text)
    lang = (await state.get_data()).get('language', 'uk')
    await message.answer("Введіть ім'я менеджера:", reply_markup=types.ReplyKeyboardRemove())
    await OrderState.manager_name.set()

@dp.message_handler(state=OrderState.manager_name)
async def set_manager_name(message: types.Message, state: FSMContext):
    await state.update_data(manager_name=message.text)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("📱 Поділитися телефоном", request_contact=True))
    kb.add("Ввести вручну")
    await message.answer("Введіть телефон менеджера або поділіться контактом:", reply_markup=kb)
    await OrderState.manager_phone.set()

@dp.message_handler(state=OrderState.manager_phone, content_types=types.ContentTypes.CONTACT)
async def set_manager_phone_contact(message: types.Message, state: FSMContext):
    if message.contact and message.contact.phone_number:
        await state.update_data(manager_phone=message.contact.phone_number)
        await send_byd_summary(message, state)

@dp.message_handler(state=OrderState.manager_phone)
async def set_manager_phone_manual(message: types.Message, state: FSMContext):
    if message.text == "Ввести вручну":
        await message.answer("Введіть телефон вручну:")
        return
    await state.update_data(manager_phone=message.text)
    await send_byd_summary(message, state)

async def send_byd_summary(message, state):
    data = await state.get_data()
    lang = data.get('language', 'uk')
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
    kb.add(TEXTS['confirm_btn'][lang])
    await message.answer(f"Перевірте дані:\n\n{summary}", reply_markup=kb)
    await OrderState.confirm.set()

@dp.message_handler(lambda m: m.text in ["Підтвердити", "Подтвердить"], state=OrderState.confirm)
async def confirm_order(message: types.Message, state: FSMContext):
    await message.answer("Замовлення прийняте! Дякую! ✅", reply_markup=types.ReplyKeyboardRemove())
    data = await state.get_data()
    await send_admin_order(message.from_user, data)
    await state.finish()

async def send_admin_order(user, data):
    # ... твоя функция отправки админу (см. выше) ...
    pass

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
