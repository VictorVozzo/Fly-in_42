# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    Makefile                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: vivozzo- <vivozzo-@student.42porto.com>    +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 0026/09/18 16:01:03 by ivozzo-           #+#    #+#              #
#    Updated: 2026/10/22 10:36:39 by vivozzo-         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

VENV_DIR = venv
VENV_BIN = $(VENV_DIR)/bin
PYTHON = $(VENV_BIN)/python3
PIP = $(VENV_BIN)/pip

SRC_DIR = source
MAIN = $(SRC_DIR)/main.py

# ARGS ?= maps/easy/01_linear_path.txt
# ARGS ?= maps/easy/02_simple_fork.txt
# ARGS ?= maps/easy/03_basic_capacity.txt
# ARGS ?= maps/medium/01_dead_end_trap.txt
# ARGS ?= maps/medium/02_circular_loop.txt
# ARGS ?= maps/medium/03_priority_puzzle.txt
# ARGS ?= maps/hard/01_maze_nightmare.txt
# ARGS ?= maps/hard/02_capacity_hell.txt
ARGS ?= maps/hard/03_ultimate_challenge.txt
# ARGS ?= maps/challenger/01_the_impossible_dream.txt


all: install

$(VENV_BIN)/activate:
	python3 -m venv $(VENV_DIR)

install: $(VENV_BIN)/activate
	$(PIP) install --upgrade pip >/dev/null 2>&1
	$(PIP) install flake8 mypy >/dev/null 2>&1
	$(PIP) install pygame >/dev/null 2>&1

run:
	@$(PYTHON) $(MAIN) $(ARGS) 

visual:
	@$(PYTHON) $(MAIN) $(ARGS) --visual_output

benchmark: 
	@$(PYTHON) $(MAIN) $(ARGS) --benchmark

lint:
	@$(VENV_BIN)/flake8 $(SRC_DIR)
	@$(VENV_BIN)/mypy $(SRC_DIR) --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	@$(VENV_BIN)/flake8 $(SRC_DIR)
	@$(VENV_BIN)/mypy --strict $(SRC_DIR)

debug:
	@$(PYTHON) -m pdb $(MAIN) $(ARGS)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache
	find . -type f -name "*.pyc" -delete

fclean: clean
	rm -rf $(VENV_DIR)

re: fclean all

.PHONY: all install run visual benchmark lint lint-strict debug clean fclean re