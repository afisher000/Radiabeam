import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import os
import pandas as pd

def merge_csvs(directory):
    # Read into dataframes
    paths = [os.path.join(directory, file) for file in os.listdir(directory)]
    dfs = [pd.read_csv(path) for path in paths]

    # Combine and drop indices
    df = pd.concat(dfs, axis=0).reset_index(drop=True)
    return df


class Drift():
    def __init__(self, length):
        self.length = length
        return

    def getMatrix(self):
        sub = np.array([
            [1, self.length],
            [0, 1],
        ])

        matrix = np.array(
            [sub, np.zeros((2,2))], 
            [np.zeros((2,2)), sub])
        return matrix

class Quad():
    def __init__(self, quadstr, rigidity, I=0):
        if quadstr=='Q216':
            self.length = 0.072
            self.peak_current = 7.4
            self.peak_gradient = 20
        elif quadstr=='Q394':
            self.length = 0.141
            self.peak_current = 6.88
            self.peak_gradient = 20   
        else:
            raise ValueError('Not valid quad string')
        self.rigidity = rigidity        
        self.I = I
    
    def getMatrix(self):
        gradient =  self.I * self.peak_gradient/self.peak_current

        k = abs(gradient)/self.rigidity
        phi = np.sqrt(k)*self.length
        if self.I>0:
            C = np.cos(phi)
            S = (1/np.sqrt(k))*np.sin(phi)
            Cp = -np.sqrt(k)*np.sin(phi)
            Sp = np.cos(phi)  
        elif self.I<0:
            C = np.cosh(phi)
            S = (1/np.sqrt(k))*np.sinh(phi)
            Cp = np.sqrt(k)*np.sinh(phi)
            Sp = np.cosh(phi)
        else:
            C = 1
            S = self.length
            Cp = 0
            Sp = 1

        matrix = np.array([
            [C, S],
            [Cp, Sp],
        ])
        return matrix


class Beamline():
    def __init__(self, rigidity):
        self.rigidity = rigidity
        self.Q1 = Quad('Q216', rigidity)
        self.Q2 = Quad('Q394', rigidity)
        self.Q3 = Quad('Q216', rigidity)
        self.Q4 = Quad('Q216', rigidity)
        self.Q5 = Quad('Q216', rigidity)

        self.beamline = {
            'D_L2_Q1':Drift(0.2766),
            'Q1':self.Q1,
            'D_Q1_Q2':Drift(0.0376),
            'Q2':self.Q2,
            'D_Q2_Q3':Drift(0.0379),
            'Q3':self.Q3,
            'D_Q3_cam4':Drift(0.5849),
            'D_cam4_cam5':Drift(0.236),
            'D_cam5_Q4':Drift(0.580-0.236),
            'Q4':self.Q4,
            'D_Q4_Q5':Drift(0.073),
            'Q5':self.Q5,
            'D_Q5_cam8':Drift(0.2),
            'D_cam8_cam6':Drift(0.684-0.2),
        }

        self.updateDistances()
        self.updateMatrices()


    def updateDistances(self):
        zs = [0]
        for element in self.beamline.values():
            zs.append(getattr(element, 'length'))

        self.zs = np.cumsum(zs)
        return


    def updateMatrices(self):
        matrices = [np.eye(2)]
        for element in self.beamline.values():
            curr_matrix = matrices[-1]
            next_matrix = element.getMatrix()
            matrices.append(next_matrix.dot(curr_matrix))

        self.matrices = matrices
        return

    def computeSpotsizes(self, beam_initial):
        spotsizes = []
        for matrix in self.matrices:
            beam_final = matrix.dot(beam_initial.dot(matrix.T))
            spotsize = np.sqrt(beam_final[0,0])
            spotsizes.append(spotsize)

        return self.zs, np.array(spotsizes)
    
    def computeGeometricStrength(self):
        ks = []
        for quad in [self.Q1, self.Q2, self.Q3, self.Q4, self.Q5]:
            gradient =  quad.I * quad.peak_gradient/quad.peak_current
            ks.append(abs(gradient)/quad.rigidity)
        return ks
    
    def updateCurrents(self, Is):
        quads = [self.Q1, self.Q2, self.Q3, self.Q4, self.Q5]
        for j, I in enumerate(Is):
            setattr(quads[j], 'I', I)

        self.updateMatrices()


class Optimizer():
    def __init__(self, beamline, measurements):
        self.beamline = beamline
        self.measurements = measurements
        return


    def parse_inputs(self, x):
        beta, alpha, emittance = x
        gamma = (1+alpha**2)/beta

        emittance = emittance*1e-7
        return beta, alpha, gamma, emittance
    
    def print_results(self, x):
        energy = self.beamline.rigidity*299792458
        rel_gamma = energy / 511000
        beta, alpha, gamma, emittance = self.parse_inputs(x)

        print(f'Optimized = {x}')
        print(f'Emittance: {emittance:.2e}')
        print(f'Norm. Emittance: {rel_gamma*emittance:.2e}')
        print(f'Beta Twiss: {beta:.2f}')
        print(f'Alpha Twiss: {alpha:.2f}')
        return

    def error_function(self, x):
        beta, alpha, gamma, emittance = self.parse_inputs(x)

        beam_initial = emittance * np.array([
            [beta, -alpha],
            [-alpha, gamma]
        ])

        error = 0
        for _, meas in self.measurements.iterrows():
            # Set currents
            self.beamline.updateCurrents([meas.Q1, meas.Q2, meas.Q3])
            full_matrix = self.beamline.matrices[-1]

            beam_final = full_matrix.dot(beam_initial.dot(full_matrix.T))

            # Error handle when 0,0 element is negative
            pred_spotsize = np.sqrt(beam_final[0,0])*1e6 if beam_final[0,0]>0 else 2000
            error += ((meas.spotsize_mean - pred_spotsize)/meas.spotsize_std)**2

        return error
    
    def run(self, x0 = [1, 0, .5], bounds = [(0.1, 10), (-5, 5), (.01, 5)]):
        self.result = minimize(self.error_function, x0, method='L-BFGS-B', bounds=bounds)
        self.print_results(self.result.x)
        return
    
    def plot_fit(self):
        beta, alpha, gamma, emittance = self.parse_inputs(self.result.x)

        beam_initial = emittance * np.array([
            [beta, -alpha],
            [-alpha, gamma]
        ])

        pred_spotsizes = []
        for _, meas in self.measurements.iterrows():
            # Set currents
            self.beamline.updateCurrents([meas.Q1, meas.Q2, meas.Q3])
            full_matrix = self.beamline.matrices[-1]

            beam_final = full_matrix.dot(beam_initial.dot(full_matrix.T))
            pred_spotsizes.append(np.sqrt(beam_final[0,0])*1e6)
        self.measurements['pred_spotsize'] = pred_spotsizes

        fig, ax = plt.subplots()
        ax.scatter(self.measurements.Q2, self.measurements.pred_spotsize, color='red', label='Simulation Fit')

        ax.errorbar(self.measurements.Q2, self.measurements.spotsize_mean,
                    yerr=self.measurements.spotsize_std, fmt='none', color='blue', capsize=5, label='Beam Data')
        ax.legend()
        return fig, ax