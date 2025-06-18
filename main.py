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

# FSM состояния
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

# Старт и запуск FSM
@dp.message_handler(commands=['start'], state='*')
async def start_order(message: types.Message):
    await message.answer("Выберите язык (например, 'ua', 'ru'):")
    await OrderState.language.set()

@dp.message_handler(state=OrderState.language)
async def set_language(message: types.Message, state: FSMContext):
    await state.update_data(language=message.text)
    await message.answer("Введите город:")
    await OrderState.city.set()

@dp.message_handler(state=OrderState.city)
async def set_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Введите VIN:")
    await OrderState.vin.set()

@dp.message_handler(state=OrderState.vin)
async def set_vin(message: types.Message, state: FSMContext):
    await state.update_data(vin=message.text)
    await message.answer("Введите Dlink:")
    await OrderState.dlink.set()

@dp.message_handler(state=OrderState.dlink)
async def set_dlink(message: types.Message, state: FSMContext):
    await state.update_data(dlink=message.text)
    await message.answer("Введите модель:")
    await OrderState.model.set()

@dp.message_handler(state=OrderState.model)
async def set_model(message: types.Message, state: FSMContext):
    await state.update_data(model=message.text)
    await message.answer("Введите язык мультимедиа:")
    await OrderState.multimedia_lang.set()

@dp.message_handler(state=OrderState.multimedia_lang)
async def set_multimedia_lang(message: types.Message, state: FSMContext):
    await state.update_data(multimedia_lang=message.text)
    await message.answer("Введите имя менеджера:")
    await OrderState.manager_name.set()

@dp.message_handler(state=OrderState.manager_name)
async def set_manager_name(message: types.Message, state: FSMContext):
    await state.update_data(manager_name=message.text)
    await message.answer("Введите телефон менеджера:")
    await OrderState.manager_phone.set()

@dp.message_handler(state=OrderState.manager_phone)
async def set_manager_phone(message: types.Message, state: FSMContext):
    await state.update_data(manager_phone=message.text)
    await message.answer("Введите номер заказа или напишите 'Пропустити':")
    await OrderState.order_number.set()

@dp.message_handler(state=OrderState.order_number)
async def set_order_number(message: types.Message, state: FSMContext):
    if message.text != "Пропустити":
        await state.update_data(order_number=message.text)
    else:
        await state.update_data(order_number="Немає")
    data = await state.get_data()
    summary = (
        f"Мова: {data.get('language', '').upper()}\n"
        f"Місто: {data.get('city', '')}\n"
        f"VIN: {data.get('vin', '')}\n"
        f"Dlink: {data.get('dlink', '')}\n"
        f"Модель: {data.get('model', '')}\n"
        f"Мова мультимедіа: {data.get('multimedia_lang', '')}\n"
        f"Менеджер: {data.get('manager_name', '')}\n"
        f"Телефон: {data.get('manager_phone', '')}\n"
        f"Номер замовлення: {data.get('order_number', '')}"
    )
    confirm_kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("Підтвердити", "Скасувати")
    await message.answer(f"Перевірте дані:\n\n{summary}", reply_markup=confirm_kb)
    await OrderState.confirm.set()

@dp.message_handler(lambda m: m.text == "Підтвердити", state=OrderState.confirm)
async def confirm_order(message: types.Message, state: FSMContext):
    await message.answer("Замовлення прийняте! Дякую!", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

@dp.message_handler(lambda m: m.text == "Скасувати", state=OrderState.confirm)
async def cancel_order(message: types.Message, state: FSMContext):
    await message.answer("Операція скасована.", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

# Echo fallback
@dp.message_handler(state=None)
async def echo(message: types.Message):
    await message.answer(f"Echo: {message.text}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
