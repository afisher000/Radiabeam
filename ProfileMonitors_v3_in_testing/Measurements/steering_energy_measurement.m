function steering_energy_measurement(dx, dz, current)
%% Theory
% Circular motion: qe * c0 * B = gamma * me * c0^2 / R
% Arc length: L = R * theta  where  theta = dx/dz
% Solve for gamma where L*B = LBoverA * current

%% Calculation
% Steering Magnet calibration
LBoverA = 169*1e-4*1e-2; % Gauss*cm/A converted to Tesla*m/A

% Physical Constants
qe      = 1.602e-19;
me      = 9.109e-31;
c0      = 299792458;

% Angular deflection 
theta   = dx/dz;

% Output
gamma   = (qe/me/c0) * (LBoverA) * current/theta;
fprintf('Energy = %.1f MeV\n', gamma*.511)

end
