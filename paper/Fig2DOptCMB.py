from __future__ import print_function
from builtins import zip
from configparser import SafeConfigParser 
import pickle as pickle
import sys, os
import itertools

from orphics.tools.io import FisherPlots


def getFisher(expName,gridName,calName,saveName,inParamList,suffix):
    saveId = expName + "_" + gridName+ "_" + calName + "_" + suffix

    paramList,FisherTot = pickle.load(open(bigDataDir+"savedFisher_"+saveId+"_"+saveName+".pkl",'rb'))
    print(paramList)
    print(inParamList)
    #assert paramList==inParamList
    return FisherTot

out_dir = os.environ['WWW']+"paper/"


iniFile = "input/pipeline.ini"
Config = SafeConfigParser()
Config.optionxform=str
Config.read(iniFile)
bigDataDir = Config.get('general','bigDataDirectory')


#fishSection = "mnu-w0-wa"
#fishSection = "mnu-w0"
#fishSection = "lcdm"


noatm = ""
# cals = ["CMB_all","CMB_pol","owl2","owl1"]
# labs = ["CMB T+P","CMB P only","Optical $z<2$","Optical $z<1$"]
# cols = ["C0","C0","C1","C1"]
# lss = ["-","--","-","--"]
# derivSet = "v0.6"
# gridNames = ["grid-default","grid-default","grid-owl2","grid-owl1"]

cals = ["CMB_all","owl1"]
labs = ["AdvACT SZ + internal CMB lensing T+P","AdvACT SZ + LSST optical lensing $z<1$"]
cols = ["C0","C1"]
lss = ["-","-"]
derivSet = "v0.6"
gridNames = ["grid-default","grid-owl1"]

fplots = FisherPlots()
fplots.startFig() 

#for fishSection,alphas in zip(["mnu-w0-wa","mnu-w0"],[[1,1,1,1],[0.3,0.3,0.3,0.3]]):
#for fishSection,alphas in zip(["mnu-w0-wa-paper"],[[1,1,1,1]]):
for fishSection,alphas in zip(["mnu-w0-paper"],[[1,1,1,1]]):

    if fishSection == "mnu-w0-wa-paper":
        labs = itertools.repeat(None)
        suff = "B"
    else:
        suff = "A"
        
    cosmoFisher = Config.get('fisher-'+fishSection,'saveSuffix')
    paramList = Config.get('fisher-'+fishSection,'paramList').split(',')
    paramLatexList = Config.get('fisher-'+fishSection,'paramLatexList').split(',')
    fparams = {} 
    for (key, val) in Config.items('params'):
        param = val.split(',')[0]
        fparams[key] = float(param)

    fplots.addSection(fishSection,paramList,paramLatexList,fparams)


    """RES STUDY"""
    for cal,gridName in zip(cals,gridNames):
        #cmbfisher = getFisher("S4-1.0-paper"+noatm,gridName,cal,cosmoFisher,paramList,derivSet)
        cmbfisher = getFisher("AdvAct"+noatm,gridName,cal,cosmoFisher,paramList,derivSet)
        fplots.addFisher(fishSection,cal,cmbfisher.copy())



    fplots.plotPair(fishSection,['mnu','w0'],cals,labels=labs,xlims=[-0.12,0.22],ylims=[-1.16,-0.84],cols=cols,lss=lss,loc='lower left',alphas=alphas)
    #fplots.plotPair(fishSection,['mnu','w0'],cals,labels=labs,xlims=[-0.1,0.2],ylims=[-1.14,-0.86],cols=cols,lss=lss,loc='lower left',alphas=alphas)
    #fplots.plotPair(fishSection,['mnu','w0'],cals,labels=labs,xlims=[-0.05,0.15],ylims=[-1.1,-0.86],cols=cols,lss=lss,loc='lower left',alphas=alphas)

fplots.done(saveFile=out_dir+"Fig2DOptCMBAdvact"+suff+".png")
