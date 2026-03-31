    # ── Crypto top N ──
    elif state == "await_crypto_top":
        user_state.pop(uid)
        bot.send_chat_action(cid, "typing")
        try:
            # Validate and parse user input
            if not text or not text.strip():
                n = 10
            else:
                n = int(text) if text.isdigit() else 10
            
            # Fetch coins
            coins = crypto.top(min(n, 20))
            
            # Validate response
            if not coins or not isinstance(coins, list):
                raise ValueError("Invalid API response format")
            
            # Send results
            for coin in coins:
                bot.send_message(cid, fmt_coin(coin), parse_mode="Markdown")
            bot.send_message(cid, "✅ Done.", reply_markup=back_kb())
        except Exception as e:
            bot.send_message(cid, f"❌ {e}", reply_markup=back_kb())
