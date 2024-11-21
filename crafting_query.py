import pandas as pd
from nltk.stem import WordNetLemmatizer
import inflect


def is_plural(word):
    word = word.replace("_", " ").split()[-1]
    print(word)
    plural_word = pluralize(word)
    return word != plural_word


def use_a_or_an(word):
    word = word.replace("_", " ").split()[0]
    p = inflect.engine()
    return p.a(word).split()[0]  # Returns "a" or "an"


def pluralize(word):
    parts = word.split("_")  # Split on underscores
    p = inflect.engine()
    parts[-1] = p.plural(parts[-1])  # Pluralize the last word
    return " ".join(parts)  # Recombine


def get_ingredients(string, multiplier, df):
    # Filter the DataFrame to the row where `result_id` matches the input string
    matching_row = df[df['result_id'] == string]

    print(matching_row)

    # Check if any matching rows exist
    if matching_row.empty:
        return []

    # Get the first (and only) matched row as a Series
    row = matching_row.iloc[0]

    # Create base msg
    msg = "To craft "

    if multiplier > 1:
        msg += f"{multiplier} "

    # Find columns with non-null values and return as a list of tuples
    info = [(col, row[col]) for col in row.index if pd.notnull(row[col])]
    target_item = info[0][1]

    # Check if item is already plural
    if is_plural(target_item):
        msg += f"{target_item}, you need "
    # If item not plural but multiplier > 1, make plural
    elif multiplier > 1:
        msg += f"{pluralize(target_item)}, you need "
    # This is a singular item, use either a or an
    else:
        msg += f"{use_a_or_an(target_item)} {target_item}, you need "

    if len(info) > 2:
        for item in info[1:-1]:
            msg += f"{multiplier * int(item[1])} {item[0]}, "
        msg += f"and {multiplier * int(info[-1][1])} {info[-1][0]}."
    else:
        msg += f"{multiplier * int(info[1][1])} {info[1][0]}."

    return msg.replace("_", " ")

# df = pd.read_csv('recipes_output.csv')
#
# ingredients = get_ingredients("piston", df)
#
# print(str(ingredients))

print(is_plural("white_wool"))
