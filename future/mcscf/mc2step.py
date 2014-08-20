#!/usr/bin/env python
# $Id$
# -*- coding: utf-8

import time
import numpy
import scipy.linalg
from pyscf import lib
from pyscf import ao2mo
import mc1step as mc1step

def kernel(mol, casscf, mo_coeff, tol=1e-7, macro=30, micro=8, \
           ci0=None, verbose=None):
    if verbose is None:
        verbose = casscf.verbose
    log = lib.logger.Logger(casscf.stdout, verbose)
    cput0 = (time.clock(), time.time())
    log.debug('Start 2-step CASSCF')

    ncas = casscf.ncas
    nelecas = casscf.nelecas
    nmo = mo_coeff.shape[1]

    mo = mo_coeff
    eris = casscf.update_ao2mo(mo)
    e_tot, e_ci, fcivec = casscf.casci(mo, ci0, eris)
    log.info('CASCI E(+nuc) = %.15g', e_tot)
    elast = e_tot
    conv = False
    toloose = casscf.conv_threshold_grad
    totmicro = totinner = 0

    t2m = t1m = log.timer('Initializing 2-step CASSCF', *cput0)
    for imacro in range(macro):
        ninner = 0
        t3m = t2m
        for imicro in range(micro):

            u, dx, g_orb, nin = mc1step.rotate_orb_ah(mol, casscf, mo, \
                                                      fcivec, e_ci, eris, 0, \
                                                      verbose=verbose)
            t3m = log.timer('orbital rotation', *t3m)

            mo = numpy.dot(mo, u)
            eris = None # to avoid using too much memory
            eris = casscf.update_ao2mo(mo)
            t3m = log.timer('update eri', *t3m)

            ninner += nin
            norm_dt = numpy.linalg.norm(u-numpy.eye(nmo))
            norm_gorb = numpy.linalg.norm(g_orb)
            log.debug('micro %d, |u-1|=%4.3g, |g[o]|=%4.3g', \
                      imicro, norm_dt, norm_gorb)
            t2m = log.timer('micro iter %d'%imicro, *t2m)
            if norm_dt < toloose or norm_gorb < toloose:
                break

        totinner += ninner
        totmicro += imicro+1

        e_tot, e_ci, fcivec = casscf.casci(mo, fcivec, eris)
        log.info('macro iter %d (%d ah, %d micro), CASSCF E(+nuc) = %.15g, dE = %.8g,',
                 imacro, ninner, imicro+1, e_tot, e_tot-elast)
        norm_gorb = numpy.linalg.norm(g_orb)
        log.info('                        |grad[o]| = %6.5g',
                 numpy.linalg.norm(g_orb))
        log.timer('CASCI solver', *t2m)
        t2m = t1m = log.timer('macro iter %d'%imacro, *t1m)

        #print e_tot, e_tot - elast
        if abs(elast - e_tot) < tol and norm_gorb < toloose:
            conv = True
            break
        else:
            elast = e_tot

    if conv:
        log.info('2-step CASSCF converged in %d macro (%d ah %d micro) steps',
                 imacro+1, totinner, totmicro)
    else:
        log.info('2-step CASSCF not converged, %d macro (%d ah %d micro) steps',
                 imacro+1, totinner, totmicro)
    log.log('2-step CASSCF, energy = %.15g', e_tot)
    log.timer('2-step CASSCF', *cput0)
    return e_tot, e_ci, fcivec, mo



if __name__ == '__main__':
    from pyscf import gto
    from pyscf import scf

    mol = gto.Mole()
    mol.verbose = 0
    mol.output = None#"out_h2o"
    mol.atom = [
        ['H', ( 1.,-1.    , 0.   )],
        ['H', ( 0.,-1.    ,-1.   )],
        ['H', ( 1.,-0.5   ,-1.   )],
        ['H', ( 0.,-0.5   ,-1.   )],
        ['H', ( 0.,-0.5   ,-0.   )],
        ['H', ( 0.,-0.    ,-1.   )],
        ['H', ( 1.,-0.5   , 0.   )],
        ['H', ( 0., 1.    , 1.   )],
    ]

    mol.basis = {'H': 'sto-3g',
                 'O': '6-31g',}
    mol.build()

    m = scf.RHF(mol)
    ehf = m.scf()
    emc = kernel(mol, mc1step.CASSCF(mol, m, 4, 4), m.mo_coeff, verbose=4)[0]
    print ehf, emc, emc-ehf
    print emc - -3.22013929407


    mol.atom = [
        ['O', ( 0., 0.    , 0.   )],
        ['H', ( 0., -0.757, 0.587)],
        ['H', ( 0., 0.757 , 0.587)],]
    mol.basis = {'H': 'cc-pvdz',
                 'O': 'cc-pvdz',}
    mol.build()

    m = scf.RHF(mol)
    ehf = m.scf()
    mc = mc1step.CASSCF(mol, m, 6, 4)
    mc.verbose = 4
    emc = mc.mc2step()[0]
    print ehf, emc, emc-ehf
    #-76.0267656731 -76.0873922924 -0.0606266193028
    print emc - -76.0873923174, emc - -76.0926176464

