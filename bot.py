import telebot
import buttons as bt
import database as db
from geopy import Photon

geolocator = Photon(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0")
bot = telebot.TeleBot(token="7302566058:AAFmTeoYn7NY1CQ-MVFtg1-jBhJya1yv21w")
users = {}

# db.add_product("Бургер", 20000, "лучший бургер", 10, "https://api.uznews.uz/storage/uploads/posts/images/47961/inner/pGx3Y69NmV.jpg")
# db.add_product("Чизбургер", 25000, "лучший чизбургер", 10, "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTBFDydbUCh47TnT--5HUJwdLaxecCV4aufVA&s")
# db.add_product("Хот-дог", 15000, "лучший хот-дог", 0, "https://cdn.nur.kz/images/1200x675/f8389f4527bd0e0c.jpeg")
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "Добро пожаловать в бот доставки!")
    checker = db.check_user(user_id)
    if checker == True:
        bot.send_message(user_id, "Главное меню: ", reply_markup=bt.main_menu_kb())
    elif checker == False:
        bot.send_message(user_id, "Введите своё имя для регистрации")
        print(message.text)
        bot.register_next_step_handler(message, get_name)
def get_name(message):
    user_id = message.from_user.id
    name = message.text
    print(message.text)
    bot.send_message(user_id, "Теперь поделитесь своим номером", reply_markup=bt.phone_buttons())
    bot.register_next_step_handler(message, get_phone_number, name)

def get_phone_number(message, name):
    user_id = message.from_user.id
    if message.contact:
        phone_number = message.contact.phone_number
        print(phone_number)
        bot.send_message(user_id, "Отправьте свою локацию", reply_markup=bt.location_buttons())
        bot.register_next_step_handler(message, get_location, name, phone_number)
    else:
        bot.send_message(user_id, "Отправьте свой номер через кнопку в меню")
        bot.register_next_step_handler(message, get_phone_number,name)


def get_location(message, name, phone_number):
    user_id = message.from_user.id
    if message.location:
        latitude = message.location.latitude
        longitude = message.location.longitude
        address = geolocator.reverse((latitude, longitude)).address
        print(name, phone_number, address)
        db.add_user(name=name, phone_number=phone_number, user_id=user_id)
        bot.send_message(user_id, "Вы успешно зарегистрировались!")
        bot.send_message(user_id, "Главное меню: ", reply_markup=bt.main_menu_kb())
    else:
        bot.send_message(user_id, "Отправьте свою локацию через кнопку")
        bot.register_next_step_handler(message, get_location, name, phone_number)
@bot.callback_query_handler(lambda call: call.data in ["cart", "back", "plus", "minus", "to_cart",
                                                       "main_menu", "order", "clear_cart"])
def all_cals(call):
    user_id = call.message.chat.id
    if call.data == "cart":
        bot.delete_message(user_id, call.message.message_id)
        cart = db.get_user_cart(user_id)
        full_text = "Ваша корзина: \n"
        count = 0
        total_price = 0
        for product in cart:
            count += 1
            full_text += f"{count}. {product[0]} * {product[1]} = {product[2]}\n"
            total_price += product[2]
        cart_for_buttons = db.get_card_id_name(user_id)
        bot.send_message(user_id, full_text+f"\n\nИтоговая сумма: {total_price} сум",
                         reply_markup=bt.get_cart_kb(cart_for_buttons))
    elif call.data == "back":
        bot.delete_message(user_id, call.message_id)
        bot.send_message(user_id, "Главное меню: ", reply_markup=bt.main_menu_kb())
    elif call.data == "plus":
        current_amount = users[user_id]["pr_count"]
        users[user_id]["pr_count"] += 1
        bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id,
                                      reply_markup=bt.plus_minus_in("plus", current_amount))
    elif call.data == "minus":
        current_amount = users[user_id]["pr_count"]
        if current_amount > 1:
            users[user_id]["pr_count"] -= 1
            bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id,
                                          reply_markup=bt.plus_minus_in("minus", current_amount))

    elif call.data == "to_cart":
        db.add_to_card(user_id, users[user_id]["pr_id"], users[user_id]["pr_name"], users[user_id]["pr_count"],
                       users[user_id]["pr_price"])
        users.pop(user_id)
        bot.delete_message(user_id, call.message.message_id)
        all_products = db.get_pr_id_name()
        bot.send_message(user_id, "Продукт успешно добавлен в корзину. \n"
                                  "Желаете выбрать что-то ещё?", reply_markup=bt.products_in(all_products))
    elif call.data == "main_menu":
        all_products = db.get_pr_id_name()
        bot.send_message(user_id, "Выберите продукт", reply_markup=bt.products_in(all_products))
    elif call.data == "order":
        bot.delete_message(user_id, call.message.message_id)
        cart = db.get_user_cart(user_id)
        full_text = f"Новый заказт от пользователя с id {user_id}: \n"
        count = 0
        total_price = 0
        for product in cart:
            count += 1
            full_text += f"{count}. {product[0]} * {product[1]} = {product[2]}\n"
            total_price += product[2]
        bot.send_message(-4778814072, full_text + f"\n\nИтоговая сумма: {total_price} сум")
        bot.send_message(user_id, "Ваш заказ принят и обрабатывается оператором", reply_markup=bt.main_menu_kb())
        db.delete_user_cart(user_id)
    elif call.data == "clear_cart":
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, "Ваша корзина очищена", reply_markup=bt.main_menu_kb())
        db.delete_user_cart(user_id)

@bot.callback_query_handler(lambda call: "prod_" in call.data)
def get_prod_info(call):
    user_id = call.message.chat.id
    bot.delete_message(user_id, call.message.message_id)
    product_id = int(call.data.replace("prod_", ""))
    product_info = db.get_exact_product(product_id)
    # Сохранить информацию о продукте и его количестве
    users[user_id] = {"pr_id": product_id, "pr_name":product_info[0], "pr_count": 1,
                      "pr_price": product_info[1]}
    bot.send_photo(user_id, photo=product_info[3], caption=f"{product_info[0]}\n\n"
                                                           f"{product_info[2]}\n"
                                                        f"Цена: {product_info[1]}",
                   reply_markup=bt.plus_minus_in())
@bot.callback_query_handler(lambda call: "delete_" in call.data)
def delete_product_from_cart(call):
    user_id = call.message.chat.id
    product_id = int(call.data.replace("delete_", ""))
    db.delete_exact_product_from_cart(user_id, product_id)

    cart = db.get_user_cart(user_id)
    full_text = "Ваша корзина: \n"
    count = 0
    total_price = 0
    for product in cart:
        count += 1
        full_text += f"{count}. {product[0]} * {product[1]} = {product[2]}\n"
        total_price += product[2]
    cart_for_buttons = db.get_card_id_name(user_id)
    bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=full_text + f"\n\nИтоговая сумма: {total_price} сум",
                     reply_markup=bt.get_cart_kb(cart_for_buttons))

@bot.message_handler(content_types=["text"])
def main_menu(message):
    user_id = message.from_user.id
    if message.text == "🍴 menu":
        all_products = db.get_pr_id_name()
        bot.send_message(user_id, "Выберите продукт: ", reply_markup=bt.products_in(all_products))
    elif message.text == "корзина":
        bot.send_message(user_id, "Ваша корзина:")
        cart = db.get_user_cart(user_id)
        full_text = "Ваша корзина: \n"
        count = 0
        total_price = 0
        for product in cart:
            count += 1
            full_text += f"{count}. {product[0]} * {product[1]} = {product[2]}\n"
            total_price += product[2]
        cart_for_buttons = db.get_card_id_name(user_id)
        bot.send_message(user_id, full_text + f"\n\nИтоговая сумма: {total_price} сум",
                         reply_markup=bt.get_cart_kb(cart_for_buttons))

    elif message.text == "✍️ отзыв":
        bot.send_message(user_id, "Напишите текст вашего отзыва: ")
        bot.register_next_step_handler(message, feed_back)

def feed_back(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    otziv_text = message.text
    bot.send_message(-4778814072, f"Новый отзыв от пользователя {user_name}, {user_id}: \n\n {otziv_text}")
    bot.send_message(user_id, "Спасибо за ваш отзыв!")

bot.infinity_polling()
