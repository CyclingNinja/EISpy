# -*- coding: utf-8 -*-
# Author: Mateo Inchaurrandieta <mateo.inchaurrandieta@gmail.com>
# pylint: disable=E1101
"""
Calibration and error calculation for EIS level 0 files.
This module calls several corrections, then attempts to interpolate missing or
damaged data, and calculates the 1-sigma errors of the good data.
"""

from __future__ import absolute_import
from . import io
from . import pixel_calibration as pc
from . import data_calibration as dc


__all__ = ['eis_prep']
# TODO: fix units


def eis_prep(filename, **kwargs):
    """
    EIS prep is the main calibration method for the level 0 FITS files produced
    by EIS. This method removes saturated and empty data points, removes dark
    current, removes hot, warm and dusty pixels, removes cosmic rays, corrects
    for losses in sensitivity over time, interpolates for missing data,
    converts the data from arbitrary units into units of spectral radiance (aka
    specific intensity), and outputs the result into a new level 1 FITS file.

    There are many keyword arguments available to fine-tune the calibration.
    Other than those detailed below, this method can take in arguments to give
    to astropy.io.fits.open and astroscrappy.detect_cosmics. Refer to these
    packages' documentation for a detailed explanation of the arguments
    available.

    Parameters
    ----------
    filename: str
        Location of the level-0 FITS file.
    zeros=True: bool, optional
        If True, remove zeros and saturated data
    darkcur=True: bool, optional
        If True, subtract dark current from the data
    calhp=True: bool, optional
        If True, remove hot pixels from the data
    calwp=True: bool, optional
        If True, remove warm pixels from the data
    caldp=True: bool, optional
        If True, remove dusty pixels from the data
    interp=True: bool, optional
        If True, interpolate missing pixels and their errors.
    cosmics=True: bool, optional
        If True, remove and correct for cosmic rays
    sens=True: bool, optional
        If True, correct for the loss in sensitivty since launch.
    phot2int=True: bool, optional
        If True, set the units of the output file to be photon intensity
        (photons*cm^-2*s^-1*A^-1*sr^-1) instead of spectral radiance - aka
        specific intensity (erg*cm^-2*s^-1*A^-1*sr^-1). Notice that doing this
        conversion will also change the errors to have the correct units.
    institute='Unknown institute': str
        Institute where this method is run, to write to the FITS file.
    outdir=None: str
        Location of the directory to output files to. If not provided, the
        function will simply return the corrected data and errors as a list
        of tuples, along with the level 0 metadata.
    """
    # TODO: verbose?
    data_and_errors, meta = io.read_fits(filename, **kwargs)
    if kwargs.get('zeros', True):
        pc.remove_zeros_saturated(*data_and_errors)
    if kwargs.get('darkcur', True):
        pc.remove_dark_current(meta, *data_and_errors)
    pc.calibrate_pixels(meta, *data_and_errors, **kwargs)
    if kwargs.get('interp', True):
        dc.interpolate_missing_pixels(*data_and_errors)
    if kwargs.get('cosmics', True):
        dc.remove_cosmic_rays(*data_and_errors, **kwargs)
    if kwargs.get('sens', True):
        dc.correct_sensitivity(meta, *data_and_errors)
    dc.radiometric_calibration(meta, *data_and_errors, **kwargs)
    outdir = kwargs.get('outdir', None)
    if outdir is not None:
        io.write_to_fits(outdir, filename, *data_and_errors, **kwargs)
    else:
        return data_and_errors, meta