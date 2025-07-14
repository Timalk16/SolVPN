#!/usr/bin/env python3
"""
Simple test script to verify Flask app works
"""
import os
import time
from flask import Flask, jsonify
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from main import build_payment_method_keyboard, cancel_subscription_flow

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "Test Flask App",
        "message": "Flask app is working!",
        "timestamp": time.time()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/ping')
def ping():
    return jsonify({"pong": True, "timestamp": time.time()})

class DummyQuery:
    def __init__(self):
        self.data = "cancel_subscription_flow"
        self.answered = False
        self.message = self
        self.texts = []
    async def answer(self):
        self.answered = True
    async def edit_message_text(self, text, **kwargs):
        self.texts.append(text)
    async def reply_text(self, text, **kwargs):
        self.texts.append(text)

class DummyContext:
    def __init__(self):
        self.user_data = {'selected_duration': '1m', 'payment_id': 'pid', 'payment_type': 'card'}

async def test_cancel_subscription_flow():
    query = DummyQuery()
    update = type('DummyUpdate', (), {'callback_query': query, 'message': None, 'effective_message': query})()
    context = DummyContext()
    await cancel_subscription_flow(update, context)
    assert any("отменен" in t.lower() for t in query.texts), f"Cancel message not sent: {query.texts}"
    print("Test passed: Cancel message sent.")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting test Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
    asyncio.run(test_cancel_subscription_flow()) 