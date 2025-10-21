import math
import copy
import random

class Gate:
    def __init__(self, name, qubits, label):
        self.name = name
        self.qubits = qubits
        self.label = label

def are_dependencies(gate_prev, gate):
    qubits1 = gate_prev.qubits
    qubits2 = gate.qubits
    if qubits1[0] in qubits2 or qubits1[1] in qubits2:
        return True
    else:
        return False

def create_dependency_graph(circuit):
    graph = {}
    for gate in circuit:
        for gate_prev in circuit:
            if gate_prev == gate:
                break
            elif are_dependencies(gate_prev, gate):
                if gate.label not in graph:
                    graph[gate.label] = set()
                for values in list(graph[gate.label]):
                    if values in list([gate_prev.label]):
                        graph[gate.label].remove(values)
                graph[gate.label].add(gate_prev.label)
    return graph

def create_distance_matrix(topology):
    n = len(topology)
    dist = [[math.inf for _ in range(n)] for _ in range(n)]
    for node in topology:
        dist[node][node] = 0
        for neighbors in topology[node]:
            dist[node][neighbors] = 1
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if (dist[i][k] != math.inf) and (dist[k][j] != math.inf):
                    dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
    return dist

def create_layers(circuit, dependency_graph, executed_list):
    layer_F = []
    layer_E = []

    for gate in circuit:
        gate_name = gate.label
        if gate_name not in dependency_graph:
            layer_F.append(gate)
        else:
            layer_E.append(gate)
    
    return layer_F, layer_E

def heuristic_function(layer_F, layer_E, weight, distance_matrix, decay, current_mapping, swapped_qubit_pair):
    length_F = len(layer_F)
    length_E = max(1, len(layer_E))
    sum_F = 0
    sum_E = 0
    for gate in layer_F:
        qubits = gate.qubits
        if not swapped_qubit_pair[0] in qubits and not swapped_qubit_pair[1] in qubits:
            continue
        sum_F = sum_F + distance_matrix[current_mapping[qubits[0]]][current_mapping[qubits[1]]]
    for gate in layer_E:
        qubits = gate.qubits
        if not swapped_qubit_pair[0] in qubits and not swapped_qubit_pair[1] in qubits:
            continue
        sum_E = sum_E + distance_matrix[current_mapping[qubits[0]]][current_mapping[qubits[1]]]
    
    H = (max(decay[swapped_qubit_pair[0]], decay[swapped_qubit_pair[1]]) * (1/length_F)*sum_F) + ((weight/length_E)*sum_E)

    return H

def sabre_swap_algorithm(circuit, layer_F, layer_E, current_mapping, distance_matrix, dependency_graph, topology, delta):
    print('--------')
    swap_count = 0
    n = len(topology)
    executed_gates = []
    executed_gate_labels = []
    while layer_F:
        decay = [1] * n
        execute_gate_list = []
        for gate in layer_F:
            qubits = gate.qubits
            if distance_matrix[current_mapping[qubits[0]]][current_mapping[qubits[1]]] == 1:
                executed_gates.append(gate)
                executed_gate_labels.append(gate.label)
                execute_gate_list.append(gate)
            print(gate.label)
        print(executed_gate_labels)
        if execute_gate_list:
            for gate in execute_gate_list:
                layer_F.remove(gate)
                for keys in dependency_graph:
                    if gate.label in dependency_graph[keys]:
                        flag = True
                        for values in dependency_graph[keys]:
                            if values not in executed_gate_labels:
                                flag = False
                                break
                        if flag:
                            for gate_obj in circuit:
                                if gate_obj.label == keys:
                                    layer_F.append(gate_obj)
                                    layer_E.remove(gate_obj)
                                    break
            continue
        else:
            SWAP_candidate_set = set()
            for gate in layer_F:
                qubits = gate.qubits
                physicalqubit1 = current_mapping[qubits[0]]
                physicalqubit2 = current_mapping[qubits[1]]
                for qub in topology[physicalqubit1]:
                    for keys in current_mapping:
                        if current_mapping[keys] == qub:
                            # Add tuple to set to avoid duplicates
                            swap_pair = tuple(sorted([qubits[0], keys]))
                            SWAP_candidate_set.add(swap_pair)
                            break
                for qub in topology[physicalqubit2]:
                    for keys in current_mapping:
                        if current_mapping[keys] == qub:
                            # Add tuple to set to avoid duplicates
                            swap_pair = tuple(sorted([qubits[1], keys]))
                            SWAP_candidate_set.add(swap_pair)
                            break
            temp_mapping = current_mapping.copy()
            h_score_dict = {}
            for swaps in SWAP_candidate_set:
                temp_mapping = copy.deepcopy(current_mapping)
                temp_mapping[swaps[0]] = current_mapping[swaps[1]]
                temp_mapping[swaps[1]] = current_mapping[swaps[0]]
                h_score = heuristic_function(layer_F, layer_E, 0.1, distance_matrix, decay, temp_mapping, swaps)
                h_score_dict[tuple(swaps)] = h_score
            print(h_score_dict)
            min_score_swap = min(h_score_dict, key=h_score_dict.get)
            print(min_score_swap)
            temp_value = current_mapping[min_score_swap[0]]
            current_mapping[min_score_swap[0]] = current_mapping[min_score_swap[1]]
            current_mapping[min_score_swap[1]] = temp_value
            swap_count += 1
            decay[min_score_swap[0]] += delta
            decay[min_score_swap[1]] += delta
            print('-------------Used SWAP here----------------')
    return current_mapping, swap_count

def tweak_mapping_random(current_mapping, topology, tweaking_parameter):
    new_mapping = copy.deepcopy(current_mapping)
    n = len(topology)
    
    num_qubits_to_rotate = max(2, int(tweaking_parameter * n))
    random_qubit_list = random.sample(range(n), num_qubits_to_rotate)
    
    if len(random_qubit_list) > 1:
        temp_var = new_mapping[random_qubit_list[0]]
        
        for i in range(len(random_qubit_list) - 1):
            new_mapping[random_qubit_list[i]] = new_mapping[random_qubit_list[i + 1]]

        new_mapping[random_qubit_list[-1]] = temp_var
    
    return new_mapping

def generate_reverse_circuit(circuit):
    new_circuit = []
    for gate in circuit:
        new_circuit = [gate] + new_circuit
    
    return new_circuit

def generate_random_mapping(topology):
    n = len(topology)
    random_qubit_list = random.sample(range(n), n)
    initial_mapping = {}
    for i in range(n):
        initial_mapping[i] = random_qubit_list[i]

    return initial_mapping
    
if __name__ == "__main__":
    topology = {
        0: {1},
        1: {0, 2, 3},
        2: {1},
        3: {1, 4},
        4: {3}
    }
    initial_mapping = generate_random_mapping(topology)
    circuit = [
        Gate('CX', [0, 1], 'g1'),
        Gate('CX', [0, 2], 'g2'),
        Gate('CX', [1, 3], 'g3'),
        Gate('CX', [0, 4], 'g4'),
        Gate('CX', [2, 4], 'g5'),
    ]
    distance_matrix = create_distance_matrix(topology)
    reverse_circuit = generate_reverse_circuit(circuit)
    delta = 0.1
    count = 0
    minimum_swap_count = math.inf
    minimum_mapping = {}
    reverse_flag = False
    for i in range(100):
        if reverse_flag == False:
            dependency_graph = create_dependency_graph(circuit)
            print(dependency_graph)
            current_initial_mapping = copy.deepcopy(initial_mapping)
            print(current_initial_mapping)
            layer_F, layer_E = create_layers(circuit, dependency_graph, [])
            new_mapping, swap_count = sabre_swap_algorithm(circuit, layer_F, layer_E, initial_mapping, 
                        distance_matrix, dependency_graph, topology, delta)
            if swap_count < minimum_swap_count:
                minimum_swap_count = swap_count
                minimum_mapping = current_initial_mapping
            if new_mapping == initial_mapping:
                count += 1
            else:
                count = 0
            if count == 5:
                initial_mapping = tweak_mapping_random(new_mapping, topology, 0.2)
                count = 0
            else:
                initial_mapping = copy.deepcopy(new_mapping)
            reverse_flag = True
        else:
            dependency_graph = create_dependency_graph(reverse_circuit)
            current_initial_mapping = copy.deepcopy(initial_mapping)
            print(current_initial_mapping)
            layer_F, layer_E = create_layers(reverse_circuit, dependency_graph, [])
            new_mapping, swap_count = sabre_swap_algorithm(reverse_circuit, layer_F, layer_E, initial_mapping, 
                        distance_matrix, dependency_graph, topology, delta)
            if swap_count < minimum_swap_count:
                minimum_swap_count = swap_count
                minimum_mapping = current_initial_mapping
            if new_mapping == initial_mapping:
                count += 1
            else:
                count = 0
            if count == 5:
                initial_mapping = tweak_mapping_random(new_mapping, topology, 0.2)
                count = 0
            else:
                initial_mapping = copy.deepcopy(new_mapping)
            reverse_flag = False
        
    print('Minimum swap count is:', minimum_swap_count)
    print('The initial mapping that gave minimum swap count is:', minimum_mapping)