
############################################################################################
#  JSON object model for full user profile
#  address, city, state, zip, games, accomplishment fields are optional
#  add an 'id' field when making requests that require it
############################################################################################
# {
#     "name": "Chris DiGiuseppe",
#     "handle": "AwakeFM",
#     "email": "Awake1077@gmail.com",
#     "address": "8 Corliss Ave",
#     "city": "Rensselaer",
#     "state": "NY",
#     "zip": "12144",
#     "games": [
#         {
#             "game": {
#                 "name": "The Last Ninja",
#                 "ninjas_killed": 32,
#                 "time_in_game": 3323
#             }
#         },
#         {
#             "game": {
#                 "enemy_ships_destroyed": 322,
#                 "name": "Star Control 2",
#                 "time_in_game": 333
#             }
#         }
#     ],
#     "accomplishments": [
#         {
#             "accomplishment": {
#                 "name": "ninja_slayer",
#                 "slug": "Ninja Slayer",
#                 "tagline": "Total number of ninjas killed",
#                 "tracked_profile_stat": "ninjas_killed",
#                 "threshold": 30,
#                 "point_value": 10
#             }
#         },
#         {
#             "accomplishment": {
#                 "name": "star_killer",
#                 "slug": "Star Killer",
#                 "tagline": "Total number of enemy starships destroyed",
#                 "tracked_profile_stat": "enemy_ships_destroyed",
#                 "threshold": 300,
#                 "point_value": 20
#             }
#         }
#     ]
# }

#===================================================================
#profile service
#===================================================================

from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from flask_pymongo import ObjectId

app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'playerprofiles'
app.config['MONGO_URI'] = 'mongodb://admin:admin@ds153845.mlab.com:53845/playerprofiles'

mongo = PyMongo(app)

#=====================================================================================
#  Get a list of all user profiles
#=====================================================================================
@app.route('/userprofiles/', methods =['GET'])
def get_all_profiles():
    profiles = mongo.db.profiles

    output = []

    for q in profiles.find():
        output.append(get_find_result(q))

    return jsonify({'all_user_profiles' : output})

#===========================================================================================================================================
#  Create a new user profile
#  JSON Syntax: {Commented out JSON object model above, required fields are: name, handle, email - others are populated with default values
#  Returns: The complete JSON document retrieved from the database after save
#===========================================================================================================================================
@app.route('/userprofiles/create', methods = ['POST'])
def create_new_user_profile():

    profiles = mongo.db.profiles

    try:
        profile = get_request_info(request)

        profile_id = profiles.insert({'name': profile.name,
                                      'handle': profile.handle,
                                      'email': profile.email,
                                      'address': profile.address,
                                      'city': profile.city,
                                      'state': profile.state,
                                      'zip': profile.zip,
                                      "games": profile.games,
                                      "accomplishments": profile.accomplishments
                                      })

        # get new profile to verify DB write
        new_profile = profiles.find_one({'_id': profile_id})

        # return new profile as JSON
        resp = {'user profile': get_output(new_profile)}

    except(KeyError):
        resp = get_general_request_error()

    return jsonify(resp)

#=============================================================================================================================================================================
#  Update an existing user profile
#  JSON Syntax: id field (uses MongoDB '_id', use the default URL GET request to get all user profiles/id's for testing.  Any field you want updated. Accepts multiple fields.
#  ie : {"id":"57b45c3acf53b82d64e70d47", "name" : "Frank Davis" , address : "34 Its Alive Lane"}
#  Returns: The complete JSON document retrieved from the database after save
#=============================================================================================================================================================================
@app.route('/userprofiles/update', methods = ['POST'])
def update_user_profile():

    profiles = mongo.db.profiles

    try:
        # search for user by name
        id = request.json['id']

        userProfile = profiles.find_one({'_id': ObjectId(id)})

        if(userProfile == None):
            resp = get_id_error_string(id)
        else:
            update_profile(userProfile,request)
            profile_id = profiles.save(userProfile)
            # get new profile
            new_profile = profiles.find_one({'_id': profile_id})

            resp = {'success' : get_output(new_profile)}

    except (KeyError):
            resp = get_general_request_error()

    return jsonify(resp)

#=============================================================================================================================================================================
#  Delete an existing user profile
#  JSON Syntax: {"id":"57b45c3acf53b82d64e70d47"}
#  Returns: A success message if the delete was successful
#=============================================================================================================================================================================
@app.route('/userprofiles/delete', methods = ['POST'])
def delete_user_profile():
    profiles = mongo.db.profiles

    try:
        # search for user by name
        id = request.json['id']

        deleteResult = profiles.delete_one({'_id': ObjectId(id)})

        if(deleteResult == None):
            resp = get_id_error_string(id)
        else:
            resp = {'success': "profile id %s has been deleted"%(id)}
    except:
        resp = get_general_request_error()

    return jsonify(resp)

#=============================================================================================================================================================================
#  Retrieve an existing user profile
#  JSON Syntax: {"id":"57b45c3acf53b82d64e70d47"}
#  Returns: The complete JSON document for the user profile retrieved from the database
#=============================================================================================================================================================================
@app.route('/userprofiles/retrieve', methods = ['POST'])
def retrieve_user_profile():
    profiles = mongo.db.profiles

    try:
        # search for user by name
        id = request.json['id']

        userProfile = profiles.find_one({'_id': ObjectId(id)})

        if(userProfile == None):
            resp = {'error' : "user id %s not found"%(id)}
        else:
            resp = {'success': get_output(userProfile)}
    except (KeyError):
        resp = get_general_request_error()

    return jsonify(resp)


#==========================================================================================
#  Add individual Game item
#  JSON Syntax: {"id" : "57b45c3acf53b82d64e70d47", "game_name" : "Seven Cities of Gold" }
#  Notes: 'time_in_game' stat added and set to zero by default
#  Returns: The complete JSON document retrieved from the database after save
#==========================================================================================
@app.route('/userprofiles/addgame', methods = ['POST'])
def add_new_game_for_user():

    profiles = mongo.db.profiles
    gameListName = UserProfile.get_games_list_name()

    try:
        id = request.json['id']
        game_name = request.json['game_name']

        # search for user by name
        userProfile = profiles.find_one({'_id': ObjectId(id)})

        # return error if user not found
        if userProfile is None:
            retStr = get_id_error_string(id)
            resp = {'error': retStr}
        elif does_item_exist(game_name, gameListName, "game", userProfile):
            retStr = "item %s already exists"%(game_name)
            resp = {'error': retStr}
        else:
            #create new game entry, default time_in_game stat to 0
            userProfile['games'].append({'game' : {'name' : game_name, 'time_in_game' : 0}})

            profile_id = profiles.save(userProfile)

            # get new profile
            new_profile = profiles.find_one({'_id': profile_id})
            resp = {'success' : get_output(new_profile)}
    except (KeyError):
        resp = get_general_request_error()

    return jsonify(resp)

#=========================================================================================
#  Delete individual Game item
#  JSON Syntax: {"id" : "57b45c3acf53b82d64e70d47", "game_name" : "Seven Cities of Gold" }
#  Returns: The complete JSON document retrieved from the database after save
#==========================================================================================
@app.route('/userprofiles/deletegame', methods = ['POST'])
def delete_game_for_user():
    profiles = mongo.db.profiles
    gameListName = UserProfile.get_games_list_name()

    try:
        id = request.json['id']
        game_name = request.json['game_name']

        # search for user by name
        userProfile = profiles.find_one({'_id': ObjectId(id)})

        # return error if user not found
        if userProfile is None:
            retStr = get_id_error_string(id)
            resp = {'error': retStr}
        elif not does_item_exist(game_name, gameListName, "game", userProfile):
            retStr = "game %s does not exist for user %s"%(game_name, id)
            resp = {'error': retStr}
        else:
            index = get_item_index(game_name,gameListName,"game", userProfile)

            del userProfile['games'][index]

            # update the old profile (replace doc)
            profile_id = profiles.save(userProfile)

            # verify saved profile
            new_profile = profiles.find_one({'_id': profile_id})
            resp = {'success': get_output(new_profile)}

    except(KeyError):
        resp = get_general_request_error()

    return jsonify(resp)


#========================================================================================================================================
#  Update game stat - add new stat if input stat_name is not found
#  JSON Syntax: {"id":"57b45c3acf53b82d64e70d47", "game_name" : "The Last Ninja" , "stat_name" : "time_in_game" , "stat_value" : "230"}
#  Returns: The complete JSON document retrieved from the database after save
#  TODO: accept a list of stats and values
#=========================================================================================================================================
@app.route('/userprofiles/updatestat', methods = ['POST'])
def update_game_stat_for_user():

    profiles = mongo.db.profiles

    try:
        id = request.json['id']
        name = request.json['game_name']
        stat_name = request.json['stat_name']
        stat_value = request.json['stat_value']

        #search for user by name
        userProfile = profiles.find_one({'_id' : ObjectId(id)})

        #return error if user not found
        if userProfile is None:
            retStr = get_id_error_string(id)
            resp = {'error' : retStr}
        else:
            #edit stat OR create a new one if stat_name isn't found
            for x in userProfile['games']:
                if DictQuery(x).get("game/name") == name:
                    x['game'][stat_name] = stat_value

            #update the old profile (replace doc)
            profile_id = profiles.save(userProfile)

            #verify saved profile
            new_profile = profiles.find_one({'_id': profile_id})
            resp = {'success': get_output(new_profile)}
    except(KeyError):
        resp = get_general_request_error()

    return jsonify(resp)

#==========================================================================================
#  Add individual Accomp;ishment item
#  JSON Syntax: {"id" : "57b45c3acf53b82d64e70d47", "name": "ninja_slayer", "slug": "Ninja Slayer", "tagline": "Total number of ninjas killed", "tracked_stat": "ninjas_killed", "threshold": 30, "point_value": 10 }
#  Notes: all properties required
#  Returns: The complete JSON document retrieved from the database after save
#  TODO: add support for date/time
#==========================================================================================
@app.route('/userprofiles/addaccomplishment', methods = ['POST'])
def add_new_accomp_for_user():

    profiles = mongo.db.profiles
    accompListName = UserProfile.get_accomplishments_list_name()

    try:
        id = request.json['id']
        name = request.json['name']
        slug = request.json['slug']
        tagline = request.json['tagline']
        threshold = request.json['threshold']
        tracked_stat = request.json['tracked_stat']
        point_value = request.json['point_value']

        # search for user by name
        userProfile = profiles.find_one({'_id': ObjectId(id)})

        if userProfile is None:
            retStr = get_id_error_string(id)
            resp = {'error' : retStr}
        elif does_item_exist(name,accompListName,"accomplishment", userProfile):
            retStr = "accomplishment %s already exists" % (name)
            resp = {'error': retStr}
        else:
            #create new accomplishment entry
            userProfile['accomplishments'].append({'accomplishment' : {'name' : name, 'slug' : slug,
                                           'tagline' : tagline, 'tracked_stat' : tracked_stat,
                                           'threshold' : threshold, 'point_value': point_value}})

            profile_id = profiles.save(userProfile)

            # get new profile
            new_profile = profiles.find_one({'_id': profile_id})
            resp = {'success' : get_output(new_profile)}

    except(KeyError):
        resp = get_general_request_error()

    return jsonify(resp)


#=========================================================================================
#  Delete individual Accomplishment item
#  JSON Syntax: {"id" : "57b45c3acf53b82d64e70d47", "name" : "ninja_killer" }
#  Returns: The complete JSON document retrieved from the database after save
#==========================================================================================
@app.route('/userprofiles/deleteaccomplishment', methods = ['POST'])
def delete_accomp_for_user():
    profiles = mongo.db.profiles
    accompListName = UserProfile.get_accomplishments_list_name()

    try:
        id = request.json['id']
        name = request.json['name']

        # search for user by name
        userProfile = profiles.find_one({'_id': ObjectId(id)})

        # return error if user not found
        if userProfile is None:
            retStr = get_id_error_string(id)
            resp = {'error': retStr}
        elif not does_item_exist(name,accompListName,"accomplishment", userProfile):
            retStr = "accomplishment %s does not exist for user %s" % (name, id)
            resp = {'error': retStr}
        else:
            index = get_item_index(name,accompListName,"accomplishment", userProfile)
            del userProfile[accompListName][index]

            # update the old profile (replace doc)
            profile_id = profiles.save(userProfile)

            # verify saved profile
            new_profile = profiles.find_one({'_id': profile_id})
            resp = {'success': get_output(new_profile)}
    except(KeyError):
        resp = get_general_request_error()

    return jsonify(resp)

#helper methods & classes

#plain container object to pass around user profile info
class UserProfile:
    id = ""
    name = ""
    handle = ""
    email = ""
    address = ""
    city = ""
    state = ""
    zip = ""
    games = []
    accomplishments = []

    @staticmethod
    def get_games_list_name():
        return "games"

    @staticmethod
    def get_accomplishments_list_name():
        return "accomplishments"

def update_profile(userProfile, request):
    print (userProfile)
    if 'name' in request.json:
        userProfile['name'] = request.json['name']
    if 'handle' in request.json:
        userProfile['handle'] = request.json['handle']
    if 'email' in request.json:
        userProfile['email'] = request.json['email']
    if 'address' in request.json:
        userProfile['address'] = request.json['address']
    if 'city' in request.json:
        userProfile['city'] = request.json['city']
    if 'state' in request.json:
        userProfile['state'] = request.json['state']
    if 'zip' in request.json:
        userProfile['zip'] = request.json['zip']
    if 'games' in request.json:
        userProfile['games'] = request.json['games']
    if 'accomplishments' in request.json:
        userProfile['accomplishments'] = request.json['accomplishments']

def get_request_info(request):

    #TODO: Ensure 'games' and 'accomplishment' lists have required dictionary with a 'name' key

    profile = UserProfile

    profile.name = request.json['name']
    profile.handle = request.json['handle']
    profile.email = request.json['email']

    # optional input parameters
    if 'address' in request.json:
        profile.address = request.json['address']
    else:
        profile.address = ""

    if 'city' in request.json:
        profile.city = request.json['city']
    else:
        profile.city = ""

    if 'state' in request.json:
        profile.state = request.json['state']
    else:
        profile.state = ""

    if 'zip' in request.json:
        profile.zip = request.json['zip']
    else:
        profile.zip = ""

    if 'games' in request.json:
        profile.games = request.json['games']
    else:
        profile.games = []

    if 'accomplishments' in request.json:
        profile.accomplishments = request.json['accomplishments']
    else:
        profile.accomplishments = []

    return profile

def get_find_result(findResult):

    return {
    'id' : str(findResult['_id']),
    'name' : findResult['name'],
    'handle' : findResult['handle'],
    'email' : findResult['email'],
    'address' : findResult['address'],
    'city' : findResult['city'],
    'state' : findResult['state'],
    'zip' : findResult['zip'],
    'games' : findResult['games'],
    'accomplishments' : findResult['accomplishments']
    }

def does_item_exist(itemName, itemListName, itemType, userProfile):

    itemExists = False

    for x in userProfile[itemListName]:
        if DictQuery(x).get("%s/name"%(itemType)) == itemName:
            itemExists = True
            break;

    return itemExists

def get_item_index(item, itemListName,itemType, userProfile):

    index = 0

    for x in userProfile[itemListName]:
        if DictQuery(x).get("%s/name"%(itemType)) == item:
           break

        index += 1

    return index


def get_id_error_string(id):
    retStr = "user %s not found" % (id)
    return retStr

def get_output(doc):
    output = {'id' : str(doc['_id']),
              'name': doc['name'],
              'handle': doc['handle'],
              'email': doc['email'],
              'address' : doc['address'],
              'city' : doc['city'],
              'state' : doc['state'],
              'zip' : doc['zip'],
              'games': doc['games'],
              'accomplishments': doc['accomplishments']}
    return output

def get_general_request_error():
    return {'error': "Request body invalid.  You may be missing a required field"}

class DictQuery(dict):
    def get(self, path, default = None):
        keys = path.split("/")
        val = None

        for key in keys:
            if val:
                if isinstance(val, list):
                    val = [ v.get(key, default) for v in val]
                else:
                    val = val.get(key, default)
            else:
                val = dict.get(self, key, default)

            if not val:
                break;

        return val

#start the service
if __name__ == '__main__':
   app.run(debug=True)




