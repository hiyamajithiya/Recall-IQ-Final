# 🚀 RecallIQ Quick Start Guide

Welcome to RecallIQ! Get started with professional email marketing in just 5 minutes. This guide works for everyone - business owners, marketers, and team members - no technical experience required.

## 🎯 What You'll Achieve

By the end of this guide, you'll have:
- ✅ Your RecallIQ account set up and ready
- ✅ Your first professional email template created
- ✅ A contact group with your recipients
- ✅ Your first email campaign sent successfully
- ✅ Knowledge of how to track results and performance

---

## 🏃‍♀️ **5-Minute Quick Start**

### **Step 1: Access RecallIQ (30 seconds)**

**For Testing/Development:**
1. Open your web browser
2. Go to: `http://localhost:3000`
3. You'll see the beautiful RecallIQ login page

**For Production:**  
1. Visit your company's RecallIQ URL (ask your admin)
2. Bookmark it for easy access

### **Step 2: Get Your Account (2 minutes)**

**🚀 Super Fast: Google Sign-Up (30 seconds)**
1. Click **"Continue with Google"** 
2. Select your Google account
3. Fill in your company details quickly
4. You're in! Skip to Step 3.

**📧 Traditional Sign-Up (2 minutes)**
1. Click **"Register"**
2. Fill in your details:
   ```
   Company Name: Your Business Name
   Your Name: John Smith  
   Email: john@yourbusiness.com (you'll get a verification code)
   Username: johnsmith
   Password: Create something strong
   ```
3. Click **"Send Code"** → Check your email
4. Enter the 6-digit code → **"Complete Registration"**
5. You're automatically logged in!

### **Step 3: Create Your First Email Template (1 minute)**

1. **Go to Templates:**
   - Click **"Email Templates"** in the left menu
   - Click **"+ Create Template"**

2. **Design Your Email:**
   ```
   Template Name: Welcome Email
   Subject Line: Welcome {{first_name}} - You're All Set!
   ```

3. **Write Your Message (copy this to start):**
   ```html
   <div style="font-family: Arial, sans-serif; max-width: 600px;">
       <h1 style="color: #2563eb;">Hello {{first_name}}! 👋</h1>
       
       <p>Welcome to {{company_name}}! We're thrilled to have you join us.</p>
       
       <div style="background: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
           <h3>🎯 What's Next?</h3>
           <ul>
               <li>✅ Explore our amazing features</li>
               <li>✅ Set up your profile</li>  
               <li>✅ Start your first project</li>
           </ul>
       </div>
       
       <p>Questions? Just reply to this email - we're here to help!</p>
       
       <p>Cheers,<br><strong>The {{company_name}} Team</strong></p>
   </div>
   ```

4. **Save & Test:**
   - Click **"Save Template"**
   - Click **"Preview"** to see how it looks
   - Click **"Send Test"** and enter your email

### **Step 4: Add Your Contacts (1 minute)**

1. **Create Contact Group:**
   - Click **"Contact Groups"** in the left menu
   - Click **"+ Create Group"**
   - Name: "My First Campaign"
   - Click **"Create Group"**

2. **Add People (Choose the easiest method):**

   **🔥 Quick Method - Paste Emails:**
   - Click **"+ Add Recipients"**
   - Paste your email list (one per line):
     ```
     john.doe@example.com
     jane.smith@company.com
     marketing@business.org
     ```
   - Click **"Add All"**

   **📊 Excel Method (if you have a spreadsheet):**
   - Click **"Import Excel"** 
   - Download template if needed
   - Upload your Excel file
   - Match columns and import

### **Step 5: Launch Your First Campaign (1 minute)**

1. **Create Campaign:**
   - Click **"Email Campaigns"** in the left menu
   - Click **"+ Create Campaign"**

2. **Set Everything Up:**
   ```
   Campaign Name: Welcome Campaign - First Try
   Email Template: Welcome Email (select from dropdown)  
   Contact Groups: My First Campaign (check the box)
   When to Send: Send Immediately (or pick a time)
   ```

3. **Add Personal Touch:**
   - Set `company_name` to your business name
   - Review everything looks good

4. **🚀 Launch It:**
   - Click **"Review Campaign"**
   - Click **"Start Sending"**
   - Watch your emails go out in real-time!

### **Step 6: See Your Results (30 seconds)**

1. **Watch Live Progress:**
   - Stay on the campaign page to see emails sending
   - See success count going up in real-time

2. **Check Detailed Results:**
   - Click **"Email Logs"** in the left menu
   - See exactly which emails were delivered
   - Filter by your campaign name

---

## 📧 **Set Up Your Email Provider (Important!)**

To send emails reliably, you need to configure your email settings:

### **🔧 Quick Gmail Setup (Recommended)**

1. **Access Settings:**
   - Click your profile picture (top-right)
   - Select **"Email Configuration"** 

2. **Enable Gmail (5 steps):**
   1. Go to your Google Account Settings
   2. Security → 2-Step Verification (enable it)
   3. Security → App Passwords → Generate for "Mail"
   4. Copy the 16-character password
   5. Paste it in RecallIQ's "Email Password" field

3. **Configure in RecallIQ:**
   ```
   Email Provider: Gmail SMTP
   Email Username: your.email@gmail.com
   Email Password: [paste the app password]
   From Name: Your Company Name
   ```

4. **Test & Save:**
   - Click **"Test Configuration"**
   - Should see "✅ Test successful!"
   - Click **"Save"**

### **⚡ Other Email Providers**
- **Outlook**: Works with regular password (or app password if 2FA enabled)
- **Yahoo**: Requires app password (similar to Gmail)
- **Custom SMTP**: Enter your server details from IT department

---

## 🧪 **Ready-to-Use Test Accounts**

Don't want to create an account right now? Use these for testing:

### **Super Admin (Can Do Everything)**
```
Username: admin
Password: admin123
Role: Full system control
```

### **Business Owner (Manage Organization)**  
```
Username: tenant_admin
Password: admin123  
Role: Company management + marketing
```

### **Marketing Team Member**
```
Username: staff
Password: staff123
Role: Create campaigns and manage contacts
```

### **Basic User**
```
Username: tenant_user  
Password: user123
Role: Basic email sending
```

---

## 🎓 **What's Next: Become a Pro**

Great job! You've sent your first campaign. Here's how to level up:

### **📧 Master Email Marketing**
- **[Advanced Templates](./FEATURES.md#email-templates)**: Beautiful designs with drag-and-drop
- **[Smart Personalization](./FEATURES.md#personalization)**: Use customer data effectively  
- **[Campaign Automation](./FEATURES.md#automation)**: Set up automatic email sequences
- **[A/B Testing](./FEATURES.md#ab-testing)**: Test what works best

### **👥 Grow Your Audience**
- **[Contact Segmentation](./FEATURES.md#segmentation)**: Target the right people
- **[List Building](./FEATURES.md#list-building)**: Grow your email list
- **[Data Management](./FEATURES.md#data-management)**: Keep lists clean and updated

### **📊 Analyze & Improve**  
- **[Performance Tracking](./FEATURES.md#analytics)**: See what's working
- **[Advanced Reports](./FEATURES.md#reporting)**: Generate detailed insights
- **[ROI Measurement](./FEATURES.md#roi)**: Prove email marketing value

---

## ✨ **Pro Tips for Immediate Success**

### **🎯 Email Best Practices**
1. **Always Test First**: Send to yourself before launching
2. **Mobile-Friendly**: 70% of emails are read on mobile
3. **Clear Subject Lines**: Say what's inside, avoid spam words
4. **Personal Touch**: Use first names, relevant content
5. **One Clear Action**: What should recipients do next?

### **📈 Campaign Success Secrets**
1. **Timing Matters**: Tuesday-Thursday, 10 AM-2 PM work best
2. **Segment Your List**: Different messages for different groups
3. **Clean Your List**: Remove bounced emails regularly
4. **Track Everything**: Open rates, clicks, conversions
5. **Keep It Simple**: Less is often more effective

### **🔐 Stay Professional**
1. **Permission-Based**: Only email people who opted in
2. **Easy Unsubscribe**: Always provide opt-out option
3. **Consistent Branding**: Use company colors, logo, voice
4. **Regular Schedule**: Don't overwhelm, don't disappear
5. **Value First**: Every email should help recipients

---

## ❓ **Quick Help & Answers**

### **"My emails aren't sending!"**
- Check your email provider settings in Profile
- Test your SMTP configuration  
- Verify recipients' email addresses are valid
- Check spam folder for test emails

### **"I can't log in!"**
- Double-check username and password
- Make sure Caps Lock is off
- Try password reset if needed
- Contact your admin for role verification

### **"Where are my contacts?"**
- Make sure you selected the right contact group
- Check if contacts were imported successfully
- Verify email addresses are in correct format

### **"Template variables not working?"**  
- Use double curly braces: `{{first_name}}`
- Check spelling exactly matches
- Set variable values when creating campaigns
- Preview template to see results

### **Need More Help?**
- **📖 Complete Manual**: [User Guide](./README.md)
- **🎯 All Features**: [Features Guide](./FEATURES.md)  
- **🛠️ Fix Problems**: [Troubleshooting](./TROUBLESHOOTING.md)
- **❓ More Q&A**: [FAQ](./FAQ.md)

---

## 🎉 **Congratulations - You're Ready!**

You've just:
✅ **Created your RecallIQ account**  
✅ **Built a professional email template**  
✅ **Set up your contact database**  
✅ **Launched your first campaign**  
✅ **Learned to track results**  

**🚀 You're now equipped to grow your business with professional email marketing!**

### **Your Next Mission**
Explore our [Complete Features Guide](./FEATURES.md) to discover advanced tools like automation, advanced analytics, team collaboration, and enterprise features that will take your email marketing to the next level.

**Ready to become an email marketing pro? Let's dive deeper!** 

---

*Questions? Need help with something specific? Jump to our [User Manual](./README.md) or check the [FAQ](./FAQ.md) for detailed answers to everything.*