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
@app.route('/')
@app.route('/player-select', methods=['POST', 'GET'])
def player_select():

    if request.method == 'POST':
        cur = mysql.connection.cursor()

        player_id = request.form['players']
        cur.execute("SELECT * FROM player WHERE PlayerId = %s", (player_id, ))
        player = cur.fetchall()

        chest_slots = fetch_slots(chest_id=1)
        cur.execute("SELECT ChestName FROM Chest WHERE ChestId = 1")
        chest_name = cur.fetchone()[0]
        mysql.connection.commit()
        cur.close()

        if len(chest_slots) == 0:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM chest")
            chest = cur.fetchall()
            if len(chest) <= 0:
                return render_template('chest-create.html', player=player[0])
            else:
                return redirect('/')  # Eventually add an add item feature to solve when the player has no items in the starting chest
        else:
            return render_template('frontend.html',
                                   player=player[0],
                                   chest_slots=chest_slots,
                                   chests=fetch_chests(),
                                   chest_name=chest_name)
    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM player")
        players = cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template('player-select.html', players=players)



@app.route('/create-player', methods=['POST', 'GET'])
def create_player():

    if request.method == 'POST':
        username = request.form['username']
        avatar_name = request.form['avatar_name']
        exp = request.form['exp']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Player (Username, AvatarName, EXP) VALUES (%s, %s, %s)", (username, avatar_name, exp))
        mysql.connection.commit()
        cur.close()

        return redirect('/')
    else:
        return render_template('player-create.html')



@app.route('/update-player/<int:player_id>', methods=['POST', 'GET'])
def update_player(player_id):

    if request.method == 'POST':
        username = request.form['username']
        avatar_name = request.form['avatar_name']
        exp = request.form['exp']

        cur = mysql.connection.cursor()
        cur.execute('''UPDATE player 
                        SET Username = %s, AvatarName = %s, EXP = %s 
                        WHERE PlayerID = %s
        ''', (username, avatar_name, exp, player_id))
        mysql.connection.commit()
        cur.close()

        return redirect('/')
    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM player WHERE PlayerID = %s", (player_id,))
        player = cur.fetchone()
        cur.close()

        return render_template('player-update.html', player=player)



# Select chest functionality
@app.route('/chest-select/<int:player_id>', methods=['POST', 'GET'])
def update_item(player_id):

    if request.method == "POST":
        try:
            cur = mysql.connection.cursor()

            chest_id = request.form['display-chest']

            chest_slots = fetch_slots(chest_id)

            cur.execute("SELECT * FROM player WHERE PlayerId = %s", (player_id,))
            player = cur.fetchall()

            cur.execute("SELECT ChestName FROM Chest WHERE ChestID = %s", (chest_id,))
            chest_name = cur.fetchone()[0]

            mysql.connection.commit()
            cur.close()
            return render_template('frontend.html',
                                   chest_slots = chest_slots,
                                   player=player[0],
                                   chests=fetch_chests(),
                                   chest_name=chest_name)
        except:
            return "Error fetching chest"
    else:
        pass



# Transfer items functionality
# This ALMOST works but need a more reliable way to transfer into empty slots or slots with the same item
@app.route('/transfer/<string:origin_chest>/<int:origin_slot>/<int:player_id>', methods=['POST', 'GET'])
def transfer_chest(origin_chest, origin_slot, player_id):
    if request.method == "POST":
        dest_chest = request.form['transfer_chest']
        item_name = request.form['transfer-item-name']
        quantity = request.form['amount_sel']

        cur = mysql.connection.cursor()
        cur.execute("SELECT MAX(SlotNumber) FROM InventorySlot, Chest WHERE InventorySlot.ChestID = Chest.ChestID AND Chest.ChestName = %s", (dest_chest,))
        dest_slot = cur.fetchone()[0] + 1

        cur.execute("SELECT ItemId FROM Item WHERE ItemName = %s", (item_name,))
        item_id = cur.fetchone()[0]

        cur.execute("SELECT ChestId FROM Chest WHERE ChestName = %s", (dest_chest,))
        dest_chest_id = cur.fetchone()[0]

        cur.execute("SELECT ChestId FROM Chest WHERE ChestName = %s", (origin_chest,))
        origin_chest_id = cur.fetchone()[0]

        cur.execute('''
            UPDATE inventoryslot
            SET Quantity = Quantity - %s
            WHERE ChestID = %s
	            AND SlotNumber = %s
                AND ItemID = %s
                AND Quantity >= %s;
            INSERT INTO inventoryslot
	            (ChestID, SlotNumber, ItemID, Quantity)
            SELECT %s, %s, %s, %s
            WHERE ROW_COUNT() = 1;
        ''', (quantity, origin_chest_id, origin_slot, item_id, quantity, dest_chest_id, dest_slot, item_id, quantity))

        cur.execute("SELECT * FROM player WHERE PlayerId = %s", (player_id,))
        player = cur.fetchall()

        cur.connection.commit()
        cur.close()

        return render_template('frontend.html',
                               chest_slots=fetch_slots(origin_chest_id),
                               player=player[0],
                               chests=fetch_chests(),
                               chest_name=origin_chest)
    else:
        return redirect("/")



@app.route('/adjust-amount/<string:chest_name>/<int:player_id>', methods=['POST', 'GET'])
def adjust_amount(chest_name, player_id):
    if request.method == 'POST':
        item_slot = request.form['amount-item-slot']
        new_quantity = request.form['new-amount']

        cur = mysql.connection.cursor()
        cur.execute("SELECT ChestID FROM Chest WHERE ChestName = %s", (chest_name,))
        chest_id = cur.fetchone()[0]
        cur.execute("UPDATE InventorySlot SET Quantity = %s WHERE ChestID = %s AND SlotNumber = %s", (new_quantity, chest_id, item_slot))
        mysql.connection.commit()

        cur.execute("SELECT * FROM player WHERE PlayerId = %s", (player_id,))
        player = cur.fetchall()

        mysql.connection.commit()
        cur.close()

        return render_template('frontend.html',
                               chest_slots=fetch_slots(chest_id),
                               player=player[0],
                               chests=fetch_chests(),
                               chest_name=chest_name)

    else:
        return redirect("/")



@app.route('/delete-item/<string:chest_name>/<int:player_id>', methods=['POST', 'GET'])
def delete_item(chest_name, player_id):
    if request.method == 'POST':
        item_slot = request.form['delete-item-slot']

        cur = mysql.connection.cursor()

        cur.execute("SELECT ChestID FROM Chest WHERE ChestName = %s", (chest_name,))
        chest_id = cur.fetchone()[0]

        cur.execute("DELETE FROM InventorySlot WHERE ChestId = %s AND SlotNumber = %s", (chest_id, item_slot))
        mysql.connection.commit()

        cur.execute("SELECT * FROM player WHERE PlayerId = %s", (player_id,))
        player = cur.fetchall()

        mysql.connection.commit()
        cur.close()

        return render_template('frontend.html',
                               chest_slots=fetch_slots(chest_id),
                               player=player[0],
                               chests=fetch_chests(),
                               chest_name=chest_name)

    else:
        return redirect("/")



@app.route('/create-chest/<int:owner_id>', methods=['POST', 'GET'])
def create_chest(owner_id):

    if request.method == 'POST':
        chest_name = request.form['chest-name']
        chest_size = request.form['chest-size']
        items_str = request.form['items-list']
        amounts_str = request.form['amounts-list']

        items_str = "".join(items_str.split())
        items = items_str.split(",")

        amounts_str = "".join(amounts_str.split())
        amounts = amounts_str.split(",")

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO chest (PlayerId, ChestName, Capacity) VALUES (%s, %s, %s)", (owner_id, chest_name, chest_size))
        cur.connection.commit()

        cur.execute("SELECT ChestId FROM chest WHERE ChestName = %s", (chest_name,))
        chest_id = cur.fetchone()[0]

        cur.execute("SELECT ItemName FROM Item")
        all_items = cur.fetchall()
        all_items_str = ()
        for item in all_items:
            all_items_str += (item[0], )

        slot_num = 1
        for item in items:
            if item in all_items_str:
                cur.execute("SELECT ItemID FROM Item WHERE ItemName = %s", (item,))
                item_id = cur.fetchone()[0]
                cur.execute('''INSERT INTO InventorySlot (ChestID, SlotNumber, ItemID, Quantity) 
                            VALUES (%s, %s, %s, %s)''', (chest_id, slot_num, item_id, amounts[items.index(item)]))
                mysql.connection.commit()
                slot_num = slot_num + 1

        cur.execute("SELECT * FROM player WHERE PlayerId = %s", (owner_id,))
        player = cur.fetchall()

        mysql.connection.commit()
        cur.close()

        return render_template('frontend.html',
                               chest_slots=fetch_slots(chest_id),
                               player=player[0],
                               chests=fetch_chests(),
                               chest_name=chest_name)
    else:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM player WHERE PlayerID = %s", (owner_id,))
        player = cur.fetchone()
        cur.close()

        return render_template('chest-create.html', player=player)



# Delete functionality skeleton
@app.route('/delete-chest/<string:chest_name>/<int:player_id>', methods=['POST', 'GET'])
def delete_chest(chest_name, player_id):
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("SELECT ChestId FROM chest WHERE ChestName = %s", (chest_name,))
        chest_id = cur.fetchone()[0]

        cur.execute("DELETE FROM InventorySlot WHERE ChestID = %s", (chest_id,))
        mysql.connection.commit()
        cur.execute("DELETE FROM Chest WHERE ChestID = %s", (chest_id,))
        mysql.connection.commit()

        cur.execute("SELECT * FROM player WHERE PlayerId = %s", (player_id,))
        player = cur.fetchall()

        cur.execute("SELECT ChestName FROM Chest WHERE ChestID = 1")
        chest_name = cur.fetchone()[0]

        mysql.connection.commit()
        cur.close()

        return render_template('frontend.html',
                               chest_slots=fetch_slots(1),
                               player=player[0],
                               chests=fetch_chests(),
                               chest_name=chest_name)

    else:
        return redirect("/")



def fetch_chests():
    cur = mysql.connection.cursor()
    cur.execute("SELECT ChestName, ChestId FROM Chest")
    chests = cur.fetchall()
    cur.close()
    return chests



def fetch_slots(chest_id):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT Chest.ChestName, inventoryslot.SlotNumber, Item.ItemName, inventoryslot.Quantity
                            FROM inventoryslot
                            JOIN Chest
                                ON inventoryslot.ChestID = Chest.ChestID
                            JOIN Item
                                ON inventoryslot.ItemID = Item.ItemID
                            WHERE Chest.ChestID = %s
                            ORDER BY inventoryslot.SlotNumber''', (chest_id,))

    chest_slots = cur.fetchall()
    cur.close()
    return chest_slots



if __name__ == '__main__':
    app.run(debug=True)