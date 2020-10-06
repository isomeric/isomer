#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Isomer - The distributed application framework
# ==============================================
# Copyright (C) 2011-2020 Heiko 'riot' Weinen <riot@c-base.org> and others.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Miscellaneous standard functions for Isomer
"""

import SecretColors
import bcrypt
import pytz

from datetime import datetime
from random import choice
from typing import AnyStr, Optional
from uuid import uuid4

from isomer.logger import isolog, warn


def std_salt() -> str:
    """Generates a secure cryptographical salt
    """

    return bcrypt.gensalt().decode("utf-8")


def std_hash(word: AnyStr, salt: AnyStr):
    """Generates a cryptographically strong (bcrypt) password hash with a given
    salt added."""

    try:
        password: bytes = word.encode("utf-8")
    except UnicodeDecodeError:
        password = word

    if isinstance(salt, str):
        salt_bytes = salt.encode("utf-8")
    else:
        salt_bytes = salt

    password_hash = bcrypt.hashpw(password, salt_bytes).decode("ascii")

    return password_hash


def std_now(delta=None, date_format="iso", tz="UTC"):
    """Return current timestamp in ISO format"""

    now = datetime.now(tz=pytz.timezone(tz))

    if delta is not None:
        now = now + delta

    if date_format == "iso":
        result = now.isoformat()
    elif date_format == "germandate":
        result = now.strftime("%d.%m.%Y")
    else:
        result = now

    return result


def std_datetime(date, date_format="%d.%m.%Y", tz="UTC"):
    """Return something that looks like a date into a timestamp in ISO format"""

    if isinstance(date, tuple):
        now = datetime(*date)
    elif isinstance(date, str):
        if date_format == 'iso':
            now = datetime.fromisoformat(date)
        else:
            now = datetime.strptime(date, date_format)

    else:
        isolog("Could not convert date:", date, date_format, tz, pretty=True, lvl=warn)
        return date

    now = now.astimezone(pytz.timezone(tz))

    result = now.isoformat()

    return result


def std_uuid():
    """Return string representation of a new UUID4"""

    return str(uuid4())


def std_color(palette_name=None):
    """Generate random default color"""
    if palette_name is None:
        palette_name = "ibm"

    color = SecretColors.Palette(palette_name, show_warning=False).random()
    return color


# def std_human_uid(kind: Literal['animal', 'place', 'color'] = None) -> str:
def std_human_uid(kind: Optional[str] = None) -> str:
    """Return a random generated human-friendly phrase as low-probability unique id

    :param kind: Specify the type of id (animal, place, color or None)
    :return: Human readable ID
    :rtype: str
    """

    kind_list = radio_alphabet

    if kind == "animal":
        kind_list = animals
    elif kind == "place":
        kind_list = places

    name = "{color} {adjective} {kind} of {attribute}".format(
        color=choice(colors),
        adjective=choice(adjectives),
        kind=choice(kind_list),
        attribute=choice(attributes),
    )

    return name


def std_table(rows):
    """Return a formatted table of given rows"""

    result = ""
    if len(rows) > 1:
        headers = rows[0]._fields
        lens = []
        for i in range(len(rows[0])):
            lens.append(
                len(max([x[i] for x in rows] + [headers[i]], key=lambda x: len(str(x))))
            )
        formats = []
        hformats = []
        for i in range(len(rows[0])):
            if isinstance(rows[0][i], int):
                formats.append("%%%dd" % lens[i])
            else:
                formats.append("%%-%ds" % lens[i])
            hformats.append("%%-%ds" % lens[i])
        pattern = " | ".join(formats)
        hpattern = " | ".join(hformats)
        separator = "-+-".join(["-" * n for n in lens])
        result += hpattern % tuple(headers) + " \n"
        result += separator + "\n"

        for line in rows:
            result += pattern % tuple(t for t in line) + "\n"
    elif len(rows) == 1:
        row = rows[0]
        hwidth = len(max(row._fields, key=lambda x: len(x)))
        for i in range(len(row)):
            result += "%*s = %s" % (hwidth, row._fields[i], row[i]) + "\n"

    return result


colors = ["Red", "Orange", "Yellow", "Green", "Cyan", "Blue", "Violet", "Purple"]
adjectives = [
    "abundant",
    "adorable",
    "agreeable",
    "alive",
    "ancient",
    "angry",
    "beautiful",
    "better",
    "bewildered",
    "big",
    "bitter",
    "boiling",
    "brave",
    "breeze",
    "brief",
    "broad",
    "broken",
    "bumpy",
    "calm",
    "careful",
    "chilly",
    "chubby",
    "circular",
    "clean",
    "clever",
    "clumsy",
    "cold",
    "colossal",
    "cooing",
    "cool",
    "creepy",
    "crooked",
    "cuddly",
    "curly",
    "curved",
    "damaged",
    "damp",
    "deafening",
    "deep",
    "defeated",
    "delicious",
    "delightful",
    "dirty",
    "drab",
    "dry",
    "dusty",
    "eager",
    "early",
    "easy",
    "elegant",
    "embarrassed",
    "empty",
    "faint",
    "faithful",
    "famous",
    "fancy",
    "fast",
    "fat",
    "few",
    "fierce",
    "flaky",
    "flat",
    "fluffy",
    "freezing",
    "fresh",
    "full",
    "gentle",
    "gifted",
    "gigantic",
    "glamorous",
    "greasy",
    "great",
    "grumpy",
    "handsome",
    "happy",
    "heavy",
    "helpful",
    "helpless",
    "high",
    "hissing",
    "hollow",
    "hot",
    "huge",
    "icy",
    "immense",
    "important",
    "inexpensive",
    "itchy",
    "jealous",
    "jolly",
    "juicy",
    "kind",
    "large",
    "late",
    "lazy",
    "light",
    "little",
    "lively",
    "long",
    "loose",
    "loud",
    "low",
    "magnificent",
    "mammoth",
    "many",
    "massive",
    "melodic",
    "melted",
    "miniature",
    "modern",
    "mushy",
    "mysterious",
    "narrow",
    "nervous",
    "nice",
    "noisy",
    "numerous",
    "nutritious",
    "obedient",
    "obnoxious",
    "odd",
    "old",
    "old-fashioned",
    "panicky",
    "petite",
    "plain",
    "powerful",
    "prickly",
    "proud",
    "puny",
    "purring",
    "quaint",
    "quick",
    "quiet",
    "rainy",
    "rapid",
    "raspy",
    "relieved",
    "rich",
    "round",
    "salty",
    "scary",
    "scrawny",
    "screeching",
    "shallow",
    "short",
    "shy",
    "silly",
    "skinny",
    "slow",
    "small",
    "sparkling",
    "sparse",
    "square",
    "steep",
    "sticky",
    "straight",
    "strong",
    "substantial",
    "sweet",
    "swift",
    "tall",
    "tart",
    "tasteless",
    "teeny",
    "tiny",
    "tender",
    "thankful",
    "thoughtless",
    "thundering",
    "uneven",
    "uninterested",
    "unsightly",
    "uptight",
    "vast",
    "victorious",
    "voiceless",
    "warm",
    "weak",
    "wet",
    "wet",
    "whispering",
    "wide",
    "wide-eyed",
    "witty",
    "wooden",
    "worried",
    "wrong",
    "young",
    "yummy",
    "zealous",
]
animals = [
    "Aardvark",
    "Abyssinian",
    "Affenpinscher",
    "Akbash",
    "Akita",
    "Albatross",
    "Alligator",
    "Angelfish",
    "Ant",
    "Anteater",
    "Antelope",
    "Armadillo",
    "Avocet",
    "Axolotl",
    "Baboon",
    "Badger",
    "Balinese",
    "Bandicoot",
    "Barb",
    "Barnacle",
    "Barracuda",
    "Bat",
    "Beagle",
    "Bear",
    "Beaver",
    "Beetle",
    "Binturong",
    "Bird",
    "Birman",
    "Bison",
    "Bloodhound",
    "Bobcat",
    "Bombay",
    "Bongo",
    "Bonobo",
    "Booby",
    "Budgerigar",
    "Buffalo",
    "Bulldog",
    "Bullfrog",
    "Burmese",
    "Butterfly",
    "Caiman",
    "Camel",
    "Capybara",
    "Caracal",
    "Cassowary",
    "Cat",
    "Caterpillar",
    "Catfish",
    "Centipede",
    "Chameleon",
    "Chamois",
    "Cheetah",
    "Chicken",
    "Chihuahua",
    "Chimpanzee",
    "Chinchilla",
    "Chinook",
    "Chipmunk",
    "Cichlid",
    "Coati",
    "Cockroach",
    "Collie",
    "Coral",
    "Cougar",
    "Cow",
    "Coyote",
    "Crab",
    "Crane",
    "Crocodile",
    "Cuscus",
    "Cuttlefish",
    "Dachshund",
    "Dalmatian",
    "Deer",
    "Dhole",
    "Dingo",
    "Discus",
    "Dodo",
    "Dog",
    "Dolphin",
    "Donkey",
    "Dormouse",
    "Dragonfly",
    "Drever",
    "Duck",
    "Dugong",
    "Dunker",
    "Eagle",
    "Earwig",
    "Echidna",
    "Elephant",
    "Emu",
    "Falcon",
    "Ferret",
    "Fish",
    "Flamingo",
    "Flounder",
    "Fly",
    "Fossa",
    "Fox",
    "Frigatebird",
    "Frog",
    "Gar",
    "Gecko",
    "Gerbil",
    "Gharial",
    "Gibbon",
    "Giraffe",
    "Goat",
    "Goose",
    "Gopher",
    "Gorilla",
    "Grasshopper",
    "Greyhound",
    "Grouse",
    "Guppy",
    "Hamster",
    "Hare",
    "Harrier",
    "Havanese",
    "Hedgehog",
    "Heron",
    "Himalayan",
    "Hippopotamus",
    "Horse",
    "Human",
    "Hummingbird",
    "Hyena",
    "Ibis",
    "Iguana",
    "Impala",
    "Indri",
    "Insect",
    "Jackal",
    "Jaguar",
    "Javanese",
    "Jellyfish",
    "Kakapo",
    "Kangaroo",
    "Kingfisher",
    "Kiwi",
    "Koala",
    "Kudu",
    "Labradoodle",
    "Ladybird",
    "Lemming",
    "Lemur",
    "Leopard",
    "Liger",
    "Lion",
    "Lionfish",
    "Lizard",
    "Llama",
    "Lobster",
    "Lynx",
    "Macaw",
    "Magpie",
    "Maltese",
    "Manatee",
    "Mandrill",
    "Markhor",
    "Mastiff",
    "Mayfly",
    "Meerkat",
    "Millipede",
    "Mole",
    "Molly",
    "Mongoose",
    "Mongrel",
    "Monkey",
    "Moorhen",
    "Moose",
    "Moth",
    "Mouse",
    "Mule",
    "Newfoundland",
    "Newt",
    "Nightingale",
    "Numbat",
    "Ocelot",
    "Octopus",
    "Okapi",
    "Olm",
    "Opossum",
    "Orang-utan",
    "Ostrich",
    "Otter",
    "Oyster",
    "Pademelon",
    "Panther",
    "Parrot",
    "Peacock",
    "Pekingese",
    "Pelican",
    "Penguin",
    "Persian",
    "Pheasant",
    "Pig",
    "Pika",
    "Pike",
    "Piranha",
    "Platypus",
    "Pointer",
    "Poodle",
    "Porcupine",
    "Possum",
    "Prawn",
    "Puffin",
    "Pug",
    "Puma",
    "Quail",
    "Quetzal",
    "Quokka",
    "Quoll",
    "Rabbit",
    "Raccoon",
    "Ragdoll",
    "Rat",
    "Rattlesnake",
    "Reindeer",
    "Rhinoceros",
    "Robin",
    "Rottweiler",
    "Salamander",
    "Saola",
    "Scorpion",
    "Seahorse",
    "Seal",
    "Serval",
    "Sheep",
    "Shrimp",
    "Siamese",
    "Siberian",
    "Skunk",
    "Sloth",
    "Snail",
    "Snake",
    "Snowshoe",
    "Somali",
    "Sparrow",
    "Sponge",
    "Squid",
    "Squirrel",
    "Starfish",
    "Stingray",
    "Stoat",
    "Swan",
    "Tang",
    "Tapir",
    "Tarsier",
    "Termite",
    "Tetra",
    "Tiffany",
    "Tiger",
    "Tortoise",
    "Toucan",
    "Tropicbird",
    "Tuatara",
    "Turkey",
    "Uakari",
    "Uguisu",
    "Umbrellabird",
    "Vulture",
    "Wallaby",
    "Walrus",
    "Warthog",
    "Wasp",
    "Weasel",
    "Whippet",
    "Wildebeest",
    "Wolf",
    "Wolverine",
    "Wombat",
    "Woodlouse",
    "Woodpecker",
    "Wrasse",
    "Yak",
    "Zebra",
    "Zebu",
    "Zonkey",
    "Zorse",
]
radio_alphabet = [
    "Alpha",
    "Bravo",
    "Charlie",
    "Delta",
    "Echo",
    "Foxtrot",
    "Golf",
    "Hotel",
    "India",
    "Juliet",
    "Kilo",
    "Lima",
    "Mike",
    "November",
    "Oscar",
    "Papa",
    "Quebec",
    "Romeo",
    "Sierra",
    "Tango",
    "Uniform",
    "Victor",
    "Whiskey",
    "X-ray",
    "Yankee",
    "Zulu",
]
places = [
    "airport",
    "aquarium",
    "bakery",
    "bar",
    "bridge",
    "building",
    "bus-stop",
    "cafe",
    "campground",
    "church",
    "city",
    "embassy",
    "florist",
    "gym",
    "harbour",
    "hospital",
    "hotel",
    "house",
    "island",
    "laundry",
    "library",
    "monument",
    "mosque",
    "museum",
    "office",
    "park",
    "pharmacy",
    "plaza",
    "restaurant",
    "road",
    "school",
    "spa",
    "stable",
    "stadium",
    "store",
    "street",
    "theater",
    "tower",
    "town",
    "train-station",
    "university",
    "village",
    "wall",
    "zoo",
]
attributes = [
    "Chaos",
    "Hate",
    "Adventure",
    "Anger",
    "Anxiety",
    "Beauty",
    "Beauty",
    "Being",
    "Beliefs",
    "Birthday",
    "Brilliance",
    "Career",
    "Charity",
    "Childhood",
    "Comfort",
    "Communication",
    "Confusion",
    "Courage",
    "Culture",
    "Curiosity",
    "Death",
    "Deceit",
    "Dedication",
    "Democracy",
    "Despair",
    "Determination",
    "Energy",
    "Failure",
    "Faith",
    "Fear",
    "Freedom",
    "Friendship",
    "Future",
    "Generosity",
    "Grief",
    "Happiness",
    "Holiday",
    "Honesty",
    "Indifference",
    "Interest",
    "Joy",
    "Knowledge",
    "Liberty",
    "Life",
    "Love",
    "Luxury",
    "Marriage",
    "Misery",
    "Motivation",
    "Nervousness",
    "Openness",
    "Opportunity",
    "Pain",
    "Past",
    "Patience",
    "Peace",
    "Perseverance",
    "Pessimism",
    "Pleasure",
    "Sacrifice",
    "Sadness",
    "Satisfaction",
    "Sensitivity",
    "Sorrow",
    "Stress",
    "Sympathy",
    "Thought",
    "Trust",
    "Warmth",
    "Wisdom",
]
