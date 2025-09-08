# Troubleshooting Guide - RecallIQ

This guide helps you diagnose and resolve common issues you may encounter while using RecallIQ. Issues are organized by category with step-by-step solutions.

## 📋 Table of Contents

1. [Login & Authentication Issues](#login--authentication-issues)
2. [Email Configuration Problems](#email-configuration-problems)
3. [Email Delivery Issues](#email-delivery-issues)
4. [Template & Content Issues](#template--content-issues)
5. [Contact Import Problems](#contact-import-problems)
6. [Campaign Issues](#campaign-issues)
7. [Performance & Loading Issues](#performance--loading-issues)
8. [Permission & Access Issues](#permission--access-issues)
9. [Browser & Compatibility Issues](#browser--compatibility-issues)
10. [Data & Export Issues](#data--export-issues)

---

## 🔐 Login & Authentication Issues

### Cannot Login - "Invalid Credentials"

**Symptoms:**
- Login form shows "Invalid credentials" error
- Password appears correct but login fails

**Solutions:**
1. **Verify Credentials:**
   - Double-check username (case-sensitive)
   - Ensure password is correct
   - Try typing password manually (don't copy/paste)

2. **Check Account Status:**
   - Contact your Tenant Admin to verify account is active
   - Account may be temporarily suspended

3. **Clear Browser Data:**
   - Clear browser cache and cookies
   - Try logging in using incognito/private mode
   - Restart your browser

4. **Try Different Browser:**
   - Test login in Chrome, Firefox, or Edge
   - Disable browser extensions temporarily

**When to Contact Admin:**
- Account lockout after multiple failed attempts
- Forgotten username or password
- Suspect account has been compromised

### Session Expires Frequently

**Symptoms:**
- Repeatedly prompted to login
- "Session expired" messages
- Automatic logout during work

**Solutions:**
1. **Check Network Stability:**
   - Ensure stable internet connection
   - Test on different network if possible

2. **Browser Settings:**
   - Enable cookies for RecallIQ domain
   - Check if browser is clearing cookies automatically
   - Disable "Clear data on exit" settings

3. **Extend Session:**
   - Stay active in the application
   - Refresh page periodically during long sessions
   - Save work frequently

### Two-Factor Authentication Issues

**Symptoms:**
- 2FA codes not working
- Cannot receive authentication codes

**Solutions:**
1. **Time Synchronization:**
   - Ensure device time is correct
   - Sync time with internet time servers

2. **Code Generation:**
   - Wait for new code to generate
   - Try backup codes if available
   - Contact admin for 2FA reset

---

## 📧 Email Configuration Problems

### SMTP Configuration Fails

**Symptoms:**
- "Test Configuration" button shows errors
- Authentication failures
- Connection timeouts

**Common Solutions:**

#### Gmail Configuration Issues
**Problem:** "Invalid credentials" with Gmail
**Solution:**
1. Verify 2-Factor Authentication is enabled
2. Generate new App Password:
   - Google Account → Security → 2-Step Verification
   - App passwords → Generate new password
3. Use App Password (not regular password) in RecallIQ
4. Ensure "Less secure app access" is NOT enabled

**Problem:** "Connection timeout" with Gmail
**Solution:**
1. Check firewall/antivirus blocking port 587
2. Try port 465 with SSL encryption
3. Verify network allows SMTP connections

#### Outlook/Hotmail Issues
**Problem:** Authentication fails with Outlook
**Solution:**
1. Verify IMAP is enabled in Outlook settings
2. For 2FA accounts, use App Password
3. Use full email address as username
4. Check Microsoft account security settings

#### Corporate Email Issues
**Problem:** Custom SMTP not working
**Solution:**
1. Contact IT department for correct settings
2. Verify VPN connection if required
3. Check if authenticated SMTP is required
4. Test with alternative ports (25, 465, 587)

### Email Provider Specific Issues

#### Yahoo Mail Problems
**Symptoms:**
- "Invalid credentials" errors
- Connection refused

**Solutions:**
1. **Enable App Passwords:**
   - Yahoo Account Info → Account Security
   - Generate app password for Mail
   - Use generated password in RecallIQ

2. **Check Security Settings:**
   - Enable "Allow apps that use less secure sign in"
   - Verify account is not locked

#### iCloud Mail Issues
**Symptoms:**
- Authentication failures
- Server connection errors

**Solutions:**
1. **App-Specific Passwords:**
   - Apple ID → Sign-In and Security
   - Generate app-specific password
   - Use generated password in RecallIQ

2. **Account Settings:**
   - Ensure 2FA is enabled on Apple ID
   - Verify iCloud Mail is active

---

## 📬 Email Delivery Issues

### Emails Not Being Sent

**Symptoms:**
- Campaign shows "failed" status
- Zero emails delivered
- Error messages in Email Logs

**Diagnostic Steps:**

1. **Check SMTP Configuration:**
   - Test email configuration in Profile settings
   - Verify credentials are current
   - Ensure provider settings are correct

2. **Review Email Logs:**
   - Go to Email Logs page
   - Look for specific error messages
   - Check for patterns in failures

3. **Verify Contact Groups:**
   - Ensure contact groups contain valid emails
   - Check for empty groups
   - Verify contact group is active

**Common Error Messages and Solutions:**

#### "Authentication Failed"
- Re-verify SMTP credentials
- Generate new App Password
- Check if email provider changed requirements

#### "Connection Timeout"
- Check network connectivity
- Verify firewall settings
- Try alternative SMTP ports

#### "Relay Access Denied"
- Ensure authenticated SMTP is configured
- Verify sender email matches SMTP account
- Check provider's relay policies

### Low Delivery Rates

**Symptoms:**
- Some emails deliver, others fail
- Inconsistent delivery success
- High failure percentage

**Solutions:**

1. **Clean Contact Lists:**
   - Remove invalid email addresses
   - Check for typos in email addresses
   - Remove hard bounces from previous campaigns

2. **Check Content Quality:**
   - Avoid spam trigger words
   - Include proper unsubscribe links
   - Use balanced text-to-image ratios

3. **Monitor Sender Reputation:**
   - Use consistent "From" email address
   - Avoid sudden volume increases
   - Monitor blacklist status

### Emails Going to Spam

**Symptoms:**
- Low open rates
- Recipients report emails in spam folder
- Poor engagement metrics

**Prevention Strategies:**

1. **Content Optimization:**
   - Avoid excessive capital letters
   - Limit promotional language
   - Include clear sender identification
   - Add physical address in footer

2. **Technical Setup:**
   - Configure SPF records (contact IT)
   - Set up DKIM authentication
   - Use reputable SMTP providers
   - Maintain consistent sending volume

3. **List Management:**
   - Use double opt-in for subscriptions
   - Remove unengaged subscribers
   - Honor unsubscribe requests promptly
   - Segment lists for targeted content

---

## 📝 Template & Content Issues

### Template Editor Problems

**Symptoms:**
- HTML editor not loading
- Formatting issues
- Preview not working

**Solutions:**

1. **Browser Compatibility:**
   - Use Chrome or Firefox for best compatibility
   - Disable ad blockers temporarily
   - Clear browser cache and reload

2. **HTML Code Issues:**
   - Validate HTML syntax
   - Remove unsupported CSS properties
   - Use inline styles instead of external CSS

3. **Variable Problems:**
   - Check variable syntax: `{{variable_name}}`
   - Ensure no spaces inside brackets
   - Verify variable names match campaign variables

### Template Display Issues

**Symptoms:**
- Template looks different in email clients
- Images not displaying
- Formatting problems

**Solutions:**

1. **Email Client Compatibility:**
   - Use table-based layouts for better compatibility
   - Avoid complex CSS (flexbox, grid)
   - Test templates in multiple email clients

2. **Image Issues:**
   - Host images on reliable servers
   - Use absolute URLs (not relative)
   - Include alt text for accessibility
   - Optimize image sizes for email

3. **Mobile Display:**
   - Keep template width under 600px
   - Use responsive design techniques
   - Test on mobile devices
   - Use larger fonts (14px minimum)

### Variable Rendering Issues

**Symptoms:**
- Variables showing as `{{variable_name}}` instead of values
- Missing content in emails
- Template errors

**Solutions:**

1. **Variable Syntax:**
   ```
   Correct: {{first_name}}
   Incorrect: {{ first_name }} (spaces)
   Incorrect: {first_name} (single brackets)
   ```

2. **Campaign Variables:**
   - Ensure all template variables are defined in campaign
   - Check spelling of variable names
   - Provide fallback values for optional variables

3. **Contact Data:**
   - Verify contact records contain required data
   - Check for empty fields in contact groups
   - Use default values for missing data

---

## 👥 Contact Import Problems

### CSV Upload Failures

**Symptoms:**
- "Invalid file format" errors
- Import process fails
- Contacts not imported correctly

**Solutions:**

1. **File Format Issues:**
   - Save as .csv (not .xlsx)
   - Use UTF-8 encoding
   - Remove special characters from headers
   - Ensure no empty rows

2. **Correct CSV Format:**
   ```csv
   email,first_name,last_name,company
   john@example.com,John,Doe,Acme Corp
   jane@example.com,Jane,Smith,Tech Inc
   ```

3. **File Size Limits:**
   - Break large files into smaller chunks
   - Remove unnecessary columns
   - Clean data before upload

### Duplicate Contact Issues

**Symptoms:**
- Same contacts appearing multiple times
- Import warnings about duplicates
- Contact count higher than expected

**Solutions:**

1. **Pre-Import Cleaning:**
   - Remove duplicates in spreadsheet before upload
   - Use email address as unique identifier
   - Standardize email format (lowercase)

2. **Import Options:**
   - Choose "Skip duplicates" during import
   - Review import preview before confirming
   - Use "Update existing" for data updates

### Invalid Email Addresses

**Symptoms:**
- Import warnings about invalid emails
- Some contacts not imported
- Email validation errors

**Solutions:**

1. **Email Validation:**
   - Check for typos (gmail.con vs gmail.com)
   - Ensure proper format (user@domain.com)
   - Remove spaces and special characters

2. **Common Format Issues:**
   ```
   Correct: user@example.com
   Incorrect: user@example (missing domain)
   Incorrect: @example.com (missing user)
   Incorrect: user example.com (missing @)
   ```

---

## 📬 Campaign Issues

### Campaign Won't Start

**Symptoms:**
- Campaign stuck in "draft" status
- "Start" button not working
- Error messages when launching

**Solutions:**

1. **Pre-Launch Checklist:**
   - Verify email configuration is working
   - Ensure template is saved and active
   - Check that contact groups contain emails
   - Confirm all required variables are set

2. **Permission Issues:**
   - Verify you have permission to send campaigns
   - Check if account has reached email limits
   - Contact admin if organizational limits exceeded

3. **Template Issues:**
   - Test template preview before launching
   - Verify all variables are properly defined
   - Check template for HTML errors

### Campaign Stuck or Slow

**Symptoms:**
- Campaign progress not moving
- Very slow sending speed
- Long time to complete

**Solutions:**

1. **Check System Status:**
   - Verify backend services are running
   - Check for maintenance notifications
   - Monitor system resources

2. **Provider Limits:**
   - Email providers may limit sending speed
   - Large campaigns take time to process
   - Consider breaking into smaller batches

3. **Technical Issues:**
   - Check network connectivity
   - Verify SMTP provider is responding
   - Review error logs for specific issues

### Campaign Errors Mid-Send

**Symptoms:**
- Campaign pauses unexpectedly
- Partial delivery with errors
- Mixed success/failure results

**Solutions:**

1. **Identify Error Patterns:**
   - Check Email Logs for specific errors
   - Look for common failure reasons
   - Identify problematic email addresses

2. **Resume or Restart:**
   - Try resuming paused campaign
   - Remove problematic contacts and restart
   - Split remaining contacts into new campaign

---

## ⚡ Performance & Loading Issues

### Slow Page Loading

**Symptoms:**
- Pages take long time to load
- Spinning loading indicators
- Timeouts or blank pages

**Solutions:**

1. **Network Issues:**
   - Check internet connection speed
   - Try different network/WiFi
   - Disable VPN temporarily

2. **Browser Optimization:**
   - Close unnecessary tabs
   - Clear browser cache
   - Disable browser extensions
   - Update browser to latest version

3. **System Resources:**
   - Close other applications
   - Check available memory/CPU
   - Restart computer if necessary

### Application Freezing

**Symptoms:**
- Interface becomes unresponsive
- Buttons don't work
- Page doesn't update

**Solutions:**

1. **Immediate Steps:**
   - Refresh page (Ctrl+F5 or Cmd+Shift+R)
   - Try different browser tab
   - Log out and back in

2. **Browser Issues:**
   - Clear browser cache and cookies
   - Disable browser extensions
   - Try incognito/private mode

3. **System Issues:**
   - Check system resources
   - Close other applications
   - Restart browser or computer

### Data Not Loading

**Symptoms:**
- Empty lists or tables
- Missing dashboard data
- "No data" messages

**Solutions:**

1. **Refresh Data:**
   - Reload the page
   - Check if data exists (try different view)
   - Verify filters aren't hiding data

2. **Permission Issues:**
   - Verify you have access to requested data
   - Check if viewing correct organization data
   - Contact admin about data access

---

## 🔒 Permission & Access Issues

### "Access Denied" Errors

**Symptoms:**
- "Permission denied" messages
- Cannot access certain pages
- Features grayed out or hidden

**Solutions:**

1. **Check User Role:**
   - Verify your assigned role in Profile
   - Understand role-based permissions
   - Contact admin for role changes

2. **Account Status:**
   - Ensure account is active
   - Check if suspended or restricted
   - Verify tenant/organization assignment

3. **Feature Access:**
   - Some features require specific roles
   - Check feature requirements in documentation
   - Request access from Tenant Admin

### Cannot Create/Edit Items

**Symptoms:**
- Save buttons don't work
- Cannot create new templates/campaigns
- Edit options not available

**Solutions:**

1. **Permission Level:**
   - Verify role allows creation/editing
   - Check if item belongs to your organization
   - Some items may be system-protected

2. **Technical Issues:**
   - Try refreshing the page
   - Check browser console for errors
   - Clear browser cache

### Data Not Visible

**Symptoms:**
- Cannot see campaigns/templates
- Empty lists where data should exist
- Inconsistent data visibility

**Solutions:**

1. **Organization/Tenant Filters:**
   - Verify viewing correct organization data
   - Check if switched between organizations
   - Confirm data exists in your tenant

2. **Role Restrictions:**
   - Some data may be role-restricted
   - Contact admin to verify data access
   - Check if data belongs to other users

---

## 🌐 Browser & Compatibility Issues

### Unsupported Browser Features

**Symptoms:**
- Missing buttons or interface elements
- JavaScript errors
- Formatting problems

**Solutions:**

1. **Browser Requirements:**
   - Use Chrome 80+ (recommended)
   - Firefox 75+ supported
   - Safari 13+ supported
   - Edge 80+ supported

2. **Browser Settings:**
   - Enable JavaScript
   - Allow cookies for RecallIQ domain
   - Disable strict privacy settings temporarily

3. **Extensions and Add-ons:**
   - Disable ad blockers for RecallIQ
   - Turn off privacy extensions temporarily
   - Try incognito/private mode

### Mobile Browser Issues

**Symptoms:**
- Interface elements too small
- Touch interactions not working
- Layout problems on mobile

**Solutions:**

1. **Mobile Optimization:**
   - Use tablet or desktop for complex tasks
   - Rotate device to landscape mode
   - Zoom interface if needed

2. **Mobile Browser Choice:**
   - Chrome mobile recommended
   - Safari on iOS works well
   - Avoid older mobile browsers

### JavaScript Errors

**Symptoms:**
- Console errors in browser
- Broken functionality
- Incomplete page loading

**Solutions:**

1. **Debug Steps:**
   - Press F12 to open developer tools
   - Check Console tab for errors
   - Refresh page and note any errors

2. **Common Fixes:**
   - Clear browser cache completely
   - Disable browser extensions
   - Try different browser
   - Check internet connection stability

---

## 📊 Data & Export Issues

### Export Not Working

**Symptoms:**
- Export buttons don't respond
- Downloaded files are empty
- Export process fails

**Solutions:**

1. **Browser Settings:**
   - Check if downloads are blocked
   - Allow popups for RecallIQ domain
   - Verify download folder permissions

2. **Data Availability:**
   - Ensure data exists to export
   - Check if filters are too restrictive
   - Verify you have export permissions

### Missing Data

**Symptoms:**
- Expected data not showing
- Incomplete reports
- Historical data missing

**Solutions:**

1. **Date Range Filters:**
   - Check if date filters are too restrictive
   - Expand date range to include more data
   - Verify data exists for selected period

2. **Data Retention:**
   - Some data may be automatically deleted
   - Check retention policies with admin
   - Older data may be archived

### Import Data Problems

**Symptoms:**
- Data not importing correctly
- Formatting issues after import
- Missing fields

**Solutions:**

1. **File Format:**
   - Use recommended CSV format
   - Check column headers match requirements
   - Ensure data encoding is correct

2. **Data Validation:**
   - Review import preview carefully
   - Fix validation errors before importing
   - Test with small sample first

---

## 🆘 Emergency Procedures

### Campaign Emergency Stop

**If you need to immediately stop a campaign:**

1. **Immediate Action:**
   - Go to Email Batches
   - Find running campaign
   - Click "Pause" or "Cancel" button

2. **If Interface Won't Respond:**
   - Refresh browser page
   - Try different browser
   - Contact administrator immediately

3. **Post-Emergency:**
   - Check Email Logs for delivery status
   - Document issue for future prevention
   - Review campaign settings before restarting

### Data Loss Prevention

**If you suspect data loss:**

1. **Don't Take Further Action:**
   - Stop using the application
   - Don't try to "fix" anything
   - Document exactly what happened

2. **Contact Support:**
   - Reach out to your admin immediately
   - Provide detailed description of issue
   - Include screenshots if possible

3. **Recovery Steps:**
   - Work with admin on recovery options
   - Check if recent backups are available
   - Document lessons learned

---

## 📞 When to Contact Support

### Contact Your Tenant Admin For:
- Account access issues
- Permission problems
- Organization-specific questions
- Billing and limit issues

### Contact System Administrator For:
- System-wide outages
- Technical integration issues
- Security concerns
- Data recovery needs

### Escalate to Development Team For:
- Software bugs
- Feature requests
- Performance issues
- Integration problems

### Information to Provide:
- Your username and organization
- Detailed description of the issue
- Steps you took before the problem
- Error messages (exact text or screenshots)
- Browser and operating system info
- Time when issue occurred

---

## 📝 Troubleshooting Checklist

Before contacting support, try these basic steps:

- [ ] Refresh the browser page
- [ ] Clear browser cache and cookies
- [ ] Try a different browser
- [ ] Check internet connection
- [ ] Verify login credentials
- [ ] Check system status page (if available)
- [ ] Review recent changes made
- [ ] Try the same action in different part of app
- [ ] Check browser console for errors
- [ ] Document exact error messages

---

**Still having issues?** Contact your administrator with specific details about your problem, including error messages and steps you've already tried. For urgent issues affecting ongoing campaigns, contact support immediately.