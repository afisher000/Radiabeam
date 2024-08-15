import numpy as np
import matplotlib.pyplot as plt
from Utils import matrix_utils as mu


def parse_inputs(x):
    beta, alpha, emittance = x
    gamma = (1+alpha**2)/beta

    emittance = emittance*1e-7
    return beta, alpha, gamma, emittance

def print_results(x, energy, coord):
    rel_gamma = energy / 511000
    beta, alpha, gamma, emittance = parse_inputs(x)

    print(f'---------- {coord} ----------')
    print(f'Emittance: {emittance:.2e}')
    print(f'Norm. Emittance: {rel_gamma*emittance:.2e}')
    print(f'Beta Twiss: {beta:.2f}')
    print(f'Alpha Twiss: {alpha:.2f}')
    return

def errorfcn(x, measurements, energy, cam):
    beta, alpha, gamma, emittance = parse_inputs(x)

    beam_initial = emittance * np.array([
        [beta, -alpha],
        [-alpha, gamma]
    ])

    rigidity = energy / 299792458
    error = 0
    for _, meas in measurements.iterrows():
        full_matrix = mu.compute_transport_matrix(meas.Q1, meas.Q2, meas.Q3, rigidity, cam)
        beam_final = full_matrix.dot(beam_initial.dot(full_matrix.T))
        pred_spotsize = np.sqrt(beam_final[0,0])*1e6 if beam_final[0,0]>0 else 1000
        error += ((meas.spotsize_mean - pred_spotsize)/meas.spotsize_std)**2

    return error

def plot_fit_vs_data(x, measurements, energy, cam):
    beta, alpha, gamma, emittance = parse_inputs(x)

    beam_initial = emittance * np.array([
        [beta, -alpha],
        [-alpha, gamma]
    ])

    rigidity = energy / 299792458
    pred_spotsizes = []
    for _, meas in measurements.iterrows():
        full_matrix = mu.compute_transport_matrix(meas.Q1, meas.Q2, meas.Q3, rigidity, cam)
        beam_final = full_matrix.dot(beam_initial.dot(full_matrix.T))
        pred_spotsizes.append(np.sqrt(beam_final[0,0])*1e6)
    measurements['pred_spotsize'] = pred_spotsizes

    fig, ax = plt.subplots()
    ax.scatter(measurements.Q2, measurements.pred_spotsize, color='red', label='Simulation Fit')

    ax.errorbar(measurements.Q2, measurements.spotsize_mean,
                 yerr=measurements.spotsize_std, fmt='none', color='blue', capsize=5, label='Beam Data')
    ax.legend()
    return fig, ax