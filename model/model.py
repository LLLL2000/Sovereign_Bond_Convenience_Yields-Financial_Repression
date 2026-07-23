"""
================================================================================
  A Captive-Intermediary Model of Financial Repression and Sovereign Duration
  Pricing  --  SOLVER CORE
================================================================================

  This module builds the log-linearized equilibrium in the canonical form of
  Sims (2002),

        G0 . y_t  =  G1 . y_{t-1}  +  PSI . eps_t  +  PI . eta_t ,

  and solves it with an ordered generalized-Schur (QZ) decomposition ("gensys").
  The output is a linear policy function  y_t = THETA1 . y_{t-1} + THETA0 . eps_t .

  THREE MODEL VARIANTS  (argument `model` of build()):
      model = 1 : flexible-price asset-pricing block   (no rigidity; theta -> 0)
      model = 2 : New Keynesian, PASSIVE money / ACTIVE fiscal      (BASELINE)
      model = 3 : New Keynesian, ACTIVE money / PASSIVE fiscal      (+ fiscal rule)

  CONVENTIONS
  -----------
  * One period = one quarter.
  * Hatted variables are log-deviations from steady state, EXCEPT pi, i (net
    rates) and omega, nu (small levels), which are LEVEL deviations.
  * Stacked vector y_t has 22 entries:
        14 endogenous + 4 exogenous AR(1) + 4 expectation variables.
  * Row comments tag each equation with its label (L1..L14) from the model
    section's log-linearized system, so the matrices can be audited line by line.
================================================================================
"""

import numpy as np
from scipy.linalg import ordqz


# =============================================================================
# 1.  CALIBRATION   (data-disciplined UK calibration, June 2026)
# =============================================================================
def calibrate():
    """Baseline parameters. See the calibration section for sources."""
    return dict(
        # ---- Tier 1 : convention (literature) ----
        beta   = 0.99,    # discount factor (~1% quarterly real rate)
        sigma  = 1.0,     # inverse IES / CRRA (log utility)
        theta  = 0.75,    # Calvo non-reset prob. (1-yr price duration)
        varphi = 0.0,     # inverse Frisch (no hours margin; -> mc = sigma*c)

        # ---- Tier 2 : data-disciplined (UK) ----
        delta  = 0.998,   # long-bond decay; Macaulay D=1/(1-beta*delta/pi_bar) ~ 15 yr
        wL     = 0.353,   # long share of debt by MARKET VALUE (DMO)
        sg     = 0.40,    # govt purchases / output (UK current expenditure ~40% GDP)
        pi_bar = 1.005,   # gross quarterly trend = (1.02)^(1/4); BoE 2%/yr target
        omega  = 0.14,    # MEASURED wedge (return differential on captive gilts)

        # ---- Tier 4 : regime / persistence / normalization ----
        phi_pi = 0.5,     # Taylor coefficient ( <1 passive [II] ; >1 active [III] )
        rho    = 0.90,    # lambda-shock persistence (only one entering headline IRF)
        Vbar   = 1.0,     # captive liability pool (scale normalization)
        gamma_v= 0.10,    # fiscal-feedback coefficient (Model III only)
    )

# Flexible-price limit: Model I uses a tiny Calvo parameter so the Phillips curve
# is (nearly) vertical and the real allocation sits at its natural level.
THETA_FLEX  = 0.02
# Active-money Taylor coefficient used by Model III.
PHI_ACTIVE  = 1.5


# =============================================================================
# 2.  DETERMINISTIC STEADY STATE   (Tier 3 -- solved, not chosen)
# =============================================================================
def steady(p):
    """Return a dict of steady-state objects implied by the parameters."""
    b, s, th, d = p['beta'], p['sigma'], p['theta'], p['delta']
    pi, om, wL  = p['pi_bar'], p['omega'], p['wL']

    QS  = b / pi                       # short price            Q^S = beta/pi_bar
    QLf = b / (pi - b*d)               # fundamental long price  beta/(pi - beta*delta)
    QL  = (1 + om) * QLf               # observed long price     (1+omega) Q^{L,f}
    nu  = (pi - b*d)/pi * om/(1 + om)  # multiplier (perpetuity-corrected shadow price)
    eta_f = b*d / pi                   # duration coef. (fundamental)  = beta*delta/pi_bar
    eta   = d*QL / (1 + d*QL)          # duration coef. (observed)
    kap   = (1-th)*(1 - b*th)/th       # NKPC slope

    # quantities: normalize total market value to 1, long market-value share wL
    bL = wL / QL
    bS = (1 - wL) / QS
    v  = bS + (1 + d*QL)*bL            # inherited real debt value
    wSv = bS / v                       # short value share
    wLv = (1 + d*QL)*bL / v            # long  value share
    R   = nu * QL * bL                 # per-period rent
    Rv  = R / v
    return dict(QS=QS, QLf=QLf, QL=QL, nu=nu, eta_f=eta_f, eta=eta, kap=kap,
                bL=bL, bS=bS, v=v, wSv=wSv, wLv=wLv, R=R, Rv=Rv)


# =============================================================================
# 3.  STACKED VECTOR, SHOCKS, FORECAST ERRORS
# =============================================================================
#   14 endogenous, 4 exogenous AR(1), 4 expectation variables  ->  22 total.
V = ['c','y','pi','i','QS','QL','QLf','om','nu','R','v','bS','bL','s',  # endogenous (14)
     'lam','g','ds','ui',                                              # exogenous  (4)
     'fc','fpi','fQL','fQLf']                                          # expectations (4)
ix = {n: j for j, n in enumerate(V)}
N  = len(V)

SH = {'e_lam': 0, 'e_g': 1, 'e_ds': 2, 'e_ui': 3}   # structural innovations -> PSI columns
ET = {'c': 0, 'pi': 1, 'QL': 2, 'QLf': 3}           # forecast errors        -> PI  columns


# =============================================================================
# 4.  SYSTEM BUILDER   ->  (G0, G1, PSI, PI)
# =============================================================================
def build(p, model=2):
    """
    Assemble the canonical-form matrices for the chosen model.

      model 1 : flexible prices  (theta -> THETA_FLEX)             [passive money]
      model 2 : NK passive money (phi_pi as calibrated, <1)        [BASELINE]
      model 3 : NK active money  (phi_pi = PHI_ACTIVE, >1) plus a
                debt-stabilizing fiscal rule on the surplus row.

    Each structural row is tagged with its log-linearized label (L1..L14).
    """
    pp = dict(p)
    if model == 1:
        pp['theta']  = THETA_FLEX        # flexible-price limit
    if model == 3:
        pp['phi_pi'] = PHI_ACTIVE        # active monetary policy

    ss   = steady(pp)
    b    = pp['beta']; sig = pp['sigma']; sg = pp['sg']
    phi  = pp['phi_pi']; rho = pp['rho']; gv = pp['gamma_v']
    nu, eta, etaf, kap = ss['nu'], ss['eta'], ss['eta_f'], ss['kap']
    wSv, wLv, Rv, om   = ss['wSv'], ss['wLv'], ss['Rv'], pp['omega']

    G0  = np.zeros((N, N))     # coefficients on date-t variables
    G1  = np.zeros((N, N))     # coefficients on date-(t-1) variables
    PSI = np.zeros((N, 4))     # structural innovations
    PI  = np.zeros((N, 4))     # one-step-ahead forecast errors
    def g0(r, n, x): G0[r, ix[n]] = x
    def g1(r, n, x): G1[r, ix[n]] = x

    # --- L1  IS curve:  c = E c' - (1/sig)(i - E pi') --------------------------
    g0(0,'c',1); g0(0,'fc',-1); g0(0,'i',1/sig); g0(0,'fpi',-1/sig)
    # --- L2  NKPC (consumption form):  pi = beta E pi' + kappa*sig*c -----------
    g0(1,'pi',1); g0(1,'fpi',-b); g0(1,'c',-kap*sig)
    # --- L3  monetary policy:  i = phi_pi*pi + u^i -----------------------------
    g0(2,'i',1); g0(2,'pi',-phi); g0(2,'ui',-1)
    # --- (def) rate definition:  Q^S = -i --------------------------------------
    g0(3,'QS',1); g0(3,'i',1)
    # --- L4  fundamental price:  Q^{L,f} = -i + eta_f E Q^{L,f}' ----------------
    g0(4,'QLf',1); g0(4,'i',1); g0(4,'fQLf',-etaf)
    # --- L5  observed long Euler:
    #         Q^L = nu/(1-nu) - sig(E c' - c) - E pi' + eta E Q^L' ---------------
    for n,x in [('QL',1),('nu',-1/(1-nu)),('fc',sig),('c',-sig),('fpi',1),('fQL',-eta)]:
        g0(5,n,x)
    # --- L6  wedge:  omega = (1+omega)(Q^L - Q^{L,f}) --------------------------
    g0(6,'om',1); g0(6,'QL',-(1+om)); g0(6,'QLf',(1+om))
    # --- L7  binding coverage:  Q^L + b^L = lambda -----------------------------
    g0(7,'QL',1); g0(7,'bL',1); g0(7,'lam',-1)
    # --- L8  rent:  R = nu/nu_ss + Q^L + b^L  (coef on nu is 1/nu_ss) ----------
    g0(8,'R',1); g0(8,'nu',-1/nu); g0(8,'QL',-1); g0(8,'bL',-1)
    # --- L11 maturity rule:  b^L = b^S -----------------------------------------
    g0(9,'bL',1); g0(9,'bS',-1)
    # --- L12 resource constraint:  y = (1-sg) c + sg g -------------------------
    g0(10,'y',1); g0(10,'c',-(1-sg)); g0(10,'g',-sg)
    # --- L9  inherited-debt revaluation (STATE row; the only structural G1):
    #         v + pi - wLv*eta*Q^L = wSv b^S_{-1} + wLv b^L_{-1} ----------------
    g0(11,'v',1); g0(11,'pi',1); g0(11,'QL',-wLv*eta)
    g1(11,'bS',wSv); g1(11,'bL',wLv)
    # --- L10 valuation identity (no forecast error; v is a state):
    #         v = (s/v) s + (R/v) R + beta(wSv b^S + wLv b^L + wLv eta E Q^L') - beta i
    #     here 'ds' carries the surplus contribution (s/v)*shat
    for n,x in [('v',1),('ds',-1),('R',-Rv),('bS',-b*wSv),('bL',-b*wLv),
                ('fQL',-b*wLv*eta),('i',b)]:
        g0(12,n,x)
    # --- L14 surplus definition:  s = ds ---------------------------------------
    g0(13,'s',1); g0(13,'ds',-1)

    # --- exogenous AR(1) rows:  z_t = rho z_{t-1} + eps_z -----------------------
    for r, z in zip(range(14,18), ['lam','g','ds','ui']):
        g0(r, z, 1); g1(r, z, rho); PSI[r, r-14] = 1

    # --- forecast-error identities:  x_t = f^x_{t-1} + eta^x_t ------------------
    #     (the ONLY rows touching PI; one per jump variable)
    for r, (x, f) in zip(range(18,22),
                         [('c','fc'),('pi','fpi'),('QL','fQL'),('QLf','fQLf')]):
        g0(r, x, 1); g1(r, f, 1); PI[r, ET[x]] = 1

    # --- MODEL III: replace the exogenous surplus process by a debt-feedback
    #     rule  ds_t = gamma_v v_{t-1} + eps  (passive fiscal). Drop own persistence.
    if model == 3:
        G1[16, ix['ds']] = 0.0
        G1[16, ix['v']]  = gv

    return G0, G1, PSI, PI


# =============================================================================
# 5.  GENSYS SOLVER   (Sims 2002, determinate case)
# =============================================================================
def gensys(g0, g1, psi, pi, div=1.0):
    """
    Solve  g0 y_t = g1 y_{t-1} + psi eps_t + pi eta_t  for the bounded RE solution
        y_t = THETA1 y_{t-1} + THETA0 eps_t.

    Returns (THETA1, THETA0, eu, eigmod_desc) where
        eu = [existence, uniqueness]  (each 0/1),
        eigmod_desc = generalized-eigenvalue moduli, sorted descending.

    AUDIT NOTES
    -----------
    * scipy.linalg.ordqz factors the pencil so that
          g0 = Q AA Z^H ,  g1 = Q BB Z^H ,    (AA, BB upper triangular; Q,Z unitary)
      and reports the generalized eigenvalue as  w = alpha/beta = AA_ii / BB_ii.
    * The DYNAMIC eigenvalue governing stability of y_t = g0^{-1}g1 y_{t-1} is the
      RECIPROCAL,  mu = BB_ii / AA_ii.  A root is EXPLOSIVE iff |mu| > 1.
    * Therefore we sort with  sort='ouc'  (scipy's "outside unit circle" applies to
      w = 1/mu): this places the dynamically STABLE roots (|mu|<1) in the top-left
      block and the EXPLOSIVE roots (|mu|>1) in the bottom-right, as the partition
      below requires.  [Using 'iuc' here would invert the partition -- a classic
      gensys pitfall.]
    * Determinacy (Blanchard-Kahn): a unique bounded solution exists iff the number
      of explosive roots equals the number of forecast errors (here 4).
    """
    n = g0.shape[0]
    # complex QZ with stable roots sorted to the top-left  (see AUDIT NOTES)
    AA, BB, alpha, beta, Q, Z = ordqz(g0, g1, sort='ouc', output='complex')

    # dynamic eigenvalue moduli |mu| = |BB_ii| / |AA_ii|
    eigmod  = np.abs(beta) / np.abs(alpha)
    nunstab = int(np.sum(eigmod > div + 1e-9))   # number of explosive roots
    neta    = pi.shape[1]                         # number of forecast errors (=4)
    nstab   = n - nunstab

    # rotate the system:  partition Q^H psi and Q^H pi into stable / unstable rows
    Qh    = Q.conj().T
    qpsi  = Qh @ psi
    qpi   = Qh @ pi
    qpsi2, qpi2 = qpsi[nstab:, :], qpi[nstab:, :]   # unstable block
    qpsi1, qpi1 = qpsi[:nstab, :], qpi[:nstab, :]   # stable   block

    # Forecast errors are pinned by zeroing the explosive canonical variables:
    #     qpi2 . eta = -qpsi2 . eps   ->   eta = phi . eps
    if nunstab == neta:                  # determinate
        phi = -np.linalg.solve(qpi2, qpsi2); eu = [1, 1]
    elif nunstab < neta:                 # indeterminate (too few explosive roots)
        phi = -np.linalg.pinv(qpi2) @ qpsi2; eu = [1, 0]
    else:                                # no bounded solution (too many)
        phi = np.zeros((neta, psi.shape[1])); eu = [0, 0]

    # Stable block dynamics in rotated coordinates, then rotate back to y:
    #     w1_t = (a11^{-1} b11) w1_{t-1} + a11^{-1}(qpsi1 + qpi1 phi) eps_t
    #     y_t  = Z1 w1_t   (the unstable canonical block w2 is set to zero)
    a11, b11 = AA[:nstab, :nstab], BB[:nstab, :nstab]
    M11 = np.linalg.solve(a11, b11)
    Nn  = np.linalg.solve(a11, qpsi1 + qpi1 @ phi)
    Z1  = Z[:, :nstab]
    THETA1 = np.real(Z1 @ M11 @ Z1.conj().T)
    THETA0 = np.real(Z1 @ Nn)
    return THETA1, THETA0, eu, np.sort(eigmod)[::-1]


# =============================================================================
# 6.  IMPULSE RESPONSES
# =============================================================================
def irf(THETA1, THETA0, shock, H):
    """
    Impulse response to a unit innovation in `shock` (a key of SH), horizon H.
    Returns an (N x (H+1)) array of deviations; row j is variable V[j].

        y_0 = THETA0 e_shock ;   y_h = THETA1 y_{h-1}   (AR(1) persistence is
        already inside THETA1 via the shock's own state row).
    """
    out = np.zeros((N, H + 1))
    e = np.zeros(4); e[SH[shock]] = 1.0
    y = THETA0 @ e
    out[:, 0] = y
    for h in range(1, H + 1):
        y = THETA1 @ y
        out[:, h] = y
    return out


def solve(p=None, model=2):
    """Convenience wrapper: build + gensys for a given parameter set and model."""
    if p is None:
        p = calibrate()
    G0, G1, PSI, PI = build(p, model=model)
    return gensys(G0, G1, PSI, PI)


# =============================================================================
# 7.  SELF-TEST  (run `python model.py`)
# =============================================================================
if __name__ == "__main__":
    p = calibrate()
    for m, name in [(1,'I  flexible'), (2,'II passive money'), (3,'III active money')]:
        T1, T0, eu, em = solve(p, model=m)
        exp = np.round(np.sort(em[em > 1.0 + 1e-6])[::-1], 3)
        print(f"Model {name:18s}: eu={eu}  explosive roots={exp}")
    # headline lambda-shock impacts (Model II, 10% tightening)
    T1, T0, eu, em = solve(p, model=2)
    R = irf(T1, T0, 'e_lam', 40) * 0.10
    P = np.cumsum(R[ix['pi'], :])
    print("\nModel II, 10% mandate tightening:")
    for v in ['pi','QL','v','i','c']:
        print(f"   {v:4s}_0 = {R[ix[v],0]*100:+.3f}%")
    print(f"   P_inf  = {P[-1]*100:+.3f}%")
