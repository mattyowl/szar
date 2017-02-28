import os
cmdRoot = "python bin/calcFisher.py "

expList = ['S4']#,'SO']
resList = ['-3m','-5m','-6m','-7m']
atmList = ['']#,'-noatm']
#calList = ['CMB_all','owl2']#,'CMB_pol','owl1']
#calList = ['CMB_pol']#,'CMB_pol','owl1']
calList = ['owl1']#,'CMB_pol','owl1']
fishList = ['mnu','w','mnu-w']#,'mnu-cvltau','w-cvltau','mnu-w-cvltau','mnu-notau','w-notau','mnu-w-notau']


for exp in expList:
    for res in resList:
        for atm in atmList:
            for cal in calList:
                for fisher in fishList:
            
                    cmd = cmdRoot + exp+res+atm+" "+cal+" "+fisher
                    print cmd
                    os.system(cmd)