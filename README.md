# Wumpus World AI Agent

This project implements an intelligent agent for the classic Wumpus World problem using propositional logic and resolution-based inference. The system is built as a web application using Flask, allowing real-time visualization of the agent’s reasoning and movement.

## Overview

The Wumpus World is a well-known problem in Artificial Intelligence used to demonstrate knowledge-based agents. The environment consists of a grid containing hazards such as pits and a Wumpus, along with a piece of gold. The agent must explore the environment, avoid dangers, and retrieve the gold.

Unlike simple rule-based agents, this implementation uses logical inference to determine safe and unsafe cells. The agent observes percepts from the environment and updates its knowledge base to make informed decisions.

## Key Features

- Knowledge-based agent using propositional logic
- Resolution algorithm for logical inference
- Conversion of rules into Conjunctive Normal Form (CNF)
- Dynamic knowledge base updates based on percepts
- Intelligent navigation avoiding pits and the Wumpus
- Automatic exploration of safe cells
- Web-based interface with real-time updates

## Environment Representation

- Grid-based world (configurable size)
- Hazards:
  - Pits (cause Breeze in adjacent cells)
  - Wumpus (causes Stench in adjacent cells)
- Goal:
  - Locate and collect the gold safely

## Agent Behavior

The agent performs the following steps:

1. Perceives the environment (Breeze, Stench)
2. Updates the knowledge base with logical rules
3. Converts rules into CNF
4. Applies the resolution algorithm to infer safety
5. Moves only to cells proven safe
6. Repeats until:
   - Gold is found
   - All safe cells are explored
   - No safe moves remain

## Logical Model

- Symbols:
  - P(i,j): Pit in cell (i,j)
  - W(i,j): Wumpus in cell (i,j)
  - B(i,j): Breeze in cell (i,j)
  - S(i,j): Stench in cell (i,j)

- Example rules:
  - B(i,j) ⇔ (Pit in adjacent cells)
  - S(i,j) ⇔ (Wumpus in adjacent cells)

- Inference:
  - Uses resolution to prove whether a cell is safe or unsafe
  - A cell is considered safe if both:
    - No pit can be inferred
    - No Wumpus can be inferred

## Tech Stack

- Backend: Python (Flask)
- Frontend: HTML, CSS, JavaScript
- AI Logic:
  - Propositional Logic
  - CNF Conversion
  - Resolution Algorithm

## Project Structure
