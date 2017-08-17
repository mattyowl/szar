import itertools
from szar.counts import rebinN
import numpy as np
from orphics.tools.io import dictFromSection, listFromConfig
from szar.counts import ClusterCosmology,Halo_MF
from szar.szproperties import SZ_Cluster_Model
import cPickle as pickle
import traceback

def pad_fisher(fisher,num_pad):
    return np.pad(fisher,pad_width=((0,num_pad),(0,num_pad)),mode="constant",constant_values=0.)


def get_sovernsquare(expName,gridName,version,qbins):
    sId = expName + "_" + gridName  + "_v" + version
    sovernsquareEach = np.loadtxt(bigDataDir+"sampleVarGrid_"+sId+".txt")
    sovernsquare =  np.dstack([sovernsquareEach]*len(qbins))
    return sovernsquare

def save_id(expName,gridName,calName,version):
    saveId = expName + "_" + gridName + "_" + calName + "_v" + version
    return saveId
def deriv_root(bigDataDir,saveId):
    return bigDataDir+"dNdp_mzq_"+saveId+"_"
def fid_file(bigDataDir,saveId):
    return bigDataDir+"N_mzq_"+saveId+"_fid"+".npy"

def counts_from_config(Config,bigDataDir,version,expName,gridName,mexp_edges,z_edges):
    experimentName = expName
    cosmoDict = dictFromSection(Config,"params")
    constDict = dictFromSection(Config,'constants')
    clusterDict = dictFromSection(Config,'cluster_params')
    clttfile = Config.get("general","clttfile")
    cc = ClusterCosmology(cosmoDict,constDict,clTTFixFile = clttfile)

    beam = listFromConfig(Config,experimentName,'beams')
    noise = listFromConfig(Config,experimentName,'noises')
    freq = listFromConfig(Config,experimentName,'freqs')
    lmax = int(Config.getfloat(experimentName,'lmax'))
    lknee = float(Config.get(experimentName,'lknee').split(',')[0])
    alpha = float(Config.get(experimentName,'alpha').split(',')[0])
    fsky = Config.getfloat(experimentName,'fsky')
    SZProf = SZ_Cluster_Model(cc,clusterDict,rms_noises = noise,fwhms=beam,freqs=freq,lknee=lknee,alpha=alpha)
    hmf = Halo_MF(cc,mexp_edges,z_edges)
    mgrid,zgrid,siggrid = pickle.load(open(bigDataDir+"szgrid_"+expName+"_"+gridName+ "_v" + version+".pkl",'rb'))

    hmf.sigN = siggrid.copy()
    Ns = np.multiply(hmf.N_of_z_SZ(fsky,SZProf),np.diff(z_edges).reshape(1,z_edges.size-1)).ravel()

    return Ns.sum()


def priors_from_config(Config,expName,calName,fishName,paramList):
    fishSection = 'fisher-'+fishName

    try:
        priorNameList = Config.get(fishSection,'prior_names').split(',')
        priorValueList = listFromConfig(Config,fishSection,'prior_values')
    except:
        priorNameList = []
        priorValueList = []

    if "CMB" in calName:
        assert "sigR" not in paramList
        paramList.append("sigR")
        try:
            priorNameList.append("sigR")
            beam = listFromConfig(Config,expName,'beams')
            freq = listFromConfig(Config,expName,'freqs')
            freq_to_use = Config.getfloat(calName,'freq')
            ind = np.where(np.isclose(freq,freq_to_use))
            beamFind = np.array(beam)[ind]
            priorValueList.append(beamFind/2.)
            print "Added sigR prior ", priorValueList[-1]
        except:
            traceback.print_exc()
            print "Couldn't add sigR prior. Is this CMB lensing? Exiting."
            sys.exit(1)

    if "owl" in calName:
        if not("b_wl") in paramList:
            print "OWL but b_wl not found in paramList. Adding with a 1% prior."
            paramList.append("b_wl")
            priorNameList.append("b_wl")
            priorValueList.append(1./(0.01**2.))
            
    return paramList, priorNameList, priorValueList
    

def cluster_fisher_from_config(Config,expName,gridName,calName,fishName,
                               overridePlanck=None,overrideBAO=None,overrideOther=None):


    """
    Returns
    1. Fisher - the Fisher matrix
    2. paramList - final parameter list defining the Fisher contents. Might add extra params (e.g. sigR, bwl)

    Accepts
    1. Config - a ConfigParser object containing the ini file contents
    2. expName - name of experiment section in ini file
    3. gridName - name of M,q,z grid definition in ini file
    4. calName - name of weak lensing calibration section
    5. fishName - looks for a section in ini file named "fisher-"+fishName for Fisher options
    6. overridePlanck - Fisher matrix to add to upper left corner of original in place of Planck fisher 
                        matrix specified in ini. Can be zero.
    7. overrideBAO - Fisher matrix to add to upper left corner of original in place of BAO fisher 
                     matrix specified in ini. Can be zero.
    8. overrideOther - Fisher matrix to add to upper left corner of original in place of "other" fisher 
                        matrix specified in ini. Can be zero.
    
    """
    
    bigDataDir = Config.get('general','bigDataDirectory')
    version = Config.get('general','version') 
    pzcutoff = Config.getfloat('general','photoZCutOff')
    fsky = Config.getfloat(expName,'fsky')
    # Fisher params
    fishSection = 'fisher-'+fishName
    paramList = Config.get(fishSection,'paramList').split(',')
    zs = listFromConfig(Config,gridName,'zrange')
    z_edges = np.arange(zs[0],zs[1]+zs[2],zs[2])

    saveId = save_id(expName,gridName,calName,version)
    derivRoot = deriv_root(bigDataDir,saveId)
    # Fiducial number counts
    new_z_edges, N_fid = rebinN(np.load(fid_file(bigDataDir,saveId)),pzcutoff,z_edges)
    N_fid = N_fid[:,:,:]*fsky
    print "Effective number of clusters: ", N_fid.sum()

    paramList, priorNameList, priorValueList = priors_from_config(Config,expName,calName,fishName,paramList)
    Fisher = getFisher(N_fid,paramList,priorNameList,priorValueList,derivRoot,pzcutoff,z_edges,fsky)

    # Number of non-SZ params (params that will be in Planck/BAO)
    numCosmo = Config.getint(fishSection,'numCosmo')
    numLeft = len(paramList) - numCosmo

    try:
        do_cmb_fisher = Config.getboolean(fishSection,"do_cmb_fisher")
    except:
        do_cmb_fisher = False

    try:
        do_clkk_fisher = Config.getboolean(fishSection,"do_clkk_fisher")
    except:
        do_clkk_fisher = False

    if do_clkk_fisher:
        assert do_cmb_fisher, "Sorry, currently Clkk fisher requires CMB fisher to be True as well."
        lensName = Config.get(fishSection,"clkk_section")
    else:
        lensName = None
        
    if do_cmb_fisher:

        import pyfisher.clFisher as pyfish
        # Load fiducials and derivatives
        cmbDerivRoot = Config.get("general","cmbDerivRoot")
        cmbParamList = paramList[:numCosmo]
        fidCls = np.loadtxt(cmbDerivRoot+'_fCls.csv',delimiter=',')
        dCls = {}
        for paramName in cmbParamList:
            dCls[paramName] = np.loadtxt(cmbDerivRoot+'_dCls_'+paramName+'.csv',delimiter=',')

        print "Calculating CMB fisher matrix..."
        cmb_fisher = pad_fisher(pyfish.fisher_from_config(fidCls,dCls,cmbParamList,Config,expName,lensName),numLeft)
    
    else:
        cmb_fisher = 0.    


    Fisher = Fisher + cmb_fisher
    
    return Fisher, paramList



def getFisher(N_fid,paramList,priorNameList,priorValueList,derivRoot,pzcutoff,z_edges,fsky):
    numParams = len(paramList)
    Fisher = np.zeros((numParams,numParams))
    paramCombs = itertools.combinations_with_replacement(paramList,2)
    for param1,param2 in paramCombs:
        i = paramList.index(param1)
        j = paramList.index(param2)
        if not(param1=='tau' or param2=='tau'): 
            new_z_edges, dN1 = rebinN(np.load(derivRoot+param1+".npy"),pzcutoff,z_edges)
            new_z_edges, dN2 = rebinN(np.load(derivRoot+param2+".npy"),pzcutoff,z_edges)
            dN1 = dN1[:,:,:]*fsky
            dN2 = dN2[:,:,:]*fsky


            assert not(np.any(np.isnan(dN1)))
            assert not(np.any(np.isnan(dN2)))
            assert not(np.any(np.isnan(N_fid)))


            with np.errstate(divide='ignore'):
                FellBlock = dN1*dN2*np.nan_to_num(1./(N_fid))#+(N_fid*N_fid*sovernsquare)))
            #Ncollapsed = N_fid.sum(axis=0).sum(axis=-1)
            #print N_fid[np.where(Ncollapsed<1.)].sum() ," clusters fall in bins where N<1"
            #FellBlock[np.where(Ncollapsed<1.)] = 0.
            Fell = FellBlock.sum()
        else:
            Fell = 0.

        if i==j and (param1 in priorNameList):
            priorIndex = priorNameList.index(param1)
            priorVal = 1./priorValueList[priorIndex]**2.
        else:
            priorVal = 0.

        Fisher[i,j] = Fell+priorVal
        if j!=i: Fisher[j,i] = Fell

    
    return Fisher
