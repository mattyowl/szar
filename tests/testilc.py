import matplotlib
matplotlib.use('Agg')
import numpy as np
from szar.counts import ClusterCosmology
from szar.szproperties import SZ_Cluster_Model
from szar.foregrounds import fgNoises, f_nu
from szar.ilc import ILC_simple
import sys,os
from ConfigParser import SafeConfigParser 
import cPickle as pickle
from orphics.tools.io import dictFromSection, listFromConfig, Plotter
from orphics.tools.cmb import noise_func

#Read ini file

iniFile = "input/pipeline.ini"
Config = SafeConfigParser()
Config.optionxform=str
Config.read(iniFile)

constDict = dictFromSection(Config,'constants')
clusterDict = dictFromSection(Config,'cluster_params')
fparams = {}   # the 
for (key, val) in Config.items('params'):
    if ',' in val:
        param, step = val.split(',')
        fparams[key] = float(param)
    else:
        fparams[key] = float(val)

#Get Cls
clttfile = Config.get('general','clttfile')
#Initiate cluster cosmology class
cc = ClusterCosmology(fparams,constDict,lmax=8000,pickling=True)#clTTFixFile=clttfile)
#Initiate foreground class
fgs = fgNoises(cc.c,ksz_battaglia_test_csv="data/ksz_template_battaglia.csv",tsz_battaglia_template_csv="data/sz_template_battaglia.csv")

#constrained ilc flag 0=False 1=True
cf = 0
constraint_tag = ['','_constrained']

#choose experiment
experimentName = "CCATP"
beams = listFromConfig(Config,experimentName,'beams')
noises = listFromConfig(Config,experimentName,'noises')
freqs = listFromConfig(Config,experimentName,'freqs')
lmax = int(Config.getfloat(experimentName,'lmax'))
lknee = listFromConfig(Config,experimentName,'lknee')[0]
alpha = listFromConfig(Config,experimentName,'alpha')[0]
fsky = Config.getfloat(experimentName,'fsky')


#SZProfExample = SZ_Cluster_Model(clusterCosmology=cc,clusterDict=clusterDict,rms_noises = noises,fwhms=beams,freqs=freqs,lmax=lmax,lknee=lknee,alpha=alpha)

#initialize ILC
ILC  = ILC_simple(cc,fgs, rms_noises = noises,fwhms=beams,freqs=freqs,lmax=lmax,lknee=lknee,alpha=alpha)

#set ells
lsedges = np.arange(100,2001,100)

#calc ILC
if (cf == 0):
    el_il,  cls_il,  err_il,  s2ny  = ILC.Forecast_Cellyy(lsedges,fsky)
    el_ilc,  cls_ilc,  err_ilc,  s2n  = ILC.Forecast_Cellcmb(lsedges,fsky)
if (cf == 1):
    el_il,  cls_il,  err_il,  s2ny  = ILC.Forecast_Cellyy(lsedges,fsky,constraint="cmb")
    el_ilc,  cls_ilc,  err_ilc,  s2n  = ILC.Forecast_Cellcmb(lsedges,fsky,constraint="tsz")
print 'S/N y', s2ny
print 'S/N CMB', s2n


#Extra stuff

#print 'S/N' , np.sqrt(np.sum((cls_ilc/err_ilc)**2))

#outDir = "/Users/nab/Desktop/Projects/SO_forecasts/"

#outfile1 = outDir + experimentName + "_y_weights"+constraint_tag[cf]+".png"
#outfile2 = outDir + experimentName + "_cmb_weights"+constraint_tag[cf]+".png"

#ILC.PlotyWeights(outfile1)
#ILC.PlotcmbWeights(outfile2)

#if (cf == 0): 
#    eln,nl = ILC.Noise_ellyy()
#    elnc,nlc = ILC.Noise_ellcmb()

#if (cf == 1): 
#    eln,nl = ILC.Noise_ellyy(constraint='cib')
#    elnc,nlc = ILC.Noise_ellcmb(constraint='tsz')




