import qiskit
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit import Aer, transpile, assemble
import math
import random
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from functools import partial

#뽑아주고자 했던 변수를 앞에서 미리 정의한다 
iter = 5
# function for plot
class OpObj(object):
    def __init__(self):
        #맨처음 params의 초기값 
        self.x_0 = [float(random.randint(0,3000))/1000 for i in range(0, 9)]
        #minimize 중간에 뽑아져 나오는 값을 담을 변수
        self.f = np.full(shape=(iter,), fill_value=np.NaN)
        #그걸 f 의 몇번째에 넣을지 계산하는 변수 
        self.count = 0

    def _fun(self, param):
        #여기에 계산된 param: (xk)의 값을 집어넣는다
        return calculate_cost_function(param)

#뽑아진 obj_fun의 값에다가 중간 param을 넣어서 계산할 값임 
def cb(xk, obj=None):
    obj.f[obj.count] = xk
    obj.count += 1


# fig, ax = plt.subplots(1,1)
x = np.linspace(1,iter, iter)

op_obj = OpObj()



def apply_fixed_ansatz(qubits, parameters):

    for iz in range (0, len(qubits)):
        circ.ry(parameters[0][iz], qubits[iz])

    circ.cz(qubits[0], qubits[1])
    circ.cz(qubits[2], qubits[0])

    for iz in range (0, len(qubits)):
        circ.ry(parameters[1][iz], qubits[iz])

    circ.cz(qubits[1], qubits[2])
    circ.cz(qubits[2], qubits[0])

    for iz in range (0, len(qubits)):
        circ.ry(parameters[2][iz], qubits[iz])

# circ = QuantumCircuit(3)
# apply_fixed_ansatz([0, 1, 2], [[1, 1, 1], [1, 1, 1], [1, 1, 1]])

# Creates the Hadamard test

def had_test(gate_type, qubits, auxiliary_index, parameters):

    circ.h(auxiliary_index)

    apply_fixed_ansatz(qubits, parameters)

    for ie in range (0, len(gate_type[0])):
        if (gate_type[0][ie] == 1):
            circ.cz(auxiliary_index, qubits[ie])

    for ie in range (0, len(gate_type[1])):
        if (gate_type[1][ie] == 1):
            circ.cz(auxiliary_index, qubits[ie])
    
    circ.h(auxiliary_index)
    
# circ = QuantumCircuit(4)
# had_test([[0, 0, 0], [0, 0, 1]], [1, 2, 3], 0, [[1, 1, 1], [1, 1, 1], [1, 1, 1]])

# Creates controlled anstaz for calculating |<b|psi>|^2 with a Hadamard test

def control_fixed_ansatz(qubits, parameters, auxiliary, reg):

    for i in range (0, len(qubits)):
        circ.cry(parameters[0][i], qiskit.circuit.Qubit(reg, auxiliary), qiskit.circuit.Qubit(reg, qubits[i]))

    circ.ccx(auxiliary, qubits[1], 4)
    circ.cz(qubits[0], 4)
    circ.ccx(auxiliary, qubits[1], 4)

    circ.ccx(auxiliary, qubits[0], 4)
    circ.cz(qubits[2], 4)
    circ.ccx(auxiliary, qubits[0], 4)

    for i in range (0, len(qubits)):
        circ.cry(parameters[1][i], qiskit.circuit.Qubit(reg, auxiliary), qiskit.circuit.Qubit(reg, qubits[i]))

    circ.ccx(auxiliary, qubits[2], 4)
    circ.cz(qubits[1], 4)
    circ.ccx(auxiliary, qubits[2], 4)

    circ.ccx(auxiliary, qubits[0], 4)
    circ.cz(qubits[2], 4)
    circ.ccx(auxiliary, qubits[0], 4)

    for i in range (0, len(qubits)):
        circ.cry(parameters[2][i], qiskit.circuit.Qubit(reg, auxiliary), qiskit.circuit.Qubit(reg, qubits[i]))

# q_reg = QuantumRegister(5)
# circ = QuantumCircuit(q_reg)
# control_fixed_ansatz([1, 2, 3], [[1, 1, 1], [1, 1, 1], [1, 1, 1]], 0, q_reg)

def control_b(auxiliary, qubits):

    for ia in qubits:
        circ.ch(auxiliary, ia)

# circ = QuantumCircuit(4)
# control_b(0, [1, 2, 3])

# Create the controlled Hadamard test, for calculating <psi|psi>

def special_had_test(gate_type, qubits, auxiliary_index, parameters, reg):
    # 여기에서 사용된 circ 는 
    # (아마) 자기 함수가 불린 scope 의 가장 인접한 부분의 circ 변수를 부르는 것일듯  
    circ.h(auxiliary_index)

    control_fixed_ansatz(qubits, parameters, auxiliary_index, reg)

    for ty in range (0, len(gate_type)):
        if (gate_type[ty] == 1):
            circ.cz(auxiliary_index, qubits[ty])


    control_b(auxiliary_index, qubits)
    
    circ.h(auxiliary_index)




# ========================= learning start =========================
# A = 0.55I + 0.225Z_2 + 0.225Z_3


# Implements the entire cost function on the quantum circuit

def calculate_cost_function(parameters):
    
    global opt

    overall_sum_1 = 0
    
    parameters = [parameters[0:3], parameters[3:6], parameters[6:9]]

    for i in range(0, len(gate_set)):
        for j in range(0, len(gate_set)):

            global circ

            qctl = QuantumRegister(5)
            qc = ClassicalRegister(5)
            circ = QuantumCircuit(qctl, qc)

            backend = Aer.get_backend('aer_simulator')
            
            multiply = coefficient_set[i]*coefficient_set[j]

            had_test([gate_set[i], gate_set[j]], [1, 2, 3], 0, parameters)

            circ.save_statevector()
            t_circ = transpile(circ, backend)
            qobj = assemble(t_circ)
            job = backend.run(qobj)

            result = job.result()
            outputstate = np.real(result.get_statevector(circ, decimals=100))
            o = outputstate

            m_sum = 0
            for l in range (0, len(o)):
                if (l%2 == 1):
                    n = o[l]**2
                    m_sum+=n

            overall_sum_1+=multiply*(1-(2*m_sum))

    overall_sum_2 = 0

    for i in range(0, len(gate_set)):
        for j in range(0, len(gate_set)):

            multiply = coefficient_set[i]*coefficient_set[j]
            mult = 1

            for extra in range(0, 2):

                qctl = QuantumRegister(5)
                qc = ClassicalRegister(5)
                circ = QuantumCircuit(qctl, qc)

                backend = Aer.get_backend('aer_simulator')

                if (extra == 0):
                    special_had_test(gate_set[i], [1, 2, 3], 0, parameters, qctl)
                if (extra == 1):
                    special_had_test(gate_set[j], [1, 2, 3], 0, parameters, qctl)

                circ.save_statevector()    
                t_circ = transpile(circ, backend)
                qobj = assemble(t_circ)
                job = backend.run(qobj)

                result = job.result()
                outputstate = np.real(result.get_statevector(circ, decimals=100))
                o = outputstate

                m_sum = 0
                for l in range (0, len(o)):
                    if (l%2 == 1):
                        n = o[l]**2
                        m_sum+=n
                mult = mult*(1-(2*m_sum))

            overall_sum_2+=multiply*mult

    print(1-float(overall_sum_2/overall_sum_1))
    # 이제 이 값을 op_obj.f 에 넣어준다 
    cb(xk= 1-float(overall_sum_2/overall_sum_1), obj=op_obj)

    return 1-float(overall_sum_2/overall_sum_1)

coefficient_set = [0.55, 0.225, 0.225]
gate_set = [[0, 0, 0], [0, 1, 0], [0, 0, 1]]

# cost function 을 minimize 하는 parameter alpha 값을 구한다 (9개)

x_soln = minimize(calculate_cost_function, x0= op_obj.x_0, options={'maxiter':iter}, method="COBYLA")

print("op_obj.f ", op_obj.f)
print("x", x)
plt.plot(x, op_obj.f)
plt.show()

# minimize(calculate_cost_function, x0=[float(random.randint(0,3000))/1000 for i in range(0, 9)], method="COBYLA", options={'maxiter':200})

## 여기서 부터는 구한 결과로 비교하는 부분 

# 구한 output 을 쪼갠다  
# 아직 out을 구하지 않은 상황 -> 넣어주어야 함 
# out_f = [out['x'][0:3], out['x'][3:6], out['x'][6:9]]

# # min parameter 을 이용해서 다시 한번 ansatz 를 계산한다 
# circ = QuantumCircuit(3, 3)
# apply_fixed_ansatz([0, 1, 2], out_f)
# circ.save_statevector()

# backend = Aer.get_backend('aer_simulator')

# t_circ = transpile(circ, backend)
# qobj = assemble(t_circ)
# job = backend.run(qobj)

# result = job.result()
# # 그걸로 확률을 구한다 = |x> 
# o = result.get_statevector(circ, decimals=10)

# #얘가 실제 coeff 값을 토대로 만든 matrix A = 0.55I + 0.225Z_2 + 0.225Z_3
# a1 = coefficient_set[2]*np.array([[1,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0], [0,0,1,0,0,0,0,0], [0,0,0,1,0,0,0,0], [0,0,0,0,-1,0,0,0], [0,0,0,0,0,-1,0,0], [0,0,0,0,0,0,-1,0], [0,0,0,0,0,0,0,-1]])
# a0 = coefficient_set[1]*np.array([[1,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0], [0,0,-1,0,0,0,0,0], [0,0,0,-1,0,0,0,0], [0,0,0,0,1,0,0,0], [0,0,0,0,0,1,0,0], [0,0,0,0,0,0,-1,0], [0,0,0,0,0,0,0,-1]])
# a2 = coefficient_set[0]*np.array([[1,0,0,0,0,0,0,0], [0,1,0,0,0,0,0,0], [0,0,1,0,0,0,0,0], [0,0,0,1,0,0,0,0], [0,0,0,0,1,0,0,0], [0,0,0,0,0,1,0,0], [0,0,0,0,0,0,1,0], [0,0,0,0,0,0,0,1]])
# #이게 진짜 최종 matrix A 
# a3 = np.add(np.add(a2, a0), a1)
# #실제 b의 값 
# #이친구 ||b|| 의 값이 1임 ㅋㅋㅋ 
# b = np.array([float(1/np.sqrt(8)),float(1/np.sqrt(8)),float(1/np.sqrt(8)),float(1/np.sqrt(8)),float(1/np.sqrt(8)),float(1/np.sqrt(8)),float(1/np.sqrt(8)),float(1/np.sqrt(8))])

# #결과 값이 1에 가까울수록 좋음 
# # (b * (b' / ||b'||))^2 
# print((b.dot(a3.dot(o)/(np.linalg.norm(a3.dot(o)))))**2)


