"""
================================================================================
  IMPULSE-RESPONSE & FIGURE DRIVER
================================================================================
  Imports the solver from model.py and reproduces every IRF / figure in the paper.
  Organized in independent BLOCKS; flip the RUN_* switches to choose what executes.

  Quick single-model run:  set MODEL = 1, 2, or 3 below and run this file; it
  prints that model's response to the regulatory shock.  The figure blocks (A-D)
  call models 1/2/3 as each experiment requires.

      Model 1 : flexible-price asset-pricing block
      Model 2 : NK, passive money / active fiscal      (baseline)
      Model 3 : NK, active money / passive fiscal
================================================================================
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from model import calibrate, steady, build, gensys, irf, solve, ix, SH

# -------------------------------- CONFIG -------------------------------------
H        = 40          # IRF horizon (quarters)
SHOCKPCT = 0.10        # experiment size: a 10% tightening of the mandate
OUTDIR   = "."         # directory for PNG output

MODEL    = 2           # single-model quick run (1/2/3); set None to skip

RUN_A = True           # Block A: headline IRF + flexible overlay
RUN_B = True           # Block B: fiscal space
RUN_C = True           # Block C: regime comparison (II vs III) + determinacy
RUN_D = True           # Block D: robustness sweeps

C2, C3, CF = '#1f4e79', '#c0392b', '#c0392b'   # colors: NK / active / flexible
def _ax(ax, title):
    ax.set_title(title, fontsize=10, fontweight='bold')
    ax.axhline(0, color='gray', lw=.6); ax.grid(alpha=.25)
    ax.set_xlabel('quarters', fontsize=8); ax.tick_params(labelsize=8)
hh = np.arange(H + 1)
p  = calibrate()


# =============================================================================
#  QUICK SINGLE-MODEL RUN   (driven by the MODEL toggle)
# =============================================================================
if MODEL is not None:
    T1, T0, eu, em = solve(p, model=MODEL)
    R = irf(T1, T0, 'e_lam', H) * SHOCKPCT
    P = np.cumsum(R[ix['pi'], :])
    print(f"--- Model {MODEL}: lambda shock ({int(SHOCKPCT*100)}% tightening) ---")
    print(f"    eu={eu}   pi_0={R[ix['pi'],0]*100:+.3f}%   P_inf={P[-1]*100:+.3f}%"
          f"   QL_0={R[ix['QL'],0]*100:+.2f}%   v_0={R[ix['v'],0]*100:+.2f}%")


# =============================================================================
#  BLOCK A -- HEADLINE IRF (Model 2) WITH FLEXIBLE-PRICE OVERLAY (Model 1)
#  Figure: irf_lambda.png
# =============================================================================
if RUN_A:
    T1, T0, _, _   = solve(p, model=2)     # New Keynesian (sticky)
    T1f, T0f, _, _ = solve(p, model=1)     # flexible-price limit
    R  = irf(T1,  T0,  'e_lam', H) * SHOCKPCT
    Rf = irf(T1f, T0f, 'e_lam', H) * SHOCKPCT
    P, Pf = np.cumsum(R[ix['pi'],:]), np.cumsum(Rf[ix['pi'],:])
    Rv = steady(p)['Rv']
    rentcontrib = Rv * R[ix['R'], :]       # (R/v) * Rhat : contribution to backing
    pc = lambda x: x * 100

    fig, ax = plt.subplots(2, 3, figsize=(13, 7))
    ax[0,0].plot(hh, pc(R[ix['pi'],:]),  C2, lw=2,   label='New Keynesian')
    ax[0,0].plot(hh, pc(Rf[ix['pi'],:]), CF, lw=1.6, ls='--', label='flexible prices')
    ax[0,0].legend(fontsize=8); _ax(ax[0,0], r'Inflation  $\hat\pi$  (%)')
    ax[0,1].plot(hh, pc(P),  C2, lw=2,   label='New Keynesian')
    ax[0,1].plot(hh, pc(Pf), CF, lw=1.6, ls='--', label='flexible prices')
    ax[0,1].legend(fontsize=8); _ax(ax[0,1], r'Price level  $\hat P$  (cumulated, %)')
    ax[0,2].plot(hh, pc(R[ix['QL'],:]), C2, lw=2);  _ax(ax[0,2], r'Long-bond price  $\hat Q^L$  (%)')
    ax[1,0].plot(hh, pc(rentcontrib),   C2, lw=2);  _ax(ax[1,0], r'Rent contribution $(R/v)\hat R$  (% of debt)')
    ax[1,1].plot(hh, pc(R[ix['v'],:]),  C2, lw=2);  _ax(ax[1,1], r'Real debt value  $\hat v$  (%)')
    ax[1,2].plot(hh, pc(R[ix['c'],:]),  C2, lw=2,   label='New Keynesian')
    ax[1,2].plot(hh, pc(Rf[ix['c'],:]), CF, lw=1.6, ls='--', label='flexible prices')
    ax[1,2].legend(fontsize=8); _ax(ax[1,2], r'Consumption  $\hat c$  (%)')
    fig.suptitle(f'Impulse responses to a {int(SHOCKPCT*100)}% tightening of the mandate'
                 r'  ($\rho_\lambda=0.9$)', fontsize=12, fontweight='bold', y=1.0)
    plt.tight_layout(); plt.savefig(f'{OUTDIR}/irf_lambda.png', dpi=140, bbox_inches='tight'); plt.close()
    print(f"[A] irf_lambda.png  |  pi_0={pc(R[ix['pi'],0]):+.3f}%  P_inf={pc(P[-1]):+.3f}%"
          f"  (impact {P[0]/P[-1]*100:.0f}% of long run)  c_0(NK)={pc(R[ix['c'],0]):+.3f}%"
          f"  c_0(flex)={pc(Rf[ix['c'],0]):+.3f}%")


# =============================================================================
#  BLOCK B -- FISCAL SPACE
#  PV of additional rents from a PERMANENT tightening, as a share of debt.
#  Figure: fiscal_space.png
# =============================================================================
if RUN_B:
    b = p['beta']
    xt = np.linspace(0, 50, 100)                       # % permanent tightening of the mandate
    fig, axf = plt.subplots(figsize=(7.2, 5))
    for om, col, lab in [(0.12,'#7fb3d5','$\\omega=0.12$'),
                         (0.14,'#1f4e79','$\\omega=0.14$ (headline)'),
                         (0.21,'#154360','$\\omega=0.21$')]:
        pp = calibrate(); pp['omega'] = om; s2 = steady(pp)
        lam_ss = pp['wL'] / pp['Vbar']                 # steady-state lambda (Q^L b^L = lambda Vbar)
        dR    = s2['nu'] * pp['Vbar'] * (xt/100) * lam_ss   # extra per-period rent
        space = dR / (1 - b) / s2['v'] * 100           # PV of rents, % of debt
        axf.plot(xt, space, color=col, lw=2.2, label=lab)
    # annotate headline 10% point
    s2 = steady(p); sp10 = s2['nu'] * (0.10 * p['wL']) / (1-b) / s2['v'] * 100
    axf.plot(10, sp10, 'o', color='#1f4e79', ms=7)
    axf.annotate(f'10% tightening\n$\\to$ {sp10:.1f}% of debt', xy=(10, sp10),
                 xytext=(15, sp10+0.4), fontsize=9, arrowprops=dict(arrowstyle='->', color='#1f4e79'))
    axf.axhline(0, color='gray', lw=.6); axf.grid(alpha=.25)
    axf.set_xlabel(r'Permanent tightening $\Delta\lambda/\lambda$  (%)', fontsize=10)
    axf.set_ylabel('Fiscal space created  (PV of rents, % of debt)', fontsize=10)
    axf.set_title('Repression buys fiscal space', fontsize=11, fontweight='bold')
    axf.legend(fontsize=9, loc='upper left')
    plt.tight_layout(); plt.savefig(f'{OUTDIR}/fiscal_space.png', dpi=140, bbox_inches='tight'); plt.close()
    print(f"[B] fiscal_space.png  |  10% tightening -> {sp10:.2f}% of debt")


# =============================================================================
#  BLOCK C -- POLICY REGIME: Model 2 vs Model 3, AND the AM/AF non-existence cell
#  Figures: regime_irf.png, determinacy_boundary.png
# =============================================================================
if RUN_C:
    # --- determinacy across the three configurations ---
    def roots(T_em): return np.round(np.sort(T_em[T_em > 1.0+1e-6])[::-1], 3)
    _,_,euII,emII   = solve(p, model=2)                          # PM/AF (baseline)
    pAM = calibrate(); pAM['phi_pi'] = 1.5
    _,_,euAF,emAF   = gensys(*build(pAM, model=2))               # AM/AF (active money + exog surplus)
    _,_,euIII,emIII = solve(p, model=3)                          # AM/PF (fiscal rule)
    print("[C] determinacy:")
    print(f"     Model II  (PM/AF) eu={euII}  explosive={roots(emII)}")
    print(f"     AM/AF             eu={euAF}  explosive={roots(emAF)}   <- {'NO SOLUTION' if euAF!=[1,1] else 'det'}")
    print(f"     Model III (AM/PF) eu={euIII} explosive={roots(emIII)}")

    # --- IRF comparison: same shock, Model 2 vs Model 3 ---
    T1_II , T0_II , _, _ = solve(p, model=2)
    T1_III, T0_III, _, _ = solve(p, model=3)
    RII , RIII = irf(T1_II,T0_II,'e_lam',H)*SHOCKPCT, irf(T1_III,T0_III,'e_lam',H)*SHOCKPCT
    PII , PIII = np.cumsum(RII[ix['pi'],:]), np.cumsum(RIII[ix['pi'],:])
    print(f"     Model III max|pi| over horizon = {np.max(np.abs(RIII[ix['pi'],:]))*100:.2e}%  (machine zero)")
    fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.2))
    for a, (yII, yIII, t) in zip(ax, [
            (RII[ix['pi'],:]*100, RIII[ix['pi'],:]*100, r'Inflation  $\hat\pi$  (%)'),
            (PII*100,             PIII*100,             r'Price level  $\hat P$  (%)'),
            (RII[ix['QL'],:]*100, RIII[ix['QL'],:]*100, r'Long-bond price  $\hat Q^L$  (%)')]):
        a.plot(hh, yII,  C2, lw=2.2, label='Model II (passive money)')
        a.plot(hh, yIII, C3, lw=2.2, ls='--', label='Model III (active money)')
        a.legend(fontsize=8); _ax(a, t)
    fig.suptitle('Same regulatory shock, two regimes: the price-level effect vanishes under active money',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout(); plt.savefig(f'{OUTDIR}/regime_irf.png', dpi=140, bbox_inches='tight'); plt.close()

    # --- determinacy boundary: explosive count vs phi_pi (active fiscal) ---
    phis = np.linspace(0, 1.6, 65); nexp = []
    for ph in phis:
        pp = calibrate(); pp['phi_pi'] = ph
        _,_,_,em = gensys(*build(pp, model=2))
        nexp.append(int(np.sum(em > 1.0+1e-6)))
    fig, axb = plt.subplots(figsize=(7.2, 4.6))
    axb.step(phis, nexp, where='mid', color='#1f4e79', lw=2)
    axb.axhline(4, color='green', ls=':', lw=1.5, label='jumps = 4 (determinacy)')
    axb.axvline(1.0, color='gray', ls='--', lw=1.2, label=r'Taylor principle $\phi_\pi=1$')
    axb.set_xlabel(r'Taylor coefficient $\phi_\pi$', fontsize=10)
    axb.set_ylabel('explosive eigenvalues', fontsize=10); axb.set_ylim(2.5, 6.5)
    axb.set_title('Determinacy boundary under active fiscal', fontsize=11, fontweight='bold')
    axb.legend(fontsize=8.5); axb.grid(alpha=.25)
    plt.tight_layout(); plt.savefig(f'{OUTDIR}/determinacy_boundary.png', dpi=140, bbox_inches='tight'); plt.close()
    print("[C] regime_irf.png, determinacy_boundary.png written")


# =============================================================================
#  BLOCK D -- ROBUSTNESS SWEEPS  (Model 2)
#  Figures: robustness_sweeps.png, robustness_phipi.png
# =============================================================================
if RUN_D:
    def sweep_pi(**over):
        pp = calibrate(); pp.update(over)
        T1, T0, eu, _ = gensys(*build(pp, model=2))
        return irf(T1, T0, 'e_lam', H)[ix['pi'], :] * SHOCKPCT * 100, eu

    sweeps = {'theta':[0.50,0.75,0.85], 'delta':[0.980,0.990,0.998],
              'sigma':[0.50,1.00,2.00], 'rho':[0.70,0.85,0.95],
              'sg':[0.30,0.40,0.45],    'phi_pi':[0.00,0.50,0.95]}
    labels = {'theta':r'Calvo $\theta$','delta':r'duration $\delta$','sigma':r'risk aversion $\sigma$',
              'rho':r'persistence $\rho_\lambda$','sg':r'gov.\ share $s_g$','phi_pi':r'Taylor $\phi_\pi$'}
    cols = ['#7fb3d5','#1f4e79','#c0392b']
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.2))
    for ax, k in zip(axes.flat, sweeps):
        for val, c in zip(sweeps[k], cols):
            pth, eu = sweep_pi(**{k: val})
            ax.plot(hh, pth, color=c, lw=2, label=f'{val}')
        ax.set_ylabel(r'$\hat\pi$ (%)', fontsize=8); ax.legend(fontsize=7.5, title=labels[k])
        _ax(ax, labels[k])
    fig.suptitle('Robustness: inflation response under parameter sweeps',
                 fontsize=12, fontweight='bold', y=1.0)
    plt.tight_layout(); plt.savefig(f'{OUTDIR}/robustness_sweeps.png', dpi=140, bbox_inches='tight'); plt.close()

    # non-monotone sensitivity to phi_pi over the passive range
    phs = np.linspace(0, 0.98, 40); pic = [abs(sweep_pi(phi_pi=ph)[0][0]) for ph in phs]
    imax = int(np.argmax(pic))
    fig, ax2 = plt.subplots(figsize=(7, 4.6))
    ax2.plot(phs, pic, color='#1f4e79', lw=2.4)
    ax2.plot(phs[imax], pic[imax], 'o', color='#c0392b', ms=7)
    ax2.annotate(f'peak near $\\phi_\\pi$={phs[imax]:.2f}', xy=(phs[imax], pic[imax]),
                 xytext=(phs[imax]+0.1, pic[imax]), fontsize=9,
                 arrowprops=dict(arrowstyle='->', color='#c0392b'))
    ax2.set_xlabel(r'Taylor coefficient $\phi_\pi$ (passive range)', fontsize=10)
    ax2.set_ylabel(r'impact $|\hat\pi_0|$ (%)', fontsize=10)
    ax2.set_title('Non-monotone sensitivity to $\\phi_\\pi$', fontsize=11, fontweight='bold'); ax2.grid(alpha=.25)
    plt.tight_layout(); plt.savefig(f'{OUTDIR}/robustness_phipi.png', dpi=140, bbox_inches='tight'); plt.close()

    # determinacy check across all sweeps
    alldet = all(sweep_pi(**{k:v})[1] == [1,1] for k in sweeps for v in sweeps[k])
    print(f"[D] robustness_sweeps.png, robustness_phipi.png written  |  all sweeps determinate: {alldet}")

print("\nDONE.")
