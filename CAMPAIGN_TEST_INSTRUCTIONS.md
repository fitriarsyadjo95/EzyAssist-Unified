# Campaign Registration System - Test Instructions

## 🎯 Overview
This document provides step-by-step testing instructions for the newly implemented campaign-based registration system in RentungFX.

## 📋 Pre-Test Setup

### 1. Environment Check
- [ ] Ensure Railway deployment is active
- [ ] Verify database is connected
- [ ] Confirm Telegram bot is running
- [ ] Check admin panel access

### 2. Required Access
- **Admin Panel**: Login credentials for admin interface
- **Telegram Bot**: Access to RentungBot_Ai in Telegram
- **Database**: Verify database tables exist (campaigns, vip_registrations)

---

## 🧪 Test Scenarios

### **Test 1: Admin Campaign Management**

#### 1.1 Access Campaign Management
1. **Navigate to**: `https://your-railway-app.railway.app/admin/`
2. **Login** with admin credentials
3. **Verify**: Campaign analytics section appears on dashboard
4. **Click**: "Campaigns" in navigation or visit `/admin/campaigns`
5. **Expected**: Campaign management page loads successfully

#### 1.2 Create New Campaign
1. **Click**: "Create Campaign" button
2. **Fill in the form**:
   - **Campaign ID**: `rm50-test-campaign`
   - **Campaign Name**: `RM50 Test Giveaway`
   - **Min Deposit**: `100`
   - **Reward Description**: `RM50 cash reward upon verification`
3. **Click**: "Create Campaign"
4. **Expected**: 
   - Success message appears
   - Campaign appears in the list
   - Campaign is marked as "Active"
   - Registration link is generated

#### 1.3 Verify Campaign Details
1. **Check**: Campaign appears in the table
2. **Verify**: Registration link format: `https://your-app.railway.app/campaign/rm50-test-campaign`
3. **Click**: Copy button next to registration link
4. **Expected**: Link copied to clipboard successfully

#### 1.4 Test Campaign Toggle
1. **Click**: Toggle button (pause/play icon) for the test campaign
2. **Confirm**: Toggle action in popup
3. **Expected**: 
   - Campaign status changes to "Inactive"
   - Badge color changes from green to gray
4. **Click toggle again**: Reactivate campaign
5. **Expected**: Campaign becomes "Active" again

---

### **Test 2: Telegram Bot Commands**

#### 2.1 Test /campaign Command (List All)
1. **Open**: Telegram and find RentungBot_Ai
2. **Send**: `/campaign`
3. **Expected Response**:
   ```
   🎉 Campaign Aktif:

   1. **RM50 Test Giveaway**
      🎁 RM50 cash reward upon verification
      💰 Min Deposit: $100 USD
      📝 `/campaign rm50-test-campaign`

   💡 Gunakan `/campaign [campaign_id]` untuk daftar campaign tertentu
   ```

#### 2.2 Test /campaign Command (Specific Campaign)
1. **Send**: `/campaign rm50-test-campaign`
2. **Expected Response**:
   ```
   🎉 RM50 Test Giveaway

   🎁 Reward: RM50 cash reward upon verification
   💰 Min Deposit: $100 USD
   🎯 Join Group Chat Fighter Rentung

   Klik link di bawah untuk menyertai campaign:

   👉 https://your-app.railway.app/campaign/rm50-test-campaign?token=...

   ⏰ Link ini akan tamat tempoh dalam 30 minit.
   📝 Pastikan anda deposit minimum yang diperlukan untuk layak mendapat reward!
   ```

#### 2.3 Test Invalid Campaign
1. **Send**: `/campaign invalid-campaign`
2. **Expected Response**:
   ```
   ❌ Campaign 'invalid-campaign' tidak dijumpai atau tidak aktif.

   Gunakan /campaign untuk lihat senarai campaign yang aktif.
   ```

#### 2.4 Test Updated Help Commands
1. **Send**: `/start`
2. **Expected Response** includes:
   ```
   Commands yang tersedia:
   📝 /register - Pendaftaran VIP biasa
   🎉 /campaign - Lihat campaign aktif atau join campaign
   👨‍💼 /agent - Berbual dengan live agent

   Contoh: /campaign rm50-giveaway
   ```

---

### **Test 3: Campaign Registration Flow**

#### 3.1 Campaign Account Setup (Step 1)
1. **Click**: Campaign registration link from bot message
2. **Expected**: Campaign account setup page loads with:
   - Campaign name prominently displayed
   - Campaign reward description
   - Minimum deposit requirement highlighted
   - Two account options (New/Existing Valetax account)
   - Step indicator showing "Step 1 of 2"

#### 3.2 Test Account Setup Options
1. **Click**: "Cipta Akaun Baru" button
2. **Expected**: Opens Valetax registration page in new tab
3. **Return** to campaign page
4. **Click**: "Tukar IB Partner" button  
5. **Expected**: Opens Valetax ticket system in new tab

#### 3.3 Continue to Registration Form
1. **Click**: "Selesai, Teruskan ke Langkah 2"
2. **Select**: "Saya telah cipta akaun baru Valetax" in modal
3. **Expected**: 
   - Redirects to campaign registration form
   - Step indicator shows "Step 2 of 2"
   - Campaign information displayed at top
   - Minimum deposit requirement shown

#### 3.4 Campaign Registration Form (Step 2)
1. **Fill in required fields**:
   - **Full Name**: `Test User Campaign`
   - **Email**: `test.campaign@example.com`
   - **Phone**: `+60123456789`
   - **Country**: `Malaysia`
   - **Trading ID**: `12345678`
   - **Deposit Amount**: `150` (above minimum)
   - **Telegram Username**: `testusercampaign`
2. **Check**: Terms and conditions checkbox
3. **Click**: "Hantar Pendaftaran Campaign"

#### 3.5 Verify Form Validation
1. **Test minimum deposit validation**:
   - Enter deposit amount below campaign minimum (e.g., `50`)
   - **Expected**: Validation error appears
   - **Message**: "Jumlah deposit mesti sekurang-kurangnya $100 USD"

2. **Test required field validation**:
   - Leave required fields empty
   - **Expected**: Browser validation prevents submission

#### 3.6 Successful Registration
1. **Complete form** with valid data
2. **Submit** the form
3. **Expected**: 
   - Redirects to campaign success page
   - Shows campaign completion confirmation
   - Displays registration summary
   - Shows next steps for verification

---

### **Test 4: Admin Campaign Analytics**

#### 4.1 Dashboard Analytics
1. **Navigate**: Back to admin dashboard (`/admin/`)
2. **Verify Campaign Analytics Section**:
   - **Active Campaigns**: Should show `1`
   - **Campaign Registrations**: Should show `1` (from test registration)
   - **Regular Registrations**: Shows non-campaign registrations
   - **Campaign Conversion**: Shows percentage

#### 4.2 Campaign Performance Table
1. **Scroll down** to Campaign Performance section
2. **Verify table shows**:
   - Campaign name: `RM50 Test Giveaway`
   - Campaign ID: `rm50-test-campaign`
   - Registrations: `1`
   - Total Deposits: `$150.00 USD`
   - Average Deposit: `$150.00 USD`

#### 4.3 Campaign Registration Details
1. **Click**: "View Details" button for test campaign
2. **Expected**: JSON response with registration details
3. **Verify**: Registration data includes campaign information

---

### **Test 5: Regular Registration Flow**

#### 5.1 Verify Regular Registration Still Works
1. **Send**: `/register` to bot
2. **Click**: Regular VIP registration link
3. **Complete**: Normal registration flow
4. **Expected**: 
   - Regular registration works unchanged
   - No campaign fields in regular flow
   - Dashboard shows separate regular vs campaign counts

---

### **Test 6: Database Validation**

#### 6.1 Admin Registrations View
1. **Navigate**: `/admin/registrations`
2. **Verify**: Campaign registration appears in list
3. **Check**: 
   - Campaign name shown in registration details
   - Campaign ID field populated
   - Is Campaign Registration marked as `Yes`

#### 6.2 Registration Details
1. **Click**: View details for campaign registration
2. **Verify fields**:
   - `campaign_id`: `rm50-test-campaign`
   - `campaign_name`: `RM50 Test Giveaway`
   - `campaign_min_deposit`: `100`
   - `campaign_reward`: `RM50 cash reward upon verification`
   - `is_campaign_registration`: `true`
   - `deposit_amount`: `150`

---

### **Test 7: Error Handling**

#### 7.1 Inactive Campaign Access
1. **Deactivate** test campaign in admin panel
2. **Try accessing**: Direct campaign URL
3. **Expected**: Error page showing "Campaign not found or inactive"

#### 7.2 Expired Token
1. **Wait** 30+ minutes after getting campaign link from bot
2. **Try accessing**: Expired campaign link
3. **Expected**: Error page about expired registration link

#### 7.3 Invalid Campaign ID
1. **Try accessing**: `/campaign/non-existent-campaign`
2. **Expected**: Error page showing campaign not found

---

## ✅ Test Completion Checklist

### Campaign Management
- [ ] Admin can create campaigns
- [ ] Campaign appears in admin list
- [ ] Campaign toggle works (activate/deactivate)
- [ ] Campaign analytics show correctly
- [ ] Registration links generate properly

### Bot Integration
- [ ] `/campaign` lists active campaigns
- [ ] `/campaign {id}` shows specific campaign
- [ ] Invalid campaigns show error message
- [ ] Help text includes campaign commands
- [ ] Registration links work from bot

### Registration Flow
- [ ] Campaign account setup page loads
- [ ] Step indicators work correctly
- [ ] Campaign info displayed prominently
- [ ] Deposit validation enforces minimums
- [ ] Success page shows campaign completion
- [ ] Form validation prevents invalid submissions

### Analytics & Tracking
- [ ] Dashboard shows campaign metrics
- [ ] Performance table tracks deposits
- [ ] Regular vs campaign registrations separated
- [ ] Registration details include campaign data

### Error Handling
- [ ] Inactive campaigns show error
- [ ] Expired tokens handled gracefully
- [ ] Invalid campaign IDs show error
- [ ] Form validation works correctly

---

## 🐛 Common Issues & Solutions

### Issue: Campaign not appearing in bot list
**Solution**: Check campaign `is_active` status in admin panel

### Issue: Registration link expired
**Solution**: Generate new link using `/campaign {id}` command

### Issue: Deposit validation not working
**Solution**: Verify campaign `min_deposit_amount` is set correctly

### Issue: Analytics not updating
**Solution**: Check database connection and refresh admin dashboard

---

## 📝 Test Results Template

```
CAMPAIGN SYSTEM TEST RESULTS
Date: ___________
Tester: ___________

✅ PASSED / ❌ FAILED / ⚠️ ISSUES

Admin Campaign Management:
- Campaign creation: ___
- Campaign toggle: ___
- Analytics display: ___

Bot Integration:
- /campaign command: ___
- Specific campaign links: ___
- Error handling: ___

Registration Flow:
- Account setup: ___
- Form validation: ___
- Success completion: ___

Database & Analytics:
- Data storage: ___
- Performance tracking: ___
- Dashboard metrics: ___

NOTES:
_________________________________
_________________________________
_________________________________
```

---

## 🚀 Next Steps After Testing

1. **If all tests pass**: System is ready for production use
2. **If issues found**: Document and fix before going live
3. **Create real campaigns**: Set up actual promotional campaigns
4. **Train team**: Ensure team knows how to use campaign system
5. **Monitor performance**: Track campaign effectiveness and ROI

---

**Happy Testing! 🎉**

For issues or questions, check the logs in Railway dashboard or contact the development team.