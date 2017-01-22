import numpy as np
from scipy import special
from sympy.functions import coth
import camb
from camb import model
import haloTools as HP

from Tinker_MF import dn_dlogM
from Tinker_MF import tinker_params

from orphics.tools.output import Plotter

class Cosmology(object):
    '''
    A wrapper around CAMB that tries to pre-calculate as much as possible
    '''
    def __init__(self,paramDict,constDict):

        cosmo = paramDict
        self.H0 = cosmo['H0']
        self.omch2 = cosmo['omch2']
        self.ombh2 = cosmo['ombh2']
        
        self.pars = camb.CAMBparams()
        self.pars.set_cosmology(H0=self.H0, ombh2=cosmo['ombh2'], omch2=self.omch2)
        self.pars.InitPower.set_params(ns=cosmo['ns'],As=cosmo['As'])

        self.results= camb.get_background(self.pars)
        self.omnuh2 = self.pars.omegan * ((self.H0 / 100.0) ** 2.)
        

class CosmoParams:
    def __init__(self,constants,         #default is WMAP9
                 om=0.279,ol=0.721,h0=70.0,s8=0.821,ns=0.972,
                 ob=0.0463,r=0.0,mnu=0.00,tau=0.08,**options):

        c = constants
        self.c = c
        h100 = 100. 
        self.rho_crit0 = 3. / (8 * np.pi) * (h100 * 1e5)**2 / c.G_CGS * c.MPC2CM / c.MSUN_CGS

        self.om = om
        self.ol = ol
        self.h0 = h0
        self.s8 = s8
        self.ns = ns
        self.ob = ob
        self.r = r
        self.mnu = mnu
        self.tau = tau
            
        if options.get("Param") == 'Planck15':
            self.om = 0.315
            self.ol = 0.685
            self.h0 = 67.31
            self.s8 = 0.829
            self.ns = 0.9655
            self.ob = 0.04904
            self.r = 0.0
            self.mnu = 0.00
            self.tau = 0.08
                
        if options.get("Param") == 'Tinker':
            self.om = 0.30
            self.ol = 0.70
            self.h0 = 70
            self.s8 = 0.9
            self.ns = 1.0
            self.ob = 0.04
            self.r = 0.0
            self.mnu = 0.00
            self.tau = 0.08
            
        if options.get("Param") == 'JB':
            self.om = 0.30
            self.ol = 0.70
            self.h0 = 70
            self.s8 = 0.98
            self.ns = 1.0
            self.ob = 0.04
            self.r = 0.0
            self.mnu = 0.00
            self.tau = 0.17
            
class Constants:
    def __init__(self):
        self.ERRTOL = 1e-12
        self.G_CGS = 6.67259e-08
        self.MSUN_CGS = 1.98900e+33
        self.MPC2CM = 3.085678e+24
        self.SIGMA_T = 6.65246e-25 #cgs
        self.ME = 9.10939E-28
        self.C = 2.99792e+10
        self.K_CGS = 1.3806488e-16
        self.H_CGS = 6.62608e-27
        self.TCMB = 2.726
        self.TCMBmuK = self.TCMB * 1.0e6
        self.eV_2_erg = 1.60217662e-12
        
    
class Halo_MF:
    def __init__(self,cosmoParams,cambResults):
        self.cp = cosmoParams
        self.HP = HP.HaloTools(self.cp)
        self.results = cambResults
    #Using CAMB to get p of k
    def pk(self,z_arr):
        
        
        pars = camb.CAMBparams()
        pars.set_cosmology(H0=self.cp.h0, ombh2=self.cp.ob*(self.cp.h0/100.)**2, omch2=(self.cp.om - self.cp.ob)*(self.cp.h0/100.)**2,)    
        pars.set_dark_energy() #re-set defaults
        pars.InitPower.set_params(As=2.19e-9,ns=self.cp.ns)
        
        pars.set_matter_power(redshifts=z_arr, kmax=11.0)
        pars.Transfer.high_precision = True
        
        pars.NonLinear = model.NonLinear_none
        self.results = camb.get_results(pars)
        kh2, z2, pk2 = self.results.get_matter_power_spectrum(minkh=2e-5, maxkh=11, npoints = 200,)
        s8 = np.array(self.results.get_sigma8())
        return kh2, z2, pk2, s8
    
    def Halo_Tinker_test(self):
        
        #define parameters delta, M and z
        z_arr = np.array([0,0.8,1.6])
        M = 10**np.arange(10., 16, .1)
        delts = z_arr*0 + 200.
        delts_8 = z_arr*0 + 800.
        delts_32 = z_arr*0 + 3200.
    
        # start timer
        start = time.clock()
        
        #get p of k and s8 
        kh, z, pk, s8 = self.pk(z_arr)
        # dn_dlogM from tinker
        N = dn_dlogM(M,z_arr,self.cp.rho_crit0*self.cp.om,delts,kh,pk[:1,:])
        N_8 = dn_dlogM(M,z_arr,self.cp.rho_crit0*self.cp.om,delts_8,kh,pk[:1,:])
        N_32 = dn_dlogM(M,z_arr,self.cp.rho_crit0*self.cp.om,delts_32,kh,pk[:1,:])
        
        elapsed1 = (time.clock() - start)
        #print elapsed1 
        
        #plot tinker values
        pl = Plotter()
        pl._ax.set_ylim(-3.6,-0.8)
        pl.add(np.log10(M),np.log10(N[:,0]*M/(self.cp.rho_crit0*self.cp.om)),color='black')
        pl.add(np.log10(M),np.log10(N_8[:,0]*M/(self.cp.rho_crit0*self.cp.om)),color='black')
        pl.add(np.log10(M),np.log10(N_32[:,0]*M/(self.cp.rho_crit0*self.cp.om)),color='black')
        pl.done("output/tinkervals.png")
        
        return f
    
    def dVdz(self,z_arr):
        pars = camb.CAMBparams()
        pars.set_cosmology(H0=self.cp.h0, ombh2=self.cp.ob*(self.cp.h0/100.)**2, omch2=(self.cp.om - self.cp.ob)*(self.cp.h0/100.)**2,)    
        results = camb.get_background(pars)
        DA_z = results.angular_diameter_distance(z_arr)
        dV_dz = DA_z**2 * (1.+z_arr)**2
        for i in xrange (len(z_arr)):
            dV_dz[i] /= (results.h_of_z(z_arr[i]))
        #print (results.h_of_z(z_arr[i])),z_arr[i],100. * 1e5/2.99792458e10*hh
        dV_dz *= (self.cp.h0/100.)**3
        return dV_dz

    def dn_dM(self,M,z_arr,delta):
        
        delts = z_arr*0 + delta
        kh, z, pk, s8 = self.pk(z_arr)
        fac = (self.cp.s8/s8[-1])**2 # sigma8 values are in reverse order
        pk *= fac
    
        dn_dlnm = dn_dlogM(M,z_arr,self.cp.rho_crit0*self.cp.om,delts,kh,pk[:,:],'comoving')
        dn_dm = dn_dlnm/M
        return dn_dm
    
    def N_of_Mz(self,M,z_arr,delta):
        
        delts = z_arr*0 + delta
        kh, z, pk, s8 = self.pk(z_arr)
        fac = (self.cp.s8/s8[-1])**2 # sigma8 values are in reverse order
        pk *= fac
    
        dn_dlnm = dn_dlogM(M,z_arr,self.cp.rho_crit0*self.cp.om,delts,kh,pk[:,:],'comoving')
        dn_dm = dn_dlnm/M
        dV_dz = self.dVdz(z_arr)
        
        N_dzdm = dn_dm[:,1:] * dV_dz[1:] * 4*np.pi
        return N_dzdm

    def N_of_z_SZ(self,z_arr):
        h0 = 70.
        lnYmin = np.log(1e-13)
        dlnY = 0.1
        lnY = np.arange(lnYmin,lnYmin+10.,dlnY)
    
        #M = 10**np.arange(14.0, 15.5, .1)
        M = 10**np.arange(14.0, 15.5, 0.5)
        dM = np.gradient(M)
        rho_crit0m = 3. / (8 * np.pi) * (h0 * 1e5)**2 / self.cp.c.G_CGS * self.cp.c.MPC2CM / self.cp.c.MSUN_CGS * self.cp.om
        hh = h0/100.

        M200 = np.outer(M,np.zeros([len(z_arr)]))
        dM200 = np.outer(M,np.zeros([len(z_arr)]))
        P_func = np.outer(M,np.zeros([len(z_arr)]))
        sigN = np.outer(M,np.zeros([len(z_arr)]))
        M_arr =  np.outer(M,np.ones([len(z_arr)]))

        DA_z = self.results.angular_diameter_distance(z_arr) * (self.cp.h0/100.)
        for ii in xrange (len(z_arr)-1):
            i = ii + 1
            M200[:,i] = self.HP.Mass_con_del_2_del_mean200(M/hh,500,z_arr[i])
            dM200[:,i] = np.gradient(M200[:,i])
            for j in xrange(len(M)):
                SZProf = SZ_Cluster_Model(self.cp,rms_noise = 1.,fwhm=3.0,M=M[j],z=z_arr[i])
                sigN[j,i] = np.sqrt(SZProf.filter_variance(DA_z[i]))
            
            P_func[:,i] = SZProf.P_of_q (lnY,M_arr[:,i],z_arr[i],sigN[:,i])*dlnY

        #print P_func
        #dN_dzdm = self.N_of_Mz(M200,z_arr,200.)
        dn_dzdm = self.dn_dM(M200,z_arr,200.)
        #print dn_dzdm
        N_z = np.zeros(len(z_arr) - 1)
        for i in xrange (len(z_arr) - 1):
            N_z[i] = np.sum(dn_dzdm[:,i+1]*P_func[:,i+1]*dM200[:,i+1])

        #N_z = np.dot(dN_dzdm,np.transpose(P_func[:,1:]*dM200[:,1:]))

        return N_z

class SZ_Cluster_Model:
    def __init__(self,cosmoParams,P0=8.403,xc=1.177,al=1.05,gm=0.31,bt=5.49,fwhm=1,rms_noise =1, M = 1.e14 ,z = 0.01 ,**options):
        self.cp = cosmoParams
        self.HP = HP.HaloTools(self.cp)
        self.P0 = P0
        self.xc = xc
        self.al = al
        self.gm = gm
        self.bt = bt
        self.fwhm = fwhm
        self.rms_noise = rms_noise
        
        self.NNR = 1000
        self.drint = 1e-4
        if options.get("Model") == 'BBPS':
            self.P0 = 7.49
            self.xc = 0.710
            self.al = 1.0
            self.gm = -0.3
            self.bt = 4.19

        from scipy.interpolate import interp1d
        r = np.arange(0.0001,100.,0.0001)
        self.R500 = self.HP.rdel_c(M,z,500)
        self.M = M
        self.z = z
        prof = self.Prof(r,M,z)
        self.profunc = interp1d(r,prof,bounds_error=True)        
    
    def f_nu(self,nu):
        mu = self.cp.c.H_CGS*(1e9*nu)/(self.cp.c.K_CGS*self.cp.c.TCMB)
        ans = mu*coth(mu/2.0) - 4.0
        return np.float(ans)
    
    def GNFW(self,xx,**options):
        ans = self.P0 / ((xx*self.xc)**self.gm * (1 + (xx*self.xc)**self.al)**((self.bt-self.gm)/self.al))
        if options.get("Model") == 'BBPS':
            ans = self.P0 * (xx/self.xc)**self.gm / (1 + (xx/self.xc)**self.al)**self.bt
        return ans
    
    def Prof(self,r,M,z):
        R500 = self.R500
        xx = r / R500
        M_fac = self.M / (3e14) * (100./70.)
        P500 = 1.65e-3 * (100./70.)**2 * M_fac**(2./3.) * self.HP.E_z(self.z) #keV cm^3
        ans = P500 * self.GNFW(xx)
        return ans
    
    def y2D_norm(self,tht):
        R500 = self.R500
        rad = (np.arange(1e5) + 1.0)*self.drint #in MPC (max rad is 10 MPC)

        P2D = tht * 0.0
        for ii in xrange(len(tht)):
            rint = np.sqrt((rad)**2 + tht[ii]**2*(R500)**2)
            P2D[ii] = np.sum(2.*self.profunc(rint)*self.drint)
            
        P2D /= P2D[0]
        y2D_out = P2D
        return y2D_out
    

    def y2D_tilde_norm(self,ell,thtc):
        dtht = 0.00001
        thta = np.arange(dtht,25*thtc,dtht)
        ans = ell*0.
        y2D_use = self.y2D_norm(thta/thtc)
        for ii in xrange(len(ell)):
            ans[ii] = np.sum(thta*special.jv(0,ell[ii]*thta)*y2D_use)*dtht
        return ans
    
    def y2D_test(self,tht,thtc):
        ans = (1. + (tht/thtc)**2)**(-0.5) # beta profile beta = 2/3
        return ans

    def y2D_tilde_test(self,k,thtc):
        #thtc = 1. / 60. / (180./np.pi) # rads 
        dtht = 0.00001
        thta = np.arange(dtht,100*thtc,dtht)
        ans = k*0.
        y2D_use = self.y2D_test(thta,thtc)
        for ii in xrange(len(k)):
            ans[ii] = np.sum(thta*special.jv(0,k[ii]*thta/thtc)*y2D_use)*dtht
        return ans/thtc**2

    def noise_func(self,ell):
        
        rms = self.rms_noise * (1./60.)*(np.pi/180.)
        tht_fwhm = np.deg2rad(self.fwhm / 60.)
        
        ans = rms**2 * np.exp(tht_fwhm**2*ell**2 / (8.*np.log(2))) ## Add Hasselfield noise knee
        return ans
    
    def tot_noise_spec(self):
        spec_file = "input/test_scalCls_new.dat"
        ell,cl = np.loadtxt(spec_file,usecols=[0,1],unpack=True)
        ell_extra = np.arange(60000)+np.max(ell)+1.
        cll_extra = np.zeros(60000)
        ell = np.append(ell,ell_extra)
        cl = np.append(cl,cll_extra) *2.*np.pi/(ell*(ell+1.))
        
        cltot = (cl + self.noise_func(ell)) / self.cp.c.TCMBmuK**2
        return ell,cltot,cl

    def plot_noise(self):
        el,nl,cl = self.tot_noise_spec()
        
        nl *= self.cp.c.TCMBmuK **2
        pl = Plotter(scaleX='log',scaleY='log')
        pl._ax.set_xlim(60,8e3)
        pl._ax.set_ylim(1e-2,1e5)
        pl.add(el,nl*el**2)
        pl.add(el,self.noise_func(el)*el**2)
        pl.add(el,cl*el**2)
        pl.done("output/noise.png")

    def filter_variance(self,DAz):
        
        thtc = self.R500/DAz
        
        el, nltemp, cl = self.tot_noise_spec()
        dell = 100
        ells = np.arange(2,60000,dell)
        nl = np.interp(ells,el,nltemp)
        freq_fac = (self.f_nu(150.))**2
        y2dtilde_2 = (self.y2D_tilde_norm(ells,thtc))**2
        var = np.sum(ells*y2dtilde_2/nl)*dell*freq_fac
        dtht = 0.0000025
        thta = np.arange(dtht,5.*thtc,dtht)
        y2D_use = self.y2D_norm(thta/thtc)
        prof_int = 2.*np.pi*(np.sum(y2D_use*thta)*dtht)**2
        
        return prof_int/var
    
    
    def Y_M(self,MM,zz):
        pars = camb.CAMBparams()
        pars.set_cosmology(H0=self.cp.h0, ombh2=self.cp.ob*(self.cp.h0/100.)**2, omch2=(self.cp.om - self.cp.ob)*(self.cp.h0/100.)**2,)    
        results = camb.get_background(pars)
        DA_z = results.angular_diameter_distance(zz) * (self.cp.h0/100.)
        
        #MM *= (self.cp.h0/100.) 
        
        Y_star = 2.42e-10 #sterads
        #dropped h70 factor
        alpha_ym = 1.79
        b_ym = 0.8
        beta_ym = 0.66
        
        ans = Y_star*((b_ym)*MM/ 1e14)**alpha_ym *(DA_z/100.)**(-2.) * self.HP.E_z(zz) ** beta_ym
        #print (0.01/DA_z)**2
        return ans
    
    def Y_erf(self,Y_true,sigma_N):
        q = 5.
        sigma_Na = np.outer(sigma_N,np.ones(len(Y_true[0,:])))
        
        ans = 0.5 * (1. + special.erf((Y_true - q*sigma_Na)/(np.sqrt(2.)*sigma_Na)))
        return ans
    
    def P_of_Y (self,lnY,MM,zz):
        sig = 0.127  
        Y = np.exp(lnY)
        Ma = np.outer(MM,np.ones(len(Y[0,:])))
        numer = -1.*np.log(Y/self.Y_M(Ma,zz))**2
        ans = 1/(sig * np.sqrt(2*np.pi)) * np.exp(numer/(2.*sig))
        return ans
    
    def P_of_q (self,lnY,MM,zz,sigma_N):
        lnYa = np.outer(np.ones(len(MM)),lnY)
        
        pars = camb.CAMBparams()
        pars.set_cosmology(H0=self.cp.h0, ombh2=self.cp.ob*(self.cp.h0/100.)**2, omch2=(self.cp.om - self.cp.ob)*(self.cp.h0/100.)**2,)    
        results = camb.get_background(pars)
        DA_z = results.angular_diameter_distance(zz) * (self.cp.h0/100.)
        
        sig_thresh = self.Y_erf(np.exp(lnYa),sigma_N)
        P_Y = self.P_of_Y(lnYa,MM, zz)

        ans = MM*0.0
        for ii in xrange(len(MM)):
            ans[ii] = np.sum(P_Y[ii,:]*sig_thresh[ii,:])
        return ans