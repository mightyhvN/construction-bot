import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

logging.basicConfig(level=logging.INFO)

TOKEN = '7504968431:AAFeZa45QN4Y5faP0EgUfLc8BvCBXnCEmZc'  # Вставь сюда свой токен

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Товары для стройматериалов
products = {
    'Цементы и смеси': {
        'Цементы': [
            {'name': 'Цемент М500', 'price': 320, 'photo': 'https://example.com/cement_m500.jpg'},
            {'name': 'Цемент М400', 'price': 280, 'photo': 'https://example.com/cement_m400.jpg'},
        ],
        'Сухие смеси': [
            {'name': 'Штукатурка гипсовая', 'price': 260, 'photo': 'https://example.com/plaster_gypsum.jpg'},
            {'name': 'Штукатурка цементная', 'price': 240, 'photo': 'https://example.com/plaster_cement.jpg'},
        ]
    },
    'Краски и Лаки': {
        'Краски': [
            {'name': 'Краска акриловая белая', 'price': 510, 'photo': 'https://example.com/paint_acrylic_white.jpg'},
            {'name': 'Краска акриловая цветная', 'price': 550, 'photo': 'https://example.com/paint_acrylic_color.jpg'},
        ],
        'Лаки': [
            {'name': 'Лак акриловый', 'price': 370, 'photo': 'https://example.com/lacquer_acrylic.jpg'},
            {'name': 'Лак алкидный', 'price': 390, 'photo': 'https://example.com/lacquer_alkyd.jpg'},
        ]
    },
    'Инструменты и оборудование': {
        'Ручные инструменты': [
            {'name': 'Молоток строительный', 'price': 420, 'photo': 'https://example.com/hammer.jpg'},
            {'name': 'Отвёртка крестовая', 'price': 180, 'photo': 'https://example.com/screwdriver_cross.jpg'},
        ],
        'Электроинструменты': [
            {'name': 'Дрель', 'price': 3200, 'photo': 'https://example.com/drill.jpg'},
            {'name': 'Шуруповерт', 'price': 2800, 'photo': 'https://example.com/screwdriver_power.jpg'},
        ]
    }
}

user_carts = {}  # user_id -> список товаров

class OrderStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()

# Главное меню с кнопками
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Каталог"), KeyboardButton("Корзина"))
    kb.add(KeyboardButton("Акции"), KeyboardButton("Помощь"))
    return kb

# Клавиатура категорий (inline)
def category_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    for category in products.keys():
        kb.insert(InlineKeyboardButton(text=category, callback_data=f"category_{category}"))
    kb.insert(InlineKeyboardButton(text="⬅ Главное меню", callback_data="main_menu"))
    return kb

# Клавиатура подкатегорий
def subcategory_keyboard(category):
    kb = InlineKeyboardMarkup(row_width=2)
    for subcat in products[category].keys():
        kb.insert(InlineKeyboardButton(text=subcat, callback_data=f"subcategory_{category}_{subcat}"))
    kb.insert(InlineKeyboardButton(text="⬅ Назад к категориям", callback_data=f"back_to_categories"))
    kb.insert(InlineKeyboardButton(text="⬅ Главное меню", callback_data="main_menu"))
    return kb

# Клавиатура товаров с кнопками "Добавить"
def products_keyboard(category, subcategory):
    kb = InlineKeyboardMarkup(row_width=1)
    items = products[category][subcategory]
    for idx, item in enumerate(items):
        kb.insert(InlineKeyboardButton(text=f"{item['name']} — {item['price']}₽", callback_data=f"add_{category}_{subcategory}_{idx}"))
    kb.insert(InlineKeyboardButton(text="⬅ Назад к подкатегориям", callback_data=f"back_to_subcategories_{category}"))
    kb.insert(InlineKeyboardButton(text="⬅ Главное меню", callback_data="main_menu"))
    return kb

# Клавиатура корзины
def cart_keyboard(user_id):
    kb = InlineKeyboardMarkup(row_width=1)
    cart = user_carts.get(user_id, [])
    for idx, item in enumerate(cart):
        kb.insert(InlineKeyboardButton(text=f"❌ Убрать {item['name']}", callback_data=f"remove_{idx}"))
    if cart:
        kb.add(InlineKeyboardButton(text="Оформить заказ", callback_data="checkout"))
    kb.add(InlineKeyboardButton(text="⬅ Главное меню", callback_data="main_menu"))
    return kb

# Старт — показываем главное меню
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_carts[message.from_user.id] = []
    await message.answer(
        "Добро пожаловать в магазин стройматериалов!\nВыберите действие:",
        reply_markup=main_menu()
    )

# Обработка текстовых кнопок главного меню
@dp.message_handler(lambda msg: msg.text in ["Каталог", "Корзина", "Акции", "Помощь"])
async def main_menu_buttons(message: types.Message):
    user_id = message.from_user.id
    if message.text == "Каталог":
        await message.answer("Выберите категорию товаров:", reply_markup=category_keyboard())
    elif message.text == "Корзина":
        cart = user_carts.get(user_id, [])
        if not cart:
            await message.answer("Ваша корзина пуста.", reply_markup=main_menu())
            return
        text = "Ваша корзина:\n"
        total = 0
        for item in cart:
            text += f"- {item['name']} — {item['price']}₽\n"
            total += item['price']
        text += f"\nИтого: {total}₽"
        await message.answer(text, reply_markup=cart_keyboard(user_id))
    elif message.text == "Акции":
        promo_text = (
            "🔥 Акции и скидки на этой неделе:\n"
            "- Цемент М500 — скидка 10%\n"
            "- Лаки — при покупке 3 баллонов, 1 в подарок\n"
            "- Электроинструменты — бесплатная доставка при заказе от 15000₽\n"
        )
        await message.answer(promo_text, reply_markup=main_menu())
    elif message.text == "Помощь":
        help_text = (
            "🛠 Магазин стройматериалов бот:\n"
            "- Используйте меню для выбора товаров.\n"
            "- Добавляйте товары в корзину.\n"
            "- Оформляйте заказ.\n"
            "- Для старта всегда доступна команда /start."
        )
        await message.answer(help_text, reply_markup=main_menu())

# Обработка inline callback для навигации
@dp.callback_query_handler(lambda c: c.data)
async def callbacks_handler(callback: types.CallbackQuery):
    data = callback.data

    if data == "main_menu":
        await callback.message.edit_text("Вы вернулись в главное меню.", reply_markup=None)
        await callback.message.answer("Выберите действие:", reply_markup=main_menu())
        await callback.answer()

    elif data.startswith("category_"):
        category = data[len("category_"):]
        await callback.message.edit_text(f"Категория: {category}\nВыберите подкатегорию:", reply_markup=subcategory_keyboard(category))
        await callback.answer()

    elif data.startswith("subcategory_"):
        parts = data.split("_")
        category = parts[1]
        subcategory = "_".join(parts[2:])
        await callback.message.edit_text(f"Подкатегория: {subcategory}\nВыберите товар:", reply_markup=products_keyboard(category, subcategory))
        await callback.answer()

    elif data.startswith("add_"):
        parts = data.split("_")
        category = parts[1]
        subcategory = parts[2]
        idx = int(parts[3])
        user_id = callback.from_user.id
        item = products[category][subcategory][idx]
        user_carts.setdefault(user_id, []).append(item)
        await callback.answer(f"Добавлено в корзину: {item['name']}")
        await bot.send_photo(user_id, item['photo'], caption=f"{item['name']} — {item['price']}₽")

    elif data.startswith("remove_"):
        idx = int(data.split("_")[1])
        user_id = callback.from_user.id
        cart = user_carts.get(user_id, [])
        if 0 <= idx < len(cart):
            removed = cart.pop(idx)
            await callback.answer(f"Удалено из корзины: {removed['name']}")
        # Обновим корзину
        if cart:
            text = "Ваша корзина:\n"
            total = sum(item['price'] for item in cart)
            for item in cart:
                text += f"- {item['name']} — {item['price']}₽\n"
            text += f"\nИтого: {total}₽"
            await callback.message.edit_text(text, reply_markup=cart_keyboard(user_id))
        else:
            await callback.message.edit_text("Ваша корзина пуста.", reply_markup=main_menu())

    elif data == "checkout":
        user_id = callback.from_user.id
        cart = user_carts.get(user_id, [])
        if not cart:
            await callback.answer("Корзина пуста!", show_alert=True)
            return
        await bot.send_message(user_id, "Пожалуйста, введите ваше полное имя для оформления заказа:")
        await OrderStates.waiting_name.set()
        await callback.answer()

    elif data == "back_to_categories":
        await callback.message.edit_text("Выберите категорию товаров:", reply_markup=category_keyboard())
        await callback.answer()

    elif data.startswith("back_to_subcategories_"):
        category = data[len("back_to_subcategories_"):]
        await callback.message.edit_text(f"Категория: {category}\nВыберите подкатегорию:", reply_markup=subcategory_keyboard(category))
        await callback.answer()

# Обработка состояний заказа
@dp.message_handler(state=OrderStates.waiting_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите номер телефона:")
    await OrderStates.waiting_phone.set()

@dp.message_handler(state=OrderStates.waiting_phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Введите адрес доставки:")
    await OrderStates.waiting_address.set()

@dp.message_handler(state=OrderStates.waiting_address)
async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()
    user_id = message.from_user.id
    cart = user_carts.get(user_id, [])

    if not cart:
        await message.answer("Ваша корзина пуста, заказ отменён.", reply_markup=main_menu())
        await state.finish()
        return

    total = sum(item['price'] for item in cart)
    order_text = (
        f"Спасибо за заказ!\n\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}\n"
        f"Адрес: {data['address']}\n\n"
        f"Заказанные товары:\n"
    )
    for item in cart:
        order_text += f"- {item['name']} — {item['price']}₽\n"
    order_text += f"\nИтого к оплате: {total}₽"

    await message.answer(order_text, reply_markup=main_menu())
    user_carts[user_id] = []
    await state.finish()

# Ответ на неизвестные команды/сообщения
@dp.message_handler()
async def unknown_message(message: types.Message):
    await message.answer("Пожалуйста, используйте меню для навигации или введите /start для начала.", reply_markup=main_menu())

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
