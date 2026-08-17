"""
Flask Web Application for ATM System.

Purpose:
    Provides a browser-based UI for the ATM System.
    Uses Flask sessions to maintain ATM state across requests.

Usage:
    python3 app.py
    Then open http://localhost:5000 in your browser.
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash

from atm_system.enums import ATMMenuItem
from atm_system.exceptions.exceptions import ATMError
from atm_system.main import create_sample_data, create_atm
from atm_system.models.bank import Bank

app = Flask(__name__)
app.secret_key = "atm-system-secret-key-2024"

# Initialize ATM (shared state - for demo purposes)
bank = Bank("ATM Bank Pakistan")
create_sample_data(bank)
atm = create_atm(bank)


@app.route("/")
def index():
    """Home page - card insertion screen."""
    session.clear()
    return render_template("index.html")


@app.route("/insert-card", methods=["POST"])
def insert_card():
    """Insert card and validate."""
    card_number = request.form.get("card_number", "").strip()
    try:
        card = atm.insert_card(card_number)
        session["card_number"] = card_number
        session["card_holder"] = card.card_holder
        session["pin_attempts"] = 0
        return redirect(url_for("pin_entry"))
    except ATMError as e:
        flash(e.message, "error")
        return redirect(url_for("index"))


@app.route("/pin", methods=["GET", "POST"])
def pin_entry():
    """PIN entry page."""
    if "card_number" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        pin = request.form.get("pin", "").strip()
        try:
            atm.insert_card(session["card_number"])
            atm.authenticate(pin)
            session["authenticated"] = True
            session["pin_attempts"] = 0
            return redirect(url_for("account_select"))
        except ATMError as e:
            session["pin_attempts"] = session.get("pin_attempts", 0) + 1
            remaining = 3 - session["pin_attempts"]
            if remaining <= 0:
                flash("Card blocked. Too many incorrect attempts.", "error")
                session.clear()
                return redirect(url_for("index"))
            flash(f"{e.message}. {remaining} attempt(s) remaining.", "error")
            return render_template("pin.html", card_holder=session.get("card_holder", ""))

    return render_template("pin.html", card_holder=session.get("card_holder", ""))


@app.route("/select-account", methods=["GET", "POST"])
def account_select():
    """Account selection page."""
    if not session.get("authenticated"):
        return redirect(url_for("index"))

    try:
        atm.insert_card(session["card_number"])
        atm.authenticate("skip")
        accounts = atm.get_linked_accounts()
    except ATMError:
        accounts = []

    if request.method == "POST":
        account_number = request.form.get("account_number")
        if account_number:
            try:
                atm.insert_card(session["card_number"])
                atm.authenticate("skip")
                atm.select_account(account_number)
                session["account_number"] = account_number
                return redirect(url_for("menu"))
            except ATMError as e:
                flash(e.message, "error")

    return render_template("account_select.html", accounts=accounts)


@app.route("/menu")
def menu():
    """Main menu page."""
    if not session.get("authenticated") or "account_number" not in session:
        return redirect(url_for("index"))
    return render_template("menu.html", account=session["account_number"])


@app.route("/balance")
def balance():
    """Check balance."""
    if not session.get("authenticated") or "account_number" not in session:
        return redirect(url_for("index"))
    try:
        atm.insert_card(session["card_number"])
        atm.authenticate("skip")
        atm.select_account(session["account_number"])
        bal = atm.check_balance()
        return render_template("balance.html", balance=bal, account=session["account_number"])
    except ATMError as e:
        flash(e.message, "error")
        return redirect(url_for("menu"))


@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    """Deposit money."""
    if not session.get("authenticated") or "account_number" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
            atm.insert_card(session["card_number"])
            atm.authenticate("skip")
            atm.select_account(session["account_number"])
            txn = atm.deposit(amount)
            flash(f"Deposit successful! Transaction ID: {txn.transaction_id}", "success")
            return redirect(url_for("menu"))
        except (ATMError, ValueError) as e:
            msg = e.message if isinstance(e, ATMError) else "Invalid amount"
            flash(msg, "error")
            return render_template("deposit.html")

    return render_template("deposit.html")


@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    """Withdraw money."""
    if not session.get("authenticated") or "account_number" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
            atm.insert_card(session["card_number"])
            atm.authenticate("skip")
            atm.select_account(session["account_number"])
            txn = atm.withdraw(amount)
            fee = txn.total_deduction - txn.amount
            msg = f"Withdrawal successful! Transaction ID: {txn.transaction_id}"
            if fee > 0:
                msg += f" (Fee: Rs. {fee:,.0f})"
            flash(msg, "success")
            return redirect(url_for("menu"))
        except (ATMError, ValueError) as e:
            msg = e.message if isinstance(e, ATMError) else "Invalid amount"
            flash(msg, "error")
            return render_template("withdraw.html")

    return render_template("withdraw.html")


@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    """Transfer money."""
    if not session.get("authenticated") or "account_number" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        try:
            receiver = request.form.get("receiver", "").strip()
            amount = float(request.form.get("amount", 0))
            atm.insert_card(session["card_number"])
            atm.authenticate("skip")
            atm.select_account(session["account_number"])
            txn = atm.transfer(receiver, amount)
            flash(f"Transfer successful! Transaction ID: {txn.transaction_id}", "success")
            return redirect(url_for("menu"))
        except (ATMError, ValueError) as e:
            msg = e.message if isinstance(e, ATMError) else "Invalid input"
            flash(msg, "error")
            return render_template("transfer.html")

    return render_template("transfer.html")


@app.route("/change-pin", methods=["GET", "POST"])
def change_pin():
    """Change PIN."""
    if not session.get("authenticated") or "account_number" not in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        try:
            old_pin = request.form.get("old_pin", "").strip()
            new_pin = request.form.get("new_pin", "").strip()
            confirm = request.form.get("confirm_pin", "").strip()
            if new_pin != confirm:
                flash("New PINs do not match.", "error")
                return render_template("change_pin.html")
            atm.insert_card(session["card_number"])
            atm.authenticate("skip")
            atm.select_account(session["account_number"])
            atm.change_pin(old_pin, new_pin)
            flash("PIN changed successfully!", "success")
            return redirect(url_for("menu"))
        except ATMError as e:
            flash(e.message, "error")
            return render_template("change_pin.html")

    return render_template("change_pin.html")


@app.route("/statement")
def statement():
    """Mini statement."""
    if not session.get("authenticated") or "account_number" not in session:
        return redirect(url_for("index"))
    try:
        atm.insert_card(session["card_number"])
        atm.authenticate("skip")
        atm.select_account(session["account_number"])
        stmt_text = atm.get_mini_statement()
        return render_template("statement.html", statement=stmt_text, account=session["account_number"])
    except ATMError as e:
        flash(e.message, "error")
        return redirect(url_for("menu"))


@app.route("/exit")
def exit_atm():
    """Exit and eject card."""
    try:
        atm.insert_card(session.get("card_number", ""))
        atm.eject_card()
    except ATMError:
        pass
    session.clear()
    flash("Session ended. Card ejected.", "info")
    return redirect(url_for("index"))


if __name__ == "__main__":
    print("=" * 50)
    print("  ATM System - Web Interface")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 50)
    print("  Demo Credentials:")
    print("  Card: CARD-10001 | PIN: 1234")
    print("  Card: CARD-20001 | PIN: 5678")
    print("=" * 50)
    app.run(debug=True, port=5000)
