import pandas as pd
import inflect
import ast


def is_plural(word):
    word = word.replace("_", " ").split()[-1]
    plural_word = pluralize(word)
    return word == plural_word


def use_a_or_an(word):
    word = word.replace("_", " ").split()[0]
    p = inflect.engine()
    return p.a(word).split()[0]  # Returns "a" or "an"


def pluralize(word):
    p = inflect.engine()
    parts = word.split("_")  # Split on underscores

    # Check if the last word is already plural
    if not p.singular_noun(parts[-1]):
        parts[-1] = p.plural(parts[-1])  # Pluralize only if it's singular

    return " ".join(parts)  # Recombine with underscores


def rename_ingredient(ingredient, count):
    if count > 1:
        return pluralize(ingredient)
    return ingredient


def get_ingredients_and_recipe(string, multiplier, df):
    # Filter the DataFrame to the row where `result_id` matches the input string
    matching_row = df[df['result_id'] == string]

    # Check if any matching rows exist
    if matching_row.empty:
        return []

    # Get the first (and only) matched row as a Series
    row = matching_row.iloc[0]

    # Create base msg
    msg = "To craft "

    if multiplier > 1:
        msg += f"{multiplier} "
    else:
        multiplier = 1

    # Find columns with non-null values and return as a list of tuples
    info = [(col, row[col]) for col in row.index if pd.notnull(row[col]) and col != "recipe"]
    target_item = info[0][1]

    # Check if item is already plural
    if is_plural(target_item):
        msg += f"{target_item}, you need "
    # If item not plural but multiplier > 1, make plural
    elif multiplier > 1:
        msg += f"{pluralize(target_item)}, you need "
    # This is a singular item, use either a or an
    else:
        print()
        msg += f"{use_a_or_an(target_item)} {target_item}, you need "

    if len(info) > 2:
        for item in info[1:-1]:
            count = multiplier * int(item[1])
            msg += f"{count} {rename_ingredient(item[0], count)}, "
        final_item_count = multiplier * int(info[-1][1])
        msg += f"and {final_item_count} {rename_ingredient(info[-1][0], final_item_count)}."
    else:
        count = multiplier * int(info[1][1])
        msg += f"{count} {rename_ingredient(info[1][0], count)}."

    recipe = ast.literal_eval(row["recipe"])

    return msg.replace("_", " "), recipe

# df = pd.read_csv('recipes_output.csv', delimiter='|')
# #
# # ingredients = get_ingredients("piston", df)
# #
# # print(str(ingredients))
#
# print(df.head())
#
# for item in df["result_id"]:
#     print(str(get_ingredients(item, 5, df)))
