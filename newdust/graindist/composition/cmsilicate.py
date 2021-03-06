import numpy as np
from scipy.interpolate import interp1d
from astropy.io import ascii
from astropy import units as u

from newdust import constants as c
from newdust.graindist.composition import _find_cmfile

__all__ = ['CmSilicate']

RHO_SIL       = 3.8  # g cm^-3

class CmSilicate(object):
    """
    | **ATTRIBUTES**
    | cmtype : 'Silicate'
    | rho : grain material density (g cm^-3)
    | citation : A string containing citation to the original work
    | interps : A tuple containing scipy.interp1d objects (rp, ip)
    |
    | *functions*
    | rp(lam, unit='kev')  : Returns real part (unit='kev'|'angs')
    | ip(lam, unit='kev')  : Returns imaginary part (unit='kev'|'angs')
    | cm(lam, unit='kev') : Complex index of refraction of dtype='complex'
    | plot(lam=None, unit='kev') : Plots Re(m-1) and Im(m)
    |   if lam is *None*, plots the original interp objects
    |   otherwise, plots with user defined wavelength (lam)
    """
    def __init__(self, rho=RHO_SIL):
        self.cmtype = 'Silicate'
        self.rho    = rho
        self.citation = "Using optical constants for astrosilicate,\nDraine, B. T. 2003, ApJ, 598, 1026\nhttp://adsabs.harvard.edu/abs/2003ApJ...598.1026D"

        D03file = _find_cmfile('callindex.out_sil.D03')
        D03dat  = ascii.read(D03file, header_start=4, data_start=5)

        wavel = D03dat['wave(um)'] * u.micron
        rp  = interp1d(wavel.to(u.cm).value, 1.0 + D03dat['Re(n)-1'])  # wavelength (cm), rp
        ip  = interp1d(wavel.to(u.cm).value, D03dat['Im(n)'])          # wavelength (cm), ip
        self.interps = (rp, ip)

    def _interp_helper(self, lam_cm, interp, rp=False):
        # Returns zero for wavelengths not covered by the interpolation object
        # If the real part is needed, returns 1 (consistent with vacuum)
        result = np.zeros(np.size(lam_cm))
        if rp: result += 1

        if np.size(lam_cm) == 1:
            if (lam_cm >= np.min(interp.x)) & (lam_cm <= np.max(interp.x)):
                result = interp(lam_cm)
        else:
            ii = (lam_cm >= np.min(interp.x)) & (lam_cm <= np.max(interp.x))
            result[ii] = interp(lam_cm[ii])
        return result

    def rp(self, lam, unit='kev'):
        lam_cm = c._lam_cm(lam, unit)
        return self._interp_helper(lam_cm, self.interps[0], rp=True)

    def ip(self, lam, unit='kev'):
        lam_cm = c._lam_cm(lam, unit)
        return self._interp_helper(lam_cm, self.interps[1])

    def cm(self, lam, unit='kev'):
        return self.rp(lam, unit=unit) + 1j * self.ip(lam, unit=unit)

    def plot(self, ax, lam=None, unit='kev', rppart=True, impart=True):
        if lam is None:
            rp_m1 = np.abs(self.interps[0].y - 1.0)
            ip = self.interps[1].y
            x  = self.interps[0].x / c.micron2cm  # cm / (cm/um)
            xlabel = "Wavelength (um)"
        else:
            rp_m1 = np.abs(self.rp(lam, unit=unit)-1.0)
            ip = self.ip(lam, unit)
            x  = lam
            assert unit in c.ALLOWED_LAM_UNITS
            if unit == 'kev': xlabel = "Energy (keV)"
            if unit == 'angs': xlabel = "Wavelength (Angstroms)"
        if rppart:
            ax.plot(x, rp_m1, ls='-', label='|Re(m-1)|')
        if impart:
            ax.plot(x, ip, ls='--', label='Im(m)')
        ax.set_xlabel(xlabel)
        ax.legend()
