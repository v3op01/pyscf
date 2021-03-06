#!/usr/bin/env python
# -*- coding: utf-8
# Author: Qiming Sun <osirpt.sun@gmail.com>
#         Timothy Berkelbach <tim.berkelbach@gmail.com>

import os
from pyscf.pbc.gto.pseudo import parse_cp2k
from pyscf.pbc.gto.pseudo.pp import *
from pyscf.pbc.gto.pseudo import pp_int

ALIAS = {
    'gthblyp'    : 'gth-blyp.dat'   ,
    'gthbp'      : 'gth-bp.dat'     ,
    'gthhcth120' : 'gth-hcth120.dat',
    'gthhcth407' : 'gth-hcth407.dat',
    'gtholyp'    : 'gth-olyp.dat'   ,
    'gthlda'     : 'gth-pade.dat'   ,
    'gthpade'    : 'gth-pade.dat'   ,
    'gthpbe'     : 'gth-pbe.dat'    ,
    'gthpbesol'  : 'gth-pbesol.dat' ,
    'gthhf    '  : 'gth-hf.dat' ,
}

def parse(string):
    '''Parse the pseudo text which is in CP2K format, return an internal
    pseudo format which can be assigned to :attr:`Cell.pseudo`

    Args:
        string : Blank linke and the lines of "PSEUDOPOTENTIAL" and "END" will be ignored

    Examples:

    >>> cell = gto.Cell()
    >>> cell.pseudo = {'C': gto.pseudo.parse("""
    ... #PSEUDOPOTENTIAL
    ... C GTH-BLYP-q4
    ...     2    2
    ...      0.33806609    2    -9.13626871     1.42925956
    ...     2
    ...      0.30232223    1     9.66551228
    ...      0.28637912    0
    ... """)}
    '''
    return parse_cp2k.parse(string)

def load(pseudo_name, symb):
    '''Convert the pseudopotential of the given symbol to internal format

    Args:
        pseudo_name : str
            Case insensitive pseudopotential name. Special characters will be removed.
        symb : str
            Atomic symbol, Special characters will be removed.

    Examples:
        Load GTH-BLYP pseudopotential of carbon 

    >>> cell = gto.Cell()
    >>> cell.pseudo = {'C': load('gth-blyp', 'C')}
    '''
    if os.path.isfile(pseudo_name):
        return parse_cp2k.load(pseudo_name, symb)

    name = pseudo_name.lower().replace(' ', '').replace('-', '').replace('_', '')
    pseudomod = ALIAS[name]
    symb = ''.join(i for i in symb if i.isalpha())
    p = parse_cp2k.load(os.path.join(os.path.dirname(__file__), pseudomod), symb)
    return p

