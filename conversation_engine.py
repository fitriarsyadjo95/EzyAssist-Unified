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
        # Only keep broker keywords for broker inquiry detection
        self.broker_keywords = [
            'valetax', 'valet tax', 'broker', 'brokers', 'trading platform', 
            'account setup', 'registration', 'deposit', 'withdrawal',
            'spread', 'leverage', 'minimum deposit', 'platform', 'mt4', 'mt5',
            'fsc', 'regulated', 'trading conditions', 'account types'
        ]
        # FAQ responses removed - now handled by AI for natural conversation

        # Malay FAQ responses also removed - handled by AI

    def detect_language(self, message: str) -> str:
        """Detect language from user message - supports English, Bahasa Malaysia, and Bahasa Indonesia"""
        message_lower = message.lower()
        
        # Indonesian specific words and patterns
        indonesian_keywords = [
            'saya', 'aku', 'kamu', 'anda', 'dengan', 'untuk', 'dari', 'yang', 'ini', 'itu',
            'bisa', 'tidak', 'nggak', 'sudah', 'belum', 'bagaimana', 'mengapa', 'kenapa',
            'dimana', 'kapan', 'siapa', 'mau', 'ingin', 'butuh', 'perlu', 'belajar',
            'trading', 'forex', 'rupiah', 'investasi', 'saham', 'broker', 'platform',
            'gimana', 'dong', 'nih', 'deh', 'sih', 'banget', 'emang'
        ]
        
        # Malaysian specific words and patterns  
        malaysian_keywords = [
            'saya', 'aku', 'awak', 'kamu', 'dengan', 'untuk', 'dari', 'yang', 'ini', 'itu',
            'boleh', 'tak', 'tak boleh', 'sudah', 'belum', 'macam mana', 'mengapa', 'kenapa',
            'kat mana', 'bila', 'siapa', 'nak', 'mau', 'hendak', 'perlukan', 'belajar',
            'trading', 'forex', 'ringgit', 'pelaburan', 'saham', 'broker', 'platform',
            'lah', 'leh', 'la', 'ke', 'jer', 'je', 'kan', 'gak', 'tak'
        ]
        
        # English keywords
        english_keywords = [
            'i', 'you', 'me', 'my', 'your', 'with', 'for', 'from', 'that', 'this',
            'can', 'cannot', 'could', 'would', 'should', 'will', 'have', 'has', 'had',
            'how', 'what', 'why', 'when', 'where', 'who', 'want', 'need', 'learn',
            'trading', 'forex', 'dollar', 'investment', 'stock', 'broker', 'platform',
            'the', 'and', 'or', 'but', 'so', 'because', 'if', 'then', 'than'
        ]
        
        # Count matches for each language
        indonesian_score = sum(1 for word in indonesian_keywords if word in message_lower)
        malaysian_score = sum(1 for word in malaysian_keywords if word in message_lower)
        english_score = sum(1 for word in english_keywords if word in message_lower)
        
        # Check for specific language indicators
        if any(indicator in message_lower for indicator in ['gimana', 'dong', 'nih', 'banget', 'emang', 'nggak', 'bisa', 'rupiah']):
            return 'id'  # Indonesian
        elif any(indicator in message_lower for indicator in ['lah', 'leh', 'jer', 'je', 'nak', 'kat mana', 'ringgit', 'boleh']):
            return 'ms'  # Malaysian
        elif any(indicator in message_lower for indicator in ['the ', ' and ', ' or ', ' but ', 'dollar', 'cannot']):
            return 'en'  # English
            
        # Determine language based on highest score
        if indonesian_score > malaysian_score and indonesian_score > english_score:
            return 'id'
        elif malaysian_score > english_score:
            return 'ms'
        elif english_score > 0:
            return 'en'
        else:
            return 'ms'  # Default to Malaysian if no clear indicators

    def needs_live_agent(self, message: str) -> bool:
        """Detect if question requires live agent intervention"""
        message_lower = message.lower()
        
        # Technical analysis keywords
        technical_keywords = [
            'fibonacci retracement', 'elliott wave', 'harmonic pattern', 'divergence analysis',
            'ichimoku cloud', 'bollinger band', 'rsi divergence', 'macd histogram',
            'pivot point calculation', 'stochastic oscillator', 'williams %r',
            'market structure', 'price action', 'volume profile', 'order flow',
            'scalping strategy', 'day trading', 'swing trading', 'position sizing',
            'correlation analysis', 'carry trade', 'hedging strategy',
            'news trading', 'economic calendar', 'fundamental analysis'
        ]
        
        # Advanced trading concepts
        advanced_keywords = [
            'algorithmic trading', 'expert advisor', 'automated trading',
            'backtesting', 'forward testing', 'optimization',
            'risk management', 'portfolio management', 'money management',
            'drawdown', 'sharpe ratio', 'risk-reward ratio',
            'margin call', 'stop out', 'margin requirement',
            'slippage', 'requote', 'spread widening'
        ]
        
        # Live agent request keywords
        agent_request_keywords = [
            'live agent', 'human agent', 'real person', 'customer service',
            'support team', 'help desk', 'representative', 'advisor',
            'agent sebenar', 'manusia sebenar', 'customer support',
            'nak cakap dengan orang', 'minta tolong staff', 'agent bantuan',
            'agen sungguhan', 'manusia asli', 'customer support',
            'mau bicara dengan orang', 'minta tolong staff', 'agen bantuan'
        ]
        
        # Check for any technical keywords
        all_keywords = technical_keywords + advanced_keywords + agent_request_keywords
        
        for keyword in all_keywords:
            if keyword in message_lower:
                return True
                
        # Check for complex question patterns (multiple questions, specific strategy requests)
        if ('how to' in message_lower and ('strategy' in message_lower or 'trade' in message_lower)) or \
           ('what is the best' in message_lower and 'trading' in message_lower) or \
           len(message.split()) > 50:  # Very long questions
            return True
            
        return False

    def is_forex_related(self, message: str) -> bool:
        """Check if message is forex/trading related"""
        forex_terms = [
            'forex', 'trading', 'currency', 'pair', 'pip', 'spread', 'leverage', 'margin',
            'broker', 'chart', 'analysis', 'technical', 'fundamental', 'support', 'resistance',
            'trend', 'bull', 'bear', 'long', 'short', 'buy', 'sell', 'profit', 'loss',
            'strategy', 'scalping', 'swing', 'position', 'market', 'exchange', 'rate',
            # Malaysian terms
            'mata wang', 'perdagangan', 'pasaran', 'analisis', 'strategi', 'keuntungan',
            'kerugian', 'broker', 'carta', 'teknikal', 'asas', 'sokongan', 'rintangan',
            'rugi', 'untung', 'trade', 'handle loss', 'manage risk', 'stop loss',
            # Indonesian terms
            'mata uang', 'perdagangan', 'pasar', 'analisis', 'strategi', 'keuntungan',
            'kerugian', 'broker', 'grafik', 'teknikal', 'fundamental', 'dukungan', 'perlawanan',
            'rugi', 'untung', 'trade', 'kelola kerugian', 'manajemen risiko', 'stop loss'
        ]

        message_lower = message.lower()

        # Check for trading context phrases
        trading_phrases = [
            # English phrases
            'learn trade', 'learn trading', 'handle loss', 'manage loss', 'trading loss',
            'how to trade', 'trading tips', 'risk management',
            # Malaysian phrases
            'nak belajar trade', 'belajar trading', 'loss dalam trading',
            'macam mana nak', 'cara nak trade', 'tips trading',
            # Indonesian phrases
            'belajar trading', 'belajar trade', 'loss dalam trading',
            'gimana cara', 'bagaimana cara', 'cara trading', 'tips trading'
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
            'valetax': 'valetax',
            'valet tax': 'valetax',
            'broker': 'valetax',  # Default broker mentions to Valetax
            'trading platform': 'valetax'
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
        """Simplified intent detection - only 4 core intents"""
        message_lower = message.lower()
        
        # Priority 1: Check for indicator registration intent
        indicator_keywords = [
            'indicator', 'indikator', 'high level', 'engulfing', 'engulfing indicator',
            'rentungfx indicator', 'trading indicator', 'mt4 indicator', 'mt5 indicator',
            'custom indicator', 'price action indicator', 'signal indicator'
        ]
        
        if any(keyword in message_lower for keyword in indicator_keywords):
            # Check if it's related to registration/access
            if any(reg_word in message_lower for reg_word in ['register', 'daftar', 'access', 'get', 'download', 'dapat', 'nak', 'want', 'mau', 'ingin']):
                return 'indicator_registration'
        
        # Priority 2: Check for general registration intent (VIP/Channel)
        registration_keywords = [
            'register', 'daftar', 'join', 'signup', 'sign up', 'masuk', 'sertai',
            'vip', 'channel', 'premium', 'member', 'membership', 'ahli'
        ]
        
        if any(keyword in message_lower for keyword in registration_keywords):
            return 'registration'
        
        # Priority 3: Check for specific broker inquiries with multiple brokers mentioned
        if self.is_broker_inquiry(message):
            mentioned_brokers = self.get_mentioned_brokers(message)
            if len(mentioned_brokers) >= 1:  # If any specific broker is mentioned
                return 'broker_inquiry'
        
        # Priority 4: Everything else goes to AI conversation (includes greetings, FAQ, forex, general)
        return 'ai_conversation'

    # FAQ handling removed - now handled by AI for natural conversation

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
                    # Use the comprehensive overview for detailed broker information
                    if 'overview' in broker_info and len(broker_info['overview']) > 100:
                        # Use the detailed overview instead of short format
                        response = f"**{broker_info['name']}:**\n\n"
                        response += f"{broker_info['overview']}\n\n"
                    else:
                        # Fallback to short format if no detailed overview
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
        elif language == 'id':
            return ("Bisa dong! Saya punya info tentang broker seperti OctaFX, HFM, Valetax, dan Dollars Markets. "
                   "Tanya aja tentang spread, leverage, regulasi, atau mau compare broker mana pun!")
        else:
            return ("I can help you with information about brokers like OctaFX, HFM, Valetax, and Dollars Markets. "
                   "Ask me about spreads, leverage, regulation, or compare these brokers!")

    async def generate_ai_response(self, message: str, conversation_context: str = "", language: str = 'en') -> str:
        """Generate AI response using OpenAI GPT-4o"""
        try:
            print(f"🤖 Generating AI response for: {message[:50]}... | Language: {language}")

            # Check if OpenAI client is properly initialized
            if not self.openai_client:
                print("❌ ERROR: OpenAI client not initialized")
                if language == 'ms':
                    return (
                        "Maaf awak, saya ada masalah dengan AI system sekarang. "
                        "Boleh try tanya lagi atau tanya soalan yang specific pasal forex?"
                    )
                elif language == 'id':
                    return (
                        "Maaf, saya ada masalah dengan sistem AI sekarang. "
                        "Bisa coba tanya lagi atau tanya pertanyaan spesifik tentang forex?"
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
                elif language == 'id':
                    return "Maaf, saya ada masalah teknis. Bisa coba lagi nanti?"
                else:
                    return "Sorry, I'm having technical issues. Please try again later."

            # Smart context detection
            is_greeting = any(word in message.lower() for word in ['hello', 'hi', 'hai', 'good morning', 'assalamualaikum', 'selamat', 'start'])
            is_forex_related = self.is_forex_related(message)
            needs_agent = self.needs_live_agent(message)
            
            # If user needs live agent, provide immediate redirection
            if needs_agent:
                if language == 'ms':
                    return (
                        "Soalan awak ni memerlukan expertise dari agent sebenar! 🧑‍💼\n\n"
                        "Untuk bantuan lanjutan dengan:\n"
                        "✅ Analisis teknikal mendalam\n"
                        "✅ Strategi trading khusus\n"
                        "✅ Setup akaun Valetax\n\n"
                        "Sila type /agent untuk disambungkan dengan agent kami yang berpengalaman!"
                    )
                elif language == 'id':
                    return (
                        "Pertanyaan Anda memerlukan keahlian dari agen sungguhan! 🧑‍💼\n\n"
                        "Untuk bantuan lanjutan dengan:\n"
                        "✅ Analisis teknikal mendalam\n"
                        "✅ Strategi trading khusus\n"
                        "✅ Setup akun Valetax\n\n"
                        "Silakan ketik /agent untuk terhubung dengan agen berpengalaman kami!"
                    )
                else:
                    return (
                        "Your question requires expertise from a real agent! 🧑‍💼\n\n"
                        "For advanced help with:\n"
                        "✅ In-depth technical analysis\n"
                        "✅ Specific trading strategies\n" 
                        "✅ Valetax account setup\n\n"
                        "Please type /agent to connect with our experienced agents!"
                    )
            mentioned_brokers = self.get_mentioned_brokers(message)
            
            # Build context-aware prompts
            if language == 'ms':
                system_prompt = (
                    "Kau ni RentungBot_Ai - assistant pintar yang pakar dalam broker Valetax dan trading! "
                    "Jawab dalam Bahasa Malaysia yang natural macam cakap dengan kawan baik. "
                    "Pakai 'awak', 'lah', 'je', 'kan', 'tak' naturally dalam conversation. "
                    
                    "PERSONALITY: Friendly, knowledgeable, helpful, encouraging tapi realistic pasal risks. "
                    "CONTEXT MALAYSIA: "
                    "- Guna RM (ringgit) sebagai currency reference "
                    "- Sebut payment methods local: online banking, TNG eWallet, FPX "
                    "- Malaysian trading hours: 4PM-1AM (London session terbaik) "
                    "- Bank Negara Malaysia untuk regulation reference "
                    "- EPF, KWSP, salary ranges RM2k-5k untuk relatable examples "
                    "- Consider M40/B40 income levels dan priorities "
                    
                    "TRADING APPROACH: "
                    "- Start small (RM100-500 untuk beginner) "
                    "- Risk management FIRST (max 1-2% per trade) "
                    "- Demo account practice essential "
                    "- Selalu mention importance of stop loss "
                    "- Recommend Valetax sebagai broker pilihan dengan leverage tinggi dan deposit rendah "
                    
                    "CONVERSATION STYLE: "
                    "- Jawab soalan dengan detail yang helpful "
                    "- Guna examples yang relatable untuk Malaysian context "
                    "- Mix BM dengan common English trading terms naturally "
                    "- If tanya complex stuff, break down step by step "
                    "- ALWAYS end setiap response dengan: 'Nak berbual dengan agent sebenar? Type /agent' "
                    "- Keep responses CONCISE - match user's message length (short questions = short answers) "
                )
                
                # Add specific context based on message content
                if is_greeting:
                    system_prompt += (
                        "\nUSER CONTEXT: First interaction - be welcoming and introduce capabilities naturally. "
                        "Mention you can help with forex basics, broker selection, trading strategies, risk management. "
                    )
                elif is_forex_related and mentioned_brokers:
                    system_prompt += (
                        f"\nUSER CONTEXT: Asking about specific brokers: {', '.join(mentioned_brokers)}. "
                        "Give detailed comparison with Malaysian perspective (regulation, spreads, support, deposit methods). "
                    )
                elif is_forex_related:
                    system_prompt += (
                        "\nUSER CONTEXT: Forex-related question. Give comprehensive answer with Malaysian context. "
                        "Include practical examples, risk warnings, and encourage learning step by step. "
                    )
                else:
                    system_prompt += (
                        "\nUSER CONTEXT: Non-forex question. Answer helpfully first, then naturally mention "
                        "your forex expertise if relevant. Don't force the transition. "
                    )
            
            elif language == 'id':
                system_prompt = (
                    "Anda adalah RentungBot_Ai - asisten pintar yang ahli dalam broker Valetax dan trading! "
                    "Jawab dalam Bahasa Indonesia yang natural seperti berbicara dengan teman baik. "
                    "Gunakan 'Anda', 'bisa', 'dong', 'nih', 'sih' secara natural dalam percakapan. "
                    
                    "PERSONALITY: Ramah, berpengetahuan, membantu, mendorong tapi realistis tentang risiko. "
                    "KONTEKS INDONESIA: "
                    "- Gunakan Rupiah (IDR) sebagai referensi mata uang "
                    "- Sebutkan metode pembayaran lokal: transfer bank, e-wallet, virtual account "
                    "- Jam trading Indonesia: 21:00-06:00 WIB (sesi London terbaik) "
                    "- Bank Indonesia untuk referensi regulasi "
                    "- Gaji rata-rata Rp 5-15 juta untuk contoh yang relatable "
                    "- Pertimbangkan level ekonomi menengah Indonesia "
                    
                    "PENDEKATAN TRADING: "
                    "- Mulai kecil (Rp 500rb-2juta untuk pemula) "
                    "- Risk management PERTAMA (maksimal 1-2% per trade) "
                    "- Latihan demo account sangat penting "
                    "- Selalu sebutkan pentingnya stop loss "
                    "- Rekomendasikan Valetax sebagai broker pilihan dengan leverage tinggi dan deposit rendah "
                    
                    "GAYA PERCAKAPAN: "
                    "- Jawab pertanyaan dengan detail yang membantu "
                    "- Gunakan contoh yang relatable untuk konteks Indonesia "
                    "- Campur Bahasa Indonesia dengan istilah trading yang umum secara natural "
                    "- Jika pertanyaan kompleks, jelaskan step by step "
                    "- SELALU akhiri setiap respons dengan: 'Mau ngobrol dengan agen sungguhan? Ketik /agent' "
                    "- Jaga respons RINGKAS - sesuaikan dengan panjang pesan user (pertanyaan pendek = jawaban pendek) "
                )
                
                # Add specific context based on message content
                if is_greeting:
                    system_prompt += (
                        "\nKONTEKS USER: Interaksi pertama - sambut dengan ramah dan perkenalkan kemampuan secara natural. "
                        "Sebutkan bisa membantu dengan dasar forex, pemilihan broker, strategi trading, manajemen risiko. "
                    )
                elif is_forex_related and mentioned_brokers:
                    system_prompt += (
                        f"\nKONTEKS USER: Menanyakan broker spesifik: {', '.join(mentioned_brokers)}. "
                        "Berikan perbandingan detail dengan perspektif Indonesia (regulasi, spread, support, metode deposit). "
                    )
                elif is_forex_related:
                    system_prompt += (
                        "\nKONTEKS USER: Pertanyaan terkait forex. Berikan jawaban komprehensif dengan konteks Indonesia. "
                        "Sertakan contoh praktis, peringatan risiko, dan dorong pembelajaran bertahap. "
                    )
                else:
                    system_prompt += (
                        "\nKONTEKS USER: Pertanyaan non-forex. Jawab dengan membantu dulu, lalu secara natural sebutkan "
                        "keahlian forex jika relevan. Jangan dipaksakan transisinya. "
                    )
                    
            else:
                system_prompt = (
                    "You are RentungBot_Ai, a smart assistant specializing in Valetax broker and forex trading. "
                    "You have deep knowledge of Valetax services, forex markets, trading strategies, and risk management. "
                    
                    "PERSONALITY: Helpful, knowledgeable, encouraging but realistic about trading risks. "
                    "APPROACH: "
                    "- Give comprehensive but concise answers "
                    "- Use practical examples and analogies "
                    "- Always emphasize proper risk management "
                    "- Encourage safe learning progression "
                    "- Be supportive but honest about trading challenges "
                    
                    "TRADING PRINCIPLES: "
                    "- Start with demo accounts and small amounts "
                    "- Never risk more than 1-2% per trade "
                    "- Recommend Valetax as preferred broker with high leverage and low minimum deposits "
                    "- Focus on education before big investments "
                    "- Stop losses are mandatory, not optional "
                    "- ALWAYS end responses with: 'Want to talk to a real person? Type /agent' "
                    "- Keep responses CONCISE - match the user's message length "
                )
                
                # Add specific context based on message content  
                if is_greeting:
                    system_prompt += (
                        "\nUSER CONTEXT: First interaction - welcome them and naturally introduce your forex expertise. "
                        "Mention you can help with trading basics, broker selection, strategies, and risk management. "
                    )
                elif is_forex_related and mentioned_brokers:
                    system_prompt += (
                        f"\nUSER CONTEXT: Asking about specific brokers: {', '.join(mentioned_brokers)}. "
                        "Provide detailed comparison including regulation, spreads, platforms, and user experience. "
                    )
                elif is_forex_related:
                    system_prompt += (
                        "\nUSER CONTEXT: Forex-related question. Give thorough answer with practical examples. "
                        "Include risk warnings and encourage gradual learning approach. "
                    )
                else:
                    system_prompt += (
                        "\nUSER CONTEXT: Non-forex question. Answer their question first, then naturally "
                        "mention your forex specialization if there's a relevant connection. "
                    )

            if conversation_context:
                system_prompt += f"\nAdditional Context: {conversation_context}"

            # Calculate appropriate max_tokens based on user message length
            message_words = len(message.split())
            if message_words <= 10:  # Short question
                max_tokens = 100
            elif message_words <= 30:  # Medium question  
                max_tokens = 200
            else:  # Long question
                max_tokens = 350

            print(f"Making OpenAI API call with model: gpt-4o")
            print(f"System prompt length: {len(system_prompt)}")
            print(f"User message: {message[:100]}... | Words: {message_words} | Max tokens: {max_tokens}")

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=max_tokens,
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
                elif language == 'id':
                    return (
                        "Hmm, saya nggak yakin gimana cara terbaik jawab pertanyaan itu. "
                        "Bisa coba tanya dengan cara lain atau tanya pertanyaan lain? "
                        "Kalau Anda tertarik sama forex trading, saya pasti bisa bantu!"
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
            elif language == 'id':
                return (
                    "Maaf, saya ada masalah sedikit sekarang untuk proses pertanyaan ini. "
                    "Bisa coba tanya lagi atau tanya pertanyaan lain?"
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
        """Simplified main method to process incoming messages"""
        print(f"🔥 ConversationEngine.process_message called")
        print(f"📝 Message: '{message}'")
        print(f"👤 User: {telegram_id}")
        print(f"📊 Engagement: {engagement_score}")
        
        # Detect language first
        language = self.detect_language(message)
        print(f"🌍 Detected language: {language}")
        
        intent = await self.detect_intent(message)
        print(f"🎯 Detected intent: {intent}")

        if intent == 'registration':
            # Generate registration link using built-in system
            registration_url = await self.generate_registration_link(telegram_id, telegram_username)
            
            if registration_url == "error":
                if language == 'ms':
                    return (
                        "🎯 Daftar Group Chat Fighter Rentung sekarang!\n\n"
                        "Untuk mendaftar, hubungi admin kami untuk proses pendaftaran.\n\n"
                        "Group Chat Fighter Rentung ada:\n"
                        "• Trading signals quality tinggi 📊\n"
                        "• Daily market analysis dari expert\n"
                        "• Tips broker terbaik untuk Malaysian\n"
                        "• Support dari experienced trader community"
                    )
                elif language == 'id':
                    return (
                        "🎯 Daftar Group Chat Fighter Rentung sekarang!\n\n"
                        "Untuk mendaftar, hubungi admin kami untuk proses pendaftaran.\n\n"
                        "Group Chat Fighter Rentung punya:\n"
                        "• Trading signal berkualitas tinggi 📊\n"
                        "• Analisis pasar harian dari expert\n"
                        "• Tips broker terbaik untuk Indonesia\n"
                        "• Support dari komunitas trader berpengalaman"
                    )
                else:
                    return (
                        "🎯 Register for Group Chat Fighter Rentung now!\n\n"
                        "To register, contact our admin for the registration process.\n\n"
                        "Our Group Chat Fighter Rentung offers:\n"
                        "• High-quality trading signals 📊\n"
                        "• Daily market analysis by experts\n"
                        "• Best broker tips for Malaysians\n"
                        "• Support from experienced trader community"
                    )
            
            if language == 'ms':
                return (
                    "🎯 Daftar Group Chat Fighter Rentung sekarang!\n\n"
                    "Group Chat Fighter Rentung ada:\n"
                    "• Trading signals quality tinggi 📊\n"
                    "• Daily market analysis dari expert (focus Asian + London session)\n"
                    "• Tips broker mana yang best untuk Malaysian\n"
                    "• Support dari experienced Malaysian trader community\n"
                    "• Strategy sesuai untuk working adults (lepas kerja trading)\n\n"
                    f"Klik link di bawah untuk lengkapkan pendaftaran:\n{registration_url}\n\n"
                    "⏰ Link ini akan expired dalam 30 minit.\n"
                    "Lepas register, team kita akan semak dan contact dalam 24-48 jam untuk Group Chat Fighter Rentung access!"
                )
            elif language == 'id':
                return (
                    "🎯 Daftar Group Chat Fighter Rentung sekarang!\n\n"
                    "Group Chat Fighter Rentung punya:\n"
                    "• Trading signal berkualitas tinggi 📊\n"
                    "• Analisis pasar harian dari expert (fokus sesi Asia + London)\n"
                    "• Tips broker mana yang terbaik untuk Indonesia\n"
                    "• Support dari komunitas trader Indonesia berpengalaman\n"
                    "• Strategi cocok untuk pekerja (trading setelah kerja)\n\n"
                    f"Klik link di bawah untuk melengkapi pendaftaran:\n{registration_url}\n\n"
                    "⏰ Link ini akan expired dalam 30 menit.\n"
                    "Setelah daftar, tim kami akan review dan menghubungi dalam 24-48 jam untuk akses Group Chat Fighter Rentung!"
                )
            else:
                return (
                    "🎯 Register for Group Chat Fighter Rentung now!\n\n"
                    "Our Group Chat Fighter Rentung offers:\n"
                    "• High-quality trading signals 📊\n"
                    "• Daily market analysis by experts\n"
                    "• Latest trading tips and strategies\n"
                    "• Support from experienced trader community\n"
                    "• Guidance to become a profitable trader 💰\n\n"
                    f"Click the link below to complete registration:\n{registration_url}\n\n"
                    "⏰ This link will expire in 30 minutes.\n"
                    "Once you register, our team will review and contact you within 24-48 hours for Group Chat Fighter Rentung access!"
                )
        
        elif intent == 'indicator_registration':
            # Handle indicator registration requests
            if language == 'ms':
                return (
                    "🎯 **High Level Engulfing Indicator Registration**\n\n"
                    "Dapatkan akses kepada indicator trading yang powerful!\n\n"
                    "🔥 **Apa yang anda dapat:**\n"
                    "• High Level Engulfing Indicator untuk MT4/MT5\n"
                    "• Complete setup guide dan tutorial\n"
                    "• Sokongan teknikal dari team kami\n"
                    "• Strategy panduan untuk maksimum profit\n\n"
                    "📝 **Untuk mendaftar, gunakan command:**\n"
                    "👉 `/indicator`\n\n"
                    "⏰ Proses pendaftaran mengambil masa 2-3 minit sahaja!\n"
                    "✅ Anda akan menerima akses setelah diluluskan admin."
                )
            elif language == 'id':
                return (
                    "🎯 **Registrasi High Level Engulfing Indicator**\n\n"
                    "Dapatkan akses ke indicator trading yang powerful!\n\n"
                    "🔥 **Apa yang Anda dapat:**\n"
                    "• High Level Engulfing Indicator untuk MT4/MT5\n"
                    "• Complete setup guide dan tutorial\n"
                    "• Support teknis dari tim kami\n"
                    "• Panduan strategi untuk profit maksimal\n\n"
                    "📝 **Untuk mendaftar, gunakan command:**\n"
                    "👉 `/indicator`\n\n"
                    "⏰ Proses registrasi hanya membutuhkan 2-3 menit!\n"
                    "✅ Anda akan mendapat akses setelah disetujui admin."
                )
            else:  # English
                return (
                    "🎯 **High Level Engulfing Indicator Registration**\n\n"
                    "Get access to powerful trading indicator!\n\n"
                    "🔥 **What you'll get:**\n"
                    "• High Level Engulfing Indicator for MT4/MT5\n"
                    "• Complete setup guide and tutorials\n"
                    "• Technical support from our team\n"
                    "• Strategy guidance for maximum profit\n\n"
                    "📝 **To register, use the command:**\n"
                    "👉 `/indicator`\n\n"
                    "⏰ Registration process takes only 2-3 minutes!\n"
                    "✅ You'll get access after admin approval."
                )

        elif intent == 'broker_inquiry':
            # Handle broker-specific inquiries with structured data
            return await self.handle_broker_inquiry(message, language)

        else:  # intent == 'ai_conversation'
            # All other conversations go to enhanced AI with smart context detection
            context = f"User engagement score: {engagement_score}"
            ai_response = await self.generate_ai_response(message, context, language)

            # Check if AI response is empty and provide fallback
            if not ai_response or ai_response.strip() == "":
                print(f"Empty AI response for question: {message[:50]}")
                if language == 'ms':
                    ai_response = (
                        "Maaf, saya ada masalah sikit nak process soalan awak tu. "
                        "Boleh try tanya dengan cara lain? Atau awak boleh tanya pasal "
                        "forex basics, broker recommendation, atau trading strategy!"
                    )
                elif language == 'id':
                    ai_response = (
                        "Maaf, saya ada masalah sedikit untuk proses pertanyaan Anda. "
                        "Bisa coba tanya dengan cara lain? Atau Anda bisa tanya tentang "
                        "forex basics, rekomendasi broker, atau strategi trading!"
                    )
                else:
                    ai_response = (
                        "Sorry, I'm having trouble processing your question right now. "
                        "Could you try asking it differently? Or ask about "
                        "forex basics, broker recommendations, or trading strategies!"
                    )

            # Add registration suggestion for highly engaged users (applies to all AI conversations)
            if await self.should_suggest_registration(engagement_score):
                registration_url = await self.generate_registration_link(telegram_id, telegram_username)
                if registration_url and registration_url != "already_registered" and registration_url != "error":
                    if language == 'ms':
                        ai_response += (
                            f"\n\n💡 Awak ni memang active bertanya! "
                            f"Nak join Group Chat Fighter Rentung untuk quality signals dan expert analysis? "
                            f"Klik sini: {registration_url}"
                        )
                    elif language == 'id':
                        ai_response += (
                            f"\n\n💡 Anda memang aktif bertanya! "
                            f"Mau join Group Chat Fighter Rentung untuk sinyal berkualitas dan analisis ahli? "
                            f"Klik di sini: {registration_url}"
                        )
                    else:
                        ai_response += (
                            f"\n\n💡 You're really engaged with learning! "
                            f"Want to join our Group Chat Fighter Rentung for quality signals and expert analysis? "
                            f"Click here: {registration_url}"
                        )

            return ai_response