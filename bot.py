import logging
from datetime import datetime
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

import config

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
(
    MAIN_MENU,
    CHOOSE_SIZE,
    COLLECT_ORDER_INFO,
    COLLECT_BUDGET_INFO,
    COLLECT_WISHES,
    PAYMENT_CONFIRMATION
) = range(6)

# Тексты
START_GIF = "https://media.giphy.com/media/your-gif-url.gif"  # Замените на ваш GIF
SIZE_GIFS = {
    "S": "https://media.giphy.com/media/s-size.gif",
    "M": "https://media.giphy.com/media/m-size.gif",
    "L": "https://media.giphy.com/media/l-size.gif"
}

# Временное хранилище заказов (в продакшене используйте БД)
user_data_store = {}

async def send_admin_notification(context: ContextTypes.DEFAULT_TYPE, user_data: dict, action: str):
    """Отправка уведомления админу"""
    user = user_data.get('user_info', {})
    text = (
        f"🚀 НОВЫЙ ПОЛЬЗОВАТЕЛЬ\n"
        f"👤 {user.get('name', 'Не указано')}\n"
        f"🆔 ID: {user.get('id', '')}\n"
        f"📛 Username: @{user.get('username', '')}\n"
        f"🌐 Язык: {user.get('language_code', '')}\n"
        f"🕐 Время: {datetime.now().strftime('%H:%M %d.%m.%Y')}\n"
        f"📲 Действие: {action}"
    )
    
    try:
        await context.bot.send_message(
            chat_id=config.ADMIN_CHAT_ID,
            text=text
        )
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Сохраняем данные пользователя
    user_data_store[user.id] = {
        'user_info': {
            'id': user.id,
            'name': user.full_name,
            'username': user.username,
            'language_code': user.language_code
        },
        'state': 'started',
        'last_action': datetime.now()
    }
    
    # Отправляем уведомление админу
    await send_admin_notification(context, user_data_store[user.id], "Запустил бота")
    
    # Отправка GIF и основного меню
    await update.message.reply_animation(
        animation=START_GIF,
        caption=(
            "*Группа проектов monoflowers / roseazov / roserostov / dorogobogato /*\n\n"
            "🚀 *сервис номер один по доставке цветов*\n"
            "📍 расширяем географию / возможности / качество / ваш выбор\n\n"
            "✨ *ДЕЛАТЬ ШИКАРНО - НАШ ПРОФИЛЬ*\n"
            "💎 *ЗАЦЕНИ e L k i v k r a f t э*"
        ),
        parse_mode='Markdown'
    )
    
    # Клавиатура главного меню
    keyboard = [
        [KeyboardButton("Н О Б И Л И С")],
        [KeyboardButton("П И С Ь М О  П О Ж Е Л А Н И Я")],
        [KeyboardButton("С В Я З А Т Ь С Я  С Н А М И")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=reply_markup
    )
    
    return MAIN_MENU

async def handle_nobilis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ вариантов НОБИЛИС"""
    keyboard = [
        [
            InlineKeyboardButton("РАЗМЕР S - 1 000 ₽", callback_data="size_S"),
            InlineKeyboardButton("РАЗМЕР M - 2 000 ₽", callback_data="size_M"),
        ],
        [
            InlineKeyboardButton("РАЗМЕР L - 3 000 ₽", callback_data="size_L"),
            InlineKeyboardButton("НА СВОЙ БЮДЖЕТ", callback_data="custom_budget"),
        ],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем GIF (в реальном боте отправьте 3 разных GIF)
    await update.message.reply_animation(
        animation=SIZE_GIFS["S"],
        caption="🎄 *ВЫБЕРИТЕ РАЗМЕР НОБИЛИС*\n\n"
                "*S* - Компактный вариант для рабочего стола\n"
                "*M* - Идеально для праздничного стола\n"
                "*L* - Роскошный вариант для большого зала",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    return CHOOSE_SIZE

async def handle_size_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора размера"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("size_"):
        size = query.data.split("_")[1]
        price = config.PRICES[size]
        
        # Сохраняем выбор
        context.user_data['order'] = {
            'type': 'nobilis',
            'size': size,
            'price': price,
            'delivery': config.DELIVERY_COST
        }
        
        await query.edit_message_caption(
            caption=f"✅ Вы выбрали размер *{size}*\n"
                   f"💰 Цена: *{price} ₽*\n"
                   f"🚚 Доставка: *{config.DELIVERY_COST} ₽*\n"
                   f"🎯 Итого: *{price + config.DELIVERY_COST} ₽*\n\n"
                   "Пожалуйста, заполните данные для доставки:",
            parse_mode='Markdown'
        )
        
        await query.message.reply_text(
            "📝 *Введите ваши данные в формате:*\n\n"
            "Имя: *Ваше имя*\n"
            "Телефон: *+7XXX XXX XX XX*\n"
            "Адрес: *Полный адрес доставки*\n"
            "Имя получателя: *Если отличается*\n"
            "Телефон получателя: *+7XXX XXX XX XX*\n"
            "Комментарий: *Дополнительные пожелания*\n\n"
            "*Пример:*\n"
            "Имя: Анна\n"
            "Телефон: +79181112233\n"
            "Адрес: Москва, ул. Примерная, д. 1, кв. 2\n"
            "Имя получателя: Мария\n"
            "Телефон получателя: +79182223344\n"
            "Комментарий: Позвонить за час",
            parse_mode='Markdown'
        )
        
        return COLLECT_ORDER_INFO
    
    elif query.data == "custom_budget":
        await query.edit_message_caption(
            caption=f"🎯 *ЗАКАЗ НА СВОЙ БЮДЖЕТ*\n\n"
                   f"Укажите бюджет от *{config.MIN_BUDGET}* до *{config.MAX_BUDGET}* рублей\n\n"
                   "Напишите сумму цифрами:",
            parse_mode='Markdown'
        )
        return COLLECT_BUDGET_INFO
    
    elif query.data == "back_to_main":
        await main_menu(update, context)
        return MAIN_MENU

async def collect_order_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбор информации о заказе"""
    order_data = update.message.text
    user_id = update.effective_user.id
    
    # Сохраняем данные
    if 'order' not in context.user_data:
        context.user_data['order'] = {}
    
    context.user_data['order']['details'] = order_data
    
    # Уведомление админу
    await send_admin_notification(
        context, 
        user_data_store.get(user_id, {}), 
        "Заполнил данные для заказа"
    )
    
    # Показываем итог и кнопку оплаты
    order = context.user_data['order']
    total = order['price'] + order['delivery']
    
    keyboard = [[
        InlineKeyboardButton("💳 ОПЛАТИТЬ", callback_data="proceed_to_payment"),
        InlineKeyboardButton("✏️ ИЗМЕНИТЬ ДАННЫЕ", callback_data="change_data")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ *ДАННЫЕ СОХРАНЕНЫ*\n\n"
        f"📦 Товар: НОБИЛИС {order['size']}\n"
        f"💰 Товар: {order['price']} ₽\n"
        f"🚚 Доставка: {order['delivery']} ₽\n"
        f"🎯 Итого: *{total} ₽*\n\n"
        f"*Ваши данные:*\n{order_data}\n\n"
        f"Для оплаты нажмите кнопку ниже:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    
    return PAYMENT_CONFIRMATION

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка оплаты через ЮКассу"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "proceed_to_payment":
        order = context.user_data['order']
        total = order['price'] + order['delivery']
        
        # Здесь должна быть интеграция с ЮКассой
        # Пример формирования платежа
        yookassa_payment_link = generate_yookassa_payment(total, order)
        
        keyboard = [[
            InlineKeyboardButton("💳 ПЕРЕЙТИ К ОПЛАТЕ", url=yookassa_payment_link),
            InlineKeyboardButton("✅ Я ОПЛАТИЛ", callback_data="payment_done")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"💳 *ОПЛАТА ЧЕРЕЗ ЮКАССУ*\n\n"
            f"Сумма к оплате: *{total} ₽*\n\n"
            f"1. Нажмите 'ПЕРЕЙТИ К ОПЛАТЕ'\n"
            f"2. Оплатите заказ\n"
            f"3. Вернитесь в бот и нажмите 'Я ОПЛАТИЛ'\n\n"
            f"После подтверждения оплаты заказ поступит нашему флористу.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif query.data == "payment_done":
        # Отправка заказа админу
        order = context.user_data['order']
        user_info = user_data_store.get(update.effective_user.id, {}).get('user_info', {})
        
        order_text = (
            f"🎄 *НОВЫЙ ЗАКАЗ НОБИЛИС*\n\n"
            f"👤 Клиент: {user_info.get('name', '')}\n"
            f"📞 Телефон: {user_info.get('phone', '')}\n"
            f"📛 Username: @{user_info.get('username', '')}\n"
            f"🆔 ID: {user_info.get('id', '')}\n\n"
            f"📦 Размер: {order['size']}\n"
            f"💰 Сумма: {order['price']} ₽\n"
            f"🚚 Доставка: {order['delivery']} ₽\n"
            f"🎯 Итого: {order['price'] + order['delivery']} ₽\n\n"
            f"*Данные для доставки:*\n{order.get('details', '')}\n\n"
            f"⏰ {datetime.now().strftime('%H:%M %d.%m.%Y')}"
        )
        
        try:
            # Отправляем заказ в канал
            await context.bot.send_message(
                chat_id=config.ADMIN_CHAT_ID,
                text=order_text,
                parse_mode='Markdown'
            )
            
            await query.edit_message_text(
                "✅ *ЗАКАЗ ОФОРМЛЕН!*\n\n"
                "Ваш заказ передан нашему флористу. "
                "Мы свяжемся с вами для уточнения деталей.\n\n"
                "Спасибо за выбор e L k i v k r a f t э! 🎄",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Ошибка отправки заказа: {e}")
            await query.edit_message_text(
                "❌ Произошла ошибка при отправке заказа. "
                "Пожалуйста, свяжитесь с нами напрямую: @rose_azov"
            )

async def handle_wishes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка пожеланий"""
    await update.message.reply_text(
        "💌 *НАПИШИТЕ ВАШИ ПОЖЕЛАНИЯ*\n\n"
        "Мы ценим каждое мнение! Напишите все, что считаете важным: "
        "пожелания, комментарии, предложения по улучшению.\n\n"
        "Ваше сообщение будет отправлено нашей команде.",
        parse_mode='Markdown'
    )
    return COLLECT_WISHES

async def collect_wishes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбор и отправка пожеланий"""
    wishes = update.message.text
    user_id = update.effective_user.id
    user_info = user_data_store.get(user_id, {}).get('user_info', {})
    
    # Формируем сообщение для админа
    wishes_text = (
        f"💌 *НОВЫЕ ПОЖЕЛАНИЯ*\n\n"
        f"👤 От: {user_info.get('name', '')}\n"
        f"📛 @{user_info.get('username', '')}\n"
        f"🆔 ID: {user_id}\n\n"
        f"*Сообщение:*\n{wishes}\n\n"
        f"🕐 {datetime.now().strftime('%H:%M %d.%m.%Y')}"
    )
    
    try:
        await context.bot.send_message(
            chat_id=config.ADMIN_CHAT_ID,
            text=wishes_text,
            parse_mode='Markdown'
        )
        
        await update.message.reply_text(
            "✅ *СПАСИБО!*\n\n"
            "Ваше сообщение отправлено нашей команде. "
            "Мы ценим ваш вклад в развитие нашего сервиса!",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки пожеланий: {e}")
        await update.message.reply_text(
            "❌ Не удалось отправить сообщение. "
            "Попробуйте позже или свяжитесь напрямую: @rose_azov"
        )
    
    await main_menu(update, context)
    return MAIN_MENU

async def handle_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ контактов"""
    keyboard = [
        [
            InlineKeyboardButton("📱 WhatsApp", url=config.CONTACTS['whatsapp']),
            InlineKeyboardButton("✈️ Telegram", url=f"https://t.me/{config.CONTACTS['telegram'].lstrip('@')}")
        ],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📞 *СВЯЗАТЬСЯ С НАМИ*\n\n"
        "Выберите удобный способ связи:\n\n"
        "*⚠️ На данный момент мы не можем гарантировать стабильную работу связи.*\n"
        "*Если у вас не отправляется сообщение, просьба воспользоваться иным источником связи.*\n"
        "*Мы гарантируем выполнение всех оформленных заказов.*",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат в главное меню"""
    keyboard = [
        [KeyboardButton("Н О Б И Л И С")],
        [KeyboardButton("П И С Ь М О  П О Ж Е Л А Н И Я")],
        [KeyboardButton("С В Я З А Т Ь С Я  С Н А М И")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            "Главное меню:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=reply_markup
        )
    
    return MAIN_MENU

async def check_inactive_users(context: ContextTypes.DEFAULT_TYPE):
    """Проверка неактивных пользователей (запускается по расписанию)"""
    now = datetime.now()
    
    for user_id, data in user_data_store.items():
        if 'last_action' in data and 'order_completed' not in data:
            last_action = data['last_action']
            if isinstance(last_action, datetime):
                time_diff = (now - last_action).total_seconds() / 60  # в минутах
                
                # Если прошло более 30 минут и нет завершенного заказа
                if time_diff > 30:
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=(
                                "👋 *Мы заметили, что вы не завершили заказ.*\n\n"
                                "Хотите, чтобы наш флорист связался с вами и помог "
                                "подобрать идеальный вариант?\n\n"
                                "Просто ответьте 'Да' или свяжитесь с нами: @rose_azov"
                            ),
                            parse_mode='Markdown'
                        )
                        # Обновляем время последнего действия
                        data['last_action'] = now
                    except Exception as e:
                        logger.error(f"Ошибка отправки напоминания: {e}")

def generate_yookassa_payment(amount, order):
    """
    Генерация ссылки на оплату ЮКассы
    ВАЖНО: Нужна реальная интеграция с API ЮКассы
    """
    # Заглушка - замените на реальную интеграцию
    # Документация: https://yookassa.ru/developers/api
    shop_id = "YOUR_SHOP_ID"
    secret_key = "YOUR_SECRET_KEY"
    
    # Пример структуры (реализуйте по документации ЮКассы)
    payment_data = {
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/your_bot"
        },
        "description": f"Заказ НОБИЛИС {order['size']}",
        "metadata": {
            "order_id": f"{order.get('size')}_{datetime.now().timestamp()}"
        }
    }
    
    # Здесь должен быть запрос к API ЮКассы
    # response = requests.post(...)
    # return response.json()['confirmation']['confirmation_url']
    
    return "https://yookassa.ru/integration/your_payment_link"

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token(config.TOKEN).build()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Text("Н О Б И Л И С"), handle_nobilis),
                MessageHandler(filters.Text("П И С Ь М О  П О Ж Е Л А Н И Я"), handle_wishes),
                MessageHandler(filters.Text("С В Я З А Т Ь С Я  С Н А М И"), handle_contacts),
            ],
            CHOOSE_SIZE: [
                CallbackQueryHandler(handle_size_selection)
            ],
            COLLECT_ORDER_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_order_info)
            ],
            COLLECT_BUDGET_INFO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_order_info)
            ],
            COLLECT_WISHES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_wishes)
            ],
            PAYMENT_CONFIRMATION: [
                CallbackQueryHandler(handle_payment)
            ]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    # Добавляем обработчики
    application.add_handler(conv_handler)
    
    # Добавляем обработчик для кнопки "Назад"
    application.add_handler(CallbackQueryHandler(main_menu, pattern="^back_to_main$"))
    
    # Настройка job queue для проверки неактивных пользователей
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(check_inactive_users, interval=1800, first=10)  # Каждые 30 минут
    
    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
