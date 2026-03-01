from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook: Dict[str, CookbookEntry] = {}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
	s = re.sub(r'[-_]', ' ', recipeName)
	s = re.sub(r'[^A-Za-z\s]', '', s)
	s = re.sub(r'\s+', ' ', s).strip()

	if not s:
		return None
	words = s.split(' ')
	upper_cased_words = [w[0].upper() + w[1:].lower() if w else '' for w in words]
	result = ' '.join(upper_cased_words)

	return result


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	data = request.get_json() or {}

	entry_type = data.get('type')
	name = data.get('name')

	if entry_type not in ('recipe', 'ingredient'):
		return 'Invalid entry type', 400

	if not name:
		return 'Invalid entry name', 400

	if name in cookbook:
		return 'Entry name must be unique', 400

	if entry_type == 'ingredient':
		cook_time = data.get('cookTime')

		if cook_time < 0:
			return 'Invalid cookTime', 400

		ingredient = Ingredient(name=name, cook_time=cook_time)
		cookbook[name] = ingredient
		return '', 200

	required_items_data = data.get('requiredItems', [])
	seen_names = set()
	required_items: List[RequiredItem] = []

	for item in required_items_data:
		item_name = item.get('name')
		quantity = item.get('quantity')

		if item_name in seen_names:
			return 'Duplicate requiredItems name', 400
		seen_names.add(item_name)

		required_items.append(RequiredItem(name=item_name, quantity=quantity))

	recipe = Recipe(name=name, required_items=required_items)
	cookbook[name] = recipe

	return '', 200


# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	name = request.args.get('name')

	entry = cookbook.get(name)
	if entry is None or not isinstance(entry, Recipe):
		return 'Invalid recipe name', 400

	ingredient_totals: Dict[str, int] = {}

	def dfs(entry_name: str, multiplier: int) -> bool:
		item = cookbook.get(entry_name)
		if item is None:
			return False

		if isinstance(item, Ingredient):
			ingredient_totals[entry_name] = ingredient_totals.get(entry_name, 0) + multiplier
			return True

		if isinstance(item, Recipe):
			for req in item.required_items:
				if not dfs(req.name, multiplier * req.quantity):
					return False
			return True

		return False

	if not dfs(name, 1):
		return 'Invalid recipe contents', 400

	total_cook_time = 0
	for ing_name, qty in ingredient_totals.items():
		ing_entry = cookbook.get(ing_name)
		total_cook_time += qty * ing_entry.cook_time

	ingredients_list = [
		{"name": ing_name, "quantity": qty}
		for ing_name, qty in ingredient_totals.items()
	]

	return jsonify({
		"name": entry.name,
		"cookTime": total_cook_time,
		"ingredients": ingredients_list
	}), 200


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
