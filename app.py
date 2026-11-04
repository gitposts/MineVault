from flask import Flask, render_template, request, redirect
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'steve'  # steve
app.config['MYSQL_PASSWORD'] = 'minecraft123' # minecraft123
app.config['MYSQL_DB'] = 'minecraft_inventory'

mysql = MySQL(app)


# Insert and select functionality skeleton
@app.route('/', methods=['POST', 'GET'])
def index():

    if request.method =='POST':
        item_content = request.form['content_item']

        try:
            cur = mysql.connection.cursor()
            # Do a sum query on inventoryslot and add item to the next place
            cur.execute('SELECT ItemID FROM Item WHERE ItemName = %s', [item_content])
            item_id = cur.fetchone()
            print(item_id)
            cur.execute('''
                INSERT INTO inventoryslot (ChestID, SlotNumber, ItemID, Quantity) 
                VALUES (1, 4, %s, 1)''',
            item_id)
            mysql.connection.commit()
            cur.close()
            return redirect('/')
        except:
            return 'Item does not exist'

    else:

        try:
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM Item')
            items = cur.fetchall()
            mysql.connection.commit()
            cur.close()
            return render_template('index.html', items=items)
        except:
            return "Couldn't retrieve items"


# Delete functionality skeleton
@app.route('/delete/<int:ChestId>/<int:SlotNumber>')
def delete_item(chest_id, slot_number):
    cur = mysql.connection.cursor()

    try:
        cur.execute("DELETE FROM InventorySlot WHERE ChestId = %s AND SlotNumber = %s", [chest_id, slot_number])
        mysql.connection.commit()
        cur.close()
        return redirect('/')
    except:
        return "Couldn't delete item"


# Update functionality skeleton
@app.route('/update', methods=['POST', 'GET'])
def update_item():
    if request.method == 'POST':
        chest_id = request.form['chest_num_u']
        slot_number = request.form['slot_num_u']
        item_name = request.form['item_name_u']

        try:
            cur = mysql.connection.cursor()
            cur.execute('SELECT ItemID FROM Item WHERE ItemName = %s', [item_name])
            item_id = cur.fetchone()
            cur.execute("UPDATE InventorySlot SET ItemId = %s WHERE ChestId = %s AND SlotNumber = %s", [item_id, chest_id, slot_number])
            cur.connection.commit()
            cur.close()
            return redirect('/')
        except:
            return "Couldn't update item"

    else:
        return render_template('index.html')


@app.route('/display_chest/<int:chest_id>')
def display_chest(chest_id):
    cur = mysql.connection.cursor()

    try:
        cur.execute(''' Chest.ChestName, inventoryslot.SlotNumber, Item.ItemName, inventoryslot.Quantity
            FROM inventoryslot
            JOIN Chest
		        ON inventoryslot.ChestID = Chest.ChestID
	        JOIN Item
		        ON inventoryslot.ItemID = Item.ItemID
	        WHERE Chest.ChestID = %s
	        ORDER BY inventoryslot.SlotNumber;
        ''', [chest_id])
        slots = cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template('chest.html', slots=slots)

    except:
        return "No such chest available"


if __name__ == '__main__':
    app.run(debug=True)
