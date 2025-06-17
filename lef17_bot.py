import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = '8025778957:AAERWvcrdy09Dxow-dHuSA2P0IzzGPxLyMQ'
URL = 'https://www.noticiasagricolas.com.br/cotacoes/'
ARQUIVO_CSV = 'cotacoes.csv'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['dados'] = atualizar()
    await exibir_menu(update, context)

async def exibir_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    produtos = sorted(set(d[0] for d in context.user_data['dados']))
    botoes = [[InlineKeyboardButton(p, callback_data=p)] for p in produtos]
    markup = InlineKeyboardMarkup(botoes)
    if update.message:
        await update.message.reply_text('👋 Escolha o produto:', reply_markup=markup)
    else:
        await update.callback_query.edit_message_text('👋 Escolha o produto:', reply_markup=markup)

async def responder_botao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    produto = query.data
    if produto == 'voltar_menu':
        await exibir_menu(update, context)
        return

    dados = [d for d in context.user_data['dados'] if d[0] == produto and d[2]]
    if not dados:
        await query.edit_message_text('⚠️ Nenhuma cotação disponível.')
        return

    msg = f"<b>{produto.upper()}</b> - {datetime.now():%d/%m/%Y}\n"
    for _, local, preco in dados[:5]:
        msg += f"📍 <b>{local}</b>\n💰 {preco}\n────\n"
    botoes = [[InlineKeyboardButton('🔙 Voltar', callback_data='voltar_menu')]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(botoes), parse_mode='HTML')

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('ℹ️ Use /start para começar.')

def atualizar():
    dados = extrair()
    salvar_csv(dados)
    return dados

def extrair():
    r = requests.get(URL)
    s = BeautifulSoup(r.text, 'html.parser')
    resultados = []
    produto = ''
    for el in s.find_all(['h2', 'table']):
        if el.name == 'h2':
            produto = el.text.strip()
        elif el.name == 'table':
            for linha in el.select('tr')[1:]:
                cols = linha.select('td')
                if len(cols) >= 2:
                    local = cols[0].text.strip()
                    preco = cols[1].text.strip()
                    if preco:
                        resultados.append([produto, local, preco])
    return resultados

def salvar_csv(dados):
    with open(ARQUIVO_CSV, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows([['Produto', 'Local', 'Preço']] + dados)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(responder_botao))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))
    print("🤖 Bot rodando...")
    app.run_polling()





