-- EzyAssist Test Data
-- 15 realistic test registrations: 10 verified, 5 rejected

-- Insert verified users (10)
INSERT INTO vip_registrations (
    telegram_id, telegram_username, full_name, email, phone_number, 
    client_id, brokerage_name, deposit_amount, status, ip_address, 
    user_agent, created_at, status_updated_at, updated_by_admin
) VALUES 
-- Verified User 1
('1234567890', 'ahmad_trader', 'Ahmad Bin Abdullah', 'ahmad.abdullah@gmail.com', '+60123456789', 
 'EXNESS_MY_001', 'Exness', 500, 'verified', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days', 'admin'),

-- Verified User 2
('2345678901', 'siti_forex', 'Siti Nurhaliza Binti Rashid', 'siti.nurhaliza@yahoo.com', '+60198765432', 
 'XM_MY_002', 'XM Global', 750, 'verified', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '8 days', NOW() - INTERVAL '7 days', 'admin'),

-- Verified User 3
('3456789012', 'mohd_profit', 'Mohammad Hafiz Bin Omar', 'hafiz.omar@hotmail.com', '+60187654321', 
 'FXCM_MY_003', 'FXCM', 300, 'verified', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '12 days', NOW() - INTERVAL '11 days', 'admin'),

-- Verified User 4
('4567890123', 'farah_trading', 'Farah Aisyah Binti Zainal', 'farah.aisyah@gmail.com', '+60176543210', 
 'IC_MARKETS_004', 'IC Markets', 1000, 'verified', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '3 days', NOW() - INTERVAL '2 days', 'admin'),

-- Verified User 5
('5678901234', 'azman_fx', 'Azman Bin Yusof', 'azman.yusof@gmail.com', '+60165432109', 
 'PEPPERSTONE_005', 'Pepperstone', 600, 'verified', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '15 days', NOW() - INTERVAL '14 days', 'admin'),

-- Verified User 6
('6789012345', 'lisa_invest', 'Lisa Tan Wei Ling', 'lisa.tan@outlook.com', '+60154321098', 
 'AVATRADE_006', 'AvaTrade', 450, 'verified', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '7 days', NOW() - INTERVAL '6 days', 'admin'),

-- Verified User 7
('7890123456', 'rizal_capital', 'Rizal Bin Hashim', 'rizal.hashim@gmail.com', '+60143210987', 
 'FXTM_007', 'FXTM', 800, 'verified', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '20 days', NOW() - INTERVAL '19 days', 'admin'),

-- Verified User 8
('8901234567', 'nina_trader', 'Nina Safiya Binti Ahmad', 'nina.safiya@yahoo.com', '+60132109876', 
 'HOTFOREX_008', 'HotForex', 550, 'verified', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '1 day', NOW() - INTERVAL '12 hours', 'admin'),

-- Verified User 9
('9012345678', 'daniel_pro', 'Daniel Lim Chee Wei', 'daniel.lim@gmail.com', '+60121098765', 
 'PLUS500_009', 'Plus500', 900, 'verified', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '10 days', NOW() - INTERVAL '9 days', 'admin'),

-- Verified User 10
('0123456789', 'sarah_wealth', 'Sarah Binti Ibrahim', 'sarah.ibrahim@hotmail.com', '+60110987654', 
 'TICKMILL_010', 'Tickmill', 650, 'verified', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '6 days', NOW() - INTERVAL '5 days', 'admin'),

-- Insert rejected users (5)
-- Rejected User 1
('1111111111', 'rejected_user1', 'Ali Bin Hassan', 'ali.hassan@gmail.com', '+60191111111', 
 'INVALID_001', 'Unknown Broker', 100, 'rejected', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day', 'admin'),

-- Rejected User 2
('2222222222', 'rejected_user2', 'Mira Binti Kamal', 'fake.email@invalid.com', '+60192222222', 
 'FAKE_002', 'Scam Broker', 200, 'rejected', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '4 days', NOW() - INTERVAL '3 days', 'admin'),

-- Rejected User 3
('3333333333', 'rejected_user3', 'Kumar Ramasamy', 'kumar.test@test.com', '+60193333333', 
 'TEST_003', 'Test Broker', 150, 'rejected', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '9 days', NOW() - INTERVAL '8 days', 'admin'),

-- Rejected User 4
('4444444444', 'rejected_user4', 'Wei Ming Tan', 'weiming@dummy.com', '+60194444444', 
 'DUMMY_004', 'Fake Markets', 75, 'rejected', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '11 days', NOW() - INTERVAL '10 days', 'admin'),

-- Rejected User 5
('5555555555', 'rejected_user5', 'Raj Singh', 'raj.singh@invalid.org', '+60195555555', 
 'INVALID_005', 'Non-existent Broker', 250, 'rejected', '127.0.0.1', 
 'Mozilla/5.0 (Test Browser)', NOW() - INTERVAL '14 days', NOW() - INTERVAL '13 days', 'admin');

-- Verify the data was inserted
SELECT 
    status,
    COUNT(*) as count
FROM vip_registrations 
GROUP BY status
ORDER BY status;