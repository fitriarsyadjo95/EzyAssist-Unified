import asyncio
import re
import requests
import json
from openai import AsyncOpenAI
from typing import Dict, List
import os
from dotenv import load_dotenv
from broker_profiles import BROKER_PROFILES, get_broker_info, compare_brokers
from broker_training_data import BROKER_QA_PAIRS, BROKER_COMPARISONS, SCENARIO_RECOMMENDATIONS
import httpx

load_dotenv()

class ConversationEngine:
    def __init__(self):
        print("🚀 Initializing ConversationEngine...")
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ ERROR: OPENAI_API_KEY not found in environment variables")
            self.openai_client = None
        else:
            print(f"🔑 Initializing OpenAI client with API key: {api_key[:8]}...")
            try:
                self.openai_client = AsyncOpenAI(api_key=api_key)
                print("✅ OpenAI client initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize OpenAI client: {e}")
                self.openai_client = None

        # Registration API configuration (using built-in system)
        self.base_url = os.getenv('BASE_URL', 'https://ezyassist-unified-production.up.railway.app')
        self.jwt_secret_key = os.getenv('JWT_SECRET_KEY')

        if not self.jwt_secret_key:
            print("WARNING: JWT_SECRET_KEY not found in environment variables")
        # VIP-specific registration keywords (direct triggers)
        self.vip_registration_keywords = [
            'vip', 'vip channel', 'belajar vip', 'jadi vip', 'become vip', 
            'want vip', 'nak vip', 'vip member', 'vip group', 'premium', 
            'upgrade', 'daftar vip', 'register vip', 'nak tahu pasal vip', 
            'tahu pasal vip', 'about vip', 'info vip', 'maklumat vip', 
            'vip info', 'vip details'
        ]
        
        # Action keywords that need to be combined with VIP
        self.action_keywords = [
            'register', 'registration', 'sign up', 'join', 'enroll',
            'daftar', 'pendaftaran', 'mendaftar', 'sertai', 'berminat',
            'ingin join', 'nak join'
        ]
        
        # General interest keywords (less specific)
        self.interest_keywords = [
            'course', 'program', 'learn more', 'interested', 'kursus'
        ]
        self.greeting_keywords = [
            'hello', 'hi', 'hey', 'good morning', 'good evening', 
            'good afternoon', 'greetings',
            'hai', 'halo', 'selamat pagi', 'selamat petang', 
            'selamat malam', 'apa khabar', 'assalamualaikum'
        ]
        self.malay_keywords = [
            'apa', 'bagaimana', 'kenapa', 'bila', 'di mana', 'siapa',
            'boleh', 'saya', 'tidak', 'ya', 'baik', 'terima kasih',
            'forex', 'perdagangan', 'mata wang', 'analisis', 'strategi'
        ]
        self.broker_keywords = [
            'octafx', 'octa', 'hfm', 'hotforex', 'valetax', 'dollars markets',
            'broker', 'brokers', 'compare', 'comparison', 'review', 'regulation',
            'spread', 'leverage', 'minimum deposit', 'platform', 'mt4', 'mt5',
            'cysec', 'fca', 'fsc', 'regulated', 'withdrawal', 'deposit'
        ]
        self.faq_responses_en = {
            'what is forex': (
                "Forex (Foreign Exchange) is the global marketplace for trading currencies. "
                "It's the largest financial market in the world, with over $6 trillion traded daily. "
                "In forex trading, you buy one currency while selling another."
            ),
            'how to start trading': (
                "To start forex trading:\n"
                "1. Learn the basics of forex markets\n"
                "2. Choose a reliable broker\n"
                "3. Open a demo account to practice\n"
                "4. Develop a trading strategy\n"
                "5. Start with small amounts\n"
                "6. Keep learning and improving"
            ),
            'risk management': (
                "Risk management is crucial in forex trading:\n"
                "• Never risk more than 1-2% of your account per trade\n"
                "• Use stop-loss orders\n"
                "• Diversify your trades\n"
                "• Don't trade with emotions\n"
                "• Have a clear trading plan"
            ),
            'trading hours': (
                "Forex markets are open 24 hours a day, 5 days a week:\n"
                "• Sydney: 10 PM - 7 AM GMT\n"
                "• Tokyo: 12 AM - 9 AM GMT\n"
                "• London: 8 AM - 5 PM GMT\n"
                "• New York: 1 PM - 10 PM GMT"
            ),
            'currency pairs': (
                "Currency pairs are divided into three categories:\n"
                "• Major Pairs: EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, USD/CAD, NZD/USD\n"
                "• Minor Pairs: EUR/GBP, EUR/JPY, GBP/JPY, CHF/JPY\n"
                "• Exotic Pairs: USD/SGD, USD/HKD, EUR/TRY\n"
                "Major pairs have the highest liquidity and lowest spreads."
            ),
            'pip': (
                "A pip (percentage in point) is the smallest price move in a currency pair:\n"
                "• For most pairs: 0.0001 (4th decimal place)\n"
                "• For JPY pairs: 0.01 (2nd decimal place)\n"
                "• Example: EUR/USD moves from 1.1250 to 1.1251 = 1 pip\n"
                "Pips are used to measure profits and losses."
            ),
            'spread': (
                "The spread is the difference between bid and ask prices:\n"
                "• Bid: Price you can sell at\n"
                "• Ask: Price you can buy at\n"
                "• Spread = Ask - Bid\n"
                "Lower spreads mean lower trading costs. Major pairs typically have tighter spreads."
            ),
            'leverage': (
                "Leverage allows you to control larger positions with smaller capital:\n"
                "• 1:100 leverage means $1 controls $100\n"
                "• Higher leverage = Higher risk and potential reward\n"
                "• Common ratios: 1:50, 1:100, 1:200, 1:500\n"
                "⚠️ Use leverage carefully - it can amplify losses!"
            ),
            'margin': (
                "Margin is the deposit required to open a leveraged position:\n"
                "• Required margin = Position size ÷ Leverage\n"
                "• Free margin = Account balance - Used margin\n"
                "• Margin call occurs when equity falls below required margin\n"
                "Always monitor your margin levels to avoid forced closure."
            ),
            'technical analysis': (
                "Technical analysis uses charts and indicators to predict prices:\n"
                "• Support & Resistance levels\n"
                "• Moving Averages (MA, EMA)\n"
                "• RSI, MACD, Bollinger Bands\n"
                "• Candlestick patterns\n"
                "• Trend lines and chart patterns"
            ),
            'fundamental analysis': (
                "Fundamental analysis examines economic factors affecting currencies:\n"
                "• Interest rates and central bank policies\n"
                "• Economic indicators (GDP, inflation, employment)\n"
                "• Political stability and news events\n"
                "• Trade balances and current accounts\n"
                "• Market sentiment and risk appetite"
            ),
            'trading strategy': (
                "Common forex trading strategies:\n"
                "• Scalping: Very short-term (minutes)\n"
                "• Day Trading: Positions closed same day\n"
                "• Swing Trading: Hold for days to weeks\n"
                "• Position Trading: Long-term (months)\n"
                "Choose based on your time, risk tolerance, and experience."
            ),
            'stop loss': (
                "Stop loss is an order to close a losing trade automatically:\n"
                "• Limits your maximum loss per trade\n"
                "• Should be set before entering trade\n"
                "• Place below support (buy) or above resistance (sell)\n"
                "• Risk 1-2% of account per trade maximum\n"
                "Never trade without a stop loss!"
            ),
            'take profit': (
                "Take profit automatically closes winning trades:\n"
                "• Secures profits at predetermined levels\n"
                "• Risk-reward ratio should be at least 1:2\n"
                "• Place at resistance (buy) or support (sell)\n"
                "• Can use trailing stops to capture more profit\n"
                "Don't be greedy - take profits when available!"
            )
        }

        self.faq_responses_ms = {
            'apa itu forex': (
                "OK, saya explain ye! Forex ni short form untuk Foreign Exchange - basically tempat orang trade mata wang lah. "
                "Memang pasaran paling besar dalam dunia ni, lebih RM25 trilion trade setiap hari! "
                "Cara kerja dia senang je - macam kita tukar RM ke USD ke, tapi untuk profit. "
                "Contoh: Kalau USD/MYR naik, maksudnya USD kuat, ringgit lemah. Kita boleh trade pair ni untuk profit."
            ),
            'bagaimana mula trading': (
                "Nak start forex trading? Boleh je! Ni step-step yang kena buat:\n"
                "1. Belajar basic dulu - jangan main campak je\n"
                "2. Cari broker yang okay dan boleh percaya (pastikan ada support BM)\n"
                "3. Buka demo account dulu, practice free\n"
                "4. Deposit minimum start dengan RM100-500 je dulu\n"
                "5. Pilih broker yang accept Malaysian payment method (online banking, eWallet)\n"
                "6. Keep learning lah - forex ni tak pernah berhenti belajar"
            ),
            'pengurusan risiko': (
                "Risk management ni memang penting betul dalam forex:\n"
                "• Jangan main ALL IN - max 1-2% je per trade (kalau account RM1000, risk RM10-20 je)\n"
                "• Mesti guna stop-loss, jangan kedekut\n"
                "• Jangan letak semua telur dalam satu bakul\n"
                "• Trading dengan kepala sejuk, bukan dengan hati\n"
                "• Trade dengan duit extra je, jangan sampai affect EPF atau emergency fund\n"
                "• Kena ada plan yang clear sebelum masuk market"
            ),
            'waktu trading': (
                "Market forex ni buka 24 jam, 5 hari seminggu je:\n"
                "• Sydney: 6 AM - 3 PM Malaysian time (pagi kita lah)\n"
                "• Tokyo: 8 AM - 5 PM Malaysian time (best untuk USD/JPY, AUD/JPY)\n"
                "• London: 4 PM - 1 AM Malaysian time (session paling best ni!)\n"
                "• New York: 9 PM - 6 AM Malaysian time (overlap dengan London)\n"
                "Best time untuk kita: 4 PM - 1 AM (London session) - volume tinggi, movement bagus!\n"
                "Weekend je tutup, so boleh trade lepas kerja pun!"
            ),
            'pasangan mata wang': (
                "Currency pairs ni ada 3 jenis lah:\n"
                "• Major pairs: EUR/USD, GBP/USD, USD/JPY - ni yang popular, spread rendah\n"
                "• Minor pairs: EUR/GBP, EUR/JPY, GBP/JPY - tak de USD tapi okay jugak\n"
                "• Exotic pairs: USD/SGD, USD/MYR, EUR/TRY - ni yang jarang orang main\n"
                "Kalau nak senang, main major pairs je dulu. Liquidity tinggi, spread pun murah."
            ),
            'pip': (
                "Pip ni macam unit kecik untuk measure pergerakan harga:\n"
                "• Most pairs: 0.0001 (4 decimal places)\n"
                "• JPY pairs: 0.01 (2 decimal places je)\n"
                "• Contoh: EUR/USD naik dari 1.1250 ke 1.1251 = 1 pip lah\n"
                "Pip ni penting sebab dia tentukan profit/loss kita. Lagi banyak pip, lagi besar untung rugi."
            ),
            'spread': (
                "Spread ni gap antara harga beli dengan harga jual:\n"
                "• Bid: Harga kita boleh jual\n"
                "• Ask: Harga kita boleh beli\n"
                "• Spread = Ask - Bid (selisih dia lah)\n"
                "Lagi kecik spread, lagi murah cost trading kita. Macam commission broker tu."
            ),
            'leverage': (
                "Leverage ni macam pinjam wang dari broker untuk trade besar:\n"
                "• Leverage 1:100 = RM1 kita boleh control RM100\n"
                "• Lagi tinggi leverage = Lagi besar risk DAN profit\n"
                "• Yang biasa: 1:30, 1:50, 1:100 (Bank Negara ada guidelines)\n"
                "• Contoh: Account RM500, leverage 1:100, boleh trade position RM50,000\n"
                "⚠️ Jangan main-main dengan leverage tinggi - boleh margin call, habis duit!"
            ),
            'margin': (
                "Margin ni deposit yang kena bayar untuk buka position leverage:\n"
                "• Formula: Position size ÷ Leverage = Margin required\n"
                "• Free margin = Balance - Margin yang dah guna\n"
                "• Kalau equity jatuh, broker call margin - tutup position paksa\n"
                "Kena monitor selalu ni, jangan sampai kena force close."
            ),
            'analisis teknikal': (
                "Technical analysis ni pakai chart dan indicator untuk predict harga:\n"
                "• Support & Resistance levels - tempat harga bounce\n"
                "• Moving Average (MA, EMA) - trend line\n"
                "• RSI, MACD, Bollinger Bands - indicator popular\n"
                "• Candlestick patterns - bentuk lilin tu\n"
                "• Trend lines dan chart patterns - corak harga\n"
                "Senang je, tengok chart dan cari pattern!"
            ),
            'analisis fundamental': (
                "Fundamental analysis ni tengok economic factors yang affect mata wang:\n"
                "• Interest rates - kalau naik, mata wang kuat\n"
                "• Economic data - GDP, inflation, employment\n"
                "• Political stability - kalau tak stable, mata wang drop\n"
                "• Trade balance - import vs export\n"
                "• Market sentiment - orang optimistic ke tak\n"
                "Basically tengok kesihatan ekonomi negara tu lah."
            ),
            'strategi trading': (
                "Trading strategy ni macam-macam, pilih yang sesuai:\n"
                "• Scalping: Cepat masuk keluar, dalam minit je\n"
                "• Day Trading: Buka tutup dalam hari yang sama\n"
                "• Swing Trading: Hold few days sampai few weeks\n"
                "• Position Trading: Long term, bulan-bulan\n"
                "Pilih ikut masa free kita, risk appetite, dan experience level."
            ),
            'stop loss': (
                "Stop loss ni auto close position kalau rugi:\n"
                "• Set limit berapa max boleh rugi per trade\n"
                "• Kena set SEBELUM masuk trade, jangan last minute\n"
                "• Letak below support (buy) atau above resistance (sell)\n"
                "• Max risk 1-2% account balance je per trade\n"
                "Golden rule: JANGAN PERNAH trade tanpa stop loss!"
            ),
            'take profit': (
                "Take profit ni auto close position kalau dah profit:\n"
                "• Lock in keuntungan pada level yang kita target\n"
                "• Risk-reward ratio minimum 1:2 (risk RM1, target RM2)\n"
                "• Set kat resistance (buy) atau support (sell)\n"
                "• Boleh pakai trailing stop untuk maximum profit\n"
                "Jangan tamak sangat - ada untung ambil je lah!"
            )
        }

    def detect_language(self, message: str) -> str:
        """Always return Bahasa Melayu - bot responds only in Malay"""
        return 'ms'

    def is_forex_related(self, message: str) -> bool:
        """Check if message is forex/trading related"""
        forex_terms = [
            'forex', 'trading', 'currency', 'pair', 'pip', 'spread', 'leverage', 'margin',
            'broker', 'chart', 'analysis', 'technical', 'fundamental', 'support', 'resistance',
            'trend', 'bull', 'bear', 'long', 'short', 'buy', 'sell', 'profit', 'loss',
            'strategy', 'scalping', 'swing', 'position', 'market', 'exchange', 'rate',
            'mata wang', 'perdagangan', 'pasaran', 'analisis', 'strategi', 'keuntungan',
            'kerugian', 'broker', 'carta', 'teknikal', 'asas', 'sokongan', 'rintangan',
            'rugi', 'untung', 'trade', 'handle loss', 'manage risk', 'stop loss'
        ]

        message_lower = message.lower()

        # Check for trading context phrases
        trading_phrases = [
            'nak belajar trade', 'belajar trading', 'learn trade', 'learn trading',
            'handle loss', 'manage loss', 'trading loss', 'loss dalam trading',
            'macam mana nak', 'how to trade', 'trading tips', 'risk management'
        ]

        # Check both individual terms and phrases
        return (any(term in message_lower for term in forex_terms) or 
                any(phrase in message_lower for phrase in trading_phrases))

    def is_broker_inquiry(self, message: str) -> bool:
        """Check if message is asking about specific brokers"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.broker_keywords)

    def get_mentioned_brokers(self, message: str) -> list:
        """Extract broker names mentioned in the message"""
        message_lower = message.lower()
        mentioned = []

        broker_mappings = {
            'octafx': 'octafx',
            'octa': 'octafx',
            'hfm': 'hfm',
            'hotforex': 'hfm',
            'hot forex': 'hfm',
            'valetax': 'valetax',
            'dollars markets': 'dollars_markets',
            'dollarsmarkets': 'dollars_markets'
        }

        for keyword, broker_key in broker_mappings.items():
            if keyword in message_lower:
                mentioned.append(broker_key)

        return list(set(mentioned))  # Remove duplicates

    async def generate_registration_link(self, telegram_id: str, telegram_username: str = "") -> str:
        """Generate VIP registration link using built-in system"""
        try:
            import jwt
            from datetime import datetime, timedelta
            
            # Generate JWT token for registration
            payload = {
                'telegram_id': str(telegram_id),
                'telegram_username': telegram_username or '',
                'exp': datetime.utcnow() + timedelta(minutes=30),
                'iat': datetime.utcnow()
            }
            
            if not self.jwt_secret_key:
                print("❌ JWT_SECRET_KEY not configured, cannot generate registration link")
                return "error"
            
            token = jwt.encode(payload, self.jwt_secret_key, algorithm='HS256')
            registration_url = f"{self.base_url}/?token={token}"
            
            print(f"✅ Generated registration link for user {telegram_id}")
            return registration_url
            
        except Exception as e:
            print(f"❌ Failed to generate registration link: {e}")
            return "error"

    async def detect_intent(self, message: str) -> str:
        """Detect the intent of the user message"""
        message_lower = message.lower()

        # Check for greeting
        if any(keyword in message_lower for keyword in self.greeting_keywords):
            return 'greeting'

        # Check for VIP registration interest with improved logic
        # 1. Direct VIP keywords (immediate trigger)
        if any(keyword in message_lower for keyword in self.vip_registration_keywords):
            return 'registration'
        
        # 2. Action keywords combined with VIP mention
        has_action = any(keyword in message_lower for keyword in self.action_keywords)
        has_vip = 'vip' in message_lower
        if has_action and has_vip:
            return 'registration'
        
        # 3. Interest keywords combined with VIP (less direct)
        has_interest = any(keyword in message_lower for keyword in self.interest_keywords)
        if has_interest and has_vip:
            return 'registration'

        # Check for FAQ topics in both languages
        for faq_key in self.faq_responses_en.keys():
            if any(word in message_lower for word in faq_key.split()):
                return 'faq'

        for faq_key in self.faq_responses_ms.keys():
            if any(word in message_lower for word in faq_key.split()):
                return 'faq'

        # Check for broker-specific inquiries
        if self.is_broker_inquiry(message):
            return 'broker_inquiry'

        # Check if forex-related for general forex inquiry
        if self.is_forex_related(message):
            return 'forex_general'

        # Default to general (non-forex) inquiry
        return 'general'

    async def get_faq_response(self, message: str, language: str = 'en') -> str:
        """Get FAQ response based on message content and language"""
        message_lower = message.lower()

        # Choose appropriate FAQ responses based on language
        faq_responses = self.faq_responses_ms if language == 'ms' else self.faq_responses_en

        # Step 1: Check for exact phrase matches first (most precise)
        for faq_key, response in faq_responses.items():
            if faq_key in message_lower:
                return response

        # Step 2: Check for specific keyword combinations
        # Handle specific "stop loss" questions in Malay
        if any(phrase in message_lower for phrase in ['stop loss', 'stoploss', 'apa itu stop loss', 'apakah stop loss']):
            if 'stop loss' in faq_responses:
                return faq_responses['stop loss']

        # Handle specific "take profit" questions in Malay  
        if any(phrase in message_lower for phrase in ['take profit', 'takeprofit', 'apa itu take profit', 'apakah take profit']):
            if 'take profit' in faq_responses:
                return faq_responses['take profit']

        # Handle "apa itu forex" specifically (prevent false matches)
        if any(phrase in message_lower for phrase in ['apa itu forex', 'apakah forex', 'what is forex']):
            if 'apa itu forex' in faq_responses:
                return faq_responses['apa itu forex']
            elif 'what is forex' in faq_responses:
                return faq_responses['what is forex']

        # Step 3: Multi-word matching with better logic
        for faq_key, response in faq_responses.items():
            faq_words = faq_key.split()

            # For multi-word FAQ keys, require ALL important words to match
            if len(faq_words) >= 2:
                # Skip common words when matching
                important_words = [word for word in faq_words if word not in ['apa', 'itu', 'what', 'is', 'the', 'how', 'to']]

                if len(important_words) >= 1:
                    # All important words must be present
                    matching_words = sum(1 for word in important_words if word in message_lower)
                    if matching_words == len(important_words):
                        return response

            # For single word FAQ keys, only match specific trading terms
            elif len(faq_words) == 1:
                word = faq_words[0]
                if word in ['forex', 'leverage', 'margin', 'spread', 'pip'] and word in message_lower:
                    # Make sure it's not part of a longer phrase
                    if f"apa itu {word}" not in message_lower and f"what is {word}" not in message_lower:
                        return response

        # Step 4: Try other language with same logic
        other_faq = self.faq_responses_en if language == 'ms' else self.faq_responses_ms

        # Exact matches in other language
        for faq_key, response in other_faq.items():
            if faq_key in message_lower:
                return response

        # Multi-word matching in other language
        for faq_key, response in other_faq.items():
            faq_words = faq_key.split()

            if len(faq_words) >= 2:
                important_words = [word for word in faq_words if word not in ['apa', 'itu', 'what', 'is', 'the', 'how', 'to']]

                if len(important_words) >= 1:
                    matching_words = sum(1 for word in important_words if word in message_lower)
                    if matching_words == len(important_words):
                        return response

        return None

    def get_specific_broker_answer(self, broker: str, query_type: str, language: str = 'en') -> str:
        """Get specific answer for broker queries"""
        if broker in BROKER_QA_PAIRS and query_type in BROKER_QA_PAIRS[broker]:
            qa_data = BROKER_QA_PAIRS[broker][query_type]
            return qa_data[f'answer_{language}'] if f'answer_{language}' in qa_data else qa_data['answer_en']
        return None

    def detect_query_type(self, message: str) -> str:
        """Detect what type of information user is asking about"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['spread', 'pip', 'eur/usd', 'eurusd']):
            return 'spreads'
        elif any(word in message_lower for word in ['minimum deposit', 'min deposit', 'deposit']):
            return 'minimum_deposit'
        elif any(word in message_lower for word in ['mt5', 'mt4', 'metatrader', 'platform']):
            return 'platforms'
        elif any(word in message_lower for word in ['regulated', 'regulation', 'license', 'safe']):
            return 'regulation'
        elif any(word in message_lower for word in ['leverage', 'margin']):
            return 'leverage'
        elif any(word in message_lower for word in ['warning', 'risk', 'problem', 'issue']):
            return 'warnings'
        elif any(word in message_lower for word in ['beginner', 'new', 'start', 'pemula']):
            return 'beginner_recommendation'
        elif any(word in message_lower for word in ['scalping', 'scalp']):
            return 'scalping_recommendation'
        elif any(word in message_lower for word in ['professional', 'high volume', 'volume tinggi']):
            return 'professional_recommendation'

        return 'general'

    async def handle_broker_inquiry(self, message: str, language: str = 'en') -> str:
        """Handle broker-specific inquiries"""
        mentioned_brokers = self.get_mentioned_brokers(message)
        message_lower = message.lower()
        query_type = self.detect_query_type(message)

        # Handle scenario-based recommendations
        if query_type in ['beginner_recommendation', 'scalping_recommendation', 'professional_recommendation']:
            scenario_key = query_type.replace('_recommendation', '_trader')
            if scenario_key in SCENARIO_RECOMMENDATIONS:
                scenario = SCENARIO_RECOMMENDATIONS[scenario_key]
                title = scenario[f'title_{language}'] if f'title_{language}' in scenario else scenario['title_en']

                response = f"**{title}**\n\n"

                if '1st_choice' in scenario['recommendations']:
                    choice = scenario['recommendations']['1st_choice']
                    reasons_key = f'reasons_{language}' if f'reasons_{language}' in choice else 'reasons_en'

                    response += f"**🥇 {choice['broker']}:**\n"
                    for reason in choice[reasons_key]:
                        response += f"• {reason}\n"
                    response += "\n"

                if '2nd_choice' in scenario['recommendations']:
                    choice = scenario['recommendations']['2nd_choice']
                    reasons_key = f'reasons_{language}' if f'reasons_{language}' in choice else 'reasons_en'

                    response += f"**🥈 {choice['broker']}:**\n"
                    for reason in choice[reasons_key]:
                        response += f"• {reason}\n"

                return response

        # Handle specific broker questions
        if len(mentioned_brokers) == 1 and query_type != 'general':
            broker = mentioned_brokers[0]
            specific_answer = self.get_specific_broker_answer(broker, query_type, language)
            if specific_answer:
                return specific_answer

        # If comparing brokers
        if ('compare' in message_lower or 'comparison' in message_lower or 'vs' in message_lower) and len(mentioned_brokers) >= 2:
            broker1, broker2 = mentioned_brokers[0], mentioned_brokers[1]
            comparison = compare_brokers(broker1, broker2)

            if comparison:
                if language == 'ms':
                    response = f"**Perbandingan {comparison['broker1']} vs {comparison['broker2']}:**\n\n"
                    response += f"**Peraturan:**\n• {comparison['broker1']}: {', '.join(comparison['regulation']['broker1'])}\n"
                    response += f"• {comparison['broker2']}: {', '.join(comparison['regulation']['broker2'])}\n\n"
                    response += f"**Deposit Minimum:**\n• {comparison['broker1']}: {comparison['min_deposit']['broker1']}\n"
                    response += f"• {comparison['broker2']}: {comparison['min_deposit']['broker2']}\n\n"
                    response += f"**Platform:**\n• {comparison['broker1']}: {', '.join(comparison['platforms']['broker1'])}\n"
                    response += f"• {comparison['broker2']}: {', '.join(comparison['platforms']['broker2'])}"
                else:
                    response = f"**{comparison['broker1']} vs {comparison['broker2']} Comparison:**\n\n"
                    response += f"**Regulation:**\n• {comparison['broker1']}: {', '.join(comparison['regulation']['broker1'])}\n"
                    response += f"• {comparison['broker2']}: {', '.join(comparison['regulation']['broker2'])}\n\n"
                    response += f"**Minimum Deposit:**\n• {comparison['broker1']}: {comparison['min_deposit']['broker1']}\n"
                    response += f"• {comparison['broker2']}: {comparison['min_deposit']['broker2']}\n\n"
                    response += f"**Platforms:**\n• {comparison['broker1']}: {', '.join(comparison['platforms']['broker1'])}\n"
                    response += f"• {comparison['broker2']}: {', '.join(comparison['platforms']['broker2'])}"
                return response

        # If asking about specific broker
        elif len(mentioned_brokers) == 1:
            broker_info = get_broker_info(mentioned_brokers[0])
            if broker_info:
                if language == 'ms':
                    response = f"**Maklumat {broker_info['name']}:**\n\n"
                    response += f"**Peraturan:** {', '.join(broker_info['regulation']['primary_regulators'])}\n"
                    response += f"**Deposit Minimum:** {list(broker_info['trading_conditions']['account_types'].values())[0]['minimum_deposit']}\n"
                    response += f"**Leverage Maksimum:** {broker_info['trading_conditions']['maximum_leverage']}\n"
                    response += f"**Platform:** {', '.join(broker_info['platforms_tools']['trading_platforms'])}\n\n"

                    # Add warnings for risky brokers
                    if 'major_warnings' in broker_info:
                        response += "**⚠️ AMARAN PENTING:**\n"
                        for warning in broker_info['major_warnings']:
                            response += f"• {warning}\n"
                else:
                    response = f"**{broker_info['name']} Information:**\n\n"
                    response += f"**Regulation:** {', '.join(broker_info['regulation']['primary_regulators'])}\n"
                    response += f"**Minimum Deposit:** {list(broker_info['trading_conditions']['account_types'].values())[0]['minimum_deposit']}\n"
                    response += f"**Maximum Leverage:** {broker_info['trading_conditions']['maximum_leverage']}\n"
                    response += f"**Platforms:** {', '.join(broker_info['platforms_tools']['trading_platforms'])}\n\n"

                    # Add warnings for risky brokers
                    if 'major_warnings' in broker_info:
                        response += "**⚠️ CRITICAL WARNINGS:**\n"
                        for warning in broker_info['major_warnings']:
                            response += f"• {warning}\n"

                return response

        # General broker question without specific broker mentioned
        if language == 'ms':
            return ("Boleh je! Saya ada info pasal broker macam OctaFX, HFM, Valetax, dan Dollars Markets. "
                   "Tanya je pasal spread, leverage, regulation, atau nak compare broker mana-mana pun!")
        else:
            return ("I can help you with information about brokers like OctaFX, HFM, Valetax, and Dollars Markets. "
                   "Ask me about spreads, leverage, regulation, or compare these brokers!")

    async def generate_ai_response(self, message: str, context: str = "", language: str = 'en', is_forex: bool = True) -> str:
        """Generate AI response using OpenAI GPT-4o"""
        try:
            print(f"🤖 Generating AI response for: {message[:50]}... | Language: {language} | Is Forex: {is_forex}")

            # Check if OpenAI client is properly initialized
            if not self.openai_client:
                print("❌ ERROR: OpenAI client not initialized")
                if language == 'ms':
                    return (
                        "Maaf awak, saya ada masalah dengan AI system sekarang. "
                        "Boleh try tanya lagi atau tanya soalan yang specific pasal forex?"
                    )
                else:
                    return (
                        "Sorry, I'm having trouble with the AI system right now. "
                        "Please try asking again or ask a specific forex question."
                    )
                    
            # Verify API key exists
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                print("❌ ERROR: OPENAI_API_KEY not found")
                if language == 'ms':
                    return "Maaf, saya ada technical issue. Boleh cuba lagi nanti?"
                else:
                    return "Sorry, I'm having technical issues. Please try again later."

            if is_forex:
                if language == 'ms':
                    system_prompt = (
                        "Kau ni EzyAssist - forex trading assistant yang friendly gila! "
                        "Jawab dalam Bahasa Malaysia yang conversational macam cakap dengan kawan. "
                        "Pakai 'awak', 'lah', 'je', 'kan', 'tak' dalam ayat naturally. "
                        "Explain forex dalam cara yang senang faham, especially untuk M40/B40 yang nak start trading dengan budget limited. "
                        "CONTEXT MALAYSIA: Guna contoh RM (ringgit), sebut payment method local macam online banking, Touch 'n Go eWallet. "
                        "Consider Malaysian trading hours dan market overlap. Bila sebut regulation, mention Bank Negara Malaysia. "
                        "Guna Malaysian-relevant examples macam EPF, salary ranges (RM2k-5k), living costs. "
                        "Consider different income levels dan financial priorities. Encouraging tapi realistic pasal trading risks. "
                        "SAMPLE PHRASES: 'Kalau awak nak start trading ni...', 'Broker mana yang sesuai untuk awak?', 'Deposit minimum berapa ek?', "
                        "'Spread dia okay tak?', 'Boleh withdraw cepat tak?', 'Ada support Bahasa Malaysia tak?' "
                        "Selalu remind pasal safe trading dan risk management - jangan bagi advice yang bahaya. "
                        "Kalau tanya pasal register atau signals, promote VIP channel dengan quality signals dan expert analysis. "
                        "Guna mix BM dengan English terms bila perlu (macam 'leverage', 'spread', 'profit'). "
                        "Tone kena friendly, helpful, macam kawan yang experienced nak tolong."
                    )
                else:
                    system_prompt = (
                        "You are EzyAssist, a helpful forex trading assistant. "
                        "Provide clear, educational responses about forex trading. "
                        "Keep responses concise but informative. "
                        "Always encourage safe trading practices and proper risk management. "
                        "If asked about registration or signals, mention that you offer a VIP channel with high-quality trading signals and expert analysis to help them become profitable traders."
                    )
            else:
                # For general non-forex questions
                if language == 'ms':
                    system_prompt = (
                        "Kau ni EzyAssist - AI assistant yang friendly gila! "
                        "Jawab soalan user dalam Bahasa Malaysia yang natural macam cakap dengan kawan baik. "
                        "Pakai 'awak', 'lah', 'je', 'kan', 'tak' naturally dalam conversation. "
                        "Jawab soalan dia dengan helpful dan accurate. Kalau dia tanya pasal apa-apa pun, "
                        "try to give useful answer. After jawab, mention secara natural yang kau actually "
                        "expert dalam forex trading jugak kalau awak berminat nak belajar. "
                        "Tone kena friendly, warm, dan helpful macam kawan yang experienced."
                    )
                else:
                    system_prompt = (
                        "You are EzyAssist, a friendly and helpful AI assistant. "
                        "Answer the user's question clearly, accurately and helpfully regardless of the topic. "
                        "Be conversational and warm in your response. Keep responses informative but not too long. "
                        "After answering their question, naturally mention that you also specialize in forex trading "
                        "and can help with that if they're interested. Be helpful first, promotional second."
                    )

            if context:
                system_prompt += f"\nContext: {context}"

            print(f"Making OpenAI API call with model: gpt-4o")
            print(f"System prompt length: {len(system_prompt)}")
            print(f"User message: {message[:100]}...")

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=300,
                temperature=0.7
            )

            print(f"OpenAI API response received")
            print(f"Response choices count: {len(response.choices) if response.choices else 0}")

            if not response.choices or len(response.choices) == 0:
                print("ERROR: No choices in OpenAI response")
                raise Exception("No choices in OpenAI response")

            ai_response = response.choices[0].message.content
            print(f"AI response content length: {len(ai_response) if ai_response else 0}")
            print(f"AI response preview: {ai_response[:100] if ai_response else 'None'}...")

            # Ensure we have a valid response
            if not ai_response or ai_response.strip() == "":
                print(f"Warning: Empty AI response received for message: {message[:50]}")
                if language == 'ms':
                    return (
                        "Hm, saya tak sure macam mana nak jawab soalan ni dengan baik. "
                        "Boleh awak try tanya dengan cara lain atau tanya soalan lain? "
                        "Kalau awak berminat pasal forex trading, saya boleh tolong dengan tu!"
                    )
                else:
                    return (
                        "I'm not sure how to best answer that question. "
                        "Could you try asking it differently or ask another question? "
                        "If you're interested in forex trading, I can definitely help with that!"
                    )

            return ai_response.strip()

        except Exception as e:
            print(f"OpenAI API Error: {e}")
            print(f"Error type: {type(e).__name__}")
            print(f"Full error details: {str(e)}")

            # Check if it's an API key issue
            if "401" in str(e) or "Unauthorized" in str(e) or "api_key" in str(e).lower():
                print("ERROR: OpenAI API key issue detected")
            elif "429" in str(e) or "rate_limit" in str(e).lower():
                print("ERROR: OpenAI API rate limit exceeded")
            elif "quota" in str(e).lower() or "billing" in str(e).lower():
                print("ERROR: OpenAI API quota/billing issue")

            if language == 'ms':
                return (
                    "Maaf awak, saya ada masalah sikit sekarang nak process soalan ni. "
                    "Boleh try tanya lagi ke atau tanya soalan lain?"
                )
            else:
                return (
                    "I'm having trouble processing your request right now. "
                    "Please try again or feel free to ask another question."
                )

    async def should_suggest_registration(self, engagement_score: int) -> bool:
        """Determine if we should suggest registration based on engagement"""
        return engagement_score >= 3

    async def process_message(self, message: str, telegram_id: str, engagement_score: int, telegram_username: str = "") -> str:
        """Main method to process incoming messages"""
        print(f"🔥 ConversationEngine.process_message called")
        print(f"📝 Message: '{message}'")
        print(f"👤 User: {telegram_id}")
        print(f"📊 Engagement: {engagement_score}")
        
        # Detect language first
        language = self.detect_language(message)
        print(f"🌍 Detected language: {language}")
        
        intent = await self.detect_intent(message)
        print(f"🎯 Detected intent: {intent}")

        if intent == 'greeting':
            if language == 'ms':
                return (
                    "Hai awak! 👋 Welcome to EzyAssist! Saya sini nak tolong awak belajar pasal forex trading. "
                    "Boleh tanya pasal broker mana yang sesuai untuk Malaysian, deposit minimum berapa, atau apa-apa soalan trading. "
                    "Saya faham context kita - dari payment method sampai la Islamic account pun ada!"
                )
            else:
                return (
                    "Hello! 👋 Welcome to EzyAssist. I'm here to help you learn about forex trading. "
                    "Feel free to ask me any questions about forex markets, trading strategies, or risk management!"
                )

        elif intent == 'registration':
            # Generate registration link using built-in system
            registration_url = await self.generate_registration_link(telegram_id, telegram_username)
            
            if registration_url == "error":
                if language == 'ms':
                    return (
                        "🎯 Daftar VIP Channel EzyAssist sekarang!\n\n"
                        "Untuk mendaftar, gunakan command /register atau hubungi admin kami.\n\n"
                        "VIP channel kita ada:\n"
                        "• Trading signals quality tinggi 📊\n"
                        "• Daily market analysis dari expert\n"
                        "• Tips broker terbaik untuk Malaysian\n"
                        "• Support dari experienced trader community"
                    )
                else:
                    return (
                        "🎯 Register for EzyAssist VIP Channel now!\n\n"
                        "To register, use the /register command or contact our admin.\n\n"
                        "Our VIP channel offers:\n"
                        "• High-quality trading signals 📊\n"
                        "• Daily market analysis by experts\n"
                        "• Best broker tips for Malaysians\n"
                        "• Support from experienced trader community"
                    )
            
            if language == 'ms':
                return (
                    "🎯 Daftar VIP Channel EzyAssist sekarang!\n\n"
                    "VIP channel kita ada:\n"
                    "• Trading signals quality tinggi 📊\n"
                    "• Daily market analysis dari expert (focus Asian + London session)\n"
                    "• Tips broker mana yang best untuk Malaysian\n"
                    "• Support dari experienced Malaysian trader community\n"
                    "• Strategy sesuai untuk working adults (lepas kerja trading)\n\n"
                    f"Klik link di bawah untuk lengkapkan pendaftaran:\n{registration_url}\n\n"
                    "⏰ Link ini akan expired dalam 30 minit.\n"
                    "Lepas register, team kita akan semak dan contact dalam 24-48 jam untuk VIP access!"
                )
            else:
                return (
                    "🎯 Register for EzyAssist VIP Channel now!\n\n"
                    "Our VIP channel offers:\n"
                    "• High-quality trading signals 📊\n"
                    "• Daily market analysis by experts\n"
                    "• Latest trading tips and strategies\n"
                    "• Support from experienced trader community\n"
                    "• Guidance to become a profitable trader 💰\n\n"
                    f"Click the link below to complete registration:\n{registration_url}\n\n"
                    "⏰ This link will expire in 30 minutes.\n"
                    "Once you register, our team will review and contact you within 24-48 hours for VIP access!"
                )

        elif intent == 'faq':
            faq_response = await self.get_faq_response(message, language)
            if faq_response:
                # Add registration suggestion for engaged users
                if await self.should_suggest_registration(engagement_score):
                    registration_url = await self.generate_registration_link(telegram_id, telegram_username)
                    if registration_url and registration_url != "already_registered" and registration_url != "error":
                        if language == 'ms':
                            faq_response += (
                                f"\n\n💡 Nak dapat quality signals dan expert analysis? "
                                f"Join VIP channel kita: {registration_url}"
                            )
                        else:
                            faq_response += (
                                f"\n\n💡 Want high-quality signals and expert analysis? "
                                f"Join our VIP channel: {registration_url}"
                            )
                return faq_response

        elif intent == 'broker_inquiry':
            # Handle broker-specific inquiries
            return await self.handle_broker_inquiry(message, language)

        elif intent == 'forex_general':
            # For forex-related general inquiries, use AI with forex context
            context = f"User engagement score: {engagement_score}"
            ai_response = await self.generate_ai_response(message, context, language, is_forex=True)

            # Check if AI response is empty and provide fallback
            if not ai_response or ai_response.strip() == "":
                print(f"Empty AI response for forex question: {message[:50]}")
                if language == 'ms':
                    ai_response = (
                        "Soalan forex yang bagus tu! Saya tengah ada masalah sikit nak process properly. "
                        "Boleh awak try tanya dengan cara lain? Atau boleh tanya pasal broker recommendation, "
                        "risk management, atau trading strategy yang specific."
                    )
                else:
                    ai_response = (
                        "That's a great forex question! I'm having trouble processing it properly right now. "
                        "Could you try asking it differently? Or ask about broker recommendations, "
                        "risk management, or specific trading strategies."
                    )

            # Add registration suggestion for highly engaged users
            if await self.should_suggest_registration(engagement_score):
                registration_url = await self.generate_registration_link(telegram_id)
                if registration_url and registration_url != "already_registered" and registration_url != "error":
                    if language == 'ms':
                        ai_response += (
                            f"\n\n📚 Wah awak ni memang minat forex! "
                            f"Nak dapat quality trading signals dan expert analysis tak? "
                            f"Join VIP channel kita: {registration_url}"
                        )
                    else:
                        ai_response += (
                            f"\n\n📚 You seem really interested in forex! "
                            f"Want to get high-quality trading signals and expert analysis? "
                            f"Join our VIP channel: {registration_url}"
                        )

            return ai_response

        # For general non-forex inquiries, use AI with general context
        # The AI will handle gentle forex redirection as part of its system prompt
        else:
            print(f"Processing general question: {message[:50]}...")
            context = f"User engagement score: {engagement_score}, Non-forex general question"
            ai_response = await self.generate_ai_response(message, context, language, is_forex=False)
            return ai_response