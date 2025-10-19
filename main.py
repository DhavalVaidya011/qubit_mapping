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
                    if values in graph[gate_prev.label]:
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

def heuristic_function(layer_F, layer_E, weight, distance_matrix, decay, current_mapping):
    length_F = len(layer_F)
    length_E = max(1, len(layer_E))
    sum_F = 0
    sum_E = 0
    for gate in layer_F:
        qubits = gate.qubits
        sum_F = sum_F + distance_matrix[current_mapping[qubits[0]]][current_mapping[qubits[1]]]
    for gate in layer_E:
        qubits = gate.qubits
        sum_E = sum_E + distance_matrix[current_mapping[qubits[0]]][current_mapping[qubits[1]]]
    
    H = (max(decay[qubits[0]], decay[qubits[1]]) * (1/length_F)*sum_F) + ((weight/length_E)*sum_E)

    return H

def sabre_swap_algorithm(circuit, layer_F, layer_E, current_mapping, distance_matrix, dependency_graph, topology, delta):
    swap_count = 0
    n = len(topology)
    while layer_F:
        # print('entered_again')
        # for gate in layer_F:
        #     print(gate.label)
        decay = [1] * n
        executed_gate_list = []
        # print(current_mapping)
        for gate in layer_F:
            qubits = gate.qubits
            if distance_matrix[current_mapping[qubits[0]]][current_mapping[qubits[1]]] == 1:
                executed_gate_list.append(gate)
        if executed_gate_list:
            for gate in executed_gate_list:
                layer_F.remove(gate)
                for keys in dependency_graph:
                    if gate.label in dependency_graph[keys]:
                        flag = True
                        executed_gate_labels = []
                        for exec_gates in executed_gate_list:
                                labels = exec_gates.label
                                executed_gate_labels.append(labels)
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
            SWAP_candidate_list = []
            for gate in layer_F:
                qubits = gate.qubits
                physicalqubit1 = current_mapping[qubits[0]]
                physicalqubit2 = current_mapping[qubits[1]]
                for qub in topology[physicalqubit1]:
                    for keys in current_mapping:
                        if current_mapping[keys] == qub:
                            SWAP_candidate_list.append([qubits[0], keys])
                            break
                for qub in topology[physicalqubit2]:
                    for keys in current_mapping:
                        if current_mapping[keys] == qub:
                            SWAP_candidate_list.append([qubits[1], keys])
                            break
            temp_mapping = current_mapping.copy()
            h_score_dict = {}
            for swaps in SWAP_candidate_list:
                temp_mapping = copy.deepcopy(current_mapping)
                temp_mapping[swaps[0]] = current_mapping[swaps[1]]
                temp_mapping[swaps[1]] = current_mapping[swaps[0]]
                h_score = heuristic_function(layer_F, layer_E, 0.1, distance_matrix, decay, temp_mapping)
                h_score_dict[tuple(swaps)] = h_score
            # print(h_score_dict)
            min_score_swap = min(h_score_dict, key=h_score_dict.get)
            temp_value = current_mapping[min_score_swap[0]]
            current_mapping[min_score_swap[0]] = current_mapping[min_score_swap[1]]
            current_mapping[min_score_swap[1]] = temp_value
            swap_count += 1
            decay[min_score_swap[0]] += delta
            decay[min_score_swap[1]] += delta
    return current_mapping, swap_count

def tweak_mapping_random(current_mapping, topology):
    new_mapping = copy.deepcopy(current_mapping)
    n = len(topology)
    random_qubit1 = random.randint(0, n-1)
    random_qubit2 = random.randint(0, n-1)
    while random_qubit1 == random_qubit2:
        random_qubit2 = random.randint(0, n-1)
    temp_var = new_mapping[random_qubit1]
    new_mapping[random_qubit1] = new_mapping[random_qubit2]
    new_mapping[random_qubit2] = temp_var

    return new_mapping

if __name__ == "__main__":
    topology = {
        0: {1},
        1: {0, 2, 3},
        2: {1},
        3: {1, 4},
        4: {3}
    }
    initial_mapping = {
        0: 0,
        1: 1,
        2: 2,
        3: 3,
        4: 4
    }
    circuit = [
        Gate('CX', [0, 1], 'g1'),
        Gate('CX', [0, 2], 'g2'),
        Gate('CX', [1, 3], 'g3'),
        Gate('CX', [0, 4], 'g4'),
        Gate('CX', [2, 4], 'g5'),
    ]
    delta = 0.1
    count = 0
    minimum_swap_count = math.inf
    minimum_mapping = {}
    for i in range(100):
        dependency_graph = create_dependency_graph(circuit)
        distance_matrix = create_distance_matrix(topology)
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
            initial_mapping = tweak_mapping_random(new_mapping, topology)
            count = 0
        else:
            initial_mapping = copy.deepcopy(new_mapping)
        print(new_mapping)
        print(swap_count)
    print('Minimum swap count is:', minimum_swap_count)
    print('The initial mapping that gave minimum swap count is:', minimum_mapping)