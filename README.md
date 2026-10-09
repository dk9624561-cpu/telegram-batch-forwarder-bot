# 📚 Telegram Lecture Auto-Forwarder & Batch Management Bot

Yeh Bot aapke **Main Storage Channel** se new lectures, videos, PDFs, ya notes ko **automatically** recognize karke alag-alag **Batch Channels** me copy/forward karta hai.

---

## 🚀 Step-by-Step Setup Guide (Hinglish)

### **Step 1: Telegram Bot Create Karein**
1. Telegram open karein aur search karein: `@BotFather`
2. Chat start karke command bhejein: `/newbot`
3. Apne Bot ka Name (e.g. `My Batch Forwarder Bot`) aur Username (e.g. `my_lecture_batch_bot`) enter karein.
4. `@BotFather` aapko ek **API Token** dega. Usko copy kar lein.

---

### **Step 2: Bot Ko Channels Me Admin Banayein**
1. Apne **Storage Channel** me jayein -> Settings -> Administrators -> Add Administrator -> Search your Bot -> Give **"Post Messages"** & **"Edit Messages"** permissions.
2. Sabhi **Batch Channels** (e.g. Batch A, Batch B, NEET Batch, JEE Batch) me bhi Bot ko Admin banayein same permissions ke sath.

---

### **Step 3: Configuration (.env File)**
1. `telegram-batch-forwarder-bot` folder me `.env` file open karein.
2. Apna Bot Token paste karein:
   ```env
   BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyZ
   ADMIN_USER_IDS=987654321
   ```
   *(Note: Apna User ID nikalne ke liye Telegram par `@userinfobot` ko message karein).*

---

### **Step 4: Bot Run Karein**
Terminal / Command Prompt me ye command chalayein:
```bash
python bot.py
```
Aapko message dikhega: `✅ Bot is online and listening for channel posts!`

---

### **Step 5: Channels & Hashtags Setup (Telegram Me Commands)**

Bot ke DM (Direct Message) me jayein aur `/start` dabayein:

1. **Storage Channel Set Karein:**
   ```text
   /setstorage -1001234567890
   ```
   *(Note: Channel ID ke start me `-100` hota hai. ID nikalne ke liye channel me `/getid` bhej sakte hain).*

2. **Batch Channels Mapping Add Karein:**
   - Syntax: `/addbatch <#hashtag> <channel_id> <Batch Name>`
   - Example 1: `/addbatch #BatchA -1001112223334 Batch A Physics`
   - Example 2: `/addbatch #BatchB -1005556667778 Batch B Chemistry`
   - Example 3: `/addbatch #Neet2026 -1009998887776 NEET 2026 Batch`

3. **Active Mappings Check Karein:**
   ```text
   /listbatches
   ```

4. **Mode Change (Clean Copy vs Forward):**
   - Clean Post (No "Forwarded from" tag): `/mode copy` (Default)
   - Original Forward Tag: `/mode forward`

---

## 🎯 How It Works (Kaam Kaise Karega?)

Jab aap **Storage Channel** me koi bhi lecture, video, photo, ya document post karenge aur usme hashtag likhenge:

> **Post Caption Example:**
> 🎬 **Physics Chapter 1 - Lecture 05**
> Video link / file...
> `#BatchA` `#Physics`

Bot turant is post ko identify karega aur **Batch A Channel** me auto-copy/forward kar dega! ✨

---

## 🛠 Available Telegram Commands

| Command | Usage | Description |
| :--- | :--- | :--- |
| `/start` | `/start` | Bot welcome & setup status |
| `/help` | `/help` | Detailed help menu |
| `/setstorage` | `/setstorage <channel_id>` | Main storage channel set karein |
| `/addbatch` | `/addbatch <#tag> <channel_id> <Batch Name>` | Tag ko destination channel se map karein |
| `/removebatch` | `/removebatch <#tag>` | Hashtag mapping delete karein |
| `/listbatches` | `/listbatches` | Saare batch channels & tags ki list |
| `/mode` | `/mode copy` ya `/mode forward` | Clean Copy ya Forward mode select karein |
| `/stats` | `/stats` | Statistics dekhein (kitne lectures kis batch me gaye) |
| `/getid` | `/getid` | Chat/Channel ki ID check karne ke liye |
