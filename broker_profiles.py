"""
Comprehensive Forex Broker Profiles
Updated: January 2025

This module contains detailed information about forex brokers to help answer client questions
about trading conditions, features, and broker comparisons.
"""

BROKER_PROFILES = {
    'octafx': {
        'name': 'OctaFX (Octa)',
        'established': 2011,
        'overview': 'Award-winning, globally reputed, multi-regulated, multi-asset broker serving over 42 million trading accounts in more than 180 countries.',

        'regulation': {
            'primary_regulators': ['CySEC (Cyprus)', 'FSC (Mauritius)', 'MISA (Comoros)', 'FSCA (South Africa)'],
            'licenses': {
                'CySEC': 'European regulation for EU clients',
                'FSC': 'Mauritius Financial Services Commission',
                'MISA': 'Mwali International Services Authority',
                'FSCA': 'Financial Sector Conduct Authority (South Africa)'
            },
            'client_protection': {
                'segregated_accounts': True,
                'negative_balance_protection': True,
                'compensation_scheme': 'Varies by jurisdiction'
            }
        },

        'trading_conditions': {
            'account_types': {
                'Micro (MT4)': {
                    'minimum_deposit': '$25',
                    'spreads': 'From 0.4 pips (variable), 2.0 pips (fixed)',
                    'leverage': 'Up to 1:500 (1:1000 international, 1:30 EU)',
                    'commission': 'None (spread-only)',
                    'platform': 'MetaTrader 4'
                },
                'Pro (MT5)': {
                    'minimum_deposit': '$25',
                    'spreads': 'From 0.2 pips (variable)',
                    'leverage': 'Up to 1:200 (currencies), 1:100 (metals)',
                    'commission': 'None (spread-only)',
                    'platform': 'MetaTrader 5'
                },
                'ECN': {
                    'minimum_deposit': '$25',
                    'spreads': 'From 0.0 pips (variable)',
                    'leverage': 'Up to 1:500',
                    'commission': 'Yes (ECN model)',
                    'platform': 'MetaTrader 4/5'
                }
            },
            'instruments': '300+ instruments across forex, CFDs, metals, energies',
            'minimum_trade_size': '0.01 lots',
            'maximum_leverage': {
                'international': '1:1000',
                'european': '1:30 (major pairs)',
                'currencies': '1:500 (Micro/ECN), 1:200 (Pro)',
                'metals': '1:200'
            }
        },

        'platforms_tools': {
            'trading_platforms': ['MetaTrader 4', 'MetaTrader 5', 'OctaTrader (proprietary)'],
            'mobile_apps': 'Full-featured mobile trading apps',
            'copy_trading': 'Available',
            'automated_trading': 'Expert Advisors supported',
            'charting_tools': 'Advanced charting with technical indicators',
            'api_access': 'Available for algorithmic trading'
        },

        'services_support': {
            'deposit_methods': ['Bank wire', 'Credit/debit cards', 'E-wallets', 'Local payment methods'],
            'withdrawal_methods': 'Same as deposit methods',
            'processing_times': {
                'deposits': 'Instant for most methods',
                'withdrawals': '1-3 business days'
            },
            'customer_support': '24/7 multilingual support',
            'educational_resources': 'Comprehensive trading education',
            'bonuses': 'Various deposit bonuses and promotions available'
        },

        'account_features': {
            'swap_free_accounts': 'Swap-free accounts available',
            'demo_accounts': 'Unlimited demo accounts',
            'vps_services': 'Virtual Private Server available',
            'negative_balance_protection': True,
            'segregated_funds': True
        },

        'trust_rating': {
            'trustpilot': '4.4/5 (8000+ reviews)',
            'industry_awards': '60+ forex industry awards',
            'overall_assessment': 'Highly trusted, well-established broker'
        },

        'pros': [
            'Multi-regulated by top-tier authorities',
            'Very low minimum deposit ($25)',
            'Competitive spreads from 0.0 pips',
            'No trading commissions on most accounts',
            'Strong client protection measures',
            'Excellent customer reviews',
            'Wide range of trading instruments'
        ],

        'cons': [
            'Limited educational resources compared to some competitors',
            'Leverage restrictions for EU clients',
            'Fixed spreads higher than variable spreads'
        ]
    },

    'hfm': {
        'name': 'HFM (HotForex)',
        'established': 2010,
        'overview': 'Award-winning forex and commodities broker with over 3.5 million live accounts, serving clients globally with 200+ employees and 27+ language support.',

        'regulation': {
            'primary_regulators': ['FCA (UK)', 'CySEC (Cyprus)', 'DFSA (UAE)', 'FSC (Mauritius)', 'FSCA (South Africa)'],
            'licenses': {
                'FCA': 'Financial Conduct Authority (UK)',
                'CySEC': 'Cyprus Securities and Exchange Commission',
                'DFSA': 'Dubai Financial Services Authority',
                'FSC': 'Financial Services Commission (Mauritius)',
                'FSCA': 'Financial Sector Conduct Authority (South Africa)'
            },
            'trust_score': '86/99',
            'client_protection': {
                'segregated_accounts': True,
                'negative_balance_protection': True,
                'compensation_scheme': 'Varies by jurisdiction'
            }
        },

        'trading_conditions': {
            'account_types': {
                'Cent Account': {
                    'minimum_deposit': '$0',
                    'spreads': 'From 1.2 pips',
                    'leverage': 'Up to 1:2000',
                    'commission': 'None',
                    'features': 'Ultra-low capital requirements, swap-free option'
                },
                'Zero Account': {
                    'minimum_deposit': '$0',
                    'spreads': 'From 0.0 pips',
                    'leverage': 'Up to 1:2000',
                    'commission': '$3 per side per lot (currencies)',
                    'features': 'Direct market access, no hidden spreads'
                },
                'Pro Account': {
                    'minimum_deposit': '$0',
                    'spreads': 'From 0.5 pips',
                    'leverage': 'Up to 1:2000',
                    'commission': 'None',
                    'features': 'Low spreads, no commission'
                },
                'Pro Plus Account': {
                    'minimum_deposit': '$0',
                    'spreads': 'From 0.2 pips',
                    'leverage': 'Up to 1:2000',
                    'commission': 'None',
                    'features': 'Professional-grade account'
                },
                'Premium Account': {
                    'minimum_deposit': '$0',
                    'spreads': 'From 1.2 pips',
                    'leverage': 'Up to 1:2000',
                    'commission': 'None',
                    'features': 'Standard premium features'
                }
            },
            'instruments': 'Forex, Metals, Energies, Indices, CFD Stocks, Commodities, Cryptocurrency, Bonds, ETFs',
            'minimum_trade_size': '0.01 lots',
            'maximum_leverage': 'Up to 1:2000'
        },

        'platforms_tools': {
            'trading_platforms': ['HFM Platform (proprietary)', 'MetaTrader 4', 'MetaTrader 5', 'Web Terminal', 'Multi Terminal'],
            'mobile_apps': 'Full-featured mobile trading',
            'copy_trading': 'Available',
            'automated_trading': 'Expert Advisors and algorithmic trading',
            'charting_tools': 'Advanced charting and technical analysis',
            'api_access': 'Available'
        },

        'services_support': {
            'deposit_methods': ['Bank transfers', 'Credit/debit cards', 'E-wallets', 'Cryptocurrency'],
            'withdrawal_methods': 'Same as deposit methods',
            'processing_times': {
                'deposits': 'Instant for most methods',
                'withdrawals': 'May take longer than advertised'
            },
            'customer_support': '24/5 support (not weekends)',
            'educational_resources': 'Comprehensive trading education',
            'bonuses': 'Various promotional offers'
        },

        'account_features': {
            'swap_free_accounts': 'Swap-free accounts available',
            'demo_accounts': 'Free demo accounts',
            'vps_services': 'Available',
            'negative_balance_protection': True,
            'supported_currencies': ['USD', 'EUR', 'NGN', 'JPY']
        },

        'pros': [
            'Multiple top-tier regulatory licenses',
            'Zero minimum deposit on most accounts',
            'Ultra-high leverage up to 1:2000',
            'Tight spreads from 0.0 pips',
            'Wide range of trading instruments',
            'Multiple account types for different needs',
            'Strong regulatory compliance'
        ],

        'cons': [
            'Trading costs slightly above average on spread-only accounts',
            'Withdrawal processing may be delayed',
            'No weekend customer support',
            'Limited currency options for accounts'
        ]
    },

    'valetax': {
        'name': 'Valetax',
        'established': 'Recent (exact year unclear)',
        'overview': '''Apa itu Valetax?
Valetax ialah sebuah broker forex berasaskan STP (Straight Through Processing) yang mendakwa mempunyai lebih 300,000 pelanggan di lebih 15 negara.

Perlesenan dan keselamatan dana
Valetax berdaftar di Mauritius dan Saint Vincent & Grenadines serta mempunyai lesen dari badan pengawal kewangan di Mauritius. Walau bagaimanapun, lesen dari negara-negara ini dianggap sebagai offshore dan tidak memberikan perlindungan pelabur seperti badan pengawal selia Tier‑1 seperti FCA (UK) atau ASIC (Australia).

Jenis akaun & syarat perdagangan
Valetax menawarkan beberapa jenis akaun seperti Cent, Standard, ECN, Booster, Bonus dan PRO. Deposit minimum bermula dari USD 1 sehingga USD 500. Leverage yang ditawarkan boleh mencecah sehingga 1:2000, dan platform dagangan yang digunakan adalah MetaTrader 4 dan 5.

Kaedah pembayaran dan proses kewangan
Valetax menyokong pelbagai kaedah deposit termasuk perbankan dalam talian dari bank-bank tempatan dan stablecoin seperti USDT. Deposit biasanya diproses serta-merta, manakala pengeluaran memerlukan jumlah minimum dan mungkin mengambil sedikit masa.

Kelebihan:
• Deposit permulaan yang rendah
• Leverage tinggi
• Pilihan platform dagangan MT4 dan MT5
• Pelbagai jenis akaun untuk pelbagai keperluan trader

Kekurangan:
• Lesen dari negara offshore, kurang perlindungan pengguna
• Terdapat aduan berkaitan pengeluaran dan khidmat pelanggan
• Kekurangan bahan pembelajaran dan analisis pasaran

Kesimpulan
Valetax menawarkan syarat perdagangan yang menarik untuk pengguna baru atau yang ingin mencuba. Namun, kekurangan pengawasan ketat dan risiko dalam aspek pengeluaran menjadikan ia sesuai hanya untuk mereka yang faham risiko dagangan dan tidak menggunakan modal besar.

Untuk Golongan B40 (Gaya bahasa santai dan mudah faham)

Apa benda Valetax ni?
Valetax ni satu platform untuk trade mata wang dan kripto. Ramai orang dah guna, dan katanya mudah nak mula – boleh mula dengan USD 1 je.

Selamat ke guna?
Dia ada lesen, tapi bukan dari negara besar macam UK atau Australia. Jadi, kalau duit hilang atau ada masalah, susah sikit nak dapat bantuan atau jaminan keselamatan.

Senang ke nak mula?
Ya, senang. Ada banyak jenis akaun ikut bajet dan pengalaman. Kalau baru nak cuba, boleh pilih akaun murah dulu. Leverage pun tinggi – maksudnya boleh guna duit sikit tapi trade macam banyak.

Macam mana nak tambah & keluarkan duit?
Boleh guna bank online Malaysia atau USDT (mata wang digital). Masuk duit cepat, tapi nak keluarkan kadang-kadang ambil masa. Kena ada minimum USD 50 untuk keluarkan.''',

        'regulation': {
            'primary_regulators': ['FSC (Mauritius)', 'SVG Commission'],
            'licenses': {
                'FSC': 'Financial Services Commission Mauritius (License: GB21026312)',
                'SVG': 'Saint Vincent and the Grenadines Commission'
            },
            'regulatory_concerns': 'Offshore regulation provides limited protection. License verification concerns reported.',
            'client_protection': {
                'segregated_accounts': 'Limited information',
                'negative_balance_protection': True,
                'compensation_scheme': 'Limited offshore protection'
            }
        },

        'trading_conditions': {
            'account_types': {
                'Cent Account': {
                    'minimum_deposit': '$1',
                    'spreads': 'Variable',
                    'leverage': 'Up to 1:1000',
                    'commission': 'None',
                    'features': 'Designed for beginners'
                },
                'Standard Account': {
                    'minimum_deposit': '$10',
                    'spreads': 'Variable',
                    'leverage': 'Up to 1:2000',
                    'commission': 'None',
                    'features': 'For experienced traders'
                },
                'ECN Account': {
                    'minimum_deposit': '$50',
                    'spreads': 'From 0.0 pips',
                    'leverage': 'Up to 1:2000',
                    'commission': '$4 per lot',
                    'features': 'Raw spreads for professionals'
                },
                'PRO Account': {
                    'minimum_deposit': '$500',
                    'spreads': 'From 0.6 pips',
                    'leverage': 'Up to 1:2000',
                    'commission': 'None',
                    'features': 'High-volume traders'
                }
            },
            'instruments': '60+ forex pairs, indices, metals, crypto, energies (6 asset classes)',
            'minimum_trade_size': '0.01 lots',
            'maximum_leverage': 'Up to 1:2000'
        },

        'platforms_tools': {
            'trading_platforms': ['MetaTrader 4', 'MetaTrader 5'],
            'mobile_apps': 'Android/iOS mobile apps',
            'copy_trading': 'Limited information',
            'automated_trading': 'Expert Advisors supported',
            'charting_tools': 'Standard MT4/MT5 tools',
            'api_access': 'Available through MT platforms'
        },

        'services_support': {
            'deposit_methods': ['Bank transfers', 'E-wallets (no card payments)'],
            'withdrawal_methods': 'Same as deposits',
            'processing_times': {
                'deposits': 'Varies',
                'withdrawals': 'Reports of delays and difficulties'
            },
            'customer_support': '24/7 claimed (mixed reviews)',
            'educational_resources': 'Limited - no educational resources provided',
            'bonuses': 'Various promotional offers'
        },

        'account_features': {
            'swap_free_accounts': 'Available',
            'demo_accounts': 'Available',
            'vps_services': 'Information not available',
            'negative_balance_protection': True,
            'no_fees': 'No account maintenance or payment processing fees'
        },

        'pros': [
            'Very low minimum deposit ($1)',
            'High leverage up to 1:2000',
            'Multiple account types',
            'Cent accounts for risk reduction',
            'No non-trading fees',
            'Negative balance protection'
        ],

        'cons': [
            'Offshore regulation with limited protection',
            'Reports of withdrawal difficulties',
            'No educational resources',
            'Limited payment options (no cards)',
            'Mixed customer support reviews',
            'Website lacks market analysis tools',
            'Spreads not highly competitive'
        ],

        'warnings': [
            'Multiple user complaints about withdrawal issues',
            'Regulatory concerns about license verification',
            'Limited investor protection due to offshore status'
        ]
    },

    'dollars_markets': {
        'name': 'Dollars Markets',
        'established': 'Recent',
        'overview': 'Global forex and CFD broker operating under offshore jurisdictions with high leverage and low spreads.',

        'regulation': {
            'primary_regulators': ['FSC (Mauritius)', 'SVG Registration'],
            'licenses': {
                'FSC': 'Financial Services Commission (Mauritius)',
                'SVG': 'Saint Vincent and the Grenadines (Registration only)'
            },
            'regulatory_status': 'No valid regulation verified - operates in offshore jurisdictions',
            'client_protection': {
                'segregated_accounts': 'Limited information',
                'negative_balance_protection': 'Unclear',
                'compensation_scheme': 'No meaningful protection'
            }
        },

        'trading_conditions': {
            'account_types': {
                'Standard Account': {
                    'minimum_deposit': '$15 (recommended $200)',
                    'spreads': 'From 0.1 pips',
                    'leverage': 'Up to 1:3000',
                    'commission': 'None',
                    'features': 'Commission-free trading'
                },
                'Pro Account': {
                    'minimum_deposit': '$50 (recommended $500)',
                    'spreads': 'From 0.0 pips',
                    'leverage': 'Up to 1:3000',
                    'commission': '4% on FX and metals',
                    'features': 'Zero spreads with commission'
                },
                'Ultra Account': {
                    'minimum_deposit': 'Variable',
                    'spreads': 'From 0.02 pips',
                    'leverage': 'Up to 1:3000',
                    'commission': '4% on FX and metals',
                    'features': 'Lowest spreads available'
                }
            },
            'instruments': '400+ instruments including forex, indices, stocks, metals, energies, cryptocurrencies, ETFs',
            'minimum_trade_size': '0.01 lots',
            'maximum_leverage': 'Up to 1:3000 (among highest in industry)'
        },

        'platforms_tools': {
            'trading_platforms': ['MetaTrader 4', 'MetaTrader 5', 'cTrader'],
            'mobile_apps': 'Available on mobile and web',
            'copy_trading': 'Available',
            'automated_trading': 'Expert Advisors supported',
            'charting_tools': 'Advanced charting tools',
            'api_access': 'Available'
        },

        'services_support': {
            'deposit_methods': ['Bank transfers', 'Credit/debit cards', 'E-wallets'],
            'withdrawal_methods': 'Same as deposits',
            'processing_times': {
                'deposits': 'Claimed to be fast',
                'withdrawals': 'Major issues reported - delays and blocks'
            },
            'customer_support': 'Claimed 24/7 (poor responsiveness reported)',
            'educational_resources': 'Limited',
            'bonuses': 'Various promotional offers'
        },

        'account_features': {
            'swap_free_accounts': 'Available',
            'demo_accounts': 'Available',
            'vps_services': 'Available',
            'negative_balance_protection': 'Claimed',
            'account_suspension': 'Risk of account suspension reported'
        },

        'pros': [
            'Very high leverage up to 1:3000',
            'Low spreads from 0.0 pips',
            'Low minimum deposit requirements',
            'Wide range of trading instruments',
            'Multiple popular trading platforms',
            'Various account types'
        ],

        'cons': [
            'No valid regulation - high risk',
            'Serious withdrawal issues reported',
            'Account blocking and suspension reports',
            'Poor customer support responsiveness',
            'Offshore jurisdiction with no protection'
        ],

        'major_warnings': [
            '⚠️ CRITICAL: Multiple reports of withdrawal blocks and account suspensions',
            '⚠️ No valid regulatory protection',
            '⚠️ Suspected fraudulent practices when accounts become profitable',
            '⚠️ Users report losing capital after successful trading',
            '⚠️ Extreme caution advised - high risk broker'
        ]
    }
}

def get_broker_info(broker_name):
    """Get broker information by name"""
    broker_key = broker_name.lower().replace(' ', '_')
    return BROKER_PROFILES.get(broker_key)

def get_all_brokers():
    """Get list of all available brokers"""
    return list(BROKER_PROFILES.keys())

def compare_brokers(broker1, broker2):
    """Compare two brokers side by side"""
    b1 = get_broker_info(broker1)
    b2 = get_broker_info(broker2)

    if not b1 or not b2:
        return None

    comparison = {
        'broker1': b1['name'],
        'broker2': b2['name'],
        'regulation': {
            'broker1': b1['regulation']['primary_regulators'],
            'broker2': b2['regulation']['primary_regulators']
        },
        'min_deposit': {
            'broker1': list(b1['trading_conditions']['account_types'].values())[0]['minimum_deposit'],
            'broker2': list(b2['trading_conditions']['account_types'].values())[0]['minimum_deposit']
        },
        'max_leverage': {
            'broker1': b1['trading_conditions']['maximum_leverage'],
            'broker2': b2['trading_conditions']['maximum_leverage']
        },
        'platforms': {
            'broker1': b1['platforms_tools']['trading_platforms'],
            'broker2': b2['platforms_tools']['trading_platforms']
        }
    }

    return comparison