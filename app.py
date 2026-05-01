from flask import Flask, render_template, request, jsonify
import random
from itertools import combinations
from collections import deque
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

class ResolutionEngine:
    def __init__(self):
        self.kb_clauses = []
        self.inference_steps = 0
    
    def negate(self, literal):
        if literal.startswith('~'):
            return literal[1:]
        else:
            return f"~{literal}"
    
    def to_cnf(self, formula):
        clauses = []
        
        if '⇔' in formula:
            left, right = formula.split('⇔')
            left = left.strip()
            right = right.strip()
            
            if left.startswith('(') and left.endswith(')'):
                left = left[1:-1]
            if right.startswith('(') and right.endswith(')'):
                right = right[1:-1]
            
            if '∨' in right:
                right_disjuncts = [r.strip() for r in right.split('∨')]
                clause1 = [self.negate(left)] + right_disjuncts
                clauses.append(clause1)
                
                for disjunct in right_disjuncts:
                    clause2 = [self.negate(disjunct), left]
                    clauses.append(clause2)
            else:
                clause1 = [self.negate(left), right]
                clauses.append(clause1)
                clause2 = [self.negate(right), left]
                clauses.append(clause2)
        
        elif '⇒' in formula:
            left, right = formula.split('⇒')
            left = left.strip()
            right = right.strip()
            clauses.append([self.negate(left), right])
        
        else:
            clauses.append([formula])
        
        return clauses
    
    def tell(self, statement):
        clauses = self.to_cnf(statement)
        for clause in clauses:
            standardized_clause = list(set(clause))
            if standardized_clause not in self.kb_clauses:
                self.kb_clauses.append(standardized_clause)
    
    def ask(self, query):
        negated_query = self.negate(query)
        temp_clauses = [list(set(clause)) for clause in self.kb_clauses]
        temp_clauses.append([negated_query])
        
        self.inference_steps = 0
        return self._resolve(temp_clauses)
    
    def _resolve(self, clauses):
        clauses = [set(c) for c in clauses]
        new_clauses = []
        
        while True:
            pairs = list(combinations(range(len(clauses)), 2))
            
            for i, j in pairs:
                resolvents = self._resolve_pair(clauses[i], clauses[j])
                self.inference_steps += 1
                
                for resolvent in resolvents:
                    if not resolvent:
                        return True
                    if resolvent not in clauses and resolvent not in new_clauses:
                        new_clauses.append(resolvent)
            
            if not new_clauses:
                return False
            
            clauses.extend(new_clauses)
            new_clauses = []
    
    def _resolve_pair(self, clause1, clause2):
        resolvents = []
        
        for lit1 in clause1:
            for lit2 in clause2:
                if lit1 == self.negate(lit2):
                    resolvent = (clause1 - {lit1}) | (clause2 - {lit2})
                    resolvents.append(set(resolvent))
        
        return resolvents

class WumpusWorld:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.agent_pos = (0, 0)
        self.kb = ResolutionEngine()
        self.visited = [[False for _ in range(cols)] for _ in range(rows)]
        self.safe_cells = [[None for _ in range(cols)] for _ in range(rows)]
        self.percepts = {'breeze': False, 'stench': False}
        self.game_over = False
        self.game_result = None
        self.gold_pos = None
        self.has_gold = False
        self.gold_taken = False
        
        self._init_environment()
    
    def _init_environment(self):
        total_cells = self.rows * self.cols
        num_pits = max(1, int(total_cells * 0.12))
        
        self.pits = set()
        while len(self.pits) < num_pits:
            pit = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
            if pit != (0, 0):
                self.pits.add(pit)
        
        self.wumpus_pos = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
        while self.wumpus_pos == (0, 0) or self.wumpus_pos in self.pits:
            self.wumpus_pos = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
        
        self.gold_pos = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
        while self.gold_pos == (0, 0) or self.gold_pos in self.pits or self.gold_pos == self.wumpus_pos:
            self.gold_pos = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
        
        self.visited[0][0] = True
        self.safe_cells[0][0] = True
        self.kb.tell(f"~P_0_0")
        self.kb.tell(f"~W_0_0")
        
        self._sense_percepts()
        self._update_kb()
    
    def _get_adjacent(self, r, c):
        adj = []
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                adj.append((nr, nc))
        return adj
    
    def _sense_percepts(self):
        r, c = self.agent_pos
        breeze = any(adj in self.pits for adj in self._get_adjacent(r, c))
        stench = any(adj == self.wumpus_pos for adj in self._get_adjacent(r, c))
        
        self.percepts = {'breeze': breeze, 'stench': stench}
        return self.percepts
    
    def _update_kb(self):
        r, c = self.agent_pos
        adjacent_cells = self._get_adjacent(r, c)
        
        if adjacent_cells:
            pit_disjuncts = [f"P_{ar}_{ac}" for ar, ac in adjacent_cells]
            pit_disjunction = " ∨ ".join(pit_disjuncts)
            breeze_rule = f"B_{r}_{c} ⇔ ({pit_disjunction})"
            self.kb.tell(breeze_rule)
            
            if self.percepts['breeze']:
                self.kb.tell(f"B_{r}_{c}")
            else:
                self.kb.tell(f"~B_{r}_{c}")
                for ar, ac in adjacent_cells:
                    self.safe_cells[ar][ac] = True
                    self.kb.tell(f"~P_{ar}_{ac}")
        
        if adjacent_cells:
            wumpus_disjuncts = [f"W_{ar}_{ac}" for ar, ac in adjacent_cells]
            wumpus_disjunction = " ∨ ".join(wumpus_disjuncts)
            stench_rule = f"S_{r}_{c} ⇔ ({wumpus_disjunction})"
            self.kb.tell(stench_rule)
            
            if self.percepts['stench']:
                self.kb.tell(f"S_{r}_{c}")
            else:
                self.kb.tell(f"~S_{r}_{c}")
                for ar, ac in adjacent_cells:
                    self.safe_cells[ar][ac] = True
                    self.kb.tell(f"~W_{ar}_{ac}")
    
    def _query_safety(self, r, c):
        if (r, c) == self.agent_pos:
            return True
            
        if self.safe_cells[r][c] is True:
            return True
        if self.safe_cells[r][c] is False:
            return False
        
        pit_safe = not self.kb.ask(f"P_{r}_{c}")
        wumpus_safe = not self.kb.ask(f"W_{r}_{c}")
        
        is_safe = pit_safe and wumpus_safe
        
        self.safe_cells[r][c] = is_safe
        
        if is_safe:
            self.kb.tell(f"~P_{r}_{c}")
            self.kb.tell(f"~W_{r}_{c}")
        
        return is_safe
    
    def _get_safe_unvisited(self):
        safe_unvisited = []
        for r in range(self.rows):
            for c in range(self.cols):
                if not self.visited[r][c] and self._query_safety(r, c):
                    safe_unvisited.append((r, c))
        return safe_unvisited
    
    def _find_path(self, start, targets):
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            pos, path = queue.popleft()
            
            if pos in targets:
                return path
            
            for adj in self._get_adjacent(pos[0], pos[1]):
                if adj not in visited and self._query_safety(adj[0], adj[1]):
                    visited.add(adj)
                    queue.append((adj, path + [adj]))
        
        return None
    
    def _move_agent(self):
        safe_unvisited = self._get_safe_unvisited()
        
        if not self.gold_taken and self.gold_pos not in safe_unvisited:
            if self._query_safety(self.gold_pos[0], self.gold_pos[1]):
                safe_unvisited.append(self.gold_pos)
        
        if not safe_unvisited:
            return False
        
        path = self._find_path(self.agent_pos, safe_unvisited)
        
        if path and len(path) > 1:
            self.agent_pos = path[1]
            return True
        
        return False
    
    def step(self):
        if self.game_over:
            return 'game_over', self.game_result
        
        self.visited[self.agent_pos[0]][self.agent_pos[1]] = True
        self.safe_cells[self.agent_pos[0]][self.agent_pos[1]] = True
        
        if self.agent_pos == self.gold_pos and not self.gold_taken:
            self.has_gold = True
            self.gold_taken = True
            return 'gold', None
        
        if self.agent_pos == self.wumpus_pos:
            self.game_over = True
            self.game_result = 'wumpus'
            return 'game_over', 'wumpus'
        
        if self.agent_pos in self.pits:
            self.game_over = True
            self.game_result = 'pit'
            return 'game_over', 'pit'
        
        self._sense_percepts()
        self._update_kb()
        
        moved = self._move_agent()
        
        all_safe_visited = True
        for r in range(self.rows):
            for c in range(self.cols):
                if self._query_safety(r, c) and not self.visited[r][c]:
                    all_safe_visited = False
                    break
        
        if all_safe_visited:
            return 'complete', None
        
        if not moved:
            return 'stuck', None
        
        return 'continue', None
    
    def get_grid_state(self):
        grid = []
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                cell = {
                    'has_pit': (r, c) in self.pits,
                    'has_wumpus': (r, c) == self.wumpus_pos,
                    'has_gold': (r, c) == self.gold_pos,
                    'has_agent': (r, c) == self.agent_pos,
                    'visited': self.visited[r][c],
                    'safe': self.safe_cells[r][c] is True,
                    'unsafe': self.safe_cells[r][c] is False,
                    'breeze': False,
                    'stench': False,
                    'has_gold_taken': self.gold_taken
                }
                row.append(cell)
            grid.append(row)
        
        if not self.game_over and self.agent_pos:
            r, c = self.agent_pos
            if 0 <= r < self.rows and 0 <= c < self.cols:
                grid[r][c]['breeze'] = self.percepts['breeze']
                grid[r][c]['stench'] = self.percepts['stench']
        
        return grid

game_instance = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init', methods=['POST'])
def init_game():
    global game_instance
    try:
        data = request.json
        rows = int(data.get('rows', 5))
        cols = int(data.get('cols', 5))
        game_instance = WumpusWorld(rows, cols)
        
        grid_state = game_instance.get_grid_state()
        visited_count = sum(sum(1 for cell in row if cell['visited']) for row in grid_state)
        safe_count = sum(sum(1 for cell in row if cell['safe']) for row in grid_state)
        
        return jsonify({
            'status': 'initialized',
            'grid': grid_state,
            'inference_steps': 0,
            'visited_count': visited_count,
            'safe_count': safe_count,
            'percepts': game_instance.percepts,
            'has_gold': False
        }), 200
    except Exception as e:
        print(f"Error in init_game: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/step', methods=['POST'])
def step_game():
    global game_instance
    if not game_instance:
        return jsonify({'status': 'error', 'message': 'Game not initialized'}), 400
    
    try:
        status, reason = game_instance.step()
        
        grid_state = game_instance.get_grid_state()
        visited_count = sum(sum(1 for cell in row if cell['visited']) for row in grid_state)
        safe_count = sum(sum(1 for cell in row if cell['safe']) for row in grid_state)
        
        return jsonify({
            'status': status,
            'reason': reason,
            'grid': grid_state,
            'inference_steps': game_instance.kb.inference_steps,
            'visited_count': visited_count,
            'safe_count': safe_count,
            'percepts': game_instance.percepts,
            'has_gold': game_instance.has_gold
        }), 200
    except Exception as e:
        print(f"Error in step_game: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Make sure templates folder exists
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    print("=" * 50)
    print("Starting Wumpus World server...")
    print("Make sure 'templates/index.html' exists")
    print("Open http://127.0.0.1:5000 in your browser")
    print("=" * 50)
    app.run(debug=True, host='127.0.0.1', port=5000)
