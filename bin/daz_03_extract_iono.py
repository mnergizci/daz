#!/usr/bin/env python3
"""
v1.0 2022-01-03 Milan Lazecky, Leeds Uni

This script will extract ionosphere shifts using either IRI2016 model or the CODE dataset.

===============
Input & output files
===============
Inputs :
 - frames.csv - contains data with heading:
frame,master,center_lon,center_lat,heading,azimuth_resolution,avg_incidence_angle,centre_range_m,centre_time,dfDC
 - esds.csv - contains data with heading:
,frame,orbits_precision,epochdate,daz_mm,years_since_beginning[,daz_tide_mm,daz_mm_notide]

Outputs :
 - esds_with_iono.csv - added iono columns
 - frames_with_iono.csv - added iono columns

=====
Usage
=====
daz_03_extract_iono.py [--indaz esds.csv] [--use_gim] [--infra frames.csv] [--outfra frames_with_iono.csv] [--outdaz esds_with_iono.csv]

Notes:
    --use_gim  Will apply JPL GIM (or CODE if JPL data not available) to get TEC values rather than the default IRI2016 estimates. Note IRI2016 can still be used to estimate iono peak altitude. Tested only in LiCSAR environment.
"""
#%% Change log
'''
v1.2 2025-06-12 ML imported codes by M. Nergizci to replace CODE for JPL GIM (proven better as with higher temporal sampling)
v1.1 2023-08-10 Milan Lazecky, UoL
 - added option to get iono correction from CODE (combined with IRI2016 to estimate iono F2 peak altitude)
v1.0 2022-01-03 Milan Lazecky, Uni of Leeds
 - Original implementation - based on codes from 2021-06-24
'''
from daz_lib import *
from daz_iono import *

import getopt, os, sys

# keeping assumption of hei=450 km --- best to test first (yet at the moment we are anyway quite coarse due to 1-value-per-frame)
use_iri_hei = False

class Usage(Exception):
    """Usage context manager"""
    def __init__(self, msg):
        self.msg = msg


#%% Main
def main(argv=None):
    
    #%% Check argv
    if argv == None:
        argv = sys.argv
    
    #%% Set default
    indazfile = 'esds.csv'
    inframesfile = 'frames.csv'
    outdazfile = 'esds_with_iono.csv'
    outframesfile = 'frames_with_iono.csv'
    ionosource = 'iri'

    #%% Read options
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help", "use_gim", "indaz=", "infra=", "outdaz=", "outfra="])
        except getopt.error as msg:
            raise Usage(msg)
        for o, a in opts:
            if o == '-h' or o == '--help':
                print(__doc__)
                return 0
            if o == '--use_gim':
                ionosource = 'code'
                print('using GIM (primarily JPL, or CODE) for iono correction - note latest data might not be processed (will be stored as NaN in the csv)')
            elif o == "--indaz":
                indazfile = a
            elif o == "--infra":
                inframesfile = a
            elif o == "--outdaz":
                outdazfile = a
            elif o == "--outfra":
                outframesfile = a
        
        if os.path.exists(outdazfile):
            raise Usage('output esds csv file already exists. Cancelling')
        if os.path.exists(outframesfile):
            raise Usage('output frames csv file already exists. Cancelling')
        if not os.path.exists(inframesfile):
            raise Usage('input frames csv file does not exist. Cancelling')
        if not os.path.exists(indazfile):
            raise Usage('input esds csv file does not exist. Cancelling')
            
    except Usage as err:
        print("\nERROR:",)
        print("  "+str(err.msg))
        print("\nFor help, use -h or --help.\n")
        return 2
    
    # processing itself:
    #esds = pd.read_csv(indazfile)
    #framespd = pd.read_csv(inframesfile)
    esds, framespd = load_csvs(esdscsv = indazfile, framescsv = inframesfile)
    ''' in case of using other csvs that already contained iono corr:
    indazfile2='../esds_with_iono.csv'
    inframesfile2='../frames_with_iono.csv'
    esdsi, framespdi = load_csvs(esdscsv = indazfile2, framescsv = inframesfile2)
    
    i=framespdi[['frame','Hiono','Hiono_std','Hiono_range','tecs_A','tecs_B']]
    outframespd=pd.merge(framespd,i,on='frame',how='inner')
    
    i=esdsi[['tecs_A','tecs_B','daz_iono_mm']]
    esds=esds.reset_index(drop=True)
    outesds=esds.combine_first(i)
    outesds=outesds.reindex(columns=['frame', 'orbits_precision', 'epochdate', 'pod_diff_azi_m', 'S1AorB',
        'daz_tide_mm', 'daz_mm', 'daz_cc_mm', 'years_since_beginning',
        'daz_mm_notide','tecs_A', 'tecs_B', 'daz_iono_mm'])
    outesds = outesds[outesds['daz_iono_mm']!=0]
    col = 'daz_mm_notide'
    esds=outesds
    esds[col+'_noiono'] = esds[col] - esds['daz_iono_mm']
    framespd=outframespd

    esds.to_csv(outdazfile)
    framespd.to_csv(outframesfile)
    '''
    print('extra data cleaning step - perhaps should add to another step (first?)')
    esds, framespd = df_preprepare_esds(esds, framespd, firstdate = '', countlimit = 25)
    print('performing the iono calculation')
    esds, framespd = extract_iono_full(esds, framespd, ionosource = ionosource, use_iri_hei=use_iri_hei)
    if 'daz_mm_notide' in esds:
        col = 'daz_mm_notide'
    else:
        col = 'daz_mm'
    try:
        esds[col+'_noiono'] = esds[col] - esds['daz_iono_mm'] # 2023/08: changed sign to keep consistent with the GRL article
    except:
        print('probably a bug, please check column names - in any case, the correction is stored as daz_iono_mm column')
    '''
    if not parallel:
        esds, framespd = extract_iono_full(esds, framespd)
    else:
        print('through {0} parallel processes'.format(str(nproc)))
        
        @dask.delayed
        def dask_extract_iono_full(esds, framespd):
            return extract_iono_full(esds, framespd)
        
        for track in range(175):
            track=track+1
            selesds = esds.copy()
            selframes = framespd.where().copy()
            selesds, selframes = dask_extract_iono_full(selesds, selframes)
            esds.update(selesds)
            framespd.update(selframes)
    '''
    print('saving files')
    esds.to_csv(outdazfile)
    framespd.to_csv(outframesfile)
    print('done')

#%% main
if __name__ == "__main__":
    sys.exit(main())

