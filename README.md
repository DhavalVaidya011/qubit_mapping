# Qubit Mapping
- To execute the program, open command prompt and run `python main.py` or `python3 main.py` depending on the virtual environment.
- The gates are in the form of Gate('CX', [0,2], 'g1'), where 'g1' is the label and [0,2] are the qubits on which the 'CX' gate is acting. You can add more gates or remove gates to test the code.
- The code can only support two qubit gates and all gates can be decomposed into a combination of single qubit gates and two qubit gates. Single qubit gates are not supported by the code as their case is trivial.