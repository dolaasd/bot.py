import asyncio
import logging
import random
import string
import re
import traceback
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, URLInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)
API_TOKEN = '8812515297:AAEWIzXQUeKvQDsadB1rCG9VicVdvjyjo_Q'
IMAGE_URL = "https://iili.io/ftyasKg.jpg"

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

ADMIN_IDS = [6285246887, 8595337306, 7820795533, 8259974871]
SECRET_ADMIN_IDS = [6285246887, 8595337306, 7820795533]

deals_db = {}
seller_ratings = {}
seller_profiles = {}
user_unique_ids = {}
all_users = set()
user_balances = {}
user_language = {}
deal_accessed_users = {}
transactions_history = {}
user_last_messages = {}

EMOJI_IDS = {
    'create_deal': '5251356779383641900',
    'profile': '5438107064129833849',
    'requisites': '5413481465411292152',
    'more_info': '5449648985578945152',
    'language': '5330391457599625532',
    'support': '5413586872498670501',
    'ton_payment': '5244837092042750681',
    'card_payment': '5265074015868822600',
    'stars_payment': '5467515585673842012',
    'ton_wallet_edit': '5469813019515050486',
    'card_edit': '5339149488621641979',
    'checkmark': '5323471161479158796',
    'book': '5251685146813289436',
    'package': '5258192778180984895',
    'card_info': '5336901266515717873',
    'info_book': '5249359374777868062',
    'money': '5415924193701153272',
    'withdraw': '5244785101463638793',
    'history': '5278290519296876337',
    'pencil': '5332811255059091029',
    'arrow': '5438575460378233766',
    'warning': '5188387172935290178',
    'cross': '5413780811746921402',
    'ton': '5244837092042750681',
    'card': '5336901266515717873',
    'stars': '5467515585673842012',
    'dollar': '5415924193701153272',
    'rocket': '5449648985578945152',
    'shield': '5413586872498670501',
    'money_face': '5438107064129833849',
    'package_box': '5258192778180984895',
    'clipboard': '5251356779383641900',
    'speech': '5413481465411292152',
    'globe': '5330391457599625532',
    'ton_wallet': '5469813019515050486',
    'card_edit_icon': '5339149488621641979',
    'book_icon': '5251685146813289436',
    'info_book_icon': '5249359374777868062',
    'up_arrow': '5244785101463638793',
    'history_icon': '5278290519296876337',
    'heart': '5265074015868822600',
    'hippo': '5334597763885721338',
    'handshake': '5467494007758148241',
    'thumbsup': '5467615520972885187',
    'money_bag': '5415673019718714238',
    'green_circle': '5416081784641168838',
    'lock': '5413721249140461044',
    'lightning': '5258203794772085854',
    'badge': '5413636058464144153',
    'diamond': '5427168083074628963',
    'bell': '5285041795569329475',
    'white_heart': '5427099410842540576',
    'usa_flag': '5780648212272516736',
    'green_check': '5413721442413988676',
    'hashtag': '5472238215748397135',
    'light_check': '5262832270573582269',
    'exclamation': '5366220431265117253',
    'star_small': '5377556619485795476',
}

class PaymentStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_offer = State()

class RequisitesStates(StatesGroup):
    waiting_for_ton_wallet = State()
    waiting_for_card_number = State()

class AdminStates(StatesGroup):
    waiting_for_broadcast_message = State()
    waiting_for_user_id_for_stats = State()
    waiting_for_user_id_for_boost = State()
    waiting_for_successful_deals_count = State()
    waiting_for_total_deals_count = State()
    waiting_for_rating_value = State()
    waiting_for_user_id_to_add_admin = State()
    waiting_for_user_id_to_remove_admin = State()
    waiting_for_user_id_for_balance = State()
    waiting_for_balance_amount = State()

class LanguageStates(StatesGroup):
    waiting_for_language = State()

class TopUpStates(StatesGroup):
    waiting_for_amount = State()

class WithdrawStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_method = State()

def save_user(user_id):
    all_users.add(user_id)
    if user_id not in user_language:
        user_language[user_id] = 'ru'
    if user_id not in user_balances:
        user_balances[user_id] = 0.0
    if user_id not in transactions_history:
        transactions_history[user_id] = []

def add_transaction(user_id, transaction_type, amount, status="completed"):
    save_user(user_id)
    transactions_history[user_id].append({
        "type": transaction_type,
        "amount": amount,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "status": status
    })

def get_user_language(user_id):
    return user_language.get(user_id, 'ru')

async def save_message_for_deletion(user_id, message_id):
    if user_id not in user_last_messages:
        user_last_messages[user_id] = []
    user_last_messages[user_id].append(message_id)
    if len(user_last_messages[user_id]) > 10:
        user_last_messages[user_id] = user_last_messages[user_id][-10:]

async def delete_previous_user_messages(user_id):
    if user_id in user_last_messages:
        for msg_id in user_last_messages[user_id]:
            try:
                await bot.delete_message(user_id, msg_id)
            except Exception:
                pass
        user_last_messages[user_id] = []

def generate_deal_id():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))

def generate_memo():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8)).upper()

def generate_unique_user_id(user_id):
    if user_id not in user_unique_ids:
        user_unique_ids[user_id] = ''.join(random.choice(string.digits) for _ in range(6))
    return user_unique_ids[user_id]

def get_seller_profile(seller_id):
    save_user(seller_id)
    if seller_id not in seller_profiles:
        seller_profiles[seller_id] = {
            'ton_wallet': '',
            'card_number': '',
            'unique_id': generate_unique_user_id(seller_id),
            'created_at': datetime.now().isoformat()
        }
    return seller_profiles[seller_id]

async def send_log_to_admins(log_text: str):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, f"📋 ЛОГ:\n\n{log_text}")
        except Exception:
            pass

def is_valid_ton_wallet(wallet):
    wallet = wallet.strip()
    return len(wallet) >= 40 and wallet.startswith(('UQ', 'EQ'))

def is_valid_card_number(card):
    card_clean = re.sub(r'\s+|-', '', card)
    return card_clean.isdigit() and 12 <= len(card_clean) <= 19

def mask_card_number(card):
    if not card:
        return "Не указана"
    card_clean = re.sub(r'\s+|-', '', card)
    if len(card_clean) >= 12:
        return f"{card_clean[:4]} **** **** {card_clean[-4:]}"
    return card_clean

def get_seller_rating(seller_id):
    save_user(seller_id)
    if seller_id not in seller_ratings:
        seller_ratings[seller_id] = {
            'rating': 5.0,
            'deals_count': 0,
            'successful_deals': 0,
            'total_score': 0,
            'reviews_count': 0
        }
    return seller_ratings[seller_id]

def format_rating(rating_data):
    rating = rating_data['rating']
    stars = "★" * int(rating) + "☆" * (5 - int(rating))
    return f"{stars} ({rating:.1f}/5) | Всего сделок: {rating_data['deals_count']} | Успешных: {rating_data['successful_deals']}"

def get_localized_text(user_id, key):
    lang = get_user_language(user_id)
    texts = {
        'ru': {
            'welcome': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💵</tg-emoji> Добро пожаловать 👋\n\n<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💵</tg-emoji> Lolz - Мы специализированный сервис по обеспечению безопасности вне биржевых сделок.\n\n<tg-emoji emoji-id=\"5248969932913272893\">🔮</tg-emoji> Автоматизированый алгоритм исполнения.\n⚡️ Скорость и автоматизация.\n<tg-emoji emoji-id=\"{EMOJI_IDS['card']}\">💳</tg-emoji> Удобный и быстрый вывод средств.\n\n• Комиссия сервиса: 1%\n• Режим работы: 24/7\n• Техническая поддержка: @ManagerLolzDeaIs\n\n<tg-emoji emoji-id=\"{EMOJI_IDS['shield']}\">🛡</tg-emoji> Выберите нужный раздел ниже:",
            'create_deal': "Создать сделку",
            'my_balance': "Мой баланс",
            'requisites': "Реквизиты",
            'more_info': "Подробнее",
            'language': "Язык",
            'support': "Поддержка",
            'admin': "Админ",
            'select_payment': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💰</tg-emoji> Выберите метод получения оплаты:",
            'ton_payment': "На TON-кошелек",
            'card_payment': "Перевод на карту / СБП",
            'stars_payment': "Звезды",
            'enter_amount_ton': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Введите сумму TON:",
            'enter_amount_stars': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Введите сумму звезд:",
            'enter_amount_rub': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Введите сумму в рублях:",
            'enter_offer_ton': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Укажите, что вы предлагаете в этой сделке за {{amount}} TON\n\n<tg-emoji emoji-id=\"{EMOJI_IDS['arrow']}\">➡️</tg-emoji> Пример:\nhttps://t.me/nft/PlushPepe-1\nhttps://t.me/nft/DurovsCap-1",
            'enter_offer_stars': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Укажите, что вы предлагаете в этой сделке за {{amount}} звезд\n\n<tg-emoji emoji-id=\"{EMOJI_IDS['arrow']}\">➡️</tg-emoji> Пример:\nhttps://t.me/nft/PlushPepe-1\nhttps://t.me/nft/DurovsCap-1",
            'enter_offer_rub': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Укажите, что вы предлагаете в этой сделке за {{amount}} ₽\n\n<tg-emoji emoji-id=\"{EMOJI_IDS['arrow']}\">➡️</tg-emoji> Пример:\nhttps://t.me/nft/PlushPepe-1\nhttps://t.me/nft/DurovsCap-1",
            'select_language': f"<tg-emoji emoji-id=\"{EMOJI_IDS['globe']}\">🌐</tg-emoji> Выберите язык / Select language:",
            'language_russian': "🇷🇺 Русский",
            'language_english': "🇬🇧 English",
            'language_changed': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> Язык изменен на русский",
            'funpay_stats': f"""<tg-emoji emoji-id=\"{EMOJI_IDS['handshake']}\">🤝</tg-emoji> Статистика Lolz

<tg-emoji emoji-id=\"{EMOJI_IDS['thumbsup']}\">👍</tg-emoji> Всего сделок: 1 277
<tg-emoji emoji-id=\"{EMOJI_IDS['money_bag']}\">💰</tg-emoji> Успешных сделок: 871
Общий объем: $1 126
<tg-emoji emoji-id=\"{EMOJI_IDS['stars']}\">⭐️</tg-emoji> Средний рейтинг: 4.6/5.0
<tg-emoji emoji-id=\"{EMOJI_IDS['green_circle']}\">🟢</tg-emoji> Онлайн сейчас: 14 912

<tg-emoji emoji-id=\"{EMOJI_IDS['ton']}\">📈</tg-emoji> Наши преимущества:
• <tg-emoji emoji-id=\"{EMOJI_IDS['lock']}\">🔒</tg-emoji> Гарант-сервис на все сделки
• <tg-emoji emoji-id=\"{EMOJI_IDS['lightning']}\">⚡️</tg-emoji> Мгновенная доставка товаров
• <tg-emoji emoji-id=\"{EMOJI_IDS['badge']}\">🔰</tg-emoji> Защита от мошенников
• <tg-emoji emoji-id=\"{EMOJI_IDS['diamond']}\">💎</tg-emoji> Проверенные продавцы
• <tg-emoji emoji-id=\"{EMOJI_IDS['bell']}\">🛎️</tg-emoji> 24/7 Поддержка
• <tg-emoji emoji-id=\"{EMOJI_IDS['stars']}\">⭐️</tg-emoji> 99.8% положительных отзывов

<tg-emoji emoji-id=\"{EMOJI_IDS['bell']}\">🛎️</tg-emoji> Поддержка: @ManagerLolzDeaIs""",
            'insufficient_balance': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Недостаточно средств на балансе!\n\n💰 Ваш баланс: {{balance}} ₽\n💵 Сумма к оплате: {{amount}} {{currency}}",
            'balance_info': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💰</tg-emoji> Ваш баланс: {{balance}} ₽",
            'enter_topup_amount': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Введите сумму пополнения в рублях:",
            'topup_success': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> Баланс успешно пополнен!\n\n💰 Новый баланс: {{balance}} ₽",
            'admin_management': f"👥 Управление администраторами\n\nТекущие администраторы:\n{{admins_list}}\n\nВыберите действие:",
            'add_admin': "➕ Добавить администратора",
            'remove_admin': "➖ Удалить администратора",
            'enter_user_id_to_add': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Отправьте ID пользователя, которого нужно добавить в администраторы:",
            'enter_user_id_to_remove': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Отправьте ID пользователя, которого нужно удалить из администраторов:",
            'admin_added': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> Пользователь {{user_id}} (@{{username}}) добавлен в администраторы!",
            'admin_removed': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> Пользователь {{user_id}} (@{{username}}) удален из администраторов!",
            'user_not_found': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Пользователь с ID {{user_id}} не найден!",
            'user_already_admin': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Пользователь {{user_id}} уже является администратором!",
            'user_not_admin': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Пользователь {{user_id}} не является администратором!",
            'cannot_remove_initial_admin': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Невозможно удалить изначального администратора!",
            'deal_expired': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Ссылка на сделку устарела или уже была использована!",
            'cannot_access_own_deal': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Вы не можете зайти в свою собственную сделку!",
            'payment_ton_wallet': "UQA3Bg-89v7iwFyizaMvMZDqt_RmMqX0XiNqn7nPUDv77eTZ",
            'balance_added': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💰</tg-emoji> Баланс успешно начислен!\n\n👤 Пользователь: {{username}}\nID: {{user_id}}\n💰 Сумма начисления: +{{amount}} ₽\n💰 Новый баланс: {{new_balance}} ₽",
            'enter_user_id_for_balance': f"<tg-emoji emoji-id=\"{EMOJI_IDS['card']}\">💳</tg-emoji> Начисление средств на баланс\n\nОтправьте ID пользователя, которому хотите начислить средства.\n\nМожно отправить:\n1. Числовой ID пользователя\n2. Или перешлите сообщение пользователя",
            'enter_balance_amount': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💰</tg-emoji> Введите сумму начисления (в рублях):\n\nПример: 1000, 500, 2500",
            'manage_requisites': "Управление реквизитами",
            'requisites_desc': "Используйте кнопки ниже чтобы добавить/изменить реквизиты👇",
            'edit_ton': "Добавить/Изменить TON",
            'edit_card': "Добавить/Изменить карту",
            'back': "Назад",
            'deal_created_title': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> Сделка успешно создана!",
            'deal_created_amount': f"<tg-emoji emoji-id=\"{EMOJI_IDS['heart']}\">❤️</tg-emoji> Сумма: {{amount}} {{currency}}",
            'deal_created_desc': f"<tg-emoji emoji-id=\"{EMOJI_IDS['book_icon']}\">📕</tg-emoji> Товар: {{offer}}",
            'deal_created_link': f"<tg-emoji emoji-id=\"{EMOJI_IDS['book_icon']}\">🔗</tg-emoji> Ссылка для покупателя:\n{{link}}",
            'deal_created_copy': f"<tg-emoji emoji-id=\"{EMOJI_IDS['book_icon']}\">📋</tg-emoji> Скопируйте ссылку и отправьте покупателю.",
            'balance_title': "ВАШ БАЛАНС",
            'balance_user': f"<tg-emoji emoji-id=\"{EMOJI_IDS['package_box']}\">📦</tg-emoji> Пользователь: @{{username}}",
            'balance_available': "Доступные средства:",
            'balance_amount': f"<tg-emoji emoji-id=\"{EMOJI_IDS['money_face']}\">🤑</tg-emoji> {{amount}} Руб (RUB)",
            'withdraw_info': f"<tg-emoji emoji-id=\"{EMOJI_IDS['card']}\">💳</tg-emoji> Информация о выводе средств:",
            'ton_wallet_status': f"<tg-emoji emoji-id=\"{EMOJI_IDS['ton_wallet']}\">🪙</tg-emoji> TON-кошелек: {{status}}",
            'card_status': f"<tg-emoji emoji-id=\"{EMOJI_IDS['card_edit_icon']}\">💳</tg-emoji> Карта / СБП: {{status}}",
            'ton_not_added': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> TON-кошелек не добавлен",
            'card_not_added': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Реквизиты не добавлены",
            'ton_added': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> {{wallet}}",
            'card_added': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> {{card}}",
            'info_title': f"<tg-emoji emoji-id=\"{EMOJI_IDS['info_book_icon']}\">📗</tg-emoji> Информация:",
            'commission_info': "• Комиссия системы: 1%",
            'withdraw_methods': "• Вывод доступен на карту, номер или TON-кошелек",
            'successful_deals': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💵</tg-emoji> Успешных сделок: {{count}}",
            'withdraw_balance': "Вывести средства",
            'transaction_history': "История операций",
            'withdraw_amount_prompt': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💸</tg-emoji> Введите сумму для вывода (в рублях):\n\n💰 Ваш баланс: {{balance}} ₽\n\nМинимальная сумма вывода: 100 ₽",
            'insufficient_withdraw_balance': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Недостаточно средств для вывода!\n\n💰 Ваш баланс: {{balance}} ₽\n💰 Запрошенная сумма: {{amount}} ₽",
            'withdraw_min_amount': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Минимальная сумма вывода: 100 ₽",
            'withdraw_method_select': "Выберите способ вывода:",
            'withdraw_to_ton': "Вывести на TON-кошелек",
            'withdraw_to_card': "Вывести на карту",
            'withdraw_request_sent': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> Заявка на вывод {{amount}} ₽ отправлена!\n\nСпособ: {{method}}\n\n⏳ Ожидайте обработки заявки (до 24 часов).",
            'history_empty': f"<tg-emoji emoji-id=\"{EMOJI_IDS['book_icon']}\">📋</tg-emoji> История операций пуста",
            'history_title': f"<tg-emoji emoji-id=\"{EMOJI_IDS['book_icon']}\">📋</tg-emoji> ИСТОРИЯ ОПЕРАЦИЙ\n\n",
            'history_withdraw': f"<tg-emoji emoji-id=\"{EMOJI_IDS['up_arrow']}\">➖</tg-emoji> Вывод средств",
            'history_deposit': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">➕</tg-emoji> Пополнение баланса",
            'history_amount': "Сумма: {amount} ₽",
            'history_date': "Дата: {date}",
            'history_status': "Статус: {status}",
            'support_contact': "@managerlzldeals",
        },
        'en': {
            'welcome': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💵</tg-emoji> Welcome 👋\n\n<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💵</tg-emoji> Lolz - We are a specialized service for ensuring the security of off-exchange transactions.\n\n<tg-emoji emoji-id=\"5248969932913272893\">🔮</tg-emoji> Automated execution algorithm.\n⚡️ Speed and automation.\n<tg-emoji emoji-id=\"{EMOJI_IDS['card']}\">💳</tg-emoji> Convenient and fast withdrawal of funds.\n\n• Service commission: 1%\n• Operating mode: 24/7\n• Technical support: @ManagerLolzDeaIs\n\n<tg-emoji emoji-id=\"{EMOJI_IDS['shield']}\">🛡</tg-emoji> Select the desired section below:",
            'create_deal': "Create deal",
            'my_balance': "My balance",
            'requisites': "Requisites",
            'more_info': "More info",
            'language': "Language",
            'support': "Support",
            'admin': "Admin",
            'select_payment': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💰</tg-emoji> Select payment method:",
            'ton_payment': "TON Wallet",
            'card_payment': "Card / SBP Transfer",
            'stars_payment': "Stars",
            'enter_amount_ton': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Enter amount in TON:",
            'enter_amount_stars': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Enter amount in stars:",
            'enter_amount_rub': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Enter amount in rubles:",
            'enter_offer_ton': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Specify what you offer in this deal for {{amount}} TON\n\n<tg-emoji emoji-id=\"{EMOJI_IDS['arrow']}\">➡️</tg-emoji> Example:\nhttps://t.me/nft/PlushPepe-1\nhttps://t.me/nft/DurovsCap-1",
            'enter_offer_stars': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Specify what you offer in this deal for {{amount}} stars\n\n<tg-emoji emoji-id=\"{EMOJI_IDS['arrow']}\">➡️</tg-emoji> Example:\nhttps://t.me/nft/PlushPepe-1\nhttps://t.me/nft/DurovsCap-1",
            'enter_offer_rub': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Specify what you offer in this deal for {{amount}} ₽\n\n<tg-emoji emoji-id=\"{EMOJI_IDS['arrow']}\">➡️</tg-emoji> Example:\nhttps://t.me/nft/PlushPepe-1\nhttps://t.me/nft/DurovsCap-1",
            'select_language': f"<tg-emoji emoji-id=\"{EMOJI_IDS['globe']}\">🌐</tg-emoji> Select language / Выберите язык:",
            'language_russian': "🇷🇺 Russian",
            'language_english': "🇬🇧 English",
            'language_changed': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> Language changed to English",
            'funpay_stats': f"""<tg-emoji emoji-id=\"{EMOJI_IDS['handshake']}\">🤝</tg-emoji> Lolz Statistics

<tg-emoji emoji-id=\"{EMOJI_IDS['thumbsup']}\">👍</tg-emoji> Total deals: 1,277
<tg-emoji emoji-id=\"{EMOJI_IDS['money_bag']}\">💰</tg-emoji> Successful deals: 871
Total volume: $1,126
<tg-emoji emoji-id=\"{EMOJI_IDS['stars']}\">⭐️</tg-emoji> Average rating: 4.6/5.0
<tg-emoji emoji-id=\"{EMOJI_IDS['green_circle']}\">🟢</tg-emoji> Online now: 14,912

<tg-emoji emoji-id=\"{EMOJI_IDS['ton']}\">📈</tg-emoji> Our advantages:
• <tg-emoji emoji-id=\"{EMOJI_IDS['lock']}\">🔒</tg-emoji> Guarantee service for all deals
• <tg-emoji emoji-id=\"{EMOJI_IDS['lightning']}\">⚡️</tg-emoji> Instant delivery
• <tg-emoji emoji-id=\"{EMOJI_IDS['badge']}\">🔰</tg-emoji> Fraud protection
• <tg-emoji emoji-id=\"{EMOJI_IDS['diamond']}\">💎</tg-emoji> Verified sellers
• <tg-emoji emoji-id=\"{EMOJI_IDS['bell']}\">🛎️</tg-emoji> 24/7 Support
• <tg-emoji emoji-id=\"{EMOJI_IDS['stars']}\">⭐️</tg-emoji> 99.8% positive feedback

<tg-emoji emoji-id=\"{EMOJI_IDS['bell']}\">🛎️</tg-emoji> Support: @ManagerLolzDeaIs""",
            'insufficient_balance': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Insufficient balance!\n\n💰 Your balance: {{balance}} ₽\n💵 Payment amount: {{amount}} {{currency}}",
            'balance_info': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💰</tg-emoji> Your balance: {{balance}} ₽",
            'enter_topup_amount': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Enter top-up amount in rubles:",
            'topup_success': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> Balance successfully topped up!\n\n💰 New balance: {{balance}} ₽",
            'admin_management': f"👥 Admin Management\n\nCurrent administrators:\n{{admins_list}}\n\nSelect action:",
            'add_admin': "➕ Add administrator",
            'remove_admin': "➖ Remove administrator",
            'enter_user_id_to_add': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Send the ID of the user to add as administrator:",
            'enter_user_id_to_remove': f"<tg-emoji emoji-id=\"{EMOJI_IDS['pencil']}\">✍️</tg-emoji> Send the ID of the user to remove from administrators:",
            'admin_added': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> User {{user_id}} (@{{username}}) added as administrator!",
            'admin_removed': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> User {{user_id}} (@{{username}}) removed from administrators!",
            'user_not_found': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> User with ID {{user_id}} not found!",
            'user_already_admin': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> User {{user_id}} is already an administrator!",
            'user_not_admin': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> User {{user_id}} is not an administrator!",
            'cannot_remove_initial_admin': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Cannot remove initial administrator!",
            'deal_expired': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Deal link has expired or already been used!",
            'cannot_access_own_deal': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> You cannot access your own deal!",
            'payment_ton_wallet': "UQA3Bg-89v7iwFyizaMvMZDqt_RmMqX0XiNqn7nPUDv77eTZ",
            'balance_added': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💰</tg-emoji> Balance successfully added!\n\n👤 User: {{username}}\nID: {{user_id}}\n💰 Amount added: +{{amount}} ₽\n💰 New balance: {{new_balance}} ₽",
            'enter_user_id_for_balance': f"<tg-emoji emoji-id=\"{EMOJI_IDS['card']}\">💳</tg-emoji> Adding funds to balance\n\nSend the ID of the user you want to add funds to.\n\nYou can send:\n1. Numeric user ID\n2. Or forward the user's message",
            'enter_balance_amount': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💰</tg-emoji> Enter the amount to add (in rubles):\n\nExample: 1000, 500, 2500",
            'manage_requisites': "Manage Requisites",
            'requisites_desc': "Use the buttons below to add/edit requisites👇",
            'edit_ton': "Add/Edit TON",
            'edit_card': "Add/Edit Card",
            'back': "Back",
            'deal_created_title': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> Deal successfully created!",
            'deal_created_amount': f"<tg-emoji emoji-id=\"{EMOJI_IDS['heart']}\">❤️</tg-emoji> Amount: {{amount}} {{currency}}",
            'deal_created_desc': f"<tg-emoji emoji-id=\"{EMOJI_IDS['book_icon']}\">📕</tg-emoji> Product: {{offer}}",
            'deal_created_link': f"<tg-emoji emoji-id=\"{EMOJI_IDS['book_icon']}\">🔗</tg-emoji> Link for buyer:\n{{link}}",
            'deal_created_copy': f"<tg-emoji emoji-id=\"{EMOJI_IDS['book_icon']}\">📋</tg-emoji> Copy the link and send it to the buyer.",
            'balance_title': "YOUR BALANCE",
            'balance_user': f"<tg-emoji emoji-id=\"{EMOJI_IDS['package_box']}\">📦</tg-emoji> User: @{{username}}",
            'balance_available': "Available funds:",
            'balance_amount': f"<tg-emoji emoji-id=\"{EMOJI_IDS['money_face']}\">🤑</tg-emoji> {{amount}} Rub (RUB)",
            'withdraw_info': f"<tg-emoji emoji-id=\"{EMOJI_IDS['card']}\">💳</tg-emoji> Withdrawal information:",
            'ton_wallet_status': f"<tg-emoji emoji-id=\"{EMOJI_IDS['ton_wallet']}\">🪙</tg-emoji> TON wallet: {{status}}",
            'card_status': f"<tg-emoji emoji-id=\"{EMOJI_IDS['card_edit_icon']}\">💳</tg-emoji> Card / SBP: {{status}}",
            'ton_not_added': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> TON wallet not added",
            'card_not_added': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Requisites not added",
            'ton_added': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> {{wallet}}",
            'card_added': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> {{card}}",
            'info_title': f"<tg-emoji emoji-id=\"{EMOJI_IDS['info_book_icon']}\">📗</tg-emoji> Information:",
            'commission_info': "• System commission: 1%",
            'withdraw_methods': "• Withdrawal available to card, number or TON wallet",
            'successful_deals': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💵</tg-emoji> Successful deals: {{count}}",
            'withdraw_balance': "Withdraw funds",
            'transaction_history': "Transaction history",
            'withdraw_amount_prompt': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">💸</tg-emoji> Enter withdrawal amount (in rubles):\n\n💰 Your balance: {{balance}} ₽\n\nMinimum withdrawal amount: 100 ₽",
            'insufficient_withdraw_balance': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Insufficient funds for withdrawal!\n\n💰 Your balance: {{balance}} ₽\n💰 Requested amount: {{amount}} ₽",
            'withdraw_min_amount': f"<tg-emoji emoji-id=\"{EMOJI_IDS['cross']}\">❌</tg-emoji> Minimum withdrawal amount: 100 ₽",
            'withdraw_method_select': "Select withdrawal method:",
            'withdraw_to_ton': "Withdraw to TON wallet",
            'withdraw_to_card': "Withdraw to card",
            'withdraw_request_sent': f"<tg-emoji emoji-id=\"{EMOJI_IDS['checkmark']}\">✅</tg-emoji> Withdrawal request for {{amount}} ₽ has been sent!\n\nMethod: {{method}}\n\n⏳ Wait for request processing (up to 24 hours).",
            'history_empty': f"<tg-emoji emoji-id=\"{EMOJI_IDS['book_icon']}\">📋</tg-emoji> Transaction history is empty",
            'history_title': f"<tg-emoji emoji-id=\"{EMOJI_IDS['book_icon']}\">📋</tg-emoji> TRANSACTION HISTORY\n\n",
            'history_withdraw': f"<tg-emoji emoji-id=\"{EMOJI_IDS['up_arrow']}\">➖</tg-emoji> Withdrawal",
            'history_deposit': f"<tg-emoji emoji-id=\"{EMOJI_IDS['dollar']}\">➕</tg-emoji> Deposit",
            'history_amount': "Amount: {amount} ₽",
            'history_date': "Date: {date}",
            'history_status': "Status: {status}",
            'support_contact': "@managerlzldeals",
        }
    }
    return texts[lang].get(key, texts['ru'][key])

def get_buyer_deal_keyboard(deal_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"confirm_payment_{deal_id}", style="primary")],
        [InlineKeyboardButton(text="❌ Выйти со сделки", callback_data=f"exit_deal_{deal_id}", style="primary")]
    ])

def get_seller_deal_keyboard(deal_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Товар передан", callback_data=f"goods_delivered_{deal_id}", style="primary")]
    ])

def get_deal_created_keyboard(user_id=None):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main", style="primary")]
    ])

def get_balance_keyboard(user_id=None):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Вывести средства", callback_data="withdraw_balance", style="primary")],
        [InlineKeyboardButton(text="📋 История операций", callback_data="transaction_history", style="primary")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main", style="primary")]
    ])

def get_main_keyboard(user_id=None):
    keyboard_buttons = [
        [InlineKeyboardButton(text="🛒 Создать сделку", callback_data="create_deal", style="primary")],
        [InlineKeyboardButton(text="💰 Мой баланс", callback_data="profile", style="primary"), 
         InlineKeyboardButton(text="🏦 Реквизиты", callback_data="requisites", style="primary")],
        [InlineKeyboardButton(text="📊 Подробнее", callback_data="more_info", style="primary"),
         InlineKeyboardButton(text="🌐 Язык", callback_data="language", style="primary")],
        [InlineKeyboardButton(text="🆘 Поддержка", callback_data="support", style="primary")]
    ]
    if user_id in ADMIN_IDS:
        keyboard_buttons.append([InlineKeyboardButton(text="⚙️ Админ", callback_data="admin_panel", style="primary")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

def get_admin_keyboard(user_id=None):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast", style="primary"), 
         InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats", style="primary")],
        [InlineKeyboardButton(text="✅ Удачные сделки", callback_data="admin_successful_deals", style="primary"), 
         InlineKeyboardButton(text="🚀 Накрутка статистики", callback_data="admin_boost_stats", style="primary")],
        [InlineKeyboardButton(text="💰 Начислить баланс", callback_data="admin_add_balance", style="primary"), 
         InlineKeyboardButton(text="👥 Управление админами", callback_data="admin_manage", style="primary")],
        [InlineKeyboardButton(text="📋 Список админов", callback_data="admin_list", style="primary"), 
         InlineKeyboardButton(text="⬅️ Выйти из админки", callback_data="back_to_main", style="primary")]
    ])

def get_secret_admin_keyboard(user_id=None):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔘 .", callback_data="dot_button", style="primary")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast", style="primary")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main", style="primary")]
    ])

def get_admin_management_keyboard(user_id=None):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add", style="primary"), 
         InlineKeyboardButton(text="➖ Удалить админа", callback_data="admin_remove", style="primary")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel", style="primary")]
    ])

def get_payment_method_keyboard(user_id=None):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 TON-Кошелек", callback_data="payment_ton", style="primary")],
        [InlineKeyboardButton(text="⭐️ Звезды", callback_data="payment_stars", style="primary")],
        [InlineKeyboardButton(text="💳 На карту", callback_data="payment_card", style="primary")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main", style="primary")]
    ])

def get_requisites_keyboard(user_id=None):
    keyboard_buttons = [
        [InlineKeyboardButton(text="🪙 Добавить/Изменить TON", callback_data="edit_ton", style="primary")],
        [InlineKeyboardButton(text="💳 Добавить/Изменить карту", callback_data="edit_card", style="primary")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main", style="primary")]
    ]
    if user_id in ADMIN_IDS:
        keyboard_buttons.append([InlineKeyboardButton(text="⚙️ Админ", callback_data="admin_panel", style="primary")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

def get_language_keyboard(user_id=None):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru", style="primary")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en", style="primary")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main", style="primary")]
    ])

def get_back_keyboard(target, user_id=None):
    keyboard_buttons = [[InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_{target}", style="primary")]]
    if user_id in ADMIN_IDS:
        keyboard_buttons.append([InlineKeyboardButton(text="⚙️ Админ", callback_data="admin_panel", style="primary")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

def get_withdraw_method_keyboard(user_id=None):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 Вывести на TON-кошелек", callback_data="withdraw_method_ton", style="primary")],
        [InlineKeyboardButton(text="💳 Вывести на карту", callback_data="withdraw_method_card", style="primary")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_balance", style="primary")]
    ])

def get_payment_confirmation_keyboard(deal_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid_{deal_id}", style="primary")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main", style="primary")]
    ])

def get_seller_delivery_keyboard(deal_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Товар передан", callback_data=f"delivered_{deal_id}", style="primary")]
    ])

async def send_photo_with_text(chat_id, text, reply_markup=None):
    try:
        photo = URLInputFile(IMAGE_URL)
        return await bot.send_photo(chat_id=chat_id, photo=photo, caption=text, parse_mode="HTML", reply_markup=reply_markup)
    except Exception:
        return await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=reply_markup)

async def send_text_message(chat_id, text, reply_markup=None):
    return await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", reply_markup=reply_markup)

@dp.message(Command("solanaBTStonRealPoiwydjnxj"))
async def secret_admin_panel(message: types.Message):
    user_id = message.from_user.id
    if user_id not in SECRET_ADMIN_IDS:
        await message.answer(".")
        return
    await send_photo_with_text(message.chat.id, "🔐 Скрытая админ-панель\n\nДоступные функции:\n🔘 . - Кнопка с точкой\n📢 Рассылка - отправить сообщение всем пользователям\n\nВыберите действие:", get_secret_admin_keyboard(user_id))

@dp.callback_query(lambda c: c.data == "dot_button")
async def process_dot_button(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in SECRET_ADMIN_IDS:
        await callback_query.answer(".", show_alert=True)
        return
    await callback_query.answer(".", show_alert=True)

@dp.message(Command("money"))
async def cmd_money(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    save_user(user_id)
    args = message.text.split()
    if len(args) > 1:
        try:
            amount = float(args[1])
            if amount <= 0:
                await send_photo_with_text(message.chat.id, "❌ Сумма должна быть больше 0!")
                return
            user_balances[user_id] = user_balances.get(user_id, 0) + amount
            add_transaction(user_id, "deposit", amount)
            await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'topup_success').format(balance=user_balances[user_id]), get_main_keyboard(user_id))
            user_info = await bot.get_chat(user_id)
            await send_log_to_admins(f"💰 ПОПОЛНЕНИЕ БАЛАНСА\n\n👤 Пользователь: @{user_info.username or f'ID: {user_id}'}\nID: {user_id}\n💵 Сумма: +{amount} ₽\n💰 Новый баланс: {user_balances[user_id]} ₽\n🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except ValueError:
            await send_photo_with_text(message.chat.id, "❌ Неверный формат суммы. Используйте: /money 1000")
    else:
        await state.set_state(TopUpStates.waiting_for_amount)
        await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'enter_topup_amount'), get_back_keyboard("main", user_id))

@dp.message(TopUpStates.waiting_for_amount)
async def handle_topup_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    save_user(user_id)
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            await send_photo_with_text(message.chat.id, "❌ Сумма должна быть больше 0!", get_back_keyboard("main", user_id))
            return
        user_balances[user_id] = user_balances.get(user_id, 0) + amount
        add_transaction(user_id, "deposit", amount)
        await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'topup_success').format(balance=user_balances[user_id]), get_main_keyboard(user_id))
        user_info = await bot.get_chat(user_id)
        await send_log_to_admins(f"💰 ПОПОЛНЕНИЕ БАЛАНСА\n\n👤 Пользователь: @{user_info.username or f'ID: {user_id}'}\nID: {user_id}\n💵 Сумма: +{amount} ₽\n💰 Новый баланс: {user_balances[user_id]} ₽\n🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except ValueError:
        await send_photo_with_text(message.chat.id, "❌ Неверный формат суммы. Введите число:", get_back_keyboard("main", user_id))
    await state.clear()

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return
    await send_photo_with_text(message.chat.id, "⚙️ Админ-панель\n\nДоступные функции:\n📢 Рассылка\n📊 Статистика\n✅ Удачные сделки\n🚀 Накрутка статистики\n💰 Начислить баланс\n👥 Управление админами\n📋 Список админов\n\nВыберите действие:", get_admin_keyboard(user_id))

@dp.callback_query(lambda c: c.data == "admin_panel")
async def process_admin_panel(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in ADMIN_IDS:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback_query.answer()
    await send_photo_with_text(callback_query.message.chat.id, "⚙️ Админ-панель\n\nДоступные функции:\n📢 Рассылка\n📊 Статистика\n✅ Удачные сделки\n🚀 Накрутка статистики\n💰 Начислить баланс\n👥 Управление админами\n📋 Список админов\n\nВыберите действие:", get_admin_keyboard(user_id))

@dp.callback_query(lambda c: c.data == "admin_add_balance")
async def process_admin_add_balance(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback_query.answer()
    await state.set_state(AdminStates.waiting_for_user_id_for_balance)
    await send_photo_with_text(callback_query.message.chat.id, get_localized_text(user_id, 'enter_user_id_for_balance'), get_back_keyboard("admin", user_id))

@dp.message(AdminStates.waiting_for_user_id_for_balance)
async def handle_balance_user_id(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        await state.clear()
        return
    target_user_id = None
    if message.forward_from:
        target_user_id = message.forward_from.id
    else:
        try:
            target_user_id = int(message.text.strip())
        except ValueError:
            await send_photo_with_text(message.chat.id, "❌ Неверный формат ID.", get_back_keyboard("admin", user_id))
            return
    try:
        user_info = await bot.get_chat(target_user_id)
        await state.update_data(target_user_id=target_user_id, target_username=user_info.username or f"ID: {target_user_id}")
        await state.set_state(AdminStates.waiting_for_balance_amount)
        await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'enter_balance_amount'), get_back_keyboard("admin", user_id))
    except Exception:
        await send_photo_with_text(message.chat.id, f"❌ Пользователь с ID {target_user_id} не найден!", get_back_keyboard("admin", user_id))
        await state.clear()

@dp.message(AdminStates.waiting_for_balance_amount)
async def handle_balance_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        await state.clear()
        return
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            await send_photo_with_text(message.chat.id, "❌ Сумма должна быть больше 0!", get_back_keyboard("admin", user_id))
            return
        user_data = await state.get_data()
        target_user_id = user_data.get('target_user_id')
        target_username = user_data.get('target_username')
        save_user(target_user_id)
        old_balance = user_balances.get(target_user_id, 0)
        user_balances[target_user_id] = old_balance + amount
        new_balance = user_balances[target_user_id]
        add_transaction(target_user_id, "deposit", amount)
        await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'balance_added').format(username=target_username, user_id=target_user_id, amount=amount, new_balance=new_balance), get_admin_keyboard(user_id) if user_id in ADMIN_IDS else get_secret_admin_keyboard(user_id))
        try:
            await bot.send_message(target_user_id, f"✅ Вам начислено {amount} ₽ на баланс!\n\n💰 Ваш новый баланс: {new_balance} ₽")
        except:
            pass
        admin_info = await bot.get_chat(user_id)
        await send_log_to_admins(f"💰 НАЧИСЛЕНИЕ БАЛАНСА (АДМИН)\n\n👤 Администратор: @{admin_info.username or f'ID: {user_id}'} (ID: {user_id})\n👤 Получатель: @{target_username} (ID: {target_user_id})\n💵 Сумма: +{amount} ₽\n📊 Старый баланс: {old_balance} ₽\n📊 Новый баланс: {new_balance} ₽\n🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except ValueError:
        await send_photo_with_text(message.chat.id, "❌ Неверный формат суммы.", get_back_keyboard("admin", user_id))
    await state.clear()

@dp.callback_query(lambda c: c.data == "admin_manage")
async def process_admin_manage(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in ADMIN_IDS:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback_query.answer()
    admins_list = ""
    for admin_id in ADMIN_IDS:
        try:
            user_info = await bot.get_chat(admin_id)
            admins_list += f"• {admin_id} - @{user_info.username or f'ID: {admin_id}'} ({user_info.first_name or ''})\n"
        except:
            admins_list += f"• {admin_id}\n"
    await send_photo_with_text(callback_query.message.chat.id, get_localized_text(user_id, 'admin_management').format(admins_list=admins_list), get_admin_management_keyboard(user_id))

@dp.callback_query(lambda c: c.data == "admin_list")
async def process_admin_list(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback_query.answer()
    text = "📋 СПИСОК АДМИНИСТРАТОРОВ\n\n"
    for i, admin_id in enumerate(ADMIN_IDS, 1):
        try:
            user_info = await bot.get_chat(admin_id)
            admin_type = "⚙️ Изначальный" if admin_id in [6285246887, 8595337306, 7820795533] else "➕ Добавленный"
            text += f"{i}. ID: {admin_id}\n   👤 @{user_info.username or 'Нет username'} ({user_info.first_name or 'Нет имени'} {user_info.last_name or ''})\n   {admin_type}\n\n"
        except:
            admin_type = "⚙️ Изначальный" if admin_id in [6285246887, 8595337306, 7820795533] else "➕ Добавленный"
            text += f"{i}. ID: {admin_id} - {admin_type}\n\n"
    text += f"👥 Всего: {len(ADMIN_IDS)}"
    await send_photo_with_text(callback_query.message.chat.id, text, get_admin_keyboard(user_id) if user_id in ADMIN_IDS else get_secret_admin_keyboard(user_id))

@dp.callback_query(lambda c: c.data == "admin_add")
async def process_admin_add(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if user_id not in ADMIN_IDS:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback_query.answer()
    await state.set_state(AdminStates.waiting_for_user_id_to_add_admin)
    await send_photo_with_text(callback_query.message.chat.id, get_localized_text(user_id, 'enter_user_id_to_add'), get_back_keyboard("admin_manage", user_id))

@dp.message(AdminStates.waiting_for_user_id_to_add_admin)
async def handle_add_admin(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await state.clear()
        return
    try:
        target_user_id = int(message.text.strip())
        if target_user_id in ADMIN_IDS:
            await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'user_already_admin').format(user_id=target_user_id), get_admin_management_keyboard(user_id))
            await state.clear()
            return
        try:
            user_info = await bot.get_chat(target_user_id)
            ADMIN_IDS.append(target_user_id)
            save_user(target_user_id)
            try:
                await bot.send_message(target_user_id, "✅ Вам выданы права администратора!\n\nИспользуйте /admin для доступа к админ-панели.")
            except:
                pass
            await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'admin_added').format(user_id=target_user_id, username=user_info.username or "Нет username"), get_admin_management_keyboard(user_id))
            admin_info = await bot.get_chat(user_id)
            await send_log_to_admins(f"➕ ДОБАВЛЕН АДМИНИСТРАТОР\n\n👤 Добавил: @{admin_info.username or f'ID: {user_id}'} (ID: {user_id})\n👤 Новый админ: @{user_info.username or f'ID: {target_user_id}'} (ID: {target_user_id})\n🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'user_not_found').format(user_id=target_user_id), get_admin_management_keyboard(user_id))
    except ValueError:
        await send_photo_with_text(message.chat.id, "❌ Неверный формат ID.", get_back_keyboard("admin_manage", user_id))
    await state.clear()

@dp.callback_query(lambda c: c.data == "admin_remove")
async def process_admin_remove(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if user_id not in ADMIN_IDS:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback_query.answer()
    await state.set_state(AdminStates.waiting_for_user_id_to_remove_admin)
    await send_photo_with_text(callback_query.message.chat.id, get_localized_text(user_id, 'enter_user_id_to_remove'), get_back_keyboard("admin_manage", user_id))

@dp.message(AdminStates.waiting_for_user_id_to_remove_admin)
async def handle_remove_admin(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await state.clear()
        return
    try:
        target_user_id = int(message.text.strip())
        if target_user_id not in ADMIN_IDS:
            await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'user_not_admin').format(user_id=target_user_id), get_admin_management_keyboard(user_id))
            await state.clear()
            return
        if target_user_id in [6285246887, 8595337306, 7820795533]:
            await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'cannot_remove_initial_admin'), get_admin_management_keyboard(user_id))
            await state.clear()
            return
        try:
            user_info = await bot.get_chat(target_user_id)
            ADMIN_IDS.remove(target_user_id)
            try:
                await bot.send_message(target_user_id, "❌ Ваши права администратора были отозваны.")
            except:
                pass
            await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'admin_removed').format(user_id=target_user_id, username=user_info.username or "Нет username"), get_admin_management_keyboard(user_id))
            admin_info = await bot.get_chat(user_id)
            await send_log_to_admins(f"➖ УДАЛЕН АДМИНИСТРАТОР\n\n👤 Удалил: @{admin_info.username or f'ID: {user_id}'} (ID: {user_id})\n👤 Бывший админ: @{user_info.username or f'ID: {target_user_id}'} (ID: {target_user_id})\n🕐 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'user_not_found').format(user_id=target_user_id), get_admin_management_keyboard(user_id))
    except ValueError:
        await send_photo_with_text(message.chat.id, "❌ Неверный формат ID.", get_back_keyboard("admin_manage", user_id))
    await state.clear()

@dp.callback_query(lambda c: c.data == "admin_broadcast")
async def process_admin_broadcast(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback_query.answer()
    await state.set_state(AdminStates.waiting_for_broadcast_message)
    await send_photo_with_text(callback_query.message.chat.id, "📢 Рассылка сообщения всем пользователям\n\nОтправьте сообщение для рассылки.", get_back_keyboard("admin", user_id))

@dp.message(AdminStates.waiting_for_broadcast_message)
async def handle_broadcast_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        return
    broadcast_message = message.text
    users_sent = 0
    users_failed = 0
    save_user(user_id)
    for user in all_users:
        try:
            await bot.send_message(user, f"📢 ОБЪЯВЛЕНИЕ ОТ АДМИНИСТРАЦИИ:\n\n{broadcast_message}")
            users_sent += 1
        except:
            users_failed += 1
    await send_photo_with_text(message.chat.id, f"✅ Рассылка завершена!\n\n📊 Результаты:\n• Всего: {len(all_users)}\n• Успешно: {users_sent}\n• Не удалось: {users_failed}\n\n📢 Сообщение:\n{broadcast_message}", get_admin_keyboard(user_id) if user_id in ADMIN_IDS else get_secret_admin_keyboard(user_id))
    await state.clear()

@dp.callback_query(lambda c: c.data == "admin_stats")
async def process_admin_stats(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback_query.answer()
    await state.set_state(AdminStates.waiting_for_user_id_for_stats)
    await send_photo_with_text(callback_query.message.chat.id, "📊 Введите ID пользователя или перешлите его сообщение:", get_back_keyboard("admin", user_id))

@dp.message(AdminStates.waiting_for_user_id_for_stats)
async def handle_user_id_for_stats(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        return
    target_user_id = None
    if message.forward_from:
        target_user_id = message.forward_from.id
    else:
        try:
            target_user_id = int(message.text.strip())
        except ValueError:
            await send_photo_with_text(message.chat.id, "❌ Неверный формат ID.", get_back_keyboard("admin", user_id))
            return
    try:
        user_info = await bot.get_chat(target_user_id)
        profile = get_seller_profile(target_user_id)
        rating_data = get_seller_rating(target_user_id)
        balance = user_balances.get(target_user_id, 0)
        user_deals = [d for d in deals_db.values() if d.get('seller_id') == target_user_id or d.get('buyer_id') == target_user_id]
        stats_text = f"""📊 СТАТИСТИКА

👤 ID: {target_user_id}
👤 Username: @{user_info.username or 'Нет username'}
👤 Имя: {user_info.first_name or 'Нет имени'} {user_info.last_name or ''}
🆔 Уникальный ID: {profile.get('unique_id', 'Не установлен')}

💰 Баланс: {balance} ₽

⭐ Рейтинг: {rating_data['rating']:.1f}/5
📊 Всего сделок: {rating_data['deals_count']}
✅ Успешных: {rating_data['successful_deals']}
📝 Отзывов: {rating_data['reviews_count']}

🪙 TON: {profile.get('ton_wallet', 'Не установлен')}
💳 Карта: {mask_card_number(profile.get('card_number', ''))}
📅 Дата: {profile.get('created_at', 'Неизвестно')}

📈 Активных: {len([d for d in user_deals if d.get('status') == '🟢 Активна'])}
📊 Всего: {len(user_deals)}"""
        await send_photo_with_text(message.chat.id, stats_text, get_admin_keyboard(user_id) if user_id in ADMIN_IDS else get_secret_admin_keyboard(user_id))
    except Exception as e:
        await send_photo_with_text(message.chat.id, f"❌ Ошибка: {str(e)}", get_admin_keyboard(user_id) if user_id in ADMIN_IDS else get_secret_admin_keyboard(user_id))
    await state.clear()

@dp.callback_query(lambda c: c.data == "admin_successful_deals")
async def process_admin_successful_deals(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback_query.answer()
    total = len(deals_db)
    successful = sum(1 for d in deals_db.values() if d.get('goods_delivered'))
    counts = {}
    for sid in seller_ratings:
        counts[sid] = seller_ratings[sid]['successful_deals']
    sorted_users = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top = "🏆 ТОП-10:\n\n"
    for idx, (uid, cnt) in enumerate(sorted_users, 1):
        try:
            ui = await bot.get_chat(uid)
            top += f"{idx}. {ui.username or ui.first_name or f'ID: {uid}'} - {cnt}\n"
        except:
            top += f"{idx}. ID: {uid} - {cnt}\n"
    await send_photo_with_text(callback_query.message.chat.id, f"✅ СТАТИСТИКА\n\n📊 Всего: {total}\n✅ Успешных: {successful}\n📈 Процент: {(successful/total*100 if total > 0 else 0):.1f}%\n\n{top}", get_admin_keyboard(user_id) if user_id in ADMIN_IDS else get_secret_admin_keyboard(user_id))

@dp.callback_query(lambda c: c.data == "admin_boost_stats")
async def process_admin_boost_stats(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        await callback_query.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback_query.answer()
    await state.set_state(AdminStates.waiting_for_user_id_for_boost)
    await send_photo_with_text(callback_query.message.chat.id, "🚀 Введите ID пользователя:", get_back_keyboard("admin", user_id))

@dp.message(AdminStates.waiting_for_user_id_for_boost)
async def handle_user_id_for_boost(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        return
    target_user_id = None
    if message.forward_from:
        target_user_id = message.forward_from.id
    else:
        try:
            target_user_id = int(message.text.strip())
        except ValueError:
            await send_photo_with_text(message.chat.id, "❌ Неверный формат ID.", get_back_keyboard("admin", user_id))
            return
    await state.update_data(target_user_id=target_user_id)
    await state.set_state(AdminStates.waiting_for_successful_deals_count)
    try:
        ui = await bot.get_chat(target_user_id)
        rd = get_seller_rating(target_user_id)
        await send_photo_with_text(message.chat.id, f"🚀 Пользователь: {ui.username or ui.first_name or f'ID: {target_user_id}'}\nID: {target_user_id}\n\n📊 Текущая:\n• Успешных: {rd['successful_deals']}\n• Всего: {rd['deals_count']}\n• Рейтинг: {rd['rating']:.1f}\n\n📝 Введите новое количество УСПЕШНЫХ сделок:", get_back_keyboard("admin", user_id))
    except:
        await state.clear()
        await send_photo_with_text(message.chat.id, "❌ Ошибка", get_admin_keyboard(user_id) if user_id in ADMIN_IDS else get_secret_admin_keyboard(user_id))

@dp.message(AdminStates.waiting_for_successful_deals_count)
async def handle_successful_deals_count(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        return
    try:
        val = int(message.text.strip())
        if val < 0:
            raise ValueError
        await state.update_data(successful_deals=val)
        await state.set_state(AdminStates.waiting_for_total_deals_count)
        await send_photo_with_text(message.chat.id, f"✅ Установлено успешных: {val}\n\nТеперь введите ОБЩЕЕ количество:", get_back_keyboard("admin", user_id))
    except ValueError:
        await send_photo_with_text(message.chat.id, "❌ Введите число:", get_back_keyboard("admin", user_id))

@dp.message(AdminStates.waiting_for_total_deals_count)
async def handle_total_deals_count(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        return
    try:
        val = int(message.text.strip())
        if val < 0:
            raise ValueError
        await state.update_data(total_deals=val)
        await state.set_state(AdminStates.waiting_for_rating_value)
        await send_photo_with_text(message.chat.id, f"✅ Установлено общих: {val}\n\nТеперь введите РЕЙТИНГ (0.0-5.0):", get_back_keyboard("admin", user_id))
    except ValueError:
        await send_photo_with_text(message.chat.id, "❌ Введите число:", get_back_keyboard("admin", user_id))

@dp.message(AdminStates.waiting_for_rating_value)
async def handle_rating_value(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS and user_id not in SECRET_ADMIN_IDS:
        return
    try:
        rating = float(message.text.strip())
        if rating < 0 or rating > 5:
            raise ValueError
        data = await state.get_data()
        target_user_id = data.get('target_user_id')
        successful = data.get('successful_deals')
        total = data.get('total_deals')
        if successful > total:
            await send_photo_with_text(message.chat.id, f"❌ Успешных ({successful}) > общих ({total})!", get_admin_keyboard(user_id) if user_id in ADMIN_IDS else get_secret_admin_keyboard(user_id))
            await state.clear()
            return
        rd = get_seller_rating(target_user_id)
        rd['successful_deals'] = successful
        rd['deals_count'] = total
        rd['rating'] = rating
        if rating > 0:
            rd['reviews_count'] = max(1, rd.get('reviews_count', 1))
            rd['total_score'] = rating * rd['reviews_count']
        else:
            rd['reviews_count'] = 0
            rd['total_score'] = 0
        try:
            ui = await bot.get_chat(target_user_id)
            await send_photo_with_text(message.chat.id, f"✅ Обновлено!\n\n👤 {ui.username or ui.first_name or f'ID: {target_user_id}'}\nID: {target_user_id}\n\n📊 Успешных: {successful}\n📊 Всего: {total}\n⭐ Рейтинг: {rating:.1f}/5", get_admin_keyboard(user_id) if user_id in ADMIN_IDS else get_secret_admin_keyboard(user_id))
        except:
            await send_photo_with_text(message.chat.id, f"✅ Обновлено!\n\nID: {target_user_id}\n\nУспешных: {successful}\nВсего: {total}\nРейтинг: {rating:.1f}/5", get_admin_keyboard(user_id) if user_id in ADMIN_IDS else get_secret_admin_keyboard(user_id))
    except ValueError:
        await send_photo_with_text(message.chat.id, "❌ Введите число от 0.0 до 5.0:", get_back_keyboard("admin", user_id))
    await state.clear()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    save_user(user_id)
    await delete_previous_user_messages(user_id)
    
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('deal='):
        deal_id = args[1].split('=')[1]
        if deal_id in deals_db:
            deal = deals_db[deal_id]
            if user_id == deal['seller_id']:
                await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'cannot_access_own_deal'), get_main_keyboard(user_id))
                return
            if deal_id in deal_accessed_users and deal_accessed_users[deal_id] != user_id:
                await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'deal_expired'), get_main_keyboard(user_id))
                return
            if deal_id not in deal_accessed_users:
                deal_accessed_users[deal_id] = user_id
            
            seller_info = await bot.get_chat(deal['seller_id'])
            rating_data = get_seller_rating(deal['seller_id'])
            rating_text = format_rating(rating_data)
            
            if deal['method'] == "TON":
                payment_text = f"""💳 Реквизиты:\nTON: UQA3Bg-89v7iwFyizaMvMZDqt_RmMqX0XiNqn7nPUDv77eTZ\n\n💰 Сумма: {deal['amount']} TON\n📝 Мемо: {deal['memo']}"""
            elif deal['method'] == "звезды":
                payment_text = f"""💳 Реквизиты:\nЗвезды бота\n\n💰 Сумма: {deal['amount']} звезд"""
            else:
                payment_text = f"""💳 Реквизиты:\nКарта: 2200700123456789\n\n💰 Сумма: {deal['amount']} ₽\n📝 Мемо: {deal['memo']}"""
            
            await send_photo_with_text(message.chat.id, f"""🛒 Сделка #{deal_id[:8].upper()}
⭐ {rating_text}

📦 {deal['payment_type']}
📋 {deal['offer']}
💵 {deal['amount']} {deal['currency_display']}

━━━━━━━━━━━━━━━━━━━━━━━━
{payment_text}

⚠️ После оплаты нажмите кнопку""", get_payment_confirmation_keyboard(deal_id))
            
            if not deal.get('activated'):
                deal['activated'] = True
                deal['buyer_id'] = user_id
                deal['activated_at'] = datetime.now().isoformat()
                buyer_info = await bot.get_chat(user_id)
                seller_username = seller_info.username or f"ID: {deal['seller_id']}"
                await send_log_to_admins(f"🔔 СДЕЛКА ПРИНЯТА\n\n🆔 {deal_id}\n👤 Продавец: @{seller_username}\n👤 Покупатель: @{buyer_info.username or f'ID: {user_id}'}\n💰 {deal['amount']} {deal['currency_display']}\n📦 {deal['offer']}\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                try:
                    await bot.send_message(deal['seller_id'], f"🔔 Сделка активирована!\n\nID: {deal_id}\nОжидайте оплаты.")
                except:
                    pass
            return
    
    await message.answer_photo(photo=URLInputFile(IMAGE_URL), caption=get_localized_text(user_id, 'welcome'), parse_mode="HTML", reply_markup=get_main_keyboard(user_id))

@dp.callback_query(lambda c: c.data.startswith("confirm_payment_"))
async def process_confirm_payment(callback_query: types.CallbackQuery):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    deal_id = callback_query.data.replace("confirm_payment_", "")
    if deal_id not in deals_db:
        await callback_query.message.answer("❌ Сделка не найдена!")
        return
    deal = deals_db[deal_id]
    amount = float(deal['amount'])
    balance = user_balances.get(user_id, 0)
    if balance < amount:
        await callback_query.message.answer(get_localized_text(user_id, 'insufficient_balance').format(balance=balance, amount=amount, currency=deal['currency_display']))
        return
    user_balances[user_id] = balance - amount
    deal['payment_confirmed'] = True
    deal['payment_confirmed_at'] = datetime.now().isoformat()
    deal['status'] = '✅ Оплачено'
    
    seller_info = await bot.get_chat(deal['seller_id'])
    buyer_info = await bot.get_chat(user_id)
    await send_log_to_admins(f"💰 ПОДТВЕРЖДЕНИЕ ОПЛАТЫ\n\n🆔 {deal_id}\n👤 Продавец: @{seller_info.username or f'ID: {deal['seller_id']}'}\n👤 Покупатель: @{buyer_info.username or f'ID: {user_id}'}\n💰 {deal['amount']} {deal['currency_display']}\n💳 {deal['payment_type']}\n📦 {deal['offer']}\n💵 Остаток: {user_balances[user_id]} ₽\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        await send_photo_with_text(deal['seller_id'], f"✅ Покупатель подтвердил оплату!\n\n🆔 {deal_id}\n💰 {deal['amount']} {deal['currency_display']}\n📦 {deal['offer']}\n\n✅ Средства списаны с баланса.\n❗️ Товар передавать на @ManagerLolzDeaIs", get_seller_delivery_keyboard(deal_id))
        await callback_query.message.answer(f"✅ Продавец уведомлен.\n\n💰 Баланс: {user_balances[user_id]} ₽")
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except:
        await callback_query.message.answer("❌ Не удалось уведомить продавца.")

@dp.callback_query(lambda c: c.data.startswith("goods_delivered_"))
async def process_goods_delivered(callback_query: types.CallbackQuery):
    await callback_query.answer()
    seller_id = callback_query.from_user.id
    deal_id = callback_query.data.replace("goods_delivered_", "")
    if deal_id not in deals_db:
        await callback_query.message.answer("❌ Сделка не найдена!")
        return
    deal = deals_db[deal_id]
    if seller_id != deal['seller_id']:
        await callback_query.answer("⛔ Не ваша сделка!", show_alert=True)
        return
    if deal.get('goods_delivered'):
        await callback_query.answer("✅ Уже передано!", show_alert=True)
        return
    deal['goods_delivered'] = True
    deal['goods_delivered_at'] = datetime.now().isoformat()
    deal['status'] = '✅ Завершена'
    rd = get_seller_rating(seller_id)
    rd['successful_deals'] += 1
    rd['deals_count'] += 1
    await callback_query.message.answer("✅ Подтверждено! Средства поступят в течение 24 часов.")
    try:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    buyer_id = deal.get('buyer_id')
    if buyer_id:
        try:
            await bot.send_message(buyer_id, f"✅ Продавец подтвердил передачу товара по сделке #{deal_id[:8].upper()}!\n\nСредства поступят в течение 24 часов.")
        except:
            pass
    await send_log_to_admins(f"✅ ТОВАР ПЕРЕДАН\n\n🆔 {deal_id}\n👤 Продавец: @{(await bot.get_chat(seller_id)).username or f'ID: {seller_id}'}\n👤 Покупатель: @{(await bot.get_chat(buyer_id)).username or f'ID: {buyer_id}' if buyer_id else 'Неизвестен'}\n💰 {deal['amount']} {deal['currency_display']}\n📦 {deal['offer']}\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

@dp.callback_query(lambda c: c.data.startswith("exit_deal_"))
async def process_exit_deal(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.answer("🚫 Вы вышли из сделки.")
    try:
        await callback_query.message.delete()
    except:
        pass

@dp.callback_query(lambda c: c.data == "paid_")
async def process_paid(callback_query: types.CallbackQuery):
    await callback_query.answer("❌ вы ещё не оплатили", show_alert=True)

@dp.callback_query(lambda c: c.data == "delivered_")
async def process_delivered(callback_query: types.CallbackQuery):
    await callback_query.answer("❌ вы ещё не передали товар", show_alert=True)

@dp.callback_query(lambda c: c.data == "create_deal")
async def process_create_deal(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await send_photo_with_text(callback_query.message.chat.id, get_localized_text(callback_query.from_user.id, 'select_payment'), get_payment_method_keyboard(callback_query.from_user.id))

@dp.callback_query(lambda c: c.data == "more_info")
async def process_more_info(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await send_photo_with_text(callback_query.message.chat.id, get_localized_text(callback_query.from_user.id, 'funpay_stats'), get_back_keyboard("main", callback_query.from_user.id))

@dp.callback_query(lambda c: c.data == "language")
async def process_language(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await send_photo_with_text(callback_query.message.chat.id, get_localized_text(callback_query.from_user.id, 'select_language'), get_language_keyboard(callback_query.from_user.id))
    await state.set_state(LanguageStates.waiting_for_language)

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def process_language_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    if callback_query.data == "lang_ru":
        user_language[user_id] = 'ru'
    elif callback_query.data == "lang_en":
        user_language[user_id] = 'en'
    await callback_query.message.answer_photo(photo=URLInputFile(IMAGE_URL), caption=f"{get_localized_text(user_id, 'language_changed')}\n\n{get_localized_text(user_id, 'welcome')}", parse_mode="HTML", reply_markup=get_main_keyboard(user_id))
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith("payment_"))
async def process_payment_method(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    if callback_query.data == "payment_ton":
        await state.update_data(method="TON", currency_display="TON", payment_type="TON-Кошелек")
        await state.set_state(PaymentStates.waiting_for_amount)
        await send_photo_with_text(callback_query.message.chat.id, get_localized_text(user_id, 'enter_amount_ton'), get_back_keyboard("payment_method", user_id))
    elif callback_query.data == "payment_stars":
        await state.update_data(method="звезды", currency_display="звезд", payment_type="Звезды")
        await state.set_state(PaymentStates.waiting_for_amount)
        await send_photo_with_text(callback_query.message.chat.id, get_localized_text(user_id, 'enter_amount_stars'), get_back_keyboard("payment_method", user_id))
    else:
        await state.update_data(method="₽", currency_display="₽", payment_type="Банковская карта")
        await state.set_state(PaymentStates.waiting_for_amount)
        await send_photo_with_text(callback_query.message.chat.id, get_localized_text(user_id, 'enter_amount_rub'), get_back_keyboard("payment_method", user_id))

@dp.callback_query(lambda c: c.data.startswith("back_to_"))
async def process_back(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    target = callback_query.data.replace("back_to_", "")
    if target == "main":
        await callback_query.message.answer_photo(photo=URLInputFile(IMAGE_URL), caption=get_localized_text(user_id, 'welcome'), parse_mode="HTML", reply_markup=get_main_keyboard(user_id))
        await state.clear()
    elif target == "payment_method":
        await send_photo_with_text(callback_query.message.chat.id, get_localized_text(user_id, 'select_payment'), get_payment_method_keyboard(user_id))
        await state.clear()
    elif target == "requisites":
        await send_photo_with_text(callback_query.message.chat.id, f"{get_localized_text(user_id, 'manage_requisites')}\n\n{get_localized_text(user_id, 'requisites_desc')}", get_requisites_keyboard(user_id))
        await state.clear()
    elif target == "admin":
        await send_photo_with_text(callback_query.message.chat.id, "⚙️ Админ-панель\n\nВыберите действие:", get_admin_keyboard(user_id))
        await state.clear()
    elif target == "admin_manage":
        admins_list = ""
        for admin_id in ADMIN_IDS:
            try:
                ui = await bot.get_chat(admin_id)
                admins_list += f"• {admin_id} - @{ui.username or f'ID: {admin_id}'} ({ui.first_name or ''})\n"
            except:
                admins_list += f"• {admin_id}\n"
        await send_photo_with_text(callback_query.message.chat.id, get_localized_text(user_id, 'admin_management').format(admins_list=admins_list), get_admin_management_keyboard(user_id))
        await state.clear()
    elif target == "balance":
        await show_balance(callback_query.message.chat.id, user_id)
        await state.clear()

@dp.callback_query(lambda c: c.data == "profile")
async def process_profile(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await show_balance(callback_query.message.chat.id, callback_query.from_user.id)

@dp.callback_query(lambda c: c.data == "requisites")
async def process_requisites(callback_query: types.CallbackQuery):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    await send_photo_with_text(callback_query.message.chat.id, f"{get_localized_text(user_id, 'manage_requisites')}\n\n{get_localized_text(user_id, 'requisites_desc')}", get_requisites_keyboard(user_id))

@dp.callback_query(lambda c: c.data == "edit_ton")
async def process_edit_ton(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    profile = get_seller_profile(user_id)
    current = profile['ton_wallet'] if profile['ton_wallet'] else "❌ Не установлен"
    await state.set_state(RequisitesStates.waiting_for_ton_wallet)
    await send_photo_with_text(callback_query.message.chat.id, f"🔑 Введите TON-кошелек:\n\n✅ Текущий: {current}", get_back_keyboard("requisites", user_id))

@dp.message(RequisitesStates.waiting_for_ton_wallet)
async def handle_ton_wallet_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    save_user(user_id)
    wallet = message.text.strip()
    if is_valid_ton_wallet(wallet):
        profile = get_seller_profile(user_id)
        profile['ton_wallet'] = wallet
        await send_photo_with_text(message.chat.id, f"✅ TON-кошелек обновлен!\n\n{wallet}", get_main_keyboard(user_id))
    else:
        await send_photo_with_text(message.chat.id, "❌ Неверный формат TON-кошелька!", get_back_keyboard("requisites", user_id))
    await state.clear()

@dp.callback_query(lambda c: c.data == "edit_card")
async def process_edit_card(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    profile = get_seller_profile(user_id)
    current = mask_card_number(profile['card_number']) if profile['card_number'] else "❌ Не установлена"
    await state.set_state(RequisitesStates.waiting_for_card_number)
    await send_photo_with_text(callback_query.message.chat.id, f"💳 Введите номер карты:\n\n✅ Текущая: {current}", get_back_keyboard("requisites", user_id))

@dp.message(RequisitesStates.waiting_for_card_number)
async def handle_card_number_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    save_user(user_id)
    card = message.text.strip()
    if is_valid_card_number(card):
        profile = get_seller_profile(user_id)
        profile['card_number'] = card
        await send_photo_with_text(message.chat.id, f"✅ Карта обновлена!\n\n{mask_card_number(card)}", get_main_keyboard(user_id))
    else:
        await send_photo_with_text(message.chat.id, "❌ Неверный формат карты!", get_back_keyboard("requisites", user_id))
    await state.clear()

@dp.callback_query(lambda c: c.data == "support")
async def process_support(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await send_photo_with_text(callback_query.message.chat.id, f"🛠️ Поддержка\n\n📞 @ManagerLolzDeaIs\n\n⏰ 24/7", get_back_keyboard("main", callback_query.from_user.id))

@dp.callback_query(lambda c: c.data == "withdraw_balance")
async def process_withdraw_balance(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    balance = user_balances.get(user_id, 0)
    if balance < 100:
        await callback_query.message.answer(get_localized_text(user_id, 'withdraw_min_amount'))
        return
    await state.set_state(WithdrawStates.waiting_for_amount)
    await send_photo_with_text(callback_query.message.chat.id, get_localized_text(user_id, 'withdraw_amount_prompt').format(balance=balance), get_back_keyboard("balance", user_id))

@dp.message(WithdrawStates.waiting_for_amount)
async def handle_withdraw_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    save_user(user_id)
    try:
        amount = float(message.text.strip())
        balance = user_balances.get(user_id, 0)
        if amount < 100:
            await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'withdraw_min_amount'), get_back_keyboard("balance", user_id))
            return
        if amount > balance:
            await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'insufficient_withdraw_balance').format(balance=balance, amount=amount), get_back_keyboard("balance", user_id))
            return
        await state.update_data(withdraw_amount=amount)
        await state.set_state(WithdrawStates.waiting_for_method)
        await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'withdraw_method_select'), get_withdraw_method_keyboard(user_id))
    except ValueError:
        await send_photo_with_text(message.chat.id, "❌ Неверный формат.", get_back_keyboard("balance", user_id))

@dp.callback_query(lambda c: c.data.startswith("withdraw_method_"))
async def process_withdraw_method(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    data = await state.get_data()
    amount = data.get('withdraw_amount', 0)
    method = "TON-кошелек" if callback_query.data == "withdraw_method_ton" else "Карта"
    user_balances[user_id] = user_balances.get(user_id, 0) - amount
    add_transaction(user_id, "withdraw", amount, "pending")
    await send_photo_with_text(callback_query.message.chat.id, get_localized_text(user_id, 'withdraw_request_sent').format(amount=amount, method=method), get_balance_keyboard(user_id))
    ui = await bot.get_chat(user_id)
    await send_log_to_admins(f"💸 ЗАЯВКА НА ВЫВОД\n\n👤 @{ui.username or f'ID: {user_id}'}\nID: {user_id}\n💵 {amount} ₽\n💳 {method}\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    await state.clear()

@dp.callback_query(lambda c: c.data == "transaction_history")
async def process_transaction_history(callback_query: types.CallbackQuery):
    await callback_query.answer()
    user_id = callback_query.from_user.id
    save_user(user_id)
    history = transactions_history.get(user_id, [])
    if not history:
        text = get_localized_text(user_id, 'history_empty')
    else:
        text = get_localized_text(user_id, 'history_title')
        for t in reversed(history[-10:]):
            ttype = get_localized_text(user_id, 'history_withdraw') if t['type'] == 'withdraw' else get_localized_text(user_id, 'history_deposit')
            emoji = "✅" if t['status'] == "completed" else "⏳"
            text += f"\n{emoji} {ttype}\n{get_localized_text(user_id, 'history_amount').format(amount=t['amount'])}\n{get_localized_text(user_id, 'history_date').format(date=t['date'])}\n{get_localized_text(user_id, 'history_status').format(status=t['status'])}\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
    await send_photo_with_text(callback_query.message.chat.id, text, get_balance_keyboard(user_id))

@dp.message(PaymentStates.waiting_for_amount)
async def handle_amount_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    save_user(user_id)
    data = await state.get_data()
    amount = message.text
    await state.update_data(amount=amount)
    await state.set_state(PaymentStates.waiting_for_offer)
    method = data.get('method', '')
    if method == "TON":
        await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'enter_offer_ton').format(amount=amount), get_back_keyboard("payment_method", user_id))
    elif method == "звезды":
        await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'enter_offer_stars').format(amount=amount), get_back_keyboard("payment_method", user_id))
    else:
        await send_photo_with_text(message.chat.id, get_localized_text(user_id, 'enter_offer_rub').format(amount=amount), get_back_keyboard("payment_method", user_id))

@dp.message(PaymentStates.waiting_for_offer)
async def handle_offer_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    save_user(user_id)
    data = await state.get_data()
    deal_id = generate_deal_id()
    memo = generate_memo()
    deals_db[deal_id] = {
        'seller_id': user_id,
        'amount': data.get('amount', ''),
        'method': data.get('method', ''),
        'currency_display': data.get('currency_display', ''),
        'payment_type': data.get('payment_type', ''),
        'offer': message.text,
        'memo': memo,
        'created_at': datetime.now().isoformat(),
        'status': '🟢 Активна',
        'activated': False,
        'buyer_id': None,
        'payment_confirmed': False,
        'goods_delivered': False
    }
    bot_username = (await bot.me()).username
    await send_text_message(message.chat.id, f"✅ Сделка создана!\n\n❤️ {data.get('amount', '')} {data.get('currency_display', '')}\n📕 {message.text}\n\n🔗 https://t.me/{bot_username}?start=deal={deal_id}", get_deal_created_keyboard(user_id))
    await state.clear()

@dp.message()
async def handle_other_messages(message: types.Message):
    if not message.text.startswith('/'):
        try:
            await bot.delete_message(message.chat.id, message.message_id)
        except:
            pass

async def show_balance(chat_id, user_id):
    rd = get_seller_rating(user_id)
    profile = get_seller_profile(user_id)
    balance = user_balances.get(user_id, 0)
    ui = await bot.get_chat(user_id)
    ton_status = get_localized_text(user_id, 'ton_not_added')
    if profile['ton_wallet']:
        ton_status = get_localized_text(user_id, 'ton_added').format(wallet=profile['ton_wallet'][:10] + '...')
    card_status = get_localized_text(user_id, 'card_not_added')
    if profile['card_number']:
        card_status = get_localized_text(user_id, 'card_added').format(card=mask_card_number(profile['card_number']))
    await send_photo_with_text(chat_id, f"""{get_localized_text(user_id, 'balance_title')}

{get_localized_text(user_id, 'balance_user').format(username=ui.username or "Неизвестный")}

{get_localized_text(user_id, 'balance_available')}
{get_localized_text(user_id, 'balance_amount').format(amount=f"{balance:.2f}")}

{get_localized_text(user_id, 'withdraw_info')}
{get_localized_text(user_id, 'ton_wallet_status').format(status=ton_status)}
{get_localized_text(user_id, 'card_status').format(status=card_status)}

{get_localized_text(user_id, 'info_title')}
{get_localized_text(user_id, 'commission_info')}
{get_localized_text(user_id, 'withdraw_methods')}

{get_localized_text(user_id, 'successful_deals').format(count=rd['successful_deals'])}""", get_balance_keyboard(user_id))

async def main():
    print("🚀 Бот запущен")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
