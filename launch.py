'''
Author: Anthony Badea
Date: 01/31/24
'''

import subprocess
import multiprocessing
import numpy as np
import os
import argparse
import submitit
from pathlib import Path
import json 
import random

def run_executable(executable_path, options):
    command = [executable_path] + options
    subprocess.run(command)

def run_commands(commands):
    for command in commands:
        print(command)
        if "pixelav" in command[0]:
            subprocess.run(command[1:], cwd=command[0])
        else:
            subprocess.run(command)

if __name__ == "__main__":

    # user options
    parser = argparse.ArgumentParser(usage=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-o", "--outDir", help="Output directory", default="./")
    parser.add_argument("-j", "--ncpu", help="Number of cores to use", default=4, type=int)
    parser.add_argument("-n", "--maxEvents", help="Number of events per bin", default=1000, type=str)
    parser.add_argument("-p", "--pixelAVdir", help="pixelAV directory", default="./pixelav/")
    parser.add_argument("--mode", help="Options: local, slurm", default="local")
    parser.add_argument("--query", help="path to json file containing query", default=None)
    parser.add_argument("--njobs", help="number of jobs to actually launch. default is all", default=-1, type=int)
    args = parser.parse_args()

    # get absolute path and check if outdir exists
    outDir = os.path.abspath(args.outDir)
    if not os.path.isdir(outDir):
        os.makedirs(outDir)

    # ./minbias.exe <outFileName> <maxEvents> <pTHatMin> <pTHatMax>
    path_to_executable = "./bin/minbias.exe"
    pt = np.linspace(0,2,21)

    # create job configurations
    confs = []
    for pTHatMin, pTHatMax in zip(pt[0:-1],pt[1:]):
        
        # fix numpy rounding
        pTHatMin = round(pTHatMin, 3)
        pTHatMax = round(pTHatMax, 3)
        
        # format
        outFileName = Path(outDir, f"minbias_{pTHatMin:.2f}_{pTHatMax:.2f}_GeV").resolve()

        # just say hi
        hi = ["echo", "hi"]

        # pythia
        pythiaExe = Path("./bin/minbias.exe").resolve()
        pythia = [pythiaExe, outFileName, args.maxEvents, str(pTHatMin), str(pTHatMax)]

        # delphes
        delphesExe = Path("/opt/delphes/DelphesHepMC3").resolve()
        delphesCard = Path("./delphes_card_CMS_ABEdit.tcl").resolve() # os.path.join("/opt/delphes/cards", "delphes_card_CMS.tcl")
        delphesOutRoot = outFileName.name + ".root"
        delphesOutHepmc = outFileName.name + ".hepmc"
        delphes = [delphesExe, delphesCard, delphesOutRoot, delphesOutHepmc]

        # delphes to track list for pixelAV
        trackListIn = f"{outFileName}.root".replace("pythia", "delphes")
        trackListOut = f"{outFileName}.txt".replace("pythia", "pixelavIn")
        trackList = ["python3", "utils/delphesRootToPixelAvTrackList.py", "-i", trackListIn, "-o", trackListOut]

        # pixelAV
        pixelavIn = trackListOut
        pixelavOut = f"{outFileName}.out".replace("pythia", "pixelavOut")
        pixelavSeedFile = f"{outFileName}_seed".replace("pythia", "pixelavOut")
        pixelAV = [str(Path(args.pixelAVdir).resolve()), "./bin/ppixelav2_list_trkpy_n_2f.exe", "1", pixelavIn, pixelavOut, pixelavSeedFile]
        
        # create configuration
        conf = (hi, pixelAV) # (pythia, delphes, trackList, pixelAV)

        # make the format correct for submission
        if args.mode == "local":
            confs.append([conf,]) # weird formatting is because pool expects a tuple at input
        elif args.mode == "slurm":
            confs.append(conf)

    print(confs)

    # multiprocessing (single or multiple core) submission
    if args.mode == "local":
        # List of CPU cores to use for parallel execution
        num_cores = multiprocessing.cpu_count() if args.ncpu == -1 else args.ncpu

        # Create a pool of processes to run in parallel
        pool = multiprocessing.Pool(num_cores)
        
        # Launch the executable N times in parallel with different options
        pool.starmap(run_commands, confs)
        
        # Close the pool of processes
        pool.close()
        pool.join()

    # slurm based submission
    elif args.mode == "slurm":

        # read in query
        if Path(args.query).resolve().exists():
            query_path = Path(args.query).resolve()
        else:
            # throw
            raise ValueError(f"Could not locate {args.query} in query directory or as absolute path")
        with open(query_path) as f:
            query = json.load(f)

        # create top level output directory
        top_dir = Path("results", f'./temp-{"%08x" % random.randrange(16**8)}', "%j").resolve()

        # submission
        executor = submitit.AutoExecutor(folder=top_dir)
        executor.update_parameters(**query.get("slurm", {}))
        
        # loop over configurations
        jobs = []
        with executor.batch():
            for iC, conf in enumerate(confs):
                
                # only launch a single job
                if args.njobs != -1 and (iC+1) > args.njobs:
                    continue
                
                print(conf)
                job = executor.submit(run_commands, conf)
                jobs.append(job)
