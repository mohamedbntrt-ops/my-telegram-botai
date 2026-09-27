#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════
   NEXUS AI  ·  Telegram Intelligence Platform  ·  v5.1
   Professional Multi-Model AI Bot — Multilingual Edition (FIXED)
   ────────────────────────────────────────────────────────────────────────
   • 8 languages: AR · EN · RU · HI · VI · ES · PT · ZH
   • 7 AI Models  ·  AI vs AI Debate  ·  Vision + Files
   • Full owner panel  ·  Group moderation
   • Auto-migrations (safe for old databases)
═══════════════════════════════════════════════════════════════════════════
"""

import asyncio
import base64
import html
import io
import logging
import os
import random
import re
import sqlite3
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand,
    ReactionTypeEmoji, ChatPermissions
)
from telegram.constants import ParseMode, ChatAction, ChatType, ChatMemberStatus
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ChatMemberHandler, ContextTypes, filters as tg_filters
)
from telegram.error import TelegramError, BadRequest, Forbidden

# ═══════════════════════════════════════════════════════════════════════════
#                                BRAND
# ═══════════════════════════════════════════════════════════════════════════
BRAND     = "NEXUS AI"
VERSION   = "5.1"
TEAM      = "SASKI Team"
SIGNATURE = "@GERYXVIP"

# ═══════════════════════════════════════════════════════════════════════════
#                                CONFIG
# ═══════════════════════════════════════════════════════════════════════════
BOT_TOKEN = "8977155307:AAEpTfSP_IapYP-hn8Gg-HnclvxWD_Cpghw"

OWNER_IDS       = [0]
OWNER_USERNAMES = ["GERYXVIP"]

DB_PATH  = "nexus.db"
LOG_FILE = "nexus.log"

MAX_HISTORY = 20
MAX_MSG_LEN = 4000

CHAT_ENDPOINT = "https://us-central1-ai-chat-bot-bf47e.cloudfunctions.net/chat_function_android"
APP_PACKAGE   = "com.open.ai.chat.bot.ask.questions"
USER_AGENT    = "Dalvik/2.1.0 (Linux; U; Android 14; SM-X910N Build/UQ1A.240205.07241537)"

DEFAULT_MODEL  = "gpt-4o-mini"
DEFAULT_SYSTEM = "Be helpful, professional, and concise."

# ═══════════════════════════════════════════════════════════════════════════
#                                MODELS
# ═══════════════════════════════════════════════════════════════════════════
MODELS = {
    "gpt-4o-mini": {
        "name": "GPT-4o Mini", "emoji": "⚡", "tier": "STANDARD", "maker": "OpenAI",
        "identity": "You are GPT-4o Mini by OpenAI. When asked who you are, always say you are GPT-4o Mini made by OpenAI.",
    },
    "gpt-4o": {
        "name": "GPT-4o", "emoji": "🧠", "tier": "PREMIUM", "maker": "OpenAI",
        "identity": "You are GPT-4o by OpenAI. When asked who you are, always say you are GPT-4o made by OpenAI.",
    },
    "o1": {
        "name": "o1", "emoji": "🔬", "tier": "PREMIUM", "maker": "OpenAI",
        "identity": "You are o1 by OpenAI. When asked who you are, always say you are o1 made by OpenAI.",
    },
    "o1-mini": {
        "name": "o1 Mini", "emoji": "🔍", "tier": "PREMIUM", "maker": "OpenAI",
        "identity": "You are o1-mini by OpenAI. When asked who you are, always say you are o1-mini made by OpenAI.",
    },
    "gemini-1.5-flash": {
        "name": "Gemini 1.5 Flash", "emoji": "🌟", "tier": "PREMIUM", "maker": "Google DeepMind",
        "identity": "You are Gemini 1.5 Flash by Google DeepMind. When asked who you are, always say you are Gemini 1.5 Flash made by Google DeepMind.",
    },
    "claude-3-5-haiku-latest": {
        "name": "Claude 3.5 Haiku", "emoji": "🎭", "tier": "PREMIUM", "maker": "Anthropic",
        "identity": "You are Claude 3.5 Haiku by Anthropic. When asked who you are, always say you are Claude 3.5 Haiku made by Anthropic.",
    },
    "claude-3-5-sonnet-latest": {
        "name": "Claude 3.5 Sonnet", "emoji": "🎨", "tier": "PREMIUM", "maker": "Anthropic",
        "identity": "You are Claude 3.5 Sonnet by Anthropic. When asked who you are, always say you are Claude 3.5 Sonnet made by Anthropic.",
    },
}

REACTION_POOL = ["👍", "🔥", "❤", "🎉", "😁", "🤔", "👏", "💯", "⚡", "👌", "🙏", "🥰"]

# ═══════════════════════════════════════════════════════════════════════════
#                                LANGUAGES
# ═══════════════════════════════════════════════════════════════════════════
LANGS = {
    "ar": {"name": "العربية",    "flag": "🇸🇦", "ai": "Always respond in Arabic. Use Arabic script only."},
    "en": {"name": "English",    "flag": "🇺🇸", "ai": "Always respond in English."},
    "ru": {"name": "Русский",    "flag": "🇷🇺", "ai": "Всегда отвечай на русском языке."},
    "hi": {"name": "हिन्दी",       "flag": "🇮🇳", "ai": "हमेशा हिंदी में जवाब दें।"},
    "vi": {"name": "Tiếng Việt", "flag": "🇻🇳", "ai": "Luôn trả lời bằng tiếng Việt."},
    "es": {"name": "Español",    "flag": "🇪🇸", "ai": "Responde siempre en español."},
    "pt": {"name": "Português",  "flag": "🇧🇷", "ai": "Responda sempre em português."},
    "zh": {"name": "中文",         "flag": "🇨🇳", "ai": "请始终用中文回答。"},
}

T = {
    "ar": {
        "choose_lang":    "🌐 <b>اختر لغتك</b>\n\nاختر لغة التحدث مع البوت والذكاء الاصطناعي.",
        "lang_set":       "✅ تم ضبط اللغة على: <b>{name}</b>",
        "welcome":        "👋 أهلاً <b>{name}</b>\n\nمرحباً بك في <b>NEXUS AI</b> — منصة ذكاء اصطناعي متعددة الموديلات.",
        "btn_models":     "🤖 الموديلات",
        "btn_settings":   "⚙️ الإعدادات",
        "btn_stats":      "📊 إحصائياتي",
        "btn_new_chat":   "🧹 محادثة جديدة",
        "btn_debate":     "🎯 AI ضد AI",
        "btn_export":     "📤 تصدير",
        "btn_help":       "ℹ️ مساعدة",
        "btn_owner":      "👑 لوحة المالك",
        "btn_lang":       "🌐 تغيير اللغة",
        "btn_back":       "⬅️ رجوع",
        "btn_cancel":     "❌ إلغاء",
        "models_title":   "🤖 <b>اختر الموديل</b>\n\nالحالي: {cur}",
        "model_changed":  "✅ تم تغيير الموديل إلى: {name}",
        "settings_title": "⚙️ <b>الإعدادات</b>",
        "system_prompt_label": "📝 البرومبت",
        "reaction_label": "🔔 التفاعل التلقائي",
        "on":  "✅ مفعّل",
        "off": "❌ معطّل",
        "stats_title": "📊 <b>إحصائياتي</b>",
        "msgs_label":  "💬 الرسائل",
        "tokens_label":"🔢 التوكنات",
        "lang_label":  "🌐 اللغة",
        "help_text":   "📖 <b>الأوامر</b>\n\n<b>عام:</b>\n/start · /lang · /help · /myid\n\n<b>المحادثة:</b>\n/model · /clear · /system · /reaction\n/stats · /export\n\n<b>المنافسة:</b>\n/debate · /topic الموضوع · /stop\n\n<b>في المجموعات:</b>\n• اكتب <code>ch رسالتك</code>\n• أو رد على رسالة البوت\n• أو <code>/model رسالتك</code>",
        "thinking":    "⚡ <i>{model} يفكر...</i>",
        "vision":      "👁 <i>{model} يحلل الصورة...</i>",
        "no_response": "❌ ما وصل رد من السيرفر.\n\nجرّب مرة أخرى أو غيّر الموديل.",
        "you": "أنت",
        "ai":  "AI",
        "new_chat_done": "🧹 تم حذف السياق. ابدأ من جديد.",
        "export_empty":  "📭 لا يوجد محادثات للتصدير.",
        "export_caption":"📤 {n} رسالة",
        "reaction_usage":"الاستخدام: <code>/reaction on|off</code>",
        "reaction_on_ok":  "✅ تم تفعيل التفاعل.",
        "reaction_off_ok": "❌ تم تعطيل التفاعل.",
        "system_usage": "📝 لعرض: /system\nلتغيير: <code>/system النص</code>\nللحذف: <code>/system -</code>",
        "system_deleted": "✅ تم حذف البرومبت المخصص.",
        "system_updated": "✅ تم تحديث البرومبت.",
        "debate_title":  "🎯 <b>منافسة AI ضد AI</b>\n\n<b>اختر الطرف الأول (A):</b>",
        "debate_choose_b":"🅰️ <b>{a}</b>\n\n<b>اختر الطرف الثاني (B):</b>",
        "debate_choose_topic":"✅ <b>تم الاختيار:</b>\n🅰️ {a}\n🅱️ {b}\n\n📝 اكتب الآن:\n<code>/topic الموضوع</code>",
        "debate_started":"🎯 <b>بدأت المنافسة</b>\n\n📌 {topic}\n\n🅰️ {a}\n🅱️ {b}\n\n<i>يبدأ خلال ثانيتين...</i>",
        "debate_stopped":"🛑 تم إيقاف المنافسة.",
        "debate_no_active":"لا توجد منافسة شغالة.",
        "debate_already":"⚠️ هناك منافسة شغالة. /stop لإيقافها.",
        "debate_topic_usage":"اكتب الموضوع: <code>/topic النص</code>",
        "debate_start_first":"❌ ابدأ بـ /debate أولاً.",
        "debate_finished":"🏁 <b>انتهت المنافسة</b>",
        "debate_model_same":"اختر موديل مختلف.",
        "banned": "🚫 أنت محظور من استخدام هذا البوت.",
        "owner_only": "❌ هذا الأمر للمالك فقط.",
        "admin_only": "❌ هذا الأمر للمشرفين فقط.",
        "reply_or_user": "❌ رد على رسالة العضو أو حدد @username أو ID.",
        "specify_user": "❌ حدد العضو.",
        "muted":  "🔇 تم الكتم: {name}",
        "unmuted":"🔊 فك الكتم: {name}",
        "kicked": "👢 تم الطرد: {name}",
        "banned_user":  "🚫 تم الحظر: {name}",
        "unbanned_user":"✅ فك الحظر: {name}",
        "warned": "⚠️ تحذير {n}/3: {name}",
        "warn_banned":"⛔ {name} وصل 3 تحذيرات — تم حظره.",
        "unlock_all":  "🔓 تم فك جميع القيود عن المجموعة.",
        "welcome_usage":"📝 <code>/welcome نص الترحيب</code>\n\nمتغيرات: <code>{name}</code> <code>{chat}</code>",
        "welcome_saved":"✅ تم حفظ الترحيب.",
        "antilink_usage":"🔗 <code>/antilink on|off</code>",
        "antilink_on": "🔗 قفل الروابط: مفعّل.",
        "antilink_off":"🔗 قفل الروابط: معطّل.",
        "link_blocked":"🔗 {name} — الروابط ممنوعة.",
        "group_settings":"⚙️ <b>إعدادات المجموعة</b>",
        "group_admin_title":"🛡 <b>لوحة إدارة المجموعة</b>\n\n<b>الأوامر:</b>\n/mute · /unmute · /kick · /ban · /unban\n/warn · /unlockall\n/welcome · /antilink · /settings · /grouplang",
        "group_joined_hint":"<b>⚡ NEXUS AI</b>\n\nمرحباً! أنا بوت ذكاء اصطناعي متعدد الموديلات.\n\n<b>الاستخدام في المجموعة:</b>\n• <code>ch سؤالك</code>\n• أو رد على رسالتي\n• أو <code>/model سؤالك</code>\n\n<b>للأدمن:</b> /gadmin",
        "owner_panel":"👑 <b>لوحة المالك</b>",
        "owner_stats":"📊 <b>Dashboard</b>",
        "owner_users":"👥 <b>المستخدمون</b>",
        "owner_groups":"💬 <b>المجموعات</b>",
        "owner_broadcast":"📢 <b>بث جماعي</b>",
        "owner_tools":"🔧 <b>أدوات</b>",
        "broadcast_prompt":"📢 أرسل النص الذي تريد إرساله لكل المستخدمين:",
        "broadcast_sending":"📤 جاري الإرسال إلى {n} مستخدم...",
        "broadcast_done":"✅ اكتمل البث\nنجح: {ok} · فشل: {fail}",
        "no_data":"لا يوجد بيانات.",
        "voice_unsupported":"🎤 الصوت غير مدعوم حالياً. اكتب النص.",
        "long_message":"⚠️ الرسالة طويلة جداً.",
        "unlimited":"♾ دائم",
    },
    "en": {
        "choose_lang":    "🌐 <b>Choose your language</b>\n\nPick the language for the bot and AI replies.",
        "lang_set":       "✅ Language set to: <b>{name}</b>",
        "welcome":        "👋 Welcome <b>{name}</b>\n\nWelcome to <b>NEXUS AI</b> — Multi-model intelligence platform.",
        "btn_models":     "🤖 Models",
        "btn_settings":   "⚙️ Settings",
        "btn_stats":      "📊 My Stats",
        "btn_new_chat":   "🧹 New Chat",
        "btn_debate":     "🎯 AI vs AI",
        "btn_export":     "📤 Export",
        "btn_help":       "ℹ️ Help",
        "btn_owner":      "👑 Owner Panel",
        "btn_lang":       "🌐 Change Language",
        "btn_back":       "⬅️ Back",
        "btn_cancel":     "❌ Cancel",
        "models_title":   "🤖 <b>Select a Model</b>\n\nCurrent: {cur}",
        "model_changed":  "✅ Model changed to: {name}",
        "settings_title": "⚙️ <b>Settings</b>",
        "system_prompt_label": "📝 System Prompt",
        "reaction_label": "🔔 Auto-Reaction",
        "on":  "✅ ON",
        "off": "❌ OFF",
        "stats_title": "📊 <b>My Stats</b>",
        "msgs_label":  "💬 Messages",
        "tokens_label":"🔢 Tokens",
        "lang_label":  "🌐 Language",
        "help_text":   "📖 <b>Commands</b>\n\n<b>General:</b>\n/start · /lang · /help · /myid\n\n<b>Chat:</b>\n/model · /clear · /system · /reaction\n/stats · /export\n\n<b>Debate:</b>\n/debate · /topic topic · /stop\n\n<b>In Groups:</b>\n• Send <code>ch your message</code>\n• Or reply to my message\n• Or <code>/model your message</code>",
        "thinking":    "⚡ <i>{model} is thinking...</i>",
        "vision":      "👁 <i>{model} is analyzing the image...</i>",
        "no_response": "❌ No response from server.\n\nTry again or switch model.",
        "you": "You",
        "ai":  "AI",
        "new_chat_done": "🧹 Context cleared. Start fresh.",
        "export_empty":  "📭 No chat history to export.",
        "export_caption":"📤 {n} messages",
        "reaction_usage":"Usage: <code>/reaction on|off</code>",
        "reaction_on_ok":  "✅ Reaction enabled.",
        "reaction_off_ok": "❌ Reaction disabled.",
        "system_usage": "📝 View: /system\nSet: <code>/system text</code>\nDelete: <code>/system -</code>",
        "system_deleted": "✅ Custom prompt deleted.",
        "system_updated": "✅ Prompt updated.",
        "debate_title":  "🎯 <b>AI vs AI Debate</b>\n\n<b>Choose side A:</b>",
        "debate_choose_b":"🅰️ <b>{a}</b>\n\n<b>Choose side B:</b>",
        "debate_choose_topic":"✅ <b>Selected:</b>\n🅰️ {a}\n🅱️ {b}\n\n📝 Now send:\n<code>/topic Topic</code>",
        "debate_started":"🎯 <b>Debate Started</b>\n\n📌 {topic}\n\n🅰️ {a}\n🅱️ {b}\n\n<i>Starting in 2 seconds...</i>",
        "debate_stopped":"🛑 Debate stopped.",
        "debate_no_active":"No active debate.",
        "debate_already":"⚠️ A debate is already running. /stop to end it.",
        "debate_topic_usage":"Send topic: <code>/topic Topic</code>",
        "debate_start_first":"❌ Start with /debate first.",
        "debate_finished":"🏁 <b>Debate Ended</b>",
        "debate_model_same":"Pick a different model.",
        "banned": "🚫 You are banned from this bot.",
        "owner_only": "❌ Owner only.",
        "admin_only": "❌ Admins only.",
        "reply_or_user": "❌ Reply to a user or specify @username / ID.",
        "specify_user": "❌ Specify the user.",
        "muted":  "🔇 Muted: {name}",
        "unmuted":"🔊 Unmuted: {name}",
        "kicked": "👢 Kicked: {name}",
        "banned_user":  "🚫 Banned: {name}",
        "unbanned_user":"✅ Unbanned: {name}",
        "warned": "⚠️ Warning {n}/3: {name}",
        "warn_banned":"⛔ {name} reached 3 warnings — banned.",
        "unlock_all":  "🔓 All restrictions lifted.",
        "welcome_usage":"📝 <code>/welcome your text</code>\n\nVariables: <code>{name}</code> <code>{chat}</code>",
        "welcome_saved":"✅ Welcome saved.",
        "antilink_usage":"🔗 <code>/antilink on|off</code>",
        "antilink_on": "🔗 Antilink: ON.",
        "antilink_off":"🔗 Antilink: OFF.",
        "link_blocked":"🔗 {name} — links are not allowed.",
        "group_settings":"⚙️ <b>Group Settings</b>",
        "group_admin_title":"🛡 <b>Group Admin Panel</b>\n\n<b>Commands:</b>\n/mute · /unmute · /kick · /ban · /unban\n/warn · /unlockall\n/welcome · /antilink · /settings · /grouplang",
        "group_joined_hint":"<b>⚡ NEXUS AI</b>\n\nHello! I am a multi-model AI bot.\n\n<b>How to use in groups:</b>\n• Send <code>ch your message</code>\n• Or reply to my message\n• Or <code>/model your message</code>\n\n<b>Admins:</b> /gadmin",
        "owner_panel":"👑 <b>Owner Panel</b>",
        "owner_stats":"📊 <b>Dashboard</b>",
        "owner_users":"👥 <b>Users</b>",
        "owner_groups":"💬 <b>Groups</b>",
        "owner_broadcast":"📢 <b>Broadcast</b>",
        "owner_tools":"🔧 <b>Tools</b>",
        "broadcast_prompt":"📢 Send the message to broadcast to all users:",
        "broadcast_sending":"📤 Sending to {n} users...",
        "broadcast_done":"✅ Broadcast complete\nSent: {ok} · Failed: {fail}",
        "no_data":"No data.",
        "voice_unsupported":"🎤 Voice not supported yet. Please type.",
        "long_message":"⚠️ Message too long.",
        "unlimited":"♾ Permanent",
    },
    "ru": {
        "choose_lang":    "🌐 <b>Выберите язык</b>\n\nВыберите язык для бота и ИИ.",
        "lang_set":       "✅ Язык установлен: <b>{name}</b>",
        "welcome":        "👋 Привет, <b>{name}</b>\n\nДобро пожаловать в <b>NEXUS AI</b> — мультимодельная ИИ-платформа.",
        "btn_models":     "🤖 Модели",
        "btn_settings":   "⚙️ Настройки",
        "btn_stats":      "📊 Статистика",
        "btn_new_chat":   "🧹 Новый чат",
        "btn_debate":     "🎯 ИИ против ИИ",
        "btn_export":     "📤 Экспорт",
        "btn_help":       "ℹ️ Помощь",
        "btn_owner":      "👑 Панель владельца",
        "btn_lang":       "🌐 Сменить язык",
        "btn_back":       "⬅️ Назад",
        "btn_cancel":     "❌ Отмена",
        "models_title":   "🤖 <b>Выберите модель</b>\n\nТекущая: {cur}",
        "model_changed":  "✅ Модель изменена: {name}",
        "settings_title": "⚙️ <b>Настройки</b>",
        "system_prompt_label": "📝 Системный промпт",
        "reaction_label": "🔔 Авто-реакция",
        "on":  "✅ Вкл",
        "off": "❌ Выкл",
        "stats_title": "📊 <b>Моя статистика</b>",
        "msgs_label":  "💬 Сообщения",
        "tokens_label":"🔢 Токены",
        "lang_label":  "🌐 Язык",
        "help_text":   "📖 <b>Команды</b>\n\n/start · /lang · /help · /myid\n/model · /clear · /system · /reaction\n/stats · /export · /debate · /stop",
        "thinking":    "⚡ <i>{model} думает...</i>",
        "vision":      "👁 <i>{model} анализирует изображение...</i>",
        "no_response": "❌ Нет ответа от сервера.",
        "you": "Вы",
        "ai":  "ИИ",
        "new_chat_done": "🧹 Контекст очищен.",
        "export_empty":  "📭 Нет истории.",
        "export_caption":"📤 {n} сообщений",
        "reaction_usage":"Использование: <code>/reaction on|off</code>",
        "reaction_on_ok":  "✅ Реакция включена.",
        "reaction_off_ok": "❌ Реакция выключена.",
        "system_usage": "📝 /system\nУстановить: <code>/system текст</code>\nУдалить: <code>/system -</code>",
        "system_deleted": "✅ Промпт удалён.",
        "system_updated": "✅ Промпт обновлён.",
        "debate_title":  "🎯 <b>Дебаты ИИ</b>\n\n<b>Выберите сторону A:</b>",
        "debate_choose_b":"🅰️ <b>{a}</b>\n\n<b>Выберите сторону B:</b>",
        "debate_choose_topic":"✅ <b>Выбрано:</b>\n🅰️ {a}\n🅱️ {b}\n\n📝 Отправьте:\n<code>/topic Тема</code>",
        "debate_started":"🎯 <b>Дебаты начались</b>\n\n📌 {topic}\n\n🅰️ {a}\n🅱️ {b}",
        "debate_stopped":"🛑 Дебаты остановлены.",
        "debate_no_active":"Нет активных дебатов.",
        "debate_already":"⚠️ Дебаты уже идут. /stop чтобы закончить.",
        "debate_topic_usage":"Отправьте: <code>/topic Тема</code>",
        "debate_start_first":"❌ Сначала /debate.",
        "debate_finished":"🏁 <b>Дебаты завершены</b>",
        "debate_model_same":"Выберите другую модель.",
        "banned": "🚫 Вы забанены.",
        "owner_only": "❌ Только для владельца.",
        "admin_only": "❌ Только для админов.",
        "reply_or_user": "❌ Ответьте на сообщение или укажите @username / ID.",
        "specify_user": "❌ Укажите пользователя.",
        "muted":  "🔇 Замучен: {name}",
        "unmuted":"🔊 Размучен: {name}",
        "kicked": "👢 Кикнут: {name}",
        "banned_user":  "🚫 Забанен: {name}",
        "unbanned_user":"✅ Разбанен: {name}",
        "warned": "⚠️ Предупреждение {n}/3: {name}",
        "warn_banned":"⛔ {name} — 3 предупреждения, забанен.",
        "unlock_all":  "🔓 Все ограничения сняты.",
        "welcome_usage":"📝 <code>/welcome текст</code>",
        "welcome_saved":"✅ Приветствие сохранено.",
        "antilink_usage":"🔗 <code>/antilink on|off</code>",
        "antilink_on": "🔗 Антиссылки: ВКЛ.",
        "antilink_off":"🔗 Антиссылки: ВЫКЛ.",
        "link_blocked":"🔗 {name} — ссылки запрещены.",
        "group_settings":"⚙️ <b>Настройки группы</b>",
        "group_admin_title":"🛡 <b>Панель администратора</b>\n/mute · /kick · /ban · /warn · /unlockall · /welcome · /antilink · /grouplang",
        "group_joined_hint":"<b>⚡ NEXUS AI</b>\n\nПривет! Я мультимодельный ИИ-бот.\n\n<code>ch ваш вопрос</code> — спросить ИИ.",
        "owner_panel":"👑 <b>Панель владельца</b>",
        "owner_stats":"📊 <b>Панель</b>",
        "owner_users":"👥 <b>Пользователи</b>",
        "owner_groups":"💬 <b>Группы</b>",
        "owner_broadcast":"📢 <b>Рассылка</b>",
        "owner_tools":"🔧 <b>Инструменты</b>",
        "broadcast_prompt":"📢 Отправьте текст для рассылки:",
        "broadcast_sending":"📤 Отправка {n} пользователям...",
        "broadcast_done":"✅ Рассылка завершена\nОтправлено: {ok} · Ошибок: {fail}",
        "no_data":"Нет данных.",
        "voice_unsupported":"🎤 Голос пока не поддерживается.",
        "long_message":"⚠️ Сообщение слишком длинное.",
        "unlimited":"♾ Навсегда",
    },
    "hi": {
        "choose_lang":    "🌐 <b>अपनी भाषा चुनें</b>\n\nबॉट और AI के लिए भाषा चुनें।",
        "lang_set":       "✅ भाषा सेट: <b>{name}</b>",
        "welcome":        "👋 नमस्ते <b>{name}</b>\n\n<b>NEXUS AI</b> में आपका स्वागत है।",
        "btn_models":     "🤖 मॉडल",
        "btn_settings":   "⚙️ सेटिंग्स",
        "btn_stats":      "📊 मेरे आंकड़े",
        "btn_new_chat":   "🧹 नई चैट",
        "btn_debate":     "🎯 AI vs AI",
        "btn_export":     "📤 निर्यात",
        "btn_help":       "ℹ️ मदद",
        "btn_owner":      "👑 ओनर पैनल",
        "btn_lang":       "🌐 भाषा बदलें",
        "btn_back":       "⬅️ वापस",
        "btn_cancel":     "❌ रद्द करें",
        "models_title":   "🤖 <b>मॉडल चुनें</b>\n\nवर्तमान: {cur}",
        "model_changed":  "✅ मॉडल बदला: {name}",
        "settings_title": "⚙️ <b>सेटिंग्स</b>",
        "system_prompt_label": "📝 सिस्टम प्रॉम्प्ट",
        "reaction_label": "🔔 ऑटो रिएक्शन",
        "on":  "✅ चालू",
        "off": "❌ बंद",
        "stats_title": "📊 <b>मेरे आंकड़े</b>",
        "msgs_label":  "💬 संदेश",
        "tokens_label":"🔢 टोकन",
        "lang_label":  "🌐 भाषा",
        "help_text":   "📖 <b>कमांड</b>\n\n/start · /lang · /help · /myid\n/model · /clear · /system · /reaction\n/stats · /export · /debate · /stop",
        "thinking":    "⚡ <i>{model} सोच रहा है...</i>",
        "vision":      "👁 <i>{model} छवि देख रहा है...</i>",
        "no_response": "❌ सर्वर से कोई जवाब नहीं।",
        "you": "आप",
        "ai":  "AI",
        "new_chat_done": "🧹 संदर्भ साफ़ किया।",
        "export_empty":  "📭 कोई इतिहास नहीं।",
        "export_caption":"📤 {n} संदेश",
        "reaction_usage":"उपयोग: <code>/reaction on|off</code>",
        "reaction_on_ok":  "✅ रिएक्शन चालू।",
        "reaction_off_ok": "❌ रिएक्शन बंद।",
        "system_usage": "📝 /system",
        "system_deleted": "✅ प्रॉम्प्ट हटाया।",
        "system_updated": "✅ प्रॉम्प्ट अपडेट।",
        "debate_title":  "🎯 <b>AI vs AI बहस</b>\n\n<b>पक्ष A चुनें:</b>",
        "debate_choose_b":"🅰️ <b>{a}</b>\n\n<b>पक्ष B चुनें:</b>",
        "debate_choose_topic":"✅ चुना: {a} vs {b}\n\n📝 भेजें: <code>/topic विषय</code>",
        "debate_started":"🎯 <b>बहस शुरू</b>\n📌 {topic}\n🅰️ {a}\n🅱️ {b}",
        "debate_stopped":"🛑 बहस रोकी।",
        "debate_no_active":"कोई बहस नहीं।",
        "debate_already":"⚠️ बहस चल रही है। /stop",
        "debate_topic_usage":"भेजें: <code>/topic विषय</code>",
        "debate_start_first":"❌ पहले /debate।",
        "debate_finished":"🏁 <b>बहस खत्म</b>",
        "debate_model_same":"अलग मॉडल चुनें।",
        "banned": "🚫 आप बैन हैं।",
        "owner_only": "❌ केवल ओनर।",
        "admin_only": "❌ केवल एडमिन।",
        "reply_or_user": "❌ किसी संदेश पर रिप्लाई करें या @username / ID दें।",
        "specify_user": "❌ उपयोगकर्ता चुनें।",
        "muted":  "🔇 म्यूट: {name}",
        "unmuted":"🔊 अनम्यूट: {name}",
        "kicked": "👢 किक: {name}",
        "banned_user":  "🚫 बैन: {name}",
        "unbanned_user":"✅ अनबैन: {name}",
        "warned": "⚠️ चेतावनी {n}/3: {name}",
        "warn_banned":"⛔ {name} — 3 चेतावनियां, बैन।",
        "unlock_all":  "🔓 सभी प्रतिबंध हटाए।",
        "welcome_usage":"📝 <code>/welcome टेक्स्ट</code>",
        "welcome_saved":"✅ स्वागत सहेजा।",
        "antilink_usage":"🔗 <code>/antilink on|off</code>",
        "antilink_on": "🔗 एंटीलिंक: चालू।",
        "antilink_off":"🔗 एंटीलिंक: बंद।",
        "link_blocked":"🔗 {name} — लिंक मना है।",
        "group_settings":"⚙️ <b>ग्रुप सेटिंग्स</b>",
        "group_admin_title":"🛡 <b>ग्रुप एडमिन पैनल</b>\n/mute · /kick · /ban · /warn · /unlockall · /welcome · /antilink · /grouplang",
        "group_joined_hint":"<b>⚡ NEXUS AI</b>\n\nनमस्ते! <code>ch आपका सवाल</code>",
        "owner_panel":"👑 <b>ओनर पैनल</b>",
        "owner_stats":"📊 <b>डैशबोर्ड</b>",
        "owner_users":"👥 <b>उपयोगकर्ता</b>",
        "owner_groups":"💬 <b>ग्रुप</b>",
        "owner_broadcast":"📢 <b>ब्रॉडकास्ट</b>",
        "owner_tools":"🔧 <b>उपकरण</b>",
        "broadcast_prompt":"📢 सभी को भेजने के लिए टेक्स्ट:",
        "broadcast_sending":"📤 {n} को भेज रहा है...",
        "broadcast_done":"✅ भेजा: {ok} · विफल: {fail}",
        "no_data":"कोई डेटा नहीं।",
        "voice_unsupported":"🎤 वॉइस समर्थित नहीं।",
        "long_message":"⚠️ संदेश बहुत लंबा।",
        "unlimited":"♾ स्थायी",
    },
    "vi": {
        "choose_lang":    "🌐 <b>Chọn ngôn ngữ</b>\n\nChọn ngôn ngữ cho bot và AI.",
        "lang_set":       "✅ Đã đặt ngôn ngữ: <b>{name}</b>",
        "welcome":        "👋 Xin chào <b>{name}</b>\n\nChào mừng đến <b>NEXUS AI</b>.",
        "btn_models":     "🤖 Mô hình",
        "btn_settings":   "⚙️ Cài đặt",
        "btn_stats":      "📊 Thống kê",
        "btn_new_chat":   "🧹 Chat mới",
        "btn_debate":     "🎯 AI vs AI",
        "btn_export":     "📤 Xuất",
        "btn_help":       "ℹ️ Trợ giúp",
        "btn_owner":      "👑 Bảng chủ",
        "btn_lang":       "🌐 Đổi ngôn ngữ",
        "btn_back":       "⬅️ Quay lại",
        "btn_cancel":     "❌ Hủy",
        "models_title":   "🤖 <b>Chọn mô hình</b>\n\nHiện tại: {cur}",
        "model_changed":  "✅ Đã đổi mô hình: {name}",
        "settings_title": "⚙️ <b>Cài đặt</b>",
        "system_prompt_label": "📝 System Prompt",
        "reaction_label": "🔔 Auto Reaction",
        "on":  "✅ Bật",
        "off": "❌ Tắt",
        "stats_title": "📊 <b>Thống kê của tôi</b>",
        "msgs_label":  "💬 Tin nhắn",
        "tokens_label":"🔢 Token",
        "lang_label":  "🌐 Ngôn ngữ",
        "help_text":   "📖 <b>Lệnh</b>\n\n/start · /lang · /help · /myid\n/model · /clear · /system · /reaction\n/stats · /export · /debate · /stop",
        "thinking":    "⚡ <i>{model} đang suy nghĩ...</i>",
        "vision":      "👁 <i>{model} đang phân tích ảnh...</i>",
        "no_response": "❌ Không có phản hồi.",
        "you": "Bạn",
        "ai":  "AI",
        "new_chat_done": "🧹 Đã xóa ngữ cảnh.",
        "export_empty":  "📭 Không có lịch sử.",
        "export_caption":"📤 {n} tin nhắn",
        "reaction_usage":"Dùng: <code>/reaction on|off</code>",
        "reaction_on_ok":  "✅ Bật reaction.",
        "reaction_off_ok": "❌ Tắt reaction.",
        "system_usage": "📝 /system",
        "system_deleted": "✅ Đã xóa prompt.",
        "system_updated": "✅ Đã cập nhật prompt.",
        "debate_title":  "🎯 <b>Tranh luận AI</b>\n\n<b>Chọn bên A:</b>",
        "debate_choose_b":"🅰️ <b>{a}</b>\n\n<b>Chọn bên B:</b>",
        "debate_choose_topic":"✅ Đã chọn: {a} vs {b}\n\n📝 Gửi: <code>/topic Chủ đề</code>",
        "debate_started":"🎯 <b>Bắt đầu tranh luận</b>\n📌 {topic}\n🅰️ {a}\n🅱️ {b}",
        "debate_stopped":"🛑 Đã dừng.",
        "debate_no_active":"Không có tranh luận.",
        "debate_already":"⚠️ Đang có tranh luận. /stop",
        "debate_topic_usage":"Gửi: <code>/topic Chủ đề</code>",
        "debate_start_first":"❌ Bắt đầu với /debate.",
        "debate_finished":"🏁 <b>Kết thúc tranh luận</b>",
        "debate_model_same":"Chọn mô hình khác.",
        "banned": "🚫 Bạn đã bị chặn.",
        "owner_only": "❌ Chỉ chủ sở hữu.",
        "admin_only": "❌ Chỉ admin.",
        "reply_or_user": "❌ Trả lời hoặc @username / ID.",
        "specify_user": "❌ Chọn người dùng.",
        "muted":  "🔇 Đã mute: {name}",
        "unmuted":"🔊 Đã unmute: {name}",
        "kicked": "👢 Đã kick: {name}",
        "banned_user":  "🚫 Đã ban: {name}",
        "unbanned_user":"✅ Đã unban: {name}",
        "warned": "⚠️ Cảnh báo {n}/3: {name}",
        "warn_banned":"⛔ {name} — 3 cảnh báo, đã ban.",
        "unlock_all":  "🔓 Đã mở khóa tất cả.",
        "welcome_usage":"📝 <code>/welcome nội dung</code>",
        "welcome_saved":"✅ Đã lưu.",
        "antilink_usage":"🔗 <code>/antilink on|off</code>",
        "antilink_on": "🔗 Chặn link: BẬT.",
        "antilink_off":"🔗 Chặn link: TẮT.",
        "link_blocked":"🔗 {name} — không cho phép link.",
        "group_settings":"⚙️ <b>Cài đặt nhóm</b>",
        "group_admin_title":"🛡 <b>Bảng Admin</b>\n/mute · /kick · /ban · /warn · /unlockall · /welcome · /antilink · /grouplang",
        "group_joined_hint":"<b>⚡ NEXUS AI</b>\n\nGửi <code>ch câu hỏi</code> để hỏi AI.",
        "owner_panel":"👑 <b>Bảng chủ</b>",
        "owner_stats":"📊 <b>Dashboard</b>",
        "owner_users":"👥 <b>Người dùng</b>",
        "owner_groups":"💬 <b>Nhóm</b>",
        "owner_broadcast":"📢 <b>Broadcast</b>",
        "owner_tools":"🔧 <b>Công cụ</b>",
        "broadcast_prompt":"📢 Gửi nội dung broadcast:",
        "broadcast_sending":"📤 Đang gửi {n} người dùng...",
        "broadcast_done":"✅ Hoàn tất\nThành công: {ok} · Lỗi: {fail}",
        "no_data":"Không có dữ liệu.",
        "voice_unsupported":"🎤 Chưa hỗ trợ giọng nói.",
        "long_message":"⚠️ Tin nhắn quá dài.",
        "unlimited":"♾ Vĩnh viễn",
    },
    "es": {
        "choose_lang":    "🌐 <b>Elige tu idioma</b>\n\nSelecciona el idioma del bot y la IA.",
        "lang_set":       "✅ Idioma establecido: <b>{name}</b>",
        "welcome":        "👋 Hola <b>{name}</b>\n\nBienvenido a <b>NEXUS AI</b>.",
        "btn_models":     "🤖 Modelos",
        "btn_settings":   "⚙️ Ajustes",
        "btn_stats":      "📊 Mis estadísticas",
        "btn_new_chat":   "🧹 Nuevo chat",
        "btn_debate":     "🎯 IA vs IA",
        "btn_export":     "📤 Exportar",
        "btn_help":       "ℹ️ Ayuda",
        "btn_owner":      "👑 Panel del dueño",
        "btn_lang":       "🌐 Cambiar idioma",
        "btn_back":       "⬅️ Atrás",
        "btn_cancel":     "❌ Cancelar",
        "models_title":   "🤖 <b>Elige un modelo</b>\n\nActual: {cur}",
        "model_changed":  "✅ Modelo cambiado: {name}",
        "settings_title": "⚙️ <b>Ajustes</b>",
        "system_prompt_label": "📝 System Prompt",
        "reaction_label": "🔔 Reacción automática",
        "on":  "✅ Activado",
        "off": "❌ Desactivado",
        "stats_title": "📊 <b>Mis estadísticas</b>",
        "msgs_label":  "💬 Mensajes",
        "tokens_label":"🔢 Tokens",
        "lang_label":  "🌐 Idioma",
        "help_text":   "📖 <b>Comandos</b>\n\n/start · /lang · /help · /myid\n/model · /clear · /system · /reaction\n/stats · /export · /debate · /stop",
        "thinking":    "⚡ <i>{model} está pensando...</i>",
        "vision":      "👁 <i>{model} analiza la imagen...</i>",
        "no_response": "❌ Sin respuesta del servidor.",
        "you": "Tú",
        "ai":  "IA",
        "new_chat_done": "🧹 Contexto borrado.",
        "export_empty":  "📭 Sin historial.",
        "export_caption":"📤 {n} mensajes",
        "reaction_usage":"Uso: <code>/reaction on|off</code>",
        "reaction_on_ok":  "✅ Reacción activada.",
        "reaction_off_ok": "❌ Reacción desactivada.",
        "system_usage": "📝 /system",
        "system_deleted": "✅ Prompt eliminado.",
        "system_updated": "✅ Prompt actualizado.",
        "debate_title":  "🎯 <b>Debate IA vs IA</b>\n\n<b>Elige el lado A:</b>",
        "debate_choose_b":"🅰️ <b>{a}</b>\n\n<b>Elige el lado B:</b>",
        "debate_choose_topic":"✅ Seleccionado: {a} vs {b}\n\n📝 Envía: <code>/topic Tema</code>",
        "debate_started":"🎯 <b>Debate iniciado</b>\n📌 {topic}\n🅰️ {a}\n🅱️ {b}",
        "debate_stopped":"🛑 Debate detenido.",
        "debate_no_active":"Sin debate activo.",
        "debate_already":"⚠️ Debate en curso. /stop",
        "debate_topic_usage":"Envía: <code>/topic Tema</code>",
        "debate_start_first":"❌ Empieza con /debate.",
        "debate_finished":"🏁 <b>Debate terminado</b>",
        "debate_model_same":"Elige otro modelo.",
        "banned": "🚫 Estás baneado.",
        "owner_only": "❌ Solo el dueño.",
        "admin_only": "❌ Solo admins.",
        "reply_or_user": "❌ Responde a un mensaje o indica @username / ID.",
        "specify_user": "❌ Especifica el usuario.",
        "muted":  "🔇 Silenciado: {name}",
        "unmuted":"🔊 Reactivado: {name}",
        "kicked": "👢 Expulsado: {name}",
        "banned_user":  "🚫 Baneado: {name}",
        "unbanned_user":"✅ Desbaneado: {name}",
        "warned": "⚠️ Advertencia {n}/3: {name}",
        "warn_banned":"⛔ {name} — 3 advertencias, baneado.",
        "unlock_all":  "🔓 Restricciones eliminadas.",
        "welcome_usage":"📝 <code>/welcome texto</code>",
        "welcome_saved":"✅ Bienvenida guardada.",
        "antilink_usage":"🔗 <code>/antilink on|off</code>",
        "antilink_on": "🔗 Antilink: ON.",
        "antilink_off":"🔗 Antilink: OFF.",
        "link_blocked":"🔗 {name} — enlaces no permitidos.",
        "group_settings":"⚙️ <b>Ajustes del grupo</b>",
        "group_admin_title":"🛡 <b>Panel de admin</b>\n/mute · /kick · /ban · /warn · /unlockall · /welcome · /antilink · /grouplang",
        "group_joined_hint":"<b>⚡ NEXUS AI</b>\n\nEnvía <code>ch pregunta</code> para preguntar a la IA.",
        "owner_panel":"👑 <b>Panel del dueño</b>",
        "owner_stats":"📊 <b>Panel</b>",
        "owner_users":"👥 <b>Usuarios</b>",
        "owner_groups":"💬 <b>Grupos</b>",
        "owner_broadcast":"📢 <b>Difusión</b>",
        "owner_tools":"🔧 <b>Herramientas</b>",
        "broadcast_prompt":"📢 Envía el texto para difundir:",
        "broadcast_sending":"📤 Enviando a {n} usuarios...",
        "broadcast_done":"✅ Difusión completa\nEnviados: {ok} · Fallos: {fail}",
        "no_data":"Sin datos.",
        "voice_unsupported":"🎤 Voz no compatible aún.",
        "long_message":"⚠️ Mensaje demasiado largo.",
        "unlimited":"♾ Permanente",
    },
    "pt": {
        "choose_lang":    "🌐 <b>Escolha seu idioma</b>\n\nEscolha o idioma do bot e da IA.",
        "lang_set":       "✅ Idioma definido: <b>{name}</b>",
        "welcome":        "👋 Olá <b>{name}</b>\n\nBem-vindo ao <b>NEXUS AI</b>.",
        "btn_models":     "🤖 Modelos",
        "btn_settings":   "⚙️ Configurações",
        "btn_stats":      "📊 Minhas estatísticas",
        "btn_new_chat":   "🧹 Novo chat",
        "btn_debate":     "🎯 IA vs IA",
        "btn_export":     "📤 Exportar",
        "btn_help":       "ℹ️ Ajuda",
        "btn_owner":      "👑 Painel do dono",
        "btn_lang":       "🌐 Mudar idioma",
        "btn_back":       "⬅️ Voltar",
        "btn_cancel":     "❌ Cancelar",
        "models_title":   "🤖 <b>Escolha um modelo</b>\n\nAtual: {cur}",
        "model_changed":  "✅ Modelo alterado: {name}",
        "settings_title": "⚙️ <b>Configurações</b>",
        "system_prompt_label": "📝 System Prompt",
        "reaction_label": "🔔 Reação automática",
        "on":  "✅ Ligado",
        "off": "❌ Desligado",
        "stats_title": "📊 <b>Minhas estatísticas</b>",
        "msgs_label":  "💬 Mensagens",
        "tokens_label":"🔢 Tokens",
        "lang_label":  "🌐 Idioma",
        "help_text":   "📖 <b>Comandos</b>\n\n/start · /lang · /help · /myid\n/model · /clear · /system · /reaction\n/stats · /export · /debate · /stop",
        "thinking":    "⚡ <i>{model} pensando...</i>",
        "vision":      "👁 <i>{model} analisando imagem...</i>",
        "no_response": "❌ Sem resposta do servidor.",
        "you": "Você",
        "ai":  "IA",
        "new_chat_done": "🧹 Contexto limpo.",
        "export_empty":  "📭 Sem histórico.",
        "export_caption":"📤 {n} mensagens",
        "reaction_usage":"Uso: <code>/reaction on|off</code>",
        "reaction_on_ok":  "✅ Reação ligada.",
        "reaction_off_ok": "❌ Reação desligada.",
        "system_usage": "📝 /system",
        "system_deleted": "✅ Prompt excluído.",
        "system_updated": "✅ Prompt atualizado.",
        "debate_title":  "🎯 <b>Debate IA vs IA</b>\n\n<b>Escolha o lado A:</b>",
        "debate_choose_b":"🅰️ <b>{a}</b>\n\n<b>Escolha o lado B:</b>",
        "debate_choose_topic":"✅ Selecionado: {a} vs {b}\n\n📝 Envie: <code>/topic Tema</code>",
        "debate_started":"🎯 <b>Debate iniciado</b>\n📌 {topic}\n🅰️ {a}\n🅱️ {b}",
        "debate_stopped":"🛑 Debate parado.",
        "debate_no_active":"Sem debate ativo.",
        "debate_already":"⚠️ Debate em andamento. /stop",
        "debate_topic_usage":"Envie: <code>/topic Tema</code>",
        "debate_start_first":"❌ Comece com /debate.",
        "debate_finished":"🏁 <b>Debate finalizado</b>",
        "debate_model_same":"Escolha outro modelo.",
        "banned": "🚫 Você está banido.",
        "owner_only": "❌ Apenas o dono.",
        "admin_only": "❌ Apenas admins.",
        "reply_or_user": "❌ Responda a uma mensagem ou indique @username / ID.",
        "specify_user": "❌ Especifique o usuário.",
        "muted":  "🔇 Silenciado: {name}",
        "unmuted":"🔊 Reativado: {name}",
        "kicked": "👢 Expulso: {name}",
        "banned_user":  "🚫 Banido: {name}",
        "unbanned_user":"✅ Desbanido: {name}",
        "warned": "⚠️ Advertência {n}/3: {name}",
        "warn_banned":"⛔ {name} — 3 advertências, banido.",
        "unlock_all":  "🔓 Restrições removidas.",
        "welcome_usage":"📝 <code>/welcome texto</code>",
        "welcome_saved":"✅ Boas-vindas salvas.",
        "antilink_usage":"🔗 <code>/antilink on|off</code>",
        "antilink_on": "🔗 Antilink: LIGADO.",
        "antilink_off":"🔗 Antilink: DESLIGADO.",
        "link_blocked":"🔗 {name} — links não permitidos.",
        "group_settings":"⚙️ <b>Configurações do grupo</b>",
        "group_admin_title":"🛡 <b>Painel de admin</b>\n/mute · /kick · /ban · /warn · /unlockall · /welcome · /antilink · /grouplang",
        "group_joined_hint":"<b>⚡ NEXUS AI</b>\n\nEnvie <code>ch pergunta</code> para consultar a IA.",
        "owner_panel":"👑 <b>Painel do dono</b>",
        "owner_stats":"📊 <b>Dashboard</b>",
        "owner_users":"👥 <b>Usuários</b>",
        "owner_groups":"💬 <b>Grupos</b>",
        "owner_broadcast":"📢 <b>Transmissão</b>",
        "owner_tools":"🔧 <b>Ferramentas</b>",
        "broadcast_prompt":"📢 Envie o texto para transmitir:",
        "broadcast_sending":"📤 Enviando para {n} usuários...",
        "broadcast_done":"✅ Transmissão completa\nEnviados: {ok} · Falhas: {fail}",
        "no_data":"Sem dados.",
        "voice_unsupported":"🎤 Voz ainda não suportada.",
        "long_message":"⚠️ Mensagem muito longa.",
        "unlimited":"♾ Permanente",
    },
    "zh": {
        "choose_lang":    "🌐 <b>选择您的语言</b>\n\n请选择机器人和 AI 使用的语言。",
        "lang_set":       "✅ 语言已设置：<b>{name}</b>",
        "welcome":        "👋 你好 <b>{name}</b>\n\n欢迎使用 <b>NEXUS AI</b>。",
        "btn_models":     "🤖 模型",
        "btn_settings":   "⚙️ 设置",
        "btn_stats":      "📊 我的统计",
        "btn_new_chat":   "🧹 新对话",
        "btn_debate":     "🎯 AI 对决",
        "btn_export":     "📤 导出",
        "btn_help":       "ℹ️ 帮助",
        "btn_owner":      "👑 所有者面板",
        "btn_lang":       "🌐 切换语言",
        "btn_back":       "⬅️ 返回",
        "btn_cancel":     "❌ 取消",
        "models_title":   "🤖 <b>选择模型</b>\n\n当前：{cur}",
        "model_changed":  "✅ 模型已切换：{name}",
        "settings_title": "⚙️ <b>设置</b>",
        "system_prompt_label": "📝 系统提示",
        "reaction_label": "🔔 自动表情",
        "on":  "✅ 已开启",
        "off": "❌ 已关闭",
        "stats_title": "📊 <b>我的统计</b>",
        "msgs_label":  "💬 消息",
        "tokens_label":"🔢 令牌",
        "lang_label":  "🌐 语言",
        "help_text":   "📖 <b>命令</b>\n\n/start · /lang · /help · /myid\n/model · /clear · /system · /reaction\n/stats · /export · /debate · /stop",
        "thinking":    "⚡ <i>{model} 正在思考...</i>",
        "vision":      "👁 <i>{model} 正在分析图片...</i>",
        "no_response": "❌ 服务器无响应。",
        "you": "你",
        "ai":  "AI",
        "new_chat_done": "🧹 上下文已清空。",
        "export_empty":  "📭 无历史记录。",
        "export_caption":"📤 {n} 条消息",
        "reaction_usage":"用法：<code>/reaction on|off</code>",
        "reaction_on_ok":  "✅ 已开启表情。",
        "reaction_off_ok": "❌ 已关闭表情。",
        "system_usage": "📝 /system",
        "system_deleted": "✅ 提示已删除。",
        "system_updated": "✅ 提示已更新。",
        "debate_title":  "🎯 <b>AI 对决</b>\n\n<b>选择正方 A：</b>",
        "debate_choose_b":"🅰️ <b>{a}</b>\n\n<b>选择反方 B：</b>",
        "debate_choose_topic":"✅ 已选择：{a} vs {b}\n\n📝 发送：<code>/topic 主题</code>",
        "debate_started":"🎯 <b>对决开始</b>\n📌 {topic}\n🅰️ {a}\n🅱️ {b}",
        "debate_stopped":"🛑 对决已停止。",
        "debate_no_active":"无进行中的对决。",
        "debate_already":"⚠️ 对决进行中。/stop",
        "debate_topic_usage":"发送：<code>/topic 主题</code>",
        "debate_start_first":"❌ 请先 /debate。",
        "debate_finished":"🏁 <b>对决结束</b>",
        "debate_model_same":"请选择不同的模型。",
        "banned": "🚫 您已被禁止使用。",
        "owner_only": "❌ 仅限所有者。",
        "admin_only": "❌ 仅限管理员。",
        "reply_or_user": "❌ 请回复消息或指定 @username / ID。",
        "specify_user": "❌ 请指定用户。",
        "muted":  "🔇 已禁言：{name}",
        "unmuted":"🔊 已解除禁言：{name}",
        "kicked": "👢 已踢出：{name}",
        "banned_user":  "🚫 已封禁：{name}",
        "unbanned_user":"✅ 已解封：{name}",
        "warned": "⚠️ 警告 {n}/3：{name}",
        "warn_banned":"⛔ {name} — 3 次警告，已封禁。",
        "unlock_all":  "🔓 已解除所有限制。",
        "welcome_usage":"📝 <code>/welcome 文本</code>",
        "welcome_saved":"✅ 欢迎语已保存。",
        "antilink_usage":"🔗 <code>/antilink on|off</code>",
        "antilink_on": "🔗 反链接：开启。",
        "antilink_off":"🔗 反链接：关闭。",
        "link_blocked":"🔗 {name} — 禁止发送链接。",
        "group_settings":"⚙️ <b>群组设置</b>",
        "group_admin_title":"🛡 <b>群组管理面板</b>\n/mute · /kick · /ban · /warn · /unlockall · /welcome · /antilink · /grouplang",
        "group_joined_hint":"<b>⚡ NEXUS AI</b>\n\n发送 <code>ch 问题</code> 咨询 AI。",
        "owner_panel":"👑 <b>所有者面板</b>",
        "owner_stats":"📊 <b>仪表盘</b>",
        "owner_users":"👥 <b>用户</b>",
        "owner_groups":"💬 <b>群组</b>",
        "owner_broadcast":"📢 <b>广播</b>",
        "owner_tools":"🔧 <b>工具</b>",
        "broadcast_prompt":"📢 发送要广播的文本：",
        "broadcast_sending":"📤 正在发送给 {n} 位用户...",
        "broadcast_done":"✅ 广播完成\n成功：{ok} · 失败：{fail}",
        "no_data":"无数据。",
        "voice_unsupported":"🎤 尚不支持语音。",
        "long_message":"⚠️ 消息太长。",
        "unlimited":"♾ 永久",
    },
}

def t(lang: str, key: str, **kw) -> str:
    if lang not in T: lang = "ar"
    txt = T[lang].get(key, T["ar"].get(key, key))
    try:
        return txt.format(**kw) if kw else txt
    except Exception:
        return txt

# ═══════════════════════════════════════════════════════════════════════════
#                                LOGGING
# ═══════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("nexus")

# ═══════════════════════════════════════════════════════════════════════════
#                                DATABASE
# ═══════════════════════════════════════════════════════════════════════════
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    lang TEXT DEFAULT 'ar',
    model TEXT DEFAULT 'gpt-4o-mini',
    system_prompt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP,
    msg_count INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    reaction_on INTEGER DEFAULT 1,
    is_banned INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    role TEXT,
    content TEXT,
    model TEXT,
    tokens INTEGER DEFAULT 0,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS groups (
    chat_id INTEGER PRIMARY KEY,
    title TEXT,
    username TEXT,
    lang TEXT DEFAULT 'ar',
    welcome TEXT,
    welcome_on INTEGER DEFAULT 1,
    antilink INTEGER DEFAULT 1,
    antiflood INTEGER DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS warnings (
    chat_id INTEGER,
    user_id INTEGER,
    count INTEGER DEFAULT 0,
    PRIMARY KEY (chat_id, user_id)
);
CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value INTEGER DEFAULT 0);
CREATE INDEX IF NOT EXISTS idx_msg_user ON messages(user_id);
"""

# migrations — تضمن وجود الأعمدة في القواعد القديمة
MIGRATIONS = [
    ("users",  "lang",         "TEXT DEFAULT 'ar'"),
    ("users",  "model",        "TEXT DEFAULT 'gpt-4o-mini'"),
    ("users",  "system_prompt","TEXT"),
    ("users",  "created_at",   "TIMESTAMP"),
    ("users",  "last_seen",    "TIMESTAMP"),
    ("users",  "msg_count",    "INTEGER DEFAULT 0"),
    ("users",  "tokens_used",  "INTEGER DEFAULT 0"),
    ("users",  "reaction_on",  "INTEGER DEFAULT 1"),
    ("users",  "is_banned",    "INTEGER DEFAULT 0"),
    ("groups", "lang",         "TEXT DEFAULT 'ar'"),
    ("groups", "welcome",      "TEXT"),
    ("groups", "welcome_on",   "INTEGER DEFAULT 1"),
    ("groups", "antilink",     "INTEGER DEFAULT 1"),
    ("groups", "antiflood",    "INTEGER DEFAULT 0"),
    ("groups", "added_at",     "TIMESTAMP"),
]

def db_init():
    with sqlite3.connect(DB_PATH, timeout=30) as c:
        c.executescript(SCHEMA)
        for table, col, coltype in MIGRATIONS:
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")
            except sqlite3.OperationalError:
                pass
        # تعبئة القيم الفارغة
        try:
            c.execute("UPDATE users SET lang='ar' WHERE lang IS NULL OR lang=''")
            c.execute("UPDATE users SET model='gpt-4o-mini' WHERE model IS NULL OR model=''")
            c.execute("UPDATE users SET reaction_on=1 WHERE reaction_on IS NULL")
            c.execute("UPDATE users SET is_banned=0 WHERE is_banned IS NULL")
            c.execute("UPDATE groups SET lang='ar' WHERE lang IS NULL OR lang=''")
            c.execute("UPDATE groups SET welcome_on=1 WHERE welcome_on IS NULL")
            c.execute("UPDATE groups SET antilink=1 WHERE antilink IS NULL")
        except Exception:
            pass
        c.commit()

db_init()

def db(sql: str, params=(), fetch: str = "none"):
    with sqlite3.connect(DB_PATH, timeout=30) as c:
        c.row_factory = sqlite3.Row
        cur = c.execute(sql, params)
        if fetch == "all": return [dict(r) for r in cur.fetchall()]
        if fetch == "one":
            r = cur.fetchone(); return dict(r) if r else None
        c.commit(); return cur.lastrowid

def stat_inc(key: str, n: int = 1):
    db("INSERT INTO stats(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value = value + ?",
       (key, n, n))

def stat_get(key: str) -> int:
    r = db("SELECT value FROM stats WHERE key=?", (key,), "one")
    return r["value"] if r else 0

# ═══════════════════════════════════════════════════════════════════════════
#                            OWNER
# ═══════════════════════════════════════════════════════════════════════════
def is_owner(user) -> bool:
    if user is None: return False
    if user.id in [x for x in OWNER_IDS if x]: return True
    if user.username:
        un = user.username.lower().lstrip("@")
        if un in [u.lower().lstrip("@") for u in OWNER_USERNAMES]: return True
    return False

# ═══════════════════════════════════════════════════════════════════════════
#                            FIREBASE
# ═══════════════════════════════════════════════════════════════════════════
class FirebaseClient:
    def __init__(self):
        self.session = requests.Session()
        self.fid = f"{uuid.uuid4().hex[:7]}-{uuid.uuid4().hex[:20]}"
        self.fcm = f"{self.fid}:{uuid.uuid4().hex[:32]}"
        self.session.headers.update({
            "content-type": "application/json; charset=utf-8",
            "accept-encoding": "gzip",
            "user-agent": USER_AGENT,
            "firebase-instance-id-token": self.fcm,
            "X-Android-Package": APP_PACKAGE,
            "X-Android-Cert": "085878EDBA0200080CA6CD94242C6ADBE21F28BA",
        })

    def _p1(self, messages, model):
        return {"data": {"messages": [{"role": m["role"], "content": m["content"]} for m in messages], "model": model}}

    def _p2(self, messages, model):
        return {"model": model, "messages": [{"role": m["role"], "content": m["content"]} for m in messages]}

    def _parse(self, data):
        try:
            result = data.get("result", data)
            choices = result.get("choices", [])
            if not choices: return None
            msg = choices[0].get("message", {})
            usage = result.get("usage", {})
            return {"content": msg.get("content", ""), "model": result.get("model", "?"),
                    "tokens": usage.get("total_tokens", 0)}
        except Exception: return None

    def send(self, messages, model, max_tokens=2000):
        for fn in (self._p1, self._p2):
            try:
                r = self.session.post(CHAT_ENDPOINT, json=fn(messages, model), timeout=90)
                if r.status_code == 200:
                    out = self._parse(r.json())
                    if out: return out
            except Exception as e:
                log.warning(f"send err: {e}")
        if model != "gpt-4o-mini":
            try:
                r = self.session.post(CHAT_ENDPOINT, json=self._p1(messages, "gpt-4o-mini"), timeout=90)
                if r.status_code == 200: return self._parse(r.json())
            except Exception: pass
        return None

    def send_image(self, image_b64: str, caption: str, model: str):
        content = [
            {"type": "text", "text": caption or "What is in this image?"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
        ]
        payload = {"data": {"model": model, "messages": [{"role": "user", "content": content}]}}
        try:
            r = self.session.post(CHAT_ENDPOINT, json=payload, timeout=120)
            if r.status_code == 200: return self._parse(r.json())
        except Exception as e:
            log.warning(f"vision err: {e}")
        return None

firebase = FirebaseClient()

# ═══════════════════════════════════════════════════════════════════════════
#                            HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def esc(s):
    if s is None: return ""
    return html.escape(str(s))

def split_message(text: str, size: int = MAX_MSG_LEN) -> List[str]:
    if len(text) <= size: return [text]
    parts = []
    while text:
        if len(text) <= size:
            parts.append(text); break
        cut = text.rfind("\n", 0, size)
        if cut < size // 2: cut = size
        parts.append(text[:cut]); text = text[cut:].lstrip("\n")
    return parts

async def send_long(msg, text: str, reply_markup=None):
    parts = split_message(text)
    for i, p in enumerate(parts):
        kb = reply_markup if i == len(parts) - 1 else None
        try:
            await msg.reply_text(p, parse_mode=ParseMode.HTML, reply_markup=kb, disable_web_page_preview=True)
        except BadRequest:
            await msg.reply_text(p, reply_markup=kb, disable_web_page_preview=True)

def with_sig(text: str) -> str:
    return f"{text}\n\n<i>— {SIGNATURE}</i>"

def ensure_user(u):
    if not u: return
    db("INSERT OR IGNORE INTO users(user_id, username, first_name) VALUES(?,?,?)",
       (u.id, u.username, u.first_name or ""))
    db("UPDATE users SET username=?, first_name=?, last_seen=? WHERE user_id=?",
       (u.username, u.first_name or "", datetime.utcnow().isoformat(), u.id))

def get_user(uid):
    row = db("SELECT * FROM users WHERE user_id=?", (uid,), "one")
    if row and not row.get("lang"):
        row["lang"] = "ar"
    return row

def get_user_lang(uid) -> str:
    u = get_user(uid)
    return (u.get("lang") if u else None) or "ar"

def set_user_lang(uid, lang):
    if lang in LANGS:
        db("UPDATE users SET lang=? WHERE user_id=?", (lang, uid))

def set_model(uid, m): db("UPDATE users SET model=? WHERE user_id=?", (m, uid))
def set_system(uid, p): db("UPDATE users SET system_prompt=? WHERE user_id=?", (p, uid))
def set_reaction(uid, v): db("UPDATE users SET reaction_on=? WHERE user_id=?", (v, uid))
def clear_history(uid): db("DELETE FROM messages WHERE user_id=?", (uid,))

def add_message(uid, role, content, model=None, tokens=0):
    db("INSERT INTO messages(user_id, role, content, model, tokens) VALUES(?,?,?,?,?)",
       (uid, role, content, model, tokens))
    if role == "user":
        db("UPDATE users SET msg_count = msg_count + 1 WHERE user_id=?", (uid,))
    elif tokens:
        db("UPDATE users SET tokens_used = tokens_used + ? WHERE user_id=?", (tokens, uid))

def get_history(uid, limit=MAX_HISTORY):
    rows = db("SELECT role, content FROM messages WHERE user_id=? ORDER BY id DESC LIMIT ?",
              (uid, limit), "all")
    return list(reversed(rows))

def build_system(model_id, user_system, lang="ar"):
    parts = []
    ident = MODELS.get(model_id, {}).get("identity", "")
    if ident: parts.append(ident)
    lang_instr = LANGS.get(lang, LANGS["ar"]).get("ai", "")
    if lang_instr: parts.append(lang_instr)
    if user_system: parts.append(user_system)
    return "\n\n".join(parts) if parts else DEFAULT_SYSTEM

async def react_to_message(update, emoji=None):
    try:
        e = emoji or random.choice(REACTION_POOL)
        await update.message.set_reaction([ReactionTypeEmoji(emoji=e)])
    except Exception: pass

def save_group(chat):
    if not chat or chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP): return
    db("INSERT OR IGNORE INTO groups(chat_id, title, username) VALUES(?,?,?)",
       (chat.id, chat.title or "", chat.username or ""))
    db("UPDATE groups SET title=?, username=? WHERE chat_id=?",
       (chat.title or "", chat.username or "", chat.id))

def get_group_lang(chat_id) -> str:
    g = db("SELECT lang FROM groups WHERE chat_id=?", (chat_id,), "one")
    return (g.get("lang") if g else None) or "ar"

# ═══════════════════════════════════════════════════════════════════════════
#                            KEYBOARDS
# ═══════════════════════════════════════════════════════════════════════════
def language_keyboard(prefix="lang"):
    rows = []
    items = list(LANGS.items())
    for i in range(0, len(items), 2):
        row = []
        for code, info in items[i:i+2]:
            row.append(InlineKeyboardButton(f"{info['flag']} {info['name']}",
                                            callback_data=f"{prefix}:{code}"))
        rows.append(row)
    return InlineKeyboardMarkup(rows)

def model_keyboard(current, lang="ar"):
    rows = []
    items = list(MODELS.items())
    for i in range(0, len(items), 2):
        row = []
        for mid, info in items[i:i+2]:
            mark = "◉ " if mid == current else ""
            row.append(InlineKeyboardButton(f"{mark}{info['emoji']} {info['name']}",
                                            callback_data=f"model:{mid}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(t(lang, "btn_back"), callback_data="nav:main")])
    return InlineKeyboardMarkup(rows)

def private_main_menu(owner: bool = False, lang="ar"):
    rows = [
        [InlineKeyboardButton(t(lang, "btn_models"),   callback_data="menu:model"),
         InlineKeyboardButton(t(lang, "btn_settings"), callback_data="menu:settings")],
        [InlineKeyboardButton(t(lang, "btn_stats"),    callback_data="menu:stats"),
         InlineKeyboardButton(t(lang, "btn_new_chat"), callback_data="menu:clear")],
        [InlineKeyboardButton(t(lang, "btn_debate"),   callback_data="menu:debate"),
         InlineKeyboardButton(t(lang, "btn_export"),   callback_data="menu:export")],
        [InlineKeyboardButton(t(lang, "btn_lang"),     callback_data="menu:lang"),
         InlineKeyboardButton(t(lang, "btn_help"),     callback_data="menu:help")],
    ]
    if owner:
        rows.append([InlineKeyboardButton(t(lang, "btn_owner"), callback_data="owner:panel")])
    return InlineKeyboardMarkup(rows)

def owner_panel_menu(lang="ar"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "owner_stats"),     callback_data="owner:stats"),
         InlineKeyboardButton(t(lang, "owner_users"),     callback_data="owner:users")],
        [InlineKeyboardButton(t(lang, "owner_groups"),    callback_data="owner:groups"),
         InlineKeyboardButton(t(lang, "owner_broadcast"), callback_data="owner:broadcast")],
        [InlineKeyboardButton(t(lang, "owner_tools"),     callback_data="owner:tools")],
        [InlineKeyboardButton(t(lang, "btn_back"),        callback_data="nav:main")],
    ])

def group_admin_menu(lang="ar"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(lang, "btn_settings"), callback_data="g:settings"),
         InlineKeyboardButton(t(lang, "btn_lang"),     callback_data="g:lang")],
    ])

# ═══════════════════════════════════════════════════════════════════════════
#                            AI GENERATION
# ═══════════════════════════════════════════════════════════════════════════
async def generate_reply(update, context, user_text: str, user_extra: str = "",
                         reply_target=None, group_mode=False, lang_override=None):
    u = update.effective_user
    ensure_user(u)
    user = get_user(u.id)

    if user and user.get("is_banned"):
        target = reply_target or update.message
        await target.reply_text(t(lang_override or get_user_lang(u.id), "banned"))
        return None

    lang = lang_override or (get_group_lang(update.effective_chat.id) if group_mode else get_user_lang(u.id))
    model = user["model"] or DEFAULT_MODEL
    system_prompt = build_system(model, user.get("system_prompt"), lang)
    target = reply_target or update.message

    try: await context.bot.send_chat_action(target.chat_id, ChatAction.TYPING)
    except Exception: pass

    history = get_history(u.id, MAX_HISTORY)
    messages = [{"role": "system", "content": system_prompt}]
    for h in history: messages.append({"role": h["role"], "content": h["content"]})
    full_input = user_text
    if user_extra: full_input = f"{user_text}\n\n[attachment: {user_extra}]"
    messages.append({"role": "user", "content": full_input})

    mname = MODELS.get(model, {}).get("name", model)
    placeholder = await target.reply_text(t(lang, "thinking", model=mname),
                                          parse_mode=ParseMode.HTML)

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, firebase.send, messages, model)

    if not response or not response.get("content"):
        await placeholder.edit_text(t(lang, "no_response"))
        return None

    reply = response["content"]
    tokens = response.get("tokens", 0)

    add_message(u.id, "user", full_input)
    add_message(u.id, "assistant", reply, model, tokens)
    stat_inc("ai_messages")

    if user.get("reaction_on", 1) and update.message:
        try: await react_to_message(update)
        except Exception: pass

    info = MODELS.get(model, {})
    header = f"<b>{info.get('emoji','🤖')} {info.get('name', model)}</b>"
    if tokens: header += f" <i>· {tokens}t</i>"
    body = with_sig(f"{header}\n\n{reply}")

    try: await placeholder.delete()
    except Exception: pass

    await send_long(target, body)
    return reply

async def generate_vision_reply(update, context, image_b64: str, caption: str,
                                 reply_target=None, group_mode=False, lang_override=None):
    u = update.effective_user
    ensure_user(u)
    user = get_user(u.id)
    lang = lang_override or (get_group_lang(update.effective_chat.id) if group_mode else get_user_lang(u.id))
    model = user["model"] or DEFAULT_MODEL
    target = reply_target or update.message

    try: await context.bot.send_chat_action(target.chat_id, ChatAction.TYPING)
    except Exception: pass

    mname = MODELS.get(model, {}).get("name", model)
    placeholder = await target.reply_text(t(lang, "vision", model=mname),
                                          parse_mode=ParseMode.HTML)

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, firebase.send_image, image_b64, caption, model)

    if not response or not response.get("content"):
        try: await placeholder.delete()
        except Exception: pass
        await generate_reply(update, context,
                             f"[User sent an image. Caption: {caption or 'none'}]",
                             user_extra="image", reply_target=target,
                             group_mode=group_mode, lang_override=lang)
        return

    reply = response["content"]
    tokens = response.get("tokens", 0)

    add_message(u.id, "user", f"[image] {caption}")
    add_message(u.id, "assistant", reply, model, tokens)
    stat_inc("ai_messages")

    if user.get("reaction_on", 1) and update.message:
        try: await react_to_message(update)
        except Exception: pass

    info = MODELS.get(model, {})
    header = f"<b>👁 {info.get('emoji','🤖')} {info.get('name', model)}</b>"
    body = with_sig(f"{header}\n\n{reply}")

    try: await placeholder.delete()
    except Exception: pass

    await send_long(target, body)

# ═══════════════════════════════════════════════════════════════════════════
#                        DEBATE  (AI vs AI)
# ═══════════════════════════════════════════════════════════════════════════
DEBATES: Dict[int, Dict] = {}
DEBATE_SETUP: Dict[int, Dict] = {}

async def cmd_debate(update, context):
    u = update.effective_user
    ensure_user(u)
    lang = get_user_lang(u.id)
    chat_id = update.effective_chat.id

    if chat_id in DEBATES and DEBATES[chat_id].get("active"):
        await update.message.reply_text(t(lang, "debate_already"))
        return

    DEBATE_SETUP[chat_id] = {"step": "m1", "lang": lang}
    rows = []
    items = list(MODELS.items())
    for i in range(0, len(items), 2):
        row = [InlineKeyboardButton(f"🅰️ {info['emoji']} {info['name']}",
                                    callback_data=f"db1:{mid}")
               for mid, info in items[i:i+2]]
        rows.append(row)
    rows.append([InlineKeyboardButton(t(lang, "btn_cancel"), callback_data="db:cancel")])
    await update.message.reply_text(t(lang, "debate_title"),
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=InlineKeyboardMarkup(rows))

async def cmd_stop(update, context):
    u = update.effective_user
    lang = get_user_lang(u.id)
    chat_id = update.effective_chat.id
    if chat_id in DEBATES:
        DEBATES[chat_id]["active"] = False
        await update.message.reply_text(t(lang, "debate_stopped"))
    else:
        await update.message.reply_text(t(lang, "debate_no_active"))

async def cmd_topic(update, context):
    u = update.effective_user
    lang = get_user_lang(u.id)
    chat_id = update.effective_chat.id
    state = DEBATE_SETUP.get(chat_id)
    if not state or state.get("step") != "topic":
        await update.message.reply_text(t(lang, "debate_start_first"))
        return
    topic = " ".join(context.args).strip() if context.args else ""
    if not topic:
        await update.message.reply_text(t(lang, "debate_topic_usage"), parse_mode=ParseMode.HTML)
        return

    m1 = state["m1"]; m2 = state["m2"]
    lang_saved = state.get("lang", lang)
    DEBATE_SETUP.pop(chat_id, None)

    DEBATES[chat_id] = {"active": True, "topic": topic, "m1": m1, "m2": m2,
                        "round": 0, "lang": lang_saved}

    a_name = MODELS[m1]['name']; b_name = MODELS[m2]['name']
    await update.message.reply_text(
        t(lang_saved, "debate_started", topic=esc(topic),
          a=f"{MODELS[m1]['emoji']} {a_name}", b=f"{MODELS[m2]['emoji']} {b_name}"),
        parse_mode=ParseMode.HTML)
    asyncio.create_task(debate_loop(context, chat_id))

async def debate_loop(context, chat_id):
    state = DEBATES.get(chat_id)
    if not state: return

    topic = state["topic"]
    m1, m2 = state["m1"], state["m2"]
    lang = state.get("lang", "ar")
    history: List[Dict] = []

    while DEBATES.get(chat_id, {}).get("active"):
        state["round"] += 1
        r = state["round"]
        current = m1 if r % 2 == 1 else m2
        other = m2 if current == m1 else m1
        icon = "🅰️" if current == m1 else "🅱️"

        sys_prompt = (
            f"{MODELS[current]['identity']}\n\n"
            f"{LANGS.get(lang, LANGS['ar'])['ai']}\n\n"
            f"You are in a formal debate with {MODELS[other]['name']}. Topic: {topic}. "
            "Present concise arguments (2-4 sentences), respond to the other side, "
            "do not repeat, no special formatting."
        )

        msgs = [{"role": "system", "content": sys_prompt}]
        for h in history[-14:]: msgs.append(h)
        if not history:
            msgs.append({"role": "user", "content": f"Begin the debate about: {topic}"})

        try: await context.bot.send_chat_action(chat_id, ChatAction.TYPING)
        except Exception: pass

        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, firebase.send, msgs, current)

        if not resp or not resp.get("content"):
            try:
                await context.bot.send_message(chat_id,
                    f"⚠️ {MODELS[current]['name']} — no response.")
            except Exception: pass
            break

        text = resp["content"].strip()
        body = f"{icon} <b>{esc(MODELS[current]['name'])}</b>\n{esc(text)}"

        for p in split_message(body):
            try: await context.bot.send_message(chat_id, p, parse_mode=ParseMode.HTML)
            except Exception: pass

        history.append({"role": "assistant", "content": f"[{MODELS[current]['name']}]: {text}"})

        if not DEBATES.get(chat_id, {}).get("active"): break
        await asyncio.sleep(2)

    DEBATES.pop(chat_id, None)
    try:
        await context.bot.send_message(chat_id, t(lang, "debate_finished"),
                                       parse_mode=ParseMode.HTML)
    except Exception: pass

# ═══════════════════════════════════════════════════════════════════════════
#                        START / LANGUAGE FLOW
# ═══════════════════════════════════════════════════════════════════════════
def brand_header():
    return f"<b>⚡ {BRAND}</b>  ·  <i>v{VERSION}</i>"

async def cmd_start(update, context):
    u = update.effective_user
    ensure_user(u)
    user = get_user(u.id)
    lang = user.get("lang")

    if not lang or lang not in LANGS:
        await update.message.reply_text(
            t("ar", "choose_lang") + "\n\n<b>Choose your language:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=language_keyboard("setlang"))
        return

    owner = is_owner(u)
    model = user["model"] or DEFAULT_MODEL
    info = MODELS.get(model, {})
    lang_info = LANGS.get(lang, LANGS["ar"])

    txt = (
        f"{brand_header()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{t(lang, 'welcome', name=esc(u.first_name or 'friend'))}\n\n"
        f"<b>{t(lang, 'lang_label')}:</b> {lang_info['flag']} {lang_info['name']}\n"
        f"<b>{t(lang, 'btn_models')}:</b> {info.get('emoji','🤖')} {info.get('name', model)}\n\n"
        f"<i>{t(lang, 'help_text').split(chr(10), 1)[0]}</i>"
    )
    await update.message.reply_text(txt, parse_mode=ParseMode.HTML,
                                    reply_markup=private_main_menu(owner, lang))

async def cmd_lang(update, context):
    u = update.effective_user
    ensure_user(u)
    lang = get_user_lang(u.id)
    await update.message.reply_text(
        t(lang, "choose_lang"),
        parse_mode=ParseMode.HTML,
        reply_markup=language_keyboard("setlang"))

async def on_setlang(update, context):
    q = update.callback_query
    code = q.data.split(":", 1)[1]
    u = q.from_user
    ensure_user(u)
    if code not in LANGS:
        await q.answer("Invalid", show_alert=True); return
    set_user_lang(u.id, code)
    info = LANGS[code]
    await q.answer(f"{info['flag']} {info['name']}")
    await q.edit_message_text(
        t(code, "lang_set", name=f"{info['flag']} {info['name']}") + "\n\n" +
        t(code, "welcome", name=esc(u.first_name or "friend")),
        parse_mode=ParseMode.HTML,
        reply_markup=private_main_menu(is_owner(u), code))

# ═══════════════════════════════════════════════════════════════════════════
#                        OWNER PANEL
# ═══════════════════════════════════════════════════════════════════════════
OWNER_STATE: Dict[int, Dict] = {}

async def cmd_admin(update, context):
    if not is_owner(update.effective_user):
        await update.message.reply_text(t(get_user_lang(update.effective_user.id), "owner_only"))
        return
    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(
        t(lang, "owner_panel"), parse_mode=ParseMode.HTML,
        reply_markup=owner_panel_menu(lang))

async def owner_stats(update, context):
    q = update.callback_query
    u = q.from_user
    if not is_owner(u):
        await q.answer("Unauthorized", show_alert=True); return
    lang = get_user_lang(u.id)
    total_u = db("SELECT COUNT(*) c FROM users", fetch="one")["c"]
    banned_u = db("SELECT COUNT(*) c FROM users WHERE is_banned=1", fetch="one")["c"]
    msgs = db("SELECT COUNT(*) c FROM messages", fetch="one")["c"]
    groups = db("SELECT COUNT(*) c FROM groups", fetch="one")["c"]
    tokens = db("SELECT COALESCE(SUM(tokens),0) s FROM messages", fetch="one")["s"]
    txt = (
        f"{t(lang, 'owner_stats')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Users: <b>{total_u}</b>  ·  🚫 Banned: <b>{banned_u}</b>\n"
        f"💬 Messages: <b>{msgs}</b>\n"
        f"🤖 AI: <b>{stat_get('ai_messages')}</b>\n"
        f"🔢 Tokens: <b>{tokens}</b>\n"
        f"💬 Groups: <b>{groups}</b>\n\n"
        f"📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
    )
    await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=owner_panel_menu(lang))

async def owner_users(update, context):
    q = update.callback_query
    u = q.from_user
    if not is_owner(u):
        await q.answer("Unauthorized", show_alert=True); return
    lang = get_user_lang(u.id)
    rows = db("SELECT user_id, username, first_name, lang, msg_count, is_banned "
              "FROM users ORDER BY last_seen DESC LIMIT 30", fetch="all")
    if not rows:
        await q.edit_message_text(t(lang, "no_data"), reply_markup=owner_panel_menu(lang)); return
    lines = [f"{t(lang, 'owner_users')}", ""]
    for r in rows:
        un = f"@{r['username']}" if r.get("username") else "—"
        ban = "🚫" if r.get("is_banned") else ""
        lg = r.get("lang", "ar") or "ar"
        lines.append(f"{ban} <b>{esc(r.get('first_name') or '—')}</b> · {un} · "
                     f"<code>{r['user_id']}</code> · {LANGS.get(lg,{}).get('flag','')}{lg} · 💬{r['msg_count']}")
    txt = "\n".join(lines)
    if len(txt) > 4000: txt = txt[:4000] + "\n..."
    await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=owner_panel_menu(lang))

async def owner_groups(update, context):
    q = update.callback_query
    u = q.from_user
    if not is_owner(u):
        await q.answer("Unauthorized", show_alert=True); return
    lang = get_user_lang(u.id)
    rows = db("SELECT chat_id, title, username, lang FROM groups ORDER BY added_at DESC LIMIT 50", fetch="all")
    if not rows:
        await q.edit_message_text(t(lang, "no_data"), reply_markup=owner_panel_menu(lang)); return
    lines = [f"{t(lang, 'owner_groups')} ({len(rows)})", ""]
    for g in rows:
        un = f"@{g['username']}" if g.get("username") else "—"
        lg = g.get("lang", "ar") or "ar"
        lines.append(f"• <b>{esc(g['title'] or '—')}</b>\n  {un} · <code>{g['chat_id']}</code> · {LANGS.get(lg,{}).get('flag','')}{lg}")
    txt = "\n".join(lines)
    if len(txt) > 4000: txt = txt[:4000] + "\n..."
    await q.edit_message_text(txt, parse_mode=ParseMode.HTML, reply_markup=owner_panel_menu(lang))

async def owner_broadcast_start(update, context):
    q = update.callback_query
    u = q.from_user
    if not is_owner(u):
        await q.answer("Unauthorized", show_alert=True); return
    lang = get_user_lang(u.id)
    OWNER_STATE[u.id] = {"step": "broadcast"}
    await q.edit_message_text(t(lang, "broadcast_prompt"), parse_mode=ParseMode.HTML)

async def owner_msg_handler(update, context, text: str) -> bool:
    u = update.effective_user
    state = OWNER_STATE.get(u.id)
    if not state: return False
    lang = get_user_lang(u.id)

    if state["step"] == "broadcast":
        OWNER_STATE.pop(u.id, None)
        rows = db("SELECT user_id FROM users WHERE is_banned=0", fetch="all")
        status = await update.message.reply_text(t(lang, "broadcast_sending", n=len(rows)))
        sent = fail = 0
        for i, r in enumerate(rows):
            try:
                await context.bot.send_message(r["user_id"], text, parse_mode=ParseMode.HTML)
                sent += 1
            except Exception:
                fail += 1
            if (i + 1) % 20 == 0:
                try: await status.edit_text(f"📤 {i+1}/{len(rows)} · ✅ {sent} · ❌ {fail}")
                except Exception: pass
            await asyncio.sleep(0.05)
        await status.edit_text(t(lang, "broadcast_done", ok=sent, fail=fail))
        return True
    return False

# ═══════════════════════════════════════════════════════════════════════════
#                        PRIVATE COMMANDS
# ═══════════════════════════════════════════════════════════════════════════
async def cmd_help(update, context):
    u = update.effective_user
    ensure_user(u)
    lang = get_user_lang(u.id)
    await update.message.reply_text(t(lang, "help_text"), parse_mode=ParseMode.HTML)

async def cmd_model(update, context):
    u = update.effective_user
    ensure_user(u)
    lang = get_user_lang(u.id)
    user = get_user(u.id)
    cur = user["model"] or DEFAULT_MODEL
    info = MODELS.get(cur, {})
    await update.message.reply_text(
        t(lang, "models_title", cur=f"{info.get('emoji','🤖')} {info.get('name', cur)}"),
        parse_mode=ParseMode.HTML, reply_markup=model_keyboard(cur, lang))

async def cmd_clear(update, context):
    u = update.effective_user
    ensure_user(u)
    lang = get_user_lang(u.id)
    clear_history(u.id)
    await update.message.reply_text(t(lang, "new_chat_done"))

async def cmd_system(update, context):
    u = update.effective_user
    ensure_user(u)
    lang = get_user_lang(u.id)
    if not context.args:
        user = get_user(u.id)
        cur = user.get("system_prompt") or "—"
        await update.message.reply_text(
            f"{t(lang, 'system_prompt_label')}\n\n<code>{esc(cur)}</code>\n\n" +
            t(lang, "system_usage"),
            parse_mode=ParseMode.HTML)
        return
    new = " ".join(context.args).strip()
    if new == "-":
        set_system(u.id, "")
        await update.message.reply_text(t(lang, "system_deleted"))
        return
    set_system(u.id, new)
    await update.message.reply_text(t(lang, "system_updated"))

async def cmd_stats(update, context):
    u = update.effective_user
    ensure_user(u)
    lang = get_user_lang(u.id)
    user = get_user(u.id)
    total = db("SELECT COUNT(*) c FROM messages WHERE user_id=?", (u.id,), "one")["c"]
    info = MODELS.get(user["model"], {})
    lang_info = LANGS.get(lang, LANGS["ar"])
    await update.message.reply_text(
        f"{t(lang, 'stats_title')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 <code>{u.id}</code>\n"
        f"🤖 {info.get('emoji','🤖')} {info.get('name', user['model'])}\n"
        f"{t(lang, 'lang_label')}: {lang_info['flag']} {lang_info['name']}\n"
        f"{t(lang, 'msgs_label')}: <b>{user['msg_count']}</b>\n"
        f"📨 Stored: <b>{total}</b>\n"
        f"{t(lang, 'tokens_label')}: <b>{user['tokens_used']}</b>\n"
        f"{t(lang, 'reaction_label')}: {t(lang, 'on') if user.get('reaction_on',1) else t(lang, 'off')}",
        parse_mode=ParseMode.HTML)

async def cmd_export(update, context):
    u = update.effective_user
    ensure_user(u)
    lang = get_user_lang(u.id)
    history = get_history(u.id, 200)
    if not history:
        await update.message.reply_text(t(lang, "export_empty"))
        return
    lines = [f"# {BRAND} Export — {u.first_name}",
             f"# {datetime.utcnow().isoformat()}",
             f"# {SIGNATURE}", ""]
    for h in history:
        role = t(lang, "you") if h["role"] == "user" else t(lang, "ai")
        lines.append(f"## {role}\n{h['content']}\n")
    content = "\n".join(lines)
    bio = io.BytesIO(content.encode("utf-8"))
    bio.name = f"nexus_{u.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    await update.message.reply_document(document=bio, filename=bio.name,
                                        caption=t(lang, "export_caption", n=len(history)))

async def cmd_reaction(update, context):
    u = update.effective_user
    ensure_user(u)
    lang = get_user_lang(u.id)
    if not context.args:
        user = get_user(u.id)
        state = t(lang, "on") if user.get("reaction_on",1) else t(lang, "off")
        await update.message.reply_text(
            f"{t(lang, 'reaction_label')}: {state}\n\n" + t(lang, "reaction_usage"),
            parse_mode=ParseMode.HTML)
        return
    v = context.args[0].lower()
    if v in ("on","1","yes"):
        set_reaction(u.id, 1); await update.message.reply_text(t(lang, "reaction_on_ok"))
    elif v in ("off","0","no"):
        set_reaction(u.id, 0); await update.message.reply_text(t(lang, "reaction_off_ok"))
    else: await update.message.reply_text(t(lang, "reaction_usage"), parse_mode=ParseMode.HTML)

async def cmd_myid(update, context):
    u = update.effective_user
    un = f"@{u.username}" if u.username else "—"
    await update.message.reply_text(
        f"🆔 <code>{u.id}</code>\n💬 <code>{update.effective_chat.id}</code>\n🔗 {un}",
        parse_mode=ParseMode.HTML)

# ═══════════════════════════════════════════════════════════════════════════
#                        GROUP MODERATION
# ═══════════════════════════════════════════════════════════════════════════
async def is_admin_in(update, context, uid=None):
    uid = uid or update.effective_user.id
    try:
        m = await context.bot.get_chat_member(update.effective_chat.id, uid)
        return m.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception: return False

async def get_target_user(update, context):
    msg = update.message
    if msg.reply_to_message and msg.reply_to_message.from_user:
        return msg.reply_to_message.from_user
    if context.args:
        arg = context.args[0].lstrip("@")
        if arg.isdigit() or (arg.startswith("-") and arg[1:].isdigit()):
            try: return await context.bot.get_chat(int(arg))
            except Exception: return None
        try: return await context.bot.get_chat("@" + arg)
        except Exception: return None
    return None

async def cmd_mute(update, context):
    lang = get_group_lang(update.effective_chat.id)
    if not await is_admin_in(update, context):
        await update.message.reply_text(t(lang, "admin_only")); return
    target = await get_target_user(update, context)
    if not target: await update.message.reply_text(t(lang, "reply_or_user")); return
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id,
            permissions=ChatPermissions(can_send_messages=False))
        await update.message.reply_text(t(lang, "muted", name=esc(target.first_name or target.username)))
    except Exception as e: await update.message.reply_text(f"❌ {esc(e)}")

async def cmd_unmute(update, context):
    lang = get_group_lang(update.effective_chat.id)
    if not await is_admin_in(update, context):
        await update.message.reply_text(t(lang, "admin_only")); return
    target = await get_target_user(update, context)
    if not target: await update.message.reply_text(t(lang, "specify_user")); return
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id,
            permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                can_send_other_messages=True, can_add_web_page_previews=True))
        await update.message.reply_text(t(lang, "unmuted", name=esc(target.first_name or target.username)))
    except Exception as e: await update.message.reply_text(f"❌ {esc(e)}")

async def cmd_kick(update, context):
    lang = get_group_lang(update.effective_chat.id)
    if not await is_admin_in(update, context):
        await update.message.reply_text(t(lang, "admin_only")); return
    target = await get_target_user(update, context)
    if not target: await update.message.reply_text(t(lang, "specify_user")); return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(t(lang, "kicked", name=esc(target.first_name or target.username)))
    except Exception as e: await update.message.reply_text(f"❌ {esc(e)}")

async def cmd_ban(update, context):
    lang = get_group_lang(update.effective_chat.id)
    if not await is_admin_in(update, context):
        await update.message.reply_text(t(lang, "admin_only")); return
    target = await get_target_user(update, context)
    if not target: await update.message.reply_text(t(lang, "specify_user")); return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(t(lang, "banned_user", name=esc(target.first_name or target.username)))
    except Exception as e: await update.message.reply_text(f"❌ {esc(e)}")

async def cmd_unban(update, context):
    lang = get_group_lang(update.effective_chat.id)
    if not await is_admin_in(update, context):
        await update.message.reply_text(t(lang, "admin_only")); return
    target = await get_target_user(update, context)
    if not target: await update.message.reply_text(t(lang, "specify_user")); return
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(t(lang, "unbanned_user", name=esc(target.first_name or target.username)))
    except Exception as e: await update.message.reply_text(f"❌ {esc(e)}")

async def cmd_warn(update, context):
    lang = get_group_lang(update.effective_chat.id)
    if not await is_admin_in(update, context):
        await update.message.reply_text(t(lang, "admin_only")); return
    target = await get_target_user(update, context)
    if not target: await update.message.reply_text(t(lang, "specify_user")); return
    db("INSERT INTO warnings(chat_id,user_id,count) VALUES(?,?,1) "
       "ON CONFLICT(chat_id,user_id) DO UPDATE SET count=count+1",
       (update.effective_chat.id, target.id))
    r = db("SELECT count FROM warnings WHERE chat_id=? AND user_id=?",
           (update.effective_chat.id, target.id), "one")
    count = r["count"] if r else 1
    if count >= 3:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, target.id)
            await update.message.reply_text(t(lang, "warn_banned", name=esc(target.first_name)))
            db("DELETE FROM warnings WHERE chat_id=? AND user_id=?",
               (update.effective_chat.id, target.id)); return
        except Exception: pass
    await update.message.reply_text(t(lang, "warned", n=count, name=esc(target.first_name)))

async def cmd_unlockall(update, context):
    lang = get_group_lang(update.effective_chat.id)
    if not await is_admin_in(update, context):
        await update.message.reply_text(t(lang, "admin_only")); return
    try:
        await context.bot.set_chat_permissions(update.effective_chat.id,
            ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                can_send_other_messages=True, can_add_web_page_previews=True,
                can_send_polls=True, can_invite_users=True))
        await update.message.reply_text(t(lang, "unlock_all"))
    except Exception as e: await update.message.reply_text(f"❌ {esc(e)}")

async def cmd_welcome(update, context):
    lang = get_group_lang(update.effective_chat.id)
    if not await is_admin_in(update, context):
        await update.message.reply_text(t(lang, "admin_only")); return
    if not context.args:
        await update.message.reply_text(t(lang, "welcome_usage"), parse_mode=ParseMode.HTML)
        return
    text = " ".join(context.args)
    db("UPDATE groups SET welcome=? WHERE chat_id=?", (text, update.effective_chat.id))
    await update.message.reply_text(t(lang, "welcome_saved"))

async def cmd_antilink(update, context):
    lang = get_group_lang(update.effective_chat.id)
    if not await is_admin_in(update, context):
        await update.message.reply_text(t(lang, "admin_only")); return
    if not context.args or context.args[0] not in ("on","off"):
        await update.message.reply_text(t(lang, "antilink_usage"), parse_mode=ParseMode.HTML); return
    v = 1 if context.args[0] == "on" else 0
    db("UPDATE groups SET antilink=? WHERE chat_id=?", (v, update.effective_chat.id))
    await update.message.reply_text(t(lang, "antilink_on") if v else t(lang, "antilink_off"))

async def cmd_settings(update, context):
    if not await is_admin_in(update, context): return
    lang = get_group_lang(update.effective_chat.id)
    g = db("SELECT * FROM groups WHERE chat_id=?", (update.effective_chat.id,), "one")
    if not g:
        await update.message.reply_text("⚠️"); return
    lang_info = LANGS.get(g.get("lang","ar") or "ar", LANGS["ar"])
    txt = (
        f"{t(lang, 'group_settings')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👋 Welcome: {'✅' if g.get('welcome_on') else '❌'}\n"
        f"🔗 Antilink: {'✅' if g.get('antilink') else '❌'}\n"
        f"🌐 Language: {lang_info['flag']} {lang_info['name']}\n"
        f"📝 Text: <code>{esc(g.get('welcome') or '—')}</code>"
    )
    await update.message.reply_text(txt, parse_mode=ParseMode.HTML,
                                    reply_markup=group_admin_menu(lang))

async def cmd_gadmin(update, context):
    lang = get_group_lang(update.effective_chat.id)
    if not await is_admin_in(update, context):
        await update.message.reply_text(t(lang, "admin_only")); return
    await update.message.reply_text(t(lang, "group_admin_title"),
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=group_admin_menu(lang))

async def cmd_group_lang(update, context):
    if not await is_admin_in(update, context):
        lang = get_group_lang(update.effective_chat.id)
        await update.message.reply_text(t(lang, "admin_only")); return
    await update.message.reply_text(
        "🌐 <b>Group Language</b>\n\n" + t("ar", "choose_lang"),
        parse_mode=ParseMode.HTML,
        reply_markup=language_keyboard("glang"))

async def on_set_group_lang(update, context):
    q = update.callback_query
    code = q.data.split(":", 1)[1]
    if code not in LANGS:
        await q.answer("Invalid", show_alert=True); return
    try:
        m = await context.bot.get_chat_member(q.message.chat_id, q.from_user.id)
        if m.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
            await q.answer("Admins only", show_alert=True); return
    except Exception: return
    db("UPDATE groups SET lang=? WHERE chat_id=?", (code, q.message.chat_id))
    info = LANGS[code]
    await q.answer(f"{info['flag']} {info['name']}")
    await q.edit_message_text(
        t(code, "lang_set", name=f"{info['flag']} {info['name']}"),
        parse_mode=ParseMode.HTML)

# ═══════════════════════════════════════════════════════════════════════════
#                        GROUP EVENTS
# ═══════════════════════════════════════════════════════════════════════════
async def on_new_members(update, context):
    chat = update.effective_chat
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP): return
    save_group(chat)
    g = db("SELECT * FROM groups WHERE chat_id=?", (chat.id,), "one")
    lang = get_group_lang(chat.id)
    if g and g.get("welcome_on", 1):
        template = g.get("welcome") or f"👋 Welcome {{name}} in {{chat}}!\n\n<i>— {SIGNATURE}</i>"
        for m in update.message.new_chat_members:
            if m.is_bot: continue
            try:
                txt = template.format(name=m.first_name or "user", chat=chat.title or "")
                await update.message.reply_text(txt, parse_mode=ParseMode.HTML)
            except Exception:
                await update.message.reply_text(f"👋 {m.first_name or 'user'}")

async def on_my_chat_member(update, context):
    cmu = update.my_chat_member
    if not cmu: return
    chat = cmu.chat
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP): return
    save_group(chat)
    new = cmu.new_chat_member
    if new and new.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR):
        lang = get_group_lang(chat.id)
        try:
            await context.bot.send_message(
                chat.id, t(lang, "group_joined_hint"),
                parse_mode=ParseMode.HTML)
        except Exception: pass

URL_RE = re.compile(r"(https?://|t\.me/|telegram\.me/|www\.)\S+", re.IGNORECASE)

async def on_group_text(update, context):
    chat = update.effective_chat
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP): return
    save_group(chat)

    msg = update.message
    if not msg or not msg.text: return
    text = msg.text.strip()
    lang = get_group_lang(chat.id)

    g = db("SELECT * FROM groups WHERE chat_id=?", (chat.id,), "one")
    if g and g.get("antilink"):
        if not await is_admin_in(update, context):
            if URL_RE.search(text):
                try:
                    await msg.delete()
                    m = await chat.send_message(t(lang, "link_blocked",
                                                   name=esc(msg.from_user.first_name)))
                    await asyncio.sleep(4)
                    try: await m.delete()
                    except Exception: pass
                    return
                except Exception: pass

    low = text.lower()
    should_respond = False
    ai_text = text
    if low.startswith("ch "):
        should_respond = True; ai_text = text[3:].strip()
    elif msg.reply_to_message and msg.reply_to_message.from_user and \
         msg.reply_to_message.from_user.id == context.bot.id:
        should_respond = True
    else:
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower().lstrip("/").split("@")[0]
        if cmd in ("model","ai") and len(parts) > 1:
            should_respond = True; ai_text = parts[1]

    if not should_respond: return
    await generate_reply(update, context, ai_text, group_mode=True, reply_target=msg)

async def on_group_photo(update, context):
    chat = update.effective_chat
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP): return
    save_group(chat)
    msg = update.message
    caption = msg.caption or ""
    low = caption.lower()
    respond = False
    text = caption
    if low.startswith("ch "):
        respond = True; text = caption[3:].strip()
    elif msg.reply_to_message and msg.reply_to_message.from_user and \
         msg.reply_to_message.from_user.id == context.bot.id:
        respond = True
    if not respond: return
    photo = msg.photo[-1] if msg.photo else None
    if not photo: return
    try:
        f = await photo.get_file()
        bio = io.BytesIO()
        await f.download_to_memory(bio)
        b64 = base64.b64encode(bio.getvalue()).decode()
        await generate_vision_reply(update, context, b64, text, group_mode=True, reply_target=msg)
    except Exception: log.exception("group photo")

async def on_group_document(update, context):
    chat = update.effective_chat
    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP): return
    save_group(chat)
    msg = update.message
    caption = msg.caption or ""
    low = caption.lower()
    respond = False
    text = caption
    if low.startswith("ch "):
        respond = True; text = caption[3:].strip()
    elif msg.reply_to_message and msg.reply_to_message.from_user and \
         msg.reply_to_message.from_user.id == context.bot.id:
        respond = True
    if not respond: return

    doc = msg.document
    fname = doc.file_name or "file"
    mime = doc.mime_type or ""
    size = doc.file_size or 0
    text_content = None
    text_types = ("text/", "application/json", "application/xml", "application/javascript",
                  "application/x-python", "application/x-sh")
    if any(mime.startswith(t_) for t_ in text_types) or fname.endswith((
        ".py",".js",".ts",".json",".html",".css",".md",".txt",".xml",".yaml",".yml",".sh",
        ".c",".cpp",".h",".hpp",".java",".go",".rs",".php",".rb",".sql",".log",".ini",".conf",".env")):
        try:
            f = await doc.get_file()
            bio = io.BytesIO()
            await f.download_to_memory(bio)
            data = bio.getvalue()
            if len(data) <= 100_000:
                text_content = data.decode("utf-8", errors="replace")
        except Exception: pass
    if text_content is not None:
        prompt = (f"[File '{fname}' | {size}b]\n```\n{text_content[:8000]}\n```\n"
                  f"Request: {text or 'Analyze'}")
        await generate_reply(update, context, prompt, group_mode=True, reply_target=msg)
    else:
        info = f"file {fname} ({mime or '—'}, {size}b)"
        await generate_reply(update, context,
                             f"[User sent file: {fname}] Request: {text or 'Reply'}",
                             user_extra=info, group_mode=True, reply_target=msg)

# ═══════════════════════════════════════════════════════════════════════════
#                        PRIVATE ATTACHMENTS
# ═══════════════════════════════════════════════════════════════════════════
async def on_photo(update, context):
    u = update.effective_user
    ensure_user(u)
    photo = update.message.photo[-1] if update.message.photo else None
    if not photo: return
    caption = update.message.caption or ""
    try:
        f = await photo.get_file()
        bio = io.BytesIO()
        await f.download_to_memory(bio)
        b64 = base64.b64encode(bio.getvalue()).decode()
        await generate_vision_reply(update, context, b64, caption)
    except Exception as e:
        log.exception("photo")
        await update.message.reply_text(f"❌ {esc(e)}", parse_mode=ParseMode.HTML)

async def on_sticker(update, context):
    u = update.effective_user
    ensure_user(u)
    st = update.message.sticker
    info = f"sticker | emoji={st.emoji or '—'}"
    try:
        f = await st.get_file()
        bio = io.BytesIO()
        await f.download_to_memory(bio)
        b64 = base64.b64encode(bio.getvalue()).decode()
        prompt = f"[User sent sticker. Emoji: {st.emoji or '—'}. Respond appropriately.]"
        await generate_vision_reply(update, context, b64, prompt)
    except Exception:
        await generate_reply(update, context, f"[sticker: {info}]", user_extra=info)

async def on_document(update, context):
    u = update.effective_user
    ensure_user(u)
    doc = update.message.document
    caption = update.message.caption or ""
    fname = doc.file_name or "file"
    mime = doc.mime_type or ""
    size = doc.file_size or 0
    text_content = None
    text_types = ("text/", "application/json", "application/xml", "application/javascript",
                  "application/x-python", "application/x-sh")
    if any(mime.startswith(t_) for t_ in text_types) or fname.endswith((
        ".py",".js",".ts",".json",".html",".css",".md",".txt",".xml",".yaml",".yml",".sh",
        ".c",".cpp",".h",".hpp",".java",".go",".rs",".php",".rb",".sql",".log",".ini",".conf",".env")):
        try:
            f = await doc.get_file()
            bio = io.BytesIO()
            await f.download_to_memory(bio)
            data = bio.getvalue()
            if len(data) <= 100_000:
                text_content = data.decode("utf-8", errors="replace")
        except Exception: pass
    if text_content is not None:
        prompt = (f"[File '{fname}' | {size}b]\n```\n{text_content[:8000]}\n```\n"
                  f"Request: {caption or 'Analyze'}")
        await generate_reply(update, context, prompt)
    else:
        info = f"file {fname} ({mime or '—'}, {size}b)"
        await generate_reply(update, context,
                             f"[User sent file: {fname}] Request: {caption or 'Reply'}",
                             user_extra=info)

async def on_voice(update, context):
    u = update.effective_user
    ensure_user(u)
    lang = get_user_lang(u.id)
    await update.message.reply_text(t(lang, "voice_unsupported"))

# ═══════════════════════════════════════════════════════════════════════════
#                        PRIVATE TEXT
# ═══════════════════════════════════════════════════════════════════════════
async def on_text(update, context):
    msg = update.message
    if not msg or not msg.text: return
    text = msg.text.strip()
    if not text: return
    u = update.effective_user
    ensure_user(u)
    lang = get_user_lang(u.id)

    if is_owner(u) and OWNER_STATE.get(u.id):
        if await owner_msg_handler(update, context, text): return

    if len(text) > 3000:
        await msg.reply_text(t(lang, "long_message"))
        return

    await generate_reply(update, context, text)

# ═══════════════════════════════════════════════════════════════════════════
#                        CALLBACKS
# ═══════════════════════════════════════════════════════════════════════════
async def on_callback(update, context):
    q = update.callback_query
    data = q.data or ""
    u = q.from_user
    ensure_user(u)
    lang = get_user_lang(u.id)
    owner = is_owner(u)

    try: await q.answer()
    except Exception: pass

    if data.startswith("setlang:"):
        await on_setlang(update, context); return
    if data.startswith("glang:"):
        await on_set_group_lang(update, context); return

    if data.startswith("owner:"):
        if not owner:
            await q.answer("Unauthorized", show_alert=True); return
        action = data.split(":", 1)[1]
        if action == "panel":
            await q.edit_message_text(t(lang, "owner_panel"),
                                      parse_mode=ParseMode.HTML,
                                      reply_markup=owner_panel_menu(lang))
        elif action == "stats": await owner_stats(update, context)
        elif action == "users": await owner_users(update, context)
        elif action == "groups": await owner_groups(update, context)
        elif action == "broadcast": await owner_broadcast_start(update, context)
        elif action == "tools":
            await q.edit_message_text(t(lang, "owner_tools"),
                                      reply_markup=owner_panel_menu(lang))
        return

    if data.startswith("model:"):
        mid = data.split(":", 1)[1]
        if mid not in MODELS: return
        set_model(u.id, mid)
        info = MODELS[mid]
        await q.edit_message_text(
            t(lang, "model_changed", name=f"{info['emoji']} {info['name']}"),
            parse_mode=ParseMode.HTML,
            reply_markup=model_keyboard(mid, lang))
        return

    if data.startswith("db1:"):
        mid = data.split(":", 1)[1]
        if mid == "cancel":
            DEBATE_SETUP.pop(q.message.chat_id, None)
            await q.edit_message_text("❌"); return
        if mid not in MODELS: return
        DEBATE_SETUP[q.message.chat_id] = {"step": "m2", "m1": mid, "lang": lang}
        rows = []
        items = list(MODELS.items())
        for i in range(0, len(items), 2):
            row = []
            for m2_, info in items[i:i+2]:
                mark = "✅ " if m2_ == mid else ""
                row.append(InlineKeyboardButton(f"{mark}🅱️ {info['emoji']} {info['name']}",
                                                callback_data=f"db2:{m2_}"))
            rows.append(row)
        rows.append([InlineKeyboardButton(t(lang, "btn_cancel"), callback_data="db:cancel")])
        await q.edit_message_text(
            t(lang, "debate_choose_b", a=MODELS[mid]['name']),
            parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows))
        return

    if data.startswith("db2:"):
        mid2 = data.split(":", 1)[1]
        state = DEBATE_SETUP.get(q.message.chat_id)
        if not state: return
        mid1 = state.get("m1")
        if mid1 == mid2:
            await q.answer(t(lang, "debate_model_same"), show_alert=True); return
        state["m2"] = mid2
        state["step"] = "topic"
        await q.edit_message_text(
            t(lang, "debate_choose_topic",
              a=f"{MODELS[mid1]['emoji']} {MODELS[mid1]['name']}",
              b=f"{MODELS[mid2]['emoji']} {MODELS[mid2]['name']}"),
            parse_mode=ParseMode.HTML)
        return

    if data == "db:cancel":
        DEBATE_SETUP.pop(q.message.chat_id, None)
        await q.edit_message_text("❌"); return

    if data == "nav:main":
        if q.message.chat.type == ChatType.PRIVATE:
            await q.edit_message_text("🏠", reply_markup=private_main_menu(owner, lang))
        return

    if data.startswith("menu:"):
        action = data.split(":", 1)[1]
        user = get_user(u.id)

        if action == "model":
            cur = user["model"] or DEFAULT_MODEL
            info = MODELS.get(cur, {})
            await q.edit_message_text(
                t(lang, "models_title", cur=f"{info.get('emoji','🤖')} {info.get('name', cur)}"),
                parse_mode=ParseMode.HTML, reply_markup=model_keyboard(cur, lang))
        elif action == "settings":
            cur = user.get("system_prompt") or "—"
            state = t(lang, "on") if user.get("reaction_on",1) else t(lang, "off")
            await q.edit_message_text(
                f"{t(lang, 'settings_title')}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{t(lang, 'system_prompt_label')}:\n<code>{esc(cur)}</code>\n\n"
                f"{t(lang, 'reaction_label')}: {state}\n\n"
                f"<i>/system</i>\n<i>/reaction on|off</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=private_main_menu(owner, lang))
        elif action == "stats":
            total = db("SELECT COUNT(*) c FROM messages WHERE user_id=?", (u.id,), "one")["c"]
            info = MODELS.get(user["model"], {})
            lang_info = LANGS.get(lang, LANGS["ar"])
            await q.edit_message_text(
                f"{t(lang, 'stats_title')}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🤖 {info.get('emoji','🤖')} {info.get('name', user['model'])}\n"
                f"{t(lang, 'lang_label')}: {lang_info['flag']} {lang_info['name']}\n"
                f"{t(lang, 'msgs_label')}: <b>{user['msg_count']}</b>\n"
                f"📨 {total}\n"
                f"{t(lang, 'tokens_label')}: <b>{user['tokens_used']}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=private_main_menu(owner, lang))
        elif action == "clear":
            clear_history(u.id)
            await q.edit_message_text(t(lang, "new_chat_done"),
                                      reply_markup=private_main_menu(owner, lang))
        elif action == "debate":
            await q.edit_message_text(
                f"🎯 <b>AI vs AI</b>\n\n/debate",
                parse_mode=ParseMode.HTML,
                reply_markup=private_main_menu(owner, lang))
        elif action == "export":
            await q.edit_message_text(
                f"📤 <code>/export</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=private_main_menu(owner, lang))
        elif action == "lang":
            await q.edit_message_text(
                t(lang, "choose_lang"),
                parse_mode=ParseMode.HTML,
                reply_markup=language_keyboard("setlang"))
        elif action == "help":
            await q.edit_message_text(t(lang, "help_text"),
                                      parse_mode=ParseMode.HTML,
                                      reply_markup=private_main_menu(owner, lang))
        return

    if data.startswith("g:"):
        action = data.split(":", 1)[1]
        if action == "lang":
            await q.edit_message_text(
                "🌐 <b>Group Language</b>\n\n" + t(lang, "choose_lang"),
                parse_mode=ParseMode.HTML,
                reply_markup=language_keyboard("glang"))
        elif action == "settings":
            await q.edit_message_text("⚙️ /settings", reply_markup=group_admin_menu(lang))

# ═══════════════════════════════════════════════════════════════════════════
#                        POST INIT / ERROR
# ═══════════════════════════════════════════════════════════════════════════
async def post_init(app: Application):
    cmds = [
        BotCommand("start",    "🚀 Start / بدء"),
        BotCommand("lang",     "🌐 Change language"),
        BotCommand("model",    "🤖 Choose model"),
        BotCommand("clear",    "🧹 New chat"),
        BotCommand("system",   "📝 System prompt"),
        BotCommand("stats",    "📊 My stats"),
        BotCommand("export",   "📤 Export"),
        BotCommand("reaction", "🔔 Auto reaction"),
        BotCommand("debate",   "🎯 AI vs AI"),
        BotCommand("stop",     "🛑 Stop debate"),
        BotCommand("topic",    "📌 Debate topic"),
        BotCommand("myid",     "🆔 My ID"),
    ]
    try: await app.bot.set_my_commands(cmds)
    except Exception as e: log.warning(f"cmds: {e}")

async def on_error(update, context):
    log.exception("error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"⚠️ <code>{esc(str(context.error)[:200])}</code>",
                parse_mode=ParseMode.HTML)
        except Exception: pass

# ═══════════════════════════════════════════════════════════════════════════
#                        MAIN
# ═══════════════════════════════════════════════════════════════════════════
def build_app() -> Application:
    if BOT_TOKEN.startswith("PUT_"):
        print("❌ Edit BOT_TOKEN first.")
        sys.exit(1)

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("help",     cmd_help))
    app.add_handler(CommandHandler("lang",     cmd_lang))
    app.add_handler(CommandHandler("model",    cmd_model))
    app.add_handler(CommandHandler("clear",    cmd_clear))
    app.add_handler(CommandHandler("system",   cmd_system))
    app.add_handler(CommandHandler("stats",    cmd_stats))
    app.add_handler(CommandHandler("export",   cmd_export))
    app.add_handler(CommandHandler("reaction", cmd_reaction))
    app.add_handler(CommandHandler("myid",     cmd_myid))
    app.add_handler(CommandHandler("admin",    cmd_admin))
    app.add_handler(CommandHandler("debate",   cmd_debate))
    app.add_handler(CommandHandler("stop",     cmd_stop))
    app.add_handler(CommandHandler("topic",    cmd_topic))

    app.add_handler(CommandHandler("mute",      cmd_mute))
    app.add_handler(CommandHandler("unmute",    cmd_unmute))
    app.add_handler(CommandHandler("kick",      cmd_kick))
    app.add_handler(CommandHandler("ban",       cmd_ban))
    app.add_handler(CommandHandler("unban",     cmd_unban))
    app.add_handler(CommandHandler("warn",      cmd_warn))
    app.add_handler(CommandHandler("unlockall", cmd_unlockall))
    app.add_handler(CommandHandler("welcome",   cmd_welcome))
    app.add_handler(CommandHandler("antilink",  cmd_antilink))
    app.add_handler(CommandHandler("settings",  cmd_settings))
    app.add_handler(CommandHandler("gadmin",    cmd_gadmin))
    app.add_handler(CommandHandler("grouplang", cmd_group_lang))

    app.add_handler(CallbackQueryHandler(on_callback))

    app.add_handler(MessageHandler(tg_filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_members))
    app.add_handler(ChatMemberHandler(on_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))

    app.add_handler(MessageHandler(tg_filters.ChatType.GROUPS & tg_filters.PHOTO, on_group_photo))
    app.add_handler(MessageHandler(tg_filters.ChatType.GROUPS & tg_filters.Document.ALL, on_group_document))

    app.add_handler(MessageHandler(
        tg_filters.ChatType.GROUPS & tg_filters.TEXT & ~tg_filters.COMMAND,
        on_group_text), group=1)

    app.add_handler(MessageHandler(tg_filters.ChatType.PRIVATE & tg_filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(tg_filters.ChatType.PRIVATE & tg_filters.Sticker.ALL, on_sticker))
    app.add_handler(MessageHandler(tg_filters.ChatType.PRIVATE & tg_filters.Document.ALL, on_document))
    app.add_handler(MessageHandler(tg_filters.ChatType.PRIVATE & (tg_filters.VOICE | tg_filters.AUDIO), on_voice))

    app.add_handler(MessageHandler(
        tg_filters.ChatType.PRIVATE & tg_filters.TEXT & ~tg_filters.COMMAND,
        on_text))

    app.add_error_handler(on_error)
    return app

def main():
    print("═" * 60)
    print(f"  ⚡  {BRAND}  ·  v{VERSION}")
    print(f"     {TEAM}  |  {SIGNATURE}")
    print(f"     Languages: {', '.join(LANGS.keys())}")
    print("═" * 60)
    app = build_app()
    print("✅ Bot running. Ctrl+C to stop.")
    print("═" * 60)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\n⛔ Stopped.")