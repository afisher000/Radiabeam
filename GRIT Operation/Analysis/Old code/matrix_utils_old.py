
import numpy as np
def focusing_matrix(Quad, I, rigidity):
    gradient =  I * Quad['peak_gradient']/Quad['peak_current']

    k = abs(gradient)/rigidity
    phi = np.sqrt(k)*Quad['length']
    if I>0:
        C = np.cos(phi)
        S = (1/np.sqrt(k))*np.sin(phi)
        Cp = -np.sqrt(k)*np.sin(phi)
        Sp = np.cos(phi)  
    else:
        C = np.cosh(phi)
        S = (1/np.sqrt(k))*np.sinh(phi)
        Cp = np.sqrt(k)*np.sinh(phi)
        Sp = np.cosh(phi)

    matrix = prop_matrix(C, S, Cp, Sp)
    return matrix


def drift_matrix(L):
    matrix = prop_matrix(1, L, 0, 1)
    return matrix

def prop_matrix(C, S, Cp, Sp):
    beam_matrix = np.array([
        [C, S],
        [Cp, Sp],
    ])
        
    twiss_matrix = np.array([
        [C*C, -2*C*S, S*S],
        [-C*Cp, C*Sp+S*Cp, -S*Sp],
        [Cp*Cp, -2*Cp*Sp, Sp*Sp]
    ])
    return beam_matrix

def compute_K(I, rigidity, Quad='Q216'):
    if Quad=='Q216':
        Quad = {'length':0.072, 'peak_current':7.4, 'peak_gradient':20}
    elif Quad=='Q394':
        Quad = {'length':0.141, 'peak_current':6.88, 'peak_gradient':20}

    gradient =  I * Quad['peak_gradient']/Quad['peak_current']
    k = abs(gradient)/rigidity
    return k


def compute_transport_matrices(currents, rigidity):
    I1, I2, I3 = currents

    # Drift lengths
    D0 = .27663
    D1 = .0376
    D2 = .0379
    D3 = .5849

    #Quadropole Lengths and Peak Currents
    Q216 = {'length':0.072, 'peak_current':7.4, 'peak_gradient':20}
    Q394 = {'length':0.141, 'peak_current':6.88, 'peak_gradient':20}

    matrices = [
        drift_matrix(D0),
        focusing_matrix(Q216, I1, rigidity),
        drift_matrix(D1),
        focusing_matrix(Q394, I2, rigidity),
        drift_matrix(D2),
        focusing_matrix(Q216, I3, rigidity),
        drift_matrix(D3)
    ]

    zs = np.cumsum([0, D0, Q216['length'], D1, Q394['length'], D2, Q216['length'], D3])

    curr_matrix = np.eye(2)
    all_matrices = [curr_matrix]
    for matrix in matrices:
        curr_matrix = matrix.dot(curr_matrix)
        all_matrices.append(curr_matrix)

    return zs, all_matrices
    
def compute_transport_matrix(I1, I2, I3, rigidity, cam):
    # Drift lengths
    D0 = .27663
    D1 = .0376
    D2 = .0379
    if cam=='cam4':
        D3 = .5849
    elif cam=='cam5':
        D3 = .5849 + .236 #popin 5 is .236 beyond popin4
    elif cam=='cam6':
        D3 = .5849 + 1.481 
    else:
        raise ValueError('Not a valid "cam" input')

    #Quadropole Lengths and Peak Currents
    Q216 = {'length':0.072, 'peak_current':7.4, 'peak_gradient':20}
    Q394 = {'length':0.141, 'peak_current':6.88, 'peak_gradient':20}

    matrices = [
        drift_matrix(D0),
        focusing_matrix(Q216, I1, rigidity),
        drift_matrix(D1),
        focusing_matrix(Q394, I2, rigidity),
        drift_matrix(D2),
        focusing_matrix(Q216, I3, rigidity),
        drift_matrix(D3)
    ]

    curr_matrix = np.eye(   2)
    for matrix in matrices:
        curr_matrix = matrix.dot(curr_matrix)

    return curr_matrix

def unpack_series(csv_path):
    df = pd.read_csv(csv_path, index_col=0, header=None).squeeze('columns').to_frame().T
    df.to_csv(csv_path)