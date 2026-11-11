# Things to fix/ make better
# Add item index page to see all items, should be pretty simple

from flask import Flask, render_template, request, redirect
from flask_mysqldb import MySQL

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

        chest_slots = fetch_slots(1, player_id)
        cur.execute("SELECT ChestName FROM Chest WHERE PlayerId = %s LIMIT 1", (player_id, ))
        if cur.rowcount == 0:
            chest_name = "No chests selected or available"
        else:
            chest_name = cur.fetchone()[0]

        mysql.connection.commit()
        cur.close()

        return render_template('frontend.html',
                                   player=player[0],
                                   chest_slots=chest_slots,
                                   chests=fetch_chests(player_id),
                                   chest_name=chest_name,
                                   item=(),
                                   recipes=fetch_recipes())
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



@app.route('/search-item/<int:player_id>/<string:chest_name>', methods=['POST','GET'])
def search_item(player_id, chest_name):
    if request.method == 'POST':
        item_name = request.form['search-item-name']
        in_chest = request.form.get('search-in-chest')

        cur = mysql.connection.cursor()
        cur.execute("SELECT ItemName FROM Item")
        all_items = cur.fetchall()
        all_items_str = ()
        for item in all_items:
            all_items_str += (item[0],)

        if item_name in all_items_str:
            item = fetch_item(item_name)

            if in_chest != 'on':
                chests_with_item = None
            else:
                # change to item_id
                cur.execute("SELECT ItemId FROM Item WHERE ItemName = %s", (item_name,))
                item_id = cur.fetchone()[0]

                cur.execute("SELECT c.ChestName, s.SlotNumber FROM InventorySlot s, Chest c WHERE s.ItemId = %s AND s.ChestId = c.ChestId AND c.PlayerId = %s", (item_id, player_id))
                chests_with_item = cur.fetchall()

        else:
            item = "none"
            chests_with_item = None

        cur.execute("SELECT * FROM player WHERE PlayerId = %s", (player_id,))
        player = cur.fetchall()

        if chest_name != "No chests selected or available":
            cur.execute("SELECT ChestID FROM Chest WHERE ChestName = %s", (chest_name,))
            chest_id = cur.fetchone()[0]
        else:
            chest_id = 1

        mysql.connection.commit()
        cur.close()
        return render_template('frontend.html',
                               chest_slots=fetch_slots(chest_id, player_id),
                               player=player[0],
                               chests=fetch_chests(player_id),
                               chest_name=chest_name,
                               item=item,
                               item_chest=chests_with_item,
                               recipes=fetch_recipes())
    else:
        return redirect('/')



@app.route('/add-item/<int:player_id>/<int:item_id>/<int:item_max>', methods=['POST', 'GET'])
def add_item(player_id, item_id, item_max):
    if request.method == 'POST':
        amount = request.form['item-add-amount']
        chest_id = request.form['item-add-chest']

        insert_item(item_id, amount, chest_id)

        cur = mysql.connection.cursor()

        cur.execute("SELECT * FROM player WHERE PlayerId = %s", (player_id,))
        player = cur.fetchall()

        cur.execute("SELECT ChestName FROM Chest WHERE ChestID = %s", (chest_id,))
        chest_name = cur.fetchone()[0]

        mysql.connection.commit()
        cur.close()
        return render_template('frontend.html',
                               chest_slots=fetch_slots(chest_id, player_id),
                               player=player[0],
                               chests=fetch_chests(player_id),
                               chest_name=chest_name,
                               item=(),
                               recipes=fetch_recipes())

    else:
        return redirect('/')




# Select chest functionality
@app.route('/chest-select/<int:player_id>', methods=['POST', 'GET'])
def update_item(player_id):

    if request.method == "POST":
        try:
            cur = mysql.connection.cursor()

            chest_id = request.form['display-chest']

            chest_slots = fetch_slots(chest_id, player_id)

            cur.execute("SELECT * FROM player WHERE PlayerId = %s", (player_id,))
            player = cur.fetchall()

            cur.execute("SELECT ChestName FROM Chest WHERE ChestID = %s", (chest_id,))
            chest_name = cur.fetchone()[0]

            mysql.connection.commit()
            cur.close()
            return render_template('frontend.html',
                                   chest_slots = chest_slots,
                                   player=player[0],
                                   chests=fetch_chests(player_id),
                                   chest_name=chest_name,
                                   item=(),
                                   recipes=fetch_recipes())
        except:
            return "Error fetching chest"
    else:
        pass



# Transfer items functionality
@app.route('/transfer/<string:origin_chest>/<int:origin_slot>/<int:player_id>', methods=['POST', 'GET'])
def transfer_chest(origin_chest, origin_slot, player_id):
    if request.method == "POST":
        dest_chest = request.form['transfer_chest']
        item_name = request.form['transfer-item-name']
        quantity = request.form['amount_sel']
        if quantity == '':
            quantity = 1

        cur = mysql.connection.cursor()

        cur.execute("SELECT ItemId FROM Item WHERE ItemName = %s", (item_name,))
        item_id = cur.fetchone()[0]

        cur.execute("SELECT ChestId FROM Chest WHERE ChestName = %s", (dest_chest,))
        dest_chest_id = cur.fetchone()[0]

        cur.execute("SELECT ChestId FROM Chest WHERE ChestName = %s", (origin_chest,))
        origin_chest_id = cur.fetchone()[0]

        cur.execute("SELECT Quantity FROM InventorySlot WHERE ChestId = %s AND SlotNumber = %s", (origin_chest_id, origin_slot))
        if (cur.fetchone()[0] == int(quantity)):
            cur.execute("DELETE FROM InventorySlot WHERE ChestId = %s AND SlotNumber = %s",
                        (origin_chest_id, origin_slot))
        else:
            cur.execute('''
                UPDATE inventoryslot
                SET Quantity = Quantity - %s
                WHERE ChestID = %s
                    AND SlotNumber = %s
                    AND ItemID = %s
                    AND Quantity > %s;
            ''', (quantity, origin_chest_id, origin_slot, item_id, quantity))

        mysql.connection.commit()

        insert_item(item_id, quantity, dest_chest_id)

        cur.execute("SELECT * FROM player WHERE PlayerId = %s", (player_id,))
        player = cur.fetchall()

        mysql.connection.commit()
        cur.close()

        return render_template('frontend.html',
                               chest_slots=fetch_slots(origin_chest_id, player_id),
                               player=player[0],
                               chests=fetch_chests(player_id),
                               chest_name=origin_chest,
                               item=(),
                               recipes=fetch_recipes())
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
                               chest_slots=fetch_slots(chest_id, player_id),
                               player=player[0],
                               chests=fetch_chests(player_id),
                               chest_name=chest_name,
                               item=(),
                               recipes=fetch_recipes())

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
                               chest_slots=fetch_slots(chest_id, player_id),
                               player=player[0],
                               chests=fetch_chests(player_id),
                               chest_name=chest_name,
                               item=(),
                               recipes=fetch_recipes())

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
                               chest_slots=fetch_slots(chest_id, owner_id),
                               player=player[0],
                               chests=fetch_chests(owner_id),
                               chest_name=chest_name,
                               item=(),
                               recipes=fetch_recipes())
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
        if cur.rowcount == 0:
            chest_name = "No chests selected/ available"
        else:
            chest_name = cur.fetchone()[0]

        mysql.connection.commit()
        cur.close()

        return render_template('frontend.html',
                               chest_slots=fetch_slots(1, player_id),
                               player=player[0],
                               chests=fetch_chests(player_id),
                               chest_name=chest_name,
                               item=(),
                               recipes=fetch_recipes())

    else:
        return redirect("/")



@app.route('/craft-select/<int:player_id>/<string:chest_name>', methods=['POST', 'GET'])
def craft_select(player_id, chest_name):
    if request.method == 'POST':
        recipe_id = request.form['select-recipe']

        cur = mysql.connection.cursor()
        cur.execute('''SELECT Item.ItemName, RecipeIngredient.Position 
                    FROM RecipeIngredient, Item
                    WHERE RecipeIngredient.RecipeId = %s AND Item.ItemId = RecipeIngredient.ItemId''', (recipe_id,))
        item_positions = cur.fetchall()

        cur.execute("SELECT GridSize FROM CraftingRecipe WHERE RecipeId = %s", (recipe_id,))
        grid_size = cur.fetchone()[0]

        crafting_grid = ["" for x in range(pow(grid_size,2)) ]
        for position in item_positions:
            crafting_grid[position[1]-1] = position[0]

        if chest_name != "No chests selected or available":
            cur.execute("SELECT ChestID FROM Chest WHERE ChestName = %s", (chest_name,))
            chest_id = cur.fetchone()[0]
        else:
            chest_id = 1

        cur.execute("SELECT * FROM player WHERE PlayerId = %s", (player_id,))
        player = cur.fetchall()

        mysql.connection.commit()
        cur.close()

        return render_template('frontend.html',
                               chest_slots=fetch_slots(chest_id, player_id),
                               player=player[0],
                               chests=fetch_chests(player_id),
                               chest_name=chest_name,
                               item=(),
                               recipes=fetch_recipes(),
                               selected_recipe=recipe_id,
                               crafting_grid=crafting_grid,
                               grid_size=grid_size)

    else:
        return redirect("/")



@app.route('/craft-item/<int:player_id>/<string:chest_name>/<int:recipe_id>', methods=['POST', 'GET'])
def craft_item(player_id, chest_name, recipe_id):
    if request.method == 'POST':

        cur=mysql.connection.cursor()

        cur.execute('''SELECT i.ItemID, SUM(ri.RequiredQuantity) AS Required,
                    COALESCE((
                        SELECT SUM(s.Quantity)
                        FROM InventorySlot s
                        JOIN Chest c ON s.ChestID = c.ChestID
                        WHERE c.PlayerId = %s AND s.ItemID = ri.ItemID
                    ), 0) AS Available
                    FROM RecipeIngredient ri
                    JOIN Item i ON ri.ItemID = i.ItemID
                    WHERE ri.RecipeID = %s
                    GROUP BY ri.ItemID, i.ItemName;
        ''', (player_id, recipe_id))
        ingredient_list = cur.fetchall()

        can_craft = True
        for ingredient in ingredient_list:
            if ingredient[2] < ingredient[1]:
                can_craft = False
            else:
                pass

        if can_craft:

            igdt_locations = ()
            for ingredient in ingredient_list:
                cur.execute('''SELECT c.ChestId, s.SlotNumber FROM InventorySlot s, Chest c
                            WHERE c.ChestId = s.ChestId AND s.ItemId = %s AND c.PlayerId = %s''', (ingredient[0], player_id))
                igdt_locations += (cur.fetchall(), )

            i = 0
            for ingredient in ingredient_list:
                req_quantity = ingredient_list[i][1]
                quantity = 0

                j = 0
                while (req_quantity > quantity):
                    cur.execute("SELECT Quantity FROM InventorySlot WHERE ChestId = %s AND SlotNumber = %s", (igdt_locations[i][j][0], igdt_locations[i][j][1]))

                    if (cur.fetchone()[0] == 1 and quantity < req_quantity):
                        cur.execute("DELETE FROM InventorySlot WHERE ChestId = %s AND SlotNumber = %s", (igdt_locations[i][j][0], igdt_locations[i][j][1]))
                        j = j + 1
                    else:
                        cur.execute('''UPDATE InventorySlot SET Quantity = Quantity - 1
                                    WHERE ChestId = %s AND SlotNumber = %s''', (igdt_locations[i][j][0], igdt_locations[i][j][1]))

                    mysql.connection.commit()

                    quantity = quantity + 1

                i = i + 1



            cur.execute("SELECT ResultItemID FROM CraftingRecipe WHERE RecipeId = %s", (recipe_id,))
            result_id = cur.fetchone()[0]

            cur.execute("SELECT ChestID FROM Chest WHERE ChestName = %s", (chest_name,))
            chest_id = cur.fetchone()[0]

            cur.execute("SELECT ResultQuantity FROM CraftingRecipe WHERE RecipeId = %s", (recipe_id,))
            result_amount = cur.fetchone()[0]
            insert_item(result_id, result_amount, chest_id)

            cur.execute("SELECT * FROM player WHERE PlayerId = %s", (player_id,))
            player = cur.fetchall()

            mysql.connection.commit()
            cur.close()

            return render_template('frontend.html',
                                   chest_slots=fetch_slots(chest_id, player_id),
                                   player=player[0],
                                   chests=fetch_chests(player_id),
                                   chest_name=chest_name,
                                   item=(),
                                   recipes=fetch_recipes(),
                                   selected_recipe=recipe_id)

        else:

            if chest_name != "No chests selected or available":
                cur.execute("SELECT ChestID FROM Chest WHERE ChestName = %s", (chest_name,))
                chest_id = cur.fetchone()[0]
            else:
                chest_id = 1

            cur.execute("SELECT * FROM player WHERE PlayerId = %s", (player_id,))
            player = cur.fetchall()

            mysql.connection.commit()
            cur.close()

            return render_template('frontend.html',
                                   chest_slots=fetch_slots(chest_id, player_id),
                                   player=player[0],
                                   chests=fetch_chests(player_id),
                                   chest_name=chest_name,
                                   item=(),
                                   recipes=fetch_recipes(),
                                   selected_recipe=recipe_id,
                                   craft_message="Item not crafted.")

    else:
        return redirect("/")



@app.route('/item-index/<int:player_name>', methods=['GET', 'POST'])
def item_index():
    if request.method == 'GET':
        pass
    else:
        pass



def fetch_item(item_name):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Item WHERE ItemName = %s", (item_name,))
    return cur.fetchone()



def fetch_chests(player_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT ChestName, ChestId FROM Chest WHERE PlayerId = %s", (player_id,))

    if cur.rowcount == 0:
        chests = ()
    else:
        chests = cur.fetchall()

    cur.close()
    return chests



def fetch_slots(chest_id, player_id):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT Chest.ChestName, inventoryslot.SlotNumber, Item.ItemName, inventoryslot.Quantity
                            FROM inventoryslot
                            JOIN Chest
                                ON inventoryslot.ChestID = Chest.ChestID
                            JOIN Item
                                ON inventoryslot.ItemID = Item.ItemID
                            WHERE Chest.ChestID = %s AND Chest.PlayerId = %s
                            ORDER BY inventoryslot.SlotNumber''', (chest_id, player_id))
    chest_slots = cur.fetchall()

    if chest_slots is None:
        chest_slots = ()

    cur.close()
    return chest_slots



def fetch_recipes():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT Item.ItemName, CraftingRecipe.RecipeId 
                    FROM CraftingRecipe, Item 
                    WHERE CraftingRecipe.ResultItemId = Item.ItemId''')
    recipes = cur.fetchall()
    cur.close()
    return recipes



def insert_item(item_id, amount, chest_id):
    cur = mysql.connection.cursor()

    cur.execute("SELECT MaxStackSize FROM Item WHERE ItemId = %s", (item_id,))
    item_max = cur.fetchone()[0]

    cur.execute('''SELECT Quantity, SlotNumber 
                        FROM InventorySlot 
                        WHERE ChestId = %s AND ItemId = %s AND Quantity < %s
                        ORDER BY SlotNumber ASC''', (chest_id, item_id, item_max))
    existing_item = cur.fetchone()

    if existing_item is None:
        cur.execute("SELECT SlotNumber FROM InventorySlot WHERE ChestId = %s ORDER BY SlotNumber ASC", (chest_id,))

        all_slots = cur.fetchall()
        print(all_slots)

        i = 1
        for slot in all_slots:
            print(slot)
            print(i)
            if slot[0] == i:
                i = i + 1
            else:
                break

        cur.execute("SELECT Capacity FROM Chest WHERE ChestId = %s", (chest_id, ))
        capacity = cur.fetchone()[0]

        if i <= capacity:
            cur.execute('''INSERT INTO inventoryslot (ChestID, SlotNumber, ItemID, Quantity)
                                                VALUES (%s, %s, %s, %s)''', (chest_id, i, item_id, amount))
            mysql.connection.commit()

    else:
        old_amount = existing_item[0]
        if (old_amount + int(amount)) > item_max:
            amount = (old_amount + int(amount)) % item_max
            cur.execute('''UPDATE InventorySlot 
                                SET Quantity = %s 
                                WHERE ChestId = %s AND SlotNumber = %s''', (item_max, chest_id, existing_item[1]))
            mysql.connection.commit()

            cur.execute("SELECT SlotNumber FROM InventorySlot WHERE ChestId = %s ORDER BY SlotNumber ASC", (chest_id,))

            all_slots = cur.fetchall()

            i = 1
            for slot in all_slots:
                print(slot)
                print(i)
                if slot[0] == i:
                    i = i + 1
                else:
                    break

            cur.execute('''INSERT INTO inventoryslot (ChestID, SlotNumber, ItemID, Quantity)
                                VALUES (%s, %s, %s, %s)''', (chest_id, i, item_id, amount))
            mysql.connection.commit()

        else:
            amount = (old_amount + int(amount))

            cur.execute('''UPDATE InventorySlot 
                                                SET Quantity = %s 
                                                WHERE ChestId = %s AND ItemId = %s''', (amount, chest_id, item_id))
            mysql.connection.commit()



if __name__ == '__main__':
    app.run(debug=True)