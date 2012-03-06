import emen2.db
db = emen2.db.opendb(admin=True)
with db:
	# print db.query([['rectype','contains','ddd']])
	for i in range(3):
		print db.query([['*','contains','ddd']])