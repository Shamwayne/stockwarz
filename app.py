"""
Application login resides in this file
"""
from flask import Flask, redirect, request, render_template, url_for, abort, flash, jsonify
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from database import db_session, User, BoughtShares, SoldShares
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from flask_caching import Cache
import stocks
from datetime import datetime

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
app.config['SECRET_KEY'] = 'somesecretkeythatisencryptedgoesherenaturally'

# Flask login initialised here
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# callback to reload the user object        
@login_manager.user_loader
def load_user(userid):
	return db_session.query(User).get(int(userid))

# redirect to login page if not logged in
@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

# fancy filter to get the current stock price
@app.template_filter('stock_price')
@cache.memoize(timeout=900)
def fetch_stock_price(symbol):
    """Get the stock price using a symbol"""
    price = stocks.get_stock_price(symbol)
    return price

"""
Meaningful routes start here
"""
@app.route('/', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')
		user = db_session.query(User).filter_by(username=username).first()
		if user is not None:
			if check_password_hash(user.password, password):
				login_user(user)
				return redirect(url_for('home'))
			else:
				flash('Wrong password!!!')
		else:
			flash('Invalid username!!')
	return render_template('login.html')


@app.route('/seedr')
def seeder():
	kudzi = User(username='Kudzi', password=generate_password_hash('secretpassword123'), phone='0783449906')
	db_session.add(kudzi)
	db_session.commit()
	return "The default user has been saved!!"


@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))

	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')
		phone = request.form.get('phone')
		user = db_session.query(User).filter(or_(User.username==username, User.phone==phone)).first()
		if user is None:
			user = User(username=username, password=generate_password_hash(password),
				phone=phone)
			db_session.add(user)
			db_session.commit()
			flash("Successfully registered")
			return redirect(url_for('login'))
		else:
			flash("Username or phone already taken! Choose another...")
	return render_template('register.html')


@app.route('/home')
@login_required
def home():
	my_shares = db_session.query(BoughtShares).filter_by(userid=current_user.id).all()
	my_sales = db_session.query(SoldShares).filter_by(userid=current_user.id).all()
	return render_template('index.html', inventory = my_shares, my_sales=my_sales)


@app.route('/add-stock', methods=['GET', 'POST'])
@login_required
def add_stock():
	if request.method == 'POST':
		symbol = request.form.get('symbol')
		no_of_shares = int(request.form.get('no_of_shares'))
		cost_per_share = stocks.get_stock_price(symbol)
		amount_spent = float(cost_per_share) * int(no_of_shares)

		amount_available = float(current_user.balance) - amount_spent

		if amount_spent > current_user.balance:
			flash("Hey hey, dont overspend!!!")
		else:
			user = db_session.query(User).filter_by(id=current_user.id).first()
			user.balance = amount_available

			# check if there weren't any bought shares
			bought_shares = db_session.query(BoughtShares).filter_by(userid=current_user.id).filter_by(symbol=symbol).first()
			# if the shares don't exist, add a new share object
			if bought_shares is None:
				bought_shares = BoughtShares(cost_per_share=cost_per_share, no_of_shares=no_of_shares,
				symbol=symbol, userid=current_user.id)
				db_session.add(bought_shares)
			# check if the existing shares have diffent prices, then add more shares
			else:
				if float(bought_shares.cost_per_share) == float(cost_per_share):
					bought_shares.no_of_shares += no_of_shares
				# if existing shares have diff prices, might as well make a new object reflecting that
				else:
					bought_shares = BoughtShares(cost_per_share=cost_per_share, no_of_shares=no_of_shares,
					symbol=symbol, userid=current_user.id)
					db_session.add(bought_shares)
			db_session.commit()
			flash('Your purchase has been saved...')
	stocks_list = stocks.get_stock_symbols()
	stock_data = stocks.get_current_stock_data()
	return render_template('add_stock.html', stocks_list=stocks_list, stocks=stock_data)

"""
This route was meant to add dividents but I'll wait for now....
"""
# @app.route('/add-divident/<int:stockid>', methods=['GET', 'POST'])
# @login_required
# def add_divident(stockid):
# 	stock = db_session.query(BoughtShares).filter_by(id=stockid).first()
# 	if stock is None:
# 		flash('Stock not found!!')
# 		return redirect(url_for('home'))

# 	if request.method == 'POST':
# 		price_per_share = request.form.get('price_per_share')
# 		pass

# 	stock_data = stocks.get_current_stock_data()
# 	return render_template('add_divident.html', stock=stock, stocks=stock_data)

@app.route('/sell-stock/<int:stockid>', methods=['GET', 'POST'])
@login_required
def sell_stock(stockid):
	stock = db_session.query(BoughtShares).filter_by(id=stockid).first()
	cost_per_share = float(stocks.get_stock_price(stock.symbol))

	if stock is None:
		flash('Stock not found!!')
		return redirect(url_for('home'))
	if request.method == 'POST':
		symbol = stock.symbol
		no_of_shares = int(request.form.get('no_of_shares'))
		amount_gained = float(cost_per_share) * int(no_of_shares)

		if int(no_of_shares) <= int(stock.no_of_shares):
			sold_share = SoldShares(cost_per_share=cost_per_share, no_of_shares=no_of_shares,
				symbol=symbol, userid=current_user.id)
			# if player sells all shares, delete the stock from bought list
			if int(no_of_shares) == int(stock.no_of_shares):
				db_session.delete(stock)
			# else just decrease the number of stocks the person owns
			else:
				stock.no_of_shares -= no_of_shares
			user = db_session.query(User).filter_by(id=current_user.id).first()
			user.balance += amount_gained
			db_session.add(sold_share)
			db_session.commit()
			flash("Sale processed successfully...")
		else:
			flash('Hey hey, you cant sell more than you have!!')
	stock_data = stocks.get_current_stock_data()
	return render_template('sell_stock.html', stock=stock, cps=cost_per_share, stocks=stock_data)

@app.route('/leader-board')
@login_required
@cache.memoize(timeout=900)
def leader_board():
	today = datetime.today().strftime('%B %d, %Y')
	users = db_session.query(User).all()
	users_data = list()

	for user in users:
		user_stocks = db_session.query(BoughtShares).filter_by(userid=user.id).all()
		net_worth = user.balance
		worth = 0.0
		if len(user_stocks) > 0:
			for stock in user_stocks:
				cost_per_share = float(stocks.get_stock_price(stock.symbol))
				worth += float(int(stock.no_of_shares) * cost_per_share)

		net_worth += worth
		users_data.append(dict(username=user.username, balance=user.balance, networth=net_worth))

	return render_template('leader_board.html', today=today, users=users_data)

@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))

if __name__ == '__main__':
	app.run(debug=True, port=5011, host='0.0.0.0', threaded=True)
