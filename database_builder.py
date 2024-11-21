import os
import json
import pandas as pd


def parse_recipe(data):
    item_mapping = {}
    counts = {}

    if "result" not in data:
        return None

    if "crafting" not in data["type"]:
        return None

    print(data["result"]["id"])

    if data["result"]["id"] == "minecraft:purpur_slab":
        print()

    # Build Item mapping
    if "key" in data:
        # Process the 'key' dictionary
        for key, definition in data["key"].items():
            if "item" in definition:
                item_mapping[key] = definition["item"].replace("minecraft:", "")
            elif "tag" in definition:
                item_mapping[key] = definition["tag"].replace("minecraft:", "")
            # definition is a list, can use multiple blocks
            else:
                item_mapping[key] = definition[0]["item"].replace("minecraft:", "")
    elif "ingredients" in data:
        # Process the 'ingredients' array
        for ingredient_dict in data["ingredients"]:
            if "item" in ingredient_dict:
                item = ingredient_dict["item"].replace("minecraft:", "")
                if item in counts:
                    counts[item] += 1
                else:
                    counts[item] = 1

            elif "tag" in ingredient_dict:
                tag = ingredient_dict["tag"].replace("minecraft:", "")
                if tag in counts:
                    counts[tag] += 1
                else:
                    counts[tag] = 1

            # This is a list not a dict, likely for dyes
            else:
                if "group" in data:
                    counts[f"of_any_{data["group"]}"] = 1  # ex. any_wool, any_bed
                else:
                    counts[ingredient_dict[0].get("item")] = 1

    # Build the DataFrame row
    row = {"result_id": data["result"]["id"].replace("minecraft:", "")}

    if "pattern" in data:
        recipe = data["pattern"]
        recipe = [item for sublist in recipe for item in sublist]

        for key, ingredient in item_mapping.items():
            counts[ingredient] = recipe.count(key)

        # Rebuild the recipe
        recipe = [item_mapping.get(item, item) for item in recipe]  # Replace using mapping
    else:
        recipe = []
        for ingredient in item_mapping.values():
            counts[ingredient] = 1
        for ingredient in counts.keys():
            recipe.append(ingredient)

        # Build recipe based on num of ingredients and counts
        if len(recipe) == 1:
            if counts[recipe[0]] == 9:
                recipe = [recipe[0] for _ in range(9)]

    row["recipe"] = recipe + [' ' for _ in range(9 - len(recipe))]


    # Build counts of each ingredient
    for i, ingredient in enumerate(counts):
        row[ingredient] = counts[ingredient]

    return row


def process_recipes(folder_path, output_file):
    all_rows = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.json'):  # Only process JSON files
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r') as file:
                data = json.load(file)
                row = parse_recipe(data)
                if row:
                    all_rows.append(row)

    # Create a DataFrame from all parsed rows
    df = pd.DataFrame(all_rows)

    # Write the DataFrame to a comma-delimited file
    df.to_csv(output_file, sep='|', index=False)


# Process the recipes in the "recipe" folder and write to "recipes_output.txt"
folder = "recipe"
output_file = "recipes_output.csv"
process_recipes(folder, output_file)
