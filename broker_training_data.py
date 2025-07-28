"""
Comprehensive Broker Training Data for Chatbot
Organized Q&A pairs, comparisons, and scenario-based responses
"""

# Question-Answer Pairs for Individual Brokers
BROKER_QA_PAIRS = {
    'octafx': {
        'spreads': {
            'question_en': "What are OctaFX's spreads for EUR/USD?",
            'question_ms': "Berapa spread OctaFX untuk EUR/USD?",
            'answer_en': "OctaFX offers EUR/USD spreads starting from 0.6 pips on average. Micro account: from 0.4 pips (variable) or 2.0 pips (fixed), Pro account: from 0.2 pips (variable), ECN account: from 0.0 pips (variable).",
            'answer_ms': "OctaFX ni spread EUR/USD dia average 0.6 pips lah. Kalau Micro account: dari 0.4 pip (variable) atau 2.0 pip (fixed), Pro account: dari 0.2 pip (variable), ECN account: dari 0.0 pip (variable). Not bad lah spread dia."
        },
        'minimum_deposit': {
            'question_en': "What is the minimum deposit for OctaFX?",
            'question_ms': "Berapa deposit minimum untuk OctaFX?",
            'answer_en': "OctaFX requires a minimum deposit of only $25 for all account types (Micro, Pro, and ECN accounts).",
            'answer_ms': "OctaFX ni deposit minimum USD25 je untuk semua akaun (Micro, Pro, ECN). Murah lah kalau convert RM, around RM100+ je. Okay lah untuk start."
        },
        'platforms': {
            'question_en': "Does OctaFX offer MetaTrader 5?",
            'question_ms': "OctaFX ada MT5 tak?",
            'answer_en': "Yes, OctaFX offers MetaTrader 5 (MT5) for Pro accounts, plus MetaTrader 4 (MT4) for Micro and ECN accounts, and their proprietary OctaTrader platform.",
            'answer_ms': "Ada lah! OctaFX bagi MT5 untuk Pro account, MT4 untuk Micro dan ECN account, plus ada platform sendiri OctaTrader. Complete package lah."
        },
        'regulation': {
            'question_en': "Is OctaFX regulated?",
            'question_ms': "OctaFX regulated ke?",
            'answer_en': "Yes, OctaFX is multi-regulated by CySEC (Cyprus), FSC (Mauritius), MISA (Comoros), and FSCA (South Africa), providing strong client protection.",
            'answer_ms': "Confirm regulated! Dia ada license dari CySEC (Cyprus), FSC (Mauritius), MISA (Comoros), dan FSCA (Afrika Selatan). Protection kita kuat lah dengan ni."
        },
        'leverage': {
            'question_en': "What leverage does OctaFX offer?",
            'question_ms': "OctaFX leverage berapa?",
            'answer_en': "OctaFX offers leverage up to 1:500 for Micro and ECN accounts, 1:200 for Pro accounts. International clients can get up to 1:1000, while EU clients are limited to 1:30 for major pairs.",
            'answer_ms': "OctaFX leverage sampai 1:500 untuk Micro dan ECN account, 1:200 untuk Pro account. Kalau international client boleh dapat 1:1000, tapi EU client limited 1:30 je untuk major pairs."
        }
    },

    'hfm': {
        'spreads': {
            'question_en': "What are HFM's spreads for EUR/USD?",
            'question_ms': "HFM spread EUR/USD berapa?",
            'answer_en': "HFM offers competitive EUR/USD spreads: Zero Account from 0.0 pips + $3 commission per side, Pro Account from 0.5 pips (no commission), Pro Plus from 0.2 pips (no commission), Cent/Premium from 1.2 pips (no commission).",
            'answer_ms': "HFM ni spread EUR/USD memang competitive: Zero Account 0.0 pip + USD3 commission per side, Pro Account 0.5 pip (no commission), Pro Plus 0.2 pip (no commission), Cent/Premium 1.2 pip (no commission). Best gila spread dia!"
        },
        'minimum_deposit': {
            'question_en': "What is the minimum deposit for HFM?",
            'question_ms': "HFM deposit minimum berapa?",
            'answer_en': "HFM offers $0 minimum deposit for most account types (Cent, Zero, Pro, Pro Plus, Premium accounts), making it very accessible for beginners.",
            'answer_ms': "HFM ni gempak - deposit minimum USD0 je untuk most account types (Cent, Zero, Pro, Pro Plus, Premium). Perfect lah untuk beginner yang nak try dulu."
        },
        'platforms': {
            'question_en': "Does HFM offer MetaTrader 5?",
            'question_ms': "HFM ada MT5 tak?",
            'answer_en': "Yes, HFM offers MetaTrader 5 (MT5) along with MetaTrader 4 (MT4), their proprietary HFM Platform, Web Terminal, and Multi Terminal.",
            'answer_ms': "Confirm ada! HFM provide MT5, MT4, HFM Platform sendiri, Web Terminal, Multi Terminal - lengkap gila platform dia. Pilih je mana yang comfortable."
        },
        'regulation': {
            'question_en': "Is HFM regulated?",
            'question_ms': "Adakah HFM dikawal selia?",
            'answer_en': "Yes, HFM is highly regulated by top-tier authorities: FCA (UK), CySEC (Cyprus), DFSA (UAE), FSC (Mauritius), FSCA (South Africa), with a trust score of 86/99.",
            'answer_ms': "Ya, HFM sangat dikawal selia oleh pihak berkuasa tertinggi: FCA (UK), CySEC (Cyprus), DFSA (UAE), FSC (Mauritius), FSCA (Afrika Selatan), dengan skor amanah 86/99."
        },
        'leverage': {
            'question_en': "What leverage does HFM offer?",
            'question_ms': "Berapa leverage yang ditawarkan HFM?",
            'answer_en': "HFM offers ultra-high leverage up to 1:2000 on all account types for maximum trading potential.",
            'answer_ms': "HFM menawarkan leverage ultra tinggi sehingga 1:2000 pada semua jenis akaun untuk potensi perdagangan maksimum."
        }
    },

    'valetax': {
        'spreads': {
            'question_en': "What are Valetax's spreads for EUR/USD?",
            'question_ms': "Berapa spread Valetax untuk EUR/USD?",
            'answer_en': "Valetax offers EUR/USD spreads from 0.0 pips on ECN account (+$4 commission per lot), from 0.6 pips on PRO account (no commission). However, spreads are not the most competitive in the market.",
            'answer_ms': "Valetax menawarkan spread EUR/USD dari 0.0 pip pada akaun ECN (+komisi $4 per lot), dari 0.6 pip pada akaun PRO (tiada komisi). Walau bagaimanapun, spread tidak paling kompetitif di pasaran."
        },
        'minimum_deposit': {
            'question_en': "What is the minimum deposit for Valetax?",
            'question_ms': "Berapa deposit minimum untuk Valetax?",
            'answer_en': "Valetax offers very low minimum deposits: Cent Account $1, Standard Account $10, ECN Account $50, PRO Account $500.",
            'answer_ms': "Valetax menawarkan deposit minimum yang sangat rendah: Akaun Cent $1, akaun Standard $10, akaun ECN $50, akaun PRO $500."
        },
        'platforms': {
            'question_en': "Does Valetax offer MetaTrader 5?",
            'question_ms': "Adakah Valetax menawarkan MetaTrader 5?",
            'answer_en': "Yes, Valetax offers both MetaTrader 4 (MT4) and MetaTrader 5 (MT5) platforms on Desktop, Mobile, and Web.",
            'answer_ms': "Ya, Valetax menawarkan kedua-dua platform MetaTrader 4 (MT4) dan MetaTrader 5 (MT5) pada Desktop, Mobile, dan Web."
        },
        'regulation': {
            'question_en': "Is Valetax regulated?",
            'question_ms': "Adakah Valetax dikawal selia?",
            'answer_en': "⚠️ WARNING: Valetax operates under offshore regulation (FSC Mauritius, SVG Commission). This provides limited client protection and there are concerns about license verification.",
            'answer_ms': "⚠️ AMARAN: Valetax beroperasi di bawah peraturan luar pesisir (FSC Mauritius, Suruhanjaya SVG). Ini memberikan perlindungan pelanggan yang terhad dan terdapat kebimbangan tentang pengesahan lesen."
        },
        'warnings': {
            'question_en': "Are there any warnings about Valetax?",
            'question_ms': "Adakah terdapat amaran tentang Valetax?",
            'answer_en': "⚠️ Yes, there are reports of withdrawal difficulties, mixed customer support reviews, and regulatory concerns. Users should exercise caution and do thorough research.",
            'answer_ms': "⚠️ Ya, terdapat laporan kesukaran pengeluaran, ulasan sokongan pelanggan bercampur, dan kebimbangan kawal selia. Pengguna harus berhati-hati dan melakukan penyelidikan menyeluruh."
        }
    },

    'dollars_markets': {
        'spreads': {
            'question_en': "What are Dollars Markets' spreads for EUR/USD?",
            'question_ms': "Berapa spread Dollars Markets untuk EUR/USD?",
            'answer_en': "Dollars Markets advertises competitive spreads from 0.0-0.1 pips on their Ultra account and from 0.1 pips on Standard account. However, based on user feedback, there have been concerns about execution quality and withdrawal processing that may affect overall trading costs.",
            'answer_ms': "Dollars Markets mengiklankan spread kompetitif dari 0.0-0.1 pip pada akaun Ultra dan dari 0.1 pip pada akaun Standard. Walau bagaimanapun, berdasarkan maklum balas pengguna, terdapat kebimbangan tentang kualiti pelaksanaan dan pemprosesan pengeluaran yang mungkin menjejaskan kos perdagangan keseluruhan."
        },
        'minimum_deposit': {
            'question_en': "What is the minimum deposit for Dollars Markets?",
            'question_ms': "Berapa deposit minimum untuk Dollars Markets?",
            'answer_en': "Dollars Markets offers low minimum deposits starting from $15 for Standard account and $50 for Pro account. While the entry barrier is low, traders should research the broker thoroughly and consider regulatory status before depositing funds.",
            'answer_ms': "Dollars Markets menawarkan deposit minimum rendah bermula dari $15 untuk akaun Standard dan $50 untuk akaun Pro. Walaupun halangan kemasukan rendah, pedagang harus menyelidik broker secara menyeluruh dan mempertimbangkan status kawal selia sebelum mendepositkan dana."
        },
        'platforms': {
            'question_en': "Does Dollars Markets offer MetaTrader 5?",
            'question_ms': "Adakah Dollars Markets menawarkan MetaTrader 5?",
            'answer_en': "Yes, Dollars Markets provides MT4, MT5, and cTrader platforms across desktop, mobile, and web versions. The platform selection is comprehensive, though users should verify execution quality and broker reliability.",
            'answer_ms': "Ya, Dollars Markets menyediakan platform MT4, MT5, dan cTrader merentasi versi desktop, mudah alih, dan web. Pemilihan platform adalah komprehensif, walaupun pengguna harus mengesahkan kualiti pelaksanaan dan kebolehpercayaan broker."
        },
        'regulation': {
            'question_en': "Is Dollars Markets regulated?",
            'question_ms': "Adakah Dollars Markets dikawal selia?",
            'answer_en': "Dollars Markets operates under offshore jurisdictions including claimed licenses from FSC Mauritius and SVG registration. Offshore regulation typically provides limited client protection compared to major financial centers. Traders should verify current regulatory status and understand the level of protection available.",
            'answer_ms': "Dollars Markets beroperasi di bawah bidang kuasa luar pesisir termasuk lesen yang didakwa dari FSC Mauritius dan pendaftaran SVG. Peraturan luar pesisir biasanya memberikan perlindungan pelanggan terhad berbanding pusat kewangan utama. Pedagang harus mengesahkan status kawal selia semasa dan memahami tahap perlindungan yang tersedia."
        },
        'user_feedback': {
            'question_en': "What do users say about Dollars Markets?",
            'question_ms': "Apa kata pengguna tentang Dollars Markets?",
            'answer_en': "User reviews for Dollars Markets are mixed, with some reporting challenges with withdrawal processing and customer service responsiveness. Some traders have experienced delays in fund withdrawals and account access issues. It's recommended to start with smaller amounts and thoroughly test withdrawal processes.",
            'answer_ms': "Ulasan pengguna untuk Dollars Markets bercampur-campur, dengan sesetengah melaporkan cabaran dengan pemprosesan pengeluaran dan responsif khidmat pelanggan. Sesetengah pedagang mengalami kelewatan dalam pengeluaran dana dan isu akses akaun. Disyorkan untuk bermula dengan jumlah yang lebih kecil dan menguji proses pengeluaran secara menyeluruh."
        },
        'risk_assessment': {
            'question_en': "What should I consider before choosing Dollars Markets?",
            'question_ms': "Apa yang harus saya pertimbangkan sebelum memilih Dollars Markets?",
            'answer_en': "Before choosing Dollars Markets, consider: 1) Offshore regulatory status with limited protection, 2) Mixed user feedback regarding withdrawals, 3) Customer service reliability, 4) Account access and fund security. Compare with more established brokers with stronger regulatory oversight for better security.",
            'answer_ms': "Sebelum memilih Dollars Markets, pertimbangkan: 1) Status kawal selia luar pesisir dengan perlindungan terhad, 2) Maklum balas pengguna bercampur mengenai pengeluaran, 3) Kebolehpercayaan khidmat pelanggan, 4) Akses akaun dan keselamatan dana. Bandingkan dengan broker yang lebih mapan dengan pengawasan kawal selia yang lebih kuat untuk keselamatan yang lebih baik."
        }
    }
}

# Comprehensive Comparison Tables
BROKER_COMPARISONS = {
    'spreads_commissions': {
        'title_en': "Spreads & Commissions Comparison",
        'title_ms': "Perbandingan Spread & Komisi",
        'data': {
            'OctaFX': {
                'eur_usd_spread': '0.6 pips avg (0.0-2.0 range)',
                'commission': 'None (spread-only)',
                'account_types': 'Micro: 0.4+, Pro: 0.2+, ECN: 0.0+',
                'rating': '⭐⭐⭐⭐⭐ Excellent'
            },
            'HFM': {
                'eur_usd_spread': '0.0-1.2 pips (varies by account)',
                'commission': '$3/side (Zero), None (others)',
                'account_types': 'Zero: 0.0+, Pro Plus: 0.2+, Pro: 0.5+',
                'rating': '⭐⭐⭐⭐⭐ Excellent'
            },
            'Valetax': {
                'eur_usd_spread': '0.0-0.6 pips',
                'commission': '$4/lot (ECN), None (PRO)',
                'account_types': 'ECN: 0.0+, PRO: 0.6+',
                'rating': '⭐⭐⭐ Average'
            },
            'Dollars Markets': {
                'eur_usd_spread': '0.0-0.1 pips (advertised)',
                'commission': '4% (Ultra), None (Standard)',
                'account_types': 'Ultra: 0.02+, Standard: 0.1+',
                'rating': '⚠️ Mixed Reviews - Research Required'
            }
        }
    },

    'deposits_accounts': {
        'title_en': "Account Types & Minimum Deposits",
        'title_ms': "Jenis Akaun & Deposit Minimum",
        'data': {
            'OctaFX': {
                'min_deposit': '$25 all accounts',
                'account_types': 'Micro (MT4), Pro (MT5), ECN',
                'currencies': 'Multiple supported',
                'demo': 'Unlimited demo accounts',
                'swap_free': 'Swap-free available'
            },
            'HFM': {
                'min_deposit': '$0 most accounts',
                'account_types': 'Cent, Zero, Pro, Pro Plus, Premium',
                'currencies': 'USD, EUR, NGN, JPY',
                'demo': 'Free demo accounts',
                'swap_free': 'Swap-free available'
            },
            'Valetax': {
                'min_deposit': '$1-$500 (varies)',
                'account_types': 'Cent ($1), Standard ($10), ECN ($50), PRO ($500)',
                'currencies': 'Limited information',
                'demo': 'Available',
                'swap_free': 'Available'
            },
            'Dollars Markets': {
                'min_deposit': '$10-$50 (varies)',
                'account_types': 'Standard ($15), Pro ($50), Ultra',
                'currencies': 'Multiple claimed',
                'demo': 'Available',
                'swap_free': 'Claimed (⚠️ Not recommended)'
            }
        }
    },

    'platforms': {
        'title_en': "Trading Platforms Comparison",
        'title_ms': "Perbandingan Platform Perdagangan",
        'data': {
            'OctaFX': {
                'mt4': '✅ Yes',
                'mt5': '✅ Yes',
                'proprietary': '✅ OctaTrader',
                'mobile': '✅ Full-featured apps',
                'web': '✅ Web trading',
                'api': '✅ Available'
            },
            'HFM': {
                'mt4': '✅ Yes',
                'mt5': '✅ Yes',
                'proprietary': '✅ HFM Platform',
                'mobile': '✅ Full-featured apps',
                'web': '✅ Web Terminal',
                'api': '✅ Available'
            },
            'Valetax': {
                'mt4': '✅ Yes',
                'mt5': '✅ Yes',
                'proprietary': '❌ No',
                'mobile': '✅ Android/iOS',
                'web': '✅ Web trading',
                'api': '✅ Via MT platforms'
            },
            'Dollars Markets': {
                'mt4': '✅ Yes',
                'mt5': '✅ Yes',
                'proprietary': '✅ cTrader',
                'mobile': '✅ Available',
                'web': '✅ Available',
                'api': '✅ Available'
            }
        }
    },

    'regulation': {
        'title_en': "Regulatory Status Comparison",
        'title_ms': "Perbandingan Status Kawal Selia",
        'data': {
            'OctaFX': {
                'primary_regulators': 'CySEC, FSC, MISA, FSCA',
                'protection_level': '🟢 High Protection',
                'segregated_funds': '✅ Yes',
                'compensation': '✅ Varies by jurisdiction',
                'trust_rating': '⭐⭐⭐⭐⭐ Excellent (4.4/5)',
                'recommendation': '🟢 HIGHLY RECOMMENDED'
            },
            'HFM': {
                'primary_regulators': 'FCA, CySEC, DFSA, FSC, FSCA',
                'protection_level': '🟢 Highest Protection',
                'segregated_funds': '✅ Yes',
                'compensation': '✅ Multiple schemes',
                'trust_rating': '⭐⭐⭐⭐⭐ Excellent (86/99)',
                'recommendation': '🟢 HIGHLY RECOMMENDED'
            },
            'Valetax': {
                'primary_regulators': 'FSC Mauritius, SVG',
                'protection_level': '🟡 Limited Protection',
                'segregated_funds': '⚠️ Limited info',
                'compensation': '⚠️ Offshore protection only',
                'trust_rating': '⭐⭐⭐ Mixed reviews',
                'recommendation': '🟡 CAUTION ADVISED'
            },
            'Dollars Markets': {
                'primary_regulators': 'Offshore (FSC Mauritius claimed, SVG)',
                'protection_level': '🟡 Limited Offshore Protection',
                'segregated_funds': '⚠️ Not clearly verified',
                'compensation': '⚠️ Limited offshore schemes',
                'trust_rating': '⭐⭐ Mixed User Feedback',
                'recommendation': '🟡 RESEARCH THOROUGHLY BEFORE CHOOSING'
            }
        }
    }
}

# Scenario-Based Recommendations
SCENARIO_RECOMMENDATIONS = {
    'beginner_trader': {
        'title_en': "Best Brokers for Beginner Traders",
        'title_ms': "Broker Terbaik untuk Trader Pemula",
        'recommendations': {
            '1st_choice': {
                'broker': 'HFM',
                'reasons_en': [
                    "$0 minimum deposit - perfect for starting small",
                    "Cent account allows trading with cents instead of dollars",
                    "Multiple regulatory licenses provide safety",
                    "Comprehensive educational resources",
                    "24/5 customer support",
                    "Negative balance protection"
                ],
                'reasons_ms': [
                    "Deposit minimum $0 - sempurna untuk bermula kecil",
                    "Akaun Cent membolehkan perdagangan dengan sen bukannya dolar",
                    "Pelbagai lesen kawal selia memberikan keselamatan",
                    "Sumber pendidikan komprehensif",
                    "Sokongan pelanggan 24/5",
                    "Perlindungan baki negatif"
                ]
            },
            '2nd_choice': {
                'broker': 'OctaFX',
                'reasons_en': [
                    "Low $25 minimum deposit",
                    "Excellent reputation with 60+ awards",
                    "Strong regulatory protection",
                    "User-friendly platforms",
                    "No commission on most accounts",
                    "Great customer reviews (4.4/5)"
                ],
                'reasons_ms': [
                    "Deposit minimum rendah $25",
                    "Reputasi cemerlang dengan 60+ anugerah",
                    "Perlindungan kawal selia yang kuat",
                    "Platform mesra pengguna",
                    "Tiada komisi pada kebanyakan akaun",
                    "Ulasan pelanggan hebat (4.4/5)"
                ]
            },
            'consider_carefully': {
                'brokers': ['Valetax', 'Dollars Markets'],
                'reasons_en': "Research thoroughly due to offshore regulation and mixed user feedback. Consider starting with established brokers for better security.",
                'reasons_ms': "Selidik dengan teliti kerana peraturan luar pesisir dan maklum balas pengguna bercampur. Pertimbangkan untuk bermula dengan broker yang mapan untuk keselamatan yang lebih baik."
            }
        }
    },

    'high_volume_trader': {
        'title_en': "Best Brokers for High-Volume Traders",
        'title_ms': "Broker Terbaik untuk Trader Volume Tinggi",
        'recommendations': {
            '1st_choice': {
                'broker': 'HFM Zero Account',
                'reasons_en': [
                    "Raw spreads from 0.0 pips",
                    "Low commission ($3 per side)",
                    "High leverage up to 1:2000",
                    "Direct market access",
                    "Professional-grade execution",
                    "Multiple top-tier regulations"
                ],
                'reasons_ms': [
                    "Spread mentah dari 0.0 pip",
                    "Komisi rendah ($3 per sisi)",
                    "Leverage tinggi sehingga 1:2000",
                    "Akses pasaran langsung",
                    "Pelaksanaan gred profesional",
                    "Pelbagai peraturan peringkat atas"
                ]
            },
            '2nd_choice': {
                'broker': 'OctaFX ECN',
                'reasons_en': [
                    "Spreads from 0.0 pips",
                    "ECN execution model",
                    "Strong regulatory backing",
                    "Reliable platform performance",
                    "Good liquidity providers"
                ],
                'reasons_ms': [
                    "Spread dari 0.0 pip",
                    "Model pelaksanaan ECN",
                    "Sokongan kawal selia yang kuat",
                    "Prestasi platform yang boleh dipercayai",
                    "Pembekal kecairan yang baik"
                ]
            }
        }
    },

    'scalping_friendly': {
        'title_en': "Best Brokers for Scalping",
        'title_ms': "Broker Terbaik untuk Scalping",
        'recommendations': {
            '1st_choice': {
                'broker': 'HFM Zero Account',
                'reasons_en': [
                    "Ultra-tight spreads from 0.0 pips",
                    "Fast execution speeds",
                    "No restrictions on scalping",
                    "Low latency trading",
                    "Professional trading tools"
                ],
                'reasons_ms': [
                    "Spread ultra ketat dari 0.0 pip",
                    "Kelajuan pelaksanaan pantas",
                    "Tiada sekatan pada scalping",
                    "Perdagangan latency rendah",
                    "Alat perdagangan profesional"
                ]
            },
            '2nd_choice': {
                'broker': 'OctaFX ECN',
                'reasons_en': [
                    "Zero spreads available",
                    "ECN execution model",
                    "No dealing desk interference",
                    "Scalping-friendly policies"
                ],
                'reasons_ms': [
                    "Spread sifar tersedia",
                    "Model pelaksanaan ECN",
                    "Tiada campur tangan dealing desk",
                    "Dasar mesra scalping"
                ]
            },
            'consideration': {
                'text_en': "⚠️ For scalping, prioritize brokers with proven execution reliability. Valetax and Dollars Markets have mixed reviews regarding execution and withdrawal processing.",
                'text_ms': "⚠️ Untuk scalping, utamakan broker dengan kebolehpercayaan pelaksanaan yang terbukti. Valetax dan Dollars Markets mempunyai ulasan bercampur mengenai pelaksanaan dan pemprosesan pengeluaran."
            }
        }
    },

    'long_term_investment': {
        'title_en': "Best Brokers for Long-Term Trading",
        'title_ms': "Broker Terbaik untuk Perdagangan Jangka Panjang",
        'recommendations': {
            '1st_choice': {
                'broker': 'OctaFX',
                'reasons_en': [
                    "Excellent regulatory track record",
                    "Strong financial stability",
                    "Transparent operations",
                    "Swap-free accounts available",
                    "Long-term reputation (since 2011)",
                    "Multiple regulatory protections"
                ],
                'reasons_ms': [
                    "Rekod jejak kawal selia cemerlang",
                    "Kestabilan kewangan yang kuat",
                    "Operasi telus",
                    "Akaun bebas swap tersedia",
                    "Reputasi jangka panjang (sejak 2011)",
                    "Pelbagai perlindungan kawal selia"
                ]
            },
            '2nd_choice': {
                'broker': 'HFM',
                'reasons_en': [
                    "Top-tier regulatory licenses",
                    "Established since 2010",
                    "Strong client fund protection",
                    "Swap-free options available",
                    "Reliable customer service"
                ],
                'reasons_ms': [
                    "Lesen kawal selia peringkat atas",
                    "Ditubuhkan sejak 2010",
                    "Perlindungan dana pelanggan yang kuat",
                    "Pilihan bebas swap tersedia",
                    "Perkhidmatan pelanggan yang boleh dipercayai"
                ]
            },
            'critical_factors': {
                'text_en': "For long-term trading, prioritize: 1) Strong regulation, 2) Financial stability, 3) Transparent operations, 4) Good customer service",
                'text_ms': "Untuk perdagangan jangka panjang, utamakan: 1) Peraturan kuat, 2) Kestabilan kewangan, 3) Operasi telus, 4) Perkhidmatan pelanggan yang baik"
            }
        }
    }
}

# Quick Comparison Functions
def get_broker_comparison_summary():
    """Get a quick summary comparison of all brokers"""
    return {
        'best_overall': 'HFM - Multiple top regulations, $0 deposit, excellent features',
        'most_trusted': 'OctaFX - 4.4/5 rating, 60+ awards, strong reputation',
        'highest_risk': 'Dollars Markets - No valid regulation, withdrawal issues reported',
        'beginner_friendly': 'HFM - $0 deposit, cent accounts, comprehensive support',
        'professional_trading': 'HFM Zero Account - 0.0 spreads, direct market access'
    }

def get_safety_rankings():
    """Get brokers ranked by safety and regulation"""
    return {
        '1st_safest': {
            'broker': 'HFM',
            'score': '9.5/10',
            'reasons': 'FCA, CySEC, DFSA regulation, trust score 86/99'
        },
        '2nd_safest': {
            'broker': 'OctaFX', 
            'score': '9.0/10',
            'reasons': 'Multi-regulated, excellent reviews, strong reputation'
        },
        '3rd_safest': {
            'broker': 'Valetax',
            'score': '5.0/10',
            'reasons': 'Offshore regulation, mixed reviews, withdrawal concerns'
        },
        'unsafe': {
            'broker': 'Dollars Markets',
            'score': '1.0/10',
            'reasons': 'No valid regulation, multiple fraud reports, avoid completely'
        }
    }