import random
from geopy import distance

import mysql.connector

connection = mysql.connector.connect(
    host='localhost',
    port=3306,
    database='spy_fly',
    user='root',
    password='yuckyt0r1!',
    autocommit=True
)


# fetch airports from different continents
def get_airports(cont):
    sql = " select iso_country, ident, name, type, latitude_deg, longitude_deg "
    sql += " from airport where continent ='" + cont + "'"
    sql += " and not type = 'closed' group by iso_country order by rand() limit 50; "
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql)
    result = cursor.fetchall()
    return result


# fetch goals
def get_goals():
    sql = "select * from goal;"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql)
    result = cursor.fetchall()
    return result


# new game
def new_game(player_name, current_airport, all_airports):
    sql = "insert into game(screen_name, location, battery_power, score) values (%s, %s , 6000, 0);"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql, (player_name, current_airport))
    game_id = cursor.lastrowid

    # Adding goals
    goals = get_goals()
    goal_list = []
    for goal in goals:
        for i in range(0, goal['probability'], 1):
            goal_list.append(goal['id'])

    # Excluding starting airport
    game_airport = all_airports[1:].copy()
    random.shuffle(game_airport)

    for i, goal_id in enumerate(goal_list):
        if i < len(game_airport):
            sql = "insert into spying_location (game, goal, airport) values (%s, %s, %s);"
            cursor = connection.cursor(dictionary=True)
            cursor.execute(sql, (game_id, goal_id, game_airport[i]['ident']))

    return game_id


# Get airport information
def get_airport_info(icao):
    sql = " select country.name, ident, airport.name, latitude_deg, longitude_deg from airport, country "
    sql += " where airport.iso_country = country.iso_country and ident = '" + icao + "'"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql)
    result = cursor.fetchall()
    return result


# Set airport as visited
def airport_visited(game, airport):
    sql = f"update spying_location set visited = 1 where game = %s and airport = %s;"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql, (game, airport))


# What goal is in the location
def location_goal(game_id, location):
    sql = (f"select spying_location.id, goal, goal.id as goal, name, points from spying_location "
           f"inner join goal on goal.id = spying_location.goal where game = %s and airport = %s; ")
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql, (game_id, location))
    result = cursor.fetchone()
    return result


# Distance between airports
def airport_distance(starting, end):
    start = get_airport_info(starting)
    ending = get_airport_info(end)
    start_coordinates = (start['latitude_deg'], start['longitude_deg'])
    end_coordinates = (ending['latitude_deg'], ending['longitude_deg'])

    return int(distance.distance(start_coordinates, end_coordinates).km)


# get airports in range:
def airports_in_range(icao, airports, remaining_battery):
    in_range = []
    for airport in airports:
        distance = airport_distance(icao, airport['ident'])
        if (distance <= remaining_battery and not distance == 0):
            in_range.append(airport)
    return in_range


# update location
def location_update(icao, bat_power, score):
    sql = f"update game set location = %s, battery_power = %s, score = %s where id = %s;"
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql, (icao, bat_power, score))


# Formulate messages in the main
def is_path_game_won(path_choice):
    rand_path = random.randint(1, 5)
    if path_choice == rand_path:
        return False
    else:
        return True


# get data from game table
def game_data(game_id):
    sql = ("SELECT * FROM GAME"
           f" WHERE ID = {game_id}")
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql)
    result = cursor.fetchall()
    return result



# GAME SETTINGS
print("When you are ready to start, ")
player = input("type your name: ")
# boolean for game over and win
game_over = False
win = False


# all airports & level selection
print("Select your continent ")
while True:
    continent = input("AS/AF/EU : ").upper()
    if continent == "AS" or continent == "AF" or continent == "EU":
        break
    else:
        print("Please enter AS/AF/EU")
all_airports = get_airports(continent)

# start_airport ident
start_airport = all_airports[0]['ident']

# current airport
current_airport = start_airport

# game id
game_id = new_game(player, current_airport, all_airports)

# GAME LOOP
while not game_over:
    # get current airport info
    airport = get_airport_info(current_airport)
    # get game info
    status = game_data(game_id)
    # fetch game status
    print(f"You are at {airport[0]['name']}.")
    print(f"You have {status[0]['battery_power']}km of range in your battery.")
    # pause
    input("Press enter to continue.")
    # check goal in the location
    goal = location_goal(game_id, current_airport)
    if {goal[0]['name']} == "Sunny":

