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

        matrix = np.block([
            [sub, np.zeros((2,2))], 
            [np.zeros((2,2)), sub]
            ])
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

        if k==0:
            sub = np.array([
                [1, self.length],
                [0, 1],
            ])
            matrix = np.block([
                [sub, np.zeros((2,2))], 
                [np.zeros((2,2)), sub]
                ])
        
        else:

            focusing = np.array([
                [np.cos(phi),               (1/np.sqrt(k))*np.sin(phi)  ],
                [-np.sqrt(k)*np.sin(phi),   np.cos(phi)                 ]
            ])

            defocusing = np.array([
                [np.cosh(phi),              (1/np.sqrt(k))*np.sinh(phi) ],
                [np.sqrt(k)*np.sinh(phi),   np.cosh(phi)                ]
            ])

            if self.I>0:
                matrix = np.block([
                    [focusing, np.zeros((2,2))], 
                    [np.zeros((2,2)), defocusing]
                    ])
            else:
                matrix = np.block([
                    [defocusing, np.zeros((2,2))], 
                    [np.zeros((2,2)), focusing]
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
            # 'D_cam4_cam5':Drift(0.236),
            # 'D_cam5_Q4':Drift(0.580-0.236),
            # 'Q4':self.Q4,
            # 'D_Q4_Q5':Drift(0.073),
            # 'Q5':self.Q5,
            # 'D_Q5_cam8':Drift(0.2),
            # 'D_cam8_cam6':Drift(0.684-0.2),
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
        matrices = [np.eye(4)]
        for element in self.beamline.values():
            curr_matrix = matrices[-1]
            next_matrix = element.getMatrix()
            matrices.append(next_matrix.dot(curr_matrix))

        self.matrices = matrices
        return

    def computeSpotsizes(self, beam_initial):
        xs = []
        ys = []
        for matrix in self.matrices:
            beam_final = matrix.dot(beam_initial.dot(matrix.T))
            xrms = np.sqrt(beam_final[0,0])
            yrms = np.sqrt(beam_final[2,2])
            xs.append(xrms)
            ys.append(yrms)

        return self.zs, np.array(xs), np.array(ys)
    
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


class QuadscanFit():
    def __init__(self, beamline, measurements):
        self.beamline = beamline
        self.measurements = measurements
        return


    def parse_inputs(self, args, list_args=False):
        xbeta, xalpha, xemit, ybeta, yalpha, yemit = args
        xgamma = (1+xalpha**2)/xbeta
        ygamma = (1+yalpha**2)/ybeta

        xemit = xemit*1e-7
        yemit = yemit*1e-7

        if list_args:
            return xbeta, xalpha, xgamma, xemit, ybeta, yalpha, ygamma, yemit
        else:
            beam_matrix = np.array([
                [xbeta*xemit, -xalpha*xemit, 0, 0],
                [-xalpha*xemit, xgamma*xemit, 0, 0],
                [0, 0, ybeta*yemit, -yalpha*yemit],
                [0, 0, -yalpha*yemit, ygamma*yemit]
            ])
            return beam_matrix
    
    def print_results(self, x):
        energy = self.beamline.rigidity*299792458
        rel_gamma = energy / 511000


        xbeta, xalpha, xgamma, xemit, ybeta, yalpha, ygamma, yemit = self.parse_inputs(x, list_args=True)
        self.beam_matrix = self.parse_inputs(x)

        print('---------- X ----------')
        print(f'Emittance: {xemit:.2e}')
        print(f'Norm. Emittance: {rel_gamma*xemit:.2e}')
        print(f'Beta Twiss: {xbeta:.2f}')
        print(f'Alpha Twiss: {xalpha:.2f}')

        print('---------- Y ----------')
        print(f'Emittance: {yemit:.2e}')
        print(f'Norm. Emittance: {rel_gamma*yemit:.2e}')
        print(f'Beta Twiss: {ybeta:.2f}')
        print(f'Alpha Twiss: {yalpha:.2f}')

        print('Beam Matrix:')
        print(repr(self.beam_matrix))
        return

    def error_function(self, x):
        beam_initial = self.parse_inputs(x)

        error = 0
        for _, meas in self.measurements.iterrows():
            # Set currents
            self.beamline.updateCurrents([meas.Q1, meas.Q2, meas.Q3])
            full_matrix = self.beamline.matrices[-1]

            beam_final = full_matrix.dot(beam_initial.dot(full_matrix.T))

            # Error handle when 0,0 element is negative
            xpred = np.sqrt(beam_final[0,0])*1e6 if beam_final[0,0]>0 else 2000
            ypred = np.sqrt(beam_final[2,2])*1e6 if beam_final[2,2]>0 else 2000

            error += ((meas.xrms_mean - xpred)/meas.xrms_std)**2
            error += ((meas.yrms_mean - ypred)/meas.yrms_std)**2

        return error
    
    def run(self, 
            x0 = [1, 0, .5, 1, 0, .5], 
            bounds = [(0.1, 10), (-5, 5), (.01, 5), (0.1, 10), (-5, 5), (.01, 5)]
            ):
        self.result = minimize(self.error_function, x0, method='L-BFGS-B', bounds=bounds)
        self.print_results(self.result.x)
        return
    
    def plot_fit(self):
        beam_initial = self.parse_inputs(self.result.x)

        xpreds = []
        ypreds = []
        for _, meas in self.measurements.iterrows():
            # Set currents
            self.beamline.updateCurrents([meas.Q1, meas.Q2, meas.Q3])
            full_matrix = self.beamline.matrices[-1]

            beam_final = full_matrix.dot(beam_initial.dot(full_matrix.T))

            xpreds.append(np.sqrt(beam_final[0,0])*1e6)
            ypreds.append(np.sqrt(beam_final[2,2])*1e6)

        self.measurements['xpred'] = xpreds
        self.measurements['ypred'] = ypreds


        fig, ax = plt.subplots()
        ax.scatter(self.measurements.Q2, self.measurements.xpred, color='blue', label='X Fit')
        ax.errorbar(self.measurements.Q2, self.measurements.xrms_mean,
                    yerr=self.measurements.xrms_std, fmt='none', color='blue', capsize=5, label='X Data')
        
        ax.scatter(self.measurements.Q2, self.measurements.ypred, color='red', label='Y Fit')
        ax.errorbar(self.measurements.Q2, self.measurements.yrms_mean,
                    yerr=self.measurements.yrms_std, fmt='none', color='red', capsize=5, label='Y Data')
        
        ax.legend()
        return fig, ax
    
class QuadOptimizer():
    def __init__(self, beamline, beam_matrix):
        self.beamline = beamline
        self.beam_matrix = beam_matrix
        return
    
    def error_function(self, Is):

        error = 0
        self.beamline.updateCurrents(Is)
        full_matrix = self.beamline.matrices[-1]

        beam_final = full_matrix.dot(self.beam_matrix.dot(full_matrix.T))

        # Error handle when 0,0 element is negative
        xpred = np.sqrt(beam_final[0,0])*1e6 if beam_final[0,0]>0 else 2000
        ypred = np.sqrt(beam_final[2,2])*1e6 if beam_final[2,2]>0 else 2000

        error = xpred**2 + ypred**2
        return error
    
    def run(self, x0 = [3, -3, 3, 0, 0], bounds = [(-2, 10), (-10,2), (-2, 10), (-2, 10), (-10, 2)]):
        self.result = minimize(self.error_function, x0, method='L-BFGS-B', bounds=bounds)
        self.plot_results()
        return
    
    def plot_results(self):
        currents = self.result.x

        print('---- Final Error-----')
        print(f'{self.result.fun:.6}')
        print('----Quad Currents----')
        for j, current in enumerate(currents):
            print(f'Q{j} = {current:.2f}A')

        self.beamline.updateCurrents(currents)
        zs, xs, ys = self.beamline.computeSpotsizes(self.beam_matrix)

        plt.plot(zs, xs, label='Xrms')
        plt.plot(zs, ys, label='Yrms')
        plt.legend()
        return

            