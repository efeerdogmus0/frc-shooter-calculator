"""
FRC Shooter Physics Simulation Module

This module handles all physics calculations for projectile motion,
including ideal (no air resistance) and realistic (with drag/lift) trajectories.
"""
import numpy as np
import math as m

# =============================================================================
# FIELD DIMENSIONS (FRC 2022 Rapid React)
# All measurements converted from inches to meters: inches * 2.54 / 100
# =============================================================================
L_x = 158.611 * 2.54 / 100   # Field length (X-axis) in meters (~4.03m)
L_y = 318.188 * 2.54 / 100   # Field width (Y-axis) in meters (~8.08m)
W_H = 60 * 2.54 / 100        # Hub width in meters (~1.52m)
H_H = 60 * 2.54 / 100        # Hub base height in meters (~1.52m)
H_H2 = 13.5 * 2.54 / 100     # Hub upper rim height in meters (~0.34m)
H_W = 20 * 2.54 / 100        # Field wall height in meters (~0.51m)
R_1 = 25 / 2 * 2.54 / 100    # Hub inner ring radius in meters (~0.32m)
R_2 = 45 / 2 * 2.54 / 100    # Hub outer ring radius in meters (~0.57m)
H_Shoot = 0.1                # Target zone height tolerance in meters

# =============================================================================
# PHYSICS CONSTANTS
# =============================================================================
R_w = 2 * 2.54 / 100         # Flywheel radius in meters (~5.08cm)
R_b = 0.15 / 2               # Ball radius in meters (7.5cm for cargo ball)
g = 9.81                     # Gravitational acceleration (m/s²)
m_ball = 0.225               # Ball mass in kg
A = m.pi * R_b ** 2          # Ball cross-sectional area (m²)
p = 1.2                      # Air density (kg/m³) at sea level

# =============================================================================
# SIMULATION PARAMETERS
# =============================================================================
duration = 2                 # Simulation duration in seconds
n_steps = 500                # Number of simulation steps
dt = duration / n_steps      # Time step (seconds)
time = np.linspace(0, duration, n_steps)  # Time array


def f_drag(v, C_D):
    F_D = 0.5 * C_D * p * A * v**2
    return F_D / m_ball

def f_lift(v, C_L, w_b):
    F_L = 0.5 * p * A * R_b * w_b * v * C_L
    return F_L / m_ball

def calculate_simulation(params):
    """
    params: dict containing:
      P_x, P_y, O_r (rad), w, O_b (rad), Z_sh, C_D, C_L, C_roll
    """
    P_x = params['P_x']
    P_y = params['P_y']
    O_r = params['O_r']
    w = params['w']
    O_b = params['O_b']
    Z_sh = params['Z_sh']
    C_D = params['C_D']
    C_L = params['C_L']
    C_roll = params['C_roll']

    # Initial conditions
    V_s = (w / 60) * 2 * m.pi * R_w
    V_b0 = V_s * C_roll
    w_b = V_s / R_b * (1 - C_roll)
    V_u0 = V_b0 * m.cos(O_b)
    V_n0 = V_b0 * m.sin(O_b)

    # --- Ideal Calculations ---
    iN_vals = []
    iU_vals = []
    ideal_point = None

    for t in time:
        # Vertical (N)
        iV_n = V_n0 - g * t
        iN_val = Z_sh + V_n0 * t - 0.5 * g * t**2 # simplified integration
        if iN_val < 0:
            iN_val = 0
        
        # Horizontal (U)
        iU_val = V_u0 * t

        iN_vals.append(iN_val)
        iU_vals.append(iU_val)

        if abs(iN_val - (H_H + H_H2 + H_Shoot)) < 0.01:
            ideal_point = [iU_val, iN_val, t]

    iPoints = [iU_vals, iN_vals, time]

    # --- Friction Calculations ---
    N_vals = []
    U_vals = []
    V_u = V_u0
    V_n = V_n0
    N = Z_sh
    U = 0
    frIdealPoint = None

    for t in time:
        V = m.sqrt(V_u**2 + V_n**2)
        if V == 0:
            a_drag = 0
            a_lift = 0
            theta = 0
        else:
            a_drag = -1 * f_drag(V, C_D)
            a_lift = f_lift(V, C_L, w_b)
            theta = m.atan2(V_n, V_u)

        V_u = V_u + dt * (m.cos(theta) * a_drag + m.cos(theta + m.pi/2) * a_lift)
        V_n = V_n + dt * (m.sin(theta) * a_drag + m.sin(theta + m.pi/2) * a_lift - g)

        U = U + V_u * dt
        N = N + V_n * dt

        if N < 0:
            N = 0

        N_vals.append(N)
        U_vals.append(U)

        if abs(N - (H_H + H_H2 + H_Shoot)) < 0.01:
            frIdealPoint = [U, N, t]

    frPoints = [U_vals, N_vals, time]

    # Convert to 3D coords
    iPoints_xyz = calculate_XYZ_fromPoints(iPoints, P_x, P_y, O_r)
    frPoints_xyz = calculate_XYZ_fromPoints(frPoints, P_x, P_y, O_r)

    return (iPoints, ideal_point, frPoints, frIdealPoint, iPoints_xyz, frPoints_xyz)

def calculate_XYZ_fromPoints(points, P_x, P_y, O_r):
    X_vals = []
    Y_vals = []
    Z_vals = []
    # points[0] is U, points[1] is N
    for i in range(len(points[0])):
        U = points[0][i]
        N = points[1][i]
        X = P_x + U * m.cos(O_r)
        Y = P_y + U * m.sin(O_r)
        Z = N
        X_vals.append(X)
        Y_vals.append(Y)
        Z_vals.append(Z)

    points_xyz = [X_vals, Y_vals, Z_vals, points[2]]
    return points_xyz


# =============================================================================
# OPTIMAL ANGLE CALCULATOR
# =============================================================================

def calculate_optimal_angle(params, target_distance):
    """
    Calculate the optimal launch angle to hit a target at a given distance.
    
    Uses binary search to find the angle that lands the ball closest to
    the target height (H_H + H_H2) at the specified horizontal distance.
    
    Args:
        params: dict with shooter parameters (w, Z_sh, C_D, C_L, C_roll)
        target_distance: horizontal distance to target in meters
        
    Returns:
        dict with:
            - optimal_angle_deg: best angle in degrees
            - landing_height: height at target distance
            - error: distance from ideal target height
            - velocity_at_target: ball velocity at impact
            - flight_time: time to reach target
            - success: True if ball can reach target height
    """
    target_height = H_H + H_H2 + H_Shoot
    best_angle = None
    best_error = float('inf')
    best_result = None
    
    # Search angles from 20° to 75° with 0.5° precision
    for angle_deg in np.arange(20, 76, 0.5):
        angle_rad = m.radians(angle_deg)
        
        # Simulate with this angle
        test_params = params.copy()
        test_params['O_b'] = angle_rad
        
        result = simulate_to_distance(test_params, target_distance)
        
        if result is None:
            continue
            
        error = abs(result['height'] - target_height)
        
        if error < best_error:
            best_error = error
            best_angle = angle_deg
            best_result = result
    
    if best_angle is None:
        return {
            'optimal_angle_deg': 45,  # Default fallback
            'landing_height': 0,
            'error': float('inf'),
            'velocity_at_target': 0,
            'flight_time': 0,
            'success': False,
            'message': 'Could not find valid trajectory'
        }
    
    success = best_error < 0.15  # Within 15cm of target
    
    return {
        'optimal_angle_deg': best_angle,
        'landing_height': best_result['height'],
        'error': best_error,
        'velocity_at_target': best_result['velocity'],
        'flight_time': best_result['time'],
        'success': success,
        'message': 'Optimal angle found!' if success else 'Target may not be reachable with current RPM'
    }


def simulate_to_distance(params, target_distance):
    """
    Simulate trajectory until ball reaches target horizontal distance.
    Returns height and velocity at that point, or None if unreachable.
    """
    w = params['w']
    O_b = params['O_b']
    Z_sh = params['Z_sh']
    C_D = params['C_D']
    C_L = params['C_L']
    C_roll = params['C_roll']
    
    # Initial conditions
    V_s = (w / 60) * 2 * m.pi * R_w
    V_b0 = V_s * C_roll
    w_b = V_s / R_b * (1 - C_roll)
    V_u = V_b0 * m.cos(O_b)
    V_n = V_b0 * m.sin(O_b)
    
    N = Z_sh  # Height
    U = 0     # Horizontal distance
    t = 0
    
    max_time = 3.0  # Maximum simulation time
    sim_dt = 0.002  # Fine time step for accuracy
    
    while t < max_time:
        V = m.sqrt(V_u**2 + V_n**2)
        
        if V == 0:
            break
            
        a_drag = -1 * f_drag(V, C_D)
        a_lift = f_lift(V, C_L, w_b)
        theta = m.atan2(V_n, V_u)
        
        V_u += sim_dt * (m.cos(theta) * a_drag + m.cos(theta + m.pi/2) * a_lift)
        V_n += sim_dt * (m.sin(theta) * a_drag + m.sin(theta + m.pi/2) * a_lift - g)
        
        U += V_u * sim_dt
        N += V_n * sim_dt
        t += sim_dt
        
        # Check if we've reached target distance
        if U >= target_distance:
            return {
                'height': N,
                'velocity': V,
                'time': t,
                'V_u': V_u,
                'V_n': V_n
            }
        
        # Ball hit ground
        if N < 0:
            return None
    
    return None


# =============================================================================
# IMPACT ZONE CALCULATION
# =============================================================================

def calculate_impact_zone(params, angle_variance_deg=2, rpm_variance_pct=3):
    """
    Calculate the impact zone considering parameter uncertainties.
    
    Simulates multiple trajectories with slight variations in angle and RPM
    to determine the probable landing zone.
    
    Args:
        params: base shooter parameters
        angle_variance_deg: ± degrees of angle uncertainty
        rpm_variance_pct: ± percentage of RPM uncertainty
        
    Returns:
        dict with:
            - center: (x, y, z) center of impact zone
            - radius: approximate radius of impact zone
            - points: list of (x, y, z) impact points
            - in_target: True if center is within hub target
            - target_probability: percentage of shots that would score
    """
    P_x = params['P_x']
    P_y = params['P_y']
    O_r = params['O_r']
    base_angle = params['O_b']
    base_rpm = params['w']
    
    impact_points = []
    
    # Generate variations
    angle_variations = np.linspace(-angle_variance_deg, angle_variance_deg, 5)
    rpm_variations = np.linspace(-rpm_variance_pct, rpm_variance_pct, 5)
    
    for angle_delta in angle_variations:
        for rpm_delta in rpm_variations:
            test_params = params.copy()
            test_params['O_b'] = base_angle + m.radians(angle_delta)
            test_params['w'] = base_rpm * (1 + rpm_delta / 100)
            
            impact = find_impact_point(test_params)
            
            if impact is not None:
                # Convert to 3D coordinates
                U, N = impact['U'], impact['N']
                X = P_x + U * m.cos(O_r)
                Y = P_y + U * m.sin(O_r)
                Z = N
                impact_points.append((X, Y, Z))
    
    if not impact_points:
        return {
            'center': (P_x, P_y, 0),
            'radius': 0,
            'points': [],
            'in_target': False,
            'target_probability': 0,
            'max_height': 0
        }
    
    # Calculate center
    x_vals = [p[0] for p in impact_points]
    y_vals = [p[1] for p in impact_points]
    z_vals = [p[2] for p in impact_points]
    
    center = (np.mean(x_vals), np.mean(y_vals), np.mean(z_vals))
    
    # Calculate radius (max distance from center)
    distances = [m.sqrt((p[0]-center[0])**2 + (p[1]-center[1])**2) for p in impact_points]
    radius = max(distances) if distances else 0
    
    # Check if in target zone (hub)
    hub_x = L_x + W_H / 2
    hub_y = L_y / 2
    target_height = H_H + H_H2
    
    # Count shots that would score
    scoring_shots = 0
    for point in impact_points:
        dist_to_hub = m.sqrt((point[0] - hub_x)**2 + (point[1] - hub_y)**2)
        height_ok = abs(point[2] - target_height) < 0.3  # Within 30cm of target height
        position_ok = dist_to_hub < R_2  # Within outer ring
        if height_ok and position_ok:
            scoring_shots += 1
    
    target_probability = (scoring_shots / len(impact_points)) * 100 if impact_points else 0
    
    # Center in target check
    center_dist = m.sqrt((center[0] - hub_x)**2 + (center[1] - hub_y)**2)
    in_target = center_dist < R_2 and abs(center[2] - target_height) < 0.3
    
    return {
        'center': center,
        'radius': radius,
        'points': impact_points,
        'in_target': in_target,
        'target_probability': target_probability,
        'max_height': max(z_vals) if z_vals else 0
    }


def find_impact_point(params):
    """
    Find where the ball crosses the target height (H_H + H_H2).
    Returns the U (horizontal) and N (vertical) coordinates.
    """
    w = params['w']
    O_b = params['O_b']
    Z_sh = params['Z_sh']
    C_D = params['C_D']
    C_L = params['C_L']
    C_roll = params['C_roll']
    
    target_height = H_H + H_H2 + H_Shoot
    
    # Initial conditions
    V_s = (w / 60) * 2 * m.pi * R_w
    V_b0 = V_s * C_roll
    w_b = V_s / R_b * (1 - C_roll)
    V_u = V_b0 * m.cos(O_b)
    V_n = V_b0 * m.sin(O_b)
    
    N = Z_sh
    U = 0
    prev_N = N
    prev_U = U
    t = 0
    passed_peak = False
    
    max_time = 3.0
    sim_dt = 0.002
    
    while t < max_time:
        V = m.sqrt(V_u**2 + V_n**2)
        
        if V == 0:
            break
            
        a_drag = -1 * f_drag(V, C_D)
        a_lift = f_lift(V, C_L, w_b)
        theta = m.atan2(V_n, V_u)
        
        V_u += sim_dt * (m.cos(theta) * a_drag + m.cos(theta + m.pi/2) * a_lift)
        V_n += sim_dt * (m.sin(theta) * a_drag + m.sin(theta + m.pi/2) * a_lift - g)
        
        prev_U = U
        prev_N = N
        U += V_u * sim_dt
        N += V_n * sim_dt
        t += sim_dt
        
        # Detect peak (when vertical velocity changes sign)
        if V_n < 0:
            passed_peak = True
        
        # After peak, check if we cross target height
        if passed_peak and prev_N >= target_height >= N:
            # Linear interpolation for more accuracy
            ratio = (target_height - N) / (prev_N - N) if (prev_N - N) != 0 else 0
            impact_U = U - ratio * (U - prev_U)
            return {'U': impact_U, 'N': target_height, 'time': t}
        
        # Ball hit ground
        if N < 0:
            return {'U': U, 'N': 0, 'time': t}
    
    return None


def draw_impact_zone(ax3d, impact_zone, color='red', alpha=0.3):
    """
    Draw the impact zone on a 3D plot as a semi-transparent disc.
    """
    if not impact_zone['points']:
        return
        
    center = impact_zone['center']
    radius = max(impact_zone['radius'], 0.05)  # Minimum visible radius
    
    # Draw impact points as scatter
    x_vals = [p[0] for p in impact_zone['points']]
    y_vals = [p[1] for p in impact_zone['points']]
    z_vals = [p[2] for p in impact_zone['points']]
    ax3d.scatter(x_vals, y_vals, z_vals, c=color, alpha=0.6, s=20, label='Impact Zone')
    
    # Draw circle at average height
    theta_circle = np.linspace(0, 2 * np.pi, 50)
    x_circle = center[0] + radius * np.cos(theta_circle)
    y_circle = center[1] + radius * np.sin(theta_circle)
    z_circle = np.full_like(x_circle, center[2])
    ax3d.plot(x_circle, y_circle, z_circle, color=color, linewidth=2, alpha=0.8)
    
    # Draw center marker
    ax3d.scatter([center[0]], [center[1]], [center[2]], 
                 c='yellow', s=100, marker='*', edgecolors='black', linewidths=1,
                 label=f'Center ({impact_zone["target_probability"]:.0f}% accuracy)')


# --- Plotting Helpers ---

def plotIdeal2D(ax, iPoints, ideal_point):
    """Plot ideal trajectory (no air resistance) in 2D."""
    ax.plot(iPoints[0], iPoints[1], label='Ideal (no drag)')
    # Draw target height lines
    ax.axhline(H_H+H_H2, color='g', linestyle='--', alpha=0.7, label='Hub height')
    ax.axhline(H_H+H_H2+H_Shoot, color='g', linestyle='--', alpha=0.5)
    
    if ideal_point:
        ax.axvline(ideal_point[0], color='r', linestyle='--', label='Ideal Shot Point') 
        ax.text(
            ideal_point[0], 
            ax.get_ylim()[0], 
            f'x = {ideal_point[0]:.2f}', 
            rotation=90,
            verticalalignment='bottom',
            horizontalalignment='right',
            color='r'
        )   
        ax.axvline(ideal_point[0]+R_2*2, color='r', linestyle='--', label='End Of Hub')

def plotFriction2D(ax, frPoints, frIdealPoint):
    ax.plot(frPoints[0], frPoints[1], color='orange')
    if frIdealPoint:
        ax.axvline(frIdealPoint[0], color='m', linestyle='--', label='Fr Ideal Shot Point') 
        ax.text(
            frIdealPoint[0], 
            ax.get_ylim()[0],
            f'x = {frIdealPoint[0]:.2f}', 
            rotation=90,
            verticalalignment='bottom',
            horizontalalignment='right',
            color='m'
        )   
        ax.axvline(frIdealPoint[0]+R_2*2, color='m', linestyle='--', label='Fr End Of Hub')

def plotIdeal3D(ax3d, iPoints_xyz):
    ax3d.plot(iPoints_xyz[0], iPoints_xyz[1], iPoints_xyz[2], color='black', alpha=1)

def plotFriction3D(ax3d, frPoints_xyz):
    ax3d.plot(frPoints_xyz[0], frPoints_xyz[1], frPoints_xyz[2], color='green', alpha=1)

def draw_field(ax3d):
    draw_ground(ax3d)
    draw_field_walls(ax3d)
    draw_hub_post(ax3d)
    draw_hub(ax3d)

def draw_ground(ax3d):
    X = np.array([[0, L_x], [0, L_x]])
    Y = np.array([[0, 0], [L_y, L_y]])
    Z = np.zeros_like(X)
    ax3d.plot_surface(X, Y, Z, color='gray', alpha=0.4, shade=True)



def draw_field_walls(ax3d):
    X_1 = np.array([[0, L_x], [0, L_x]])
    Z_1 = np.array([[0, 0], [H_W, H_W]])
    Y_1 = np.full_like(X_1, 0)

    X_2 = np.array([[0, L_x], [0, L_x]])
    Z_2 = np.array([[0, 0], [H_W, H_W]])
    Y_2 = np.full_like(X_1, L_y)

    X_3 = np.full_like(X_1, 0)
    Z_3 = np.array([[0, H_W], [0, H_W]])
    Y_3 = np.array([[0, 0], [L_y, L_y]])

    ax3d.plot_surface(X_1, Y_1, Z_1, color='gray', alpha=0.4, shade=True)
    ax3d.plot_surface(X_2, Y_2, Z_2, color='gray', alpha=0.4, shade=True)
    ax3d.plot_surface(X_3, Y_3, Z_3, color='gray', alpha=0.4, shade=True)

def draw_hub_post(ax3d):
    # Using simplified lines for the hub post to save space but keep visual
    ax3d.plot([L_x, L_x], [(L_y-W_H)/2, (L_y-W_H)/2], [0, H_H], color='black')
    ax3d.plot([L_x, L_x], [(L_y+W_H)/2, (L_y+W_H)/2], [0, H_H], color='black')
    ax3d.plot([L_x+W_H, L_x+W_H], [(L_y-W_H)/2, (L_y-W_H)/2], [0, H_H], color='black')
    ax3d.plot([L_x+W_H, L_x+W_H], [(L_y+W_H)/2, (L_y+W_H)/2], [0, H_H], color='black')
    # Top box
    ax3d.plot([L_x, L_x+W_H], [(L_y-W_H)/2, (L_y-W_H)/2], [H_H, H_H], color='black')
    ax3d.plot([L_x, L_x+W_H], [(L_y+W_H)/2, (L_y+W_H)/2], [H_H, H_H], color='black')
    ax3d.plot([L_x, L_x], [(L_y-W_H)/2, (L_y+W_H)/2], [H_H, H_H], color='black')
    ax3d.plot([L_x+W_H, L_x+W_H], [(L_y-W_H)/2, (L_y+W_H)/2], [H_H, H_H], color='black')

def draw_hub(ax3d):
    x_c = L_x + W_H / 2
    y_c = L_y / 2
    theta = np.linspace(0, 2*np.pi, 200)
    z = np.linspace(H_H, H_H + H_H2, 100)
    Theta, Z = np.meshgrid(theta, z)
    R = (R_2 - R_1) / H_H2 * (Z - H_H) + R_1
    X = x_c + R * np.cos(Theta)
    Y = y_c + R * np.sin(Theta)
    ax3d.plot_surface(X, Y, Z, color='purple', alpha=0.3, linewidth=0, shade=True)


