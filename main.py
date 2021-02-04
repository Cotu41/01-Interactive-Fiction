#!/usr/bin/env python3
import sys,os,json,re
assert sys.version_info >= (3,9), "This script requires at least Python 3.9"

#synonym dictionary, if we are going to require the player to type in commands
lookup = {
    "north":"go north",
    "south":"go south",
    "west":"go west",
    "east":"go east",
    "n":"go north",
    "s":"go south",
    "w":"go west",
    "e":"go east"
}
#distinguish direction commands from other types-you could make as many of these as you want
directions = {'go north','go south','go east','go west','go up','go down'}



def load(l):
    f = open(os.path.join(sys.path[0], l))
    data = f.read()
    j = json.loads(data)
    return j

def find_passage(game_desc, pid):
    for p in game_desc["passages"]:
        if p["pid"] == pid:
            return p
    return {}


# Removes Harlowe formatting from Twison description
def format_passage(description):
    description = re.sub(r'//([^/]*)//',r'\1',description)
    description = re.sub(r"''([^']*)''",r'\1',description)
    description = re.sub(r'~~([^~]*)~~',r'\1',description)
    description = re.sub(r'\*\*([^\*]*)\*\*',r'\1',description)
    description = re.sub(r'\*([^\*]*)\*',r'\1',description)
    description = re.sub(r'\^\^([^\^]*)\^\^',r'\1',description)

    # instead of cleaning up the links in the description text, remove them entirely
    #description = re.sub(r'(\[\[[^\|]*?)\|([^\]]*?\]\])',r'\1->\2',description)
    #description = re.sub(r'\[\[([^(->\])]*?)->[^\]]*?\]\]',r'[ \1 ]',description)
    description = re.sub(r'\[\[(.+?)\]\]\n*','',description)
    return description


# Add items to the inventory list and return it (doesn't actually remove them from the current location)
def update_inventory(current,inventory,choice):
    if "inventory" in current:
        for i in current["inventory"]:
            if choice == "get {}".format(i.lower()):
                inventory.append(i)
    return inventory

# Score can be updated based on location or acquiring items in the inventory
# looks for a "score" field in the location or a "score" dictionary in the game description
def update_score(current,scores,inventory,score,locations,items):
    if "score" in current and current["name"] not in locations:
        score += int(current["score"])
    for i in inventory:
        if i not in items and i in scores:
            score += int(scores[i])
    return score

# Allows for restricting choices based on whether an item is in the inventory
def update(current,choice,game_desc,inventory):
    if choice == "":
        return current
    for l in current["links"]:
        if "requires" not in l or l["requires"] in inventory:
            if l["name"].lower() == choice:
                current = find_passage(game_desc, l["pid"])
                return current
    if choice in directions:
        print("\nI don't know how to go that way. Please try again")
    else:
        print("\nI don't understand. Please try again.")
    return current

# Allows for restricting choices based on whether an item is in the inventory
# Prints score, moves, and HP
def render(current,score,moves,hp,inventory):
    print("\n\n")
    print("Score: {score}       HP: {hp}       Moves: {moves}".format(score=score, hp=hp, moves=moves))
    print("\n")
    print(current["name"])
    print(format_passage(current["text"]))
    if "links" in current:
        for l in current["links"]:
            if "requires" not in l or l["requires"] in inventory:
                print(l["name"])

    if "inventory" in current:
        for i in inventory:
            if i in current["inventory"]:
                current["inventory"].remove(i)
    if "inventory" in current and len(current["inventory"]):
        print("\nYou see ")
        for i in current["inventory"]:
            print(i)
    print("\n")

# Normalizes user input: lowercase, remove whitespace, and look up in synonym dictionary
def get_input():
    choice = input("What would you like to do? (type quit to exit) ")
    choice = choice.lower().strip()
    if choice in lookup:
        choice = lookup[choice]
    return choice


def main():
    game_desc = load("game.json")
    current = find_passage(game_desc, game_desc["startnode"])
    last_location = current
    choice = ""

    score = 0
    moves = 0
    hp = 100
    inventory = []
    previous_inventory = []
    locations = set()
    items = set()

    while choice != "quit" and current != {}:
        # if the player types "get [item]"
        inventory = update_inventory(current, inventory, choice)
        # if an item was not added to the inventory, then do the usual update
        if inventory == previous_inventory:
            current = update(current,choice,game_desc,inventory)
        else:
            previous_inventory = inventory.copy()
        # update the score (based on location or inventory item): locations and items sets prevent point pump
        score = update_score(current,game_desc["scores"],inventory,score,locations,items)

        # keep a running list of locations visited and items in inventory
        locations.add(current["name"])
        for i in inventory:
            items.add(i)

        # increase moves if we visit a new location
        if current != last_location:
            moves += 1
            last_location = current

        render(current,score,moves,hp,inventory)

        # if the current location doesn't have an exit, quit
        if "links" in current:
            choice = get_input()
        else:
            current = {}
    
    print("Thanks for playing!")
    print("Your final score was {score} in {moves} moves.".format(score=score,moves=moves))



if __name__ == "__main__":
  main()